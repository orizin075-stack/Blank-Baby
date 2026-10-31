package jp.oror.reborn.vehicle;

import java.util.List;
import java.util.function.Consumer;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.royal.RoyalRegistry;
import jp.oror.reborn.royal.RoyalRole;
import jp.oror.reborn.royal.RoyalSovereign;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.EntityTickEvent;

/**
 * Royal soldiers crew Superb Warfare vehicles and fight with them on their own. Superb Warfare already lets a mob in a
 * seat aim that seat's turret or weapon station at the vehicle's AI target and fire when on target; this class is the
 * driver and the pilot it lacks (its loiter autopilot runs on a player's client).
 *
 * Tanks and other ground vehicles drive at the crew's target to a stand-off distance and hold there while the gunner
 * fires, back off when an enemy is too close, work themselves free when stuck, and return to their post when there is
 * nothing to fight. Aircraft wait on their runway; with an enemy about they take off along it, climb, attack in diving
 * runs (pulling up early enough), and when the sky has been clear for half a minute they fly back, line up with the
 * runway, glide down, touch down, brake and park. Everything a vehicle needs to remember (mode, post, runway, flight
 * log) is in its persistent data, so it survives saving.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class RoyalPilots {
    public static final String CREWED = "oror_crewed";
    static final String KEY = "OrorPilot";
    private static final double STANDOFF = 26, TOO_CLOSE = 10, CRUISE = 45, GLIDE = 0.1, GATE = 150;

    private RoyalPilots() {
    }

    /** A vehicle of the given Superb Warfare id at a place, facing yaw, charged and armed, with seats royal soldiers aboard. */
    public static Entity deploy(ServerLevel level, Vec3 at, float yaw, String id, int seats, Consumer<Mob> crewSink) {
        if (!Sbw.present() || !Sbw.has(id)) {
            return null;
        }
        Entity v = BuiltInRegistries.ENTITY_TYPE.get(Sbw.id(id)).create(level);
        if (v == null) {
            return null;
        }
        v.moveTo(at.x, at.y, at.z, yaw, 0F);
        if (!level.addFreshEntity(v)) {
            return null;
        }
        v.addTag(CREWED);
        CompoundTag p = new CompoundTag();
        p.putLong("Home", BlockPos.containing(at).asLong());
        p.putFloat("Heading", yaw);
        p.putDouble("RunwayY", at.y);
        p.putString("Mode", "ground");
        v.getPersistentData().put(KEY, p);
        Sbw.charge(v);
        arm(v);
        for (int i = 0; i < seats; i++) {
            RoyalMob m = RoyalRegistry.TYPES.get(i == 0 ? RoyalRole.IMPERIAL : RoyalRole.GUARD).create(level);
            if (m == null) {
                continue;
            }
            m.moveTo(at.x, at.y, at.z, yaw, 0F);
            m.setPersistenceRequired();
            level.addFreshEntity(m);
            m.startRiding(v, true);
            if (crewSink != null) {
                crewSink.accept(m);
            }
        }
        if ("AIRCRAFT".equals(Sbw.engine(v))) {
            p.putString("Mode", runway(level, at, yaw) ? "parked" : "launch");
        }
        return v;
    }

    /** True if there is a straight, level strip of 150 blocks ahead to take off from (and land on). */
    public static boolean runway(ServerLevel level, Vec3 at, float yaw) {
        Vec3 f = Vec3.directionFromRotation(0, yaw);
        Vec3 side = new Vec3(-f.z, 0, f.x);
        int y = Mth.floor(at.y);
        for (int d = 0; d <= 150; d += 3) {
            for (int s = -2; s <= 2; s += 2) {
                Vec3 q = at.add(f.scale(d)).add(side.scale(s));
                if (!level.hasChunk(Mth.floor(q.x) >> 4, Mth.floor(q.z) >> 4)) {
                    continue;           // not loaded yet: a built runway is taken on trust
                }
                int top = level.getHeight(Heightmap.Types.MOTION_BLOCKING, Mth.floor(q.x), Mth.floor(q.z));
                if (top > y + 1 || top < y - 3) {
                    return false;
                }
            }
        }
        return true;
    }

    private static void arm(Entity v) {
        boolean air = "AIRCRAFT".equals(Sbw.engine(v)) || "HELICOPTER".equals(Sbw.engine(v));
        String[][] load = air
            ? new String[][]{{"small_shell_ap", "64"}, {"small_shell_ap", "64"}, {"small_shell_he", "64"}, {"large_anti_ground_missile", "4"}, {"small_rocket", "16"}}
            : new String[][]{{"large_shell_he", "16"}, {"large_shell_ap", "16"}, {"rifle_ammo", "64"}, {"heavy_ammo", "64"}, {"large_shell_he", "16"}};
        int slot = 0;
        for (String[] l : load) {
            if (BuiltInRegistries.ITEM.containsKey(Sbw.id(l[0]))) {
                Item item = BuiltInRegistries.ITEM.get(Sbw.id(l[0]));
                Sbw.call(v, "setItem", slot++, item.getDefaultInstance().copyWithCount(Math.min(item.getDefaultMaxStackSize(), Integer.parseInt(l[1]))));
            }
        }
    }

    @SubscribeEvent
    public static void tick(EntityTickEvent.Post e) {
        Entity v = e.getEntity();
        if (v.level().isClientSide || !v.getTags().contains(CREWED) || !v.isAlive()) {
            return;
        }
        CompoundTag p = v.getPersistentData().getCompound(KEY);
        VehicleWatch.watch(v, p);
        if (Sbw.wreck(v)) {
            v.getPersistentData().put(KEY, p);
            return;
        }
        if (v.tickCount % 1200 == 0) {
            Sbw.charge(v);
            arm(v);
        }
        log(v, p);
        Mob driver = v.getFirstPassenger() instanceof Mob m ? m : null;
        if (driver == null) {
            Sbw.keys(v, false, false, false, false, false, "AIRCRAFT".equals(Sbw.engine(v)) && v.onGround());
            Sbw.mouse(v, 0, 0);
            return;
        }
        LivingEntity target = target(v, p);
        if (v.tickCount % 10 == 0) {
            // a ground vehicle holds its fire while the line to the target runs into the ground or a wall: its shells
            // would only blast a crater at its own tracks
            Sbw.aim(v, target != null && (Sbw.engine(v).equals("AIRCRAFT") || lineOfFire(v, target)) ? target : null);
            for (Entity rider : v.getPassengers()) {
                if (rider instanceof Mob m && target != null && m.getTarget() != target) {
                    m.setTarget(target);
                }
            }
        }
        String engine = Sbw.engine(v);
        if (engine.equals("AIRCRAFT")) {
            fly(v, p, target);
        } else if (engine.equals("HELICOPTER")) {
            hover(v, p, target);
        } else if (!engine.equals("HELICOPTER") && !engine.equals("FIXED") && !engine.equals("EMPTY") && !engine.isEmpty()) {
            drive(v, p, target);
        }
        v.getPersistentData().put(KEY, p);
    }

    /**
     * The crew's enemy: any rider's living target, else the one the vehicle went after last (a soldier drops a target
     * beyond his own follow range, the vehicle keeps it while it lives, stays within reach and was seen in the last
     * twenty seconds), else (every second) the nearest hostile the royals would fight.
     */
    private static LivingEntity target(Entity v, CompoundTag p) {
        long now = v.level().getGameTime();
        boolean air = "AIRCRAFT".equals(Sbw.engine(v));
        for (Entity rider : v.getPassengers()) {
            if (rider instanceof Mob m && m.getTarget() != null && m.getTarget().isAlive() && !m.isAlliedTo(m.getTarget())) {
                p.putUUID("Target", m.getTarget().getUUID());
                p.putLong("TargetSeen", now);
                return m.getTarget();
            }
        }
        if (p.hasUUID("Target") && v.level() instanceof ServerLevel level && now - p.getLong("TargetSeen") < 400
            && level.getEntity(p.getUUID("Target")) instanceof LivingEntity kept && kept.isAlive()
            && kept.distanceToSqr(v) < (air ? 220 * 220 : 96 * 96)) {
            if (v.tickCount % 20 == 7) {
                p.putLong("TargetSeen", now);
            }
            return kept;
        }
        p.remove("Target");
        if (v.tickCount % 20 != 7) {
            return null;
        }
        List<LivingEntity> near = v.level().getEntitiesOfClass(LivingEntity.class, v.getBoundingBox().inflate(air ? 160 : 64, air ? 96 : 24, air ? 160 : 64),
            l -> l.isAlive() && RoyalSovereign.hostile(l) && !(l.getVehicle() != null && l.getVehicle() == v));
        LivingEntity best = null;
        double bestD = Double.MAX_VALUE;
        for (LivingEntity l : near) {
            double d = l.distanceToSqr(v);
            if (d < bestD) {
                bestD = d;
                best = l;
            }
        }
        if (best != null) {
            p.putUUID("Target", best.getUUID());
            p.putLong("TargetSeen", now);
            if (v.getFirstPassenger() instanceof Mob m) {
                m.setTarget(best);
            }
        }
        return best;
    }

    /** True if nothing solid is between the top of the vehicle and the target, nor within the last two blocks of it. */
    static boolean lineOfFire(Entity v, LivingEntity target) {
        Vec3 from = v.position().add(0, v.getBbHeight() * 0.85, 0);
        Vec3 to = target.getBoundingBox().getCenter();
        net.minecraft.world.phys.BlockHitResult hit = v.level().clip(new net.minecraft.world.level.ClipContext(from, to,
            net.minecraft.world.level.ClipContext.Block.COLLIDER, net.minecraft.world.level.ClipContext.Fluid.NONE, v));
        return hit.getType() == net.minecraft.world.phys.HitResult.Type.MISS || hit.getLocation().distanceTo(to) < 2.0;
    }

    // ------------------------------------------------------------------------------------------------ ground vehicles

    private static void drive(Entity v, CompoundTag p, LivingEntity target) {
        Vec3 pos = v.position();
        Vec3 home = Vec3.atBottomCenterOf(BlockPos.of(p.getLong("Home")));
        int unstick = p.getInt("Unstick");
        if (unstick > 0) {
            p.putInt("Unstick", unstick - 1);
            boolean right = p.getBoolean("UnstickRight"), ahead = p.getBoolean("UnstickForward");
            Sbw.keys(v, ahead, !ahead, !right, right, true, false);
            return;
        }
        Vec3 goal;
        double hold;
        boolean back = false;
        if (target != null) {
            Vec3 d = target.position().subtract(pos).multiply(1, 0, 1);
            double dist = d.length();
            if (dist < TOO_CLOSE) {
                back = true;
                goal = target.position();
                hold = 0;
            } else if (dist > STANDOFF + 8) {
                goal = target.position().subtract(d.normalize().scale(STANDOFF));
                hold = 3;
            } else {
                goal = target.position();
                hold = Double.MAX_VALUE;
            }
            p.putString("Mode", "attack");
        } else {
            goal = home;
            hold = 3;
            p.putString("Mode", pos.distanceToSqr(home) > 16 ? "return" : "post");
        }
        Vec3 d = goal.subtract(pos).multiply(1, 0, 1);
        double dist = d.length();
        // which way the right key turns this vehicle is learnt from the vehicle itself (SteerSign: +1 when it raises the
        // yaw), so the steering below holds for every kind of tracked or wheeled vehicle
        int sign = p.contains("SteerSign") ? p.getInt("SteerSign") : 1;
        // and which way is its front: some models face backwards against their yaw (NoseBack, learnt in learnFacing)
        float heading = v.getYRot() + (p.getBoolean("NoseBack") ? 180F : 0F);
        float err = Mth.wrapDegrees(yawTo(d) - heading) * sign;
        boolean arrived = hold != Double.MAX_VALUE && dist <= hold;
        boolean forward, left = false, right = false;
        if (back) {
            // too close: back off, the nose kept toward the enemy (reversing, the steering is the other way round)
            forward = false;
            right = err < -8;
            left = err > 8;
        } else if (arrived || hold == Double.MAX_VALUE) {
            // at the stand-off: face the enemy, a short pivot on the spot
            forward = false;
            right = err > 8;
            left = err < -8;
        } else if (Math.abs(err) < 110) {
            // drive in an arc toward the goal: tracks turn while they roll
            forward = true;
            right = err > 6;
            left = err < -6;
        } else {
            // the goal is behind: a reversing turn brings the nose round
            forward = false;
            back = true;
            left = err > 0;
            right = err < 0;
        }
        Sbw.keys(v, forward, back, left, right, forward && dist > 40 && Math.abs(err) < 30, false);
        learnSteering(v, p, left, right, back);
        learnFacing(v, p, forward && !back);
        // stuck: pressing to move without moving, or turning without the heading changing, for two seconds backs it off
        // (or pulls it forward) at an angle for a second and a half
        double speed = v.getDeltaMovement().horizontalDistance();
        float yawNow = v.getYRot();
        boolean trying = forward || back || left || right;
        boolean moving = speed > 0.02 || Math.abs(Mth.wrapDegrees(yawNow - p.getFloat("LastYaw"))) > 0.4F;
        p.putFloat("LastYaw", yawNow);
        int still = trying && !moving ? p.getInt("Still") + 1 : 0;
        p.putInt("Still", still);
        if (still > 40) {
            p.putInt("Still", 0);
            p.putInt("Unstick", 30);
            p.putBoolean("UnstickRight", v.getRandom().nextBoolean());
            p.putBoolean("UnstickForward", back || !forward && v.getRandom().nextBoolean());
            p.putInt("Unsticks", p.getInt("Unsticks") + 1);
        }
    }

    /**
     * Keeps NoseBack: while driven forward and moving, whether it moves along its yaw or against it; fifteen ticks
     * more against than along (net) and the front is taken to be the other way.
     */
    private static void learnFacing(Entity v, CompoundTag p, boolean forward) {
        Vec3 m = v.getDeltaMovement().multiply(1, 0, 1);
        if (!forward || m.length() < 0.05) {
            return;
        }
        double dot = m.normalize().dot(Vec3.directionFromRotation(0, v.getYRot()));
        int score = Mth.clamp(p.getInt("FacingScore") + (dot < -0.5 ? 1 : dot > 0.5 ? -1 : 0), -40, 40);
        p.putInt("FacingScore", score);
        boolean back = p.getBoolean("NoseBack");
        if (score >= 15 && !back || score <= -15 && back) {
            p.putBoolean("NoseBack", !back);
            p.putInt("FacingScore", 0);
            p.putInt("FacingFlips", p.getInt("FacingFlips") + 1);
        }
    }

    /**
     * Keeps SteerSign: over the ticks the vehicle is steered one way, whether its yaw went the way the sign says; after
     * twelve ticks of it going the other way the sign flips.
     */
    private static void learnSteering(Entity v, CompoundTag p, boolean left, boolean right, boolean back) {
        float yaw = v.getYRot();
        float turned = Mth.wrapDegrees(yaw - p.getFloat("SteerYaw"));
        p.putFloat("SteerYaw", yaw);
        if (left == right || Math.abs(turned) < 0.3F) {
            return;
        }
        int sign = p.contains("SteerSign") ? p.getInt("SteerSign") : 1;
        // forward: right should raise the yaw by the sign; reversing turns the other way round
        int expected = (right ? 1 : -1) * (back ? -1 : 1) * sign;
        int wrong = Math.signum(turned) == expected ? 0 : p.getInt("SteerWrong") + 1;
        p.putInt("SteerWrong", wrong);
        if (wrong >= 12) {
            p.putInt("SteerSign", -sign);
            p.putInt("SteerWrong", 0);
            p.putInt("SteerFlips", p.getInt("SteerFlips") + 1);
        }
    }

    // ------------------------------------------------------------------------------------------------ aircraft

    private static void fly(Entity v, CompoundTag p, LivingEntity target) {
        String mode = p.getString("Mode");
        long now = v.level().getGameTime();
        float heading = p.getFloat("Heading");
        Vec3 home = Vec3.atBottomCenterOf(BlockPos.of(p.getLong("Home")));
        double runwayY = p.getDouble("RunwayY");
        Vec3 f = Vec3.directionFromRotation(0, heading);
        double speed = v.getDeltaMovement().length();
        if (target != null) {
            p.putLong("LastEnemy", now);
        }
        boolean quiet = now - p.getLong("LastEnemy") > 600;
        switch (mode) {
            case "parked" -> {
                Sbw.keys(v, false, false, false, false, false, true);
                Sbw.mouse(v, 0, 0);
                if (target != null) {
                    mode = "roll";
                    p.putLong("Since", now);
                }
            }
            case "launch" -> {
                // no runway: a catapult start, straight into the climb
                v.setPos(v.getX(), Math.max(v.getY() + 30, groundAt(v, v.position()) + 30), v.getZ());
                v.setDeltaMovement(f.scale(1.6));
                Sbw.call(v, "setPower", 1.5F);
                Sbw.call(v, "setEngineStart", true);
                Sbw.call(v, "setEngineStartOver", true);
                p.putBoolean("NoRunway", true);
                mode = "climb";
                p.putLong("Since", now);
            }
            case "roll" -> {
                // take-off run along the runway, full power, kept on its centre line
                Vec3 ahead = home.add(f.scale(200));
                float err = Mth.wrapDegrees(yawTo(ahead.subtract(v.position())) - v.getYRot());
                Sbw.keys(v, true, false, false, false, true, false);
                Sbw.mouse(v, Mth.clamp(err / 6.0, -1, 1), 0);
                if (!v.onGround() && v.getY() > runwayY + 2.5) {
                    mode = "climb";
                    p.putLong("Since", now);
                    p.putBoolean("TookOff", true);
                } else if (now - p.getLong("Since") > 500) {
                    mode = "rollout";
                    p.putInt("Aborts", p.getInt("Aborts") + 1);
                }
            }
            case "climb" -> {
                double cruise = cruise(v, home, target);
                steer(v, target != null ? target.position() : home.add(f.scale(120)), cruise, true, -18);
                if (v.getY() > cruise - 8 || now - p.getLong("Since") > 400) {
                    mode = "patrol";
                    p.putLong("Since", now);
                }
            }
            case "patrol" -> {
                double cruise = cruise(v, home, target);
                if (target != null) {
                    double h = target.position().subtract(v.position()).horizontalDistance();
                    float err = Mth.wrapDegrees(yawTo(target.position().subtract(v.position())) - v.getYRot());
                    // a run only from high enough to pull out of it
                    if (h < 160 && h > 70 && Math.abs(err) < 20 && v.getY() - target.getY() > 40) {
                        mode = "dive";
                        p.putLong("Since", now);
                    } else {
                        steer(v, target.position(), cruise, true, 0);
                    }
                } else if (quiet && !p.getBoolean("NoRunway")) {
                    mode = "return";
                    p.putLong("Since", now);
                } else {
                    // circle the post
                    Vec3 r = v.position().subtract(home).multiply(1, 0, 1);
                    Vec3 tangent = r.lengthSqr() < 1 ? f : new Vec3(-r.z, 0, r.x).normalize();
                    Vec3 aim = home.add(r.normalize().scale(90)).add(tangent.scale(60));
                    steer(v, aim, cruise, false, 0);
                }
            }
            case "dive" -> {
                if (target == null) {
                    mode = "patrol";
                    break;
                }
                Vec3 to = target.getBoundingBox().getCenter().subtract(v.position());
                double h = to.horizontalDistance();
                float wantPitch = (float) Mth.clamp(Math.toDegrees(Math.atan2(-to.y, h)), -10, 28);
                aimNose(v, yawTo(to), wantPitch, speed < 1.4);
                // pull out with room to spare: the faster it sinks, the higher it starts
                double sink = Math.max(0, -v.getDeltaMovement().y);
                double clearance = v.getY() - Math.max(groundAt(v, v.position()), target.getY());
                if (h < 35 || clearance < 24 + 16 * sink || now - p.getLong("Since") > 200) {
                    mode = "pullup";
                    p.putLong("Since", now);
                    p.putInt("Runs", p.getInt("Runs") + 1);
                }
            }
            case "pullup" -> {
                // nose up at full power until climbing again and clear of the ground, then back to the patrol; a slow
                // aircraft keeps its nose lower so as not to stall
                steer(v, v.position().add(Vec3.directionFromRotation(0, v.getYRot()).scale(100)), cruise(v, home, target), true,
                    speed < 1.0 ? -10 : -25);
                long t = now - p.getLong("Since");
                boolean clear = v.getDeltaMovement().y > 0 && v.getY() - groundAt(v, v.position()) > 30;
                if (t > 40 && clear || t > 160) {
                    mode = "patrol";
                }
            }
            case "return" -> {
                // to a point on the extended centre line, GATE blocks before the threshold
                Vec3 gate = home.subtract(f.scale(GATE));
                steer(v, gate, runwayY + 28, false, 0);
                if (target != null) {
                    mode = "patrol";
                } else if (v.position().subtract(gate).horizontalDistance() < 30) {
                    mode = "approach";
                    p.putLong("Since", now);
                }
            }
            case "approach" -> {
                Vec3 touch = home.add(f.scale(25));
                Vec3 rel = touch.subtract(v.position());
                double along = rel.dot(f);
                double glide = runwayY + 1.5 + Math.max(0, along) * GLIDE;
                Vec3 aim = touch.add(f.scale(Math.max(20, -along)));
                boolean slow = speed > 1.35, fast = speed < 0.9;
                steerSpeed(v, aim, glide, fast, slow);
                if (v.onGround()) {
                    mode = "rollout";
                    p.putLong("Since", now);
                    p.putBoolean("Landed", true);
                } else if (along < -120 || v.getY() > glide + 25 || now - p.getLong("Since") > 900) {
                    mode = "return";
                    p.putInt("GoArounds", p.getInt("GoArounds") + 1);
                }
            }
            case "rollout" -> {
                Sbw.keys(v, false, true, false, false, false, true);
                Sbw.mouse(v, 0, 0);
                if (speed < 0.05 || now - p.getLong("Since") > 400) {
                    mode = "parked";
                    p.putLong("Home", v.blockPosition().asLong());
                    p.putFloat("Heading", v.getYRot());
                    p.putDouble("RunwayY", v.getY());
                }
            }
            default -> mode = "parked";
        }
        // terrain ahead: whatever the mode, never fly into the ground. Where the aircraft will be in one to two seconds
        // on its present course (climb or sink included) must stay ten blocks above the ground there.
        if (!v.onGround() && !mode.equals("approach") && !mode.equals("rollout") && !mode.equals("parked")) {
            Vec3 m = v.getDeltaMovement();
            boolean danger = false;
            for (float side : new float[]{0F, -25F, 25F}) {
                Vec3 course = side == 0F ? m : m.yRot(side * Mth.DEG_TO_RAD);
                for (int t = 5; t <= 50 && !danger; t += 5) {
                    Vec3 at = v.position().add(course.scale(t));
                    danger = at.y - groundAt(v, at) < (side == 0F ? 12 : 6);
                }
            }
            if (danger) {
                steer(v, v.position().add(Vec3.directionFromRotation(0, v.getYRot()).scale(100)), v.getY() + 40, true,
                    speed < 1.0 ? -12 : -30);
                if (mode.equals("dive") || mode.equals("patrol") || mode.equals("climb")) {
                    mode = "pullup";
                    p.putLong("Since", now);
                }
                p.putInt("TerrainSaves", p.getInt("TerrainSaves") + 1);
            }
        }
        p.putString("Mode", mode);
    }

    /**
     * Helicopters: lift off on the collective, hold 22 blocks over the ground (or the enemy), turn to face the enemy and
     * fly at it to a stand-off of 35 blocks for the gunner, and with nothing to fight go back over the pad and settle on
     * it. The first three seconds are a lift test (collective only), whose climb goes in the log.
     */
    private static void hover(Entity v, CompoundTag p, LivingEntity target) {
        long now = v.level().getGameTime();
        Vec3 pos = v.position();
        Vec3 home = Vec3.atBottomCenterOf(BlockPos.of(p.getLong("Home")));
        if (!p.contains("HeliStart")) {
            p.putLong("HeliStart", now);
            p.putDouble("HeliY0", pos.y);
        }
        if (now % 20 == 0) {
            Sbw.call(v, "setEngineStart", true);
            Sbw.call(v, "setEngineStartOver", true);
        }
        long t = now - p.getLong("HeliStart");
        if (t < 60) {
            p.putString("Mode", "lift-test");
            Sbw.heliKeys(v, false, false, false, false, true, false);
            Sbw.mouse(v, 0, 0);
            return;
        }
        if (t == 60) {
            double climbed = pos.y - p.getDouble("HeliY0");
            // a helicopter whose own controls did not lift it is flown by hand (Assist): its motion and heading set here
            p.putBoolean("Assist", climbed < 0.5);
            LOG.info(String.format(java.util.Locale.ROOT, "HELI-LIFT {\"id\":\"%s\",\"climbed\":%.2f,\"power\":%.2f,\"vy\":%.2f,\"assist\":%b}",
                BuiltInRegistries.ENTITY_TYPE.getKey(v.getType()).getPath(), climbed, Sbw.power(v), v.getDeltaMovement().y, climbed < 0.5));
        }
        double ground = groundAt(v, pos);
        Vec3 goal;
        double altitude;
        Vec3 face;
        if (target != null) {
            Vec3 off = pos.subtract(target.position()).multiply(1, 0, 1);
            off = off.lengthSqr() < 1 ? Vec3.directionFromRotation(0, v.getYRot()).scale(-1) : off.normalize();
            goal = target.position().add(off.scale(35));
            altitude = Math.max(ground, target.getY()) + 22;
            face = target.position().subtract(pos);
            p.putString("Mode", "attack");
        } else {
            goal = home;
            boolean over = pos.subtract(home).horizontalDistance() < 4;
            altitude = over ? home.y : Math.max(ground, home.y) + 22;
            face = home.subtract(pos);
            p.putString("Mode", over ? "settle" : "return");
        }
        // keep clear of the ground ahead too
        Vec3 ahead = pos.add(v.getDeltaMovement().multiply(20, 0, 20));
        altitude = Math.max(altitude, groundAt(v, ahead) + 12);
        double dist = goal.subtract(pos).horizontalDistance();
        float err = Mth.wrapDegrees(yawTo(face) - v.getYRot());
        boolean up = pos.y < altitude - 1.5, down = pos.y > altitude + 2.5 && !(v.onGround());
        boolean forward = dist > 6 && Math.abs(err) < 35 && pos.y > ground + 6;
        boolean back = dist < 3 && v.getDeltaMovement().horizontalDistance() > 0.3;
        Sbw.heliKeys(v, forward, back, false, false, up, down);
        Sbw.mouse(v, Mth.clamp(err / 10.0, -2, 2), 0);
        if (p.getBoolean("Assist")) {
            // by hand: turn toward the enemy (or the pad) six degrees a tick, climb or sink to the height wanted, and
            // move toward the goal once high enough, at most 0.7 blocks a tick, easing into each change
            float turn = Mth.clamp(err, -6F, 6F);
            v.setYRot(v.getYRot() + turn);
            v.setYBodyRot(v.getYRot());
            Vec3 flat = goal.subtract(pos).multiply(1, 0, 1);
            Vec3 move = pos.y > ground + 6 && flat.length() > 2 ? flat.normalize().scale(Math.min(0.7, flat.length() * 0.05)) : Vec3.ZERO;
            double climb = Mth.clamp((altitude - pos.y) * 0.08, -0.35, 0.4);
            Vec3 want = new Vec3(move.x, climb, move.z);
            v.setDeltaMovement(v.getDeltaMovement().scale(0.75).add(want.scale(0.25)));
            v.hasImpulse = true;
            v.fallDistance = 0;
        }
        if (now % 40 == 0) {
            LOG.info(String.format(java.util.Locale.ROOT, "HELI-TRACK {\"t\":%d,\"mode\":\"%s\",\"y\":%.1f,\"want\":%.1f,\"ground\":%.0f,\"dist\":%.1f,"
                    + "\"err\":%.0f,\"speed\":%.2f,\"vy\":%.2f,\"power\":%.2f,\"keys\":\"%s%s%s%s\"}",
                t, p.getString("Mode"), pos.y, altitude, ground, dist, err, v.getDeltaMovement().horizontalDistance(), v.getDeltaMovement().y,
                Sbw.power(v), forward ? "F" : "", back ? "B" : "", up ? "U" : "", down ? "D" : ""));
        }
    }

    private static final org.slf4j.Logger LOG = org.slf4j.LoggerFactory.getLogger("OROR Vehicles");

    /** The top of the ground at a column; a column of a chunk not loaded counts as the ground under the vehicle. */
    private static int groundAt(Entity v, Vec3 at) {
        int x = Mth.floor(at.x), z = Mth.floor(at.z);
        if (!v.level().hasChunk(x >> 4, z >> 4)) {
            x = Mth.floor(v.getX());
            z = Mth.floor(v.getZ());
            if (!v.level().hasChunk(x >> 4, z >> 4)) {
                return v.level().getMinBuildHeight();
            }
        }
        return v.level().getHeight(Heightmap.Types.MOTION_BLOCKING, x, z);
    }

    /** Cruising height: 45 above the post or the target, and 35 above the highest ground of the next 200 blocks ahead. */
    private static double cruise(Entity v, Vec3 home, LivingEntity target) {
        double base = Math.max(home.y, target == null ? home.y : target.getY());
        CompoundTag p = v.getPersistentData().getCompound(KEY);
        // the highest ground all round (eight bearings out to 160 blocks) and 200 blocks ahead, kept for two seconds:
        // a patrol circle or a turn at the enemy must not take it into a hillside
        long now = v.level().getGameTime();
        if (now - p.getLong("HighAt") > 40) {
            Vec3 dir = v.getDeltaMovement().multiply(1, 0, 1);
            dir = dir.lengthSqr() < 1.0E-4 ? Vec3.directionFromRotation(0, v.getYRot()) : dir.normalize();
            int high = groundAt(v, v.position());
            for (int d = 40; d <= 200; d += 40) {
                high = Math.max(high, groundAt(v, v.position().add(dir.scale(d))));
            }
            for (int b = 0; b < 8; b++) {
                Vec3 bearing = Vec3.directionFromRotation(0, b * 45F);
                for (int d = 40; d <= 160; d += 40) {
                    high = Math.max(high, groundAt(v, v.position().add(bearing.scale(d))));
                }
            }
            p.putInt("High", high);
            p.putLong("HighAt", now);
            v.getPersistentData().put(KEY, p);
        }
        return Math.max(base + CRUISE, p.getInt("High") + 40);
    }

    /** Toward a point at an altitude: yaw by the mouse's x, pitch from the altitude error by its y; minPitch < 0 forces a climb. */
    private static void steer(Entity v, Vec3 point, double altitude, boolean fullPower, float minPitch) {
        float wantPitch = (float) Mth.clamp(-(altitude - v.getY()) * 0.6, -22, 18);
        if (minPitch < 0) {
            wantPitch = Math.min(wantPitch, minPitch);
        }
        // a slow aircraft stalls: nose down to gather speed again (unless the ground is close below)
        double speed = v.getDeltaMovement().length();
        if (speed < 1.5 && !v.onGround() && v.getY() - groundAt(v, v.position()) > 20) {
            wantPitch = Math.max(wantPitch, speed < 0.8 ? 15 : 6);
        }
        aimNose(v, yawTo(point.subtract(v.position())), wantPitch, true);
    }

    private static void steerSpeed(Entity v, Vec3 point, double altitude, boolean faster, boolean slower) {
        float wantPitch = (float) Mth.clamp(-(altitude - v.getY()) * 0.8, -12, 14);
        float yawErr = Mth.wrapDegrees(yawTo(point.subtract(v.position())) - v.getYRot());
        float pitchErr = wantPitch - v.getXRot();
        Sbw.mouse(v, Mth.clamp(yawErr / 10.0, -2, 2), Mth.clamp(pitchErr / 3.0, -8, 8));
        Sbw.keys(v, faster, slower, false, false, false, false);
    }

    private static void aimNose(Entity v, float wantYaw, float wantPitch, boolean power) {
        float yawErr = Mth.wrapDegrees(wantYaw - v.getYRot());
        float pitchErr = wantPitch - v.getXRot();
        Sbw.mouse(v, Mth.clamp(yawErr / 10.0, -2, 2), Mth.clamp(pitchErr / 3.0, -8, 8));
        Sbw.keys(v, power, false, false, false, power, false);
    }

    private static float yawTo(Vec3 d) {
        return (float) (Mth.atan2(d.z, d.x) * Mth.RAD_TO_DEG) - 90F;
    }

    /** The flight and drive log: distance covered, time in the air, highest point above the runway. */
    private static void log(Entity v, CompoundTag p) {
        double moved = v.getDeltaMovement().horizontalDistance();
        if (moved > 0.01) {
            p.putDouble("Odometer", p.getDouble("Odometer") + moved);
        }
        if (!v.onGround()) {
            p.putInt("Airborne", p.getInt("Airborne") + 1);
            p.putDouble("MaxAlt", Math.max(p.getDouble("MaxAlt"), v.getY() - p.getDouble("RunwayY")));
        }
    }

    /** One line of JSON about a vehicle for the battle and flight reports. */
    public static String report(Entity v) {
        CompoundTag p = v.getPersistentData().getCompound(KEY);
        String id = BuiltInRegistries.ENTITY_TYPE.getKey(v.getType()).getPath();
        return String.format(java.util.Locale.ROOT,
            "{\"id\":\"%s\",\"engine\":\"%s\",\"alive\":%b,\"health\":%.2f,\"mode\":\"%s\",\"odometer\":%.1f,\"airborne\":%d,\"maxAlt\":%.1f,"
                + "\"tookOff\":%b,\"landed\":%b,\"runs\":%d,\"unsticks\":%d,\"goArounds\":%d,\"terrainSaves\":%d,\"crew\":%d,"
                + "\"power\":%.2f,\"energy\":%s,\"target\":%b,\"y\":%.1f,\"ground\":%d,\"vy\":%.2f,\"speed\":%.2f,\"pitch\":%.1f,"
                + "\"steerSign\":%d,\"steerFlips\":%d,\"noseBack\":%b,\"facingFlips\":%d}",
            id, Sbw.engine(v), v.isAlive() && !Sbw.wreck(v), Sbw.health(v), p.getString("Mode"), p.getDouble("Odometer"), p.getInt("Airborne"),
            p.getDouble("MaxAlt"), p.getBoolean("TookOff"), p.getBoolean("Landed"), p.getInt("Runs"), p.getInt("Unsticks"), p.getInt("GoArounds"),
            p.getInt("TerrainSaves"), v.getPassengers().size(), Sbw.power(v), Sbw.call(v, "getEnergy"), p.hasUUID("Target"),
            v.getY(), groundAt(v, v.position()), v.getDeltaMovement().y, v.getDeltaMovement().length(), v.getXRot(),
            p.contains("SteerSign") ? p.getInt("SteerSign") : 1, p.getInt("SteerFlips"), p.getBoolean("NoseBack"), p.getInt("FacingFlips"));
    }

    /** Royal soldiers posted to a vehicle (OrorMotor in their data) bring it out and board it the first time they act. */
    @SubscribeEvent
    public static void motorPool(EntityTickEvent.Post e) {
        if (!(e.getEntity() instanceof RoyalMob m) || m.level().isClientSide || m.tickCount % 20 != 1) {
            return;
        }
        CompoundTag d = m.getPersistentData();
        if (!d.contains("OrorMotor") || m.isPassenger() || !(m.level() instanceof ServerLevel level)) {
            return;
        }
        String id = d.getString("OrorMotor");
        int seats = Math.max(1, d.getInt("OrorMotorSeats"));
        float yaw = d.contains("OrorMotorYaw") ? d.getFloat("OrorMotorYaw") : m.getYRot();
        boolean still = d.getBoolean("OrorMotorStill");
        d.remove("OrorMotor");
        Entity v = deploy(level, m.position(), yaw, id, seats - 1, null);
        if (v != null) {
            m.startRiding(v, true);
            if (still) {
                // a turret's gunner: the turret aims and fires at the target the crew is given; he needs no mind of his own
                for (Entity rider : v.getPassengers()) {
                    if (rider instanceof net.minecraft.world.entity.Mob gunner) {
                        gunner.setNoAi(true);
                    }
                }
            }
            // the soldier who brought it drives; the others ride behind
            if (v.getPassengers().size() > 1 && v.getFirstPassenger() != m) {
                List<Entity> others = List.copyOf(v.getPassengers());
                for (Entity o : others) {
                    o.stopRiding();
                }
                m.startRiding(v, true);
                for (Entity o : others) {
                    if (o != m) {
                        o.startRiding(v, true);
                    }
                }
            }
        }
    }

    /** Crewed vehicles near a point, for reports. */
    public static List<Entity> near(ServerLevel level, Vec3 at, double r) {
        return level.getEntities((Entity) null, new AABB(at, at).inflate(r), x -> x.getTags().contains(CREWED));
    }

    static EntityType<?> type(String id) {
        return BuiltInRegistries.ENTITY_TYPE.get(Sbw.id(id));
    }
}
