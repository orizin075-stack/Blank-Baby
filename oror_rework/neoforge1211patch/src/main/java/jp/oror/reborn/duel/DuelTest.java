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
 * Possession is not run: it moves the player's camera, which a fake player (no client) cannot follow.
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
        };
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
        if (calledGod != null) {
            OUT.put("godAliveAfter2s", calledGod.isAlive() && !calledGod.isRemoved() && ((LivingEntity) calledGod).getHealth() > 0F);
            OUT.put("godRaidCleared", !Raid.active(calledGod));
        }
        finish();
    }

    private static void finish() {
        boolean pass = OUT.containsKey("error") ? false
            : ok("duelStarted") && ok("zombieSealed") && ok("sealMade") && ok("calledOut") && ok("calledBack") && ok("godDuel")
            && ok("godRaid") && ok("godSealed") && ok("godCalledOut") && ok("godAliveAfter2s") && ok("nightParade") && ok("healing")
            && Integer.valueOf(4).equals(OUT.get("effigies"));
        StringBuilder s = new StringBuilder("{\"present\":true");
        for (Map.Entry<String, Object> en : OUT.entrySet()) {
            s.append(",\"").append(en.getKey()).append("\":").append(en.getValue());
        }
        s.append(",\"said\":[");
        for (int i = 0; i < SAID.size() && i < 40; i++) {
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
        if (level != null) {
            for (ChunkPos p : FORCED) {
                level.setChunkForced(p.x, p.z, false);
            }
        }
        FORCED.clear();
        level = null;
        calledGod = null;
        resultLogged = true;
    }

    private static boolean ok(String k) {
        return Boolean.TRUE.equals(OUT.get(k));
    }
}
