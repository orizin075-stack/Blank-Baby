package jp.oror.reborn;

import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.phys.AABB;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (059g) A village with a tank or a jet keeps two of its strong at home (ExpeditionHomeGuardMixin). The CI check of the
 * village's arms (CI 44 to 46) found the castle town's tank built and never brought out: every one of its strong
 * villagers (its weaponsmith, armourer and mason) had gone on a dungeon expedition, and a vehicle is crewed only by the
 * strong. An expedition's party now leaves two of them behind where the village has a vehicle (its weakest go no more;
 * with fewer than two left to go it does not set out).
 */
public final class VillageHomeGuard {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Village");
    static int trimmed;

    private VillageHomeGuard() {
    }

    /** The expedition's party with as many taken off its end as keep two strong at home, or null to leave it as it is. */
    public static List<Villager> trim(List<Villager> party) {
        if (party == null || party.isEmpty() || !(party.get(0).level() instanceof ServerLevel sl)) {
            return null;
        }
        VillageLedger.Village v = VillageLedger.of(party.get(0));
        if (v == null) {
            return null;
        }
        VillageProgress.Record r = VillageProgress.get(sl).villages.get(v.id);
        if (r == null || r.vehicles == null || r.vehicles.isEmpty()) {
            return null;
        }
        List<Villager> home = sl.getEntitiesOfClass(Villager.class, new AABB(v.center).inflate(64, 24, 64),
            x -> x.isAlive() && VillageAI.strong(x) && VillageLedger.of(x) == v && !party.contains(x) && !x.isPassenger());
        int need = 2 - home.size();
        if (need <= 0) {
            return null;
        }
        List<Villager> out = new ArrayList<>(party);
        while (need-- > 0 && !out.isEmpty()) {
            out.remove(out.size() - 1);
        }
        if (trimmed++ < 20) {
            LOG.info("EXPEDITION-HOME-GUARD {\"village\":\"{}\",\"party\":{},\"goes\":{},\"home\":{}}", r.name(), party.size(), out.size(),
                home.size() + party.size() - out.size());
        }
        return out;
    }

    static int stepped;

    /**
     * (CI 63, 64) A tank's crewman called to board who cannot set out: twice the CI's second crewman stood beside the
     * village's chest, on the ground with open ground all round, and every path to the tank (18 blocks over a level green)
     * came out empty as soon as it was asked; once he stood there a whole minute and the tank went out with one man. A
     * crewman of a boarding sortie who has not left his block for three seconds, his path done, steps to the open
     * neighbouring block nearest the tank and is set walking again (the village's own crew walk goes on from there).
     * VillagerLife.tick's start (VillagerRoadMixin), every villager each tick; it acts once a second.
     */
    public static void unstick(Entity e) {
        if (!(e instanceof Villager v) || !(v.level() instanceof ServerLevel level) || v.isPassenger() || (v.tickCount + v.getId()) % 20 != 3) {
            return;
        }
        CompoundTag d = VillagerLife.data(v);
        if (!d.hasUUID("Sortie")) {
            if (d.contains("OrorBoardStill")) {
                d.remove("OrorBoardStill");
                d.remove("OrorBoardAt");
            }
            return;
        }
        VillageProgress.Record rec = VillageProgress.get(level).villages.get(d.getUUID("Sortie"));
        if (rec == null || rec.sortie == null || !"board".equals(rec.sortie.getString("Phase")) || !rec.sortie.hasUUID("Vehicle")) {
            return;
        }
        Entity tank = level.getEntity(rec.sortie.getUUID("Vehicle"));
        if (tank == null || v.distanceTo(tank) < 4) {
            return;
        }
        long here = v.blockPosition().asLong();
        int still = d.getLong("OrorBoardAt") == here ? d.getInt("OrorBoardStill") + 1 : 0;
        d.putLong("OrorBoardAt", here);
        d.putInt("OrorBoardStill", still);
        if (still < 3 || !v.getNavigation().isDone()) {
            return;
        }
        BlockPos at = v.blockPosition(), best = null;
        double bestD = Double.MAX_VALUE;
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                BlockPos q = at.offset(dx, 0, dz);
                if ((dx == 0 && dz == 0) || !level.getBlockState(q).getCollisionShape(level, q).isEmpty()
                    || !level.getBlockState(q.above()).getCollisionShape(level, q.above()).isEmpty()
                    || !level.getBlockState(q.below()).isFaceSturdy(level, q.below(), net.minecraft.core.Direction.UP)) {
                    continue;
                }
                double dd = q.distToCenterSqr(tank.position());
                if (dd < bestD) {
                    bestD = dd;
                    best = q;
                }
            }
        }
        String before = VillagerState.of(v, tank);
        // (CI 65: three steps of a block each, and no path until he was 16 blocks from the tank) why: his follow range (the
        // pathfinder's reach) and a path tried here and now
        double reach = v.getAttributeValue(net.minecraft.world.entity.ai.attributes.Attributes.FOLLOW_RANGE);
        net.minecraft.world.level.pathfinder.Path tried = v.getNavigation().createPath(tank.blockPosition(), 0);
        String pathTried = tried == null ? "none" : (tried.canReach() ? "reaches" : "short") + " nodes " + tried.getNodeCount()
            + (tried.getEndNode() == null ? "" : " ends " + tried.getEndNode().asBlockPos().toShortString());
        if (best != null) {
            v.teleportTo(best.getX() + 0.5, best.getY(), best.getZ() + 0.5);
        }
        v.getNavigation().stop();
        VillageAI.walk(v, tank.blockPosition(), VillageAI.pace(v, 0.36), 1);
        d.putInt("OrorBoardStill", 0);
        stepped++;
        LOG.info("VILLAGE-CREW-STEP {\"to\":\"{}\",\"pathNow\":{},\"followRange\":{},\"pathTried\":\"{}\",\"was\":\"{}\"}",
            best == null ? "-" : best.toShortString(), !v.getNavigation().isDone(), reach, pathTried, before.replace('"', '\''));
    }

    static int waypoints;

    /**
     * (059h) VillageAI.walk's start (VillageWalkWaypointMixin): a villager sent more than 14 blocks off whose brain has just
     * failed to find the way there (it remembers it could not reach its walk target) is sent ten blocks toward it instead,
     * along the ground. The next call sends him to the real place again; failing that, to the next waypoint. True when
     * the waypoint was given (the walk itself is then not made).
     */
    public static boolean waypoint(net.minecraft.world.entity.Mob mob, BlockPos to, float speed, int close) {
        if (!(mob instanceof Villager v) || !(v.level() instanceof ServerLevel level) || to == null) {
            return false;
        }
        net.minecraft.world.phys.Vec3 d = net.minecraft.world.phys.Vec3.atBottomCenterOf(to).subtract(v.position()).multiply(1, 0, 1);
        if (d.lengthSqr() < 14 * 14) {
            return false;
        }
        java.util.Optional<Long> failed = v.getBrain().getMemory(net.minecraft.world.entity.ai.memory.MemoryModuleType.CANT_REACH_WALK_TARGET_SINCE);
        if (failed.isEmpty() || level.getGameTime() - failed.get() > 200) {
            return false;
        }
        net.minecraft.world.phys.Vec3 at = v.position().add(d.normalize().scale(10));
        int y = level.getHeight(net.minecraft.world.level.levelgen.Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, net.minecraft.util.Mth.floor(at.x),
            net.minecraft.util.Mth.floor(at.z));
        if (Math.abs(y - v.getY()) > 6) {
            y = v.getBlockY();   // a roof or a pit there: on at his own height
        }
        BlockPos wp = BlockPos.containing(at.x, y, at.z);
        v.getBrain().setMemory(net.minecraft.world.entity.ai.memory.MemoryModuleType.WALK_TARGET,
            new net.minecraft.world.entity.ai.memory.WalkTarget(wp, speed, Math.max(1, close)));
        if (waypoints++ < 40) {
            LOG.info("VILLAGE-CREW-WAYPOINT {\"to\":\"{}\",\"via\":\"{}\",\"off\":{}}", to.toShortString(), wp.toShortString(),
                String.format(java.util.Locale.ROOT, "%.1f", d.length()));
        }
        return true;
    }
}
