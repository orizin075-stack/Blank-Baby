package jp.oror.reborn.waza;

import com.mojang.authlib.GameProfile;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import jp.oror.reborn.OrorReborn;
import jp.oror.reborn.SupremeEntity;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Arrow;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (057) The CI check of the 984 techniques (/oror waza test, CiDriver's "waza"): each of the 41 characters in its own
 * walled-off yard, all at once, runs its 24 techniques in turn against a dummy that takes every blow and never dies
 * (the blows are counted, then refused), and each technique is judged by what its behaviour is for. Every one must
 * pass through TELEGRAPH, ACTIVE and RECOVERY to its cooldown without being cut short, fire each of its hits, and:
 * a melee cut, a shot, a beam, a field, a ring of sound, a growth, a curse's delivery, a hold, a summons' volley must
 * reach the dummy; a move must move its caster to a place with footing; a guard must stand and stop an arrow from the
 * front; a status must leave something on the dummy; a heal must heal its caster and not the dummy; a device must be
 * built and set to work; a rewind must give back health or place; learning must answer the blow it has seen (twice)
 * and not one it has not; a contract must be offered, cost nothing to the player who refuses, and give (and later
 * take) only from the one who agrees. One line per technique (WAZA-TRY), and the whole (WAZA-RESULT).
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class WazaTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Waza");
    public static volatile boolean resultLogged;

    static final class Signer extends FakePlayer {
        Signer(ServerLevel level, int n) {
            super(level, new GameProfile(UUID.fromString("0a0b0c0d-0e0f-4a1b-8c2d-3e4f5a6b7c" + String.format("%02x", n)), "[OROR Pact " + n + "]"));
        }
    }

    private static final class Yard {
        String character;
        BlockPos at;
        SupremeEntity b;
        Mob dummy;
        int next;
        WazaEngine.Cast cast;
        long phaseAt;
        int stage; // 0 prepare, 1 running, 2 settling, 3 done
        Vec3 startPos;
        float healthBefore, dummyHealthBefore;
        int effectsBefore;
        int hitsAtStart;
        int maxDeviceStage = -1;
        boolean guardSeen, statusSeen;
        int effectsMax;
        float guardStrength = -1;
        Arrow arrow;
        Signer agree, refuse;
        final List<int[]> chunks = new ArrayList<>();
    }

    private static final List<Yard> YARDS = new ArrayList<>();
    private static final Map<Integer, Integer> DUMMY_HITS = new HashMap<>();
    private static final Map<String, int[]> TALLY = new LinkedHashMap<>();
    /** blows on the dummies that were not the techniques' own (kinds and sources), for the record */
    private static final Map<String, Integer> OTHER = new HashMap<>();
    private static final List<String> FAILED = new ArrayList<>();
    private static int tried, passed;
    private static long started = -1;

    private WazaTest() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("waza").then(Commands.literal("test")
            .requires(s -> s.hasPermission(2)).executes(c -> start(c.getSource())))));
    }

    /** The players a character in a yard may offer a contract to (fake players are not in the level's list). */
    static List<ServerPlayer> signers(SupremeEntity b) {
        for (Yard y : YARDS) {
            if (y.b == b && y.agree != null) {
                return List.of(y.agree, y.refuse);
            }
        }
        return List.of();
    }

    private static int start(CommandSourceStack src) {
        if (started >= 0) {
            return 0;
        }
        ServerLevel level = src.getServer().overworld();
        BlockPos o = BlockPos.containing(src.getPosition()).offset(6000, 0, -6000);
        int i = 0;
        TALLY.clear();
        FAILED.clear();
        OTHER.clear();
        tried = passed = 0;
        for (String id : Waza.BY_CHARACTER.keySet()) {
            Yard y = new Yard();
            y.character = id;
            // a yard of three chunks by three, centred in its middle chunk (as little new land as will do: the
            // first 057 run's 41 five-by-five yards were followed by an Ice and Fire world-generation crash)
            BlockPos c0 = o.offset((i % 7) * 96, 0, (i / 7) * 96);
            BlockPos c = new BlockPos(((c0.getX() >> 4) << 4) + 8, 0, ((c0.getZ() >> 4) << 4) + 8);
            i++;
            for (int dx = -1; dx <= 1; dx++) {
                for (int dz = -1; dz <= 1; dz++) {
                    int cx = (c.getX() >> 4) + dx, cz = (c.getZ() >> 4) + dz;
                    level.setChunkForced(cx, cz, true);
                    y.chunks.add(new int[]{cx, cz});
                }
            }
            int ground = Math.max(level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, c.getX(), c.getZ()), level.getSeaLevel() + 1) + 4;
            y.at = new BlockPos(c.getX(), ground, c.getZ());
            for (int dx = -23; dx <= 23; dx++) {
                for (int dz = -23; dz <= 23; dz++) {
                    level.setBlock(y.at.offset(dx, -1, dz), Blocks.STONE.defaultBlockState(), 2);
                    for (int h = 0; h < 14; h++) {
                        level.setBlock(y.at.offset(dx, h, dz), Blocks.AIR.defaultBlockState(), 2);
                    }
                }
            }
            YARDS.add(y);
        }
        started = level.getGameTime();
        LOG.info("WAZA-START {} yards at {}", YARDS.size(), o);
        return 1;
    }

    private static SupremeEntity spawnCaster(ServerLevel level, Yard y) {
        var holder = OrorReborn.TYPES.get(y.character);
        if (holder == null) {
            return null;
        }
        SupremeEntity b = holder.get().create(level);
        if (b == null) {
            return null;
        }
        b.moveTo(y.at.getX() + 0.5, y.at.getY() + (b.spec.airborne() ? 1 : 0), y.at.getZ() + 0.5, 0F, 0F);
        b.setPersistenceRequired();
        level.addFreshEntity(b);
        WazaEngine.testMode(b, true);
        return b;
    }

    private static Mob spawnDummy(ServerLevel level, Yard y, double dist) {
        Mob m = EntityType.HUSK.create(level);
        if (m == null) {
            return null;
        }
        m.moveTo(y.at.getX() + 0.5, y.at.getY(), y.at.getZ() + 0.5 + dist, 180F, 0F);
        m.finalizeSpawn(level, level.getCurrentDifficultyAt(m.blockPosition()), MobSpawnType.COMMAND, null);
        m.setPersistenceRequired();
        m.setNoAi(true);
        m.addTag("oror_waza_dummy");
        level.addFreshEntity(m);
        return m;
    }

    /** The dummy's blows are counted and refused (it stays put and alive for the next technique). */
    static void incoming(LivingIncomingDamageEvent e) {
        if (started < 0) {
            return;
        }
        if (e.getEntity().getTags().contains("oror_waza_dummy")) {
            DUMMY_HITS.merge(e.getEntity().getId(), 1, Integer::sum);
            if (!WazaActs.striking) {
                Entity by = e.getSource().getEntity();
                OTHER.merge(e.getSource().getMsgId() + "/" + (by == null ? "-" : by.getType().toShortString()), 1, Integer::sum);
            }
            e.setCanceled(true);
        }
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        if (started < 0 || YARDS.isEmpty()) {
            return;
        }
        ServerLevel level = e.getServer().overworld();
        long now = level.getGameTime();
        boolean all = true;
        for (Yard y : YARDS) {
            try {
                step(level, y, now);
            } catch (RuntimeException ex) {
                LOG.error("WAZA-ERROR " + y.character + " " + y.next, ex);
                record(y, false, "error:" + ex);
                y.next++;
                y.stage = 0;
                y.phaseAt = now;
            }
            all &= y.stage == 3;
        }
        if (all || now - started > 12000) {
            finish(level, now);
        }
    }

    private static double dummyDistance(SupremeEntity b, Waza w) {
        return switch (w.behaviour()) {
            case MELEE -> Math.max(1.2, w.range() * 0.6) + b.getBbWidth() * 0.5;
            case GROWTH, FIELD -> 4 + b.getBbWidth() * 0.25;
            default -> 5 + b.getBbWidth() * 0.25;
        };
    }

    private static void step(ServerLevel level, Yard y, long now) {
        if (y.stage == 3) {
            return;
        }
        List<Waza> list = Waza.BY_CHARACTER.get(y.character);
        if (y.next >= list.size()) {
            y.stage = 3;
            cleanup(y);
            return;
        }
        Waza w = list.get(y.next);
        if (y.stage == 0) {
            if (y.phaseAt == 0) {
                y.phaseAt = now;
            }
            if (y.b == null || !y.b.isAlive()) {
                y.b = spawnCaster(level, y);
                if (y.b == null) {
                    record(y, false, "no-caster");
                    y.next = list.size();
                    return;
                }
            }
            if (y.agree == null && list.stream().anyMatch(x -> x.behaviour() == Waza.Behaviour.PACT)) {
                y.agree = new Signer(level, 1);
                y.refuse = new Signer(level, 2);
                y.agree.moveTo(y.at.getX() - 3.5, y.at.getY(), y.at.getZ() - 2.5, 0F, 0F);
                y.refuse.moveTo(y.at.getX() + 3.5, y.at.getY(), y.at.getZ() - 2.5, 0F, 0F);
            }
            long waited = now - y.phaseAt;
            int prep = w.behaviour() == Waza.Behaviour.REWIND ? 120 : 12;
            if (waited == 1) {
                // a fresh start: home, whole, the dummy in front at the technique's reach
                y.b.teleportTo(y.at.getX() + 0.5, y.at.getY() + (y.b.spec.airborne() ? 1 : 0), y.at.getZ() + 0.5);
                y.b.setDeltaMovement(Vec3.ZERO);
                y.b.setHealth(y.b.getMaxHealth());
                y.b.removeAllEffects();
                y.b.getPersistentData().putLong("ororFreezeUntil", 0);
                if (y.dummy != null) {
                    y.dummy.discard();
                }
                y.dummy = spawnDummy(level, y, dummyDistance(y.b, w));
                y.b.setTarget(y.dummy);
                y.b.lookAt(y.dummy, 360, 360);
            }
            if (waited == 8 && w.behaviour() == Waza.Behaviour.ADAPT) {
                // two blows of one kind seen, so that learning has something to answer
                WazaWorld.forgetLearning(y.b);
                y.b.invulnerableTime = 0;
                y.b.hurt(level.damageSources().mobAttack(y.dummy), 1);
                y.b.invulnerableTime = 0;
                y.b.hurt(level.damageSources().mobAttack(y.dummy), 1);
            }
            if (waited == prep - 2 && w.behaviour() == Waza.Behaviour.REWIND) {
                y.b.setHealth(y.b.getMaxHealth() * 0.5F);
            }
            if (waited >= prep && y.dummy != null) {
                if (w.behaviour() == Waza.Behaviour.HEAL) {
                    y.b.setHealth(y.b.getMaxHealth() * 0.5F);
                    y.dummy.setHealth(y.dummy.getMaxHealth() * 0.5F);
                }
                y.startPos = y.b.position();
                y.healthBefore = y.b.getHealth();
                y.dummyHealthBefore = y.dummy.getHealth();
                y.effectsBefore = y.dummy.getActiveEffects().size();
                y.hitsAtStart = DUMMY_HITS.getOrDefault(y.dummy.getId(), 0);
                y.maxDeviceStage = -1;
                y.guardSeen = false;
                y.statusSeen = false;
                y.effectsMax = y.effectsBefore;
                y.guardStrength = -1;
                y.arrow = null;
                y.cast = WazaEngine.start(y.b, w, y.dummy, true);
                y.stage = 1;
                y.phaseAt = now;
            }
            return;
        }
        WazaEngine.Cast c = y.cast;
        int e = (int) (now - c.start);
        for (WazaWorld.Thing t : WazaWorld.THINGS.values()) {
            if (t.cast == c && t.kind == WazaWorld.DEVICE) {
                y.maxDeviceStage = Math.max(y.maxDeviceStage, t.stage);
            }
            if (t.cast == c && t.kind == WazaWorld.GUARD && t instanceof WazaWorld.Guard g) {
                y.guardSeen = true;
                y.guardStrength = g.strength;
            }
        }
        if (y.dummy != null) {
            y.statusSeen |= WazaWorld.hasStatus(y.dummy, w.id()) && (WazaWorld.statusCount(y.dummy) >= 2
                || y.dummy.getActiveEffects().size() > y.effectsBefore || y.dummy.getPersistentData().getLong("ororFreezeUntil") > c.start);
            y.effectsMax = Math.max(y.effectsMax, y.dummy.getActiveEffects().size());
        }
        if (w.behaviour() == Waza.Behaviour.GUARD && e == w.windup() + 1 && y.arrow == null) {
            // an arrow from in front, at the guard
            Arrow a = EntityType.ARROW.create(level);
            if (a != null) {
                Vec3 from = y.b.position().add(y.b.getLookAngle().multiply(1, 0, 1).normalize().scale(4)).add(0, y.b.getBbHeight() * 0.5, 0);
                a.setPos(from.x, from.y, from.z);
                a.setOwner(y.dummy);
                a.setDeltaMovement(y.b.getBoundingBox().getCenter().subtract(from).normalize().scale(1.5));
                level.addFreshEntity(a);
                y.arrow = a;
            }
        }
        if (y.stage == 1 && c.ended) {
            y.stage = 2;
            y.phaseAt = now;
        }
        if (y.stage == 2 && now - y.phaseAt >= 30) {
            judge(y, w, c);
            WazaWorld.removeCastObjects(c);
            for (var f : WazaWorld.summonsOf(y.b)) {
                f.discard();
            }
            if (y.arrow != null) {
                y.arrow.discard();
            }
            y.next++;
            y.stage = 0;
            y.phaseAt = 0;
        }
    }

    private static void judge(Yard y, Waza w, WazaEngine.Cast c) {
        boolean phases = c.phase == WazaEngine.Phase.COOLDOWN && c.notes.stream().noneMatch(n -> n.startsWith("cancelled"));
        int want = Math.max(1, w.hits().length);
        boolean fired = c.fired >= want;
        int dummyHits = y.dummy == null ? 0 : DUMMY_HITS.getOrDefault(y.dummy.getId(), 0) - y.hitsAtStart;
        // only the technique's own blows count (the dummy is struck by other things too: see WAZA-RESULT's other)
        boolean reached = c.landed > 0;
        String why = "";
        boolean ok = switch (w.behaviour()) {
            case MELEE, PROJECTILE, BEAM, FIELD, SONG, GROWTH -> reached;
            case CONTROL -> reached && y.statusSeen;
            case CURSE -> reached && c.notes.stream().anyMatch(n -> n.startsWith("mark:"));
            case SUMMON -> c.notes.stream().anyMatch(n -> n.startsWith("summoned:") && !n.equals("summoned:0")) && reached;
            case MOVE -> y.startPos != null && y.b.position().distanceTo(y.startPos) >= 1.0;
            case GUARD -> y.guardSeen && (y.arrow == null || y.guardStrength >= 0);
            case STATUS -> y.statusSeen || c.notes.contains("swap");
            case HEAL -> y.b.getHealth() > y.healthBefore && y.dummy != null && y.dummy.getHealth() <= y.dummyHealthBefore + 0.01F;
            case BUILD -> y.maxDeviceStage >= 3;
            case REWIND -> c.notes.stream().anyMatch(n -> n.equals("rewound:enemy") || n.startsWith("rewound:self ") && !n.equals("rewound:self 0"));
            case ADAPT -> c.notes.contains("learned:melee") && !WazaWorld.learned(y.b, "magic");
            case PACT -> pactOk(y, w, c);
        };
        if (!phases) {
            why += "phases;";
        }
        if (!fired) {
            why += "fired " + c.fired + "/" + want + ";";
        }
        if (!ok) {
            why += "effect;";
        }
        boolean pass = phases && fired && ok;
        StringBuilder b = new StringBuilder();
        b.append("{\"id\":\"").append(w.id()).append("\",\"name\":\"").append(w.name()).append("\",\"tier\":").append(w.tier())
            .append(",\"behaviour\":\"").append(w.behaviour()).append("\",\"ok\":").append(pass).append(",\"fired\":").append(c.fired)
            .append(",\"landed\":").append(c.landed).append(",\"dummyHits\":").append(dummyHits).append(",\"dealt\":").append(Math.round(c.dealt))
            .append(",\"why\":\"").append(why).append("\",\"notes\":\"").append(String.join(" ", c.notes).replace("\"", "'")).append("\"}");
        LOG.info("WAZA-TRY {}", b);
        record(y, pass, why);
        TALLY.computeIfAbsent(w.behaviour().name(), k -> new int[2])[pass ? 0 : 1]++;
    }

    private static boolean pactOk(Yard y, Waza w, WazaEngine.Cast c) {
        if (y.agree == null) {
            return false;
        }
        // the one who refuses never pays; the one who agrees is given its due at once
        boolean refusedClean = !y.refuse.hasEffect(MobEffects.WEAKNESS) && !y.refuse.hasEffect(MobEffects.MOVEMENT_SLOWDOWN);
        switch (w.kind()) {
            case "COLLECT" -> {
                return refusedClean && c.notes.stream().anyMatch(n -> n.startsWith("collected:"));
            }
            case "GIFT" -> {
                return refusedClean && c.notes.contains("gift");
            }
            default -> {
                boolean offered = c.notes.stream().anyMatch(n -> n.startsWith("offered:") && !n.equals("offered:0"));
                // answer as the two players would: one agrees, one refuses
                boolean agreed = false, refused = false;
                for (WazaWorld.Contract k : WazaWorld.contracts(y.b)) {
                    if (k.w == w && k.state == 0) {
                        boolean yes = k.player.equals(y.agree.getUUID());
                        WazaWorld.answer(yes ? y.agree : y.refuse, k.id, yes);
                        agreed |= yes && k.state == 1;
                        refused |= !yes && k.state == 2;
                    }
                }
                return offered && agreed && refused && refusedClean;
            }
        }
    }

    private static void record(Yard y, boolean ok, String why) {
        tried++;
        if (ok) {
            passed++;
        } else if (FAILED.size() < 200) {
            Waza w = Waza.of(y.character, y.next + 1);
            FAILED.add((w == null ? y.character + "#" + y.next : w.id()) + ":" + why);
        }
    }

    private static void cleanup(Yard y) {
        if (y.b != null) {
            y.b.discard();
        }
        if (y.dummy != null) {
            y.dummy.discard();
        }
    }

    private static void finish(ServerLevel level, long now) {
        StringBuilder t = new StringBuilder("{");
        TALLY.forEach((k, v) -> t.append(t.length() > 1 ? "," : "").append('"').append(k).append("\":[").append(v[0]).append(',').append(v[1]).append(']'));
        t.append('}');
        StringBuilder o = new StringBuilder();
        OTHER.entrySet().stream().sorted(Map.Entry.<String, Integer>comparingByValue().reversed()).limit(12)
            .forEach(x -> o.append(x.getKey()).append('=').append(x.getValue()).append(' '));
        LOG.info("WAZA-RESULT {\"techniques\":{},\"tried\":{},\"passed\":{},\"ticks\":{},\"byBehaviour\":{},\"failed\":\"{}\",\"other\":\"{}\",\"pass\":{}}",
            Waza.ALL.size(), tried, passed, now - started, t, String.join(" ", FAILED), o.toString().trim(), tried == Waza.ALL.size() && passed == tried);
        for (Yard y : YARDS) {
            cleanup(y);
            for (Entity e : level.getEntities((Entity) null, new AABB(y.at).inflate(24, 16, 24), x -> !(x instanceof Player))) {
                e.discard();
            }
            for (int[] c : y.chunks) {
                level.setChunkForced(c[0], c[1], false);
            }
        }
        YARDS.clear();
        started = -1;
        resultLogged = true;
    }
}
