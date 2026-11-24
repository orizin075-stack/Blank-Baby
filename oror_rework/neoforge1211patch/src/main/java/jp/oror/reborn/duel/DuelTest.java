package jp.oror.reborn.duel;

import com.mojang.authlib.GameProfile;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import jp.oror.reborn.OrorReborn;
import jp.oror.reborn.SupremeEntity;
import jp.oror.reborn.raid.Raid;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.ModList;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (059e) CI check "duel" (/oror duel test): the user's OROR Duel Dominion 0.17.0-alpha with OROR on a dedicated server
 * (the user: "これもお願いね デバッグも", "導入"). Through its own code (by reflection: OROR needs no Duel Dominion):
 * <ol>
 * <li>a white-glove duel with a zombie, won by the player: the zombie sealed into a bound hair;</li>
 * <li>the hair called out (the zombie back, the player's) and called back in;</li>
 * <li>a duel with an OROR god (Ferdinand): the player's blows start its raid, its last fall seals it (Duel Dominion turns
 * the death away), and the god called out of its hair lives (its raid gone: OROR's fix) two seconds later;</li>
 * <li>three vexes and an allay bound into spirit effigies, the night parade talisman cast with three (its spirits come)
 * and the healing one with one.</li>
 * </ol>
 * (059g, "じゃあそれのデバッグもお願い") and then the rest of it (deeper): the eight other talisman families at their
 * smallest offering (retribution returning a blow, guardian, binding, malice transfer, soul seeker, exorcism, calamity,
 * revival), possession and fusion on the server's side (a fake player has no client: its camera is checked as the
 * server sets it) with their recovery after a logout and after a crash, a duel lost, and the ledgers saved and read back.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class DuelTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Duel");
    public static volatile boolean resultLogged;
    private static final Map<String, Object> OUT = new LinkedHashMap<>();
    /** What Duel Dominion told the tester, in order. */
    private static final List<String> SAID = new java.util.ArrayList<>();
    private static final List<ChunkPos> FORCED = new ArrayList<>();
    private static final List<Entity> MADE = new ArrayList<>();
    private static ServerLevel level;
    private static long checkAt, runAt;
    private static Entity calledGod;
    private static FakePlayer fp;
    private static BlockPos site;
    private static volatile boolean vulnerable;
    private static Mob gloved, meddler;
    private static long check2At = Long.MAX_VALUE;

    private DuelTest() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("duel").then(Commands.literal("test")
            .requires(s -> s.hasPermission(2)).executes(c -> start(c.getSource())))));
    }

    private static Item item(String path) {
        return BuiltInRegistries.ITEM.get(ResourceLocation.fromNamespaceAndPath("dueldominion", path));
    }

    private static int start(CommandSourceStack src) {
        OUT.clear();
        MADE.clear();
        if (!ModList.get().isLoaded("dueldominion")) {
            LOG.info("DUEL-RESULT {\"present\":false,\"pass\":true}");
            resultLogged = true;
            return 0;
        }
        ServerLevel lv = src.getServer().overworld();
        level = lv;
        BlockPos c = BlockPos.containing(src.getPosition()).offset(2400, 0, -2400);
        for (int dx = -2; dx <= 2; dx++) {
            for (int dz = -2; dz <= 2; dz++) {
                ChunkPos p = new ChunkPos((c.getX() >> 4) + dx, (c.getZ() >> 4) + dz);
                if (lv.setChunkForced(p.x, p.z, true)) {
                    FORCED.add(p);
                }
            }
        }
        int y = lv.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, c.getX(), c.getZ());
        site = new BlockPos(c.getX(), Math.max(y, lv.getSeaLevel() + 1), c.getZ());
        for (BlockPos q : BlockPos.betweenClosed(site.offset(-10, -1, -10), site.offset(10, -1, 10))) {
            lv.setBlock(q, Blocks.STONE.defaultBlockState(), 2);
        }
        for (BlockPos q : BlockPos.betweenClosed(site.offset(-10, 0, -10), site.offset(10, 7, 10))) {
            lv.setBlock(q, Blocks.AIR.defaultBlockState(), 2);
        }
        // (059e) a tester that keeps what Duel Dominion tells it (a fake player drops every message): CI 22 and 23 could not
        // call a sealed zombie out, and only Duel Dominion's own message says why
        SAID.clear();
        fp = new FakePlayer(lv, new GameProfile(UUID.nameUUIDFromBytes("oror_duel_tester".getBytes()), "[Duel Tester]")) {
            @Override
            public void sendSystemMessage(net.minecraft.network.chat.Component message) {
                SAID.add(message.getString());
            }

            @Override
            public void displayClientMessage(net.minecraft.network.chat.Component message, boolean overlay) {
                SAID.add(message.getString());
            }

            // (059g) a fake player takes no damage; the steps that need the tester hurt (a duel lost, retribution) turn
            // this on for themselves
            @Override
            public boolean isInvulnerableTo(net.minecraft.world.damagesource.DamageSource source) {
                return !vulnerable && super.isInvulnerableTo(source);
            }

            @Override
            public boolean canHarmPlayer(net.minecraft.world.entity.player.Player other) {
                return vulnerable || super.canHarmPlayer(other);
            }

            // (059g, CI 38) a fake player has no client to complete a teleport (its connection drops it): moved at once,
            // as a real player is once its client answers - possession and fusion move the player's body
            @Override
            public void teleportTo(double x, double y, double z) {
                this.moveTo(x, y, z, this.getYRot(), this.getXRot());
            }

            @Override
            public boolean teleportTo(ServerLevel to, double x, double y, double z, java.util.Set<net.minecraft.world.entity.RelativeMovement> rel,
                                      float yRot, float xRot) {
                if (to != this.serverLevel()) {
                    return super.teleportTo(to, x, y, z, rel, yRot, xRot);
                }
                this.moveTo(x, y, z, yRot, xRot);
                return true;
            }
        };
        // (CI 38) a fake player never ticks: its three seconds of spawn protection never run out, and no blow lands
        unshield(fp);
        fp.moveTo(site.getX() + 0.5, site.getY(), site.getZ() + 0.5, 0F, 0F);
        if (fp.isCreative() || fp.isSpectator()) {
            fp.setGameMode(GameType.SURVIVAL);
        }
        fp.getInventory().clearContent();
        // (059e) the duels three seconds on, once the forced chunks hold entities: run in the tick they were forced, every
        // mob Duel Dominion called out went into a chunk not yet taking entities (CI 24: "召喚：Zombie" said, and nothing
        // there: "calledAt":"none", then "召喚済み個体が未読み込み"), and so did the night parade's spirit
        runAt = lv.getGameTime() + 60;
        checkAt = Long.MAX_VALUE;
        return 1;
    }

    private static void run(ServerLevel lv) throws ReflectiveOperationException {
        Class<?> manager = Class.forName("jp.oror.dueldominion.DuelManager");
        Method start = manager.getMethod("start", ServerPlayer.class, LivingEntity.class);
        Class<?> sealData = Class.forName("jp.oror.dueldominion.SealData");
        Method read = sealData.getMethod("read", ItemStack.class);
        Method put = sealData.getMethod("put", ItemStack.class, CompoundTag.class);
        Method valid = sealData.getMethod("valid", CompoundTag.class);
        Method toggle = Class.forName("jp.oror.dueldominion.SealSummoning").getMethod("toggle", ServerPlayer.class, CompoundTag.class);
        Method bind = Class.forName("jp.oror.dueldominion.SpiritBinding").getMethod("bind", ServerPlayer.class, Mob.class);
        Class<?> talisman = Class.forName("jp.oror.dueldominion.RitualPolicy$Talisman");
        Method cast = Class.forName("jp.oror.dueldominion.RitualCasting").getMethod("cast", ServerPlayer.class, talisman, List.class, ItemStack.class);
        Item hair = item("bound_hair");

        // 1. a duel with a zombie, won: the zombie sealed
        Zombie z = EntityType.ZOMBIE.create(lv);
        z.moveTo(site.getX() + 3.5, site.getY(), site.getZ() + 0.5, 0F, 0F);
        z.setNoAi(true);
        lv.addFreshEntity(z);
        OUT.put("duelStarted", start.invoke(null, fp, z));
        z.invulnerableTime = 0;
        z.hurt(fp.damageSources().playerAttack(fp), 1000F);
        OUT.put("zombieSealed", z.isRemoved());
        ItemStack seal = held(hair, null);
        CompoundTag sd = seal.isEmpty() ? new CompoundTag() : (CompoundTag) read.invoke(null, seal);
        OUT.put("sealMade", !seal.isEmpty() && (Boolean) valid.invoke(null, sd));
        if (seal.isEmpty()) {
            return;
        }
        // 2. called out and back in
        boolean out = (Boolean) toggle.invoke(null, fp, sd);
        put.invoke(null, seal, sd);
        Mob servant = servant(EntityType.ZOMBIE);
        // (CI 22: called out false) what Duel Dominion said and where the tester and the zombie are
        OUT.put("toggleOut", out);
        OUT.put("sealActive", sd.hasUUID("ActiveEntity"));
        OUT.put("testerAt", "\"" + fp.blockPosition().toShortString() + "\"");
        if (sd.hasUUID("ActiveEntity")) {
            Entity called = lv.getEntity(sd.getUUID("ActiveEntity"));
            OUT.put("calledAt", called == null ? "\"none\"" : "\"" + called.blockPosition().toShortString() + " " + called.isAlive() + "\"");
        }
        OUT.put("calledOut", out && servant != null);
        boolean back = (Boolean) toggle.invoke(null, fp, sd);
        put.invoke(null, seal, sd);
        OUT.put("calledBack", back && servant != null && servant.isRemoved());

        // 3. a duel with an OROR god: its raid, its seal, its return
        var holder = OrorReborn.TYPES.get("ferdinand");
        SupremeEntity god = holder == null ? null : holder.get().create(lv);
        if (god != null) {
            god.moveTo(site.getX() - 4.5, site.getY(), site.getZ() + 0.5, 0F, 0F);
            god.setNoAi(true);
            lv.addFreshEntity(god);
            OUT.put("godDuel", start.invoke(null, fp, god));
            god.invulnerableTime = 0;
            god.hurt(fp.damageSources().playerAttack(fp), 10F);
            OUT.put("godRaid", Raid.active(god));
            Raid.testHealth(god, 1F);
            god.invulnerableTime = 0;
            god.hurt(fp.damageSources().playerAttack(fp), 500F);
            OUT.put("godSealed", god.isRemoved());
            ItemStack godSeal = held(hair, "oror_supreme_bosses:ferdinand");
            if (!godSeal.isEmpty()) {
                CompoundTag gd = (CompoundTag) read.invoke(null, godSeal);
                OUT.put("godSealHasRaid", gd.getCompound("MobData").getCompound("NeoForgeData").contains("ororRaid"));
                boolean called = (Boolean) toggle.invoke(null, fp, gd);
                put.invoke(null, godSeal, gd);
                Mob g = servant(god.getType());
                OUT.put("godCalledOut", called && g != null);
                calledGod = g;
            } else {
                OUT.put("godCalledOut", false);
            }
        }

        // 4. spirit effigies and two talismans
        List<ItemStack> spirits = new ArrayList<>();
        for (int i = 0; i < 4; i++) {
            Mob m = (i < 3 ? EntityType.VEX : EntityType.ALLAY).create(lv);
            m.moveTo(site.getX() + 0.5, site.getY() + 1, site.getZ() + 4.5 + i, 0F, 0F);
            m.setNoAi(true);
            lv.addFreshEntity(m);
            ItemStack token = (ItemStack) bind.invoke(null, fp, m);
            if (!token.isEmpty()) {
                spirits.add(token);
            }
        }
        OUT.put("effigies", spirits.size());
        if (spirits.size() == 4) {
            @SuppressWarnings({"unchecked", "rawtypes"})
            Object parade = Enum.valueOf((Class) talisman, "NIGHT_PARADE");
            @SuppressWarnings({"unchecked", "rawtypes"})
            Object healing = Enum.valueOf((Class) talisman, "HEALING");
            boolean p = (Boolean) cast.invoke(null, fp, parade, List.of(spirits.get(0), spirits.get(1), spirits.get(2)), new ItemStack(item("ofuda_night_parade")));
            OUT.put("nightParade", p);
            List<Mob> came = lv.getEntitiesOfClass(Mob.class, fp.getBoundingBox().inflate(16), m -> m.getPersistentData().getBoolean("DuelParadeSpirit"));
            OUT.put("paradeSpirits", came.size());
            MADE.addAll(came);
            fp.setHealth(Math.max(1F, fp.getMaxHealth() - 10F));
            OUT.put("healing", cast.invoke(null, fp, healing, List.of(spirits.get(3)), new ItemStack(item("ofuda_healing"))));
        }
        deeper(lv, seal, hair);
    }

    // ============================================================================================ (059g) the rest of it
    // the user: "じゃあそれのデバッグもお願い" - every talisman family, possession and fusion (and their recovery after a
    // logout or a crash), a duel lost, a servant's revival, and the ledgers saved and read back. Each step on its own, so
    // one that throws does not hide the others; what threw is reported with where.

    private interface Step {
        void run() throws Exception;
    }

    private static void step(String name, Step s) {
        try {
            s.run();
        } catch (Throwable t) {
            Throwable c = t instanceof java.lang.reflect.InvocationTargetException && t.getCause() != null ? t.getCause() : t;
            String at = c.getStackTrace().length > 0 ? c.getStackTrace()[0].toString() : "";
            OUT.put("err_" + name, "\"" + (c + " @ " + at).replace('"', '\'').replace('\\', '/') + "\"");
            LOG.warn("DUEL-TEST step {} threw", name, c);
        }
    }

    private static Object talisman(String name) throws ClassNotFoundException {
        @SuppressWarnings({"unchecked", "rawtypes"})
        Object t = Enum.valueOf((Class) Class.forName("jp.oror.dueldominion.RitualPolicy$Talisman"), name);
        return t;
    }

    /** n fresh effigies (vexes bound one by one beside the tester). */
    private static List<ItemStack> effigies(ServerLevel lv, int n) throws ReflectiveOperationException {
        Method bind = Class.forName("jp.oror.dueldominion.SpiritBinding").getMethod("bind", ServerPlayer.class, Mob.class);
        List<ItemStack> out = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            Mob m = EntityType.VEX.create(lv);
            m.moveTo(fp.getX() - 2.0, fp.getY() + 1.0, fp.getZ() - 2.0, 0F, 0F);
            m.setNoAi(true);
            lv.addFreshEntity(m);
            ItemStack token = (ItemStack) bind.invoke(null, fp, m);
            if (!token.isEmpty()) {
                out.add(token);
            } else if (!m.isRemoved()) {
                m.discard();
            }
        }
        return out;
    }

    /** A still enemy four blocks before the tester, the tester looking at it. */
    private static Mob foe(ServerLevel lv, EntityType<? extends Mob> type, double side) {
        Mob m = type.create(lv);
        m.moveTo(fp.getX() + side, fp.getY(), fp.getZ() + 4.0, 180F, 0F);
        m.setNoAi(true);
        lv.addFreshEntity(m);
        MADE.add(m);
        fp.lookAt(net.minecraft.commands.arguments.EntityAnchorArgument.Anchor.EYES, m.getEyePosition());
        return m;
    }

    private static boolean castWith(String name, String item, List<ItemStack> spirits, LivingEntity target) throws ReflectiveOperationException {
        Class<?> tc = Class.forName("jp.oror.dueldominion.RitualPolicy$Talisman");
        Class<?> rc = Class.forName("jp.oror.dueldominion.RitualCasting");
        ItemStack ofuda = new ItemStack(item(item));
        if (target == null) {
            return (Boolean) rc.getMethod("cast", ServerPlayer.class, tc, List.class, ItemStack.class).invoke(null, fp, talisman(name), spirits, ofuda);
        }
        return (Boolean) rc.getMethod("cast", ServerPlayer.class, tc, List.class, ItemStack.class, LivingEntity.class)
            .invoke(null, fp, talisman(name), spirits, ofuda, target);
    }

    private static void deeper(ServerLevel lv, ItemStack seal, Item hair) throws ReflectiveOperationException {
        Method read = Class.forName("jp.oror.dueldominion.SealData").getMethod("read", ItemStack.class);
        Method put = Class.forName("jp.oror.dueldominion.SealData").getMethod("put", ItemStack.class, CompoundTag.class);
        Method toggle = Class.forName("jp.oror.dueldominion.SealSummoning").getMethod("toggle", ServerPlayer.class, CompoundTag.class);
        Class<?> pmc = Class.forName("jp.oror.dueldominion.PossessionManager");
        Class<?> dmc = Class.forName("jp.oror.dueldominion.DuelManager");
        Class<?> dec = Class.forName("jp.oror.dueldominion.DuelEvents");
        UUID me = fp.getUUID();

        // 5. every talisman family at its smallest offering
        step("retribution", () -> {
            List<ItemStack> sp = effigies(lv, 1);
            Mob v = foe(lv, EntityType.VINDICATOR, -3.0);
            boolean ok = castWith("RETRIBUTION", "ofuda_retribution", sp, null);
            float before = v.getHealth();
            vulnerable = true;
            fp.invulnerableTime = 0;
            fp.hurt(fp.damageSources().mobAttack(v), 3F);
            vulnerable = false;
            fp.setHealth(fp.getMaxHealth());
            OUT.put("retribution", ok);
            OUT.put("retributionReturned", v.getHealth() < before);
        });
        step("guardian", () -> {
            boolean ok = castWith("GUARDIAN", "ofuda_guardian", effigies(lv, 1), null);
            OUT.put("guardian", ok && fp.hasEffect(net.minecraft.world.effect.MobEffects.DAMAGE_RESISTANCE));
        });
        step("binding", () -> {
            Mob v = foe(lv, EntityType.VINDICATOR, 0.0);
            boolean ok = castWith("BINDING", "ofuda_binding", effigies(lv, 1), v);
            OUT.put("binding", ok && v.hasEffect(net.minecraft.world.effect.MobEffects.MOVEMENT_SLOWDOWN));
        });
        step("maliceTransfer", () -> {
            Mob v = foe(lv, EntityType.PILLAGER, 1.5);
            fp.addEffect(new net.minecraft.world.effect.MobEffectInstance(net.minecraft.world.effect.MobEffects.DIG_SLOWDOWN, 600, 0));
            boolean ok = castWith("MALICE_TRANSFER", "ofuda_malice_transfer", effigies(lv, 3), v);
            OUT.put("maliceTransfer", ok && v.hasEffect(net.minecraft.world.effect.MobEffects.DIG_SLOWDOWN)
                && !fp.hasEffect(net.minecraft.world.effect.MobEffects.DIG_SLOWDOWN));
        });
        step("soulSeeker", () -> {
            Mob v = foe(lv, EntityType.PILLAGER, -1.5);
            float before = v.getHealth();
            boolean ok = castWith("SOUL_SEEKER", "ofuda_soul_seeker", effigies(lv, 3), v);
            OUT.put("soulSeeker", ok && (v.getHealth() < before || !v.isAlive()));
        });
        step("exorcism", () -> {
            Mob z = foe(lv, EntityType.ZOMBIE, 2.5);
            float before = z.getHealth();
            boolean ok = castWith("EXORCISM", "ofuda_exorcism", effigies(lv, 3), null);
            OUT.put("exorcism", ok && (z.getHealth() < before || !z.isAlive()));
        });
        step("calamity", () -> {
            Mob v = foe(lv, EntityType.VINDICATOR, 3.0);
            float before = v.getHealth();
            boolean ok = castWith("CALAMITY", "ofuda_calamity", effigies(lv, 7), null);
            OUT.put("calamity", ok);
            // (CI 38) at seven offerings 禍刻 lays weakness and slowness on the enemies about; harm comes with more
            OUT.put("calamityHit", v.getHealth() < before || !v.isAlive() || v.hasEffect(net.minecraft.world.effect.MobEffects.WEAKNESS)
                || v.hasEffect(net.minecraft.world.effect.MobEffects.MOVEMENT_SLOWDOWN));
            OUT.put("testerAliveAfterCalamity", fp.isAlive() && fp.getHealth() > 0F);
        });
        for (Entity x : List.copyOf(MADE)) {
            if (x instanceof Mob && !x.isRemoved() && !x.getPersistentData().hasUUID("DuelDominionOwner")) {
                x.discard();
            }
        }

        // 6. possession and fusion with the sealed zombie called out, then their recovery after a logout and a crash
        CompoundTag sd = (CompoundTag) read.invoke(null, seal);
        boolean out = (Boolean) toggle.invoke(null, fp, sd);
        put.invoke(null, seal, sd);
        Mob called = servant(EntityType.ZOMBIE);
        OUT.put("calledForPossession", out && called != null);
        if (called == null) {
            // (a summon cooldown after the recall) the god called out in step 3 serves instead, not killed below
            OUT.put("possessionOn", "\"god\"");
            called = calledGod instanceof Mob g ? g : null;
        }
        if (called != null) {
            final Mob sv = called;
            final boolean isGod = sv == calledGod;
            step("possession", () -> {
                net.minecraft.world.phys.Vec3 from = fp.position();
                boolean wasNoAi = sv.isNoAi();
                // (CI 38: NullPointerException in DistanceManager.removePlayer) the camera moves the player, and the chunk
                // map lets go of the section it was last in: a fake player was never in one. A real player always is.
                java.lang.reflect.Method sec = ServerPlayer.class.getDeclaredMethod("setLastSectionPos", net.minecraft.core.SectionPos.class);
                sec.setAccessible(true);
                sec.invoke(fp, net.minecraft.core.SectionPos.of(sv));
                boolean in = (Boolean) pmc.getMethod("enter", ServerPlayer.class, Mob.class).invoke(null, fp, sv);
                boolean during = (Boolean) pmc.getMethod("isPossessing", UUID.class).invoke(null, me);
                pmc.getMethod("exit", ServerPlayer.class).invoke(null, fp);
                boolean after = (Boolean) pmc.getMethod("isPossessing", UUID.class).invoke(null, me);
                OUT.put("possession", in && during && !after);
                OUT.put("possessionRestored", sv.isNoAi() == wasNoAi && fp.getCamera() == fp && fp.position().distanceTo(from) < 1.5);
            });
            step("fusion", () -> {
                net.minecraft.world.phys.Vec3 from = fp.position();
                boolean in = (Boolean) pmc.getMethod("fuse", ServerPlayer.class, Mob.class).invoke(null, fp, sv);
                boolean hidden = fp.isInvisible() && fp.isInvulnerable();
                pmc.getMethod("exit", ServerPlayer.class).invoke(null, fp);
                OUT.put("fusion", in && hidden);
                OUT.put("fusionRestored", !fp.isInvisible() && !fp.isInvulnerable() && !fp.noPhysics
                    && !fp.getPersistentData().getBoolean("DuelFusionNeedsRecovery") && sv.isAlive());
                fp.teleportTo(from.x, from.y, from.z);
            });
            step("logoutWhileFused", () -> {
                boolean in = (Boolean) pmc.getMethod("fuse", ServerPlayer.class, Mob.class).invoke(null, fp, sv);
                dec.getMethod("logout", net.neoforged.neoforge.event.entity.player.PlayerEvent.PlayerLoggedOutEvent.class)
                    .invoke(null, new net.neoforged.neoforge.event.entity.player.PlayerEvent.PlayerLoggedOutEvent(fp));
                boolean still = (Boolean) pmc.getMethod("isPossessing", UUID.class).invoke(null, me);
                OUT.put("logoutWhileFused", in && !still && !fp.isInvisible() && !fp.isInvulnerable() && !fp.noPhysics);
            });
            step("crashWhileFused", () -> {
                boolean in = (Boolean) pmc.getMethod("fuse", ServerPlayer.class, Mob.class).invoke(null, fp, sv);
                pmc.getMethod("reset").invoke(null);              // the server gone without an exit: only the player's data knows
                boolean marked = fp.getPersistentData().getBoolean("DuelFusionNeedsRecovery");
                dec.getMethod("login", net.neoforged.neoforge.event.entity.player.PlayerEvent.PlayerLoggedInEvent.class)
                    .invoke(null, new net.neoforged.neoforge.event.entity.player.PlayerEvent.PlayerLoggedInEvent(fp));
                OUT.put("crashWhileFused", in && marked && !fp.isInvisible() && !fp.isInvulnerable() && !fp.noPhysics
                    && !fp.getPersistentData().getBoolean("DuelFusionNeedsRecovery"));
            });
            fp.setInvisible(false);
            fp.setInvulnerable(false);
            fp.noPhysics = false;
            step("clickPossess", () -> {
                fp.setShiftKeyDown(false);
                fp.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, ItemStack.EMPTY);
                dec.getMethod("possessOnClick", net.neoforged.neoforge.event.entity.player.PlayerInteractEvent.EntityInteract.class)
                    .invoke(null, new net.neoforged.neoforge.event.entity.player.PlayerInteractEvent.EntityInteract(fp,
                        net.minecraft.world.InteractionHand.MAIN_HAND, sv));
                boolean in = (Boolean) pmc.getMethod("isPossessing", UUID.class).invoke(null, me);
                pmc.getMethod("exit", ServerPlayer.class).invoke(null, fp);
                OUT.put("clickPossess", in);
            });
            step("clickFuse", () -> {
                fp.setShiftKeyDown(true);
                dec.getMethod("possessOnClick", net.neoforged.neoforge.event.entity.player.PlayerInteractEvent.EntityInteract.class)
                    .invoke(null, new net.neoforged.neoforge.event.entity.player.PlayerInteractEvent.EntityInteract(fp,
                        net.minecraft.world.InteractionHand.MAIN_HAND, sv));
                fp.setShiftKeyDown(false);
                boolean fused = (Boolean) pmc.getMethod("isFused", UUID.class).invoke(null, me);
                OUT.put("clickFuse", fused);
                // fused, the body goes where the host goes
                sv.teleportTo(sv.getX() + 3.0, sv.getY(), sv.getZ());
                pmc.getMethod("playerTick", net.neoforged.neoforge.event.tick.PlayerTickEvent.Post.class)
                    .invoke(null, new net.neoforged.neoforge.event.tick.PlayerTickEvent.Post(fp));
                OUT.put("fusionFollows", fused && fp.distanceTo(sv) < 2.0);
                pmc.getMethod("exit", ServerPlayer.class).invoke(null, fp);
                OUT.put("clickFuseRestored", !fp.isInvisible() && !fp.isInvulnerable() && !fp.noPhysics);
            });
            // fused, the host killed: its owner falls with it (Duel Dominion's own rule), the servant drops nothing
            // (CI 39) Duel Dominion finds the host's owner through the server's player list, which a fake player is not in:
            // the owner never fell, the fusion never ended, and every duel after it was refused (still fused). For this
            // step the tester is listed by its UUID (and the world keeps its inventory, should its death drop anything).
            if (!isGod) step("fusionHostDeath", () -> {
                net.minecraft.world.phys.Vec3 from = fp.position();
                boolean in = (Boolean) pmc.getMethod("fuse", ServerPlayer.class, Mob.class).invoke(null, fp, sv);
                AABB around = sv.getBoundingBox().inflate(6.0);
                int drops0 = lv.getEntitiesOfClass(net.minecraft.world.entity.item.ItemEntity.class, around).size()
                    + lv.getEntitiesOfClass(net.minecraft.world.entity.ExperienceOrb.class, around).size();
                var keep = lv.getGameRules().getRule(net.minecraft.world.level.GameRules.RULE_KEEPINVENTORY);
                boolean kept = keep.get();
                keep.set(true, lv.getServer());
                net.minecraft.nbt.ListTag inv = fp.getInventory().save(new net.minecraft.nbt.ListTag());
                listed(lv, true);
                vulnerable = true;
                try {
                    sv.kill();
                } finally {
                    vulnerable = false;
                    listed(lv, false);
                    keep.set(kept, lv.getServer());
                }
                int drops1 = lv.getEntitiesOfClass(net.minecraft.world.entity.item.ItemEntity.class, around).size()
                    + lv.getEntitiesOfClass(net.minecraft.world.entity.ExperienceOrb.class, around).size();
                boolean ownerFell = fp.getHealth() <= 0F || fp.isDeadOrDying();
                boolean still = (Boolean) pmc.getMethod("isPossessing", UUID.class).invoke(null, me);
                OUT.put("fusionHostDeath", in && !sv.isAlive());
                OUT.put("fusionHostDeathOwnerFalls", ownerFell);
                OUT.put("fusionEndsOnHostDeath", !still);
                OUT.put("noDropsOnServantDeath", drops1 == drops0);
                if (still) {
                    pmc.getMethod("exit", ServerPlayer.class).invoke(null, fp);     // so the steps after it are not refused
                }
                fp.getInventory().clearContent();
                fp.getInventory().load(inv);
                try {
                    java.lang.reflect.Field dead = LivingEntity.class.getDeclaredField("dead");
                    dead.setAccessible(true);
                    dead.setBoolean(fp, false);
                } catch (ReflectiveOperationException | RuntimeException ex) {
                    LOG.warn("DUEL-TEST revive {}", ex.toString());
                }
                fp.setHealth(fp.getMaxHealth());
                fp.deathTime = 0;
                fp.setInvisible(false);
                fp.setInvulnerable(false);
                fp.noPhysics = false;
                fp.teleportTo(from.x, from.y, from.z);
            });

            // 7. the servant killed: its revival waits, the revival talisman brings it nearer
            if (!isGod) step("revival", () -> {
                Class<?> blc = Class.forName("jp.oror.dueldominion.BindingLedger");
                Object ledger = blc.getMethod("forPlayer", ServerPlayer.class).invoke(null, fp);
                if (sv.isAlive()) {
                    sv.kill();
                }
                long now = lv.getServer().overworld().getGameTime();
                boolean waiting = (Boolean) blc.getMethod("hasRecovering", UUID.class, long.class).invoke(ledger, me, now);
                long before = reviveAt(ledger, me);
                boolean ok = castWith("REVIVAL", "ofuda_revival", effigies(lv, 3), null);
                long after = reviveAt(ledger, me);
                OUT.put("revivalWaiting", waiting);
                OUT.put("revival", ok && after < before);
                OUT.put("revivalTicks", "\"" + (before - now) + "->" + (after - now) + "\"");
            });
        }

        // 8. a duel lost: the tester is not killed, the duel ends, the mob's duel strength comes off
        step("duelLost", () -> {
            Zombie z2 = EntityType.ZOMBIE.create(lv);
            z2.moveTo(fp.getX() + 2.5, fp.getY(), fp.getZ(), 0F, 0F);
            z2.setNoAi(true);
            lv.addFreshEntity(z2);
            MADE.add(z2);
            boolean started = (Boolean) dmc.getMethod("start", ServerPlayer.class, LivingEntity.class).invoke(null, fp, z2);
            float buffed = z2.getMaxHealth();
            vulnerable = true;
            fp.invulnerableTime = 0;
            fp.hurt(fp.damageSources().mobAttack(z2), 1000F);
            vulnerable = false;
            Object duel = dmc.getMethod("duel", LivingEntity.class).invoke(null, fp);
            OUT.put("duelLost", started && fp.isAlive() && fp.getHealth() > 0F && duel == null);
            OUT.put("duelBuffRemoved", z2.getMaxHealth() < buffed || z2.isRemoved());
            fp.setHealth(fp.getMaxHealth());
        });

        // 9. the ledgers saved and read back the same
        step("ledgers", () -> {
            var reg = lv.registryAccess();
            boolean same = true;
            for (String n : new String[]{"BindingLedger", "SpiritLedger"}) {
                Class<?> c = Class.forName("jp.oror.dueldominion." + n);
                Object l = c.getMethod("forPlayer", ServerPlayer.class).invoke(null, fp);
                Method save = c.getMethod("save", CompoundTag.class, net.minecraft.core.HolderLookup.Provider.class);
                CompoundTag a = (CompoundTag) save.invoke(l, new CompoundTag(), reg);
                Object back = c.getMethod("load", CompoundTag.class, net.minecraft.core.HolderLookup.Provider.class).invoke(null, a, reg);
                CompoundTag b = (CompoundTag) save.invoke(back, new CompoundTag(), reg);
                same &= a.equals(b);
                OUT.put("ledger" + n, a.size() + "");
            }
            OUT.put("ledgersRoundTrip", same);
        });

        // 10. a duel between two players: both made whole, the loser not killed and not sealed
        step("pvp", () -> {
            FakePlayer fp2 = new FakePlayer(lv, new GameProfile(UUID.nameUUIDFromBytes("oror_duel_tester2".getBytes()), "[Duel Tester 2]")) {
                @Override
                public boolean isInvulnerableTo(net.minecraft.world.damagesource.DamageSource source) {
                    return !vulnerable && super.isInvulnerableTo(source);
                }

                @Override
                public boolean canHarmPlayer(net.minecraft.world.entity.player.Player other) {
                    return vulnerable || super.canHarmPlayer(other);
                }
            };
            unshield(fp2);
            fp2.moveTo(fp.getX() + 3.0, fp.getY(), fp.getZ() - 2.0, 0F, 0F);
            if (fp2.isCreative() || fp2.isSpectator()) {
                fp2.setGameMode(GameType.SURVIVAL);
            }
            fp2.setHealth(5F);
            int hairs = count(hair);
            boolean started = (Boolean) dmc.getMethod("start", ServerPlayer.class, LivingEntity.class).invoke(null, fp, fp2);
            boolean whole = fp2.getHealth() >= fp2.getMaxHealth() - 0.01F;
            vulnerable = true;
            fp2.invulnerableTime = 0;
            fp2.hurt(fp.damageSources().playerAttack(fp), 1000F);
            vulnerable = false;
            Object duel = dmc.getMethod("duel", LivingEntity.class).invoke(null, fp);
            OUT.put("pvpDuel", started && whole);
            OUT.put("pvpLoserAlive", fp2.getHealth() > 0F && duel == null);
            OUT.put("pvpNoCapture", count(hair) == hairs);
        });

        // 11. the grimoire takes the tester's own seal (the hair in the other hand)
        step("grimoire", () -> {
            ItemStack g = new ItemStack(item("dominion_grimoire"));
            ItemStack h = held(hair, "minecraft:zombie");
            if (h.isEmpty()) {
                h = held(hair, null);
            }
            int slot = fp.getInventory().findSlotMatchingItem(h);
            if (slot >= 0) {
                fp.getInventory().setItem(slot, ItemStack.EMPTY);
            }
            fp.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, g);
            fp.setItemInHand(net.minecraft.world.InteractionHand.OFF_HAND, h);
            g.use(lv, fp, net.minecraft.world.InteractionHand.MAIN_HAND);
            ItemStack after = fp.getItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND);
            CompoundTag gd = (CompoundTag) read.invoke(null, after);
            OUT.put("grimoireStored", fp.getItemInHand(net.minecraft.world.InteractionHand.OFF_HAND).isEmpty() && gd.getList("Entries", 10).size() == 1);
            fp.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            fp.setItemInHand(net.minecraft.world.InteractionHand.OFF_HAND, ItemStack.EMPTY);
        });

        // 12. the soul archive keeps an effigy and gives it back
        step("soulArchive", () -> {
            List<ItemStack> one = effigies(lv, 1);
            ItemStack token = one.isEmpty() ? ItemStack.EMPTY : one.get(0);
            int slot = fp.getInventory().findSlotMatchingItem(token);
            if (slot >= 0) {
                fp.getInventory().setItem(slot, ItemStack.EMPTY);
            }
            ItemStack a = new ItemStack(item("soul_archive"));
            fp.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, a);
            fp.setItemInHand(net.minecraft.world.InteractionHand.OFF_HAND, token);
            fp.setShiftKeyDown(false);
            a.use(lv, fp, net.minecraft.world.InteractionHand.MAIN_HAND);
            boolean stored = fp.getItemInHand(net.minecraft.world.InteractionHand.OFF_HAND).isEmpty();
            int before = count(item("spirit_effigy"));
            fp.setShiftKeyDown(true);
            fp.getItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND).use(lv, fp, net.minecraft.world.InteractionHand.MAIN_HAND);
            fp.setShiftKeyDown(false);
            OUT.put("soulArchiveStored", stored);
            OUT.put("soulArchiveReturned", count(item("spirit_effigy")) > before);
            fp.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, ItemStack.EMPTY);
        });

        // 13. the white glove thrown at a zombie (the duel begins where it lands; checked two seconds on)
        step("glove", () -> {
            Zombie g = EntityType.ZOMBIE.create(lv);
            g.moveTo(fp.getX(), fp.getY(), fp.getZ() + 4.0, 180F, 0F);
            g.setNoAi(true);
            lv.addFreshEntity(g);
            MADE.add(g);
            gloved = g;
            // (r71) onlookers about the duel: they should gather in a ring and cheer (DuelCrowd)
            EntityType<?>[] onlookers = {EntityType.VILLAGER, EntityType.VILLAGER, EntityType.PILLAGER, EntityType.COW};
            for (int i = 0; i < onlookers.length; i++) {
                Entity o = onlookers[i].create(lv);
                if (o != null) {
                    double ang = Math.PI * 2 * i / onlookers.length;
                    o.moveTo(fp.getX() + Math.cos(ang) * 11, fp.getY(), fp.getZ() + 2 + Math.sin(ang) * 11, 0F, 0F);
                    lv.addFreshEntity(o);
                    MADE.add(o);
                }
            }
            fp.lookAt(net.minecraft.commands.arguments.EntityAnchorArgument.Anchor.EYES, g.getEyePosition());
            ItemStack glove = new ItemStack(item("white_glove"));
            fp.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, glove);
            glove.use(lv, fp, net.minecraft.world.InteractionHand.MAIN_HAND);
            fp.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, ItemStack.EMPTY);
        });
    }

    /** (CI 38) a fake player never ticks: its sixty ticks of spawn protection never run out and no blow lands on it (as
     * KingStoryTest and RelicTest take them away). */
    /** The tester put in (or taken out of) the player list's UUID map only - what PlayerList.getPlayer reads - so code that
     * looks a player up by UUID finds it; the list of players itself (what is sent to, saved, ticked) is left alone. */
    @SuppressWarnings("unchecked")
    private static void listed(ServerLevel lv, boolean on) {
        if (fp == null || lv == null) {
            return;
        }
        try {
            java.lang.reflect.Field f = net.minecraft.server.players.PlayerList.class.getDeclaredField("playersByUUID");
            f.setAccessible(true);
            Map<UUID, ServerPlayer> m = (Map<UUID, ServerPlayer>) f.get(lv.getServer().getPlayerList());
            if (on) {
                m.putIfAbsent(fp.getUUID(), fp);
            } else {
                m.remove(fp.getUUID(), fp);
            }
        } catch (ReflectiveOperationException | RuntimeException ex) {
            LOG.warn("DUEL-TEST listed {}", ex.toString());
        }
    }

    private static void unshield(ServerPlayer p) {
        p.invulnerableTime = 0;
        try {
            java.lang.reflect.Field f = ServerPlayer.class.getDeclaredField("spawnInvulnerableTime");
            f.setAccessible(true);
            f.setInt(p, 0);
        } catch (ReflectiveOperationException | RuntimeException ex) {
            LOG.warn("DUEL-TEST unshield {}", ex.toString());
        }
    }

    /** The earliest revival time among the owner's bindings that wait (the ledger's own record, as it saves it). */
    private static long reviveAt(Object ledger, UUID owner) throws ReflectiveOperationException {
        CompoundTag t = (CompoundTag) ledger.getClass().getMethod("save", CompoundTag.class, net.minecraft.core.HolderLookup.Provider.class)
            .invoke(ledger, new CompoundTag(), level.registryAccess());
        long best = Long.MAX_VALUE;
        for (net.minecraft.nbt.Tag e : t.getList("Bindings", 10)) {
            CompoundTag c = (CompoundTag) e;
            if (c.hasUUID("Owner") && owner.equals(c.getUUID("Owner")) && c.getLong("ReviveAt") > 0L) {
                best = Math.min(best, c.getLong("ReviveAt"));
            }
        }
        return best;
    }

    private static int count(Item item) {
        int n = 0;
        for (ItemStack s : fp.getInventory().items) {
            if (s.is(item)) {
                n += s.getCount();
            }
        }
        for (ItemStack s : fp.getInventory().offhand) {
            if (s.is(item)) {
                n += s.getCount();
            }
        }
        return n;
    }

    /** Two seconds on: the glove's duel, a third party kept out of it, the duelist's own blows let in; then the zombie taken
     * far off (the duel should end on its own). */
    private static void glovePhase(ServerLevel lv) {
        step("gloveDuel", () -> {
            Class<?> dmc = Class.forName("jp.oror.dueldominion.DuelManager");
            Object duel = dmc.getMethod("duel", LivingEntity.class).invoke(null, fp);
            boolean withIt = duel != null && gloved != null && (dmc.getMethod("duel", LivingEntity.class).invoke(null, gloved) == duel);
            OUT.put("gloveDuel", withIt);
            OUT.put("crowdWatching", jp.oror.reborn.duel.DuelCrowd.watching(fp));
            OUT.put("crowdCheers", jp.oror.reborn.duel.DuelCrowd.cheers);
            if (!withIt) {
                return;
            }
            Zombie m = EntityType.ZOMBIE.create(lv);
            m.moveTo(gloved.getX() + 2.0, gloved.getY(), gloved.getZ(), 0F, 0F);
            m.setNoAi(true);
            lv.addFreshEntity(m);
            MADE.add(m);
            meddler = m;
            float h0 = gloved.getHealth();
            gloved.invulnerableTime = 0;
            gloved.hurt(lv.damageSources().mobAttack(m), 4F);
            float h1 = gloved.getHealth();
            gloved.invulnerableTime = 0;
            gloved.hurt(fp.damageSources().playerAttack(fp), 2F);
            float h2 = gloved.getHealth();
            OUT.put("interferenceBlocked", h1 >= h0);
            OUT.put("duelistBlowsCount", h2 < h1);
            gloved.teleportTo(gloved.getX() + 80.0, gloved.getY(), gloved.getZ());
        });
        check2At = lv.getGameTime() + 45;
    }

    /** The first stack of the item in the tester's inventory (of the god's kind when asked). */
    private static ItemStack held(Item item, String entity) throws ReflectiveOperationException {
        Method read = Class.forName("jp.oror.dueldominion.SealData").getMethod("read", ItemStack.class);
        for (ItemStack s : fp.getInventory().items) {
            if (s.is(item) && (entity == null || entity.equals(((CompoundTag) read.invoke(null, s)).getString("EntityId")))) {
                return s;
            }
        }
        return ItemStack.EMPTY;
    }

    private static Mob servant(EntityType<?> type) {
        UUID me = fp.getUUID();
        List<Mob> found = level.getEntitiesOfClass(Mob.class, fp.getBoundingBox().inflate(16), m -> m.getType() == type && m.isAlive()
            && m.getPersistentData().hasUUID("DuelDominionOwner") && me.equals(m.getPersistentData().getUUID("DuelDominionOwner")));
        if (!found.isEmpty()) {
            MADE.add(found.get(0));
        }
        return found.isEmpty() ? null : found.get(0);
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        if (level != null && runAt > 0 && level.getGameTime() >= runAt) {
            runAt = 0;
            try {
                run(level);
            } catch (Throwable ex) {
                OUT.put("error", "\"" + ex.toString().replace('"', '\'') + "\"");
                LOG.warn("DUEL-TEST failed with an exception", ex);
                finish();
                return;
            }
            checkAt = level.getGameTime() + 40;
            return;
        }
        if (level == null || level.getGameTime() < checkAt) {
            return;
        }
        if (check2At == Long.MAX_VALUE) {
            if (calledGod != null) {
                OUT.put("godAliveAfter2s", calledGod.isAlive() && !calledGod.isRemoved() && ((LivingEntity) calledGod).getHealth() > 0F);
                OUT.put("godRaidCleared", !Raid.active(calledGod));
            }
            glovePhase(level);
            checkAt = check2At;
            return;
        }
        step("duelEndsFar", () -> {
            Object duel = Class.forName("jp.oror.dueldominion.DuelManager").getMethod("duel", LivingEntity.class).invoke(null, fp);
            OUT.put("duelEndsFar", duel == null);
            // (r72) the zombie was carried off, the tester stayed: no flight of the tester's
            OUT.put("deserterNotWhenFoeCarried", !Deserters.marked(fp));
        });
        step("deserter", () -> deserterCheck(level));
        check2At = Long.MAX_VALUE;
        finish();
    }

    /**
     * (r72) The deserter's mark: the tester runs from a duel (out of its reach), and then every mob about it (a villager, a
     * cow, a zombie, a skeleton) is set on it, the zombie and the skeleton armed with the highest arms; a hunting party
     * comes; ten deaths and the world is satisfied.
     */
    private static void deserterCheck(ServerLevel lv) {
        Zombie z = EntityType.ZOMBIE.create(lv);
        z.moveTo(fp.getX(), fp.getY(), fp.getZ() + 4.0, 180F, 0F);
        z.setNoAi(true);
        lv.addFreshEntity(z);
        MADE.add(z);
        Deserters.begun(fp, z);
        net.minecraft.world.phys.Vec3 from = fp.position();
        fp.teleportTo(from.x + 70, from.y, from.z);
        Deserters.ended(fp, z, "距離超過により中断しました。");
        OUT.put("deserterMarked", Deserters.marked(fp));
        List<Mob> mobs = new ArrayList<>();
        EntityType<?>[] kinds = {EntityType.VILLAGER, EntityType.COW, EntityType.ZOMBIE, EntityType.SKELETON};
        for (int i = 0; i < kinds.length; i++) {
            if (kinds[i].create(lv) instanceof Mob m) {
                m.moveTo(fp.getX() + 6 * Math.cos(i * 1.6), fp.getY(), fp.getZ() + 6 * Math.sin(i * 1.6), 0F, 0F);
                lv.addFreshEntity(m);
                MADE.add(m);
                mobs.add(m);
            }
        }
        Deserters.hunt(fp, 40);
        OUT.put("deserterAllOnHim", mobs.stream().allMatch(m -> m.getTarget() == fp));
        boolean armed = mobs.get(2).getMainHandItem().is(net.minecraft.world.item.Items.NETHERITE_SWORD)
            && mobs.get(3).getMainHandItem().is(net.minecraft.world.item.Items.BOW) && mobs.get(3).getMainHandItem().isEnchanted()
            && mobs.get(2).getItemBySlot(net.minecraft.world.entity.EquipmentSlot.CHEST).is(net.minecraft.world.item.Items.NETHERITE_CHESTPLATE);
        OUT.put("deserterArmed", armed);
        int before = Deserters.parties;
        Deserters.party(fp, 4, 5, 9);
        int hunters = lv.getEntitiesOfClass(Mob.class, fp.getBoundingBox().inflate(12), m -> m.getTags().contains(Deserters.HUNTER)).size();
        OUT.put("deserterParty", hunters);
        for (Mob m : lv.getEntitiesOfClass(Mob.class, fp.getBoundingBox().inflate(12), m -> m.getTags().contains(Deserters.HUNTER))) {
            MADE.add(m);
        }
        for (int i = 0; i < Deserters.DEATHS - 1; i++) {
            Deserters.died(new net.neoforged.neoforge.event.entity.living.LivingDeathEvent(fp, lv.damageSources().generic()));
        }
        boolean stillAfterNine = Deserters.marked(fp) && Deserters.deathsLeft(fp) == 1;
        Deserters.died(new net.neoforged.neoforge.event.entity.living.LivingDeathEvent(fp, lv.damageSources().generic()));
        OUT.put("deserterSatisfiedAfterTen", stillAfterNine && !Deserters.marked(fp));
        OUT.put("deserterPartyCame", Deserters.parties > before);
        fp.teleportTo(from.x, from.y, from.z);
    }

    private static void finish() {
        boolean pass = OUT.containsKey("error") ? false
            : ok("duelStarted") && ok("zombieSealed") && ok("sealMade") && ok("calledOut") && ok("calledBack") && ok("godDuel")
            && ok("godRaid") && ok("godSealed") && ok("godCalledOut") && ok("godAliveAfter2s") && ok("nightParade") && ok("healing")
            && Integer.valueOf(4).equals(OUT.get("effigies"))
            // (059g) the rest of Duel Dominion
            && OUT.keySet().stream().noneMatch(k -> k.startsWith("err_"))
            && ok("retribution") && ok("guardian") && ok("binding") && ok("maliceTransfer") && ok("soulSeeker") && ok("exorcism")
            && ok("calamity") && ok("possession") && ok("possessionRestored") && ok("fusion") && ok("fusionRestored")
            && ok("logoutWhileFused") && ok("crashWhileFused") && ok("revival") && ok("duelLost") && ok("duelBuffRemoved")
            && ok("ledgersRoundTrip") && ok("pvpDuel") && ok("pvpLoserAlive") && ok("pvpNoCapture") && ok("grimoireStored")
            && ok("soulArchiveStored") && ok("soulArchiveReturned") && ok("gloveDuel") && ok("interferenceBlocked")
            && ok("duelistBlowsCount") && ok("duelEndsFar") && ok("clickPossess") && ok("noDropsOnServantDeath")
            && ok("clickFuse") && ok("fusionFollows") && ok("clickFuseRestored") && ok("fusionHostDeath") && ok("fusionEndsOnHostDeath")
            && ok("fusionHostDeathOwnerFalls")
            // (r71) the onlookers gathered about the glove's duel
            && OUT.get("crowdWatching") instanceof Integer w && w >= 3
            // (r72) the deserter's mark
            && ok("deserterNotWhenFoeCarried") && ok("deserterMarked") && ok("deserterAllOnHim") && ok("deserterArmed") && ok("deserterSatisfiedAfterTen")
            && OUT.get("deserterParty") instanceof Integer hp && hp >= 1;
        StringBuilder s = new StringBuilder("{\"present\":true");
        for (Map.Entry<String, Object> en : OUT.entrySet()) {
            s.append(",\"").append(en.getKey()).append("\":").append(en.getValue());
        }
        s.append(",\"said\":[");
        for (int i = 0; i < SAID.size() && i < 80; i++) {
            s.append(i == 0 ? "" : ",").append('"').append(SAID.get(i).replace("\\", "/").replace('"', '\'').replace('\n', ' ')).append('"');
        }
        s.append(']');
        s.append(",\"pass\":").append(pass).append('}');
        LOG.info("DUEL-RESULT " + s);
        for (Entity x : MADE) {
            if (!x.isRemoved()) {
                x.discard();
            }
        }
        listed(level, false);
        if (level != null) {
            for (ChunkPos p : FORCED) {
                level.setChunkForced(p.x, p.z, false);
            }
        }
        FORCED.clear();
        level = null;
        calledGod = null;
        gloved = null;
        meddler = null;
        check2At = Long.MAX_VALUE;
        resultLogged = true;
    }

    private static boolean ok(String k) {
        return Boolean.TRUE.equals(OUT.get(k));
    }
}
