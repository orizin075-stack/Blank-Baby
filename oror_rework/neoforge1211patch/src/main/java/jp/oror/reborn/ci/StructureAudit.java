package jp.oror.reborn.ci;

import com.mojang.datafixers.util.Either;
import com.mojang.datafixers.util.Pair;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.EmptyBlockGetter;
import net.minecraft.world.level.LightLayer;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.status.ChunkStatus;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.PoolElementStructurePiece;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import net.minecraft.world.level.levelgen.structure.pools.SinglePoolElement;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplateManager;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (r62) Every structure of OROR's own as world generation really builds it (the user: buildings without light inside,
 * buildings that pass as generated but stand broken, floating buildings). Each is found with the game's own search
 * (as /locate), its chunks are generated in full (terrain, features, light), and every template piece of it is compared
 * with the world, cell by cell:
 * <ul>
 * <li>missing: a block of the template that is not in the world (another block stands there);</li>
 * <li>intruding: natural ground, rock, water, logs or leaves inside the building, in a cell the template leaves empty
 * with the template's blocks both above and below it (a room, a hall, a passage);</li>
 * <li>floating: a column whose lowest template block has air, water or leaves under it, and how deep the gap is;</li>
 * <li>dark: a cell indoors where one stands (the template's block under it, room for the head, a roof somewhere above)
 * with block light under 8.</li>
 * </ul>
 * One STRUCT-AUDIT line per structure, then STRUCT-AUDIT-RESULT.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class StructureAudit {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Structures");
    public static volatile boolean resultLogged;
    private static final int CHUNKS_PER_TICK = 4;
    private static final int RADIUS = 48;
    /** wall-clock budget: the dedicated-server job has the lanes before this one to run as well */
    private static final long BUDGET_MS = 15L * 60 * 1000;
    private static Run run;

    private StructureAudit() {
    }

    static final class Run {
        ServerLevel level;
        List<ResourceKey<Structure>> keys = new ArrayList<>();
        int index;
        StructureStart start;
        ResourceKey<Structure> current;
        List<ChunkPos> todo = new ArrayList<>();
        int done;
        long startedAt;
        long startedMs;
        int found, missingTotal, intrudingTotal, floatingTotal, darkTotal, indoorTotal;
        List<String> notFound = new ArrayList<>();
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("structures").then(Commands.literal("audit")
            .requires(s -> s.hasPermission(2)).executes(c -> start(c.getSource())))));
    }

    private static int start(CommandSourceStack src) {
        if (run != null) {
            return 0;
        }
        Run r = new Run();
        r.level = src.getServer().overworld();
        Registry<Structure> reg = r.level.registryAccess().registryOrThrow(Registries.STRUCTURE);
        for (ResourceKey<Structure> k : reg.registryKeySet()) {
            if (k.location().getNamespace().equals("oror_supreme_bosses")) {
                r.keys.add(k);
            }
        }
        // the kingdom and the buildings players walk into most first, the gods' citadels after them
        r.keys.sort((a, b) -> {
            int ra = rank(a.location().getPath()), rb = rank(b.location().getPath());
            return ra != rb ? Integer.compare(ra, rb) : a.location().toString().compareTo(b.location().toString());
        });
        r.startedAt = r.level.getGameTime();
        r.startedMs = System.currentTimeMillis();
        run = r;
        resultLogged = false;
        LOG.info("STRUCT-AUDIT-START {\"structures\":{}}", r.keys.size());
        return 1;
    }

    private static int rank(String path) {
        if (path.contains("kingdom")) {
            return 0;
        }
        return path.endsWith("_citadel") ? 2 : 1;
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        Run r = run;
        if (r == null) {
            return;
        }
        try {
            step(r);
        } catch (Throwable t) {
            LOG.error("STRUCT-AUDIT failed at {}", r.current, t);
            r.notFound.add(String.valueOf(r.current) + " (error " + t + ")");
            r.start = null;
            r.todo.clear();
            r.index++;
        }
        if (r.index >= r.keys.size() && r.start == null) {
            LOG.info("STRUCT-AUDIT-RESULT {\"structures\":{},\"found\":{},\"missing\":{},\"intruding\":{},\"floatingColumns\":{},\"indoor\":{},\"dark\":{},\"notFound\":\"{}\",\"footingPieces\":{},\"footingCleared\":{},\"footingLaid\":{},\"guardStarts\":{},\"guardRefused\":{},\"ticks\":{}}",
                r.keys.size(), r.found, r.missingTotal, r.intrudingTotal, r.floatingTotal, r.indoorTotal, r.darkTotal,
                String.join(" ", r.notFound), jp.oror.reborn.worldgen.StructureFooting.PIECES.get(),
                jp.oror.reborn.worldgen.StructureFooting.CLEARED.get(), jp.oror.reborn.worldgen.StructureFooting.FOOTED.get(),
                jp.oror.reborn.worldgen.StructureGuard.STARTS.get(), jp.oror.reborn.worldgen.StructureGuard.REFUSED.get(),
                r.level.getGameTime() - r.startedAt);
            resultLogged = true;
            run = null;
        }
    }

    private static void step(Run r) {
        if (r.start == null) {
            if (r.index >= r.keys.size()) {
                return;
            }
            r.current = r.keys.get(r.index);
            if (System.currentTimeMillis() - r.startedMs > BUDGET_MS) {
                r.notFound.add(r.current.location().getPath() + "(not searched)");
                r.index++;
                return;
            }
            Registry<Structure> reg = r.level.registryAccess().registryOrThrow(Registries.STRUCTURE);
            Holder<Structure> holder = reg.getHolderOrThrow(r.current);
            Pair<BlockPos, Holder<Structure>> at = r.level.getChunkSource().getGenerator()
                .findNearestMapStructure(r.level, HolderSet.direct(holder), BlockPos.ZERO, RADIUS, false);
            if (at == null) {
                r.notFound.add(r.current.location().getPath());
                LOG.info("STRUCT-AUDIT {\"id\":\"{}\",\"found\":false}", r.current.location());
                r.index++;
                return;
            }
            ChunkPos cp = new ChunkPos(at.getFirst());
            ChunkAccess c = r.level.getChunk(cp.x, cp.z, ChunkStatus.STRUCTURE_STARTS);
            StructureStart st = c.getStartForStructure(holder.value());
            if (st == null || !st.isValid()) {
                r.notFound.add(r.current.location().getPath() + "(no start)");
                LOG.info("STRUCT-AUDIT {\"id\":\"{}\",\"found\":false,\"at\":[{},{}],\"start\":false}", r.current.location(), cp.x, cp.z);
                r.index++;
                return;
            }
            r.start = st;
            BoundingBox bb = st.getBoundingBox();
            r.todo.clear();
            for (int x = (bb.minX() >> 4) - 1; x <= (bb.maxX() >> 4) + 1; x++) {
                for (int z = (bb.minZ() >> 4) - 1; z <= (bb.maxZ() >> 4) + 1; z++) {
                    r.todo.add(new ChunkPos(x, z));
                }
            }
            r.done = 0;
            return;
        }
        if (r.done < r.todo.size()) {
            for (int i = 0; i < CHUNKS_PER_TICK && r.done < r.todo.size(); i++, r.done++) {
                ChunkPos p = r.todo.get(r.done);
                r.level.setChunkForced(p.x, p.z, true);
                r.level.getChunk(p.x, p.z);
            }
            return;
        }
        try {
            audit(r);
        } finally {
            for (ChunkPos p : r.todo) {
                r.level.setChunkForced(p.x, p.z, false);
            }
        }
        r.start = null;
        r.index++;
    }

    private static boolean solid(BlockState s) {
        return !s.isAir() && !s.is(Blocks.STRUCTURE_VOID) && s.isCollisionShapeFullBlock(EmptyBlockGetter.INSTANCE, BlockPos.ZERO);
    }

    private static boolean natural(BlockState s) {
        return s.is(BlockTags.BASE_STONE_OVERWORLD) || s.is(BlockTags.DIRT) || s.is(BlockTags.SAND) || s.is(Blocks.GRAVEL)
            || s.is(BlockTags.LOGS) || s.is(BlockTags.LEAVES) || s.is(Blocks.WATER) || s.is(Blocks.LAVA) || s.is(Blocks.SNOW_BLOCK)
            || s.is(Blocks.POWDER_SNOW) || s.is(Blocks.ICE) || s.is(Blocks.PACKED_ICE) || s.is(Blocks.CLAY) || s.is(BlockTags.TERRACOTTA)
            || s.is(Blocks.SANDSTONE) || s.is(Blocks.RED_SANDSTONE) || s.is(BlockTags.COAL_ORES) || s.is(BlockTags.IRON_ORES)
            || s.is(BlockTags.COPPER_ORES) || s.is(Blocks.SHORT_GRASS) || s.is(Blocks.TALL_GRASS) || s.is(Blocks.FERN);
    }

    /** A block and its weathered or broken forms (the weathered processor, cracked or mossy bricks) count as one. */
    private static String family(Block b) {
        String id = BuiltInRegistries.BLOCK.getKey(b).getPath();
        return id.replace("mossy_", "").replace("cracked_", "").replace("chiseled_", "").replace("infested_", "");
    }

    private static Field field(Class<?> c, String name) throws NoSuchFieldException {
        for (Class<?> k = c; k != null; k = k.getSuperclass()) {
            try {
                Field f = k.getDeclaredField(name);
                f.setAccessible(true);
                return f;
            } catch (NoSuchFieldException ignored) {
            }
        }
        throw new NoSuchFieldException(c.getName() + "." + name);
    }

    @SuppressWarnings("unchecked")
    static StructureTemplate template(SinglePoolElement el, StructureTemplateManager manager) throws ReflectiveOperationException {
        Either<ResourceLocation, StructureTemplate> t = (Either<ResourceLocation, StructureTemplate>) field(SinglePoolElement.class, "template").get(el);
        return t.map(manager::getOrCreate, x -> x);
    }

    @SuppressWarnings("unchecked")
    static List<StructureTemplate.StructureBlockInfo> blocks(StructureTemplate t) throws ReflectiveOperationException {
        List<StructureTemplate.Palette> palettes = (List<StructureTemplate.Palette>) field(StructureTemplate.class, "palettes").get(t);
        return palettes.isEmpty() ? List.of() : palettes.get(0).blocks();
    }

    static void audit(Run r) {
        ServerLevel level = r.level;
        StructureTemplateManager manager = level.getStructureManager();
        long missing = 0, intruding = 0, floating = 0, columns = 0, indoor = 0, dark = 0, cells = 0;
        int maxGap = 0, pieces = 0, templatePieces = 0;
        StringBuilder grounds = new StringBuilder();
        long gapSum = 0;
        Map<String, Integer> missPairs = new HashMap<>();
        Map<String, Integer> intrudeKinds = new HashMap<>();
        List<String> darkSamples = new ArrayList<>(), floatSamples = new ArrayList<>(), intrudeSamples = new ArrayList<>(), missSamples = new ArrayList<>();
        BlockPos.MutableBlockPos w = new BlockPos.MutableBlockPos();
        for (StructurePiece piece : r.start.getPieces()) {
            pieces++;
            if (!(piece instanceof PoolElementStructurePiece pe) || !(pe.getElement() instanceof SinglePoolElement el)) {
                continue;
            }
            StructureTemplate t;
            List<StructureTemplate.StructureBlockInfo> infos;
            try {
                t = template(el, manager);
                infos = blocks(t);
            } catch (ReflectiveOperationException ex) {
                LOG.warn("STRUCT-AUDIT reflection", ex);
                continue;
            }
            templatePieces++;
            StructurePlaceSettings settings = new StructurePlaceSettings().setRotation(pe.getRotation());
            BlockPos origin = pe.getPosition();
            int sx = t.getSize().getX(), sy = t.getSize().getY(), sz = t.getSize().getZ();
            // the template as a grid: 0 left empty (structure void or absent), 1 air, 2 a full block, 3 another block
            byte[] grid = new byte[sx * sy * sz];
            for (StructureTemplate.StructureBlockInfo info : infos) {
                BlockPos p = info.pos();
                if (p.getX() < 0 || p.getY() < 0 || p.getZ() < 0 || p.getX() >= sx || p.getY() >= sy || p.getZ() >= sz) {
                    continue;
                }
                BlockState s = info.state();
                byte v = s.is(Blocks.STRUCTURE_VOID) || s.is(Blocks.JIGSAW) ? 0 : s.isAir() ? (byte) 1 : solid(s) ? (byte) 2 : (byte) 3;
                grid[(p.getX() * sy + p.getY()) * sz + p.getZ()] = v;
                if (v >= 2) {
                    BlockPos wp = StructureTemplate.calculateRelativePosition(settings, p).offset(origin);
                    if (!level.hasChunkAt(wp)) {
                        continue;
                    }
                    BlockState have = level.getBlockState(wp);
                    cells++;
                    if (have.getBlock() != s.getBlock() && !family(have.getBlock()).equals(family(s.getBlock()))
                        && !s.is(BlockTags.LEAVES) && !s.is(BlockTags.CROPS) && !s.is(Blocks.WATER) && !s.is(Blocks.LAVA)
                        && !s.is(BlockTags.FIRE) && !s.is(BlockTags.SAPLINGS)) {
                        missing++;
                        missPairs.merge(BuiltInRegistries.BLOCK.getKey(s.getBlock()).getPath() + "->"
                            + BuiltInRegistries.BLOCK.getKey(have.getBlock()).getPath(), 1, Integer::sum);
                        if (missSamples.size() < 12 && (missing % 37 == 1 || missSamples.size() < 4)) {
                            missSamples.add(wp.getX() + " " + wp.getY() + " " + wp.getZ() + " " + BuiltInRegistries.BLOCK.getKey(have.getBlock()).getPath()
                                + " (template " + p.getX() + " " + p.getY() + " " + p.getZ() + ")");
                        }
                    }
                }
            }
            // the template's ground: the height most of its columns start at (a column starting higher up, an eave or
            // a bridge, is not counted as floating)
            int[] lows = new int[sx * sz], highs = new int[sx * sz];
            int[] lowCount = new int[sy];
            for (int x = 0; x < sx; x++) {
                for (int z = 0; z < sz; z++) {
                    int low = -1, high = -1;
                    for (int y = 0; y < sy; y++) {
                        if (grid[(x * sy + y) * sz + z] == 2) {
                            if (low < 0) {
                                low = y;
                            }
                            high = y;
                        }
                    }
                    lows[x * sz + z] = low;
                    highs[x * sz + z] = high;
                    if (low >= 0) {
                        lowCount[low]++;
                    }
                }
            }
            int ground = 0;
            for (int y = 1; y < sy; y++) {
                if (lowCount[y] > lowCount[ground]) {
                    ground = y;
                }
            }
            if (grounds.length() < 60) {
                grounds.append(grounds.length() > 0 ? " " : "").append(ground);
            }
            for (int x = 0; x < sx; x++) {
                for (int z = 0; z < sz; z++) {
                    int low = lows[x * sz + z], high = highs[x * sz + z];
                    if (low < 0) {
                        continue;
                    }
                    BlockPos base = StructureTemplate.calculateRelativePosition(settings, new BlockPos(x, low, z)).offset(origin);
                    if (low <= ground + 1 && level.hasChunkAt(base)) {
                        columns++;
                        int gap = 0;
                        for (int d = 1; d <= 64; d++) {
                            BlockState below = level.getBlockState(w.set(base.getX(), base.getY() - d, base.getZ()));
                            if (below.isAir() || below.is(Blocks.WATER) || below.is(BlockTags.LEAVES) || below.is(Blocks.LAVA)) {
                                gap = d;
                            } else {
                                break;
                            }
                        }
                        if (gap > 0) {
                            floating++;
                            gapSum += gap;
                            maxGap = Math.max(maxGap, gap);
                            if (floatSamples.size() < 6) {
                                floatSamples.add(base.getX() + " " + base.getY() + " " + base.getZ() + " gap " + gap);
                            }
                        }
                    }
                    for (int y = low + 1; y < high; y++) {
                        byte v = grid[(x * sy + y) * sz + z];
                        if (v == 2 || v == 3) {
                            continue;
                        }
                        BlockPos wp = StructureTemplate.calculateRelativePosition(settings, new BlockPos(x, y, z)).offset(origin);
                        if (!level.hasChunkAt(wp)) {
                            continue;
                        }
                        BlockState have = level.getBlockState(wp);
                        if (natural(have)) {
                            intruding++;
                            intrudeKinds.merge(BuiltInRegistries.BLOCK.getKey(have.getBlock()).getPath(), 1, Integer::sum);
                            if (intrudeSamples.size() < 6) {
                                intrudeSamples.add(wp.getX() + " " + wp.getY() + " " + wp.getZ() + " " + BuiltInRegistries.BLOCK.getKey(have.getBlock()).getPath());
                            }
                            continue;
                        }
                        // a place to stand indoors: the template's full block under it and room for the head
                        if (grid[(x * sy + y - 1) * sz + z] == 2 && y + 1 < sy && grid[(x * sy + y + 1) * sz + z] != 2
                            && !have.isCollisionShapeFullBlock(level, wp)) {
                            indoor++;
                            if (level.getBrightness(LightLayer.BLOCK, wp) < 8) {
                                dark++;
                                if (darkSamples.size() < 6) {
                                    darkSamples.add(wp.getX() + " " + wp.getY() + " " + wp.getZ());
                                }
                            }
                        }
                    }
                }
            }
        }
        r.found++;
        r.missingTotal += (int) missing;
        r.intrudingTotal += (int) intruding;
        r.floatingTotal += (int) floating;
        r.indoorTotal += (int) indoor;
        r.darkTotal += (int) dark;
        BoundingBox bb = r.start.getBoundingBox();
        LOG.info(String.format(Locale.ROOT,
            "STRUCT-AUDIT {\"id\":\"%s\",\"found\":true,\"ground\":\"%s\",\"box\":[%d,%d,%d,%d,%d,%d],\"pieces\":%d,\"templatePieces\":%d,\"cells\":%d,"
                + "\"missing\":%d,\"missingPct\":%.2f,\"missingTop\":\"%s\",\"missingAt\":\"%s\",\"intruding\":%d,\"intrudingTop\":\"%s\",\"intrudingAt\":\"%s\","
                + "\"columns\":%d,\"floatingColumns\":%d,\"floatingPct\":%.2f,\"maxGap\":%d,\"meanGap\":%.1f,\"floatingAt\":\"%s\","
                + "\"indoor\":%d,\"dark\":%d,\"darkPct\":%.1f,\"darkAt\":\"%s\"}",
            r.current.location(), grounds, bb.minX(), bb.minY(), bb.minZ(), bb.maxX(), bb.maxY(), bb.maxZ(), pieces, templatePieces, cells,
            missing, cells == 0 ? 0 : 100.0 * missing / cells, top(missPairs), String.join("; ", missSamples), intruding, top(intrudeKinds), String.join("; ", intrudeSamples),
            columns, floating, columns == 0 ? 0 : 100.0 * floating / columns, maxGap, floating == 0 ? 0 : (double) gapSum / floating,
            String.join("; ", floatSamples), indoor, dark, indoor == 0 ? 0 : 100.0 * dark / indoor, String.join("; ", darkSamples)));
    }

    private static String top(Map<String, Integer> m) {
        return m.entrySet().stream().sorted((a, b) -> b.getValue() - a.getValue()).limit(6)
            .map(x -> x.getKey() + " " + x.getValue()).reduce((a, b) -> a + ", " + b).orElse("");
    }
}
