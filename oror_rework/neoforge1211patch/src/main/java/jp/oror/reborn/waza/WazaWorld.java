package jp.oror.reborn.waza;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import jp.oror.reborn.FamiliarEntity;
import jp.oror.reborn.SupremeEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingEntityUseItemEvent;
import net.neoforged.neoforge.event.entity.living.LivingHealEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.tick.LevelTickEvent;

/**
 * (057) What the techniques put into the world, owned by the server and kept only in memory: never saved, never a block
 * changed for good (the design's 時間・世界・全能系は一時的な戦闘領域で表現し、保存データへ恒久変更しない). Each thing knows
 * its owner (the parent), the technique that made it, its birth and its life, and there is a limit to how many one owner
 * may have; when the owner dies or leaves the world they all go.
 *
 * <p>Shots fly as segments the server checks against blocks and bodies, and vanish once. Fields, rings of sound,
 * growths and devices have their centre, radius, life and stages. A guard has its facing and its strength, a curse's
 * mark its stacks, its trigger, its end and whether it can be lifted; a status its strength and its end, and what to
 * undo when it ends. Contracts wait for their player's answer. The last few seconds of where the characters and their
 * enemies stood and how hurt they were are kept for rewinding; the kinds of blow each character has taken, for learning.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class WazaWorld {
    public static final int BOLT = 0, BEAM = 1, FIELD = 2, RING = 3, GROWTH = 4, DEVICE = 5, GUARD = 6, MARK = 7, CIRCLE = 8, WARN = 9, LINE = 10;
    private static final int PER_OWNER = 24, ALL_THINGS = 600;

    private WazaWorld() {
    }

    // ---------------------------------------------------------------------------------------------------- the things

    public abstract static class Thing {
        public final int id;
        public final int kind;
        public final WazaEngine.Cast cast;
        public final Waza w;
        public final SupremeEntity owner;
        public final ServerLevel level;
        public Vec3 pos;
        public Vec3 dir = Vec3.ZERO;
        public float radius;
        public final long born;
        public int life;
        public int stage;
        public boolean dead;

        Thing(int kind, WazaEngine.Cast cast, Vec3 pos, float radius, int life) {
            this.id = nextId++;
            this.kind = kind;
            this.cast = cast;
            this.w = cast.w;
            this.owner = cast.b;
            this.level = (ServerLevel) cast.b.level();
            this.pos = pos;
            this.radius = radius;
            this.born = this.level.getGameTime();
            this.life = life;
        }

        int age() {
            return (int) (this.level.getGameTime() - this.born);
        }

        void send(int op) {
            WazaNet.toWatchers(this.owner, new WazaNet.Obj(op, this.id, this.kind, this.owner.getId(), this.w.index(), this.pos.x, this.pos.y,
                this.pos.z, (float) this.dir.x, (float) this.dir.y, (float) this.dir.z, this.radius, this.life, this.stage, this.born));
        }

        void stage(int s) {
            if (s != this.stage) {
                this.stage = s;
                this.send(1);
            }
        }

        void tick(long now) {
        }

        void gone() {
        }
    }

    private static int nextId = 1;
    static final Map<Integer, Thing> THINGS = new LinkedHashMap<>();

    static <T extends Thing> T add(T t) {
        long mine = THINGS.values().stream().filter(x -> x.owner == t.owner).count();
        if (mine >= PER_OWNER || THINGS.size() >= ALL_THINGS) {
            // the oldest of its own goes first
            THINGS.values().stream().filter(x -> x.owner == t.owner).findFirst().ifPresent(WazaWorld::remove);
        }
        THINGS.put(t.id, t);
        t.cast.objects.add(t.id);
        t.send(0);
        return t;
    }

    static void remove(Thing t) {
        if (THINGS.remove(t.id) != null) {
            t.dead = true;
            t.gone();
            t.send(2);
        }
    }

    public static List<Thing> of(WazaEngine.Cast c, int kind) {
        List<Thing> l = new ArrayList<>();
        for (int id : c.objects) {
            Thing t = THINGS.get(id);
            if (t != null && t.kind == kind) {
                l.add(t);
            }
        }
        return l;
    }

    /** A shot: a segment from where it was to where it is, against blocks and bodies, each tick; it vanishes once. */
    public static final class Bolt extends Thing {
        Vec3 vel;
        LivingEntity homing;
        boolean falls;
        boolean returns;
        boolean back;
        final int event;
        final float damage;

        Bolt(WazaEngine.Cast c, Vec3 pos, Vec3 vel, float radius, int life, int event, float damage) {
            super(BOLT, c, pos, radius, life);
            this.vel = vel;
            this.dir = vel;
            this.event = event;
            this.damage = damage;
        }

        @Override
        void tick(long now) {
            if (this.homing != null && this.homing.isAlive() && !this.back) {
                Vec3 want = this.homing.getBoundingBox().getCenter().subtract(this.pos).normalize().scale(this.vel.length());
                this.vel = this.vel.scale(0.82).add(want.scale(0.18));
            }
            if (this.falls) {
                this.vel = this.vel.add(0, -0.06, 0);
            }
            if (this.returns && !this.back && this.age() > this.life / 2) {
                this.back = true;
            }
            if (this.back) {
                Vec3 home = this.owner.getBoundingBox().getCenter();
                this.vel = home.subtract(this.pos).normalize().scale(this.vel.length());
                if (home.distanceTo(this.pos) < 1.2) {
                    remove(this);
                    return;
                }
            }
            Vec3 next = this.pos.add(this.vel);
            if (!this.level.hasChunkAt(BlockPos.containing(next))) {
                remove(this);
                return;
            }
            // bodies first, then blocks: whichever is nearer along the segment
            LivingEntity hit = null;
            double best = Double.MAX_VALUE;
            AABB sweep = new AABB(this.pos, next).inflate(this.radius + 1);
            for (LivingEntity e : this.level.getEntitiesOfClass(LivingEntity.class, sweep, x -> x != this.owner && this.owner.validEnemy(x))) {
                var clip = e.getBoundingBox().inflate(this.radius).clip(this.pos, next);
                if (clip.isPresent()) {
                    double d = clip.get().distanceToSqr(this.pos);
                    if (d < best) {
                        best = d;
                        hit = e;
                    }
                } else if (e.getBoundingBox().inflate(this.radius).contains(this.pos)) {
                    best = 0;
                    hit = e;
                }
            }
            BlockHitResult block = this.level.clip(new ClipContext(this.pos, next, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this.owner));
            if (block.getType() == HitResult.Type.BLOCK && block.getLocation().distanceToSqr(this.pos) < best) {
                this.pos = block.getLocation();
                WazaActs.boltHit(this, null);
                remove(this);
                return;
            }
            if (hit != null) {
                this.pos = this.pos.add(this.vel.normalize().scale(Math.sqrt(best)));
                WazaActs.boltHit(this, hit);
                remove(this);
                return;
            }
            this.pos = next;
            this.dir = this.vel;
            if (this.homing != null || this.falls || this.back || this.age() % 10 == 0) {
                this.send(1);
            }
            if (this.age() >= this.life) {
                remove(this);
            }
        }
    }

    /** A field: a centre, a radius and a life in the battle; who comes in and who goes out. */
    public static final class Field extends Thing {
        final Set<Integer> inside = new HashSet<>();

        Field(WazaEngine.Cast c, Vec3 pos, float radius, int life) {
            super(FIELD, c, pos, radius, life);
        }

        @Override
        void tick(long now) {
            if (!this.level.hasChunkAt(BlockPos.containing(this.pos)) || this.age() >= this.life) {
                remove(this);
                return;
            }
            if (this.age() % 5 != 0) {
                return;
            }
            Set<Integer> now5 = new HashSet<>();
            for (LivingEntity e : this.level.getEntitiesOfClass(LivingEntity.class, new AABB(this.pos, this.pos).inflate(this.radius, 4, this.radius),
                x -> x.position().distanceToSqr(this.pos) <= this.radius * this.radius + 9)) {
                now5.add(e.getId());
                boolean entered = !this.inside.contains(e.getId());
                WazaActs.fieldTouch(this, e, entered, this.age() % 20 == 0);
            }
            for (int id : this.inside) {
                if (!now5.contains(id) && this.level.getEntity(id) instanceof LivingEntity left) {
                    WazaActs.fieldLeft(this, left);
                }
            }
            this.inside.clear();
            this.inside.addAll(now5);
        }

        @Override
        void gone() {
            for (int id : this.inside) {
                if (this.level.getEntity(id) instanceof LivingEntity left) {
                    WazaActs.fieldLeft(this, left);
                }
            }
        }
    }

    /** A ring of sound or pressure, spreading: each body is touched once, on the tick the ring passes it. */
    public static final class Ring extends Thing {
        final float speed, damage;
        final Set<Integer> passed = new HashSet<>();

        Ring(WazaEngine.Cast c, Vec3 pos, float maxRadius, float speed, float damage) {
            super(RING, c, pos, maxRadius, (int) Math.ceil(maxRadius / Math.max(0.05F, speed)) + 1);
            this.speed = speed;
            this.damage = damage;
        }

        @Override
        void tick(long now) {
            float r = this.speed * this.age();
            if (r > this.radius || !this.level.hasChunkAt(BlockPos.containing(this.pos))) {
                remove(this);
                return;
            }
            for (LivingEntity e : this.level.getEntitiesOfClass(LivingEntity.class, new AABB(this.pos, this.pos).inflate(r + 1, 4, r + 1))) {
                double d = e.position().distanceTo(this.pos);
                if (d <= r && d > r - this.speed - 1.0 && this.passed.add(e.getId())) {
                    WazaActs.ringPass(this, e);
                }
            }
        }
    }

    /** A growth: sprout, leaf, grown, withering; what touches it changes as it grows. */
    public static final class Growth extends Thing {
        final int leafAt, grownAt, witherAt;

        /** grown by its first hit, so that the hit has a body to strike with (its hitbox changes with each stage) */
        Growth(WazaEngine.Cast c, Vec3 pos, int life, int firstHit) {
            super(GROWTH, c, pos, 0.6F, life);
            this.leafAt = Math.max(1, firstHit / 2);
            this.grownAt = Math.max(this.leafAt + 1, firstHit);
            this.witherAt = Math.max(this.grownAt + 4, life - 12);
        }

        @Override
        void tick(long now) {
            int a = this.age();
            if (a >= this.life || !this.level.hasChunkAt(BlockPos.containing(this.pos))) {
                remove(this);
                return;
            }
            int s = a < this.leafAt ? 0 : a < this.grownAt ? 1 : a < this.witherAt ? 2 : 3;
            this.radius = switch (s) {
                case 0 -> 0F;
                case 1 -> 1.0F;
                case 2 -> 1.8F + this.w.tier() * 0.4F;
                default -> 0.8F;
            };
            this.stage(s);
            if (a % 10 == 0 && this.radius > 0) {
                for (LivingEntity e : this.level.getEntitiesOfClass(LivingEntity.class, new AABB(this.pos, this.pos).inflate(this.radius, 2.5, this.radius),
                    x -> x != this.owner && this.owner.validEnemy(x))) {
                    WazaActs.growthTouch(this, e);
                }
            }
        }
    }

    /** A device: drawn, built, finished, at work, and taken down; each stage told to the players who see it. */
    public static final class Device extends Thing {
        final int builtAt, doneAt, workAt;
        final String what;

        Device(WazaEngine.Cast c, Vec3 pos, int build, int life, String what) {
            super(DEVICE, c, pos, 1.2F, life);
            this.builtAt = Math.max(2, build / 3);
            this.doneAt = Math.max(this.builtAt + 2, build);
            this.workAt = this.doneAt + 4;
            this.what = what;
        }

        @Override
        void tick(long now) {
            int a = this.age();
            if (a >= this.life || !this.level.hasChunkAt(BlockPos.containing(this.pos))) {
                remove(this);
                return;
            }
            this.stage(a < this.builtAt ? 0 : a < this.doneAt ? 1 : a < this.workAt ? 2 : 3);
            if (this.stage == 3) {
                WazaActs.deviceWork(this, a - this.workAt);
            }
        }
    }

    /** A guard: its facing, how much it can take, and until when. */
    public static final class Guard extends Thing {
        float strength;
        final float full;
        final long until;

        Guard(WazaEngine.Cast c, float yaw, float strength, int life) {
            super(GUARD, c, c.b.position(), Math.max(1.2F, c.b.getBbWidth()), life);
            this.dir = Vec3.directionFromRotation(0, yaw);
            this.strength = strength;
            this.full = strength;
            this.until = this.born + life;
        }

        @Override
        void tick(long now) {
            this.pos = this.owner.position();
            if (now >= this.until || !this.owner.isAlive()) {
                remove(this);
            }
        }

        boolean facing(Vec3 from) {
            Vec3 to = from.subtract(this.owner.position());
            to = new Vec3(to.x, 0, to.z);
            return to.lengthSqr() < 1e-4 || to.normalize().dot(new Vec3(this.dir.x, 0, this.dir.z).normalize()) > 0.26;
        }
    }

    /** A warning: where a blow or a fall or a beam will come (shown through the windup, then gone). */
    public static final class Warn extends Thing {
        Warn(WazaEngine.Cast c, Vec3 pos, Vec3 dir, float radius, int life, int shape) {
            super(WARN, c, pos, radius, life);
            this.dir = dir;
            this.stage = shape;
        }

        @Override
        void tick(long now) {
            if (this.age() >= this.life) {
                remove(this);
            }
        }
    }

    /** A line from the caster to someone (a chain, a thread, a curse's tie, a beam), for as long as it lasts. */
    public static final class Line extends Thing {
        final Entity to;

        Line(WazaEngine.Cast c, Entity to, int life, int shape) {
            super(LINE, c, c.b.position(), 0.2F, life);
            this.to = to;
            this.stage = shape;
            this.dir = to.position().subtract(c.b.position());
        }

        @Override
        void tick(long now) {
            if (this.age() >= this.life || !this.to.isAlive()) {
                remove(this);
                return;
            }
            Vec3 d = this.to.position().subtract(this.owner.position());
            if (d.distanceToSqr(this.dir) > 0.25) {
                this.pos = this.owner.position();
                this.dir = d;
                this.send(1);
            }
        }
    }

    public static final class Beam extends Thing {
        Beam(WazaEngine.Cast c, Vec3 from, Vec3 dir, float length, int life) {
            super(BEAM, c, from, length, life);
            this.dir = dir;
        }

        @Override
        void tick(long now) {
            if (this.age() >= this.life) {
                remove(this);
            }
        }
    }

    public static final class Circle extends Thing {
        Circle(WazaEngine.Cast c, Vec3 pos, float radius, int life) {
            super(CIRCLE, c, pos, radius, life);
        }

        @Override
        void tick(long now) {
            if (this.age() >= this.life) {
                remove(this);
            }
        }
    }

    // -------------------------------------------------------------------------------------- statuses on their targets

    /** A status: its strength, its end, who gave it, and what undoes it. */
    public record Status(String effect, int strength, long until, int owner, Runnable undo) {
    }

    private static final Map<UUID, Map<String, Status>> STATUS = new HashMap<>();

    /**
     * Gives a status. The same status again: the stronger stays; as strong, the later end; a weaker one does not
     * replace a stronger (the design's 再付与・重複の優先順位). Returns whether it took.
     */
    public static boolean status(LivingEntity t, String effect, int strength, int ticks, SupremeEntity owner, Runnable apply, Runnable undo) {
        long until = t.level().getGameTime() + ticks;
        Map<String, Status> m = STATUS.computeIfAbsent(t.getUUID(), k -> new HashMap<>());
        Status was = m.get(effect);
        if (was != null && (was.strength() > strength || was.strength() == strength && was.until() >= until)) {
            return false;
        }
        if (was != null && was.undo() != null) {
            was.undo().run();
        }
        if (apply != null) {
            apply.run();
        }
        m.put(effect, new Status(effect, strength, until, owner == null ? -1 : owner.getId(), undo));
        return true;
    }

    public static boolean hasStatus(LivingEntity t, String effect) {
        Map<String, Status> m = STATUS.get(t.getUUID());
        Status s = m == null ? null : m.get(effect);
        return s != null && s.until() > t.level().getGameTime();
    }

    static void clearStatus(LivingEntity t, String effect) {
        Map<String, Status> m = STATUS.get(t.getUUID());
        Status s = m == null ? null : m.remove(effect);
        if (s != null && s.undo() != null) {
            s.undo().run();
        }
    }

    /** A temporary change to an attribute, for a status (taken away when the status ends, and never saved). */
    static Runnable[] modifier(LivingEntity t, net.minecraft.core.Holder<net.minecraft.world.entity.ai.attributes.Attribute> attribute, String name,
                               double amount, net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation op) {
        ResourceLocation id = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "waza_" + name);
        Runnable apply = () -> {
            AttributeInstance a = t.getAttribute(attribute);
            if (a != null) {
                a.addOrUpdateTransientModifier(new net.minecraft.world.entity.ai.attributes.AttributeModifier(id, amount, op));
            }
        };
        Runnable undo = () -> {
            AttributeInstance a = t.getAttribute(attribute);
            if (a != null) {
                a.removeModifier(id);
            }
        };
        return new Runnable[]{apply, undo};
    }

    // ------------------------------------------------------------------------------------------------- curses' marks

    public static final class Mark {
        public final SupremeEntity owner;
        public final Waza w;
        public final String trigger;
        public int stacks;
        public final long until;
        public final boolean removable;
        Vec3 lastPos;
        double walked;

        Mark(SupremeEntity owner, Waza w, String trigger, long until, boolean removable, Vec3 at) {
            this.owner = owner;
            this.w = w;
            this.trigger = trigger;
            this.until = until;
            this.removable = removable;
            this.lastPos = at;
        }
    }

    static final Map<UUID, List<Mark>> MARKS = new HashMap<>();

    /** Lays a curse's mark (or one more stack of it); returns its stacks. */
    static int mark(SupremeEntity owner, Waza w, LivingEntity t) {
        List<Mark> l = MARKS.computeIfAbsent(t.getUUID(), k -> new ArrayList<>());
        Mark m = l.stream().filter(x -> x.w == w && x.owner == owner).findFirst().orElse(null);
        long now = t.level().getGameTime();
        if (m == null) {
            m = new Mark(owner, w, w.kind().isEmpty() ? "TIMER" : w.kind(), now + 200 + 100L * w.tier(), w.tier() < 3, t.position());
            l.add(m);
        }
        m.stacks = Math.min(3, m.stacks + 1);
        tellMark(t, m, false);
        if (m.stacks >= 3 && m.trigger.equals("TIMER")) {
            fire(t, m);
        }
        return m.stacks;
    }

    private static void tellMark(LivingEntity t, Mark m, boolean fired) {
        if (t instanceof ServerPlayer sp) {
            long left = Math.max(0, (m.until - t.level().getGameTime()) / 20);
            String when = switch (m.trigger) {
                case "HEAL" -> "回復を受けると発動";
                case "ATTACK" -> "攻撃すると発動";
                case "MOVE" -> "動くと発動";
                default -> "満了か3段で発動";
            };
            sp.displayClientMessage(Component.literal(fired ? "呪印〈" + m.w.name() + "〉が発動した"
                : "呪印〈" + m.w.name() + "〉 " + m.stacks + "/3・" + when + "・残り" + left + "秒" + (m.removable ? "（牛乳で解ける）" : "（解除不可）")), true);
        }
    }

    private static void fire(LivingEntity t, Mark m) {
        List<Mark> l = MARKS.get(t.getUUID());
        if (l != null) {
            l.remove(m);
        }
        tellMark(t, m, true);
        if (m.owner.isAlive()) {
            WazaActs.curseFires(m, t);
        }
    }

    public static int marks(LivingEntity t) {
        List<Mark> l = MARKS.get(t.getUUID());
        return l == null ? 0 : l.stream().mapToInt(x -> x.stacks).sum();
    }

    // --------------------------------------------------------------------------------------- memory: rewind and learning

    public record Snap(Vec3 pos, float health, long at) {
    }

    private static final Map<Integer, ArrayDeque<Snap>> HISTORY = new HashMap<>();
    private static final Map<Integer, Map<String, Integer>> SEEN = new HashMap<>();
    private static final Map<Integer, Map<String, Long>> LEARNED = new HashMap<>();

    static void record(LivingEntity e, long now) {
        ArrayDeque<Snap> q = HISTORY.computeIfAbsent(e.getId(), k -> new ArrayDeque<>());
        if (q.size() >= 40) {
            q.removeFirst();
        }
        q.addLast(new Snap(e.position(), e.getHealth(), now));
    }

    /** Where it stood and how hurt it was about ticks ago (null when nothing was kept). */
    public static Snap past(LivingEntity e, int ticks) {
        ArrayDeque<Snap> q = HISTORY.get(e.getId());
        if (q == null || q.isEmpty()) {
            return null;
        }
        long at = e.level().getGameTime() - ticks;
        Snap best = null;
        for (Snap s : q) {
            if (s.at() <= at) {
                best = s;
            }
        }
        return best == null ? q.peekFirst() : best;
    }

    static boolean betterPast(SupremeEntity b, float by) {
        ArrayDeque<Snap> q = HISTORY.get(b.getId());
        if (q == null) {
            return false;
        }
        for (Snap s : q) {
            if (s.health() > b.getHealth() + b.getMaxHealth() * by) {
                return true;
            }
        }
        return false;
    }

    /** The kind of a blow, for learning: what the design calls an attack tag. */
    static String tag(DamageSource s) {
        if (s.is(net.minecraft.tags.DamageTypeTags.IS_FIRE)) {
            return "fire";
        }
        if (s.is(net.minecraft.tags.DamageTypeTags.IS_EXPLOSION)) {
            return "explosion";
        }
        if (s.is(net.minecraft.tags.DamageTypeTags.IS_PROJECTILE) || s.getDirectEntity() instanceof Projectile) {
            return "projectile";
        }
        if (s.is(DamageTypes.MAGIC) || s.is(DamageTypes.INDIRECT_MAGIC) || s.is(net.minecraft.tags.DamageTypeTags.WITCH_RESISTANT_TO)) {
            return "magic";
        }
        if (s.getDirectEntity() instanceof LivingEntity) {
            return "melee";
        }
        return "other";
    }

    public static void observe(SupremeEntity b, String tag, int n) {
        SEEN.computeIfAbsent(b.getId(), k -> new HashMap<>()).merge(tag, n, Integer::sum);
    }

    /** A kind of blow taken at least twice and not yet answered (null: nothing to learn yet). */
    static String observedTag(SupremeEntity b) {
        Map<String, Integer> m = SEEN.get(b.getId());
        if (m == null) {
            return null;
        }
        long now = b.level().getGameTime();
        Map<String, Long> l = LEARNED.getOrDefault(b.getId(), Map.of());
        return m.entrySet().stream().filter(e -> e.getValue() >= 2 && l.getOrDefault(e.getKey(), 0L) < now)
            .max(Map.Entry.comparingByValue()).map(Map.Entry::getKey).orElse(null);
    }

    /** For the CI check: what a character has seen and learned, forgotten. */
    static void forgetLearning(SupremeEntity b) {
        SEEN.remove(b.getId());
        LEARNED.remove(b.getId());
    }

    static void learn(SupremeEntity b, String tag, int ticks) {
        LEARNED.computeIfAbsent(b.getId(), k -> new HashMap<>()).put(tag, b.level().getGameTime() + ticks);
    }

    public static boolean learned(SupremeEntity b, String tag) {
        Map<String, Long> l = LEARNED.get(b.getId());
        return l != null && l.getOrDefault(tag, 0L) > b.level().getGameTime();
    }

    // ------------------------------------------------------------------------------------------------------ contracts

    public static final class Contract {
        public final int id;
        public final SupremeEntity owner;
        public final UUID player;
        /** the player as it was offered (a player who logged out and back in is found again by its id) */
        final ServerPlayer offeredTo;
        public final Waza w;
        public final long expires;
        public int state; // 0 offered, 1 accepted, 2 refused, 3 lapsed
        public boolean paid;
        public long payAt = -1;

        Contract(int id, SupremeEntity owner, ServerPlayer player, Waza w, long expires) {
            this.id = id;
            this.owner = owner;
            this.player = player.getUUID();
            this.offeredTo = player;
            this.w = w;
            this.expires = expires;
        }
    }

    static final Map<Integer, Contract> CONTRACTS = new LinkedHashMap<>();
    private static int nextContract = 1;

    static Contract offer(SupremeEntity owner, Waza w, ServerPlayer p, String benefit, String cost) {
        Contract c = new Contract(nextContract++, owner, p, w, owner.level().getGameTime() + 400);
        CONTRACTS.put(c.id, c);
        WazaNet.toPlayer(p, new WazaNet.Offer(c.id, w.index(), owner.getId(), benefit, cost, 20));
        return c;
    }

    /** The player's answer: only an agreed contract ever costs anything. */
    public static void answer(ServerPlayer p, int id, boolean accept) {
        Contract c = CONTRACTS.get(id);
        if (c == null || !c.player.equals(p.getUUID()) || c.state != 0 || p.level().getGameTime() > c.expires) {
            return;
        }
        c.state = accept ? 1 : 2;
        WazaActs.contractAnswered(c, p);
    }

    /** The contract's player, if still here. */
    static ServerPlayer signer(Contract c) {
        ServerPlayer p = c.owner.getServer() == null ? null : c.owner.getServer().getPlayerList().getPlayer(c.player);
        return p != null ? p : c.offeredTo != null && !c.offeredTo.isRemoved() ? c.offeredTo : null;
    }

    public static List<Contract> contracts(SupremeEntity owner) {
        return CONTRACTS.values().stream().filter(c -> c.owner == owner).toList();
    }

    // --------------------------------------------------------------------------------------------------------- summons

    private static final Map<UUID, Long> SUMMONED = new HashMap<>();
    private static final Map<UUID, Integer> SUMMONER = new HashMap<>();

    static void summoned(SupremeEntity b, FamiliarEntity f, int life) {
        f.addTag("oror_waza");
        SUMMONED.put(f.getUUID(), b.level().getGameTime() + life);
        SUMMONER.put(f.getUUID(), b.getId());
    }

    public static int summons(SupremeEntity b) {
        int n = 0;
        for (Map.Entry<UUID, Integer> e : SUMMONER.entrySet()) {
            if (e.getValue() == b.getId() && b.level() instanceof ServerLevel sl && sl.getEntity(e.getKey()) != null) {
                n++;
            }
        }
        return n;
    }

    public static List<FamiliarEntity> summonsOf(SupremeEntity b) {
        List<FamiliarEntity> l = new ArrayList<>();
        if (b.level() instanceof ServerLevel sl) {
            for (Map.Entry<UUID, Integer> e : SUMMONER.entrySet()) {
                if (e.getValue() == b.getId() && sl.getEntity(e.getKey()) instanceof FamiliarEntity f && f.isAlive()) {
                    l.add(f);
                }
            }
        }
        return l;
    }

    public static int devices(SupremeEntity b) {
        return (int) THINGS.values().stream().filter(t -> t.owner == b && t.kind == DEVICE).count();
    }

    // ------------------------------------------------------------------------------------------------------- ticking

    @SubscribeEvent
    public static void tick(LevelTickEvent.Post e) {
        if (!(e.getLevel() instanceof ServerLevel sl)) {
            return;
        }
        long now = sl.getGameTime();
        for (Thing t : new ArrayList<>(THINGS.values())) {
            if (t.level == sl && !t.dead) {
                if (!t.owner.isAlive() || t.owner.isRemoved()) {
                    remove(t);
                } else {
                    t.tick(now);
                }
            }
        }
        if (now % 5 == 0) {
            // the past, for rewinding: the characters and whoever they fight
            for (SupremeEntity b : WazaEngine.casters(sl)) {
                record(b, now);
                if (b.getTarget() != null) {
                    record(b.getTarget(), now);
                }
            }
        }
        if (now % 10 == 0) {
            expire(sl, now);
        }
    }

    private static void expire(ServerLevel sl, long now) {
        for (Iterator<Map.Entry<UUID, Map<String, Status>>> it = STATUS.entrySet().iterator(); it.hasNext(); ) {
            Map.Entry<UUID, Map<String, Status>> en = it.next();
            Entity ent = sl.getEntity(en.getKey());
            if (ent == null && sl.getServer().getPlayerList().getPlayer(en.getKey()) == null) {
                continue;
            }
            en.getValue().values().removeIf(s -> {
                if (s.until() <= now) {
                    if (s.undo() != null) {
                        s.undo().run();
                    }
                    return true;
                }
                return false;
            });
            if (en.getValue().isEmpty()) {
                it.remove();
            }
        }
        for (Map.Entry<UUID, List<Mark>> en : new ArrayList<>(MARKS.entrySet())) {
            if (!(sl.getEntity(en.getKey()) instanceof LivingEntity t)) {
                continue;
            }
            for (Mark m : new ArrayList<>(en.getValue())) {
                if (now >= m.until) {
                    if (m.trigger.equals("TIMER")) {
                        fire(t, m);
                    } else {
                        en.getValue().remove(m);
                    }
                } else if (m.trigger.equals("MOVE")) {
                    m.walked += t.position().distanceTo(m.lastPos);
                    m.lastPos = t.position();
                    if (m.walked > 6) {
                        fire(t, m);
                    }
                }
            }
            if (en.getValue().isEmpty()) {
                MARKS.remove(en.getKey());
            }
        }
        for (Iterator<Map.Entry<UUID, Long>> it = SUMMONED.entrySet().iterator(); it.hasNext(); ) {
            Map.Entry<UUID, Long> en = it.next();
            Entity f = sl.getEntity(en.getKey());
            Integer owner = SUMMONER.get(en.getKey());
            boolean ownerGone = owner == null || !(sl.getEntity(owner) instanceof SupremeEntity s) || !s.isAlive();
            if (f != null && (now >= en.getValue() || ownerGone)) {
                f.discard();
            }
            if (f == null || f.isRemoved()) {
                if (f != null || now >= en.getValue()) {
                    it.remove();
                    SUMMONER.remove(en.getKey());
                }
            }
        }
        for (Iterator<Contract> it = CONTRACTS.values().iterator(); it.hasNext(); ) {
            Contract c = it.next();
            if (c.state == 0 && now > c.expires) {
                c.state = 3;
            }
            if (c.state == 1 && c.payAt >= 0 && now >= c.payAt && !c.paid) {
                ServerPlayer p = signer(c);
                if (p != null) {
                    WazaActs.payCost(c, p);
                }
            }
            if (now > c.expires + 2400 || !c.owner.isAlive() && c.state != 1) {
                it.remove();
            }
        }
    }

    /** The owner died or left: its things, its summons, its marks' future and its contracts' claims go with it. */
    static void ownerGone(SupremeEntity b) {
        for (Thing t : new ArrayList<>(THINGS.values())) {
            if (t.owner == b) {
                remove(t);
            }
        }
        if (b.level() instanceof ServerLevel sl) {
            for (Map.Entry<UUID, Integer> en : new ArrayList<>(SUMMONER.entrySet())) {
                if (en.getValue() == b.getId()) {
                    Entity f = sl.getEntity(en.getKey());
                    if (f != null) {
                        f.discard();
                    }
                    SUMMONER.remove(en.getKey());
                    SUMMONED.remove(en.getKey());
                }
            }
        }
        for (List<Mark> l : MARKS.values()) {
            l.removeIf(m -> m.owner == b);
        }
        CONTRACTS.values().removeIf(c -> c.owner == b && c.state != 1);
        HISTORY.remove(b.getId());
        SEEN.remove(b.getId());
        LEARNED.remove(b.getId());
    }

    static void removeCastObjects(WazaEngine.Cast c) {
        for (int id : new ArrayList<>(c.objects)) {
            Thing t = THINGS.get(id);
            if (t != null) {
                remove(t);
            }
        }
    }

    static void forget(LivingEntity e) {
        HISTORY.remove(e.getId());
    }

    static void clear() {
        THINGS.clear();
        STATUS.clear();
        MARKS.clear();
        HISTORY.clear();
        SEEN.clear();
        LEARNED.clear();
        CONTRACTS.clear();
        SUMMONED.clear();
        SUMMONER.clear();
    }

    // ------------------------------------------------------------------------------------- blows taken, heals received

    /** Set by the damage listener: the last body a blow reached (WazaActs.hurt reads it to know whether a hit landed). */
    static LivingEntity lastReached;
    static float lastReachedAmount;

    @SubscribeEvent(priority = EventPriority.LOW)
    public static void incoming(LivingIncomingDamageEvent e) {
        LivingEntity t = e.getEntity();
        if (t.level().isClientSide) {
            return;
        }
        DamageSource s = e.getSource();
        Entity by = s.getEntity();
        // a guard: blows from in front are taken on it (shots stopped outright, or sent back); broken, its owner reels
        for (Thing th : new ArrayList<>(THINGS.values())) {
            if (th.kind == GUARD && th.owner == t && th instanceof Guard g && !g.dead) {
                Vec3 from = s.getSourcePosition() != null ? s.getSourcePosition() : by != null ? by.position() : null;
                if (from != null && g.facing(from)) {
                    boolean shot = s.getDirectEntity() instanceof Projectile;
                    float took = shot ? e.getAmount() : e.getAmount() * 0.7F;
                    g.strength -= took;
                    if (shot) {
                        if (g.w.has("REFLECT") && s.getDirectEntity() instanceof Projectile p) {
                            p.setDeltaMovement(p.getDeltaMovement().scale(-1));
                            p.setOwner(t);
                            p.hurtMarked = true;
                        }
                        e.setCanceled(true);
                    } else {
                        e.setAmount(e.getAmount() * 0.3F);
                    }
                    int crack = g.strength <= 0 ? 3 : g.strength < g.full * 0.33F ? 2 : g.strength < g.full * 0.66F ? 1 : 0;
                    g.stage(crack);
                    if (g.strength <= 0) {
                        WazaNet.toWatchers(t, new WazaNet.Fx(2, g.w.index(), t.getId(), t.getX(), t.getY() + t.getBbHeight() * 0.5, t.getZ(), 0));
                        remove(g);
                        t.getPersistentData().putLong("ororFreezeUntil", t.level().getGameTime() + 20);
                    }
                    if (e.isCanceled()) {
                        return;
                    }
                }
            }
        }
        // what a character has learned to answer is answered (only what it has seen: no resistance to everything)
        if (t instanceof SupremeEntity b) {
            String tag = tag(s);
            if (learned(b, tag)) {
                e.setAmount(e.getAmount() * 0.5F);
            }
            observe(b, tag, 1);
        }
        // a mark from a character: its own next blow on the marked bites deeper
        if (by instanceof SupremeEntity b && hasStatus(t, "MARK_" + b.getId())) {
            e.setAmount(e.getAmount() * 1.25F);
            clearStatus(t, "MARK_" + b.getId());
        }
        // death refused once
        if (e.getAmount() >= t.getHealth() && hasStatus(t, "DEATHWARD")) {
            e.setAmount(Math.max(0, t.getHealth() - 1));
            clearStatus(t, "DEATHWARD");
            WazaNet.toWatchers(t, new WazaNet.Fx(6, -1, t.getId(), t.getX(), t.getY() + 1, t.getZ(), 0));
        }
        // a curse that waits for its bearer to strike
        if (by instanceof LivingEntity attacker) {
            List<Mark> l = MARKS.get(attacker.getUUID());
            if (l != null) {
                for (Mark m : new ArrayList<>(l)) {
                    if (m.trigger.equals("ATTACK")) {
                        fire(attacker, m);
                    }
                }
            }
        }
        lastReached = t;
        lastReachedAmount = e.getAmount();
        WazaTest.incoming(e);
    }

    @SubscribeEvent
    public static void healed(LivingHealEvent e) {
        LivingEntity t = e.getEntity();
        if (t.level().isClientSide) {
            return;
        }
        List<Mark> l = MARKS.get(t.getUUID());
        if (l != null) {
            for (Mark m : new ArrayList<>(l)) {
                if (m.trigger.equals("HEAL")) {
                    fire(t, m);
                }
            }
        }
    }

    /** Milk lifts the marks that can be lifted, and the techniques' statuses with them. */
    @SubscribeEvent
    public static void drank(LivingEntityUseItemEvent.Finish e) {
        if (e.getEntity().level().isClientSide || !e.getItem().is(Items.MILK_BUCKET)) {
            return;
        }
        LivingEntity t = e.getEntity();
        List<Mark> l = MARKS.get(t.getUUID());
        if (l != null) {
            l.removeIf(m -> m.removable);
        }
        Map<String, Status> m = STATUS.remove(t.getUUID());
        if (m != null) {
            for (Status s : m.values()) {
                if (s.undo() != null) {
                    s.undo().run();
                }
            }
        }
        if (t instanceof Player p) {
            p.displayClientMessage(Component.literal("呪印と技の効果が解けた"), true);
        }
    }
}
