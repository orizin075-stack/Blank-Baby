package jp.oror.reborn.combat;

import jp.oror.reborn.royal.RoyalMob;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.pathfinder.Path;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.EntityTickEvent;

/**
 * (r65) A mob with a gun whose target is behind a wall goes round it to a spot it can shoot from. The gun mods' own AI
 * (JEG's, Pillager Guns', TACZ Bandits') and OROR's (AdaptiveCombat: a shooter inside ten blocks holds its ground) only
 * close in, so a pillager or bandit with its foe behind a house stood at the wall's face and never fired (GUN-MOBS: every
 * ground gunner's walled lane 0 hits in the last run, the golem 7.8 blocks off through the wall). After a second and a
 * half without a sight of its target, it looks round the target (sixteen ways, at its own range and nearer) for open
 * ground that sees the target and that it can walk to, nearest first, and goes there; a sight of its target ends it.
 * Not the royals (RoyalArmory brings their guns to bear) nor fliers.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class GunFlank {
    static final String BLIND = "OrorGunBlind", UNTIL = "OrorFlankUntil", SPOT = "OrorFlankSpot";
    /** Checked every ten ticks; going round after thirty ticks without a sight; a way taken for at most five seconds. */
    static final int EVERY = 10, BLIND_TICKS = 30, WAY_TICKS = 100;

    private GunFlank() {
    }

    @SubscribeEvent
    public static void tick(EntityTickEvent.Post e) {
        if (!(e.getEntity() instanceof PathfinderMob m) || !(m.level() instanceof ServerLevel sl)
            || (m.tickCount + m.getId()) % EVERY != 0 || m instanceof RoyalMob || m.isNoGravity() || m.isNoAi()
            || m.isPassenger() || !Guns.held(m.getMainHandItem())) {
            return;
        }
        LivingEntity t = m.getTarget();
        CompoundTag d = m.getPersistentData();
        if (t == null || !t.isAlive() || t.level() != sl || m.distanceToSqr(t) > 48 * 48) {
            clear(d);
            return;
        }
        if (m.getSensing().hasLineOfSight(t)) {
            clear(d);
            return;
        }
        int blind = d.getInt(BLIND) + EVERY;
        d.putInt(BLIND, blind);
        if (blind < BLIND_TICKS) {
            return;
        }
        long now = sl.getGameTime();
        if (d.getLong(UNTIL) > now && d.contains(SPOT)) {
            BlockPos s = BlockPos.of(d.getLong(SPOT));
            if (m.getNavigation().isDone() && m.blockPosition().distSqr(s) > 2) {
                m.getNavigation().moveTo(s.getX() + 0.5, s.getY(), s.getZ() + 0.5, 1.1);
            }
            return;
        }
        BlockPos spot = find(sl, m, t);
        if (spot == null) {
            d.putLong(UNTIL, now + 40);
            d.remove(SPOT);
            return;
        }
        d.putLong(SPOT, spot.asLong());
        d.putLong(UNTIL, now + WAY_TICKS);
        m.getNavigation().moveTo(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5, 1.1);
    }

    static void clear(CompoundTag d) {
        if (d.contains(BLIND)) {
            d.remove(BLIND);
            d.remove(UNTIL);
            d.remove(SPOT);
        }
    }

    /** Open ground round the target that sees it and that the mob can walk to: the nearest to the mob of a few tried. */
    static BlockPos find(ServerLevel sl, PathfinderMob m, LivingEntity t) {
        double range = Math.max(5.0, Math.min(14.0, Math.sqrt(m.distanceToSqr(t))));
        Vec3 eye = t.getEyePosition();
        java.util.List<BlockPos> seen = new java.util.ArrayList<>();
        for (double r : new double[]{range, Math.max(4.0, range * 0.6)}) {
            for (int i = 0; i < 16; i++) {
                double a = i * Math.PI / 8.0;
                BlockPos at = stand(sl, BlockPos.containing(t.getX() + Math.cos(a) * r, t.getY(), t.getZ() + Math.sin(a) * r));
                if (at == null) {
                    continue;
                }
                Vec3 from = new Vec3(at.getX() + 0.5, at.getY() + m.getEyeHeight(), at.getZ() + 0.5);
                if (sl.clip(new ClipContext(from, eye, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, m)).getType() == HitResult.Type.MISS) {
                    seen.add(at);
                }
            }
        }
        seen.sort(java.util.Comparator.comparingDouble(p -> p.distToCenterSqr(m.position())));
        for (int i = 0; i < Math.min(3, seen.size()); i++) {
            Path p = m.getNavigation().createPath(seen.get(i), 0);
            if (p != null && p.canReach()) {
                return seen.get(i);
            }
        }
        return null;
    }

    /** A place to stand near p (three up or down): solid ground under it, room for a body on it. */
    static BlockPos stand(ServerLevel sl, BlockPos p) {
        if (!sl.hasChunkAt(p)) {
            return null;
        }
        for (int dy = 0; dy <= 6; dy++) {
            BlockPos q = p.offset(0, (dy % 2 == 0 ? dy / 2 : -(dy + 1) / 2), 0);
            BlockState below = sl.getBlockState(q.below());
            if (below.isFaceSturdy(sl, q.below(), Direction.UP) && sl.getBlockState(q).getCollisionShape(sl, q).isEmpty()
                && sl.getBlockState(q.above()).getCollisionShape(sl, q.above()).isEmpty() && sl.getFluidState(q).isEmpty()) {
                return q;
            }
        }
        return null;
    }
}
