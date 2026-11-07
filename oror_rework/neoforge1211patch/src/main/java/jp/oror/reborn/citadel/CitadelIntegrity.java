package jp.oror.reborn.citadel;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.chunk.PalettedContainer;

/**
 * (053) The capital as it stands against the capital as it was built (the user: several buildings broken, the palace
 * above all). Every block of the loaded chunks of the capital is compared with the save's block there (CitadelData,
 * lifted by the site's dy), by block (a door opened or a crop grown is not a difference): what differs, how often (the
 * save's block -> the world's), where (the chunks with most, in the save's chunk coordinates, and samples in the save's
 * block coordinates), and how much of it is round the palace. The natural rock under the kingdom's ground (the save's
 * dirt and bedrock) is not compared.
 */
public final class CitadelIntegrity {
    private CitadelIntegrity() {
    }

    private static boolean living(Block b) {
        BlockState d = b.defaultBlockState();
        return d.is(BlockTags.CROPS) || d.is(BlockTags.LEAVES) || d.is(BlockTags.SAPLINGS) || b == Blocks.FARMLAND || b == Blocks.DIRT_PATH
            || b == Blocks.GRASS_BLOCK || b == Blocks.DIRT || b == Blocks.SHORT_GRASS || b == Blocks.TALL_GRASS || b == Blocks.FIRE
            || b == Blocks.WATER || b == Blocks.LAVA || b == Blocks.SNOW || b == Blocks.LIGHT;
    }

    public static String scan(ServerLevel level, CitadelSites.Site site, List<ChunkPos> chunks) {
        Map<String, Integer> pairs = new HashMap<>();
        Map<String, Integer> perChunk = new HashMap<>();
        Map<String, List<String>> samples = new HashMap<>();
        long compared = 0, differ = 0, nearPalace = 0;
        int dy = site.dy(), ground = site.ground();
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        for (ChunkPos cp : chunks) {
            LevelChunk chunk = level.getChunkSource().getChunkNow(cp.x, cp.z);
            int sx = cp.x - site.chunkX() - CitadelData.HALF, sz = cp.z - site.chunkZ() - CitadelData.HALF;
            CitadelData.Chunk data = CitadelData.chunk(sx, sz);
            if (chunk == null || data == null) {
                continue;
            }
            int bx = cp.getMinBlockX(), bz = cp.getMinBlockZ();
            for (int sy = 0; sy < CitadelData.SECTIONS; sy++) {
                PalettedContainer<BlockState> section = data.sections()[sy];
                for (int y = 0; y < 16; y++) {
                    int wy = sy * 16 + y + dy;
                    if (wy < level.getMinBuildHeight() || wy >= level.getMaxBuildHeight() || section == null && wy <= ground) {
                        continue;
                    }
                    for (int z = 0; z < 16; z++) {
                        for (int x = 0; x < 16; x++) {
                            Block want = section == null ? Blocks.AIR : section.get(x, y, z).getBlock();
                            if (want == Blocks.DIRT || want == Blocks.BEDROCK) {
                                continue;
                            }
                            Block got = chunk.getBlockState(p.set(bx + x, wy, bz + z)).getBlock();
                            compared++;
                            // the same block, two kinds of growth or ground (grass and dirt, a crop for another), the two airs
                            if (got == want || living(want) && living(got) || want == Blocks.AIR && got == Blocks.CAVE_AIR) {
                                continue;
                            }
                            differ++;
                            int tx = bx + x - site.offsetX(), tz = bz + z - site.offsetZ();
                            if (Math.abs(tx - CitadelData.THRONE_X) < 70 && Math.abs(tz - CitadelData.THRONE_Z) < 70) {
                                nearPalace++;
                            }
                            String key = BuiltInRegistries.BLOCK.getKey(want).getPath() + "->" + BuiltInRegistries.BLOCK.getKey(got).getPath();
                            pairs.merge(key, 1, Integer::sum);
                            perChunk.merge(sx + "," + sz, 1, Integer::sum);
                            List<String> s = samples.computeIfAbsent(key, k -> new ArrayList<>());
                            if (s.size() < 4) {
                                s.add("[" + tx + "," + (sy * 16 + y) + "," + tz + "]");
                            }
                        }
                    }
                }
            }
        }
        StringBuilder top = new StringBuilder();
        pairs.entrySet().stream().sorted((a, b) -> b.getValue() - a.getValue()).limit(30).forEach(en -> top.append(top.length() > 0 ? "," : "")
            .append('"').append(en.getKey()).append("\":[").append(en.getValue()).append(',').append(String.join(",", samples.get(en.getKey())))
            .append(']'));
        StringBuilder worst = new StringBuilder();
        perChunk.entrySet().stream().sorted((a, b) -> b.getValue() - a.getValue()).limit(15).forEach(en -> worst.append(worst.length() > 0 ? "," : "")
            .append("\"").append(en.getKey()).append("\":").append(en.getValue()));
        return String.format(Locale.ROOT, "{\"compared\":%d,\"differ\":%d,\"nearPalace\":%d,\"pairs\":{%s},\"worstChunks\":{%s}}", compared, differ,
            nearPalace, top, worst);
    }
}
