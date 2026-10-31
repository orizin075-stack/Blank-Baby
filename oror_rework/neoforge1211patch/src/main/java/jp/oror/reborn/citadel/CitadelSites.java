package jp.oror.reborn.citadel;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
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
 * Where the Grand Citadel stands in a world: the kingdom's capital, one to a world, its centre 800 to 960 blocks from the
 * world's spawn (along a side of the kingdom, so the spawn stays outside its walls) where the land under the whole
 * 1,280-block kingdom is driest and most level (sampled from the terrain noise, so before anything is generated), never
 * where a chunk has been generated already (an old world gets its capital on new land) and away from every stronghold.
 * The choice is made once, when the world is first loaded with this version, and kept with the world (oror_citadels);
 * every chunk of the kingdom is the Royal Capital biome (oror_supreme_bosses:royal_capital). Operators can add more with
 * /oror citadel place. The 045 preview save's citadel at its origin is that world's capital.
 */
public final class CitadelSites {
    public static final int SIZE = CitadelData.CHUNKS;
    /** The capital's centre from the spawn: at least NEAR along one axis (the spawn outside the kingdom and its apron), at most FAR in all. */
    public static final int NEAR = 780, FAR = 960;
    /** Chunks of graded land around the kingdom, between its ground and the natural terrain. */
    public static final int APRON = 2;
    /** Chunks around the kingdom where no other structure starts. */
    public static final int CLEAR = 6;
    private static final org.slf4j.Logger LOG = org.slf4j.LoggerFactory.getLogger("OROR Citadel");

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
                         ChunkGeneratorStructureState structures, Site capital, List<Site> forced, ChunkPos[][] strongholds) {
    }

    private static volatile World world;
    /** The 045 preview save's citadel, built at the origin on y 64 (that world has the save's build_manifest.json). */
    private static volatile Site preview;

    private CitadelSites() {
    }

    /**
     * Called when the overworld is created, before its first chunk is generated: the world's capital, chosen now if the
     * world has none yet. A new world's spawn is not set yet: it is taken where the game will look for it (the climate's
     * spawn point), and checked once the server has started (spawnCheck).
     */
    public static void bind(ServerLevel level) {
        java.nio.file.Path root = level.getServer().getWorldPath(net.minecraft.world.level.storage.LevelResource.ROOT);
        preview = java.nio.file.Files.isRegularFile(root.resolve("build_manifest.json"))
            ? new Site(-CitadelData.HALF, -CitadelData.HALF, CitadelData.GROUND, true) : null;
        Store store = level.getDataStorage().computeIfAbsent(Store.FACTORY, "oror_citadels");
        World w = new World(level.getChunkSource().getGenerator(), level.getChunkSource().randomState(), level.getSeed(), level,
            level.getSeaLevel(), level.getChunkSource().getGeneratorState(), null, new CopyOnWriteArrayList<>(store.sites), new ChunkPos[1][]);
        Site capital = preview != null ? preview : store.capital;
        if (capital == null) {
            boolean initialized = level.getLevelData() instanceof net.minecraft.world.level.storage.ServerLevelData d && d.isInitialized();
            BlockPos spawn = initialized ? level.getSharedSpawnPos() : w.random.sampler().findSpawnPosition();
            long t0 = System.nanoTime();
            capital = chooseCapital(w, spawn, root.resolve("region"));
            if (capital != null) {
                store.capital = capital;
                store.setDirty();
            }
            LOG.info("Royal capital {} for spawn {} ({} ms)", capital == null ? "none" : capital.center(), spawn, (System.nanoTime() - t0) / 1000000);
        }
        world = new World(w.generator, w.random, w.seed, w.height, w.seaLevel, w.structures, capital, w.forced, w.strongholds);
    }

    /**
     * Once the server has started: if the spawn the game settled on is inside the kingdom or more than a thousand
     * blocks from its centre, the spawn moves to the road outside the kingdom's gate facing where it was.
     */
    public static void spawnCheck(ServerLevel level) {
        World w = world;
        if (w == null || w.capital == null || w.capital == preview) {
            return;
        }
        BlockPos spawn = level.getSharedSpawnPos();
        BlockPos c = w.capital.center();
        int dx = spawn.getX() - c.getX(), dz = spawn.getZ() - c.getZ();
        double d = Math.sqrt((double) dx * dx + (double) dz * dz);
        int half = SIZE * 8 + (APRON + 1) * 16;
        if (d <= 1000 && Math.max(Math.abs(dx), Math.abs(dz)) >= half) {
            return;
        }
        int gx = c.getX(), gz = c.getZ();
        if (Math.abs(dx) >= Math.abs(dz)) {
            gx += Integer.signum(dx == 0 ? 1 : dx) * half;
        } else {
            gz += Integer.signum(dz) * half;
        }
        int gy = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, gx, gz);
        level.setDefaultSpawnPos(new BlockPos(gx, gy, gz), 0F);
        LOG.info("World spawn moved from {} to the capital's gate {} {} {}", spawn, gx, gy, gz);
    }

    /** The capital: of the places 800 to 960 blocks from the spawn along a side of the kingdom, the best land; never on generated chunks. */
    private static Site chooseCapital(World w, BlockPos spawn, java.nio.file.Path regions) {
        // a coarse look at every candidate (4 x 4 samples of the ground's height and biome), then the full survey of the best eight
        List<double[]> coarse = new ArrayList<>();
        for (int r = 820; r <= FAR; r += 70) {
            for (int step = 0; step < 48; step++) {
                double a = step * Math.PI * 2 / 48;
                int x = spawn.getX() + (int) Math.round(Math.cos(a) * r), z = spawn.getZ() + (int) Math.round(Math.sin(a) * r);
                if (Math.max(Math.abs(x - spawn.getX()), Math.abs(z - spawn.getZ())) < NEAR) {
                    continue;
                }
                Site probe = new Site((x >> 4) - CitadelData.HALF, (z >> 4) - CitadelData.HALF, 0, false);
                if (nearStronghold(w, probe) || generated(regions, probe)) {
                    continue;
                }
                coarse.add(new double[]{glance(w, probe.chunkX(), probe.chunkZ()), probe.chunkX(), probe.chunkZ()});
            }
        }
        coarse.sort((p, q) -> Double.compare(p[0], q[0]));
        Site best = null, fallback = null;
        double bestScore = Double.MAX_VALUE, fallbackScore = Double.MAX_VALUE;
        for (double[] c : coarse.subList(0, Math.min(8, coarse.size()))) {
            Site probe = new Site((int) c[1], (int) c[2], 0, false);
            double[] score = new double[1];
            Integer ground = survey(w, probe.chunkX(), probe.chunkZ(), false, score);
            if (ground != null && score[0] < bestScore) {
                bestScore = score[0];
                best = new Site(probe.chunkX(), probe.chunkZ(), ground, false);
            }
            if (score[0] < fallbackScore) {
                // the least bad place, kept in case no place is good: its ground follows the land
                fallbackScore = score[0];
                fallback = new Site(probe.chunkX(), probe.chunkZ(), survey(w, probe.chunkX(), probe.chunkZ(), true), false);
            }
        }
        return best != null ? best : fallback;
    }

    /** A quick score of a site's land (lower is better): the spread of 4 x 4 heights, water and oceans counted heavily. */
    private static double glance(World w, int cx, int cz) {
        int n = 4;
        int[] h = new int[n * n];
        int wet = 0;
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                int x = cx * 16 + 60 + i * (SIZE * 16 - 120) / (n - 1);
                int z = cz * 16 + 60 + j * (SIZE * 16 - 120) / (n - 1);
                int floor = w.generator.getBaseHeight(x, z, Heightmap.Types.OCEAN_FLOOR_WG, w.height, w.random);
                h[i * n + j] = floor;
                Holder<Biome> biome = w.generator.getBiomeSource().getNoiseBiome(QuartPos.fromBlock(x), QuartPos.fromBlock(floor),
                    QuartPos.fromBlock(z), w.random.sampler());
                if (floor < w.seaLevel - 1 || biome.is(BiomeTags.IS_OCEAN) || biome.is(BiomeTags.IS_RIVER)) {
                    wet++;
                }
            }
        }
        Arrays.sort(h);
        return (h[h.length - 2] - h[1]) + wet * 12 + Math.max(0, h[h.length / 2] - 100) * 2;
    }

    /** True if any chunk of the site or its apron is in the world's region files already. */
    private static boolean generated(java.nio.file.Path regions, Site s) {
        int x0 = s.chunkX() - APRON, z0 = s.chunkZ() - APRON, x1 = s.chunkX() + SIZE + APRON, z1 = s.chunkZ() + SIZE + APRON;
        for (int rx = Math.floorDiv(x0, 32); rx <= Math.floorDiv(x1 - 1, 32); rx++) {
            for (int rz = Math.floorDiv(z0, 32); rz <= Math.floorDiv(z1 - 1, 32); rz++) {
                java.nio.file.Path f = regions.resolve("r." + rx + "." + rz + ".mca");
                if (!java.nio.file.Files.isRegularFile(f)) {
                    continue;
                }
                try (java.io.InputStream in = java.nio.file.Files.newInputStream(f)) {
                    byte[] header = in.readNBytes(4096);
                    for (int i = 0; i + 3 < header.length; i += 4) {
                        int cx = rx * 32 + (i / 4) % 32, cz = rz * 32 + (i / 4) / 32;
                        boolean present = (header[i] | header[i + 1] | header[i + 2] | header[i + 3]) != 0;
                        if (present && cx >= x0 && cx < x1 && cz >= z0 && cz < z1) {
                            return true;
                        }
                    }
                } catch (java.io.IOException e) {
                    return true;
                }
            }
        }
        return false;
    }

    public static void unbind() {
        world = null;
        preview = null;
    }

    /** The citadel whose people stand in chunk cx, cz: the preview save's, or a generated or placed one. */
    public static Site garrisoned(ChunkGenerator generator, int cx, int cz) {
        Site p = preview;
        if (p != null && p.contains(cx, cz, 0)) {
            return p;
        }
        return at(generator, cx, cz, 0);
    }

    public static Site preview() {
        return preview;
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
        if (w.capital != null && w.capital != preview && w.capital.contains(cx, cz, margin)) {
            return w.capital;
        }
        for (Site s : w.forced) {
            if (s.contains(cx, cz, margin)) {
                return s;
            }
        }
        return null;
    }

    /** The world's capital (the preview save's citadel in that save), or null. */
    public static Site capital() {
        World w = world;
        return w == null ? preview : w.capital;
    }

    /** True where other structures must not start: within CLEAR chunks of a citadel. */
    public static boolean excludesStructures(ChunkGenerator generator, ChunkPos pos) {
        return at(generator, pos.x, pos.z, CLEAR) != null;
    }

    /** The nearest citadel to pos: the capital or an operator's. */
    public static Site nearest(BlockPos pos, int radius) {
        World w = world;
        if (w == null) {
            return preview;
        }
        List<Site> candidates = new ArrayList<>(w.forced);
        if (w.capital != null) {
            candidates.add(w.capital);
        }
        Site best = null;
        double bestD = Double.MAX_VALUE;
        for (Site s : candidates) {
            double d = s.center().distSqr(pos);
            if (d < bestD) {
                bestD = d;
                best = s;
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
        if (w.capital != null && overlaps(site, w.capital)) {
            return null;
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
        return survey(w, cx, cz, forced, new double[1]);
    }

    /** As survey, also giving score[0]: lower is better land (spread of the heights, and water counted heavily). */
    private static Integer survey(World w, int cx, int cz, boolean forced, double[] score) {
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
        int lo = h[h.length / 6], hi = h[h.length * 5 / 6];
        score[0] = (hi - lo) + wet * 12 + Math.max(0, median - 100) * 2;
        if (forced) {
            return ground;
        }
        if (wet > 5 || median < w.seaLevel - 1 || median > 118 || hi - lo > 24) {
            return null;
        }
        return ground;
    }

    /** A world's capital and its operators' citadels. */
    public static final class Store extends SavedData {
        static final Factory<Store> FACTORY = new Factory<>(Store::new, Store::load, null);
        final List<Site> sites = new ArrayList<>();
        Site capital;

        static Store load(CompoundTag tag, HolderLookup.Provider registries) {
            Store s = new Store();
            if (tag.contains("Capital", Tag.TAG_COMPOUND)) {
                CompoundTag c = tag.getCompound("Capital");
                s.capital = new Site(c.getInt("ChunkX"), c.getInt("ChunkZ"), c.getInt("Ground"), false);
            }
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
            if (capital != null) {
                CompoundTag c = new CompoundTag();
                c.putInt("ChunkX", capital.chunkX());
                c.putInt("ChunkZ", capital.chunkZ());
                c.putInt("Ground", capital.ground());
                tag.put("Capital", c);
            }
            return tag;
        }
    }
}
