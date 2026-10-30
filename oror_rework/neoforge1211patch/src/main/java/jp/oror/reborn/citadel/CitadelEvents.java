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
    private static Pending pending;

    private record Pending(CitadelSites.Site site, List<ChunkPos> chunks, long at, Map<String, Integer> expected) {
    }

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
        pending = null;
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
        for (Villager v : level.getEntitiesOfClass(Villager.class, box, v -> v.isAlive() && v.getTags().contains(GrandCitadelFeature.TAG))) {
            n.merge("VILLAGER", 1, Integer::sum);
        }
        return n;
    }

    /**
     * For CI: finds the nearest natural citadel to the world origin, generates the chunks of the throne room, the north
     * gates, a fortress and part of the town, and logs the site, the timings, the blocks of the throne and who stands
     * where, against the garrison table. 200 ticks later it logs again (are they armed, still at their posts, MSPT).
     */
    private static int selftest(CommandSourceStack src) {
        ServerLevel level = src.getServer().overworld();
        long t0 = System.nanoTime();
        CitadelSites.Site site = CitadelSites.nearest(BlockPos.ZERO, 4);
        long t1 = System.nanoTime();
        if (site == null) {
            LOG.info("CITADEL-SELFTEST {\"site\":null}");
            src.sendFailure(Component.literal("no citadel within 4 regions"));
            return 0;
        }
        List<ChunkPos> chunks = new ArrayList<>();
        int[][] spots = {{0, -32}, {0, -100}, {0, -288}, {0, -457}, {0, -570}, {-234, -234}, {-234, -193}, {-115, -29}, {0, 0}};
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
        // also the apron and the land beyond on the north edge
        for (int dz = -3; dz <= 0; dz++) {
            chunks.add(new ChunkPos(site.chunkX() + CitadelData.HALF, site.chunkZ() + dz));
        }
        for (ChunkPos p : chunks) {
            level.setChunkForced(p.x, p.z, true);
        }
        for (ChunkPos p : chunks) {
            level.getChunk(p.x, p.z);
        }
        long t2 = System.nanoTime();
        Map<String, Integer> expected = new TreeMap<>();
        for (ChunkPos p : chunks) {
            int sx = p.x - site.chunkX() - CitadelData.HALF, sz = p.z - site.chunkZ() - CitadelData.HALF;
            for (CitadelData.Post post : CitadelData.posts(sx, sz)) {
                expected.merge(post.role().equals("TANK") ? "GUARD" : post.role(), 1, Integer::sum);
                if (!post.vehicle().isEmpty()) {
                    expected.merge("VEHICLE", 1, Integer::sum);
                }
            }
        }
        BlockPos throne = site.throne();
        String below = level.getBlockState(throne.below()).getBlock().getDescriptionId();
        boolean dais = level.getBlockState(throne.below()).is(Blocks.GOLD_BLOCK) && level.getBlockState(throne).isAir();
        Map<String, Integer> found = census(level, site);
        RoyalMob king = level.getEntitiesOfClass(RoyalMob.class, new AABB(throne).inflate(3), m -> m.role().name().equals("KING")).stream().findFirst().orElse(null);
        String line = String.format(Locale.ROOT, "{\"site\":[%d,%d,%d],\"forced\":%b,\"ground\":%d,\"dy\":%d,\"locateMs\":%.1f,\"chunks\":%d,"
                + "\"generateMs\":%.1f,\"throne\":[%d,%d,%d],\"dais\":%b,\"underKing\":\"%s\",\"kingAtThrone\":%b,\"expected\":%s,\"found\":%s}",
            site.center().getX(), site.center().getY(), site.center().getZ(), site.forced(), site.ground(), site.dy(), (t1 - t0) / 1e6,
            chunks.size(), (t2 - t1) / 1e6, throne.getX(), throne.getY(), throne.getZ(), dais, below, king != null, json(expected), json(found));
        LOG.info("CITADEL-SELFTEST {}", line);
        src.sendSuccess(() -> Component.literal(line), false);
        pending = new Pending(site, chunks, level.getGameTime() + 200, expected);
        return 1;
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        Pending p = pending;
        if (p == null) {
            return;
        }
        ServerLevel level = e.getServer().overworld();
        if (level.getGameTime() < p.at) {
            return;
        }
        pending = null;
        BlockPos a = p.site.toWorld(-CitadelData.HALF * 16, 0, -CitadelData.HALF * 16);
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
            royals, armed, atPost, json(census(level, p.site)), String.join(",", vehicles), e.getServer().getAverageTickTimeNanos() / 1e6);
        LOG.info("CITADEL-SELFTEST-LATER {}", line);
    }

    private static String json(Map<String, Integer> m) {
        StringBuilder b = new StringBuilder("{");
        m.forEach((k, v) -> b.append(b.length() > 1 ? "," : "").append('"').append(k).append("\":").append(v));
        return b.append('}').toString();
    }
}
