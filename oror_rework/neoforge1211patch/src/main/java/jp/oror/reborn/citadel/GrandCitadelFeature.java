package jp.oror.reborn.citadel;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.DoubleTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.ImposterProtoChunk;
import net.minecraft.world.level.chunk.ProtoChunk;
import net.minecraft.world.level.chunk.PalettedContainer;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.FeaturePlaceContext;
import net.minecraft.world.level.levelgen.feature.configurations.NoneFeatureConfiguration;

/**
 * Builds the Grand Citadel v12 into the world one chunk at a time, as each chunk of a site (CitadelSites) is generated:
 * the save's blocks, chests and dispensers lifted to the site's ground, and its animals and monsters (the people of the
 * kingdom take their posts when the chunk first loads: CitadelGarrison).
 * It runs last in each chunk (top layer modification), after the trees and other features, which it replaces.
 * Under the citadel the natural rock stays where the save had only dirt; valleys below its ground are filled. Around it a
 * two-chunk apron grades the land between the kingdom's ground and the natural terrain. Every chunk of the kingdom is the
 * Royal Capital biome (no hostile mob spawns, the capital's own grass and sky).
 */
public final class GrandCitadelFeature extends Feature<NoneFeatureConfiguration> {
    private static final BlockState AIR = Blocks.AIR.defaultBlockState();
    private static final BlockState DIRT = Blocks.DIRT.defaultBlockState();
    private static final BlockState STONE = Blocks.STONE.defaultBlockState();
    private static final BlockState GRASS = Blocks.GRASS_BLOCK.defaultBlockState();
    /** How far into a neighbouring chunk this chunk's trees can reach, and how high above the ground. */
    private static final int SPILL = 10;
    public static final ResourceKey<Biome> CAPITAL = ResourceKey.create(Registries.BIOME,
        ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "royal_capital"));

    public GrandCitadelFeature() {
        super(NoneFeatureConfiguration.CODEC);
    }

    @Override
    public boolean place(FeaturePlaceContext<NoneFeatureConfiguration> ctx) {
        WorldGenLevel level = ctx.level();
        ChunkPos pos = new ChunkPos(ctx.origin());
        CitadelSites.Site site = CitadelSites.at(ctx.chunkGenerator(), pos.x, pos.z, CitadelSites.APRON);
        if (site == null) {
            return false;
        }
        ChunkAccess chunk = level.getChunk(pos.x, pos.z);
        int sx = pos.x - site.chunkX() - CitadelData.HALF, sz = pos.z - site.chunkZ() - CitadelData.HALF;
        CitadelData.Chunk data = CitadelData.chunk(sx, sz);
        if (data == null) {
            grade(chunk, site);
        } else {
            build(chunk, site, data);
            populate(level, site, data, sx, sz);
            level.registryAccess().registryOrThrow(Registries.BIOME).getHolder(CAPITAL)
                .ifPresent(capital -> chunk.fillBiomesFromNoise((x, y, z, sampler) -> capital, null));
        }
        tidyNeighbours(level, site, pos);
        return true;
    }

    /** The save's blocks of this chunk, lifted by the site's dy; the save's dirt keeps the natural ground under the topsoil. */
    private static void build(ChunkAccess chunk, CitadelSites.Site site, CitadelData.Chunk data) {
        int dy = site.dy(), ground = site.ground();
        int minY = chunk.getMinBuildHeight(), maxY = chunk.getMaxBuildHeight();
        int bx = chunk.getPos().getMinBlockX(), bz = chunk.getPos().getMinBlockZ();
        int[] natural = new int[256];
        for (int x = 0; x < 16; x++) {
            for (int z = 0; z < 16; z++) {
                natural[x * 16 + z] = chunk.getHeight(Heightmap.Types.OCEAN_FLOOR_WG, x, z) - 1;
            }
        }
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        for (int sy = 0; sy < CitadelData.SECTIONS; sy++) {
            PalettedContainer<BlockState> section = data.sections()[sy];
            for (int y = 0; y < 16; y++) {
                int wy = sy * 16 + y + dy;
                if (wy < minY || wy >= maxY) {
                    continue;
                }
                for (int z = 0; z < 16; z++) {
                    for (int x = 0; x < 16; x++) {
                        // a section the save does not have: below the kingdom's ground it is one the extraction left out
                        // (all dirt and bedrock: the natural ground stays), above it the open sky (the save stores no empty
                        // sections over its buildings); it used to be filled with dirt up to the template's top, burying
                        // the outer belt (runways, helipads, hangars) and roofing the town over
                        BlockState st = section == null ? (wy > ground ? AIR : DIRT) : section.get(x, y, z);
                        p.set(bx + x, wy, bz + z);
                        if (st.is(Blocks.DIRT) || st.is(Blocks.BEDROCK)) {
                            underground(chunk, p, wy, ground, natural[x * 16 + z], section != null);
                        } else {
                            put(chunk, p, st);
                        }
                    }
                }
            }
        }
        // the natural terrain above the template's top (a hill higher than the save reached) is cleared too
        int top = CitadelData.SECTIONS * 16 + dy;
        for (int z = 0; z < 16; z++) {
            for (int x = 0; x < 16; x++) {
                for (int wy = Math.max(top, minY); wy <= natural[x * 16 + z] && wy < maxY; wy++) {
                    put(chunk, p.set(bx + x, wy, bz + z), AIR);
                }
            }
        }
        for (CompoundTag be : data.blockEntities()) {
            CompoundTag t = be.copy();
            t.putInt("x", be.getInt("x") + site.offsetX());
            t.putInt("y", be.getInt("y") + dy);
            t.putInt("z", be.getInt("z") + site.offsetZ());
            p.set(t.getInt("x"), t.getInt("y"), t.getInt("z"));
            if (chunk.getBlockState(p).hasBlockEntity()) {
                chunk.setBlockEntityNbt(t);
            }
        }
    }

    /**
     * Where the save has dirt: its topsoil (the three blocks under the grass) and any valley between the natural terrain
     * and the kingdom's ground become dirt and stone; deeper down the natural rock stays, except that caves opening into
     * the citadel's own tunnels (sections the save built in) are walled with stone.
     */
    private static void underground(ChunkAccess chunk, BlockPos.MutableBlockPos p, int wy, int ground, int natural, boolean built) {
        if (wy >= ground - 3) {
            put(chunk, p, DIRT);
        } else if (wy > natural) {
            put(chunk, p, wy >= ground - 6 ? DIRT : STONE);
        } else if (built) {
            BlockState here = chunk.getBlockState(p);
            if (!here.isSolid() || !here.getFluidState().isEmpty()) {
                put(chunk, p, STONE);
            }
        }
    }

    private static void put(ChunkAccess chunk, BlockPos p, BlockState st) {
        BlockState old = chunk.setBlockState(p, st, false);
        if (old != null && old != st && old.hasBlockEntity()) {
            chunk.removeBlockEntity(p);
        }
        if (st.hasBlockEntity() && old != st) {
            // as WorldGenRegion.setBlock does: an empty block entity, made when the chunk is finished
            CompoundTag t = new CompoundTag();
            t.putInt("x", p.getX());
            t.putInt("y", p.getY());
            t.putInt("z", p.getZ());
            t.putString("id", "DUMMY");
            chunk.setBlockEntityNbt(t);
        }
    }

    /** The apron: the land graded from the kingdom's ground at its edge to the natural terrain two chunks out. */
    private static void grade(ChunkAccess chunk, CitadelSites.Site site) {
        int x0 = site.chunkX() * 16, z0 = site.chunkZ() * 16;
        int x1 = x0 + CitadelSites.SIZE * 16 - 1, z1 = z0 + CitadelSites.SIZE * 16 - 1;
        double reach = CitadelSites.APRON * 16;
        int bx = chunk.getPos().getMinBlockX(), bz = chunk.getPos().getMinBlockZ();
        int minY = chunk.getMinBuildHeight() + 1, maxY = chunk.getMaxBuildHeight() - 1;
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        for (int x = 0; x < 16; x++) {
            for (int z = 0; z < 16; z++) {
                int wx = bx + x, wz = bz + z;
                double dx = wx < x0 ? x0 - wx : Math.max(0, wx - x1);
                double dz = wz < z0 ? z0 - wz : Math.max(0, wz - z1);
                double d = Math.sqrt(dx * dx + dz * dz);
                if (d >= reach) {
                    continue;
                }
                double t = 1 - d / reach;
                t = t * t * (3 - 2 * t);
                int natural = chunk.getHeight(Heightmap.Types.OCEAN_FLOOR_WG, x, z) - 1;
                int g = (int) Math.round(natural + (site.ground() - natural) * t);
                if (g == natural) {
                    continue;
                }
                BlockState top = chunk.getBlockState(p.set(wx, natural, wz));
                if (!top.is(BlockTags.DIRT) && !top.is(BlockTags.SAND) && !top.is(Blocks.SNOW_BLOCK)) {
                    top = GRASS;
                }
                if (g < natural) {
                    // cut the hill down, with whatever grows on it
                    for (int y = g + 1; y <= Math.min(maxY, natural + 24); y++) {
                        BlockState here = chunk.getBlockState(p.set(wx, y, wz));
                        if (y <= natural || vegetation(here)) {
                            put(chunk, p, AIR);
                        }
                    }
                } else {
                    for (int y = Math.max(minY, natural); y < g; y++) {
                        put(chunk, p.set(wx, y, wz), y >= g - 3 ? DIRT : STONE);
                    }
                }
                if (g >= minY && g <= maxY) {
                    put(chunk, p.set(wx, g, wz), top);
                }
            }
        }
    }

    private static boolean vegetation(BlockState st) {
        return st.is(BlockTags.LEAVES) || st.is(BlockTags.LOGS) || st.is(BlockTags.REPLACEABLE) || st.is(Blocks.VINE)
            || st.is(Blocks.BEE_NEST) || st.is(Blocks.COCOA) || st.is(Blocks.MANGROVE_ROOTS) || st.is(Blocks.MOSS_CARPET)
            || st.is(Blocks.SNOW) || st.is(BlockTags.FLOWERS) || st.is(BlockTags.SAPLINGS);
    }

    /** What a neighbour's decoration can leave in a chunk built before it (trees, rocks, ice, a geode's crystals). */
    private static boolean natural(BlockState st) {
        return vegetation(st) || st.is(BlockTags.BASE_STONE_OVERWORLD) || st.is(BlockTags.DIRT) || st.is(BlockTags.SAND)
            || st.is(BlockTags.ICE) || st.is(Blocks.MOSSY_COBBLESTONE) || st.is(Blocks.COBBLESTONE) || st.is(Blocks.GRAVEL)
            || st.is(Blocks.CLAY) || st.is(Blocks.SNOW_BLOCK) || st.is(Blocks.POWDER_SNOW) || st.is(Blocks.AMETHYST_BLOCK)
            || st.is(Blocks.BUDDING_AMETHYST) || st.is(Blocks.AMETHYST_CLUSTER) || st.is(Blocks.CALCITE) || st.is(Blocks.SMOOTH_BASALT)
            || st.is(Blocks.MUSHROOM_STEM) || st.is(Blocks.RED_MUSHROOM_BLOCK) || st.is(Blocks.BROWN_MUSHROOM_BLOCK) || st.is(Blocks.BAMBOO)
            || st.is(Blocks.POINTED_DRIPSTONE) || st.is(Blocks.DRIPSTONE_BLOCK) || st.is(Blocks.MAGMA_BLOCK) || st.is(Blocks.OBSIDIAN);
    }

    /**
     * What this chunk's own decoration put across its border into chunks of the citadel built before it is taken back
     * to the save's blocks there (the neighbour would otherwise keep it). (053) Not only trees and plants (a rock, ice
     * spikes, a geode's crystals, a giant mushroom...), ten blocks in rather than six, and up to the top of the save,
     * not 48 blocks over the ground: a tree on a hill grew into the palace's upper floors. Only where the block there now
     * is one such natural block and the save's is another: what the kingdom built is never touched. Under the ground only
     * the kingdom's own blocks (the mine labyrinth) are put back, never the natural rock the save leaves there, and the
     * hollow of a neighbour's geode only in a chunk no one has been in yet.
     */
    private static void tidyNeighbours(WorldGenLevel level, CitadelSites.Site site, ChunkPos pos) {
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        int top = site.dy() + CitadelData.SECTIONS * 16;
        for (int ox = -1; ox <= 1; ox++) {
            for (int oz = -1; oz <= 1; oz++) {
                if (ox == 0 && oz == 0) {
                    continue;
                }
                int ncx = pos.x + ox, ncz = pos.z + oz;
                int sx = ncx - site.chunkX() - CitadelData.HALF, sz = ncz - site.chunkZ() - CitadelData.HALF;
                CitadelData.Chunk data = CitadelData.chunk(sx, sz);
                if (data == null || !level.hasChunk(ncx, ncz)) {
                    continue;
                }
                ChunkAccess chunk = level.getChunk(ncx, ncz);
                // still being made (no one has been in it): a hole a neighbour's geode left under the ground may be filled
                boolean unvisited = chunk instanceof ProtoChunk && !(chunk instanceof ImposterProtoChunk);
                // the strip of the neighbour next to this chunk
                int xa = ox < 0 ? 16 - SPILL : 0, xb = ox > 0 ? SPILL : 16;
                int za = oz < 0 ? 16 - SPILL : 0, zb = oz > 0 ? SPILL : 16;
                int bx = ncx * 16, bz = ncz * 16;
                for (int y = Math.max(site.dy(), chunk.getMinBuildHeight()); y < top && y < chunk.getMaxBuildHeight(); y++) {
                    int sy = (y - site.dy()) >> 4;
                    if (sy < 0 || sy >= CitadelData.SECTIONS) {
                        continue;
                    }
                    PalettedContainer<BlockState> section = data.sections()[sy];
                    boolean below = y <= site.ground();
                    if (below && section == null) {
                        // under the ground the save's missing sections are the natural ground (place): nothing to take back
                        continue;
                    }
                    for (int x = xa; x < xb; x++) {
                        for (int z = za; z < zb; z++) {
                            BlockState here = chunk.getBlockState(p.set(bx + x, y, bz + z));
                            boolean hole = below && unvisited && here.isAir();
                            if (!hole && (here.isAir() || !natural(here))) {
                                continue;
                            }
                            BlockState want = section == null ? AIR : section.get(x, (y - site.dy()) & 15, z);
                            // (053) under the ground only what the kingdom built (the mine labyrinth's walls) is taken back:
                            // a neighbour's geode had cut into them, its shell and the hollow inside (053's CI,
                            // CAPITAL-INTEGRITY)
                            if (below && (want.isAir() || natural(want))) {
                                continue;
                            }
                            if (want.getBlock() != here.getBlock() && !want.is(Blocks.DIRT) && !want.is(Blocks.BEDROCK)) {
                                put(chunk, p, want);
                            }
                        }
                    }
                }
            }
        }
    }

    /** The save's animals and monsters of this chunk (its people come when it loads: CitadelGarrison). */
    private static void populate(WorldGenLevel level, CitadelSites.Site site, CitadelData.Chunk data, int sx, int sz) {
        for (CompoundTag saved : data.entities()) {
            CompoundTag tag = saved.copy();
            relocate(tag, site);
            Entity e = EntityType.loadEntityRecursive(tag, level.getLevel(), x -> x);
            if (e != null) {
                if (e instanceof Mob mob) {
                    mob.setPersistenceRequired();
                }
                level.addFreshEntityWithPassengers(e);
            }
        }
    }

    /** Moves a saved entity (and its riders) to the site, with a new identity and no remembered places from the save. */
    private static void relocate(CompoundTag tag, CitadelSites.Site site) {
        tag.remove("UUID");
        tag.remove("Brain");
        ListTag pos = tag.getList("Pos", Tag.TAG_DOUBLE);
        if (pos.size() == 3) {
            ListTag moved = new ListTag();
            moved.add(DoubleTag.valueOf(pos.getDouble(0) + site.offsetX()));
            moved.add(DoubleTag.valueOf(pos.getDouble(1) + site.dy()));
            moved.add(DoubleTag.valueOf(pos.getDouble(2) + site.offsetZ()));
            tag.put("Pos", moved);
        }
        ListTag riders = tag.getList("Passengers", Tag.TAG_COMPOUND);
        for (int i = 0; i < riders.size(); i++) {
            relocate(riders.getCompound(i), site);
        }
    }
}
