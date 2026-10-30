package jp.oror.reborn.citadel;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Random;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.QuartPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BiomeTags;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.LevelHeightAccessor;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.chunk.ChunkGeneratorStructureState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.RandomState;
import net.minecraft.world.level.levelgen.structure.StructureSet;
import net.minecraft.world.level.levelgen.structure.placement.ConcentricRingsStructurePlacement;
import net.minecraft.world.level.saveddata.SavedData;

/**
 * Where Grand Citadels stand in a world. The overworld is cut into regions of 256 x 256 chunks; each region gets one
 * candidate place from the seed, tried up to four times, and keeps it only where the land under the whole 1,280-block
 * kingdom is dry and level enough (sampled from the terrain noise, so before anything is generated), away from the
 * world's spawn and from every stronghold. Operators can add more with /oror citadel place. Everything a worldgen
 * thread asks is a pure function of the seed, so the threads agree without the world being loaded.
 */
public final class CitadelSites {
    public static final int REGION = 256;
    public static final int SIZE = CitadelData.CHUNKS;
    /** Chunks of graded land around the kingdom, between its ground and the natural terrain. */
    public static final int APRON = 2;
    /** Chunks around the kingdom where no other structure starts. */
    public static final int CLEAR = 6;
    private static final int EDGE = 8;
    private static final int ATTEMPTS = 4;
    private static final int SPAWN_CLEAR = 24;
    private static final long SALT = 0x4F524F52_43495441L;

    /** A citadel: its north-west chunk and the y of its ground (the save's grass at y 64). */
    public record Site(int chunkX, int chunkZ, int ground, boolean forced) {
        public int dy() {
            return ground - CitadelData.GROUND;
        }

        /** World x of the save's x 0. */
        public int offsetX() {
            return (chunkX + CitadelData.HALF) * 16;
        }

        public int offsetZ() {
            return (chunkZ + CitadelData.HALF) * 16;
        }

        public boolean contains(int cx, int cz, int margin) {
            return cx >= chunkX - margin && cx < chunkX + SIZE + margin && cz >= chunkZ - margin && cz < chunkZ + SIZE + margin;
        }

        public BlockPos toWorld(int x, int y, int z) {
            return new BlockPos(x + offsetX(), y + dy(), z + offsetZ());
        }

        public BlockPos center() {
            return toWorld(0, CitadelData.GROUND + 1, 0);
        }

        public BlockPos throne() {
            return toWorld(CitadelData.THRONE_X, CitadelData.THRONE_Y, CitadelData.THRONE_Z);
        }
    }

    private record World(ChunkGenerator generator, RandomState random, long seed, LevelHeightAccessor height, int seaLevel,
                         ChunkGeneratorStructureState structures, Map<Long, Optional<Site>> regions, List<Site> forced,
                         ChunkPos[][] strongholds) {
    }

    private static volatile World world;

    private CitadelSites() {
    }

    /** Called when the overworld is created, before its first chunk is generated. */
    public static void bind(ServerLevel level) {
        Store store = level.getDataStorage().computeIfAbsent(Store.FACTORY, "oror_citadels");
        world = new World(level.getChunkSource().getGenerator(), level.getChunkSource().randomState(), level.getSeed(), level,
            level.getSeaLevel(), level.getChunkSource().getGeneratorState(), new ConcurrentHashMap<>(),
            new CopyOnWriteArrayList<>(store.sites), new ChunkPos[1][]);
    }

    public static void unbind() {
        world = null;
    }

    public static boolean bound(ChunkGenerator generator) {
        World w = world;
        return w != null && w.generator == generator;
    }

    /** The citadel whose footprint, widened by margin chunks, holds chunk cx, cz of this generator's world, if any. */
    public static Site at(ChunkGenerator generator, int cx, int cz, int margin) {
        World w = world;
        if (w == null || w.generator != generator) {
            return null;
        }
        for (Site s : w.forced) {
            if (s.contains(cx, cz, margin)) {
                return s;
            }
        }
        int rx = Math.floorDiv(cx, REGION), rz = Math.floorDiv(cz, REGION);
        Site s = w.regions.computeIfAbsent(ChunkPos.asLong(rx, rz), k -> Optional.ofNullable(choose(w, rx, rz))).orElse(null);
        return s != null && s.contains(cx, cz, margin) ? s : null;
    }

    /** True where other structures must not start: within CLEAR chunks of a citadel. */
    public static boolean excludesStructures(ChunkGenerator generator, ChunkPos pos) {
        return at(generator, pos.x, pos.z, CLEAR) != null;
    }

    /** The nearest citadel to pos within radius regions, or null. Slow the first time a region is asked: run it off the server thread. */
    public static Site nearest(BlockPos pos, int radius) {
        World w = world;
        if (w == null) {
            return null;
        }
        Site best = null;
        double bestD = Double.MAX_VALUE;
        List<Site> candidates = new ArrayList<>(w.forced);
        int rx0 = Math.floorDiv(pos.getX() >> 4, REGION), rz0 = Math.floorDiv(pos.getZ() >> 4, REGION);
        for (int ring = 0; ring <= radius; ring++) {
            for (int rx = rx0 - ring; rx <= rx0 + ring; rx++) {
                for (int rz = rz0 - ring; rz <= rz0 + ring; rz++) {
                    if (Math.max(Math.abs(rx - rx0), Math.abs(rz - rz0)) != ring) {
                        continue;
                    }
                    int x = rx, z = rz;
                    w.regions.computeIfAbsent(ChunkPos.asLong(x, z), k -> Optional.ofNullable(choose(w, x, z))).ifPresent(candidates::add);
                }
            }
            for (Site s : candidates) {
                double d = s.center().distSqr(pos);
                if (d < bestD) {
                    bestD = d;
                    best = s;
                }
            }
            // a site in the next ring is at least (ring) regions away
            if (best != null && Math.sqrt(bestD) < ring * REGION * 16.0) {
                break;
            }
        }
        return best;
    }

    /** An operator's citadel centred on the column x, z; its ground follows the land there. Null if it would overlap another. */
    public static Site place(ServerLevel level, int x, int z) {
        World w = world;
        if (w == null) {
            return null;
        }
        int cx = (x >> 4) - CitadelData.HALF, cz = (z >> 4) - CitadelData.HALF;
        Integer ground = survey(w, cx, cz, true);
        Site site = new Site(cx, cz, ground, true);
        int m = APRON + CLEAR;
        for (int rx = Math.floorDiv(cx - m, REGION); rx <= Math.floorDiv(cx + SIZE + m, REGION); rx++) {
            for (int rz = Math.floorDiv(cz - m, REGION); rz <= Math.floorDiv(cz + SIZE + m, REGION); rz++) {
                int x0 = rx, z0 = rz;
                Site other = w.regions.computeIfAbsent(ChunkPos.asLong(x0, z0), k -> Optional.ofNullable(choose(w, x0, z0))).orElse(null);
                if (other != null && overlaps(site, other)) {
                    return null;
                }
            }
        }
        for (Site other : w.forced) {
            if (overlaps(site, other)) {
                return null;
            }
        }
        w.forced.add(site);
        Store store = level.getDataStorage().computeIfAbsent(Store.FACTORY, "oror_citadels");
        store.sites.add(site);
        store.setDirty();
        return site;
    }

    private static boolean overlaps(Site a, Site b) {
        int m = APRON + CLEAR;
        return a.chunkX - m < b.chunkX + SIZE + m && b.chunkX - m < a.chunkX + SIZE + m
            && a.chunkZ - m < b.chunkZ + SIZE + m && b.chunkZ - m < a.chunkZ + SIZE + m;
    }

    private static Site choose(World w, int rx, int rz) {
        Random r = new Random(w.seed ^ SALT ^ rx * 341873128712L ^ rz * 132897987541L);
        int span = REGION - 2 * EDGE - SIZE;
        for (int attempt = 0; attempt < ATTEMPTS; attempt++) {
            int cx = rx * REGION + EDGE + r.nextInt(span + 1);
            int cz = rz * REGION + EDGE + r.nextInt(span + 1);
            Site probe = new Site(cx, cz, 0, false);
            if (probe.contains(0, 0, CLEAR + SPAWN_CLEAR) || nearStronghold(w, probe)) {
                continue;
            }
            for (Site f : w.forced) {
                if (overlaps(probe, f)) {
                    probe = null;
                    break;
                }
            }
            if (probe == null) {
                continue;
            }
            Integer ground = survey(w, cx, cz, false);
            if (ground != null) {
                return new Site(cx, cz, ground, false);
            }
        }
        return null;
    }

    private static boolean nearStronghold(World w, Site s) {
        ChunkPos[] rings;
        synchronized (w.strongholds) {
            if (w.strongholds[0] == null) {
                List<ChunkPos> all = new ArrayList<>();
                for (Holder<StructureSet> set : w.structures.possibleStructureSets()) {
                    if (set.value().placement() instanceof ConcentricRingsStructurePlacement p) {
                        List<ChunkPos> l = w.structures.getRingPositionsFor(p);
                        if (l != null) {
                            all.addAll(l);
                        }
                    }
                }
                w.strongholds[0] = all.toArray(new ChunkPos[0]);
            }
            rings = w.strongholds[0];
        }
        for (ChunkPos p : rings) {
            if (s.contains(p.x, p.z, CLEAR + 2)) {
                return true;
            }
        }
        return false;
    }

    /**
     * The ground for a citadel at chunk cx, cz: the median of 7 x 7 samples of the terrain under it. Null (unless forced)
     * where more than a few samples are under water or in an ocean or river, the median is below the sea or high in the
     * mountains, or the middle two thirds of the samples spread over more than 24 blocks.
     */
    private static Integer survey(World w, int cx, int cz, boolean forced) {
        int n = 7;
        int[] h = new int[n * n];
        int wet = 0;
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                int x = cx * 16 + 40 + i * (SIZE * 16 - 80) / (n - 1);
                int z = cz * 16 + 40 + j * (SIZE * 16 - 80) / (n - 1);
                int floor = w.generator.getBaseHeight(x, z, Heightmap.Types.OCEAN_FLOOR_WG, w.height, w.random);
                int surface = w.generator.getBaseHeight(x, z, Heightmap.Types.WORLD_SURFACE_WG, w.height, w.random);
                h[i * n + j] = floor - 1;
                Holder<Biome> biome = w.generator.getBiomeSource().getNoiseBiome(QuartPos.fromBlock(x), QuartPos.fromBlock(floor),
                    QuartPos.fromBlock(z), w.random.sampler());
                if (surface - floor > 1 || biome.is(BiomeTags.IS_OCEAN) || biome.is(BiomeTags.IS_RIVER)) {
                    wet++;
                }
            }
        }
        Arrays.sort(h);
        int median = h[h.length / 2];
        int ground = Math.max(w.seaLevel, median);
        ground = Math.min(ground, w.height.getMaxBuildHeight() - 16 * CitadelData.SECTIONS + CitadelData.GROUND - 8);
        if (forced) {
            return ground;
        }
        int lo = h[h.length / 6], hi = h[h.length * 5 / 6];
        if (wet > 5 || median < w.seaLevel - 1 || median > 118 || hi - lo > 24) {
            return null;
        }
        return ground;
    }

    /** The operators' citadels of a world. */
    public static final class Store extends SavedData {
        static final Factory<Store> FACTORY = new Factory<>(Store::new, Store::load, null);
        final List<Site> sites = new ArrayList<>();

        static Store load(CompoundTag tag, HolderLookup.Provider registries) {
            Store s = new Store();
            ListTag list = tag.getList("Sites", Tag.TAG_COMPOUND);
            for (int i = 0; i < list.size(); i++) {
                CompoundTag t = list.getCompound(i);
                s.sites.add(new Site(t.getInt("ChunkX"), t.getInt("ChunkZ"), t.getInt("Ground"), true));
            }
            return s;
        }

        @Override
        public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
            ListTag list = new ListTag();
            for (Site s : sites) {
                CompoundTag t = new CompoundTag();
                t.putInt("ChunkX", s.chunkX());
                t.putInt("ChunkZ", s.chunkZ());
                t.putInt("Ground", s.ground());
                list.add(t);
            }
            tag.put("Sites", list);
            return tag;
        }
    }
}
