package jp.oror.reborn.waza;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import jp.oror.reborn.RebornConfig;
import jp.oror.reborn.SupremeEntity;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.EntityLeaveLevelEvent;
import net.neoforged.neoforge.event.entity.living.LivingDeathEvent;
import net.neoforged.neoforge.event.server.ServerStoppingEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;

/**
 * (057) The 984 techniques at work. Each character runs its own 24 through one state machine, as the design asks:
 * IDLE → TELEGRAPH (the windup: the technique's own motion gathers, its warning is shown) → ACTIVE (the window in which its
 * hits land, at the moments the design gives) → RECOVERY (the motion comes home, its leftovers are taken down) →
 * COOLDOWN (the technique waits its own cooldown), and back to IDLE. A technique is cancelled when its caster is frozen
 * in its windup, dies, or leaves the world (killed, unloaded with its chunk, removed), and everything it put into the
 * world goes with it.
 *
 * <p>Which technique comes next is the character's own choice, by what each technique is for (the design's AI・対処): a
 * cut when the enemy stands within its reach, a shot when it is seen and in range, a guard when it is being hit, a heal
 * when a friend is hurt, a step away when it is pressed, a contract when there is a player to offer it to; the special
 * techniques once the fight has gone on a little or it is hurt, the great ones later, the two finishing ones when it is
 * badly hurt or the fight is long. A technique the design chains (前提・後続・姿勢復帰後) is likelier after its partner.
 * The character's old abilities still get every fourth turn, and its big moves (BossMoves) wait while a technique runs.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class WazaEngine {
    public enum Phase { IDLE, TELEGRAPH, ACTIVE, RECOVERY, COOLDOWN }

    /** A technique under way. */
    public static final class Cast {
        public final Waza w;
        public final SupremeEntity b;
        public final long start;
        public final long seed;
        public final RandomSource random;
        public final boolean forced;
        public Phase phase = Phase.TELEGRAPH;
        public LivingEntity target;
        /** where it was aimed, locked late in the windup (a beam, a field, a fall of rocks) so that it can be dodged */
        public Vec3 aim;
        public Vec3 dir;
        public Vec3 moveTo;
        /** where the caster stood as the technique began */
        public Vec3 home;
        /** a move's checked destination and where it began */
        public Vec3 dest, from;
        public float yaw;
        /** the hits so far, the blows that landed and their damage (read by the CI check) */
        public int fired;
        public int landed;
        public float dealt;
        public final List<String> notes = new ArrayList<>();
        public final Set<Integer> struck = new HashSet<>();
        public final Map<Integer, Long> lastBeamHit = new HashMap<>();
        public final List<Integer> objects = new ArrayList<>();
        public boolean ended;

        Cast(Waza w, SupremeEntity b, LivingEntity target, long start, long seed, boolean forced) {
            this.w = w;
            this.b = b;
            this.target = target;
            this.start = start;
            this.seed = seed;
            this.random = RandomSource.create(seed);
            this.forced = forced;
            this.aim = target != null ? target.position() : b.position().add(b.getLookAngle().scale(4));
            this.yaw = b.getYRot();
            this.home = b.position();
        }

        public int elapsed() {
            return (int) (this.b.level().getGameTime() - this.start);
        }

        public void note(String s) {
            if (this.notes.size() < 12) {
                this.notes.add(s);
            }
        }
    }

    /** What a character remembers between techniques. */
    static final class Brain {
        Cast cast;
        final long[] ready = new long[25];
        int last = -1;
        long lastEnd;
        long engagedAt = -1;
        int count;
        long nextAt;
        boolean oldTurn;
        boolean test;
    }

    private static final Map<Integer, Brain> BRAINS = new HashMap<>();
    /** the last technique each character finished (for the CI check: id, hits, landed, dealt, notes) */
    public static final Map<Integer, Cast> LAST = new HashMap<>();

    private WazaEngine() {
    }

    static Brain brain(SupremeEntity b) {
        return BRAINS.computeIfAbsent(b.getId(), k -> new Brain());
    }

    /** The characters in this level that have run (or are running) techniques. */
    static List<SupremeEntity> casters(ServerLevel sl) {
        List<SupremeEntity> l = new ArrayList<>();
        for (int id : BRAINS.keySet()) {
            if (sl.getEntity(id) instanceof SupremeEntity b && b.isAlive()) {
                l.add(b);
            }
        }
        return l;
    }

    public static Cast current(SupremeEntity b) {
        Brain br = BRAINS.get(b.getId());
        return br == null ? null : br.cast;
    }

    /** For the CI check: this character's choices are the check's, not its own. */
    public static void testMode(SupremeEntity b, boolean on) {
        brain(b).test = on;
    }

    // --------------------------------------------------------------------------------------------------------- ticking

    @SubscribeEvent(priority = EventPriority.HIGH)
    public static void tick(EntityTickEvent.Pre e) {
        if (!(e.getEntity() instanceof SupremeEntity b) || !(b.level() instanceof ServerLevel sl) || b.spec == null) {
            return;
        }
        if (!b.isAlive()) {
            return;
        }
        List<Waza> mine = Waza.BY_CHARACTER.get(b.spec.id);
        if (mine == null) {
            return;
        }
        Brain br = brain(b);
        long now = sl.getGameTime();
        if (br.cast != null) {
            hold(b, now);
            step(br, br.cast, sl, now);
            return;
        }
        if (br.test) {
            hold(b, now);
            return;
        }
        if (!RebornConfig.EXTRA_ABILITIES.get() || b.isNoAi()) {
            return;
        }
        LivingEntity t = b.getTarget();
        if (t == null || !b.validEnemy(t) || b.distanceToSqr(t) > 48 * 48) {
            br.engagedAt = -1;
            return;
        }
        if (br.engagedAt < 0) {
            br.engagedAt = now;
        }
        if (now < br.nextAt) {
            if (!br.oldTurn) {
                hold(b, now);
            }
            return;
        }
        br.oldTurn = false;
        CompoundTag d = b.getPersistentData();
        if (b.windup > 0 || b.action() != 0 || !d.getString("ororMove").isEmpty() || d.getLong("ororFreezeUntil") > now) {
            return;
        }
        // every fourth turn is the old abilities' (the lore power, the arsenal's three)
        if (br.count % 4 == 3) {
            br.count++;
            br.oldTurn = true;
            b.cooldown = Math.min(b.cooldown, 1);
            br.nextAt = now + 48;
            return;
        }
        Waza w = choose(b, br, t, now);
        if (w != null) {
            start(b, br, w, t, now, false);
        } else {
            br.nextAt = now + 10;
        }
    }

    /** For the CI check: a character in its yard stays where it was put, but for its own moves. */
    @SubscribeEvent(priority = EventPriority.LOW)
    public static void after(EntityTickEvent.Post e) {
        if (e.getEntity() instanceof SupremeEntity b && !b.level().isClientSide) {
            Brain br = BRAINS.get(b.getId());
            if (br != null && br.test && (br.cast == null || br.cast.w.behaviour() != Waza.Behaviour.MOVE)) {
                b.getNavigation().stop();
                Vec3 v = b.getDeltaMovement();
                b.setDeltaMovement(0, b.spec.airborne() ? 0 : Math.min(0, v.y), 0);
                // and kept where the technique began: some characters' own passives carry them off (the sixth run:
                // Arcana and Ain Sof Aur were taken seven blocks away mid-technique, out of its reach)
                Cast c = br.cast;
                if (c != null && c.home != null && c.w.behaviour() != Waza.Behaviour.REWIND && b.position().distanceToSqr(c.home) > 1.0) {
                    b.teleportTo(c.home.x, c.home.y, c.home.z);
                }
            }
        }
    }

    /** The old abilities and the big moves wait while a technique is under way. */
    private static void hold(SupremeEntity b, long now) {
        b.cooldown = Math.max(b.cooldown, 6);
        CompoundTag d = b.getPersistentData();
        if (d.getLong("ororMoveNext") < now + 12) {
            d.putLong("ororMoveNext", now + 12);
        }
    }

    /** Starts a technique (the CI check calls this with forced = true, which skips the cooldown). */
    public static Cast start(SupremeEntity b, Waza w, LivingEntity target, boolean forced) {
        Brain br = brain(b);
        if (br.cast != null) {
            cancel(b, br, 1);
        }
        return start(b, br, w, target, b.level().getGameTime(), forced);
    }

    private static Cast start(SupremeEntity b, Brain br, Waza w, LivingEntity target, long now, boolean forced) {
        long seed = b.getRandom().nextLong();
        Cast c = new Cast(w, b, target, now, seed, forced);
        br.cast = c;
        br.count++;
        b.getPersistentData().putString("OrorLastTechnique", w.name());
        WazaNet.toWatchers(b, new WazaNet.Show(b.getId(), w.index(), seed, now, target == null ? -1 : target.getId(), 0));
        WazaActs.telegraphStart(c);
        return c;
    }

    private static void step(Brain br, Cast c, ServerLevel sl, long now) {
        Waza w = c.w;
        int e = (int) (now - c.start);
        int wu = w.windup(), al = w.activeLength(), rc = w.recovery();
        if (c.target != null && (!c.target.isAlive() || c.target.isRemoved())) {
            LivingEntity t = c.b.getTarget();
            c.target = t != null && c.b.validEnemy(t) ? t : null;
        }
        if (e < wu) {
            // frozen in the windup: the technique is lost (the opening the design's 対処 points at)
            if (c.b.getPersistentData().getLong("ororFreezeUntil") > now && !c.forced) {
                cancel(c.b, br, 1);
                return;
            }
            WazaActs.telegraph(c, e);
            return;
        }
        if (e < wu + al) {
            int a = e - wu;
            if (c.phase == Phase.TELEGRAPH) {
                c.phase = Phase.ACTIVE;
                WazaActs.begin(c);
            }
            WazaActs.during(c, a);
            int[] hits = w.hits();
            for (int i = 0; i < hits.length; i++) {
                if (hits[i] == a) {
                    c.fired++;
                    WazaActs.event(c, i);
                }
            }
            if (hits.length == 0 && a == release(w)) {
                c.fired++;
                WazaActs.release(c);
            }
            return;
        }
        if (e < wu + al + rc) {
            if (c.phase != Phase.RECOVERY) {
                c.phase = Phase.RECOVERY;
                WazaActs.recover(c);
            }
            return;
        }
        finish(c.b, br, c, now);
    }

    /** When a technique without hits does what it does: as its motion releases (build_waza.py's release keyframe). */
    public static int release(Waza w) {
        return Math.min(w.activeLength() - 1, Math.max(1, Math.round(w.active() * 0.3F)));
    }

    private static void finish(SupremeEntity b, Brain br, Cast c, long now) {
        c.phase = Phase.COOLDOWN;
        c.ended = true;
        WazaActs.finish(c);
        int cd = c.w.cooldown();
        if (b.lore()) {
            cd = Math.max(10, cd / 2);
        }
        br.ready[c.w.n()] = now + cd;
        br.last = c.w.n();
        br.lastEnd = now;
        br.cast = null;
        int gap = switch (c.w.tier()) {
            case 0 -> 8 + b.getRandom().nextInt(8);
            case 1 -> 12;
            default -> 20;
        };
        br.nextAt = now + (b.lore() ? gap / 2 : gap);
        LAST.put(b.getId(), c);
        WazaNet.toWatchers(b, new WazaNet.Show(b.getId(), -1, 0, now, -1, 0));
    }

    /** Ends the technique under way early (1 cancelled, 2 death, 3 the caster left the world). */
    static void cancel(SupremeEntity b, Brain br, int reason) {
        Cast c = br.cast;
        if (c == null) {
            return;
        }
        c.ended = true;
        c.note("cancelled:" + reason);
        br.cast = null;
        br.nextAt = b.level().getGameTime() + 20;
        WazaActs.finish(c);
        WazaWorld.removeCastObjects(c);
        LAST.put(b.getId(), c);
        WazaNet.toWatchers(b, new WazaNet.Show(b.getId(), -1, 0, b.level().getGameTime(), -1, reason));
    }

    @SubscribeEvent
    public static void died(LivingDeathEvent e) {
        if (e.getEntity() instanceof SupremeEntity b && !b.level().isClientSide) {
            Brain br = BRAINS.get(b.getId());
            if (br != null) {
                cancel(b, br, 2);
            }
            WazaWorld.ownerGone(b);
        }
    }

    @SubscribeEvent
    public static void left(EntityLeaveLevelEvent e) {
        if (e.getLevel().isClientSide()) {
            return;
        }
        if (e.getEntity() instanceof SupremeEntity b) {
            Brain br = BRAINS.remove(b.getId());
            if (br != null && br.cast != null) {
                br.cast.ended = true;
                WazaActs.finish(br.cast);
                WazaWorld.removeCastObjects(br.cast);
                WazaNet.toWatchers(b, new WazaNet.Show(b.getId(), -1, 0, b.level().getGameTime(), -1, 3));
            }
            WazaWorld.ownerGone(b);
            LAST.remove(b.getId());
        } else if (e.getEntity() instanceof LivingEntity l) {
            WazaWorld.forget(l);
        }
    }

    @SubscribeEvent
    public static void stopping(ServerStoppingEvent e) {
        BRAINS.clear();
        LAST.clear();
        WazaWorld.clear();
    }

    // -------------------------------------------------------------------------------------------------------- choosing

    private static Waza choose(SupremeEntity b, Brain br, LivingEntity t, long now) {
        List<Waza> list = Waza.BY_CHARACTER.get(b.spec.id);
        double dist = b.distanceTo(t);
        boolean los = b.hasLineOfSight(t);
        float hp = b.getHealth() / Math.max(1, b.getMaxHealth());
        long battle = now - br.engagedAt;
        Waza lastW = br.last > 0 ? Waza.of(b.spec.id, br.last) : null;
        double total = 0;
        double[] weight = new double[list.size()];
        for (int i = 0; i < list.size(); i++) {
            Waza w = list.get(i);
            if (now < br.ready[w.n()]) {
                continue;
            }
            boolean open = switch (w.tier()) {
                case 0 -> true;
                case 1 -> battle >= 40 || hp < 0.9F;
                case 2 -> battle >= 200 || hp < 0.75F;
                default -> battle >= 500 || hp < 0.5F;
            };
            if (!open) {
                continue;
            }
            double f = fitness(b, w, t, dist, los, hp);
            if (f <= 0) {
                continue;
            }
            f *= switch (w.tier()) {
                case 0 -> 1.0;
                case 1 -> 0.75;
                case 2 -> 0.6;
                default -> 0.55;
            };
            if (w.linkKind() == 0) {
                f *= br.last == w.linkN() && now - br.lastEnd < 60 ? 3.0 : 0.6;
            }
            if (lastW != null && lastW.linkN() == w.n() && now - br.lastEnd < 60) {
                f *= lastW.linkKind() == 1 ? 3.0 : lastW.linkKind() == 2 ? 2.5 : 1.0;
            }
            if (w.n() == br.last) {
                f *= 0.35;
            }
            weight[i] = f;
            total += f;
        }
        if (total <= 0) {
            return null;
        }
        double r = b.getRandom().nextDouble() * total;
        for (int i = 0; i < weight.length; i++) {
            r -= weight[i];
            if (weight[i] > 0 && r <= 0) {
                return list.get(i);
            }
        }
        return null;
    }

    /** How well the technique fits the moment (0: not now). */
    private static double fitness(SupremeEntity b, Waza w, LivingEntity t, double dist, boolean los, float hp) {
        double reach = w.range() + b.getBbWidth() * 0.5 + t.getBbWidth() * 0.5;
        return switch (w.behaviour()) {
            case MELEE -> dist <= reach + 0.8 ? 1.2 : 0;
            case PROJECTILE, BEAM -> dist <= w.range() && los ? 1.0 : 0;
            case CURSE, STATUS, CONTROL -> dist <= Math.max(6, w.range()) && los ? 0.9 : 0;
            case FIELD, SONG, GROWTH -> dist <= w.range() + 2 ? 0.9 : 0;
            case MOVE -> switch (w.kind()) {
                case "BACK" -> hp < 0.6F && dist < 5 ? 1.5 : dist < 4 ? 0.3 : 0;
                case "TOWARD" -> dist > 6 && dist < w.range() + 8 ? 1.2 : 0;
                case "BEHIND", "SIDE" -> dist < 6 ? 1.0 : 0;
                default -> dist < 8 ? 0.7 : dist > 12 ? 0.6 : 0.2;
            };
            case GUARD -> threatened(b, t) ? 1.6 : 0.12;
            case HEAL -> {
                LivingEntity need = WazaActs.neediest(b, w.range());
                yield need == null ? 0 : 1.5 + (0.75 - need.getHealth() / Math.max(1, need.getMaxHealth())) * 3;
            }
            case SUMMON -> WazaWorld.summons(b) < 3 ? 1.0 : 0;
            case BUILD -> WazaWorld.devices(b) < 2 ? 0.9 : 0;
            case REWIND -> w.kind().equals("ENEMY") ? (dist <= Math.max(8, w.range()) ? 0.8 : 0)
                : WazaWorld.betterPast(b, 0.15F) ? 1.4 : 0.05;
            case ADAPT -> WazaWorld.observedTag(b) != null ? 1.3 : 0.25;
            case PACT -> WazaActs.pactPartner(b, w) != null ? 1.0 : 0;
        };
    }

    /** Being hit, or about to be: hurt a moment ago, the enemy swinging close, or a shot flying at it. */
    static boolean threatened(SupremeEntity b, LivingEntity t) {
        if (b.hurtTime > 0 || b.tickCount - b.getLastHurtByMobTimestamp() < 30) {
            return true;
        }
        if (t.swinging && b.distanceTo(t) < 5) {
            return true;
        }
        for (Projectile p : b.level().getEntitiesOfClass(Projectile.class, b.getBoundingBox().inflate(8))) {
            if (p.getOwner() != b && p.getDeltaMovement().lengthSqr() > 0.01
                && p.getDeltaMovement().normalize().dot(b.position().subtract(p.position()).normalize()) > 0.8) {
                return true;
            }
        }
        return t instanceof Player pl && pl.getAttackStrengthScale(0) > 0.9F && b.distanceTo(t) < 4;
    }
}
