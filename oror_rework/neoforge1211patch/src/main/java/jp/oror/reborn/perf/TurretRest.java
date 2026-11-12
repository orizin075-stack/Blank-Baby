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

    /** True when this move of v may be skipped (the server's, a still turret of the kingdom's at rest on its floor). */
    public static boolean resting(Entity v, Vec3 step) {
        if (v.level().isClientSide() || !v.onGround() || v.isVehicle() && v.getControllingPassenger() instanceof net.minecraft.world.entity.player.Player
            || !v.getTags().contains(RoyalPilots.CREWED) || (v.tickCount + v.getId()) % 20 == 0) {
            return false;
        }
        if (step.x * step.x + step.z * step.z > 1.0E-6 || step.y > 1.0E-3 || step.y < -0.6) {
            return false;
        }
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
        if (!still) {
            return false;
        }
        v.setDeltaMovement(Vec3.ZERO);
        skipped++;
        return true;
    }
}
