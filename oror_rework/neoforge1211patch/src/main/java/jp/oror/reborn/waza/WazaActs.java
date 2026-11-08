package jp.oror.reborn.waza;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import jp.oror.reborn.Abilities;
import jp.oror.reborn.FamiliarEntity;
import jp.oror.reborn.LorePowers;
import jp.oror.reborn.RebornConfig;
import jp.oror.reborn.SupremeEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.BowItem;
import net.minecraft.world.item.CrossbowItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TridentItem;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * (057) What each of the seventeen behaviours does, in each phase of its technique, and the verbs (what the
 * technique's text asks for: a burn, a bind, a pull, gravity turned over, a body made small...) it does to whoever it
 * reaches. The design's rules are kept here: the attack value is damage only for attacks, shared out over a
 * technique's hits so that their sum never exceeds the technique's whole; a melee blow lands only on what the moving
 * blade (or claw, fist, tail) sweeps through between one tick and the next; a shot is a segment the server checks and
 * vanishes once; a beam fires only after its warning line, and each body it holds is hurt at most every eight ticks; a
 * move lands only where there is footing, room and a loaded chunk; healing reaches only friends, never past their
 * health; learning answers only what has been seen; a contract costs nothing until its player has agreed to it.
 */
final class WazaActs {
    private WazaActs() {
    }

    private static final float[] TIER_DAMAGE = {0.9F, 1.3F, 2.0F, 3.0F};

    // ------------------------------------------------------------------------------------------------------- numbers

    /** The technique's whole damage (all its hits together). */
    static float whole(SupremeEntity b, Waza w) {
        return (float) (b.getAttributeValue(Attributes.ATTACK_DAMAGE) * RebornConfig.DAMAGE.get() * TIER_DAMAGE[w.tier()]);
    }

    /** One hit's share. */
    static float share(SupremeEntity b, Waza w) {
        return whole(b, w) / Math.max(1, w.hits().length);
    }

    static int lasting(Waza w) {
        return 40 + 30 * w.tier();
    }

    /** True while a technique's own blow is being dealt (the CI check tells its blows from any other). */
    static boolean striking;

    /** A blow from the technique: true when it reached the body (the damage listener saw it). */
    static boolean hurt(WazaEngine.Cast c, LivingEntity t, float amount) {
        SupremeEntity b = c.b;
        if (t == b || !b.validEnemy(t) || amount <= 0) {
            return false;
        }
        t.invulnerableTime = 0;
        WazaWorld.lastReached = null;
        striking = true;
        try {
            LorePowers.strike(b, t, amount, false);
        } finally {
            striking = false;
        }
        boolean landed = WazaWorld.lastReached == t;
        if (landed) {
            c.landed++;
            c.dealt += WazaWorld.lastReachedAmount;
            if (c.w.has("DRAIN")) {
                b.heal(Math.min(b.getMaxHealth() * 0.05F, WazaWorld.lastReachedAmount * 0.3F));
            }
            fx(c, 0, t, t.getX(), t.getY() + t.getBbHeight() * 0.6, t.getZ(), amount);
        }
        return landed;
    }

    static void fx(WazaEngine.Cast c, int kind, Entity at, double x, double y, double z, float a) {
        WazaNet.toWatchers(c.b, new WazaNet.Fx(kind, c.w.index(), at == null ? -1 : at.getId(), x, y, z, a));
    }

    static List<LivingEntity> enemiesNear(SupremeEntity b, Vec3 at, double r) {
        return b.level().getEntitiesOfClass(LivingEntity.class, new AABB(at, at).inflate(r, Math.max(3, r * 0.6), r),
                e -> e != b && b.validEnemy(e) && e.position().distanceToSqr(at) <= r * r + 4)
            .stream().sorted(Comparator.comparingDouble(e -> e.position().distanceToSqr(at))).limit(24).toList();
    }

    static List<LivingEntity> friendsNear(SupremeEntity b, double r) {
        List<LivingEntity> l = new ArrayList<>(b.level().getEntitiesOfClass(LivingEntity.class, b.getBoundingBox().inflate(r),
            e -> e != b && e.isAlive() && b.ally(e) && e != b.getTarget()));
        l.add(0, b);
        return l;
    }

    /** The most hurt friend within reach (itself included), if any is below three quarters of its health. */
    static LivingEntity neediest(SupremeEntity b, double r) {
        return friendsNear(b, Math.max(4, r)).stream().filter(e -> e.getHealth() < e.getMaxHealth() * 0.75F)
            .min(Comparator.comparingDouble(e -> e.getHealth() / Math.max(1, e.getMaxHealth()))).orElse(null);
    }

    /** The targets of a technique aimed at one enemy but able to reach a few: the target and the next nearest. */
    static List<LivingEntity> targets(WazaEngine.Cast c, double reach) {
        List<LivingEntity> l = new ArrayList<>();
        if (c.target != null && c.target.isAlive() && c.b.validEnemy(c.target) && c.b.distanceTo(c.target) <= reach + 4) {
            l.add(c.target);
        }
        int more = c.w.count() - 1 + (c.w.tier() >= 2 ? 2 : 0);
        if (more > 0) {
            Vec3 at = c.target != null ? c.target.position() : c.b.position();
            for (LivingEntity e : enemiesNear(c.b, at, Math.min(8, reach))) {
                if (!l.contains(e) && more-- > 0) {
                    l.add(e);
                }
            }
        }
        return l;
    }

    static Vec3 ground(ServerLevel sl, Vec3 at) {
        BlockPos p = BlockPos.containing(at);
        for (int i = 0; i < 8; i++) {
            if (!sl.getBlockState(p.below()).getCollisionShape(sl, p.below()).isEmpty()) {
                return new Vec3(at.x, p.getY(), at.z);
            }
            p = p.below();
        }
        return at;
    }

    // -------------------------------------------------------------------------------------------------------- windup

    static void telegraphStart(WazaEngine.Cast c) {
        Waza w = c.w;
        SupremeEntity b = c.b;
        ServerLevel sl = (ServerLevel) b.level();
        Vec3 toward = c.target != null ? c.target.position().subtract(b.position()) : b.getLookAngle();
        c.dir = toward.lengthSqr() < 1e-4 ? b.getLookAngle() : toward.normalize();
        int wu = Math.max(1, w.windup());
        switch (w.behaviour()) {
            case MELEE -> WazaWorld.add(new WazaWorld.Warn(c, b.position(), c.dir, w.range() + b.getBbWidth() * 0.5F, wu, 0));
            case PROJECTILE -> {
                if (falls(w)) {
                    for (Vec3 at : fallPoints(c)) {
                        WazaWorld.add(new WazaWorld.Warn(c, ground(sl, at), Vec3.ZERO, 1.6F + w.tier() * 0.4F, wu + w.activeLength(), 1));
                    }
                } else {
                    WazaWorld.add(new WazaWorld.Warn(c, b.getEyePosition(), c.dir, w.range(), wu, 2));
                }
            }
            case BEAM -> {
                if (c.target != null) {
                    Vec3 d = c.target.getBoundingBox().getCenter().subtract(b.getEyePosition());
                    if (d.lengthSqr() > 1e-4) {
                        c.dir = d.normalize();
                    }
                }
                WazaWorld.add(new WazaWorld.Warn(c, b.getEyePosition(), c.dir, w.range(), wu, 3));
            }
            case FIELD, GROWTH -> WazaWorld.add(new WazaWorld.Warn(c, ground(sl, c.aim), Vec3.ZERO, fieldRadius(w), wu, 1));
            case SONG -> WazaWorld.add(new WazaWorld.Warn(c, ground(sl, b.position()), Vec3.ZERO, songRadius(w), wu, 4));
            case SUMMON -> WazaWorld.add(new WazaWorld.Circle(c, ground(sl, b.position().add(c.dir.scale(2))), 1.5F + w.tier() * 0.5F,
                wu + 10));
            case BUILD -> {
                Vec3 site = ground(sl, b.position().add(c.dir.scale(2.5)));
                c.moveTo = site;
                WazaWorld.add(new WazaWorld.Warn(c, site, c.dir, 1.4F, wu, 5));
            }
            default -> {
            }
        }
    }

    static void telegraph(WazaEngine.Cast c, int e) {
        // a beam follows its target until a moment before it fires, then holds still: it can be stepped out of
        if (c.w.behaviour() == Waza.Behaviour.BEAM && c.target != null && e < c.w.windup() - 4) {
            Vec3 d = c.target.getBoundingBox().getCenter().subtract(c.b.getEyePosition());
            if (d.lengthSqr() > 1e-4) {
                c.dir = d.normalize();
                for (WazaWorld.Thing t : WazaWorld.of(c, WazaWorld.WARN)) {
                    t.pos = c.b.getEyePosition();
                    t.dir = c.dir;
                    t.send(1);
                }
            }
        }
        if (c.w.behaviour() == Waza.Behaviour.BEAM || c.w.behaviour() == Waza.Behaviour.MELEE) {
            c.b.getNavigation().stop();
        }
    }

    // -------------------------------------------------------------------------------------------------------- active

    static void begin(WazaEngine.Cast c) {
        Waza w = c.w;
        SupremeEntity b = c.b;
        ServerLevel sl = (ServerLevel) b.level();
        if (c.target != null) {
            Vec3 d = c.target.position().subtract(b.position());
            if (d.lengthSqr() > 1e-4 && w.behaviour() != Waza.Behaviour.BEAM) {
                c.dir = d.normalize();
            }
        }
        c.yaw = (float) (Mth.atan2(c.dir.z, c.dir.x) * Mth.RAD_TO_DEG) - 90F;
        switch (w.behaviour()) {
            case BEAM -> {
                Vec3 from = b.getEyePosition();
                float len = beamLength(c, from);
                WazaWorld.add(new WazaWorld.Beam(c, from, c.dir, len, w.activeLength()));
            }
            case MOVE -> moveBegin(c);
            case GUARD -> {
                float strength = b.getMaxHealth() * (0.06F + 0.03F * w.tier()) + 20;
                WazaWorld.add(new WazaWorld.Guard(c, c.yaw, strength, w.activeLength() + w.recovery() + 20 * (w.tier() + 1)));
                if (w.has("WARD")) {
                    for (LivingEntity f : friendsNear(b, 6)) {
                        support(c, f, "WARD");
                    }
                }
            }
            case FIELD -> WazaWorld.add(new WazaWorld.Field(c, ground(sl, c.aim), fieldRadius(w),
                w.activeLength() + w.recovery() + 40 + 40 * w.tier()));
            case GROWTH -> {
                int first = w.hits().length > 0 ? w.hits()[0] : 4;
                int n = Math.min(3, w.count() + (w.tier() >= 2 ? 1 : 0));
                for (int i = 0; i < n; i++) {
                    double ang = c.random.nextDouble() * Math.PI * 2;
                    double r = i == 0 ? 0 : 1.5 + c.random.nextDouble() * 2;
                    Vec3 at = ground(sl, c.aim.add(Math.cos(ang) * r, 0, Math.sin(ang) * r));
                    WazaWorld.add(new WazaWorld.Growth(c, at, w.activeLength() + w.recovery() + 60 + 40 * w.tier(), first));
                }
            }
            case SUMMON -> summon(c);
            case BUILD -> {
                Vec3 site = c.moveTo != null ? c.moveTo : ground(sl, b.position().add(c.dir.scale(2.5)));
                String what = w.kind().isEmpty() ? "TURRET" : w.kind();
                int build = w.activeLength() + 10;
                WazaWorld.add(new WazaWorld.Device(c, site, build, build + 160 + 80 * w.tier(), what));
                c.note("device:" + what);
            }
            default -> {
            }
        }
    }

    static void during(WazaEngine.Cast c, int a) {
        Waza w = c.w;
        switch (w.behaviour()) {
            case MELEE -> meleeSweep(c, a);
            case BEAM -> beamHold(c, a);
            case MOVE -> moveDuring(c, a);
            default -> {
            }
        }
    }

    /** One of the technique's hits, at the moment the design gives it. */
    static void event(WazaEngine.Cast c, int i) {
        Waza w = c.w;
        SupremeEntity b = c.b;
        if (i == 0) {
            selfSupport(c);
        }
        switch (w.behaviour()) {
            case MELEE -> {
                // the sweep has done its work by now; a blow that touched nothing is a miss (the design's 空振り)
            }
            case PROJECTILE -> shoot(c, i);
            case BEAM -> {
            }
            case FIELD -> {
                for (WazaWorld.Thing t : WazaWorld.of(c, WazaWorld.FIELD)) {
                    for (LivingEntity e : enemiesNear(b, t.pos, t.radius)) {
                        if (hurt(c, e, share(b, w))) {
                            hitVerbs(c, e);
                        }
                    }
                    fx(c, 1, null, t.pos.x, t.pos.y, t.pos.z, t.radius);
                }
            }
            case SUMMON -> {
                List<FamiliarEntity> mine = WazaWorld.summonsOf(b);
                float each = share(b, w) / Math.max(1, mine.size());
                for (FamiliarEntity f : mine) {
                    LivingEntity t = enemiesNear(b, f.position(), 16).stream().findFirst().orElse(c.target);
                    if (t != null) {
                        Vec3 from = f.getBoundingBox().getCenter();
                        Vec3 v = t.getBoundingBox().getCenter().subtract(from).normalize().scale(1.1);
                        WazaWorld.Bolt bolt = new WazaWorld.Bolt(c, from, v, 0.35F, 40, i, each);
                        bolt.homing = t;
                        WazaWorld.add(bolt);
                    }
                }
            }
            case CONTROL -> {
                for (LivingEntity t : targets(c, w.range())) {
                    hurt(c, t, share(b, w));
                    WazaWorld.status(t, w.id(), w.tier(), lasting(w), b, null, null);
                    controlVerbs(c, t);
                    WazaWorld.add(new WazaWorld.Line(c, t, 30, 0));
                }
            }
            case CURSE -> {
                for (LivingEntity t : targets(c, Math.max(6, w.range()))) {
                    hurt(c, t, share(b, w) * 0.3F);
                    int s = WazaWorld.mark(b, w, t);
                    c.note("mark:" + s);
                    WazaWorld.add(new WazaWorld.Line(c, t, 16, 1));
                }
            }
            case GROWTH -> {
                for (WazaWorld.Thing t : WazaWorld.of(c, WazaWorld.GROWTH)) {
                    int st = t instanceof WazaWorld.Growth g ? g.stageNow() : t.stage;
                    if (st >= 1 && st <= 2) {
                        float r = st == 1 ? 1.2F : 1.8F + w.tier() * 0.4F;
                        for (LivingEntity e : enemiesNear(b, t.pos, r)) {
                            if (hurt(c, e, share(b, w))) {
                                hitVerbs(c, e);
                            }
                        }
                    }
                }
            }
            case SONG -> {
                Vec3 at = b.position();
                float maxR = songRadius(w);
                int left = Math.max(6, w.activeLength() - w.hits()[i]);
                WazaWorld.add(new WazaWorld.Ring(c, at, maxR, maxR / left, share(b, w)));
            }
            default -> {
            }
        }
    }

    /** The moment a technique without hits does what it does. */
    static void release(WazaEngine.Cast c) {
        Waza w = c.w;
        SupremeEntity b = c.b;
        selfSupport(c);
        switch (w.behaviour()) {
            case STATUS -> {
                for (LivingEntity t : targets(c, Math.max(6, w.range()))) {
                    // the technique's own effect, its strength and its end, on its target (the design's 固有効果ID)
                    WazaWorld.status(t, w.id(), w.tier(), lasting(w), b, null, null);
                    statusVerbs(c, t);
                    fx(c, 10, t, t.getX(), t.getY() + t.getBbHeight() + 0.4, t.getZ(), 0);
                }
            }
            case HEAL -> heal(c);
            case REWIND -> rewind(c);
            case ADAPT -> adapt(c);
            case PACT -> pact(c);
            case GUARD, MOVE, BUILD -> {
            }
            default -> {
            }
        }
    }

    static void recover(WazaEngine.Cast c) {
        // the warnings, lines and beams are taken down; fields, growths, devices, guards and rings live out their lives
        for (int id : new ArrayList<>(c.objects)) {
            WazaWorld.Thing t = WazaWorld.THINGS.get(id);
            if (t != null && (t.kind == WazaWorld.WARN && !falls(c.w) || t.kind == WazaWorld.BEAM)) {
                WazaWorld.remove(t);
            }
        }
        if (c.w.behaviour() == Waza.Behaviour.MOVE) {
            c.b.setDeltaMovement(c.b.getDeltaMovement().multiply(0.3, 1, 0.3));
        }
    }

    static void finish(WazaEngine.Cast c) {
        for (int id : new ArrayList<>(c.objects)) {
            WazaWorld.Thing t = WazaWorld.THINGS.get(id);
            if (t != null && (t.kind == WazaWorld.WARN || t.kind == WazaWorld.BEAM || t.kind == WazaWorld.CIRCLE)) {
                WazaWorld.remove(t);
            }
        }
    }

    // --------------------------------------------------------------------------------------------------------- melee

    /**
     * The blade's sweep: through the two ticks before each hit the tip runs along the technique's path (level, down
     * across, up across, a thrust, straight down, the ground about the feet, a whole turn), and whatever lies between
     * where the blade was on the tick before and where it is now is struck, once for that hit.
     */
    private static void meleeSweep(WazaEngine.Cast c, int a) {
        Waza w = c.w;
        int[] hits = w.hits();
        for (int i = 0; i < hits.length; i++) {
            int h = hits[i];
            if (a < h - 2 || a > h) {
                continue;
            }
            int arc = w.arcs().length > 0 ? w.arcs()[i % w.arcs().length] : 0;
            float u0 = Math.max(0, (a - (h - 2) - 1) / 2F), u1 = (a - (h - 2)) / 2F;
            // the tick's part of the swing in small steps (a whole turn is half a circle a tick): each step's blade
            // against the step before's, so that nothing between them is passed over
            int steps = arc >= 5 ? 10 : 5;
            Vec3[][] path = new Vec3[steps + 1][];
            for (int s = 0; s <= steps; s++) {
                path[s] = blade(c, arc, u0 + (u1 - u0) * s / steps);
            }
            int key = i * 100000;
            float far = w.range() + c.b.getBbWidth() + c.b.getBbHeight() * 0.3F + 2;
            for (LivingEntity e : enemiesNear(c.b, c.b.position(), far)) {
                if (c.struck.contains(key + e.getId())) {
                    continue;
                }
                AABB box = e.getBoundingBox().inflate(0.25);
                boolean touched = false;
                for (int s = 0; s < steps && !touched; s++) {
                    Vec3[] from = path[s], to = path[s + 1];
                    for (int k = 0; k <= 4 && !touched; k++) {
                        double f = k / 4.0;
                        Vec3 p0 = from[0].lerp(from[1], f), p1 = to[0].lerp(to[1], f);
                        touched = box.contains(p0) || box.contains(p1) || box.clip(p0, p1).isPresent();
                    }
                    // and along the blade itself, where it is at the end of the step
                    touched |= box.clip(to[0], to[1]).isPresent();
                }
                if (touched) {
                    c.struck.add(key + e.getId());
                    if (hurt(c, e, share(c.b, w))) {
                        hitVerbs(c, e);
                    }
                }
            }
        }
    }

    /** The blade at u (0 to 1 through its swing): from the shoulder to the tip. */
    private static Vec3[] blade(WazaEngine.Cast c, int arc, float u) {
        SupremeEntity b = c.b;
        // a big body reaches further, and from higher up
        float reach = c.w.range() + b.getBbWidth() * 0.5F + b.getBbHeight() * 0.25F;
        Vec3 fwd = new Vec3(c.dir.x, 0, c.dir.z);
        fwd = fwd.lengthSqr() < 1e-4 ? b.getLookAngle() : fwd.normalize();
        Vec3 side = new Vec3(-fwd.z, 0, fwd.x);
        Vec3 up = new Vec3(0, 1, 0);
        Vec3 shoulder = b.position().add(0, b.getBbHeight() * 0.62, 0);
        if (c.target != null && arc != 5) {
            // the swing's plane tilted down (or up) to where the enemy's body is: a giant cuts down at a man
            Vec3 to = c.target.getBoundingBox().getCenter().subtract(shoulder);
            if (to.lengthSqr() > 1e-4) {
                fwd = to.normalize();
                up = side.cross(fwd).normalize();
                if (up.y < 0) {
                    up = up.scale(-1);
                }
            }
        }
        Vec3 tipDir;
        switch (arc) {
            case 1 -> { // down across, from high right to low left
                double t = Mth.lerp(u, -1.1, 1.1);
                tipDir = fwd.scale(Math.cos(t * 0.8)).add(side.scale(Math.sin(t) * 0.9)).add(up.scale(-t * 0.6));
            }
            case 2 -> { // up across
                double t = Mth.lerp(u, -1.1, 1.1);
                tipDir = fwd.scale(Math.cos(t * 0.8)).add(side.scale(-Math.sin(t) * 0.9)).add(up.scale(t * 0.6));
            }
            case 3 -> { // a thrust: straight out, the reach growing
                tipDir = fwd.add(up.scale(-0.05));
                reach *= 0.45F + 0.55F * u;
            }
            case 4 -> { // straight down from overhead
                double t = Mth.lerp(u, -1.3, 0.9);
                tipDir = fwd.scale(Math.cos(t)).add(up.scale(-Math.sin(t)));
            }
            case 5 -> { // about the feet: a ring spreading on the ground
                double ang = u * Math.PI * 2;
                tipDir = fwd.scale(Math.cos(ang)).add(side.scale(Math.sin(ang))).add(up.scale(-0.08));
                shoulder = b.position().add(0, 0.5, 0);
            }
            case 6 -> { // a whole turn
                double ang = Mth.lerp(u, -Math.PI, Math.PI);
                tipDir = fwd.scale(Math.cos(ang)).add(side.scale(Math.sin(ang)));
                shoulder = b.position().add(0, b.getBbHeight() * 0.45, 0);
            }
            default -> { // level, right to left
                double t = Mth.lerp(u, -1.2, 1.2);
                tipDir = fwd.scale(Math.cos(t)).add(side.scale(Math.sin(t)));
            }
        }
        Vec3 tip = shoulder.add(tipDir.normalize().scale(reach));
        return new Vec3[]{shoulder.add(tipDir.normalize().scale(reach * 0.25)), tip};
    }

    // ---------------------------------------------------------------------------------------------------------- shots

    static boolean falls(Waza w) {
        return w.behaviour() == Waza.Behaviour.PROJECTILE && (w.shape() == 2 || w.name().contains("落") || w.name().contains("流星")
            || w.name().contains("雨") || w.name().contains("降"));
    }

    private static List<Vec3> fallPoints(WazaEngine.Cast c) {
        List<Vec3> l = new ArrayList<>();
        Vec3 at = c.aim;
        int n = Math.min(5, c.w.count() + c.w.tier());
        for (int i = 0; i < n; i++) {
            double ang = i * 2.399963 + c.seed % 7;
            double r = i == 0 ? 0 : 1.5 + i * 0.9;
            l.add(at.add(Math.cos(ang) * r, 0, Math.sin(ang) * r));
        }
        return l;
    }

    private static void shoot(WazaEngine.Cast c, int i) {
        Waza w = c.w;
        SupremeEntity b = c.b;
        ServerLevel sl = (ServerLevel) b.level();
        float dmg = share(b, w);
        if (falls(w)) {
            List<Vec3> pts = fallPoints(c);
            float each = dmg / Math.max(1, pts.size());
            for (Vec3 at : pts) {
                Vec3 g = ground(sl, at);
                // from as high as there is open sky over the spot (up to twelve blocks): nothing starts inside a block
                int up = 2;
                while (up < 12 && sl.getBlockState(BlockPos.containing(g.add(0, up + 1, 0))).getCollisionShape(sl,
                    BlockPos.containing(g.add(0, up + 1, 0))).isEmpty()) {
                    up++;
                }
                WazaWorld.Bolt bolt = new WazaWorld.Bolt(c, g.add(0, up, 0), new Vec3(0, -1.2, 0), 0.6F + w.tier() * 0.25F, 30, i, each);
                bolt.falls = true;
                WazaWorld.add(bolt);
            }
            return;
        }
        int n = Math.min(5, w.count());
        float each = dmg / n;
        Vec3 from = b.getEyePosition().add(c.dir.scale(0.6));
        float speed = Mth.clamp(w.range() / Math.max(8F, w.activeLength() * 1.5F), 0.7F, 2.2F);
        String text = w.name();
        for (int k = 0; k < n; k++) {
            Vec3 aimAt = c.target != null ? c.target.getBoundingBox().getCenter() : from.add(c.dir.scale(w.range()));
            Vec3 d = aimAt.subtract(from).normalize();
            if (n > 1) {
                double spread = (k - (n - 1) / 2.0) * 0.12;
                d = d.yRot((float) spread);
            }
            WazaWorld.Bolt bolt = new WazaWorld.Bolt(c, from, d.scale(speed), 0.3F + w.tier() * 0.15F, (int) (w.range() / speed) + 20, i, each);
            if (c.target != null && (w.shape() == 0 || w.shape() == 6 || w.shape() == 13 || text.contains("追") || w.tier() >= 2)) {
                bolt.homing = c.target;
            }
            bolt.returns = text.contains("戻") || text.contains("返") || text.contains("環") || text.contains("巡");
            WazaWorld.add(bolt);
        }
    }

    static void boltHit(WazaWorld.Bolt bolt, LivingEntity hit) {
        WazaEngine.Cast c = bolt.cast;
        if (hit != null) {
            if (hurt(c, hit, bolt.damage)) {
                hitVerbs(c, hit);
            }
        }
        if (bolt.w.has("BLAST") || bolt.falls) {
            for (LivingEntity e : enemiesNear(bolt.owner, bolt.pos, 1.8 + bolt.w.tier() * 0.5)) {
                if (e != hit) {
                    hurt(c, e, bolt.damage * 0.5F);
                }
            }
        }
        fx(c, 1, hit, bolt.pos.x, bolt.pos.y, bolt.pos.z, bolt.radius);
    }

    // ---------------------------------------------------------------------------------------------------------- beams

    private static float beamLength(WazaEngine.Cast c, Vec3 from) {
        Vec3 to = from.add(c.dir.scale(c.w.range()));
        var hit = c.b.level().clip(new net.minecraft.world.level.ClipContext(from, to, net.minecraft.world.level.ClipContext.Block.COLLIDER,
            net.minecraft.world.level.ClipContext.Fluid.NONE, c.b));
        return (float) (hit.getType() == net.minecraft.world.phys.HitResult.Type.BLOCK ? hit.getLocation().distanceTo(from) : c.w.range());
    }

    private static void beamHold(WazaEngine.Cast c, int a) {
        Waza w = c.w;
        int first = w.hits().length > 0 ? w.hits()[0] : 0;
        if (a < first) {
            return;
        }
        Vec3 from = c.b.getEyePosition();
        float len = beamLength(c, from);
        Vec3 to = from.add(c.dir.scale(len));
        int applications = Math.max(1, (w.activeLength() - first + 7) / 8);
        float each = whole(c.b, w) / applications;
        long now = c.b.level().getGameTime();
        for (LivingEntity e : c.b.level().getEntitiesOfClass(LivingEntity.class, new AABB(from, to).inflate(1.5),
            x -> x != c.b && c.b.validEnemy(x))) {
            if (e.getBoundingBox().inflate(0.5 + w.tier() * 0.25).clip(from, to).isPresent() || e.getBoundingBox().inflate(0.5).contains(from)) {
                Long last = c.lastBeamHit.get(e.getId());
                if (last == null || now - last >= 8) {
                    c.lastBeamHit.put(e.getId(), now);
                    if (hurt(c, e, each)) {
                        hitVerbs(c, e);
                    }
                }
            }
        }
    }

    // ---------------------------------------------------------------------------------------------------------- moves

    private static void moveBegin(WazaEngine.Cast c) {
        Waza w = c.w;
        SupremeEntity b = c.b;
        Vec3 dest = destination(c);
        if (dest == null) {
            c.note("move:no-footing");
            return;
        }
        c.moveTo = dest;
        Vec3 was = b.position();
        if (w.kind().equals("BLINK") || w.kind().isEmpty()) {
            b.teleportTo(dest.x, dest.y, dest.z);
            c.note("move:blink");
            fx(c, 9, b, was.x, was.y, was.z, (float) was.distanceTo(dest));
            if (w.has("INVIS")) {
                b.addEffect(new MobEffectInstance(MobEffects.INVISIBILITY, 20, 0));
            }
            c.moveTo = null;
        } else if (w.kind().equals("UP") && !b.spec.airborne()) {
            Vec3 d = dest.subtract(was);
            b.setDeltaMovement(d.x * 0.18, 0.75, d.z * 0.18);
            b.hurtMarked = true;
            c.note("move:leap");
        } else {
            c.note("move:" + w.kind().toLowerCase());
        }
    }

    private static void moveDuring(WazaEngine.Cast c, int a) {
        if (c.moveTo == null || c.w.kind().equals("UP") && !c.b.spec.airborne()) {
            return;
        }
        Vec3 d = c.moveTo.subtract(c.b.position());
        int left = Math.max(1, c.w.activeLength() - a);
        if (d.lengthSqr() < 0.25) {
            c.moveTo = null;
            return;
        }
        Vec3 v = d.scale(1.0 / left);
        if (v.length() > 1.4) {
            v = v.normalize().scale(1.4);
        }
        c.b.setDeltaMovement(v.x, c.b.spec.airborne() ? v.y : Math.max(c.b.getDeltaMovement().y, Math.min(0.4, v.y)), v.z);
        c.b.hurtMarked = true;
    }

    /** Where the move goes, checked first: a loaded chunk, inside the border, room for the body, and footing. */
    private static Vec3 destination(WazaEngine.Cast c) {
        SupremeEntity b = c.b;
        Waza w = c.w;
        LivingEntity t = c.target;
        Vec3 me = b.position();
        Vec3 toT = t != null ? t.position().subtract(me) : b.getLookAngle();
        Vec3 flat = new Vec3(toT.x, 0, toT.z);
        flat = flat.lengthSqr() < 1e-4 ? new Vec3(0, 0, 1) : flat.normalize();
        Vec3 side = new Vec3(-flat.z, 0, flat.x).scale((c.seed & 1) == 0 ? 1 : -1);
        double step = Math.min(w.range(), 8);
        double gap = 1.5 + b.getBbWidth() * 0.5 + (t != null ? t.getBbWidth() * 0.5 : 0);
        Vec3 want = switch (w.kind()) {
            case "BEHIND" -> t != null ? t.position().add(flat.scale(gap)) : me.add(flat.scale(step));
            case "BACK" -> me.subtract(flat.scale(step));
            case "TOWARD" -> t != null ? t.position().subtract(flat.scale(gap)) : me.add(flat.scale(step));
            case "SIDE" -> me.add(side.scale(Math.min(step, 6))).add(flat.scale(1.5));
            case "UP" -> me.add(flat.scale(Math.min(step, 5))).add(0, b.spec.airborne() ? 4 : 0, 0);
            default -> t != null ? t.position().add(flat.yRot((float) ((c.seed % 360) * Mth.DEG_TO_RAD)).scale(3 + (c.seed & 3)))
                : me.add(side.scale(4));
        };
        for (int k = 0; k < 9; k++) {
            Vec3 tryAt = k == 0 ? want : me.add(want.subtract(me).yRot((float) (k * 0.7 * ((k & 1) == 0 ? 1 : -1))).scale(1 - k * 0.07));
            Vec3 ok = valid(b, tryAt);
            // a move goes somewhere: a spot within two blocks of where it began is no move
            if (ok != null && ok.distanceTo(me) >= 2) {
                return ok;
            }
        }
        return null;
    }

    static Vec3 valid(LivingEntity b, Vec3 at) {
        ServerLevel sl = (ServerLevel) b.level();
        BlockPos p = BlockPos.containing(at);
        if (!sl.hasChunkAt(p) || !sl.getWorldBorder().isWithinBounds(p) || at.y < sl.getMinBuildHeight() + 1 || at.y > sl.getMaxBuildHeight() - 3) {
            return null;
        }
        boolean flies = b instanceof SupremeEntity s && (s.spec.airborne() || s.spec.aquatic());
        Vec3 spot = flies ? at : ground(sl, at.add(0, 2, 0));
        if (!flies && sl.getBlockState(BlockPos.containing(spot).below()).getCollisionShape(sl, BlockPos.containing(spot).below()).isEmpty()) {
            return null;
        }
        if (!sl.noCollision(b, b.getBoundingBox().move(spot.subtract(b.position())))) {
            return null;
        }
        return spot;
    }

    // ------------------------------------------------------------------------------------------------------- support

    private static void selfSupport(WazaEngine.Cast c) {
        if (c.w.behaviour() == Waza.Behaviour.HEAL) {
            return;
        }
        for (String v : c.w.verbs()) {
            switch (v) {
                case "WARD", "HASTE", "MIGHT", "INVIS", "DEATHWARD", "CLEANSE" -> support(c, c.b, v);
                default -> {
                }
            }
        }
    }

    /** A friend helped (never an enemy: the caller has made sure). */
    static void support(WazaEngine.Cast c, LivingEntity f, String v) {
        int d = lasting(c.w);
        switch (v) {
            case "WARD" -> {
                f.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, d, c.w.tier() >= 2 ? 1 : 0));
                f.setAbsorptionAmount(Math.min(f.getMaxHealth() * 0.2F, f.getAbsorptionAmount() + 4 + 2 * c.w.tier()));
            }
            case "HASTE" -> f.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, d, 1));
            case "MIGHT" -> f.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, d, c.w.tier() >= 2 ? 1 : 0));
            case "INVIS" -> f.addEffect(new MobEffectInstance(MobEffects.INVISIBILITY, Math.min(60, d), 0));
            case "CLEANSE" -> {
                f.getActiveEffects().stream().filter(e -> e.getEffect().value().getCategory() == MobEffectCategory.HARMFUL).map(MobEffectInstance::getEffect)
                    .toList().forEach(f::removeEffect);
                f.clearFire();
            }
            case "DEATHWARD" -> WazaWorld.status(f, "DEATHWARD", 1, d * 3, c.b, null, null);
            case "HEAL_ALLY" -> f.heal(f.getMaxHealth() * 0.03F);
            default -> {
            }
        }
    }

    private static final float[] HEAL_SHARE = {0.06F, 0.12F, 0.22F, 0.35F};

    /** Healing: friends only (itself and its side), never past their health; a ward's excess becomes a small shield. */
    private static void heal(WazaEngine.Cast c) {
        SupremeEntity b = c.b;
        Waza w = c.w;
        List<LivingEntity> friends = friendsNear(b, Math.max(4, w.range())).stream()
            .sorted(Comparator.comparingDouble(e -> e.getHealth() / Math.max(1, e.getMaxHealth()))).toList();
        int n = w.tier() >= 3 ? 8 : 3;
        for (LivingEntity f : friends) {
            if (n-- <= 0) {
                break;
            }
            if (!(f == b || b.ally(f)) || f == b.getTarget()) {
                continue;
            }
            float amount = f.getMaxHealth() * HEAL_SHARE[w.tier()];
            float room = f.getMaxHealth() - f.getHealth();
            f.heal(Math.min(amount, room));
            if (amount > room && w.has("WARD")) {
                f.setAbsorptionAmount(Math.min(f.getMaxHealth() * 0.1F, f.getAbsorptionAmount() + (amount - room) * 0.5F));
            }
            for (String v : w.verbs()) {
                if (!v.equals("HEAL_ALLY")) {
                    support(c, f, v);
                }
            }
            c.note("healed:" + (f == b ? "self" : f.getType().getDescriptionId()));
            fx(c, 5, f, f.getX(), f.getY() + f.getBbHeight() * 0.5, f.getZ(), amount);
        }
    }

    // --------------------------------------------------------------------------------------------- the enemy's verbs

    /** What a blow carries (after it landed). */
    static void hitVerbs(WazaEngine.Cast c, LivingEntity t) {
        for (String v : c.w.verbs()) {
            enemyVerb(c, t, v, true);
        }
    }

    /** The verbs that leave something on the body for a while (a status technique always leaves one). */
    private static final java.util.Set<String> LINGERING = java.util.Set.of("STOP", "GRAVITY", "SHRINK", "SILENCE", "BIND", "BURN", "FROST",
        "POISON", "WITHER", "BLIND", "WEAKEN", "SLOW", "ARMORBREAK", "CONFUSE", "MARK", "FEAR");

    private static void statusVerbs(WazaEngine.Cast c, LivingEntity t) {
        List<String> vs = new ArrayList<>(c.w.verbs().stream().filter(v -> !isSupport(v)).toList());
        if (vs.stream().noneMatch(LINGERING::contains)) {
            vs.add(vs.isEmpty() ? "SLOW" : "WEAKEN");
            if (vs.size() == 1) {
                vs.add("WEAKEN");
            }
        }
        for (String v : vs) {
            enemyVerb(c, t, v, false);
        }
    }

    private static void controlVerbs(WazaEngine.Cast c, LivingEntity t) {
        // a hold is a state on the body (the design's 状態として付与): a pull or a throw alone still binds it a moment
        List<String> vs = new ArrayList<>(c.w.verbs().stream().filter(v -> !isSupport(v)).toList());
        if (vs.stream().noneMatch(LINGERING::contains)) {
            vs.add("BIND");
        }
        for (String v : vs) {
            enemyVerb(c, t, v, false);
        }
    }

    static boolean isSupport(String v) {
        return switch (v) {
            case "HEAL_ALLY", "WARD", "HASTE", "MIGHT", "CLEANSE", "DEATHWARD", "INVIS" -> true;
            default -> false;
        };
    }

    /**
     * One verb on an enemy. Statuses are given through WazaWorld.status (the stronger stays; each undone when it ends);
     * a push, a pull or a lift is a push of the body, never a change to the world.
     */
    static void enemyVerb(WazaEngine.Cast c, LivingEntity t, String v, boolean blow) {
        SupremeEntity b = c.b;
        Waza w = c.w;
        int d = lasting(w);
        int amp = w.tier() >= 2 ? 1 : 0;
        Vec3 away = t.position().subtract(b.position());
        away = away.lengthSqr() < 1e-4 ? b.getLookAngle() : away.normalize();
        long now = b.level().getGameTime();
        switch (v) {
            case "STOP" -> {
                Abilities.stun(t, Math.min(80, 20 + 15 * w.tier()));
                for (Projectile p : t.level().getEntitiesOfClass(Projectile.class, t.getBoundingBox().inflate(6), q -> q.getOwner() != b)) {
                    p.setDeltaMovement(Vec3.ZERO);
                }
            }
            case "GRAVITY" -> {
                int up = 20 + 10 * w.tier();
                WazaWorld.status(t, "GRAVITY", amp, up, b, () -> t.addEffect(new MobEffectInstance(MobEffects.LEVITATION, up, 1)),
                    () -> t.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 60, 0)));
            }
            case "SHRINK" -> {
                Runnable[] m = WazaWorld.modifier(t, Attributes.SCALE, "shrink", -0.4, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
                WazaWorld.status(t, "SHRINK", amp, d, b, m[0], m[1]);
            }
            case "SWAP" -> {
                LivingEntity other = enemiesNear(b, t.position(), 12).stream().filter(e -> e != t).findFirst().orElse(null);
                Entity with = other != null ? other : b;
                Vec3 a = t.position(), o = with.position();
                if (valid(t, o) != null && (with == b || valid((LivingEntity) with, a) != null)) {
                    t.teleportTo(o.x, o.y, o.z);
                    with.teleportTo(a.x, a.y, a.z);
                    fx(c, 9, t, a.x, a.y, a.z, (float) a.distanceTo(o));
                    c.note("swap");
                }
            }
            case "DISPEL" -> {
                t.getActiveEffects().stream().filter(e -> e.getEffect().value().getCategory() == MobEffectCategory.BENEFICIAL)
                    .map(MobEffectInstance::getEffect).toList().forEach(t::removeEffect);
                for (Projectile p : t.level().getEntitiesOfClass(Projectile.class, t.getBoundingBox().inflate(10), q -> q.getOwner() == t)) {
                    p.discard();
                }
            }
            case "SILENCE" -> {
                t.getPersistentData().putLong("OrorSilencedUntil", now + d);
                WazaWorld.status(t, "SILENCE", amp, d, b, null, null);
            }
            case "BIND" -> {
                int ticks = Math.min(60, 16 + 8 * w.tier());
                if (WazaWorld.status(t, "BIND", amp, ticks + 40, b, null, null) || blow) {
                    Abilities.stun(t, ticks);
                }
            }
            case "PULL" -> {
                Vec3 pull = away.scale(-(0.8 + 0.2 * w.tier()));
                t.setDeltaMovement(pull.x, 0.25, pull.z);
                t.hurtMarked = true;
            }
            case "KNOCK" -> {
                t.setDeltaMovement(away.x * (1.0 + 0.2 * w.tier()), 0.35, away.z * (1.0 + 0.2 * w.tier()));
                t.hurtMarked = true;
            }
            case "LIFT" -> {
                t.setDeltaMovement(t.getDeltaMovement().x, 0.8 + 0.1 * w.tier(), t.getDeltaMovement().z);
                t.hurtMarked = true;
            }
            case "SLAM" -> {
                t.setDeltaMovement(t.getDeltaMovement().x * 0.3, t.onGround() ? 0 : -1.4, t.getDeltaMovement().z * 0.3);
                t.hurtMarked = true;
                t.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 30, 1));
            }
            case "BURN" -> t.setRemainingFireTicks(Math.max(t.getRemainingFireTicks(), 60 + 20 * w.tier()));
            case "FROST" -> {
                t.setTicksFrozen(Math.max(t.getTicksFrozen(), t.getTicksRequiredToFreeze() + 40 + 20 * w.tier()));
                t.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, d, 1));
            }
            case "SHOCK" -> {
                Abilities.stun(t, 6 + 2 * w.tier());
                fx(c, 11, t, t.getX(), t.getY() + 1, t.getZ(), 1);
            }
            case "POISON" -> t.addEffect(new MobEffectInstance(MobEffects.POISON, d, amp));
            case "WITHER" -> t.addEffect(new MobEffectInstance(MobEffects.WITHER, d, amp));
            case "BLIND" -> {
                t.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, Math.min(80, d), 0));
                if (t instanceof Mob m) {
                    m.setTarget(null);
                }
            }
            case "WEAKEN" -> t.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, d, amp));
            case "SLOW" -> t.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, d, 1 + amp));
            case "ARMORBREAK" -> {
                Runnable[] m = WazaWorld.modifier(t, Attributes.ARMOR, "armorbreak", -4.0 * (w.tier() + 1), AttributeModifier.Operation.ADD_VALUE);
                WazaWorld.status(t, "ARMORBREAK", w.tier(), d, b, m[0], m[1]);
            }
            case "CONFUSE" -> {
                t.addEffect(new MobEffectInstance(MobEffects.CONFUSION, d, 0));
                if (t instanceof Mob m) {
                    m.setTarget(null);
                    m.setYRot(m.getYRot() + 120 + c.random.nextInt(120));
                }
            }
            case "MARK" -> {
                WazaWorld.status(t, "MARK_" + b.getId(), 0, d * 2, b, null, null);
                t.addEffect(new MobEffectInstance(MobEffects.GLOWING, d, 0));
            }
            case "FEAR" -> {
                t.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, d, 0));
                if (t instanceof Mob m && !(t instanceof Player)) {
                    Vec3 run = t.position().add(away.scale(8));
                    m.getNavigation().moveTo(run.x, run.y, run.z, 1.3);
                } else {
                    t.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 30, 0));
                }
            }
            case "REFLECT" -> {
                for (Projectile p : b.level().getEntitiesOfClass(Projectile.class, b.getBoundingBox().inflate(5),
                    q -> q.getOwner() instanceof LivingEntity o && b.validEnemy(o))) {
                    p.setDeltaMovement(p.getDeltaMovement().scale(-1.2));
                    p.setOwner(b);
                    p.hurtMarked = true;
                }
            }
            case "SHATTER" -> {
                if (t.getAbsorptionAmount() > 0) {
                    t.setAbsorptionAmount(0);
                }
                if (t instanceof SupremeEntity s) {
                    s.shield = 0;
                }
            }
            case "DRAIN" -> {
                // the blow's own share comes back (WazaActs.hurt)
            }
            case "BLAST" -> fx(c, 12, t, t.getX(), t.getY() + 0.5, t.getZ(), 2.5F);
            case "PILLAR" -> {
                t.setDeltaMovement(t.getDeltaMovement().x, 0.5, t.getDeltaMovement().z);
                t.hurtMarked = true;
                fx(c, 13, t, t.getX(), t.getY(), t.getZ(), 1);
            }
            default -> {
            }
        }
    }

    // --------------------------------------------------------------------------------------- fields, rings, growths

    static float fieldRadius(Waza w) {
        return Mth.clamp(w.range() * 0.5F, 3F, 16F);
    }

    static float songRadius(Waza w) {
        return Mth.clamp(w.range(), 6F, 24F);
    }

    /** A body in a field: an enemy is held, slowed, turned over...; a friend is helped. Every second while inside. */
    static void fieldTouch(WazaWorld.Field f, LivingEntity e, boolean entered, boolean second) {
        WazaEngine.Cast c = f.cast;
        SupremeEntity b = f.owner;
        if (e != b && b.validEnemy(e)) {
            for (String v : f.w.verbs()) {
                switch (v) {
                    case "BIND", "PULL", "KNOCK", "STOP", "SWAP", "LIFT" -> {
                        if (entered) {
                            enemyVerb(c, e, v, false);
                        }
                    }
                    case "SLOW", "WEAKEN", "POISON", "WITHER", "BLIND", "BURN", "FROST", "GRAVITY", "SILENCE", "MARK", "CONFUSE", "SHRINK",
                         "ARMORBREAK", "FEAR" -> {
                        if (entered || second) {
                            enemyVerb(c, e, v, false);
                        }
                    }
                    case "REFLECT", "DISPEL" -> {
                        if (second) {
                            enemyVerb(c, e, v, false);
                        }
                    }
                    default -> {
                    }
                }
            }
        } else if (e == b || b.ally(e)) {
            if (second) {
                for (String v : f.w.verbs()) {
                    if (isSupport(v)) {
                        support(c, e, v);
                    }
                }
            }
        }
    }

    static void fieldLeft(WazaWorld.Field f, LivingEntity e) {
        // what the field gave runs out by itself (its statuses are short); nothing is left behind in the world
    }

    static void ringPass(WazaWorld.Ring r, LivingEntity e) {
        WazaEngine.Cast c = r.cast;
        SupremeEntity b = r.owner;
        if (e != b && b.validEnemy(e)) {
            hurt(c, e, r.damage);
            List<String> vs = r.w.verbs().stream().filter(v -> !isSupport(v)).toList();
            for (String v : vs.isEmpty() ? List.of("KNOCK") : vs) {
                enemyVerb(c, e, v, true);
            }
        } else if (e == b || b.ally(e)) {
            for (String v : r.w.verbs()) {
                if (isSupport(v)) {
                    support(c, e, v);
                }
            }
        }
    }

    static void growthTouch(WazaWorld.Growth g, LivingEntity e) {
        WazaEngine.Cast c = g.cast;
        if (g.stage == 1) {
            enemyVerb(c, e, "SLOW", false);
        } else if (g.stage == 2) {
            List<String> vs = g.w.verbs().stream().filter(v -> !isSupport(v)).toList();
            for (String v : vs.isEmpty() ? List.of("BIND") : vs) {
                enemyVerb(c, e, v, false);
            }
        }
    }

    // ------------------------------------------------------------------------------------------------------ summons

    private static void summon(WazaEngine.Cast c) {
        SupremeEntity b = c.b;
        ServerLevel sl = (ServerLevel) b.level();
        Waza w = c.w;
        int style;
        try {
            style = Integer.parseInt(w.kind());
        } catch (NumberFormatException ex) {
            style = 1;
        }
        int n = Math.min(4, Math.min(w.count(), 2) + w.tier() / 2);
        java.util.Set<java.util.UUID> before = new java.util.HashSet<>();
        for (FamiliarEntity f : sl.getEntitiesOfClass(FamiliarEntity.class, b.getBoundingBox().inflate(16))) {
            before.add(f.getUUID());
        }
        FamiliarEntity.create(b, sl, style, n);
        int made = 0;
        for (FamiliarEntity f : sl.getEntitiesOfClass(FamiliarEntity.class, b.getBoundingBox().inflate(16))) {
            if (!before.contains(f.getUUID()) && b.getUUID().equals(f.creator)) {
                WazaWorld.summoned(b, f, 200 + 100 * w.tier());
                fx(c, 11, f, f.getX(), f.getY() + 0.5, f.getZ(), 0);
                made++;
            }
        }
        c.note("summoned:" + made);
    }

    // ------------------------------------------------------------------------------------------------------ devices

    static void deviceWork(WazaWorld.Device d, int a) {
        WazaEngine.Cast c = d.cast;
        SupremeEntity b = d.owner;
        Waza w = d.w;
        switch (d.what) {
            case "TURRET" -> {
                if (a % 15 == 0) {
                    LivingEntity t = enemiesNear(b, d.pos, 20).stream().findFirst().orElse(null);
                    if (t != null) {
                        Vec3 from = d.pos.add(0, 1.2, 0);
                        Vec3 v = t.getBoundingBox().getCenter().subtract(from).normalize().scale(1.4);
                        WazaWorld.add(new WazaWorld.Bolt(c, from, v, 0.3F, 30, -1, whole(b, w) * 0.2F));
                    }
                }
            }
            case "WALL" -> {
                for (Projectile p : b.level().getEntitiesOfClass(Projectile.class, new AABB(d.pos, d.pos).inflate(3),
                    q -> q.getOwner() instanceof LivingEntity o && b.validEnemy(o))) {
                    p.discard();
                }
                if (a % 20 == 0) {
                    for (LivingEntity f : friendsNear(b, 6)) {
                        if (f.position().distanceTo(d.pos) < 5) {
                            f.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 30, 0));
                        }
                    }
                }
            }
            case "HEALER" -> {
                if (a % 20 == 0) {
                    for (LivingEntity f : friendsNear(b, 8)) {
                        if (f.position().distanceTo(d.pos) < 6) {
                            f.heal(Math.min(f.getMaxHealth() - f.getHealth(), f.getMaxHealth() * 0.04F));
                        }
                    }
                }
            }
            case "FORGE" -> {
                if (a % 40 == 0) {
                    for (LivingEntity f : friendsNear(b, 8)) {
                        f.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 60, 0));
                        f.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 60, 0));
                    }
                }
            }
            case "TRAP" -> {
                for (LivingEntity e : enemiesNear(b, d.pos, 1.6)) {
                    hurt(c, e, whole(b, w) * 0.6F);
                    enemyVerb(c, e, "BIND", true);
                    WazaWorld.remove(d);
                    return;
                }
            }
            default -> {
            }
        }
    }

    // ------------------------------------------------------------------------------------------------------- rewind

    private static void rewind(WazaEngine.Cast c) {
        SupremeEntity b = c.b;
        Waza w = c.w;
        int back = 40 + 20 * w.tier();
        if (w.kind().equals("ENEMY") && c.target != null) {
            WazaWorld.Snap s = WazaWorld.past(c.target, back);
            if (s != null) {
                Vec3 ok = valid(c.target, s.pos());
                if (ok != null) {
                    Vec3 was = c.target.position();
                    c.target.teleportTo(ok.x, ok.y, ok.z);
                    fx(c, 3, c.target, was.x, was.y, was.z, (float) was.distanceTo(ok));
                    c.note("rewound:enemy");
                }
            }
            return;
        }
        WazaWorld.Snap s = WazaWorld.past(b, back);
        if (s == null) {
            c.note("rewind:nothing kept");
            return;
        }
        float was = b.getHealth();
        if (s.health() > was) {
            // through heal(): a lore-bound body keeps its health in its soul, and heal() is how that is given back
            b.heal((s.health() - was) * 0.6F);
        }
        Vec3 ok = valid(b, s.pos());
        Vec3 from = b.position();
        double moved = 0;
        if (ok != null && ok.distanceTo(from) > 0.5) {
            b.teleportTo(ok.x, ok.y, ok.z);
            moved = ok.distanceTo(from);
        }
        fx(c, 3, b, from.x, from.y, from.z, b.getHealth() - was);
        c.note("rewound:self " + Math.round(b.getHealth() - was) + " moved " + Math.round(moved));
    }

    // -------------------------------------------------------------------------------------------------------- learning

    private static void adapt(WazaEngine.Cast c) {
        SupremeEntity b = c.b;
        Waza w = c.w;
        String tag = WazaWorld.observedTag(b);
        if (tag != null) {
            WazaWorld.learn(b, tag, 200 + 100 * w.tier());
            fx(c, 4, b, b.getX(), b.getY() + b.getBbHeight(), b.getZ(), tagIndex(tag));
            c.note("learned:" + tag);
            return;
        }
        // nothing seen twice yet: look at the enemy and note what it fights with (the counter waits for proof)
        if (c.target != null) {
            ItemStack held = c.target.getMainHandItem();
            String seen = held.getItem() instanceof BowItem || held.getItem() instanceof CrossbowItem || held.getItem() instanceof TridentItem
                ? "projectile" : held.isEmpty() ? "melee" : "melee";
            WazaWorld.observe(b, seen, 1);
            c.note("observed:" + seen);
        }
    }

    static int tagIndex(String tag) {
        return switch (tag) {
            case "melee" -> 0;
            case "projectile" -> 1;
            case "magic" -> 2;
            case "fire" -> 3;
            case "explosion" -> 4;
            default -> 5;
        };
    }

    // ------------------------------------------------------------------------------------------------------ contracts

    /** The players within reach a contract can be offered to. */
    static List<ServerPlayer> players(SupremeEntity b, double reach) {
        List<ServerPlayer> l = new ArrayList<>();
        for (Player p : b.level().getEntitiesOfClass(Player.class, b.getBoundingBox().inflate(reach))) {
            if (p instanceof ServerPlayer sp && !sp.isSpectator()) {
                l.add(sp);
            }
        }
        for (ServerPlayer sp : WazaTest.signers(b)) {
            if (!l.contains(sp)) {
                l.add(sp);
            }
        }
        return l;
    }

    static ServerPlayer pactPartner(SupremeEntity b, Waza w) {
        long now = b.level().getGameTime();
        for (ServerPlayer sp : players(b, Math.max(6, w.range()))) {
            if (w.kind().equals("COLLECT")) {
                if (WazaWorld.contracts(b).stream().anyMatch(k -> k.player.equals(sp.getUUID()) && k.state == 1 && !k.paid)) {
                    return sp;
                }
                continue;
            }
            if (asked(b, sp, now)) {
                continue;
            }
            return sp;
        }
        return null;
    }

    /**
     * Whether this player was asked lately: a contract still waiting for the answer, one still owed, or one refused
     * in the last minute (the screen is not pushed on a player again and again).
     */
    static boolean asked(SupremeEntity b, ServerPlayer sp, long now) {
        return WazaWorld.contracts(b).stream().anyMatch(k -> k.player.equals(sp.getUUID())
            && (k.state == 0 || k.state == 1 && !k.paid || k.state == 2 && now - k.expires + 400 < 1200));
    }

    private static String benefitText(Waza w) {
        return w.has("MIGHT") ? "力の強化（30秒）と体力の回復" : w.has("WARD") ? "守りの加護（30秒）と体力の回復" : "体力の回復と幸運の守り（30秒）";
    }

    private static String costText(Waza w) {
        return "60秒後に、30秒間の衰弱と鈍足（支払期限）";
    }

    private static void pact(WazaEngine.Cast c) {
        SupremeEntity b = c.b;
        Waza w = c.w;
        double reach = Math.max(6, w.range());
        switch (w.kind()) {
            case "COLLECT" -> {
                // only what was agreed and is still owed is collected, once; a player who never agreed owes nothing
                int got = 0;
                for (WazaWorld.Contract k : WazaWorld.contracts(b)) {
                    if (k.state == 1 && !k.paid) {
                        ServerPlayer p = WazaWorld.signer(k);
                        if (p != null && p.distanceTo(b) <= reach * 2) {
                            payCost(k, p);
                            got++;
                        }
                    }
                }
                c.note("collected:" + got);
            }
            case "GIFT" -> {
                // a gift with no price: nothing to agree to
                for (LivingEntity f : friendsNear(b, reach)) {
                    f.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 100, 0));
                }
                for (ServerPlayer p : players(b, reach)) {
                    p.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 100, 0));
                    p.displayClientMessage(Component.literal("〈" + w.name() + "〉: 代償のない贈り物を受け取った"), true);
                }
                c.note("gift");
            }
            default -> {
                int offered = 0;
                long now = b.level().getGameTime();
                for (ServerPlayer sp : players(b, reach)) {
                    if (!c.forced && asked(b, sp, now)) {
                        continue;
                    }
                    WazaWorld.offer(b, w, sp, benefitText(w), costText(w));
                    offered++;
                }
                c.note("offered:" + offered);
            }
        }
    }

    /** The player agreed (or refused): only now is anything given or owed. */
    static void contractAnswered(WazaWorld.Contract k, ServerPlayer p) {
        Waza w = k.w;
        if (k.state == 1) {
            p.heal(p.getMaxHealth() * 0.3F);
            p.addEffect(new MobEffectInstance(w.has("MIGHT") ? MobEffects.DAMAGE_BOOST : MobEffects.DAMAGE_RESISTANCE, 600, 0));
            p.addEffect(new MobEffectInstance(MobEffects.LUCK, 600, 0));
            k.payAt = p.level().getGameTime() + 1200;
            p.displayClientMessage(Component.literal("〈" + w.name() + "〉の契約に同意した。60秒後に代償を支払う"), false);
            WazaNet.toWatchers(k.owner, new WazaNet.Fx(8, w.index(), p.getId(), p.getX(), p.getY() + 1, p.getZ(), 1));
        } else {
            p.displayClientMessage(Component.literal("〈" + w.name() + "〉の契約を断った。代償は生じない"), true);
        }
    }

    static void payCost(WazaWorld.Contract k, ServerPlayer p) {
        if (k.paid || k.state != 1) {
            return;
        }
        k.paid = true;
        p.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 600, 0));
        p.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 600, 0));
        p.displayClientMessage(Component.literal("〈" + k.w.name() + "〉の契約の代償を支払った（衰弱と鈍足30秒）"), false);
        WazaNet.toWatchers(k.owner, new WazaNet.Fx(8, k.w.index(), p.getId(), p.getX(), p.getY() + 1, p.getZ(), 2));
    }

    // --------------------------------------------------------------------------------------------------------- curses

    /** A curse's mark goes off: its damage by its stacks, and what the curse carries (a withering, by default). */
    static void curseFires(WazaWorld.Mark m, LivingEntity t) {
        SupremeEntity b = m.owner;
        Waza w = m.w;
        WazaEngine.Cast c = WazaEngine.current(b);
        if (c == null || c.w != w) {
            c = new WazaEngine.Cast(w, b, t, b.level().getGameTime(), 0, true);
        }
        float amount = whole(b, w) * 0.7F * (0.5F + 0.5F * m.stacks / 3F);
        hurt(c, t, amount);
        List<String> vs = w.verbs().stream().filter(v -> !isSupport(v)).toList();
        for (String v : vs.isEmpty() ? List.of("WITHER") : vs) {
            enemyVerb(c, t, v, true);
        }
        fx(c, 7, t, t.getX(), t.getY() + t.getBbHeight(), t.getZ(), m.stacks);
    }
}
