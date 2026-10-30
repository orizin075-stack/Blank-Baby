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
                    t.expected.merge(post.role().equals("TANK") ? "GUARD" : post.role(), 1, Integer::sum);
                }
            }
            CitadelSites.Site site = t.site;
            BlockPos throne = site.throne();
            String below = level.getBlockState(throne.below()).getBlock().getDescriptionId();
            boolean dais = level.getBlockState(throne.below()).is(Blocks.GOLD_BLOCK) && level.getBlockState(throne).isAir();
            RoyalMob king = level.getEntitiesOfClass(RoyalMob.class, new AABB(throne).inflate(3), m -> m.role().name().equals("KING"))
                .stream().findFirst().orElse(null);
            String line = String.format(Locale.ROOT, "{\"site\":[%d,%d,%d],\"forced\":%b,\"ground\":%d,\"dy\":%d,\"locateMs\":%.1f,"
                    + "\"chunks\":%d,\"loaded\":%d,\"loadTicks\":%d,\"throne\":[%d,%d,%d],\"dais\":%b,\"underKing\":\"%s\",\"kingAtThrone\":%b,"
                    + "\"spawned\":%d,\"expected\":%s,\"found\":%s}",
                site.center().getX(), site.center().getY(), site.center().getZ(), site.forced(), site.ground(), site.dy(), t.locateMs,
                t.chunks.size(), loaded, t.loadedAt - t.started, throne.getX(), throne.getY(), throne.getZ(), dais, below, king != null,
                CitadelGarrison.spawned(), json(t.expected), json(census(level, site)));
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
        List<String> vehicles = new ArrayList<>();
        for (net.minecraft.world.entity.Entity v : level.getEntities((net.minecraft.world.entity.Entity) null, box,
            x -> x.getTags().contains(jp.oror.reborn.vehicle.RoyalPilots.CREWED))) {
            vehicles.add(jp.oror.reborn.vehicle.RoyalPilots.report(v));
        }
        String line = String.format(Locale.ROOT, "{\"royals\":%d,\"armed\":%d,\"nearPost\":%d,\"found\":%s,\"vehicles\":[%s],\"mspt\":%.2f}",
            royals, armed, atPost, json(census(level, t.site)), String.join(",", vehicles), e.getServer().getAverageTickTimeNanos() / 1e6);
        LOG.info("CITADEL-SELFTEST-LATER {}", line);
        for (ChunkPos p : t.chunks) {
            level.setChunkForced(p.x, p.z, false);
        }
        selftestDone = true;
    }

    private static String json(Map<String, Integer> m) {
        StringBuilder b = new StringBuilder("{");
        m.forEach((k, v) -> b.append(b.length() > 1 ? "," : "").append('"').append(k).append("\":").append(v));
        return b.append('}').toString();
    }
}
