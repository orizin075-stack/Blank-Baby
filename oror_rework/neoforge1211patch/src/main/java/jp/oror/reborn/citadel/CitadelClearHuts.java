package jp.oror.reborn.citadel;

import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.chunk.PalettedContainer;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;

/**
 * (053) /oror citadel clearhuts: the huts villagers began in the capital before 053 (their foundations, walls, doors,
 * beds and torches standing in its streets and before its doors, many half built) taken away from the chunks of the
 * capital loaded now (within 256 blocks of whoever runs it). Only where the capital's save has open air and only the
 * huts' own materials (planks, cobblestone, wooden doors, beds, torches) are taken: the kingdom's buildings and what a
 * player built of anything else stay.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class CitadelClearHuts {
    private CitadelClearHuts() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("citadel").then(Commands.literal("clearhuts")
            .requires(s -> s.hasPermission(2)).executes(c -> run(c.getSource())))));
    }

    private static boolean hutPart(BlockState st) {
        return st.is(BlockTags.PLANKS) || st.is(Blocks.COBBLESTONE) || st.is(BlockTags.WOODEN_DOORS) || st.is(BlockTags.BEDS)
            || st.is(Blocks.TORCH) || st.is(Blocks.WALL_TORCH);
    }

    private static int run(CommandSourceStack src) {
        ServerLevel level = src.getLevel();
        BlockPos me = BlockPos.containing(src.getPosition());
        CitadelSites.Site site = CitadelSites.nearest(me, 0);
        if (site == null) {
            src.sendFailure(Component.literal("王都が見つかりません。"));
            return 0;
        }
        int removed = 0, chunks = 0;
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        ChunkPos here = new ChunkPos(me);
        for (int cx = here.x - 16; cx <= here.x + 16; cx++) {
            for (int cz = here.z - 16; cz <= here.z + 16; cz++) {
                LevelChunk chunk = level.getChunkSource().getChunkNow(cx, cz);
                int sx = cx - site.chunkX() - CitadelData.HALF, sz = cz - site.chunkZ() - CitadelData.HALF;
                CitadelData.Chunk data = chunk == null ? null : CitadelData.chunk(sx, sz);
                if (data == null) {
                    continue;
                }
                chunks++;
                for (int sy = 0; sy < CitadelData.SECTIONS; sy++) {
                    PalettedContainer<BlockState> section = data.sections()[sy];
                    for (int y = 0; y < 16; y++) {
                        int wy = sy * 16 + y + site.dy();
                        if (wy <= site.ground() - 1 || wy >= level.getMaxBuildHeight()) {
                            continue;
                        }
                        for (int z = 0; z < 16; z++) {
                            for (int x = 0; x < 16; x++) {
                                Block want = section == null ? Blocks.AIR : section.get(x, y, z).getBlock();
                                if (want != Blocks.AIR) {
                                    continue;
                                }
                                p.set(cx * 16 + x, wy, cz * 16 + z);
                                if (hutPart(chunk.getBlockState(p))) {
                                    level.setBlock(p, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
                                    removed++;
                                }
                            }
                        }
                    }
                }
            }
        }
        int n = removed, c = chunks;
        src.sendSuccess(() -> Component.literal("王都の " + c + " チャンクから、村人の建てかけの小屋のブロックを " + n + " 個取り除きました。"), true);
        return removed;
    }
}
