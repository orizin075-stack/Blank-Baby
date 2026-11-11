package jp.oror.reborn.citadel;

import java.io.DataInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.zip.InflaterInputStream;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.vehicle.RoyalPilots;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.LongArrayTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.chunk.PalettedContainer;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.level.ChunkEvent;
import net.neoforged.neoforge.event.server.ServerStoppedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * A capital built by an earlier version is brought up to this one's (049): the castle's mended roofs, the airfields,
 * hangars and helipads inside the walls, their supply, the town's houses. Generation only ever built new chunks from the
 * template, so a world's capital kept whatever version first built it.
 * <p>
 * update.bin (tools/citadel/patch.py) marks each block where any template the mod has shipped differs from this one's;
 * when a chunk of a capital (a generated one, an operator's, or the preview save's) loads, those blocks, and only those,
 * are set to this template's, a few thousand a tick. What players built or broke elsewhere stays as it is, and where the
 * world already has the new block (a chunk this version generated) nothing changes. The kingdom's own chests and barrels
 * of the old templates are emptied before they are replaced, their stock would spill over the streets; a player's chest
 * where the kingdom's blocks change drops its items as when broken. The new blocks' chests and stations get the
 * template's contents.
 * <p>
 * The kingdom's machines follow their posts: a vehicle left by an earlier version at a post that is no longer there (the
 * old runways, hangars and helipads outside the walls) is retired with its crew, and each vehicle post of an updated chunk
 * that has no vehicle at it gets one, crewed as the garrison would (CitadelGarrison). Chunks whose people have not come
 * yet are left to the garrison.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class CitadelUpdate {
    /** The template's revision: worlds updated to an earlier one are updated again. */
    public static final int REVISION = 51;
    private static final Logger LOG = LoggerFactory.getLogger("OROR Citadel");
    private static final String FILE = "/data/oror_supreme_bosses/citadel/v12/update.bin";
    /** Blocks looked at a tick. */
    private static final int BUDGET = 4000;
    private static final BlockState AIR = Blocks.AIR.defaultBlockState(), DIRT = Blocks.DIRT.defaultBlockState();

    /** One chunk's marked blocks: per section (sy) the positions x | z << 4 | y << 8; the kingdom's containers to empty (xz | save y << 8). */
    record Patch(int[] sy, int[][] positions, Set<Integer> containers, int size) {
    }

    private static final class Job {
        final long key;
        final int cx, cz, sx, sz;
        final CitadelSites.Site site;
        final Patch patch;
        int section, index, changed;
        /** (058) Every block of the chunk, by the operator's order (a rebuild), not only the marked ones. */
        boolean whole;
        final long started = System.nanoTime();

        Job(long key, int cx, int cz, CitadelSites.Site site, Patch patch) {
            this.key = key;
            this.cx = cx;
            this.cz = cz;
            this.site = site;
            this.patch = patch;
            this.sx = cx - site.chunkX() - CitadelData.HALF;
            this.sz = cz - site.chunkZ() - CitadelData.HALF;
        }
    }

    private static volatile Map<Long, Patch> patches;
    private static final Deque<Job> QUEUE = new ArrayDeque<>();
    private static final Set<Long> QUEUED = new HashSet<>();
    private static final List<Object[]> MUSTER = new ArrayList<>();
    private static final List<Entity> RETIRE = new ArrayList<>();
    public static int chunksUpdated, blocksChanged, containersEmptied, vehiclesRetired, vehiclesMustered, chunksRebuilt;
    private static Test test;

    private CitadelUpdate() {
    }

    // ------------------------------------------------------------------------------------------------------------ data

    static Map<Long, Patch> patches() {
        Map<Long, Patch> p = patches;
        if (p == null) {
            p = new HashMap<>();
            try (InputStream raw = CitadelUpdate.class.getResourceAsStream(FILE)) {
                if (raw != null) {
                    DataInputStream in = new DataInputStream(new InflaterInputStream(raw));
                    byte[] magic = new byte[4];
                    in.readFully(magic);
                    if (!new String(magic, java.nio.charset.StandardCharsets.US_ASCII).equals("OCU1")) {
                        throw new IOException("unknown format");
                    }
                    int revision = in.readInt(), chunks = in.readInt();
                    for (int c = 0; c < chunks; c++) {
                        int sx = in.readByte(), sz = in.readByte(), sections = in.readByte();
                        Set<Integer> containers = new HashSet<>();
                        int nc = in.readShort();
                        for (int i = 0; i < nc; i++) {
                            int xz = in.readUnsignedByte(), y = in.readShort();
                            containers.add(xz | y << 8);
                        }
                        int[] sy = new int[sections];
                        int[][] positions = new int[sections][];
                        int size = 0;
                        for (int s = 0; s < sections; s++) {
                            sy[s] = in.readByte();
                            int kind = in.readByte();
                            if (kind == 0) {
                                int n = in.readShort();
                                positions[s] = new int[n];
                                for (int i = 0; i < n; i++) {
                                    positions[s][i] = in.readShort() & 0xFFFF;
                                }
                            } else {
                                byte[] mask = new byte[512];
                                in.readFully(mask);
                                int n = 0;
                                for (byte b : mask) {
                                    n += Integer.bitCount(b & 0xFF);
                                }
                                positions[s] = new int[n];
                                int k = 0;
                                for (int i = 0; i < 4096; i++) {
                                    if ((mask[i >> 3] >> (i & 7) & 1) != 0) {
                                        positions[s][k++] = i;
                                    }
                                }
                            }
                            size += positions[s].length;
                        }
                        p.put(ChunkPos.asLong(sx, sz), new Patch(sy, positions, containers, size));
                    }
                    LOG.info("Citadel update {}: {} chunks", revision, p.size());
                }
            } catch (IOException | RuntimeException e) {
                LOG.error("Citadel update table could not be read", e);
            }
            patches = p;
        }
        return p;
    }

    // ---------------------------------------------------------------------------------------------------------- events

    @SubscribeEvent
    public static void load(ChunkEvent.Load e) {
        if (!(e.getLevel() instanceof ServerLevel level) || !level.dimension().equals(Level.OVERWORLD) || !(e.getChunk() instanceof LevelChunk chunk)) {
            return;
        }
        ChunkPos pos = chunk.getPos();
        CitadelSites.Site site = CitadelSites.garrisoned(level.getChunkSource().getGenerator(), pos.x, pos.z);
        if (site == null) {
            return;
        }
        int sx = pos.x - site.chunkX() - CitadelData.HALF, sz = pos.z - site.chunkZ() - CitadelData.HALF;
        consider(level, site, pos.x, pos.z, sx, sz);
    }

    /**
     * (058) What a loaded chunk of a capital is due: nothing unless the world's operator asked. The update used to run
     * by itself on every load, and on a capital another build of the mod had made or mended it wrote this template's
     * blocks over part of it (the user's capital "broken from the middle", its containers emptied).
     */
    private static void consider(ServerLevel level, CitadelSites.Site site, int cx, int cz, int sx, int sz) {
        Ledger ledger = Ledger.of(level);
        long key = CitadelGarrison.key(site, sx, sz);
        if (ledger.rebuild.contains(key)) {
            CitadelData.Chunk data = CitadelData.chunk(sx, sz);
            boolean any = false;
            if (data != null) {
                for (Object section : data.sections()) {
                    any |= section != null;
                }
            }
            if (any) {
                Job j = new Job(key, cx, cz, site, whole(data));
                j.whole = true;
                enqueue(j);
            } else {
                // nothing of the template here (the natural land about the capital): nothing to rebuild
                ledger.rebuild.remove(key);
                ledger.setDirty();
            }
            return;
        }
        if (!ledger.auto) {
            return;
        }
        Patch patch = patches().get(ChunkPos.asLong(sx, sz));
        if (patch == null) {
            return;
        }
        enqueue(new Job(key, cx, cz, site, patch));
    }

    private static final int[] ALL = new int[4096];

    static {
        for (int i = 0; i < 4096; i++) {
            ALL[i] = i;
        }
    }

    /** Every position of every section of a chunk of the template. */
    private static Patch whole(CitadelData.Chunk data) {
        int n = data.sections().length;
        int[] sy = new int[n];
        int[][] positions = new int[n][];
        for (int i = 0; i < n; i++) {
            sy[i] = i;
            positions[i] = ALL;
        }
        return new Patch(sy, positions, Set.of(), n * 4096);
    }

    /** The loaded chunks about the players are looked at again (after the operator's order). */
    private static int reconsider(ServerLevel level) {
        int n = 0;
        for (net.minecraft.server.level.ServerPlayer pl : level.players()) {
            ChunkPos c = pl.chunkPosition();
            for (int dx = -12; dx <= 12; dx++) {
                for (int dz = -12; dz <= 12; dz++) {
                    if (level.getChunkSource().getChunkNow(c.x + dx, c.z + dz) == null) {
                        continue;
                    }
                    CitadelSites.Site site = CitadelSites.garrisoned(level.getChunkSource().getGenerator(), c.x + dx, c.z + dz);
                    if (site != null) {
                        consider(level, site, c.x + dx, c.z + dz, c.x + dx - site.chunkX() - CitadelData.HALF, c.z + dz - site.chunkZ() - CitadelData.HALF);
                        n++;
                    }
                }
            }
        }
        return n;
    }

    private static void enqueue(Job j) {
        synchronized (QUEUE) {
            if (QUEUED.add(j.key)) {
                QUEUE.add(j);
            }
        }
    }

    /** A vehicle an earlier version left: whether its post is still there is decided on the server thread (tick). */
    @SubscribeEvent
    public static void joined(EntityJoinLevelEvent e) {
        if (e.getLevel().isClientSide() || !e.loadedFromDisk() || !e.getEntity().getTags().contains(RoyalPilots.CREWED)) {
            return;
        }
        if (e.getEntity().getPersistentData().getCompound(RoyalPilots.KEY).getInt("Rev") >= REVISION) {
            return;
        }
        synchronized (RETIRE) {
            RETIRE.add(e.getEntity());
        }
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        ServerLevel level = e.getServer().overworld();
        retire(level);
        long now = level.getGameTime();
        for (Iterator<Object[]> it = MUSTER.iterator(); it.hasNext(); ) {
            Object[] m = it.next();
            if ((long) m[0] > now) {
                continue;
            }
            it.remove();
            Job j = (Job) m[1];
            if (level.getChunkSource().getChunkNow(j.cx, j.cz) != null) {
                muster(level, j.site, j.sx, j.sz);
            }
        }
        int budget = BUDGET;
        while (budget > 0) {
            Job j;
            synchronized (QUEUE) {
                j = QUEUE.peek();
            }
            if (j == null) {
                break;
            }
            Ledger ledger = Ledger.of(level);
            boolean loaded = level.getChunkSource().getChunkNow(j.cx, j.cz) != null;
            if ((ledger.done.contains(j.key) && !j.whole) || !loaded) {
                drop(j);
                continue;
            }
            budget -= step(level, j, budget);
            if (j.section >= j.patch.sy().length) {
                drop(j);
                ledger.done.add(j.key);
                if (j.whole) {
                    ledger.rebuild.remove(j.key);
                    chunksRebuilt++;
                }
                ledger.setDirty();
                chunksUpdated++;
                blocksChanged += j.changed;
                if (j.changed > 0 && (chunksUpdated % 50 == 1 || test != null)) {
                    LOG.info("CITADEL-UPDATE-CHUNK {\"chunk\":[{},{}],\"marked\":{},\"changed\":{},\"ms\":{},\"chunks\":{},\"blocks\":{}}", j.sx, j.sz,
                        j.patch.size(), j.changed, (System.nanoTime() - j.started) / 1000000, chunksUpdated, blocksChanged);
                }
                // the posts of a chunk whose people came under an earlier version: its vehicles, once its entities are in
                if (CitadelGarrison.Ledger.of(level).done.contains(j.key) && !CitadelData.posts(j.sx, j.sz).isEmpty()) {
                    MUSTER.add(new Object[]{now + 100, j});
                }
            }
        }
        if (test != null) {
            test.tick(level);
        }
    }

    private static void drop(Job j) {
        synchronized (QUEUE) {
            QUEUE.remove(j);
            QUEUED.remove(j.key);
        }
    }

    @SubscribeEvent
    public static void stopped(ServerStoppedEvent e) {
        synchronized (QUEUE) {
            QUEUE.clear();
            QUEUED.clear();
        }
        synchronized (RETIRE) {
            RETIRE.clear();
        }
        MUSTER.clear();
        test = null;
    }

    // ---------------------------------------------------------------------------------------------------------- blocks

    /** Up to budget marked blocks of the job's chunk set to the template's; the number looked at. */
    private static int step(ServerLevel level, Job j, int budget) {
        CitadelData.Chunk data = CitadelData.chunk(j.sx, j.sz);
        if (data == null) {
            j.section = j.patch.sy().length;
            return 1;
        }
        Map<Integer, CompoundTag> bes = new HashMap<>();
        for (CompoundTag t : data.blockEntities()) {
            bes.put((t.getInt("x") & 15) | (t.getInt("z") & 15) << 4 | t.getInt("y") << 8, t);
        }
        int looked = 0;
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        while (j.section < j.patch.sy().length && looked < budget) {
            int sy = j.patch.sy()[j.section];
            int[] positions = j.patch.positions()[j.section];
            for (; j.index < positions.length && looked < budget; j.index++, looked++) {
                if (apply(level, j, data, bes, sy, positions[j.index], p)) {
                    j.changed++;
                }
            }
            if (j.index >= positions.length) {
                j.section++;
                j.index = 0;
            }
        }
        return Math.max(1, looked);
    }

    /** What the template has at a marked position, as generation builds it; null where the natural ground stays. */
    static BlockState expected(CitadelSites.Site site, CitadelData.Chunk data, int sy, int i) {
        int x = i & 15, z = i >> 4 & 15, yl = i >> 8;
        int wy = sy * 16 + yl + site.dy();
        PalettedContainer<BlockState> section = sy < data.sections().length ? data.sections()[sy] : null;
        BlockState st = section == null ? (wy > site.ground() ? AIR : DIRT) : section.get(x, yl, z);
        if (st.is(Blocks.DIRT) || st.is(Blocks.BEDROCK)) {
            // the save's dirt: topsoil under the kingdom's ground, the natural rock deeper down
            return wy >= site.ground() - 3 ? DIRT : null;
        }
        return st;
    }

    static BlockPos world(Job j, int sy, int i) {
        return new BlockPos(j.cx * 16 + (i & 15), sy * 16 + (i >> 8) + j.site.dy(), j.cz * 16 + (i >> 4 & 15));
    }

    private static boolean apply(ServerLevel level, Job j, CitadelData.Chunk data, Map<Integer, CompoundTag> bes, int sy, int i,
                                 BlockPos.MutableBlockPos p) {
        BlockState st = expected(j.site, data, sy, i);
        int x = i & 15, z = i >> 4 & 15, saveY = sy * 16 + (i >> 8);
        int wy = saveY + j.site.dy();
        if (st == null || wy <= level.getMinBuildHeight() || wy >= level.getMaxBuildHeight()) {
            return false;
        }
        p.set(j.cx * 16 + x, wy, j.cz * 16 + z);
        BlockState here = level.getBlockState(p);
        if (here == st) {
            return false;
        }
        if (j.patch.containers().contains(x | z << 4 | saveY << 8) && level.getBlockEntity(p) instanceof Container c) {
            c.clearContent();
            containersEmptied++;
        }
        level.setBlock(p, st, Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
        if (st.hasBlockEntity()) {
            CompoundTag t = bes.get(x | z << 4 | saveY << 8);
            BlockEntity be = level.getBlockEntity(p);
            if (t != null && be != null) {
                CompoundTag c = t.copy();
                c.putInt("x", p.getX());
                c.putInt("y", p.getY());
                c.putInt("z", p.getZ());
                try {
                    be.loadWithComponents(c, level.registryAccess());
                    be.setChanged();
                } catch (RuntimeException ex) {
                    LOG.warn("Citadel update: block entity at {} not loaded: {}", p, ex.toString());
                }
            }
        }
        return true;
    }

    // -------------------------------------------------------------------------------------------------------- vehicles

    /** True where a vehicle post of this version stands within a few blocks of home (a turret's post was lowered to its floor in 049). */
    static boolean postAt(CitadelSites.Site site, BlockPos home) {
        int hx = home.getX() - site.offsetX(), hz = home.getZ() - site.offsetZ();
        for (int ox = -1; ox <= 1; ox++) {
            for (int oz = -1; oz <= 1; oz++) {
                for (CitadelData.Post post : CitadelData.posts((hx >> 4) + ox, (hz >> 4) + oz)) {
                    if (post.vehicle().isEmpty()) {
                        continue;
                    }
                    BlockPos at = site.toWorld(post.x(), post.y(), post.z());
                    double dx = at.getX() - home.getX(), dz = at.getZ() - home.getZ();
                    if (dx * dx + dz * dz <= 9 && Math.abs(at.getY() - home.getY()) <= 4) {
                        return true;
                    }
                }
            }
        }
        return false;
    }

    /** A vehicle from before this revision whose home is in a capital where this version has no vehicle post. */
    static boolean stale(Entity v) {
        CompoundTag p = v.getPersistentData().getCompound(RoyalPilots.KEY);
        if (!p.contains("Home")) {
            return false;
        }
        BlockPos home = BlockPos.of(p.getLong("Home"));
        CitadelSites.Site site = CitadelSites.nearest(home, CitadelData.HALF * 16 + 32);
        if (site == null) {
            return false;
        }
        BlockPos c = site.center();
        if (Math.abs(home.getX() - c.getX()) > CitadelData.HALF * 16 || Math.abs(home.getZ() - c.getZ()) > CitadelData.HALF * 16) {
            return false;
        }
        for (Entity rider : v.getPassengers()) {
            if (rider instanceof Player) {
                return false;
            }
        }
        return !postAt(site, home);
    }

    private static void retire(ServerLevel level) {
        List<Entity> batch;
        synchronized (RETIRE) {
            if (RETIRE.isEmpty()) {
                return;
            }
            batch = new ArrayList<>(RETIRE);
            RETIRE.clear();
        }
        for (Entity v : batch) {
            if (!v.isAlive() || v.level() != level) {
                continue;
            }
            if (stale(v)) {
                LOG.info("CITADEL-UPDATE-RETIRE {\"vehicle\":\"{}\",\"home\":\"{}\"}", net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.getKey(v.getType()),
                    BlockPos.of(v.getPersistentData().getCompound(RoyalPilots.KEY).getLong("Home")).toShortString());
                for (Entity rider : List.copyOf(v.getPassengers())) {
                    if (!(rider instanceof Player)) {
                        rider.discard();
                    }
                }
                v.discard();
                vehiclesRetired++;
            } else {
                CompoundTag p = v.getPersistentData().getCompound(RoyalPilots.KEY);
                p.putInt("Rev", REVISION);
                v.getPersistentData().put(RoyalPilots.KEY, p);
            }
        }
    }

    /** Each vehicle post of the chunk without its vehicle (nor a soldier about to bring it out) gets one. */
    static int muster(ServerLevel level, CitadelSites.Site site, int sx, int sz) {
        List<CitadelData.Post> posts = new ArrayList<>();
        for (CitadelData.Post post : CitadelData.posts(sx, sz)) {
            if (!post.vehicle().isEmpty()) {
                posts.add(post);
            }
        }
        if (posts.isEmpty()) {
            return 0;
        }
        List<BlockPos> homes = new ArrayList<>();
        BlockPos first = site.toWorld(posts.get(0).x(), posts.get(0).y(), posts.get(0).z());
        // the kingdom's vehicles and crews about here (a tank on patrol is not far from its post while its chunk is loaded)
        for (Entity en : level.getEntities((Entity) null, new AABB(first).inflate(160, 96, 160), x -> true)) {
            if (en.getTags().contains(RoyalPilots.CREWED)) {
                homes.add(BlockPos.of(en.getPersistentData().getCompound(RoyalPilots.KEY).getLong("Home")));
            } else if (en instanceof RoyalMob m && m.getPersistentData().contains("OrorMotor")) {
                homes.add(m.blockPosition());
            }
        }
        int n = 0;
        for (CitadelData.Post post : posts) {
            BlockPos at = site.toWorld(post.x(), post.y(), post.z());
            boolean manned = false;
            for (BlockPos h : homes) {
                double dx = h.getX() - at.getX(), dz = h.getZ() - at.getZ();
                if (dx * dx + dz * dz <= 9 && Math.abs(h.getY() - at.getY()) <= 4) {
                    manned = true;
                    break;
                }
            }
            if (!manned) {
                CitadelGarrison.spawn(level, site, post);
                homes.add(at);
                vehiclesMustered++;
                n++;
            }
        }
        if (n > 0) {
            LOG.info("CITADEL-UPDATE-MUSTER {\"chunk\":[{},{}],\"posts\":{},\"brought\":{}}", sx, sz, posts.size(), n);
        }
        return n;
    }

    // --------------------------------------------------------------------------------------------------------- command

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("citadel").requires(s -> s.hasPermission(2))
            .then(Commands.literal("update").executes(c -> status(c.getSource()))
                .then(Commands.literal("on").executes(c -> auto(c.getSource(), true)))
                .then(Commands.literal("off").executes(c -> auto(c.getSource(), false)))
                .then(Commands.literal("test").executes(c -> startTest(c.getSource()))))
            .then(Commands.literal("rebuild").executes(c -> rebuild(c.getSource(), false))
                .then(Commands.literal("confirm").executes(c -> rebuild(c.getSource(), true)))
                .then(Commands.literal("cancel").executes(c -> cancelRebuild(c.getSource()))))));
    }

    private static int auto(CommandSourceStack src, boolean on) {
        ServerLevel level = src.getServer().overworld();
        Ledger ledger = Ledger.of(level);
        ledger.auto = on;
        ledger.setDirty();
        int n = on ? reconsider(level) : 0;
        src.sendSuccess(() -> Component.literal(on
            ? "王都の自動更新を入にしました。読み込まれた王都のチャンクから、この版の型と違う「印のある」ブロックだけを書き換えます（いま対象 " + n
                + " チャンク）。別の版で建てた・直した建物があると、部分的に上書きされることがあります。先にワールドのバックアップを取ってください。"
            : "王都の自動更新を切にしました（既定）。王都のブロックは、命令しない限り書き換えません。").withStyle(ChatFormatting.GOLD), true);
        return 1;
    }

    /**
     * (058) The whole capital the operator stands in, set to this version's template, chunk by chunk as each is loaded:
     * the way out for a capital broken across versions (halves of two templates side by side, buildings cut at chunk
     * borders). Everything in the capital's own volume goes back to the template: asked twice.
     */
    private static int rebuild(CommandSourceStack src, boolean confirmed) {
        ServerLevel level = src.getServer().overworld();
        BlockPos at = BlockPos.containing(src.getPosition());
        CitadelSites.Site site = CitadelSites.garrisoned(level.getChunkSource().getGenerator(), at.getX() >> 4, at.getZ() >> 4);
        if (site == null) {
            site = CitadelSites.capital();
        }
        if (site == null) {
            src.sendFailure(Component.literal("この世界に王都が見つかりません。"));
            return 0;
        }
        if (!confirmed) {
            src.sendSuccess(() -> Component.literal("王都を、この版の型どおりに建て直します。王都の範囲にあるブロックはすべて型のとおりに戻ります（あなたが王都の中に建てた物・壊した所も戻ります。"
                + "置き換わる場所の箱の中身は、その場に落ちます）。地下深くの自然の地面と、王都の外は変えません。ワールドのバックアップを取ってから、"
                + "/oror citadel rebuild confirm を実行してください。建て直しは、王都を歩いて読み込まれたチャンクから順に進みます。").withStyle(ChatFormatting.GOLD), false);
            return 1;
        }
        Ledger ledger = Ledger.of(level);
        int n = 0;
        for (int sx = -CitadelData.HALF; sx <= CitadelData.HALF; sx++) {
            for (int sz = -CitadelData.HALF; sz <= CitadelData.HALF; sz++) {
                // (which chunks the template has is known without reading them: they are read as each is rebuilt)
                if (CitadelData.inSave(sx, sz) && ledger.rebuild.add(CitadelGarrison.key(site, sx, sz))) {
                    n++;
                }
            }
        }
        ledger.setDirty();
        int loaded = reconsider(level);
        int total = n;
        LOG.info("CITADEL-REBUILD ordered: {} chunks ({} loaded now)", total, loaded);
        src.sendSuccess(() -> Component.literal("王都の建て直しを始めました：" + total + " チャンク。読み込まれた所から順に進みます（/oror citadel update で進み具合、"
            + "/oror citadel rebuild cancel で中止）。").withStyle(ChatFormatting.GOLD), true);
        return 1;
    }

    private static int cancelRebuild(CommandSourceStack src) {
        Ledger ledger = Ledger.of(src.getServer().overworld());
        int n = ledger.rebuild.size();
        ledger.rebuild.clear();
        ledger.setDirty();
        src.sendSuccess(() -> Component.literal("王都の建て直しを中止しました（残り " + n + " チャンクはそのまま）。").withStyle(ChatFormatting.GOLD), true);
        return 1;
    }

    private static int status(CommandSourceStack src) {
        ServerLevel level = src.getServer().overworld();
        Ledger ledger = Ledger.of(level);
        int queued;
        synchronized (QUEUE) {
            queued = QUEUE.size();
        }
        int total = patches().size();
        src.sendSuccess(() -> Component.literal("自動更新：" + (ledger.auto ? "入" : "切（/oror citadel update on で入）") + "。建て直し待ち：" + ledger.rebuild.size()
            + " チャンク（建て直し済み " + chunksRebuilt + "）。王都の更新（" + REVISION + "版）: 更新の要るチャンク " + total + " のうち " + ledger.done.size()
            + " を更新済み（待ち " + queued + "）。このセッションで " + blocksChanged + " ブロック、空にした王国の容器 " + containersEmptied
            + "、引き上げた車両 " + vehiclesRetired + "、新しい持ち場に出した車両 " + vehiclesMustered + "。残りは王都を歩くと読み込まれた所から更新されます。")
            .withStyle(ChatFormatting.GOLD), false);
        return 1;
    }

    // ------------------------------------------------------------------------------------------------------------ test

    public static volatile boolean testDone;

    /**
     * The CI check: a chunk of the capital is made stale (every marked block to stone, a stocked chest where the kingdom's
     * old container was), then updated as on load; every marked block must be the template's afterwards and the chest's
     * stock must not spill. A vehicle away from any post (from before this revision) must be stale, one at a post not;
     * an empty vehicle post must get its vehicle, once.
     */
    private static int startTest(CommandSourceStack src) {
        ServerLevel level = src.getServer().overworld();
        CitadelSites.Site site = CitadelSites.capital();
        if (site == null || patches().isEmpty()) {
            LOG.info("CITADEL-UPDATE {\"ok\":false,\"why\":\"{}\"}", site == null ? "no capital" : "no update table");
            testDone = true;
            return 0;
        }
        test = new Test(level, site);
        src.sendSuccess(() -> Component.literal("citadel update test started"), false);
        return 1;
    }

    private static final class Test {
        final CitadelSites.Site site;
        final long started;
        Job job;
        int spoiled, skipped;
        BlockPos chest;
        final List<ChunkPos> forced = new ArrayList<>();
        boolean staleOff, staleAtPost;
        int mustered = -1, musteredAgain = -1, expectMuster;
        String musterPost = "";

        Test(ServerLevel level, CitadelSites.Site site) {
            this.site = site;
            this.started = level.getGameTime();
            // the marked chunk with the most kingdom containers and blocks near the castle
            long best = 0;
            double bestScore = -1;
            for (Map.Entry<Long, Patch> en : patches().entrySet()) {
                int sx = ChunkPos.getX(en.getKey()), sz = ChunkPos.getZ(en.getKey());
                double score = en.getValue().size() + 500.0 * Math.min(4, en.getValue().containers().size()) - 20.0 * (Math.abs(sx) + Math.abs(sz));
                if (score > bestScore) {
                    bestScore = score;
                    best = en.getKey();
                }
            }
            int sx = ChunkPos.getX(best), sz = ChunkPos.getZ(best);
            int cx = site.chunkX() + CitadelData.HALF + sx, cz = site.chunkZ() + CitadelData.HALF + sz;
            force(level, cx, cz);
            level.getChunk(cx, cz);
            Patch patch = patches().get(best);
            job = new Job(CitadelGarrison.key(site, sx, sz), cx, cz, site, patch);
            CitadelData.Chunk data = CitadelData.chunk(sx, sz);
            // the stale chunk: every marked block that generation sets is made stone
            for (int s = 0; s < patch.sy().length; s++) {
                for (int i : patch.positions()[s]) {
                    BlockPos p = world(job, patch.sy()[s], i);
                    if (expected(site, data, patch.sy()[s], i) == null) {
                        skipped++;
                        continue;
                    }
                    level.setBlock(p, Blocks.STONE.defaultBlockState(), Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
                    spoiled++;
                }
            }
            // an old kingdom container, stocked, where the new template has something else
            for (int k : patch.containers()) {
                int x = k & 15, z = k >> 4 & 15, y = k >> 8;
                BlockState want = expected(site, data, y >> 4, x | z << 4 | (y & 15) << 8);
                if (want != null && !want.hasBlockEntity()) {
                    chest = new BlockPos(cx * 16 + x, y + site.dy(), cz * 16 + z);
                    level.setBlock(chest, Blocks.BARREL.defaultBlockState(), Block.UPDATE_CLIENTS);
                    if (level.getBlockEntity(chest) instanceof Container c) {
                        c.setItem(0, new ItemStack(Items.BREAD, 64));
                        c.setItem(1, new ItemStack(Items.IRON_INGOT, 64));
                    }
                    break;
                }
            }
            Ledger.of(level).done.remove(job.key);
            synchronized (QUEUE) {
                // the job the chunk's loading queued gives way to the test's own
                QUEUE.removeIf(q -> q.key == job.key);
                QUEUED.remove(job.key);
            }
            enqueue(job);
            vehicles(level, cx, cz);
            LOG.info("CITADEL-UPDATE-TEST {\"chunk\":[{},{}],\"marked\":{},\"spoiled\":{},\"natural\":{},\"chest\":{}}", sx, sz, patch.size(), spoiled,
                skipped, chest != null);
        }

        private void force(ServerLevel level, int cx, int cz) {
            if (level.setChunkForced(cx, cz, true)) {
                forced.add(new ChunkPos(cx, cz));
            }
        }

        private void vehicles(ServerLevel level, int cx, int cz) {
            if (!jp.oror.reborn.vehicle.Sbw.present()) {
                return;
            }
            // a tank of an earlier version left in the capital (in the test's chunk) where no post is
            BlockPos spot = null;
            for (int dx = 0; dx < 16 && spot == null; dx += 5) {
                for (int dz = 0; dz < 16 && spot == null; dz += 5) {
                    BlockPos q = new BlockPos(cx * 16 + dx, site.ground() + 1, cz * 16 + dz);
                    if (!postAt(site, q)) {
                        spot = q;
                    }
                }
            }
            Entity off = spot == null ? null : RoyalPilots.deploy(level, Vec3.atBottomCenterOf(spot), 0F, "m_1a_2", 0, null);
            if (off != null) {
                off.getPersistentData().getCompound(RoyalPilots.KEY).remove("Rev");
                staleOff = stale(off);
                off.discard();
            }
            // and a parked vehicle post: one standing at it is not stale; with none there, the muster brings one, once
            CitadelData.Post parked = null;
            for (List<CitadelData.Post> list : CitadelData.posts().values()) {
                for (CitadelData.Post p : list) {
                    if (p.role().equals("PARKED") && (parked == null || Math.abs(p.x()) + Math.abs(p.z()) < Math.abs(parked.x()) + Math.abs(parked.z()))) {
                        parked = p;
                    }
                }
            }
            if (parked == null) {
                return;
            }
            BlockPos at = site.toWorld(parked.x(), parked.y(), parked.z());
            musterPost = parked.vehicle() + "@" + at.toShortString();
            force(level, at.getX() >> 4, at.getZ() >> 4);
            level.getChunk(at.getX() >> 4, at.getZ() >> 4);
            Entity here = RoyalPilots.deploy(level, Vec3.atBottomCenterOf(at), parked.yaw(), parked.vehicle(), 0, null);
            if (here != null) {
                here.getPersistentData().getCompound(RoyalPilots.KEY).remove("Rev");
                staleAtPost = stale(here);
                here.discard();
            }
            // the post's chunk with none of its vehicles nor their crews (and its people taken as come, so the garrison
            // does not bring them as well): the muster must bring one for each vehicle post, and a second muster none
            int sx = Math.floorDiv(parked.x(), 16), sz = Math.floorDiv(parked.z(), 16);
            CitadelGarrison.Ledger g = CitadelGarrison.Ledger.of(level);
            g.done.add(CitadelGarrison.key(site, sx, sz));
            g.setDirty();
            BlockPos lo = site.toWorld(sx * 16, parked.y(), sz * 16);
            for (Entity en : level.getEntities((Entity) null, new AABB(lo).expandTowards(16, 0, 16).inflate(8, 16, 8),
                x -> x.getTags().contains(RoyalPilots.CREWED) || x instanceof RoyalMob m && m.getPersistentData().contains("OrorMotor"))) {
                for (Entity rider : List.copyOf(en.getPassengers())) {
                    rider.discard();
                }
                en.discard();
            }
            expectMuster = (int) CitadelData.posts(sx, sz).stream().filter(q -> !q.vehicle().isEmpty()).count();
            mustered = muster(level, site, sx, sz);
            musteredAgain = muster(level, site, sx, sz);
        }

        void tick(ServerLevel level) {
            boolean waiting;
            synchronized (QUEUE) {
                waiting = QUEUED.contains(job.key);
            }
            long t = level.getGameTime() - started;
            if (waiting && t < 1200) {
                return;
            }
            CitadelData.Chunk data = CitadelData.chunk(job.sx, job.sz);
            int mismatch = 0;
            String firstBad = "";
            for (int s = 0; s < job.patch.sy().length; s++) {
                for (int i : job.patch.positions()[s]) {
                    BlockState want = expected(site, data, job.patch.sy()[s], i);
                    if (want == null) {
                        continue;
                    }
                    BlockPos p = world(job, job.patch.sy()[s], i);
                    if (p.getY() <= level.getMinBuildHeight() || p.getY() >= level.getMaxBuildHeight()) {
                        continue;
                    }
                    BlockState have = level.getBlockState(p);
                    // water spreading since, and grass turning to dirt in the shade, are the world going on, not the update
                    boolean living = !have.getFluidState().isEmpty() || !want.getFluidState().isEmpty()
                        || have.is(Blocks.DIRT) && want.is(Blocks.GRASS_BLOCK) || have.is(Blocks.GRASS_BLOCK) && want.is(Blocks.DIRT);
                    if (have != want && !living) {
                        if (mismatch++ == 0) {
                            firstBad = p.toShortString() + " " + have + " for " + want;
                        }
                    }
                }
            }
            int spilled = chest == null ? 0 : level.getEntitiesOfClass(ItemEntity.class, new AABB(chest).inflate(3)).size();
            boolean ok = !waiting && mismatch == 0 && spilled == 0 && job.changed >= spoiled
                && (!jp.oror.reborn.vehicle.Sbw.present() || staleOff && !staleAtPost && mustered == expectMuster && expectMuster > 0 && musteredAgain == 0);
            LOG.info("CITADEL-UPDATE {\"ok\":{},\"chunk\":[{},{}],\"marked\":{},\"spoiled\":{},\"changed\":{},\"mismatch\":{},\"firstBad\":\"{}\","
                    + "\"chestSpilled\":{},\"emptied\":{},\"staleOffPost\":{},\"staleAtPost\":{},\"mustered\":{},\"expected\":{},\"musteredAgain\":{},"
                    + "\"post\":\"{}\",\"ticks\":{},\"tableChunks\":{}}", ok, job.sx, job.sz, job.patch.size(), spoiled, job.changed, mismatch,
                firstBad.replace("\"", "'"), spilled, containersEmptied, staleOff, staleAtPost, mustered, expectMuster, musteredAgain, musterPost, t,
                patches().size());
            for (ChunkPos p : forced) {
                level.setChunkForced(p.x, p.z, false);
            }
            test = null;
            testDone = true;
        }
    }

    // ---------------------------------------------------------------------------------------------------------- ledger

    /** Which chunks of which capitals have been updated to REVISION. */
    static final class Ledger extends SavedData {
        static final Factory<Ledger> FACTORY = new Factory<>(Ledger::new, Ledger::load, null);
        final Set<Long> done = new HashSet<>();
        /** (058) Chunks the operator ordered rebuilt, still to do; and whether the update runs by itself (off unless asked). */
        final Set<Long> rebuild = new HashSet<>();
        boolean auto;

        static Ledger of(ServerLevel level) {
            return level.getDataStorage().computeIfAbsent(FACTORY, "oror_citadel_update");
        }

        static Ledger load(CompoundTag tag, HolderLookup.Provider registries) {
            Ledger l = new Ledger();
            if (tag.getInt("Revision") == REVISION) {
                for (long k : tag.getLongArray("Done")) {
                    l.done.add(k);
                }
            }
            for (long k : tag.getLongArray("Rebuild")) {
                l.rebuild.add(k);
            }
            l.auto = tag.getBoolean("Auto");
            return l;
        }

        @Override
        public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
            tag.putInt("Revision", REVISION);
            tag.put("Done", new LongArrayTag(done.stream().mapToLong(Long::longValue).toArray()));
            tag.put("Rebuild", new LongArrayTag(rebuild.stream().mapToLong(Long::longValue).toArray()));
            tag.putBoolean("Auto", auto);
            return tag;
        }
    }
}
