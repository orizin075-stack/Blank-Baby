package jp.oror.reborn.citadel;

import com.mojang.brigadier.CommandDispatcher;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.CompletableFuture;
import jp.oror.reborn.royal.RoyalMob;
import net.minecraft.ChatFormatting;
import net.minecraft.Util;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.coordinates.ColumnPosArgument;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ColumnPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.level.LevelEvent;
import net.neoforged.neoforge.event.server.ServerStoppedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import net.neoforged.neoforge.registries.RegisterEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/** Registers the Grand Citadel feature, binds the sites to the overworld, and the /oror citadel commands. */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class CitadelEvents {
    public static final GrandCitadelFeature FEATURE = new GrandCitadelFeature();
    private static final Logger LOG = LoggerFactory.getLogger("OROR Citadel");

    private CitadelEvents() {
    }

    @EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD)
    public static final class Registration {
        @SubscribeEvent
        public static void register(RegisterEvent e) {
            if (e.getRegistryKey().equals(Registries.FEATURE)) {
                e.register(Registries.FEATURE, ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "grand_citadel"), () -> FEATURE);
            }
        }
    }

    @SubscribeEvent
    public static void load(LevelEvent.Load e) {
        if (e.getLevel() instanceof ServerLevel level && level.dimension().equals(Level.OVERWORLD)) {
            CitadelSites.bind(level);
        }
    }

    @SubscribeEvent
    public static void started(net.neoforged.neoforge.event.server.ServerStartedEvent e) {
        CitadelSites.spawnCheck(e.getServer().overworld());
    }

    @SubscribeEvent
    public static void stopped(ServerStoppedEvent e) {
        CitadelSites.unbind();
        test = null;
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        CommandDispatcher<CommandSourceStack> d = e.getDispatcher();
        d.register(Commands.literal("oror").then(Commands.literal("citadel").requires(s -> s.hasPermission(2))
            .then(Commands.literal("locate").executes(c -> locate(c.getSource())))
            .then(Commands.literal("info").executes(c -> info(c.getSource())))
            .then(Commands.literal("place").then(Commands.argument("pos", ColumnPosArgument.columnPos())
                .executes(c -> place(c.getSource(), ColumnPosArgument.getColumnPos(c, "pos")))))
            .then(Commands.literal("selftest").executes(c -> selftest(c.getSource())))));
    }

    private static int locate(CommandSourceStack src) {
        BlockPos from = BlockPos.containing(src.getPosition());
        MinecraftServer server = src.getServer();
        src.sendSuccess(() -> Component.literal("グランドシタデルを探しています…").withStyle(ChatFormatting.GRAY), false);
        CompletableFuture.supplyAsync(() -> CitadelSites.nearest(from, 4), Util.backgroundExecutor()).thenAcceptAsync(site -> {
            if (site == null) {
                src.sendFailure(Component.literal("近く（約16,000ブロック以内）にグランドシタデルはありません。"));
                return;
            }
            BlockPos c = site.center(), t = site.throne();
            int dist = (int) Math.sqrt(c.distSqr(from));
            String tp = "/tp @s " + c.getX() + " " + (c.getY() + 1) + " " + c.getZ();
            src.sendSuccess(() -> Component.literal("グランドシタデル: 城 " + c.getX() + " " + c.getY() + " " + c.getZ()
                    + "（約" + dist + "ブロック、王座 " + t.getX() + " " + t.getY() + " " + t.getZ() + "）")
                .withStyle(s -> s.withColor(ChatFormatting.GOLD).withClickEvent(new ClickEvent(ClickEvent.Action.SUGGEST_COMMAND, tp))
                    .withHoverEvent(new HoverEvent(HoverEvent.Action.SHOW_TEXT, Component.literal(tp)))), false);
        }, server);
        return 1;
    }

    private static int info(CommandSourceStack src) {
        ServerLevel level = src.getServer().overworld();
        BlockPos at = BlockPos.containing(src.getPosition());
        CitadelSites.Site site = CitadelSites.at(level.getChunkSource().getGenerator(), at.getX() >> 4, at.getZ() >> 4, CitadelSites.APRON);
        if (site == null) {
            src.sendFailure(Component.literal("ここはグランドシタデルの中ではありません。/oror citadel locate で探せます。"));
            return 0;
        }
        Map<String, Integer> found = census(level, site);
        src.sendSuccess(() -> Component.literal("グランドシタデル（" + (site.forced() ? "設置" : "自然生成") + "）: 城 " + site.center().toShortString()
            + "、地面 y" + site.ground() + "、王座 " + site.throne().toShortString() + "\n読み込み中の住人: " + found), false);
        return 1;
    }

    private static int place(CommandSourceStack src, ColumnPos pos) {
        CitadelSites.Site site = CitadelSites.place(src.getServer().overworld(), pos.x(), pos.z());
        if (site == null) {
            src.sendFailure(Component.literal("ほかのグランドシタデルと重なるため置けません。"));
            return 0;
        }
        src.sendSuccess(() -> Component.literal("グランドシタデルを城 " + site.center().toShortString() + " に予定しました。"
            + "まだ生成されていないチャンクから建ちます（生成済みの場所は変わりません）。"), true);
        return 1;
    }

    /** Royals and townsfolk of the citadel in loaded chunks, by role. */
    private static Map<String, Integer> census(ServerLevel level, CitadelSites.Site site) {
        BlockPos a = site.toWorld(-CitadelData.HALF * 16, -CitadelData.GROUND, -CitadelData.HALF * 16);
        AABB box = new AABB(a.getX(), level.getMinBuildHeight(), a.getZ(), a.getX() + CitadelSites.SIZE * 16, level.getMaxBuildHeight(),
            a.getZ() + CitadelSites.SIZE * 16);
        Map<String, Integer> n = new TreeMap<>();
        for (RoyalMob m : level.getEntitiesOfClass(RoyalMob.class, box, RoyalMob::isAlive)) {
            n.merge(m.role().name(), 1, Integer::sum);
        }
        for (Villager v : level.getEntitiesOfClass(Villager.class, box, v -> v.isAlive() && v.getTags().contains(CitadelGarrison.TAG))) {
            n.merge("VILLAGER", 1, Integer::sum);
        }
        return n;
    }

    /**
     * For CI: finds the nearest natural citadel to the world origin (off the server thread), forces the chunks of the
     * throne room, the north gates, a fortress and part of the town to load, and once they have loaded and their people
     * have taken their posts logs the site, the timings, the blocks of the throne and who stands where, against the
     * garrison table (CITADEL-SELFTEST). 200 ticks later it logs again: are they armed, still at their posts, the tank
     * crews, MSPT (CITADEL-SELFTEST-LATER). Nothing here blocks the server thread.
     */
    private static int selftest(CommandSourceStack src) {
        MinecraftServer server = src.getServer();
        long t0 = System.nanoTime();
        CompletableFuture.supplyAsync(() -> CitadelSites.nearest(BlockPos.ZERO, 4), Util.backgroundExecutor()).thenAcceptAsync(site -> {
            ServerLevel level = server.overworld();
            if (site == null) {
                LOG.info("CITADEL-SELFTEST {\"site\":null}");
                selftestDone = true;
                return;
            }
            List<ChunkPos> chunks = new ArrayList<>();
            int[][] spots = {{0, -32}, {0, -100}, {0, -288}, {0, -440}, {0, -570}, {-234, -234}, {-234, -193}, {-115, -29}, {0, 0}};
            for (int[] s : spots) {
                int cx = (s[0] + site.offsetX()) >> 4, cz = (s[1] + site.offsetZ()) >> 4;
                for (int dx = -1; dx <= 1; dx++) {
                    for (int dz = -1; dz <= 1; dz++) {
                        ChunkPos p = new ChunkPos(cx + dx, cz + dz);
                        if (!chunks.contains(p)) {
                            chunks.add(p);
                        }
                    }
                }
            }
            for (int dz = -3; dz <= 0; dz++) {
                chunks.add(new ChunkPos(site.chunkX() + CitadelData.HALF, site.chunkZ() + dz));
            }
            // one post of each of the kingdom's installations: a runway, a helipad, a hangar, the turrets of each kind
            java.util.Set<String> kinds = new java.util.TreeSet<>(List.of("airbase", "helipad", "hangar", "battery", "crossfire", "casemate", "redoubt"));
            java.util.Set<String> vehicles = new java.util.TreeSet<>();
            for (List<CitadelData.Post> posts : CitadelData.posts().values()) {
                for (CitadelData.Post post : posts) {
                    if (kinds.remove(post.post()) | (!post.vehicle().isEmpty() && vehicles.add(post.vehicle()))) {
                        ChunkPos p = new ChunkPos((post.x() + site.offsetX()) >> 4, (post.z() + site.offsetZ()) >> 4);
                        for (int dx = -1; dx <= 1; dx++) {
                            for (int dz = -1; dz <= 1; dz++) {
                                ChunkPos q = new ChunkPos(p.x + dx, p.z + dz);
                                if (!chunks.contains(q)) {
                                    chunks.add(q);
                                }
                            }
                        }
                    }
                }
            }
            for (ChunkPos p : chunks) {
                level.setChunkForced(p.x, p.z, true);
            }
            test = new Test(site, chunks, level.getGameTime(), (System.nanoTime() - t0) / 1e6);
        }, server);
        src.sendSuccess(() -> Component.literal("citadel selftest started"), false);
        return 1;
    }

    private static final class Test {
        final CitadelSites.Site site;
        final List<ChunkPos> chunks;
        final long started;
        final double locateMs;
        long loadedAt = -1, reportedAt = -1;
        Map<String, Integer> expected;

        Test(CitadelSites.Site site, List<ChunkPos> chunks, long started, double locateMs) {
            this.site = site;
            this.chunks = chunks;
            this.started = started;
            this.locateMs = locateMs;
        }
    }

    private static volatile Test test;
    public static volatile boolean selftestDone;

    private static final java.util.ArrayDeque<ChunkPos> RELEASE = new java.util.ArrayDeque<>();

    @SubscribeEvent
    public static void release(ServerTickEvent.Post e) {
        net.minecraft.server.level.ServerLevel level = e.getServer().overworld();
        for (int i = 0; i < 4 && !RELEASE.isEmpty(); i++) {
            ChunkPos p = RELEASE.poll();
            level.setChunkForced(p.x, p.z, false);
        }
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        Test t = test;
        if (t == null) {
            return;
        }
        ServerLevel level = e.getServer().overworld();
        long now = level.getGameTime();
        if (t.loadedAt < 0) {
            boolean all = t.chunks.stream().allMatch(p -> level.getChunkSource().getChunkNow(p.x, p.z) != null);
            if (all || now - t.started > 6000) {
                t.loadedAt = now;
            }
            return;
        }
        if (t.reportedAt < 0) {
            // let the garrison queue fill the posts of the chunks that just loaded
            if (now - t.loadedAt < 60 && CitadelGarrison.queued() > 0 || now - t.loadedAt < 20) {
                return;
            }
            t.reportedAt = now;
            t.expected = new TreeMap<>();
            int loaded = 0;
            for (ChunkPos p : t.chunks) {
                if (level.getChunkSource().getChunkNow(p.x, p.z) == null) {
                    continue;
                }
                loaded++;
                int sx = p.x - t.site.chunkX() - CitadelData.HALF, sz = p.z - t.site.chunkZ() - CitadelData.HALF;
                for (CitadelData.Post post : CitadelData.posts(sx, sz)) {
                    if (post.role().equals("PARKED")) {
                        continue;
                    }
                    t.expected.merge(post.role().equals("TANK") ? "GUARD" : post.role(), 1, Integer::sum);
                }
            }
            CitadelSites.Site site = t.site;
            BlockPos throne = site.throne();
            String below = level.getBlockState(throne.below()).getBlock().getDescriptionId();
            boolean dais = level.getBlockState(throne.below()).is(Blocks.GOLD_BLOCK) && level.getBlockState(throne).isAir();
            RoyalMob king = level.getEntitiesOfClass(RoyalMob.class, new AABB(throne).inflate(3), m -> m.role().name().equals("KING"))
                .stream().findFirst().orElse(null);
            BlockPos spawn = level.getSharedSpawnPos();
            String biome = level.getBiome(site.center()).unwrapKey().map(k -> k.location().toString()).orElse("?");
            String line = String.format(Locale.ROOT, "{\"site\":[%d,%d,%d],\"forced\":%b,\"ground\":%d,\"dy\":%d,\"locateMs\":%.1f,"
                    + "\"spawn\":[%d,%d,%d],\"fromSpawn\":%.0f,\"biome\":\"%s\","
                    + "\"chunks\":%d,\"loaded\":%d,\"loadTicks\":%d,\"throne\":[%d,%d,%d],\"dais\":%b,\"underKing\":\"%s\",\"kingAtThrone\":%b,"
                    + "\"spawned\":%d,\"expected\":%s,\"found\":%s,\"treasury\":%s,\"modItems\":%s}",
                site.center().getX(), site.center().getY(), site.center().getZ(), site.forced(), site.ground(), site.dy(), t.locateMs,
                spawn.getX(), spawn.getY(), spawn.getZ(), Math.sqrt(spawn.distSqr(new BlockPos(site.center().getX(), spawn.getY(), site.center().getZ()))),
                biome, t.chunks.size(), loaded, t.loadedAt - t.started, throne.getX(), throne.getY(), throne.getZ(), dais, below, king != null,
                CitadelGarrison.spawned(), json(t.expected), json(census(level, site)), treasury(level, t.chunks), modItems());
            LOG.info("CITADEL-SELFTEST {}", line);
            return;
        }
        if (now - t.reportedAt < 200) {
            return;
        }
        test = null;
        BlockPos a = t.site.toWorld(-CitadelData.HALF * 16, 0, -CitadelData.HALF * 16);
        AABB box = new AABB(a.getX(), level.getMinBuildHeight(), a.getZ(), a.getX() + CitadelSites.SIZE * 16, level.getMaxBuildHeight(),
            a.getZ() + CitadelSites.SIZE * 16);
        int royals = 0, armed = 0, atPost = 0;
        for (RoyalMob m : level.getEntitiesOfClass(RoyalMob.class, box, RoyalMob::isAlive)) {
            royals++;
            if (!m.getItemBySlot(EquipmentSlot.MAINHAND).isEmpty()) {
                armed++;
            }
            if (m.hasRestriction() && m.getRestrictCenter().distSqr(m.blockPosition()) < 24 * 24) {
                atPost++;
            }
        }
        // the kingdom's vehicles and turrets by type: manned, and standing ready with no crew
        Map<String, Integer> manned = new TreeMap<>(), ready = new TreeMap<>(), supply = new TreeMap<>();
        List<String> sample = new ArrayList<>(), supplySample = new ArrayList<>();
        java.util.Set<String> supplySeen = new java.util.HashSet<>();
        for (net.minecraft.world.entity.Entity v : level.getEntities((net.minecraft.world.entity.Entity) null, box,
            x -> x.getTags().contains(jp.oror.reborn.vehicle.RoyalPilots.CREWED))) {
            String id = net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.getKey(v.getType()).getPath();
            (v.getPassengers().isEmpty() ? ready : manned).merge(id, 1, Integer::sum);
            if (sample.size() < 3 && !v.getPassengers().isEmpty()) {
                sample.add(jp.oror.reborn.vehicle.RoyalPilots.report(v));
            }
            // the posts' supply: a station in reach of the vehicle, a depot beside it, what it carries
            String sup = jp.oror.reborn.vehicle.Supply.report(level, v);
            supply.merge(id + (sup.contains("\"charger\":true") ? "+station" : "") + (sup.contains("\"depots\":0") ? "" : "+depot"), 1, Integer::sum);
            if (supplySample.size() < 12 && !supplySeen.contains(id)) {
                supplySeen.add(id);
                supplySample.add(sup);
            }
        }
        // the king ten seconds on: still on the throne (his feet on the dais, within a block of its centre), and seated
        BlockPos throne = t.site.throne();
        RoyalMob king = level.getEntitiesOfClass(RoyalMob.class, new AABB(throne).inflate(24), m -> m.role().name().equals("KING")).stream()
            .min(java.util.Comparator.comparingDouble(m -> m.distanceToSqr(throne.getX() + 0.5, throne.getY(), throne.getZ() + 0.5))).orElse(null);
        String kingAt = king == null ? "null" : String.format(Locale.ROOT, "{\"distance\":%.2f,\"dy\":%.2f,\"onThrone\":%b,\"target\":%b}",
            Math.sqrt(king.distanceToSqr(throne.getX() + 0.5, king.getY(), throne.getZ() + 0.5)), king.getY() - throne.getY(),
            king.blockPosition().equals(throne) || king.distanceToSqr(throne.getX() + 0.5, throne.getY(), throne.getZ() + 0.5) < 1.5,
            king.getTarget() != null);
        String line = String.format(Locale.ROOT, "{\"royals\":%d,\"armed\":%d,\"nearPost\":%d,\"found\":%s,\"manned\":%s,\"ready\":%s,"
                + "\"parked\":%d,\"king\":%s,\"vehicles\":[%s],\"mspt\":%.2f}",
            royals, armed, atPost, json(census(level, t.site)), json(manned), json(ready), CitadelGarrison.parked(), kingAt, String.join(",", sample),
            e.getServer().getAverageTickTimeNanos() / 1e6);
        LOG.info("CITADEL-SELFTEST-LATER {}", line);
        LOG.info("CITADEL-SUPPLY {\"posts\":{},\"kinds\":[{}],\"magnetScan\":{\"answered\":{},\"checked\":{}}}", json(supply),
            String.join(",", supplySample), jp.oror.reborn.perf.MagnetScan.hits, jp.oror.reborn.perf.MagnetScan.probes);
        // released a few a tick: letting two hundred chunks of royals, townsfolk and vehicles unload in one go has
        // crashed the server's entity unloading (CI run 26)
        RELEASE.addAll(t.chunks);
        selftestDone = true;
    }

    /** The royal treasury's chests among the loaded chunks: how many, how many stacks, and the other namespaces' items in them. */
    private static String treasury(ServerLevel level, List<ChunkPos> chunks) {
        int chests = 0, stacks = 0;
        java.util.TreeSet<String> mods = new java.util.TreeSet<>();
        for (ChunkPos p : chunks) {
            net.minecraft.world.level.chunk.LevelChunk c = level.getChunkSource().getChunkNow(p.x, p.z);
            if (c == null) {
                continue;
            }
            for (net.minecraft.world.level.block.entity.BlockEntity be : c.getBlockEntities().values()) {
                if (be instanceof net.minecraft.world.level.block.entity.ChestBlockEntity chest && chest.getCustomName() != null
                    && chest.getCustomName().getString().contains("宝物庫")) {
                    chests++;
                    for (int i = 0; i < chest.getContainerSize(); i++) {
                        net.minecraft.world.item.ItemStack st = chest.getItem(i);
                        if (!st.isEmpty()) {
                            stacks++;
                            ResourceLocation id = net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(st.getItem());
                            if (!id.getNamespace().equals("minecraft")) {
                                mods.add(id.toString());
                            }
                        }
                    }
                }
            }
        }
        return String.format(Locale.ROOT, "{\"chests\":%d,\"stacks\":%d,\"modItems\":[%s]}", chests, stacks,
            String.join(",", mods.stream().map(m -> "\"" + m + "\"").toList()));
    }

    /** Of the other namespaces' items the citadel's containers can hold (treasure_items.json), the ones not registered. */
    private static String modItems() {
        List<String> missing = new ArrayList<>();
        int all = 0;
        try (java.io.InputStream in = CitadelData.class.getResourceAsStream("/data/oror_supreme_bosses/citadel/v12/treasure_items.json")) {
            if (in != null) {
                for (com.google.gson.JsonElement el : com.google.gson.JsonParser.parseReader(
                    new java.io.InputStreamReader(in, java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonArray("items")) {
                    all++;
                    if (!net.minecraft.core.registries.BuiltInRegistries.ITEM.containsKey(ResourceLocation.parse(el.getAsString()))) {
                        missing.add("\"" + el.getAsString() + "\"");
                    }
                }
            }
        } catch (java.io.IOException | RuntimeException ex) {
            LOG.error("treasure_items.json could not be read", ex);
        }
        return String.format(Locale.ROOT, "{\"listed\":%d,\"missing\":[%s]}", all, String.join(",", missing));
    }

    private static String json(Map<String, Integer> m) {
        StringBuilder b = new StringBuilder("{");
        m.forEach((k, v) -> b.append(b.length() > 1 ? "," : "").append('"').append(k).append("\":").append(v));
        return b.append('}').toString();
    }
}
