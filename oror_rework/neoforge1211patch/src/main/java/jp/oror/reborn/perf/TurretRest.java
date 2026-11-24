package jp.oror.reborn.perf;

import java.util.Map;
import java.util.WeakHashMap;
import jp.oror.reborn.vehicle.RoyalPilots;
import jp.oror.reborn.vehicle.Sbw;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;

/**
 * (059d) The user: "very heavy". In the capital nearly half the server thread went to Superb Warfare's vehicles (CI 17's
 * capital profile: VehicleEntity.baseTick 41% of the samples, its move 26%, the box-against-the-world collision under it
 * 16%), most of them the kingdom's turrets (168 of them), which never move: each tick the turret's gravity pulls it into
 * its floor and its move works out, block by block round its box, that the floor holds it.
 * <p>
 * A still machine of the kingdom (a crewed turret: its engine FIXED or none) standing on its floor and not pushed sideways
 * now skips that move nineteen ticks in twenty: its fall is undone instead (it stays where it is, on its floor). On the
 * twentieth it moves as before, so that one whose floor is blown away falls within a second. Its turning and firing are
 * not moves and go on every tick. A tank, a helicopter, an aircraft moves as before.
 */
public final class TurretRest {
    private static final Map<Entity, Boolean> STILL = new WeakHashMap<>();
    public static long skipped;

    private TurretRest() {
    }

    public static long parkedSkipped;

    /**
     * True when this move of v may be skipped (the server's): a still turret of the kingdom's at rest on its floor, or
     * (r70, the user: "かなり重い") any machine standing parked on the ground, a player not at its controls: the
     * capital's tanks, helicopters and aircraft on their pads went through their whole box-against-the-world move every
     * tick to find that they stay where they are (CI's capital profile: Superb Warfare's vehicles 31% of the server
     * thread, their move 17%). One whose move is more than its own weight's pull (driven, pushed, lifting, falling) moves
     * as before, and every twentieth tick each moves as before, so that one whose ground goes falls within a second.
     */
    public static boolean resting(Entity v, Vec3 step) {
        if (v.level().isClientSide() || !v.onGround() || v.getControllingPassenger() instanceof net.minecraft.world.entity.player.Player
            || (v.tickCount + v.getId()) % 20 == 0) {
            return false;
        }
        if (step.y > 1.0E-3 || step.y < -0.6) {
            return false;
        }
        double side = step.x * step.x + step.z * step.z;
        if (!v.getTags().contains(RoyalPilots.CREWED) || !still(v)) {
            // a machine with an engine, or not the kingdom's: only when it is not moving at all (an engine starting
            // gives far more than this in its first tick)
            if (side > 1.0E-8 || v.isVehicle() && v.getControllingPassenger() == null && v.getPassengers().stream().anyMatch(e -> e instanceof net.minecraft.world.entity.player.Player)) {
                return false;
            }
            v.setDeltaMovement(Vec3.ZERO);
            parkedSkipped++;
            return true;
        }
        if (side > 1.0E-6) {
            return false;
        }
        v.setDeltaMovement(Vec3.ZERO);
        skipped++;
        return true;
    }

    private static boolean still(Entity v) {
        Boolean still = STILL.get(v);
        if (still == null) {
            String engine;
            try {
                engine = Sbw.engine(v);
            } catch (RuntimeException e) {
                engine = "?";
            }
            still = engine.equals("FIXED") || engine.equals("EMPTY") || engine.isEmpty();
            STILL.put(v, still);
        }
        return still;
    }
}
