package jp.oror.reborn.arms;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Stream;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.NbtAccounter;
import net.minecraft.nbt.NbtIo;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.nbt.Tag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.LevelResource;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.level.BlockEvent;
import net.neoforged.neoforge.event.server.ServerStoppingEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.joml.Vector3f;

/**
 * The Blueprinter's scans and prints.
 *
 * <p>A scan keeps block states only (no block-entity data, so nothing inside a chest or machine is copied) and skips
 * what must not be multiplied: #oror_supreme_bosses:blueprinter_unprintable (ores, storage blocks, beacons, spawners,
 * shulker boxes and the like) and unbreakable blocks. It is saved under the world folder in oror_blueprints/, the item
 * keeping only its id, size and cost.
 *
 * <p>A print costs one Matter Cartridge per 256 units: a block is one unit, a block with a block entity or in
 * #oror_supreme_bosses:blueprinter_costly sixteen; air is free. It is placed bottom-up, 1024 blocks a tick, without
 * neighbour updates (the copied states already fit together). It never removes a block with a block entity or an
 * unbreakable one, and asks the break event (land-claim mods) before replacing anything else.
 */
@EventBusSubscriber(modid = OrorArms.ID)
public final class Blueprints {
    static final int MAX_SIDE = 64;
    static final int UNITS_PER_CARTRIDGE = 256;
    static final int COSTLY_UNITS = 16;
    static final int PER_TICK = 1024;
    static final int PREVIEW_TICKS = 200;
    static final int KEEP_FILES = 256;
    static final TagKey<Block> UNPRINTABLE = TagKey.create(Registries.BLOCK, OrorArms.id("blueprinter_unprintable"));
    static final TagKey<Block> COSTLY = TagKey.create(Registries.BLOCK, OrorArms.id("blueprinter_costly"));
    static final DustParticleOptions LINE = new DustParticleOptions(new Vector3f(0.31f, 0.72f, 1.0f), 1.4f);

    /** cells: x fastest, then z, then y; -1 leaves the target block as it is. */
    record Blueprint(int sx, int sy, int sz, List<BlockState> palette, int[] cells) {
    }

    record Preview(ServerLevel level, BlockPos target, int rotation, BlockPos origin, int[] dims, long expires) {
    }

    static final class Job {
        final ServerLevel level;
        final UUID player;
        final Blueprint bp;
        final Rotation rotation;
        final BlockPos origin;
        int index;
        int placed;
        int kept;

        Job(ServerLevel level, UUID player, Blueprint bp, Rotation rotation, BlockPos origin) {
            this.level = level;
            this.player = player;
            this.bp = bp;
            this.rotation = rotation;
            this.origin = origin;
        }
    }

    private static final List<Job> JOBS = new ArrayList<>();
    private static final Map<UUID, Preview> PREVIEWS = new HashMap<>();
    private static final Map<UUID, Blueprint> CACHE = new LinkedHashMap<>(8, 0.75f, true) {
        @Override
        protected boolean removeEldestEntry(Map.Entry<UUID, Blueprint> eldest) {
            return size() > 4;
        }
    };

    public static int cartridges(int units) {
        return (units + UNITS_PER_CARTRIDGE - 1) / UNITS_PER_CARTRIDGE;
    }

    static boolean printable(BlockState state, ServerLevel level, BlockPos pos) {
        return !state.is(UNPRINTABLE) && state.getDestroySpeed(level, pos) >= 0;
    }

    static int units(BlockState state) {
        if (state.isAir()) {
            return 0;
        }
        return state.is(COSTLY) || state.hasBlockEntity() ? COSTLY_UNITS : 1;
    }

    // ---------------------------------------------------------------------------------------------------------------
    // scanning

    static void scanClick(ServerLevel level, ServerPlayer player, ItemStack stack, CompoundTag tag, BlockPos pos) {
        String dim = level.dimension().location().toString();
        int[] a = tag.getIntArray("A");
        if (a.length != 3 || !dim.equals(tag.getString("Dim"))) {
            tag.putIntArray("A", new int[] {pos.getX(), pos.getY(), pos.getZ()});
            tag.putString("Dim", dim);
            BlueprinterItem.save(stack, tag);
            player.displayClientMessage(Component.translatable("oror.blueprinter.corner_a", pos.getX(), pos.getY(), pos.getZ())
                .withStyle(ChatFormatting.GOLD), true);
            outline(level, player, pos, new int[] {1, 1, 1});
            return;
        }
        BlockPos lo = new BlockPos(Math.min(a[0], pos.getX()), Math.min(a[1], pos.getY()), Math.min(a[2], pos.getZ()));
        int sx = Math.abs(a[0] - pos.getX()) + 1, sy = Math.abs(a[1] - pos.getY()) + 1, sz = Math.abs(a[2] - pos.getZ()) + 1;
        if (sx > MAX_SIDE || sy > MAX_SIDE || sz > MAX_SIDE) {
            player.displayClientMessage(Component.translatable("oror.blueprinter.too_large", sx, sy, sz, MAX_SIDE).withStyle(ChatFormatting.RED), true);
            return;
        }
        List<BlockState> palette = new ArrayList<>();
        Map<BlockState, Integer> index = new HashMap<>();
        int[] cells = new int[sx * sy * sz];
        int blocks = 0, cost = 0, i = 0;
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        for (int y = 0; y < sy; y++) {
            for (int z = 0; z < sz; z++) {
                for (int x = 0; x < sx; x++, i++) {
                    p.set(lo.getX() + x, lo.getY() + y, lo.getZ() + z);
                    BlockState state = level.isLoaded(p) ? level.getBlockState(p) : Blocks.VOID_AIR.defaultBlockState();
                    if (state.is(Blocks.VOID_AIR) || !printable(state, level, p)) {
                        cells[i] = -1;
                        continue;
                    }
                    if (state.is(Blocks.CAVE_AIR)) {
                        state = Blocks.AIR.defaultBlockState();
                    }
                    cells[i] = index.computeIfAbsent(state, s -> {
                        palette.add(s);
                        return palette.size() - 1;
                    });
                    if (!state.isAir()) {
                        blocks++;
                        cost += units(state);
                    }
                }
            }
        }
        Blueprint bp = new Blueprint(sx, sy, sz, palette, cells);
        UUID id = UUID.randomUUID();
        try {
            store(level.getServer(), id, bp);
        } catch (IOException e) {
            player.displayClientMessage(Component.literal("Blueprinter: " + e.getMessage()).withStyle(ChatFormatting.RED), false);
            return;
        }
        tag.remove("A");
        tag.putUUID("Blueprint", id);
        tag.putIntArray("Size", new int[] {sx, sy, sz});
        tag.putInt("Blocks", blocks);
        tag.putInt("Cost", cost);
        tag.putInt("Facing", player.getDirection().get2DDataValue());
        tag.putBoolean("Print", true);
        BlueprinterItem.save(stack, tag);
        outline(level, player, lo, new int[] {sx, sy, sz});
        level.playSound(null, player.blockPosition(), SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 0.8f, 1.6f);
        player.displayClientMessage(Component.translatable("oror.blueprinter.scanned", sx, sy, sz, blocks, cartridges(cost))
            .withStyle(ChatFormatting.AQUA), false);
    }

    // ---------------------------------------------------------------------------------------------------------------
    // printing

    static void printClick(ServerLevel level, ServerPlayer player, ItemStack stack, CompoundTag tag, BlockPos target) {
        if (!tag.hasUUID("Blueprint")) {
            player.displayClientMessage(Component.translatable("oror.blueprinter.no_blueprint").withStyle(ChatFormatting.RED), true);
            return;
        }
        Blueprint bp = load(level.getServer(), tag.getUUID("Blueprint"));
        if (bp == null) {
            player.displayClientMessage(Component.translatable("oror.blueprinter.missing").withStyle(ChatFormatting.RED), true);
            return;
        }
        int turns = Math.floorMod(player.getDirection().get2DDataValue() - tag.getInt("Facing"), 4);
        int[] dims = turns % 2 == 0 ? new int[] {bp.sx(), bp.sy(), bp.sz()} : new int[] {bp.sz(), bp.sy(), bp.sx()};
        BlockPos origin = new BlockPos(target.getX() - dims[0] / 2, target.getY(), target.getZ() - dims[2] / 2);
        int need = player.isCreative() ? 0 : cartridges(tag.getInt("Cost"));
        Preview prev = PREVIEWS.get(player.getUUID());
        long now = level.getGameTime();
        if (prev == null || prev.level() != level || !prev.target().equals(target) || prev.rotation() != turns || now > prev.expires()) {
            PREVIEWS.put(player.getUUID(), new Preview(level, target, turns, origin, dims, now + PREVIEW_TICKS));
            outline(level, player, origin, dims);
            player.displayClientMessage(Component.translatable("oror.blueprinter.preview", dims[0], dims[1], dims[2], need)
                .withStyle(ChatFormatting.AQUA), true);
            return;
        }
        PREVIEWS.remove(player.getUUID());
        for (Job job : JOBS) {
            if (job.player.equals(player.getUUID())) {
                player.displayClientMessage(Component.translatable("oror.blueprinter.busy").withStyle(ChatFormatting.RED), true);
                return;
            }
        }
        BlockPos far = origin.offset(dims[0] - 1, dims[1] - 1, dims[2] - 1);
        if (origin.getY() < level.getMinBuildHeight() || far.getY() >= level.getMaxBuildHeight()
            || !level.getWorldBorder().isWithinBounds(origin) || !level.getWorldBorder().isWithinBounds(far)
            || !level.mayInteract(player, origin) || !level.mayInteract(player, far) || !player.mayBuild()) {
            player.displayClientMessage(Component.translatable("oror.blueprinter.denied").withStyle(ChatFormatting.RED), true);
            return;
        }
        int have = countCartridges(player);
        if (have < need) {
            player.displayClientMessage(Component.translatable("oror.blueprinter.need_cartridges", have, need).withStyle(ChatFormatting.RED), true);
            return;
        }
        takeCartridges(player, need);
        JOBS.add(new Job(level, player.getUUID(), bp, Rotation.values()[turns], origin));
        level.playSound(null, target, SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 1.0f, 1.2f);
        player.displayClientMessage(Component.translatable("oror.blueprinter.started", tag.getInt("Blocks"), need).withStyle(ChatFormatting.AQUA), false);
    }

    static int countCartridges(Player player) {
        int n = 0;
        for (ItemStack s : player.getInventory().items) {
            if (s.is(OrorArms.MATTER_CARTRIDGE)) {
                n += s.getCount();
            }
        }
        return n;
    }

    static void takeCartridges(Player player, int n) {
        for (ItemStack s : player.getInventory().items) {
            if (n <= 0) {
                return;
            }
            if (s.is(OrorArms.MATTER_CARTRIDGE)) {
                int take = Math.min(n, s.getCount());
                s.shrink(take);
                n -= take;
            }
        }
    }

    /** Box cell (x, y, z) after {@code turns} clockwise quarter turns about the vertical axis. */
    static BlockPos turned(Blueprint bp, int x, int y, int z, Rotation r) {
        return switch (r) {
            case CLOCKWISE_90 -> new BlockPos(bp.sz() - 1 - z, y, x);
            case CLOCKWISE_180 -> new BlockPos(bp.sx() - 1 - x, y, bp.sz() - 1 - z);
            case COUNTERCLOCKWISE_90 -> new BlockPos(z, y, bp.sx() - 1 - x);
            default -> new BlockPos(x, y, z);
        };
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post event) {
        MinecraftServer server = event.getServer();
        if (server.getTickCount() % 10 == 0 && !PREVIEWS.isEmpty()) {
            Iterator<Map.Entry<UUID, Preview>> it = PREVIEWS.entrySet().iterator();
            while (it.hasNext()) {
                Map.Entry<UUID, Preview> e = it.next();
                Preview pv = e.getValue();
                ServerPlayer player = server.getPlayerList().getPlayer(e.getKey());
                if (player == null || player.level() != pv.level() || pv.level().getGameTime() > pv.expires()) {
                    it.remove();
                } else {
                    outline(pv.level(), player, pv.origin(), pv.dims());
                }
            }
        }
        Iterator<Job> jobs = JOBS.iterator();
        while (jobs.hasNext()) {
            Job job = jobs.next();
            if (step(job, server.getPlayerList().getPlayer(job.player))) {
                jobs.remove();
            }
        }
    }

    /** Places up to PER_TICK cells; true when the job is done. */
    static boolean step(Job job, ServerPlayer player) {
        Blueprint bp = job.bp;
        ServerLevel level = job.level;
        int total = bp.cells().length;
        int budget = PER_TICK;
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        while (job.index < total && budget > 0) {
            int i = job.index++;
            int c = bp.cells()[i];
            if (c < 0) {
                continue;
            }
            budget--;
            int x = i % bp.sx(), z = (i / bp.sx()) % bp.sz(), y = i / (bp.sx() * bp.sz());
            BlockPos off = turned(bp, x, y, z, job.rotation);
            p.set(job.origin.getX() + off.getX(), job.origin.getY() + off.getY(), job.origin.getZ() + off.getZ());
            BlockState want = bp.palette().get(c).rotate(job.rotation);
            if (!level.isLoaded(p)) {
                job.kept++;
                continue;
            }
            BlockState have = level.getBlockState(p);
            if (have == want) {
                continue;
            }
            if (have.hasBlockEntity() || have.getDestroySpeed(level, p) < 0) {
                job.kept++;
                continue;
            }
            if (!have.isAir() && player != null) {
                BlockEvent.BreakEvent ev = new BlockEvent.BreakEvent(level, p.immutable(), have, player);
                NeoForge.EVENT_BUS.post(ev);
                if (ev.isCanceled()) {
                    job.kept++;
                    continue;
                }
            }
            level.setBlock(p, want, Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
            if (!want.isAir()) {
                job.placed++;
                if (job.placed % 96 == 0) {
                    level.sendParticles(ParticleTypes.END_ROD, p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 3, 0.3, 0.3, 0.3, 0.02);
                }
            }
        }
        if (level.getGameTime() % 8 == 0) {
            level.playSound(null, job.origin, SoundEvents.BEACON_AMBIENT, SoundSource.BLOCKS, 0.6f, 1.8f);
        }
        if (job.index < total) {
            return false;
        }
        if (player != null) {
            player.displayClientMessage(Component.translatable("oror.blueprinter.done", job.placed, job.kept).withStyle(ChatFormatting.AQUA), false);
        }
        level.playSound(null, job.origin, SoundEvents.BEACON_DEACTIVATE, SoundSource.BLOCKS, 1.0f, 1.4f);
        return true;
    }

    /** Dust along the twelve edges of the box, to that player only. */
    static void outline(ServerLevel level, ServerPlayer player, BlockPos lo, int[] dims) {
        double x0 = lo.getX(), y0 = lo.getY(), z0 = lo.getZ();
        double x1 = x0 + dims[0], y1 = y0 + dims[1], z1 = z0 + dims[2];
        double[][] edges = {
            {x0, y0, z0, x1, y0, z0}, {x0, y1, z0, x1, y1, z0}, {x0, y0, z1, x1, y0, z1}, {x0, y1, z1, x1, y1, z1},
            {x0, y0, z0, x0, y1, z0}, {x1, y0, z0, x1, y1, z0}, {x0, y0, z1, x0, y1, z1}, {x1, y0, z1, x1, y1, z1},
            {x0, y0, z0, x0, y0, z1}, {x1, y0, z0, x1, y0, z1}, {x0, y1, z0, x0, y1, z1}, {x1, y1, z0, x1, y1, z1},
        };
        for (double[] e : edges) {
            double len = Math.max(Math.abs(e[3] - e[0]), Math.max(Math.abs(e[4] - e[1]), Math.abs(e[5] - e[2])));
            int n = (int) Math.max(1, Math.min(24, Math.ceil(len)));
            for (int k = 0; k <= n; k++) {
                double t = (double) k / n;
                level.sendParticles(player, LINE, true, e[0] + (e[3] - e[0]) * t, e[1] + (e[4] - e[1]) * t, e[2] + (e[5] - e[2]) * t, 1, 0, 0, 0, 0);
            }
        }
    }

    // ---------------------------------------------------------------------------------------------------------------
    // storage: <world>/oror_blueprints/<id>.dat, gzip NBT; the oldest are removed past KEEP_FILES

    static Path dir(MinecraftServer server) {
        return server.getWorldPath(LevelResource.ROOT).resolve("oror_blueprints");
    }

    static void store(MinecraftServer server, UUID id, Blueprint bp) throws IOException {
        CompoundTag tag = new CompoundTag();
        tag.putIntArray("Size", new int[] {bp.sx(), bp.sy(), bp.sz()});
        ListTag palette = new ListTag();
        for (BlockState s : bp.palette()) {
            palette.add(NbtUtils.writeBlockState(s));
        }
        tag.put("Palette", palette);
        tag.putIntArray("Cells", bp.cells());
        Path dir = dir(server);
        Files.createDirectories(dir);
        NbtIo.writeCompressed(tag, dir.resolve(id + ".dat"));
        CACHE.put(id, bp);
        try (Stream<Path> files = Files.list(dir)) {
            List<Path> all = files.filter(f -> f.toString().endsWith(".dat")).sorted(Comparator.comparingLong(f -> f.toFile().lastModified())).toList();
            for (int k = 0; k < all.size() - KEEP_FILES; k++) {
                Files.deleteIfExists(all.get(k));
            }
        }
    }

    static Blueprint load(MinecraftServer server, UUID id) {
        Blueprint cached = CACHE.get(id);
        if (cached != null) {
            return cached;
        }
        Path file = dir(server).resolve(id + ".dat");
        if (!Files.exists(file)) {
            return null;
        }
        try {
            CompoundTag tag = NbtIo.readCompressed(file, NbtAccounter.unlimitedHeap());
            int[] size = tag.getIntArray("Size");
            ListTag list = tag.getList("Palette", Tag.TAG_COMPOUND);
            List<BlockState> palette = new ArrayList<>(list.size());
            for (int k = 0; k < list.size(); k++) {
                palette.add(NbtUtils.readBlockState(BuiltInRegistries.BLOCK.asLookup(), list.getCompound(k)));
            }
            int[] cells = tag.getIntArray("Cells");
            if (size.length != 3 || cells.length != size[0] * size[1] * size[2]) {
                return null;
            }
            for (int k = 0; k < cells.length; k++) {
                if (cells[k] >= palette.size()) {
                    cells[k] = -1;
                }
            }
            Blueprint bp = new Blueprint(size[0], size[1], size[2], palette, cells);
            CACHE.put(id, bp);
            return bp;
        } catch (IOException e) {
            return null;
        }
    }

    @SubscribeEvent
    public static void stopping(ServerStoppingEvent event) {
        JOBS.clear();
        PREVIEWS.clear();
        CACHE.clear();
    }

    private Blueprints() {
    }
}
