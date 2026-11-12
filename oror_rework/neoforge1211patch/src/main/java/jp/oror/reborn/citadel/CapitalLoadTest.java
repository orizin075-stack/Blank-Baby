package jp.oror.reborn.citadel;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import net.minecraft.Util;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.ChunkPos;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (053) /oror capitalload test: how heavy the capital is in ordinary play (the user: too heavy). The capital's middle
 * and eight chunks round it (17 x 17, a player's view of it) are kept loaded; once it has loaded and its people have
 * come (a minute), the server's ticks are timed for a minute, and each kind of entity's own ticks: CAPITAL-LOAD-START
 * then CAPITAL-LOAD {...} (the CI profiles the server thread between the two: out/capital_profile.txt).
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class CapitalLoadTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Capital Load");
    public static volatile boolean resultLogged;
    private static final int RADIUS = 8, SETTLE = 1200, MEASURE = 1200;

    private static final class Run {
        ServerLevel level;
        CitadelSites.Site site;
        final List<ChunkPos> chunks = new ArrayList<>();
        long forcedAt, loadedAt = -1, measureFrom = -1;
        long tickStart;
        final List<Double> ticks = new ArrayList<>();
        final Map<String, long[]> perType = new HashMap<>();
        final Map<Integer, Long> began = new HashMap<>();
    }

    private static volatile Run run;

    private CapitalLoadTest() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("capitalload").then(Commands.literal("test")
            .requires(s -> s.hasPermission(2)).executes(c -> start(c.getSource())))));
    }

    private static int start(CommandSourceStack src) {
        if (run != null) {
            return 0;
        }
        MinecraftServer server = src.getServer();
        CompletableFuture.supplyAsync(() -> CitadelSites.nearest(BlockPos.ZERO, 4), Util.backgroundExecutor()).thenAcceptAsync(site -> {
            if (site == null) {
                LOG.info("CAPITAL-LOAD {\"site\":null}");
                resultLogged = true;
                return;
            }
            Run r = new Run();
            r.level = server.overworld();
            r.site = site;
            ChunkPos mid = new ChunkPos(site.center());
            for (int dx = -RADIUS; dx <= RADIUS; dx++) {
                for (int dz = -RADIUS; dz <= RADIUS; dz++) {
                    ChunkPos p = new ChunkPos(mid.x + dx, mid.z + dz);
                    r.chunks.add(p);
                    CitadelChunkLoading.force(r.level, p.x, p.z, true);
                }
            }
            r.forcedAt = r.level.getGameTime();
            run = r;
        }, server);
        return 1;
    }

    @SubscribeEvent(priority = EventPriority.HIGHEST)
    public static void before(ServerTickEvent.Pre e) {
        Run r = run;
        if (r != null && r.measureFrom >= 0) {
            r.tickStart = System.nanoTime();
        }
    }

    @SubscribeEvent(priority = EventPriority.HIGHEST)
    public static void entityBefore(EntityTickEvent.Pre e) {
        Run r = run;
        if (r != null && r.measureFrom >= 0 && !e.getEntity().level().isClientSide) {
            r.began.put(e.getEntity().getId(), System.nanoTime());
        }
    }

    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void entityAfter(EntityTickEvent.Post e) {
        Run r = run;
        if (r == null || r.measureFrom < 0 || e.getEntity().level().isClientSide) {
            return;
        }
        Long t0 = r.began.remove(e.getEntity().getId());
        if (t0 != null) {
            String type = BuiltInRegistries.ENTITY_TYPE.getKey(e.getEntity().getType()).toString();
            long[] c = r.perType.computeIfAbsent(type, k -> new long[2]);
            c[0] += System.nanoTime() - t0;
            c[1]++;
        }
    }

    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void tick(ServerTickEvent.Post e) {
        Run r = run;
        if (r == null) {
            return;
        }
        long now = r.level.getGameTime();
        if (r.measureFrom >= 0) {
            r.ticks.add((System.nanoTime() - r.tickStart) / 1e6);
        }
        if (r.loadedAt < 0) {
            boolean all = r.chunks.stream().allMatch(p -> r.level.getChunkSource().getChunkNow(p.x, p.z) != null);
            if (all || now - r.forcedAt > 6000) {
                r.loadedAt = now;
            }
            return;
        }
        if (r.measureFrom < 0) {
            if (now - r.loadedAt >= SETTLE) {
                r.measureFrom = now;
                LOG.info("CAPITAL-LOAD-START {\"chunks\":{},\"loadTicks\":{}}", r.chunks.size(), r.loadedAt - r.forcedAt);
            }
            return;
        }
        if (now - r.measureFrom < MEASURE) {
            return;
        }
        run = null;
        List<Double> t = new ArrayList<>(r.ticks);
        t.sort(Double::compare);
        double avg = t.stream().mapToDouble(Double::doubleValue).average().orElse(0);
        double p95 = t.isEmpty() ? 0 : t.get(Math.min(t.size() - 1, (int) (t.size() * 0.95)));
        double max = t.isEmpty() ? 0 : t.get(t.size() - 1);
        Map<String, Integer> count = new HashMap<>();
        int total = 0;
        for (Entity x : r.level.getAllEntities()) {
            count.merge(BuiltInRegistries.ENTITY_TYPE.getKey(x.getType()).toString(), 1, Integer::sum);
            total++;
        }
        StringBuilder cost = new StringBuilder();
        r.perType.entrySet().stream().sorted(Comparator.comparingLong((Map.Entry<String, long[]> en) -> -en.getValue()[0])).limit(15)
            .forEach(en -> cost.append(cost.length() > 0 ? "," : "").append(String.format(Locale.ROOT, "\"%s\":[%.2f,%d]", en.getKey(),
                en.getValue()[0] / 1e6 / Math.max(1, t.size()), count.getOrDefault(en.getKey(), 0))));
        LOG.info(String.format(Locale.ROOT, "CAPITAL-LOAD {\"site\":[%d,%d],\"chunks\":%d,\"entities\":%d,\"msptAvg\":%.2f,\"msptP95\":%.2f,"
                + "\"msptMax\":%.2f,\"turretMovesSkipped\":%d,\"mapSearches\":[%d,%d],\"tickMsPerType\":{%s}}", r.site.center().getX(), r.site.center().getZ(),
            r.chunks.size(), total, avg, p95, max, jp.oror.reborn.perf.TurretRest.skipped, jp.oror.reborn.perf.MapSearchCache.searched,
            jp.oror.reborn.perf.MapSearchCache.reused, cost));
        try {
            LOG.info("CAPITAL-INTEGRITY {}", CitadelIntegrity.scan(r.level, r.site, r.chunks));
        } catch (RuntimeException ex) {
            LOG.error("CAPITAL-INTEGRITY failed", ex);
        }
        for (ChunkPos p : r.chunks) {
            CitadelChunkLoading.force(r.level, p.x, p.z, false);
        }
        resultLogged = true;
    }
}
