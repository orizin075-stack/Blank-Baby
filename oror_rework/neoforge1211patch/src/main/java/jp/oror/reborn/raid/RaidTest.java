package jp.oror.reborn.raid;

import com.mojang.authlib.GameProfile;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;
import jp.oror.reborn.CharacterRelics;
import jp.oror.reborn.OrorReborn;
import jp.oror.reborn.RelicSpec;
import jp.oror.reborn.SupremeEntity;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (059e) CI check "raid" (/oror raid test), the user: "体力面増やすテストはやった？". The kill time of each of the 41 gods
 * in a raid, measured in game time through the god's real hurt (its armour, its lore's reductions as they stand in a
 * raid, the raid's guard, caps and second rising):
 * <ul>
 * <li>"通常武器": a netherite sword with Sharpness V, one player;</li>
 * <li>"神具": the god's own relic weapon (oror_supreme_bosses:&lt;id&gt;_weapon), one player;</li>
 * <li>"レジェンド": the god's legend weapon (&lt;id&gt;_legend) and, every five seconds, a technique of a million damage
 * (the weapons' "100万級"), by one, two and four players.</li>
 * </ul>
 * Each blow is the weapon's full-charge damage (its attribute modifiers and enchantments, as Player.attack makes it,
 * without critical hits), at the weapon's attack speed, from fake players (several players' blows meet the god's
 * hurt immunity as in a real fight). The gods stand without their AI (their own techniques, flight and healing are not
 * in this measure; the raid's caps and guard are). The test runs the server at full speed (/tick sprint) for at most
 * twelve game minutes; a fight not ended by then gets an estimate from the damage done so far (marked).
 * <p>
 * Pass: every legend fight ends with the god dead (no god stays unbeatable, no endless rising), no solo legend kill under
 * a minute (a million-damage blow does not end a raid), outside a raid the lore is as it was (a mob's blow on an
 * ABSOLUTE god does nothing and starts no raid), and the raid health survives a save and load.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class RaidTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Raid");
    public static volatile boolean resultLogged;
    private static final long LIMIT = 14400;
    private static final int ART_GAP = 100;
    private static final float ART = 1_000_000F;

    private static final class Sim {
        final String id;
        final String tier;
        final int group;
        SupremeEntity god;
        float blow;
        int gap;
        long[] next;
        long artNext;
        long done = -1;
        boolean dead;
        float max;
        int rose;

        Sim(String id, String tier, int group) {
            this.id = id;
            this.tier = tier;
            this.group = group;
        }
    }

    private static ServerLevel level;
    private static final List<Sim> SIMS = new ArrayList<>();
    private static final List<ChunkPos> FORCED = new ArrayList<>();
    private static FakePlayer[] fighters;
    private static long started;
    private static boolean wasEnabled;
    private static final Map<String, Object> CHECKS = new LinkedHashMap<>();
    private static BlockPos origin;

    private RaidTest() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("raid").then(Commands.literal("test")
            .requires(s -> s.hasPermission(2)).executes(c -> start(c.getSource())))));
    }

    private static int start(CommandSourceStack src) {
        ServerLevel lv = src.getServer().overworld();
        level = lv;
        SIMS.clear();
        CHECKS.clear();
        wasEnabled = Raid.enabled();
        Raid.enable(src.getServer(), true);
        origin = BlockPos.containing(src.getPosition()).offset(-2400, 0, 2400);
        origin = new BlockPos(origin.getX() & ~15, 120, origin.getZ() & ~15);
        for (int dx = -1; dx <= 6; dx++) {
            for (int dz = -1; dz <= 6; dz++) {
                ChunkPos p = new ChunkPos((origin.getX() >> 4) + dx, (origin.getZ() >> 4) + dz);
                if (lv.setChunkForced(p.x, p.z, true)) {
                    FORCED.add(p);
                }
            }
        }
        fighters = new FakePlayer[4];
        for (int i = 0; i < 4; i++) {
            fighters[i] = FakePlayerFactory.get(lv, new GameProfile(UUID.nameUUIDFromBytes(("oror_raid_" + i).getBytes()), "[Raid " + (i + 1) + "]"));
            fighters[i].moveTo(origin.getX() - 8 - i, origin.getY(), origin.getZ() - 8);
        }
        // the lore unchanged outside a raid: a mob's blow on an ABSOLUTE god
        controls(lv);
        int n = 0;
        for (RaidTable.Entry t : RaidTable.ALL.values()) {
            for (Object[] f : new Object[][]{{"通常武器", 1}, {"神具", 1}, {"レジェンド", 1}, {"レジェンド", 2}, {"レジェンド", 4}}) {
                Sim s = new Sim(t.id(), (String) f[0], (Integer) f[1]);
                // six by six in a chunk square of 96, eight floors 32 apart
                int col = n % 36, floor = n / 36;
                BlockPos at = origin.offset(8 + (col % 6) * 16, floor * 32, 8 + (col / 6) * 16);
                n++;
                if (!spawn(lv, s, at)) {
                    LOG.info("RAID-GOD {\"id\":\"{}\",\"tier\":\"{}\",\"made\":false}", s.id, s.tier);
                    continue;
                }
                SIMS.add(s);
            }
        }
        started = lv.getGameTime();
        for (Sim s : SIMS) {
            s.next = new long[s.group];
            for (int k = 0; k < s.group; k++) {
                s.next[k] = started + 1 + (long) k * Math.max(1, s.gap / s.group);
            }
            s.artNext = started + 20;
        }
        LOG.info("RAID-START {} fights at {}", SIMS.size(), origin.toShortString());
        src.getServer().tickRateManager().requestGameToSprint((int) LIMIT + 200);
        return 1;
    }

    private static boolean spawn(ServerLevel lv, Sim s, BlockPos at) {
        var holder = OrorReborn.TYPES.get(s.id);
        SupremeEntity b = holder == null ? null : holder.get().create(lv);
        if (b == null) {
            return false;
        }
        b.moveTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5, 0F, 0F);
        b.setNoAi(true);
        b.setPersistenceRequired();
        lv.addFreshEntity(b);
        s.god = b;
        ItemStack weapon = switch (s.tier) {
            case "通常武器" -> sharpSword(lv);
            case "神具" -> relic(s.id + "_weapon");
            default -> relic(s.id + "_legend");
        };
        DamageSource src = fighters[0].damageSources().playerAttack(fighters[0]);
        float[] w = blow(lv, weapon, b, src);
        s.blow = w[0];
        s.gap = (int) w[1];
        RaidTable.Entry t = RaidTable.of(s.id);
        s.max = t.health();
        return true;
    }

    private static ItemStack sharpSword(ServerLevel lv) {
        ItemStack sword = new ItemStack(Items.NETHERITE_SWORD);
        lv.registryAccess().registryOrThrow(Registries.ENCHANTMENT).getHolder(Enchantments.SHARPNESS).ifPresent(h -> sword.enchant(h, 5));
        return sword;
    }

    private static ItemStack relic(String path) {
        return BuiltInRegistries.ITEM.getOptional(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", path)).map(ItemStack::new)
            .orElse(ItemStack.EMPTY);
    }

    /**
     * The weapon's full-charge blow and its gap in ticks: Player.attack's damage (base 1 and the weapon's modifiers,
     * then its enchantments), its attack speed (base 4). A relic without a melee modifier (a bow, a shield) strikes for
     * its own damage (CharacterRelics: (damage + 4) x the rank's power) once a second.
     */
    static float[] blow(ServerLevel lv, ItemStack stack, SupremeEntity target, DamageSource src) {
        double[] dmg = {1.0, 0.0, 1.0};
        double[] spd = {4.0, 0.0, 1.0};
        boolean[] melee = {false};
        stack.forEachModifier(EquipmentSlot.MAINHAND, (a, m) -> {
            double[] v = a.value() == Attributes.ATTACK_DAMAGE.value() ? dmg : a.value() == Attributes.ATTACK_SPEED.value() ? spd : null;
            if (v == null) {
                return;
            }
            if (v == dmg) {
                melee[0] = true;
            }
            if (m.operation() == AttributeModifier.Operation.ADD_VALUE) {
                v[0] += m.amount();
            } else if (m.operation() == AttributeModifier.Operation.ADD_MULTIPLIED_BASE) {
                v[1] += m.amount();
            } else {
                v[2] *= 1.0 + m.amount();
            }
        });
        float base;
        int gap;
        if (melee[0]) {
            base = (float) (dmg[0] * (1.0 + dmg[1]) * dmg[2]);
            double speed = Math.max(0.25, spd[0] * (1.0 + spd[1]) * spd[2]);
            gap = (int) Math.max(4, Math.round(20.0 / speed));
        } else {
            RelicSpec r = CharacterRelics.of(stack);
            base = r == null ? 1F : (r.damage + 4F) * (r.rank >= 3 ? 4F : r.rank == 2 ? 3.5F : 3F);
            gap = 20;
        }
        float full = EnchantmentHelper.modifyDamage(lv, stack, target, src, base);
        return new float[]{full, gap};
    }

    /** Outside a raid the lore is as it was; the raid health survives a save. */
    private static void controls(ServerLevel lv) {
        var holder = OrorReborn.TYPES.get("riha");
        SupremeEntity riha = holder == null ? null : holder.get().create(lv);
        Zombie z = EntityType.ZOMBIE.create(lv);
        if (riha != null && z != null) {
            riha.moveTo(origin.getX() - 20.5, origin.getY(), origin.getZ() - 20.5, 0F, 0F);
            riha.setNoAi(true);
            lv.addFreshEntity(riha);
            z.moveTo(origin.getX() - 22.5, origin.getY(), origin.getZ() - 20.5, 0F, 0F);
            z.setNoAi(true);
            lv.addFreshEntity(z);
            float h0 = riha.getHealth();
            boolean lore = riha.lore();
            riha.hurt(riha.damageSources().mobAttack(z), 1000F);
            CHECKS.put("loreMode", lore);
            CHECKS.put("mobBlowNoRaid", !Raid.active(riha));
            CHECKS.put("mobBlowLoreKept", !lore || riha.getHealth() >= h0);
            // a player's blow starts the raid, and a save keeps it
            riha.invulnerableTime = 0;
            riha.hurt(fighters[0].damageSources().playerAttack(fighters[0]), 200F);
            CHECKS.put("playerBlowRaid", Raid.active(riha));
            float hp = Raid.health(riha);
            CHECKS.put("raidHealthAfterBlow", Math.round(hp));
            CompoundTag saved = new CompoundTag();
            riha.saveWithoutId(saved);
            SupremeEntity back = holder.get().create(lv);
            boolean kept = false;
            if (back != null) {
                back.load(saved);
                kept = Raid.active(back) && Math.abs(Raid.health(back) - hp) < 0.5F && Raid.max(back) == RaidTable.of("riha").health();
            }
            CHECKS.put("savedAndLoaded", kept);
            CHECKS.put("controlsPass", (!lore || (Boolean) CHECKS.get("mobBlowLoreKept")) && (Boolean) CHECKS.get("mobBlowNoRaid")
                && (!lore || (Boolean) CHECKS.get("playerBlowRaid")) && (!lore || kept));
            riha.discard();
            z.discard();
        } else {
            CHECKS.put("controlsPass", false);
        }
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        if (level == null) {
            return;
        }
        long now = level.getGameTime();
        long t = now - started;
        boolean open = false;
        for (Sim s : SIMS) {
            if (s.done >= 0) {
                continue;
            }
            SupremeEntity b = s.god;
            if (b == null || b.isRemoved() || b.isDeadOrDying()) {
                s.done = t;
                s.dead = b != null && (b.isDeadOrDying() || b.isRemoved()) && Raid.slainInRaid(b);
                s.rose = b == null ? 0 : Raid.state(b).getInt("Rose");
                report(s, false);
                continue;
            }
            open = true;
            for (int k = 0; k < s.group; k++) {
                if (now >= s.next[k]) {
                    s.next[k] += s.gap;
                    b.hurt(fighters[k].damageSources().playerAttack(fighters[k]), s.blow);
                }
            }
            if (s.tier.equals("レジェンド") && now >= s.artNext) {
                s.artNext += ART_GAP;
                b.invulnerableTime = 0;
                b.hurt(fighters[0].damageSources().playerAttack(fighters[0]), ART);
            }
        }
        if (open && t < LIMIT) {
            return;
        }
        // the end: estimates for the fights still open
        for (Sim s : SIMS) {
            if (s.done < 0) {
                s.rose = Raid.state(s.god).getInt("Rose");
                report(s, true);
            }
        }
        summary(t);
        level.getServer().tickRateManager().stopSprinting();
        for (Sim s : SIMS) {
            if (s.god != null && !s.god.isRemoved()) {
                s.god.discard();
            }
        }
        AABB box = new AABB(origin).inflate(160, 300, 160).move(48, 0, 48);
        level.getEntitiesOfClass(ItemEntity.class, box).forEach(ItemEntity::discard);
        level.getEntitiesOfClass(net.minecraft.world.entity.ExperienceOrb.class, box).forEach(net.minecraft.world.entity.ExperienceOrb::discard);
        for (ChunkPos p : FORCED) {
            level.setChunkForced(p.x, p.z, false);
        }
        FORCED.clear();
        Raid.enable(level.getServer(), wasEnabled);
        level = null;
        resultLogged = true;
    }

    private static final Map<String, double[]> SECONDS = new LinkedHashMap<>();

    private static void report(Sim s, boolean open) {
        CompoundTag st = s.god == null ? new CompoundTag() : Raid.state(s.god);
        double secs;
        boolean estimated = false;
        if (!open) {
            secs = s.done / 20.0;
        } else {
            float dealt = st.getFloat("Dealt");
            float need = s.max * (Raid.IMMORTAL.contains(s.id) ? 1F + Raid.REVIVE : 1F);
            long t = level.getGameTime() - started;
            secs = dealt > 0F ? t / 20.0 * need / dealt : -1;
            estimated = true;
        }
        SECONDS.computeIfAbsent(s.id, k -> new double[]{-1, -1, -1, -1, -1})[slot(s)] = estimated ? -secs : secs;
        LOG.info(String.format(Locale.ROOT, "RAID-GOD {\"id\":\"%s\",\"tier\":\"%s\",\"players\":%d,\"hp\":%.0f,\"blow\":%.1f,\"gapTicks\":%d,"
                + "\"seconds\":%.1f,\"minutes\":%.2f,\"estimated\":%b,\"dead\":%b,\"rose\":%d,\"dealt\":%.0f,\"healed\":%.0f}",
            s.id, s.tier, s.group, s.max, s.blow, s.gap, secs, secs / 60.0, estimated, s.dead, s.rose, st.getFloat("Dealt"), st.getFloat("Healed")));
    }

    private static int slot(Sim s) {
        return switch (s.tier) {
            case "通常武器" -> 0;
            case "神具" -> 1;
            default -> s.group == 1 ? 2 : s.group == 2 ? 3 : 4;
        };
    }

    private static void summary(long t) {
        int legendFights = 0, legendDead = 0, soloInTarget = 0, groupInTarget = 0, groupFights = 0, tooFast = 0;
        double minSolo = 1e9, maxSolo = 0, min4 = 1e9, max4 = 0;
        for (Sim s : SIMS) {
            if (!s.tier.equals("レジェンド")) {
                continue;
            }
            legendFights++;
            boolean finished = s.done >= 0;
            legendDead += finished && s.dead ? 1 : 0;
            double sec = finished ? s.done / 20.0 : Double.NaN;
            if (s.group == 1 && finished) {
                minSolo = Math.min(minSolo, sec);
                maxSolo = Math.max(maxSolo, sec);
                soloInTarget += sec >= 180 && sec <= 480 ? 1 : 0;
                tooFast += sec < 60 ? 1 : 0;
            } else if (s.group > 1) {
                groupFights++;
                if (finished) {
                    groupInTarget += sec >= 120 && sec <= 300 ? 1 : 0;
                    if (s.group == 4) {
                        min4 = Math.min(min4, sec);
                        max4 = Math.max(max4, sec);
                    }
                }
            }
        }
        boolean controls = Boolean.TRUE.equals(CHECKS.get("controlsPass"));
        boolean pass = SIMS.size() == RaidTable.ALL.size() * 5 && legendDead == legendFights && tooFast == 0 && controls;
        StringBuilder table = new StringBuilder();
        for (Map.Entry<String, double[]> en : SECONDS.entrySet()) {
            double[] v = en.getValue();
            table.append(String.format(Locale.ROOT, "%s:%s/%s/%s/%s/%s ", en.getKey(), m(v[0]), m(v[1]), m(v[2]), m(v[3]), m(v[4])));
        }
        LOG.info("RAID-TABLE minutes 通常武器/神具/レジェンド1人/2人/4人 (~ = estimate) " + table.toString().trim());
        LOG.info(String.format(Locale.ROOT, "RAID-RESULT {\"fights\":%d,\"gameSeconds\":%.0f,\"legendFights\":%d,\"legendDead\":%d,"
                + "\"soloMinutes\":[%.1f,%.1f],\"soloIn3to8\":%d,\"fourMinutes\":[%.1f,%.1f],\"groupIn2to5\":%d,\"groupFights\":%d,"
                + "\"underAMinute\":%d,\"started\":%d,\"broken\":%d,\"rose\":%d,\"slain\":%d,\"checks\":%s,\"pass\":%b}",
            SIMS.size(), t / 20.0, legendFights, legendDead, minSolo / 60, maxSolo / 60, soloInTarget, min4 / 60, max4 / 60, groupInTarget,
            groupFights, tooFast, Raid.started, Raid.broken, Raid.revived, Raid.slain, json(CHECKS), pass));
    }

    private static String m(double sec) {
        if (sec == -1) {
            return "-";
        }
        return sec < 0 ? String.format(Locale.ROOT, "~%.1f", -sec / 60) : String.format(Locale.ROOT, "%.1f", sec / 60);
    }

    private static String json(Map<String, Object> m) {
        StringBuilder s = new StringBuilder("{");
        for (Map.Entry<String, Object> e : m.entrySet()) {
            if (s.length() > 1) {
                s.append(',');
            }
            s.append('"').append(e.getKey()).append("\":").append(e.getValue());
        }
        return s.append('}').toString();
    }
}
