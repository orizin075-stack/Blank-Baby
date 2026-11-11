package jp.oror.reborn.safety;

import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.phys.Vec3;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (059) No entity moves more than 64 blocks in one step, nor by a vector that is not a number (SaneMoveMixin, at the
 * head of Entity.move). A move's collisions are sought over the whole box it sweeps, a chunk lookup a column: the
 * thirteenth CI run's server froze in one (a vex in an Epic Fight attack's motion, its step sweeping chunk after chunk),
 * the kind of stall that makes a world "heavy" at random. A real step is never near the cap; teleports do not move.
 */
public final class SaneMoves {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Safety");
    private static final double MAX = 64.0;
    public static int capped, invalid;

    private SaneMoves() {
    }

    public static Vec3 check(Entity e, Vec3 v) {
        double x = v.x, y = v.y, z = v.z;
        if (!Double.isFinite(x) || !Double.isFinite(y) || !Double.isFinite(z)) {
            invalid++;
            if (invalid <= 3) {
                LOG.warn("SANE-MOVE: {} at {} was to move by {}: not moved", EntityType.getKey(e.getType()), e.blockPosition().toShortString(), v);
            }
            e.setDeltaMovement(Vec3.ZERO);
            return Vec3.ZERO;
        }
        double l2 = x * x + y * y + z * z;
        if (l2 > MAX * MAX) {
            capped++;
            if (capped <= 3) {
                LOG.warn("SANE-MOVE: {} at {} was to move {} blocks in one step: cut to {}", EntityType.getKey(e.getType()),
                    e.blockPosition().toShortString(), Math.round(Math.sqrt(l2)), (int) MAX);
            }
            return v.scale(MAX / Math.sqrt(l2));
        }
        return v;
    }

    public static String report() {
        return "capped=" + capped + " invalid=" + invalid;
    }
}
