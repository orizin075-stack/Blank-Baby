package jp.oror.reborn.vehicle;

import jp.oror.reborn.citadel.CitadelData;
import jp.oror.reborn.citadel.CitadelSites;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.royal.RoyalRegistry;
import jp.oror.reborn.royal.RoyalRole;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (058) A turret stays on its post and keeps a gunner (the user's report: turrets lying at the bottom of their towers'
 * shafts, turrets no guard ever mans).
 *
 * <p>A turret was brought out where its soldier stood the first time he acted, and a soldier who had stepped into
 * the ladder shaft of his tower by then set it down at the bottom of it; its home was then the bottom too. And a turret
 * whose gunner fell was left empty for good. Every ten seconds now, each of the kingdom's still machines:</p>
 * <ul>
 * <li>is put back where it belongs if it lies below or beside it: the capital's own post for a turret of its kind
 * within three blocks, else its home; the floor under the post is mended first if it is open air;</li>
 * <li>empty for ten seconds, takes the nearest guard as its gunner, a fighting one too (059e); with none about for a
 * minute, a new guard comes (once in two minutes at most).</li>
 * </ul>
 */
final class TurretCare {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Vehicles");
    /** A gunner given no mind of his own while he sits at his gun: he gets it back when he no longer does. */
    static final String GUNNER = "oror_gunner";
    static int resets, recrewed, floors, logged;

    private TurretCare() {
    }

    static void tick(ServerLevel level, Entity v, CompoundTag p) {
        if ((v.tickCount + v.getId()) % 200 != 57) {
            return;
        }
        place(level, v, p);
        crew(level, v, p);
    }

    /** The capital's post for a still machine of this kind within three blocks (whatever the height), or null. */
    private static BlockPos post(ServerLevel level, Entity v) {
        CitadelSites.Site site = CitadelSites.garrisoned(level.getChunkSource().getGenerator(), v.chunkPosition().x, v.chunkPosition().z);
        if (site == null) {
            return null;
        }
        String id = BuiltInRegistries.ENTITY_TYPE.getKey(v.getType()).getPath();
        int hx = v.getBlockX() - site.offsetX(), hz = v.getBlockZ() - site.offsetZ();
        BlockPos best = null;
        double bestD = 9.01;
        for (int ox = -1; ox <= 1; ox++) {
            for (int oz = -1; oz <= 1; oz++) {
                for (CitadelData.Post post : CitadelData.posts((hx >> 4) + ox, (hz >> 4) + oz)) {
                    if (!post.still() || !post.vehicle().equals(id)) {
                        continue;
                    }
                    BlockPos at = site.toWorld(post.x(), post.y(), post.z());
                    double dx = at.getX() + 0.5 - v.getX(), dz = at.getZ() + 0.5 - v.getZ();
                    if (dx * dx + dz * dz < bestD) {
                        bestD = dx * dx + dz * dz;
                        best = at;
                    }
                }
            }
        }
        return best;
    }

    private static void place(ServerLevel level, Entity v, CompoundTag p) {
        BlockPos want = post(level, v);
        if (want == null) {
            want = BlockPos.of(p.getLong("Home"));
        }
        if (!level.isLoaded(want)) {
            return;
        }
        double dx = want.getX() + 0.5 - v.getX(), dz = want.getZ() + 0.5 - v.getZ(), h2 = dx * dx + dz * dz;
        boolean below = v.getY() < want.getY() - 1.5, aside = h2 > 2.25;
        if ((!below && !aside) || h2 > 36) {
            return;
        }
        if (!floor(level, want)) {
            return;
        }
        double fromY = v.getY();
        v.teleportTo(want.getX() + 0.5, want.getY(), want.getZ() + 0.5);
        v.setDeltaMovement(Vec3.ZERO);
        p.putLong("Home", want.asLong());
        p.putDouble("RunwayY", want.getY());
        resets++;
        if (logged++ < 40) {
            LOG.info("TURRET-RESET {} from y={} to {} ({})", BuiltInRegistries.ENTITY_TYPE.getKey(v.getType()), Math.round(fromY),
                want.toShortString(), below ? "below its post" : "beside its post");
        }
    }

    /** Something to stand on under a post: open air there is closed with the block beside it (stone bricks if none). */
    static boolean floor(ServerLevel level, BlockPos at) {
        BlockPos below = at.below();
        BlockState here = level.getBlockState(below);
        if (!here.getCollisionShape(level, below).isEmpty()) {
            return true;
        }
        if (!here.isAir() && !here.canBeReplaced()) {
            // a ladder, a hatch, a sign: not ours to close
            return false;
        }
        BlockState fill = null;
        for (Direction d : Direction.Plane.HORIZONTAL) {
            BlockPos n = below.relative(d);
            BlockState s = level.getBlockState(n);
            if (s.isCollisionShapeFullBlock(level, n) && !s.hasBlockEntity()) {
                fill = s;
                break;
            }
        }
        level.setBlock(below, fill != null ? fill : Blocks.STONE_BRICKS.defaultBlockState(), 3);
        floors++;
        return true;
    }

    private static void crew(ServerLevel level, Entity v, CompoundTag p) {
        if (!v.getPassengers().isEmpty()) {
            p.remove("Unmanned");
            return;
        }
        int n = p.getInt("Unmanned") + 1;
        p.putInt("Unmanned", n);
        // (059e, the user: soldiers should get into empty turrets and shoot) the nearest guard takes it after ten
        // seconds empty, a fighting one too (a fight is when a gun is wanted: before, only an idle guard came, so a
        // turret stayed empty through every attack); from thirty-two blocks about
        RoyalMob pick = null;
        double best = 32 * 32;
        for (RoyalMob m : level.getEntitiesOfClass(RoyalMob.class, v.getBoundingBox().inflate(32, 16, 32),
            x -> x.isAlive() && x.role() == RoyalRole.GUARD && !x.isPassenger() && !x.isNoAi()
                && !x.getPersistentData().contains("OrorMotor"))) {
            double d = m.distanceToSqr(v) * (m.getTarget() == null ? 1.0 : 0.8);
            if (d < best) {
                best = d;
                pick = m;
            }
        }
        long now = level.getGameTime();
        if (pick == null && n >= 6 && now >= p.getLong("RecrewAt")) {
            // no guard about for a minute: one is sent (not again for two)
            RoyalMob m = RoyalRegistry.TYPES.get(RoyalRole.GUARD).create(level);
            if (m != null) {
                m.moveTo(v.getX(), v.getY(), v.getZ(), v.getYRot(), 0F);
                m.setPersistenceRequired();
                level.addFreshEntity(m);
                pick = m;
                p.putLong("RecrewAt", now + 2400);
            }
        }
        if (pick != null && pick.startRiding(v, true)) {
            pick.setNoAi(true);
            pick.addTag(GUNNER);
            p.remove("Unmanned");
            recrewed++;
            if (logged++ < 40) {
                LOG.info("TURRET-CREW {} at {} manned again", BuiltInRegistries.ENTITY_TYPE.getKey(v.getType()), v.blockPosition().toShortString());
            }
        }
    }

    static String report() {
        return "resets=" + resets + " floors=" + floors + " recrewed=" + recrewed;
    }
}
