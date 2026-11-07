package jp.oror.reborn.perf;

import java.lang.reflect.Method;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Stream;
import net.minecraft.core.BlockPos;
import net.minecraft.core.SectionPos;
import net.minecraft.server.level.ServerLevel;

/**
 * (053) Alex's Caves looks for its magnets round every entity of the server, every tick (MagnetUtil.tickMagnetism: two
 * searches of the points of interest, one for the attracting magnets and one for the repelling, five blocks round the
 * entity), whether or not there is a magnet anywhere near: a third of the server thread in the hundred-man battle
 * (052's CI profile), most of it finding nothing. Here, for each 16-block section, whether there is any magnet of that
 * kind within reach of anything in it is looked up once (the same search, from the section's middle, wide enough to
 * cover the five blocks round any point of it) and remembered for two seconds; while there is none, an entity's search
 * answers "none" at once, exactly as the search would have. Where there are magnets the search is made as before. A
 * magnet set down shows within two seconds. On any error the search is made as before.
 */
public final class MagnetRegions {
    private static final String UTIL = "com.github.alexmodguy.alexscaves.server.entity.util.MagnetUtil";
    private static final int TTL = 40;
    private static final ThreadLocal<Boolean> PROBING = ThreadLocal.withInitial(() -> Boolean.FALSE);
    private static final Map<Long, Long> ATTRACTING = new ConcurrentHashMap<>(), REPELLING = new ConcurrentHashMap<>();
    private static volatile Method attracting, repelling;
    private static volatile boolean broken;

    private MagnetRegions() {
    }

    /** True if the search from pos, this far, can only find no magnet of this kind (answered from the section's look). */
    public static boolean none(BlockPos pos, ServerLevel level, int range, boolean attract) {
        if (broken || PROBING.get() || range > 8) {
            return false;
        }
        int sx = SectionPos.blockToSectionCoord(pos.getX()), sy = SectionPos.blockToSectionCoord(pos.getY()), sz = SectionPos.blockToSectionCoord(pos.getZ());
        long key = SectionPos.asLong(sx, sy, sz) * 31L + level.dimension().location().hashCode();
        Map<Long, Long> seen = attract ? ATTRACTING : REPELLING;
        long now = level.getGameTime();
        Long v = seen.get(key);
        if (v != null && Math.abs(v) > now) {
            return v > 0;
        }
        boolean none;
        PROBING.set(Boolean.TRUE);
        try {
            Method m = method(attract);
            BlockPos mid = new BlockPos(SectionPos.sectionToBlockCoord(sx) + 8, SectionPos.sectionToBlockCoord(sy) + 8,
                SectionPos.sectionToBlockCoord(sz) + 8);
            // the section's corners are 13.9 blocks from its middle: anything within range of a point in it is within
            // range + 14 of the middle
            @SuppressWarnings("unchecked")
            Stream<BlockPos> found = (Stream<BlockPos>) m.invoke(null, mid, level, range + 14);
            none = found.findAny().isEmpty();
        } catch (ReflectiveOperationException | RuntimeException | LinkageError ex) {
            broken = true;
            return false;
        } finally {
            PROBING.set(Boolean.FALSE);
        }
        if (seen.size() > 50000) {
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
