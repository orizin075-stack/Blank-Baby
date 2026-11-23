package jp.oror.reborn.worldgen;

import com.mojang.datafixers.util.Either;
import java.lang.reflect.Field;
import java.util.BitSet;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.level.EmptyBlockGetter;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.PoolElementStructurePiece;
import net.minecraft.world.level.levelgen.structure.pools.SinglePoolElement;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (r62) What world generation does after one of OROR's own templates is placed in a chunk (the user: floating buildings,
 * buildings broken inside). Its templates store only their blocks (the rooms are left empty, not air), so where the
 * land is higher than a building's floor the natural ground, rock, trees and grass stayed inside its halls, and where
 * the land falls away from its centre (a slope, a valley, a lake) its floor hung over the drop.
 * <ul>
 * <li>Inside: in each column of the template, between its lowest and highest block, a cell the template leaves empty
 * that holds natural ground (rock, dirt, sand, gravel, logs, leaves, snow, plants) is cleared to air.</li>
 * <li>Under: a column that starts at the template's ground (its most common lowest block, give or take one) gets a footing
 * down to the land, at most 64 blocks, through air, water, lava, leaves and plants, of the template's own lowest block
 * where that is a plain full block, of stone bricks otherwise.</li>
 * </ul>
 * Only cells inside the chunk being generated are touched (the box), so each chunk does its own part.
 */
public final class StructureFooting {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Structures");
    private static final int MAX_FOOTING = 64;
    private static final Map<String, Shape> SHAPES = new ConcurrentHashMap<>();
    private static Field templateField;
    private static Field palettesField;
    private static volatile boolean failed;
    /** For CI (StructureAudit): pieces done, cells cleared inside, footing blocks laid. */
    public static final java.util.concurrent.atomic.AtomicLong PIECES = new java.util.concurrent.atomic.AtomicLong(),
        CLEARED = new java.util.concurrent.atomic.AtomicLong(), FOOTED = new java.util.concurrent.atomic.AtomicLong();

    private StructureFooting() {
    }

    /** One template, as columns: its lowest and highest full block, the empty cells, its ground and footing blocks. */
    private record Shape(int sx, int sy, int sz, int[] low, int[] high, BitSet empty, int ground, BlockState[] foot) {
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

    private static boolean full(BlockState s) {
        return !s.isAir() && !s.is(Blocks.STRUCTURE_VOID) && s.isCollisionShapeFullBlock(EmptyBlockGetter.INSTANCE, BlockPos.ZERO);
    }

    /** Natural ground and growth that does not belong inside a building. */
    public static boolean natural(BlockState s) {
        return s.is(BlockTags.BASE_STONE_OVERWORLD) || s.is(BlockTags.DIRT) || s.is(BlockTags.SAND) || s.is(Blocks.GRAVEL)
            || s.is(BlockTags.LOGS) || s.is(BlockTags.LEAVES) || s.is(Blocks.SNOW) || s.is(Blocks.SNOW_BLOCK) || s.is(Blocks.POWDER_SNOW)
            || s.is(Blocks.CLAY) || s.is(BlockTags.TERRACOTTA) || s.is(Blocks.SANDSTONE) || s.is(Blocks.RED_SANDSTONE)
            || s.is(BlockTags.COAL_ORES) || s.is(BlockTags.IRON_ORES) || s.is(BlockTags.COPPER_ORES) || s.is(Blocks.SHORT_GRASS)
            || s.is(Blocks.TALL_GRASS) || s.is(Blocks.FERN) || s.is(Blocks.LARGE_FERN) || s.is(BlockTags.FLOWERS)
            || s.is(Blocks.SWEET_BERRY_BUSH) || s.is(Blocks.DEAD_BUSH) || s.is(Blocks.VINE) || s.is(Blocks.MOSS_CARPET)
            || s.is(Blocks.MOSS_BLOCK) || s.is(Blocks.POINTED_DRIPSTONE) || s.is(Blocks.DRIPSTONE_BLOCK) || s.is(BlockTags.SAPLINGS)
            || s.is(Blocks.MUD) || s.is(Blocks.ICE) || s.is(Blocks.PACKED_ICE) || s.is(Blocks.BAMBOO) || s.is(Blocks.SUGAR_CANE)
            || s.is(Blocks.PUMPKIN) || s.is(Blocks.MELON) || s.is(Blocks.BROWN_MUSHROOM_BLOCK) || s.is(Blocks.RED_MUSHROOM_BLOCK)
            || s.is(Blocks.MUSHROOM_STEM) || s.is(Blocks.CACTUS);
    }

    /** What a footing goes down through. */
    private static boolean open(BlockState s) {
        // (r66) and sand, gravel and the like: the footing stopped on them, then they fell into the cave under them and
        // left a gap under the floor (the gods' check: under berit's, ferdinand's, mels' and yggdrasil's floors, after placing)
        return s.isAir() || s.is(Blocks.WATER) || s.is(Blocks.LAVA) || s.is(BlockTags.LEAVES) || s.canBeReplaced()
            || s.is(BlockTags.FLOWERS) || s.is(BlockTags.SAPLINGS) || s.is(Blocks.SNOW)
            || s.getBlock() instanceof net.minecraft.world.level.block.FallingBlock
            // and ice that melts (to water, or to air over a hollow): berit's and mels' gaps came after placing too
            || s.is(Blocks.ICE) || s.is(Blocks.FROSTED_ICE) || s.is(Blocks.POWDER_SNOW);
    }

    private static boolean plainFoot(BlockState s) {
        Block b = s.getBlock();
        return full(s) && !s.hasBlockEntity() && !s.is(BlockTags.LEAVES) && !s.is(BlockTags.ICE) && !s.is(BlockTags.WOOL)
            && b != Blocks.GLASS && !s.is(Blocks.TINTED_GLASS) && !s.is(Blocks.GLOWSTONE) && !s.is(Blocks.SEA_LANTERN)
            && !s.is(Blocks.SHROOMLIGHT) && !s.is(Blocks.SLIME_BLOCK) && !s.is(Blocks.HONEY_BLOCK) && !s.is(Blocks.TNT)
            && !s.is(Blocks.BEDROCK) && !s.is(Blocks.BARRIER) && !s.is(BlockTags.CORAL_BLOCKS) && !s.is(Blocks.MAGMA_BLOCK)
            && !s.is(Blocks.GOLD_BLOCK) && !s.is(Blocks.DIAMOND_BLOCK) && !s.is(Blocks.EMERALD_BLOCK) && !s.is(Blocks.NETHERITE_BLOCK)
            && !s.is(Blocks.IRON_BLOCK) && !s.is(Blocks.REDSTONE_BLOCK) && !s.is(Blocks.LAPIS_BLOCK) && !s.is(Blocks.AMETHYST_BLOCK);
    }

    @SuppressWarnings("unchecked")
    private static Shape shape(SinglePoolElement el, PoolElementStructurePiece piece, WorldGenLevel level) throws ReflectiveOperationException {
        if (templateField == null) {
            templateField = field(SinglePoolElement.class, "template");
            palettesField = field(StructureTemplate.class, "palettes");
        }
        Either<ResourceLocation, StructureTemplate> either = (Either<ResourceLocation, StructureTemplate>) templateField.get(el);
        ResourceLocation id = either.left().orElse(null);
        if (id == null || !id.getNamespace().equals("oror_supreme_bosses")) {
            return null;
        }
        Shape cached = SHAPES.get(id.toString());
        if (cached != null) {
            return cached;
        }
        StructureTemplate t = level.getLevel().getStructureManager().getOrCreate(id);
        List<StructureTemplate.Palette> palettes = (List<StructureTemplate.Palette>) palettesField.get(t);
        int sx = t.getSize().getX(), sy = t.getSize().getY(), sz = t.getSize().getZ();
        int[] low = new int[sx * sz], high = new int[sx * sz];
        java.util.Arrays.fill(low, -1);
        java.util.Arrays.fill(high, -1);
        BlockState[] foot = new BlockState[sx * sz];
        BitSet filled = new BitSet(sx * sy * sz);
        if (!palettes.isEmpty()) {
            for (StructureTemplate.StructureBlockInfo info : palettes.get(0).blocks()) {
                BlockPos p = info.pos();
                if (p.getX() < 0 || p.getY() < 0 || p.getZ() < 0 || p.getX() >= sx || p.getY() >= sy || p.getZ() >= sz) {
                    continue;
                }
                BlockState s = info.state();
                if (s.isAir() || s.is(Blocks.STRUCTURE_VOID) || s.is(Blocks.JIGSAW)) {
                    continue;
                }
                filled.set((p.getX() * sz + p.getZ()) * sy + p.getY());
                if (full(s)) {
                    int c = p.getX() * sz + p.getZ();
                    if (low[c] < 0 || p.getY() < low[c]) {
                        low[c] = p.getY();
                        foot[c] = s;
                    }
                    high[c] = Math.max(high[c], p.getY());
                }
            }
        }
        int[] count = new int[Math.max(1, sy)];
        for (int c = 0; c < low.length; c++) {
            if (low[c] >= 0) {
                count[low[c]]++;
            }
        }
        int ground = 0;
        for (int y = 1; y < count.length; y++) {
            if (count[y] > count[ground]) {
                ground = y;
            }
        }
        BitSet empty = new BitSet(sx * sy * sz);
        for (int c = 0; c < low.length; c++) {
            if (low[c] < 0) {
                continue;
            }
            for (int y = low[c] + 1; y < high[c]; y++) {
                int i = c * sy + y;
                if (!filled.get(i)) {
                    empty.set(i);
                }
            }
            if (foot[c] != null && !plainFoot(foot[c])) {
                foot[c] = Blocks.STONE_BRICKS.defaultBlockState();
            }
        }
        Shape s = new Shape(sx, sy, sz, low, high, empty, ground, foot);
        SHAPES.put(id.toString(), s);
        return s;
    }

    /** After the piece has placed its blocks in the chunk of box. */
    public static void after(PoolElementStructurePiece piece, WorldGenLevel level, BoundingBox box) {
        if (failed || !(piece.getElement() instanceof SinglePoolElement el)) {
            return;
        }
        Shape s;
        try {
            s = shape(el, piece, level);
        } catch (ReflectiveOperationException | RuntimeException e) {
            failed = true;
            LOG.error("STRUCT-FOOTING off: cannot read templates", e);
            return;
        }
        if (s == null) {
            return;
        }
        Rotation rot = piece.getRotation();
        StructurePlaceSettings settings = new StructurePlaceSettings().setRotation(rot);
        BlockPos origin = piece.getPosition();
        BlockPos.MutableBlockPos m = new BlockPos.MutableBlockPos();
        BlockState air = Blocks.AIR.defaultBlockState();
        int minY = level.getMinBuildHeight();
        long cleared = 0, footed = 0;
        for (int x = 0; x < s.sx(); x++) {
            for (int z = 0; z < s.sz(); z++) {
                int c = x * s.sz() + z;
                int low = s.low()[c];
                if (low < 0) {
                    continue;
                }
                BlockPos w = StructureTemplate.calculateRelativePosition(settings, new BlockPos(x, 0, z)).offset(origin);
                if (w.getX() < box.minX() || w.getX() > box.maxX() || w.getZ() < box.minZ() || w.getZ() > box.maxZ()) {
                    continue;
                }
                int base = origin.getY();
                for (int y = low + 1; y < s.high()[c]; y++) {
                    if (!s.empty().get(c * s.sy() + y)) {
                        continue;
                    }
                    m.set(w.getX(), base + y, w.getZ());
                    if (natural(level.getBlockState(m))) {
                        level.setBlock(m, air, 2);
                        cleared++;
                    }
                }
                if (low > s.ground() + 1) {
                    continue;
                }
                BlockState foot = s.foot()[c];
                for (int d = 1; d <= MAX_FOOTING; d++) {
                    int y = base + low - d;
                    if (y < minY) {
                        break;
                    }
                    m.set(w.getX(), y, w.getZ());
                    if (!open(level.getBlockState(m))) {
                        break;
                    }
                    level.setBlock(m, foot, 2);
                    footed++;
                }
            }
        }
        if (PIECES.getAndIncrement() == 0) {
            LOG.info("STRUCT-FOOTING on (first piece {})", origin);
        }
        CLEARED.addAndGet(cleared);
        FOOTED.addAndGet(footed);
    }
}
