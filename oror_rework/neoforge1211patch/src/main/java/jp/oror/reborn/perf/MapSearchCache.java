package jp.oror.reborn.perf;

import java.util.HashMap;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.levelgen.structure.Structure;

/**
 * (059d) The user: "very heavy". In the look run's flight recording, with the player in the capital, a twelfth of the
 * server thread went to cartographers making their explorer maps: each time a villager rose a level (the capital's
 * people trade with one another and rise), a cartographer's new offers asked the world for the nearest woodland
 * mansion or ocean monument within a hundred chunks, a search that samples the biome of every place one might stand
 * (and, under Alex's Caves, sets its dimension each time).
 * <p>
 * Here the answer is remembered for a game day per 512-block cell of the world and kind of structure: the cartographers
 * of a town share the first one's search (their maps lead to the same mansion, as a player's would from the same
 * town). A search that found nothing is remembered too. Only on the server thread; a hundred cells at most.
 */
public final class MapSearchCache {
    private record Key(String dimension, String tag, int cx, int cz) {
    }

    private record Found(BlockPos pos, long until) {
    }

    private static final Map<Key, Found> FOUND = new HashMap<>();
    private static final long KEEP = 24000;
    public static int searched, reused;

    private MapSearchCache() {
    }

    public static BlockPos find(ServerLevel level, TagKey<Structure> tag, BlockPos from, int radius, boolean skipKnown) {
        if (!level.getServer().isSameThread()) {
            return level.findNearestMapStructure(tag, from, radius, skipKnown);
        }
        long now = level.getGameTime();
        Key key = new Key(level.dimension().location().toString(), tag.location().toString(), from.getX() >> 9, from.getZ() >> 9);
        Found f = FOUND.get(key);
        if (f != null && now < f.until()) {
            reused++;
            return f.pos();
        }
        BlockPos pos = level.findNearestMapStructure(tag, from, radius, skipKnown);
        if (FOUND.size() > 100) {
            FOUND.entrySet().removeIf(e -> now >= e.getValue().until());
            if (FOUND.size() > 100) {
                FOUND.clear();
            }
        }
        FOUND.put(key, new Found(pos, now + KEEP));
        searched++;
        return pos;
    }
}
