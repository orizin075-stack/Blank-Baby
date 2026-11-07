package jp.oror.reborn.perf;

import it.unimi.dsi.fastutil.longs.Long2LongOpenHashMap;
import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Stream;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;

/**
 * (053) Alex's Caves looks for its magnets round every entity of the server, every tick (MagnetUtil.tickMagnetism: one
 * search for the attracting magnets and one for the repelling, five blocks round the entity, reading the blocks there),
 * whether or not there is a magnet anywhere near: a third of the server thread in the hundred-man battle (052's CI
 * profile), most of it finding nothing.
 * <p>
 * Here the answer is shared by the points of a 2 x 2 x 2 cell of blocks: the cell's search is the same search from the
 * cell's upper corner, two blocks wider (anything within reach of a point of the cell is within reach of that corner
 * plus the 1.8 blocks between them), made once and remembered for two seconds; while it found none, an entity's search
 * in that cell answers "none" at once, exactly as its own search would have. Where it found a magnet the search is made
 * as before. A magnet set down shows within two seconds. Only on the server's own thread; on any error the search is
 * made as before.
 * <p>
 * The first form of this (one look per 16-block section, from the section's middle and 14 blocks wider) cost more than
 * it saved: that search reads 45 times the blocks of an entity's own, and most sections hold only a few entities (in the
 * capital it was half the server thread, 053's CI profile). The cell's search reads 2.5 times an entity's, and an entity
 * standing at its post asks it once every two seconds instead of forty times.
 */
public final class MagnetRegions {
    private static final String UTIL = "com.github.alexmodguy.alexscaves.server.entity.util.MagnetUtil";
    private static final int TTL = 40;
    private static final int WIDER = 2;
    private static final Map<ResourceKey<Level>, Long2LongOpenHashMap> ATTRACTING = new HashMap<>(), REPELLING = new HashMap<>();
    private static volatile Method attracting, repelling;
    private static volatile boolean broken;
    private static boolean probing;

    private MagnetRegions() {
    }

    /** True if the search from pos, this far, can only find no magnet of this kind (answered from its cell's search). */
    public static boolean none(BlockPos pos, ServerLevel level, int range, boolean attract) {
        if (broken || probing || range < 0 || range > 8 || level.getServer().getRunningThread() != Thread.currentThread()) {
            return false;
        }
        int cx = pos.getX() >> 1, cy = pos.getY() >> 1, cz = pos.getZ() >> 1;
        if (cx < -(1 << 23) || cx >= 1 << 23 || cz < -(1 << 23) || cz >= 1 << 23 || cy < -(1 << 11) || cy >= 1 << 11) {
            return false;
        }
        long key = ((cx & 0xFFFFFFL) << 40) | ((cz & 0xFFFFFFL) << 16) | ((cy & 0xFFFL) << 4) | range;
        Long2LongOpenHashMap seen = (attract ? ATTRACTING : REPELLING).computeIfAbsent(level.dimension(), k -> new Long2LongOpenHashMap());
        long now = level.getGameTime();
        long v = seen.get(key);
        if (v != 0 && Math.abs(v) > now) {
            return v > 0;
        }
        boolean none;
        probing = true;
        try {
            Method m = method(attract);
            // the cell's points are (2cx or 2cx+1, ...): within one block of its upper corner on each axis, so 1.8 blocks
            // away at most, whether the search reaches as a cube or a ball
            BlockPos corner = new BlockPos(2 * cx + 1, 2 * cy + 1, 2 * cz + 1);
            @SuppressWarnings("unchecked")
            Stream<BlockPos> found = (Stream<BlockPos>) m.invoke(null, corner, level, range + WIDER);
            none = found.findAny().isEmpty();
        } catch (ReflectiveOperationException | RuntimeException | LinkageError ex) {
            broken = true;
            return false;
        } finally {
            probing = false;
        }
        if (seen.size() > 200000) {
            seen.clear();
        }
        seen.put(key, none ? now + TTL : -(now + TTL));
        return none;
    }

    private static Method method(boolean attract) throws ReflectiveOperationException {
        Method m = attract ? attracting : repelling;
        if (m == null) {
            m = Class.forName(UTIL).getDeclaredMethod(attract ? "getNearbyAttractingMagnets" : "getNearbyRepellingMagnets", BlockPos.class,
                ServerLevel.class, int.class);
            m.setAccessible(true);
            if (attract) {
                attracting = m;
            } else {
                repelling = m;
            }
        }
        return m;
    }
}
