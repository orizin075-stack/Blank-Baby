package jp.oror.reborn.perf;

import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.longs.Long2LongOpenHashMap;
import java.util.Map;
import java.util.WeakHashMap;
import java.util.function.BiPredicate;
import net.minecraft.core.BlockPos;
import net.minecraft.core.SectionPos;
import net.minecraft.server.level.ServerLevel;

/**
 * Alex's Caves asks the point-of-interest store, for every entity on every tick, which magnets are near it (twice: the
 * attracting and the repelling ones); in the capital, with its hundreds of beds and workstations among the POIs, those
 * two scans were an eighth of the hundred-man battle's tick. Almost always there is no magnet anywhere near, so the
 * answer "none" is kept per 16-block section for two seconds: the section is checked once with the scan's reach grown
 * by 24 blocks (so that no point inside it can have a magnet in reach that the check missed, whatever distance the
 * mod measures by), and an entity in a section with no magnet in that wider reach gets "none" without a scan. Where a
 * magnet is near, the mod's own scan runs as before. A magnet just placed is felt up to two seconds late.
 */
public final class MagnetScan {
    private static final long TTL = 40;
    private static final Map<ServerLevel, Int2ObjectOpenHashMap<Long2LongOpenHashMap>> CACHE = new WeakHashMap<>();
    private static boolean probing;
    public static long hits, probes;

    private MagnetScan() {
    }

    /** True if no magnet of this kind can be within range of pos (the caller then answers with no magnets). */
    public static boolean none(ServerLevel level, BlockPos pos, int range, int kind, BiPredicate<BlockPos, Integer> anyWithin) {
        if (probing) {
            return false;
        }
        long now = level.getGameTime();
        Long2LongOpenHashMap map = CACHE.computeIfAbsent(level, l -> new Int2ObjectOpenHashMap<>()).computeIfAbsent(range * 2 + kind,
            k -> new Long2LongOpenHashMap());
        long key = SectionPos.asLong(pos.getX() >> 4, pos.getY() >> 4, pos.getZ() >> 4);
        long v = map.getOrDefault(key, -1L);
        if (v >= 0 && (v >>> 1) > now) {
            hits++;
            return (v & 1L) == 0;
        }
        if (map.size() > 8192) {
            map.clear();
        }
        BlockPos center = new BlockPos((pos.getX() & ~15) + 8, (pos.getY() & ~15) + 8, (pos.getZ() & ~15) + 8);
        boolean present;
        probing = true;
        try {
            present = anyWithin.test(center, range + 24);
        } finally {
            probing = false;
        }
        probes++;
        map.put(key, ((now + TTL) << 1) | (present ? 1L : 0L));
        return !present;
    }
}
