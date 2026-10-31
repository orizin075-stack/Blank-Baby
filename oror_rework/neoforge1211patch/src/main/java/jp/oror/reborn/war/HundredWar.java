package jp.oror.reborn.war;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.royal.RoyalRegistry;
import jp.oror.reborn.royal.RoyalRole;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.living.LivingDeathEvent;
import net.neoforged.neoforge.event.entity.living.LivingDropsEvent;
import net.neoforged.neoforge.event.entity.living.LivingExperienceDropEvent;
import net.neoforged.neoforge.event.server.ServerStoppedEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * The hundred-man battle: /oror war start [size] brings the kingdom's army (royal guards, imperial guards, mages, a
 * general, and when Superb Warfare is present tanks and a ground-attack aircraft crewed by royal soldiers) against an
 * illager host of the same size, fifty a side by default, a little way north and south of the caller. A director gives
 * every soldier an enemy (the nearest one, from a spatial grid) and keeps them on the field; how many it re-targets in a
 * tick follows the server's tick time (an AI budget that shrinks above 40 ms and grows again below 25 ms), and the dead
 * drop nothing, so a hundred fighters and their arrows, spells and shells do not bring the server down. The battle ends
 * when a side is down to a tenth, or after ten minutes (three with "test"), and the result is announced and logged
 * (WAR-RESULT: survivors, losses, duration, tick times).
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class HundredWar {
    public static final String TAG = "oror_war";
    private static final Logger LOG = LoggerFactory.getLogger("OROR War");
    private static final int FIELD = 96, SEPARATION = 26, CELL = 16;
    private static War war;
    /** Set when a battle has ended and its WAR-RESULT is logged. */
    public static volatile boolean resultLogged;
    /** Tick time of the fighters by entity type during a battle (nanoseconds, entity ticks), and the tick each started. */
    private static final Map<String, long[]> COST = new HashMap<>();
    private static final Map<Integer, Long> TICKING = new HashMap<>();

    /** A side's soldiers: who still has to be brought in, who is on the field. */
    private static final class Army {
        final String name;
        final List<Runnable> toSpawn = new ArrayList<>();
        final Set<UUID> ids = new HashSet<>();
        final List<Mob> alive = new ArrayList<>();
        int raised, lost;

        Army(String name) {
            this.name = name;
        }
    }

    private static final class War {
        final ServerLevel level;
        final Vec3 center;
        final int size;
        final boolean test;
        final long started;
        final long deadline;
        final Army[] sides = {new Army("王国軍"), new Army("イリジャー軍")};
        final List<ChunkPos> forced = new ArrayList<>();
        final List<Entity> machines = new ArrayList<>();
        int budget = 12;
        long endedAt = -1;
        String winner;
        double msptSum, msptMax;
        int msptSamples, peakFighters;

        War(ServerLevel level, Vec3 center, int size, boolean test) {
            this.level = level;
            this.center = center;
            this.size = size;
            this.test = test;
            this.started = level.getGameTime();
            this.deadline = started + (test ? 3600 : 12000);
        }
    }

    private HundredWar() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("war").requires(s -> s.hasPermission(2))
            .then(Commands.literal("start").executes(c -> start(c.getSource(), 100, false))
                .then(Commands.argument("size", com.mojang.brigadier.arguments.IntegerArgumentType.integer(10, 300))
                    .executes(c -> start(c.getSource(), com.mojang.brigadier.arguments.IntegerArgumentType.getInteger(c, "size"), false))
                    .then(Commands.literal("test").executes(c ->
                        start(c.getSource(), com.mojang.brigadier.arguments.IntegerArgumentType.getInteger(c, "size"), true)))))
            .then(Commands.literal("stop").executes(c -> stop(c.getSource())))
            .then(Commands.literal("status").executes(c -> status(c.getSource())))));
    }

    private static int start(CommandSourceStack src, int size, boolean test) {
        if (war != null) {
            src.sendFailure(Component.literal("すでに戦闘中です（/oror war status, /oror war stop）。"));
            return 0;
        }
        ServerLevel level = src.getLevel();
        BlockPos at = BlockPos.containing(src.getPosition());
        Vec3 center = Vec3.atBottomCenterOf(level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, at));
        War w = new War(level, center, size, test);
        for (int dx = -FIELD / 16 - 1; dx <= FIELD / 16 + 1; dx++) {
            for (int dz = -FIELD / 16 - 1; dz <= FIELD / 16 + 1; dz++) {
                ChunkPos p = new ChunkPos(((int) center.x >> 4) + dx, ((int) center.z >> 4) + dz);
                if (level.setChunkForced(p.x, p.z, true)) {
                    w.forced.add(p);
                }
            }
        }
        muster(w, size / 2, size - size / 2);
        war = w;
        announce(w, "百人戦開始：" + w.sides[0].name + " " + (size / 2) + " 対 " + w.sides[1].name + " " + (size - size / 2) + "（"
            + (int) center.x + ", " + (int) center.y + ", " + (int) center.z + "）");
        LOG.info("WAR-START {\"size\":{},\"center\":[{},{},{}],\"test\":{}}", size, (int) center.x, (int) center.y, (int) center.z, test);
        return 1;
    }

    /** The two armies, queued to arrive a few at a time. */
    private static void muster(War w, int kingdom, int host) {
        Army k = w.sides[0], h = w.sides[1];
        int machines = WarMachines.available() ? Math.max(1, kingdom / 25) : 0;
        int crew = 0;
        for (int i = 0; i < machines; i++) {
            boolean air = i == machines - 1 && kingdom >= 40;
            int seats = air ? 1 : 2;
            Vec3 at = w.center.add(air ? -30 : (i - (machines - 1) / 2.0) * 9, 0, -SEPARATION - 10);
            k.toSpawn.add(() -> WarMachines.deploy(w.level, at, air, seats, m -> enlist(w, 0, m), e -> w.machines.add(e)));
            crew += seats;
        }
        RoyalRole[] cycle = {RoyalRole.GUARD, RoyalRole.GUARD, RoyalRole.IMPERIAL, RoyalRole.GUARD, RoyalRole.MAGE, RoyalRole.GUARD,
            RoyalRole.GUARD, RoyalRole.IMPERIAL, RoyalRole.MAGE, RoyalRole.GUARD, RoyalRole.ARCHMAGE, RoyalRole.BODYGUARD};
        for (int i = 0; i < kingdom - crew; i++) {
            RoyalRole role = i == 0 ? RoyalRole.GENERAL : i == 1 && kingdom >= 60 ? RoyalRole.SAGE : cycle[i % cycle.length];
            Vec3 at = rank(w.center, -SEPARATION, i, kingdom - crew);
            k.toSpawn.add(() -> {
                RoyalMob m = RoyalRegistry.TYPES.get(role).create(w.level);
                if (m != null) {
                    place(w, m, at, 0F);
                    w.level.addFreshEntity(m);
                    enlist(w, 0, m);
                }
            });
        }
        List<EntityType<? extends Mob>> host6 = List.of(EntityType.PILLAGER, EntityType.VINDICATOR, EntityType.PILLAGER, EntityType.VINDICATOR,
            EntityType.WITCH, EntityType.PILLAGER, EntityType.VINDICATOR, EntityType.EVOKER, EntityType.PILLAGER, EntityType.VINDICATOR,
            EntityType.PILLAGER, EntityType.RAVAGER);
        for (int i = 0; i < host; i++) {
            EntityType<? extends Mob> type = host6.get(i % host6.size());
            Vec3 at = rank(w.center, SEPARATION, i, host);
            h.toSpawn.add(() -> {
                Mob m = type.create(w.level);
                if (m != null) {
                    place(w, m, at, 180F);
                    m.finalizeSpawn(w.level, w.level.getCurrentDifficultyAt(m.blockPosition()), MobSpawnType.EVENT, null);
                    w.level.addFreshEntity(m);
                    enlist(w, 1, m);
                }
            });
        }
    }

    /** Ranks of ten facing the enemy, z offset from the centre. */
    private static Vec3 rank(Vec3 c, int z, int i, int n) {
        int row = i / 10, col = i % 10, cols = Math.min(10, n);
        return c.add((col - (cols - 1) / 2.0) * 2.5, 0, z + Math.signum(z) * row * 2.5);
    }

    private static void place(War w, Mob m, Vec3 at, float yaw) {
        BlockPos top = w.level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, BlockPos.containing(at));
        m.moveTo(at.x, top.getY(), at.z, yaw, 0F);
        m.setYHeadRot(yaw);
        m.setPersistenceRequired();
    }

    private static void enlist(War w, int side, Mob m) {
        m.addTag(TAG);
        m.getPersistentData().putInt("OrorWarSide", side);
        m.setPersistenceRequired();
        Army a = w.sides[side];
        a.ids.add(m.getUUID());
        a.alive.add(m);
        a.raised++;
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        War w = war;
        if (w == null) {
            return;
        }
        MinecraftServer server = e.getServer();
        long now = w.level.getGameTime();
        // arrivals: four a tick from each side
        for (Army a : w.sides) {
            for (int i = 0; i < 4 && !a.toSpawn.isEmpty(); i++) {
                a.toSpawn.remove(0).run();
            }
        }
        for (Army a : w.sides) {
            a.alive.removeIf(m -> !m.isAlive() || m.isRemoved());
        }
        if (now % 20 == 0) {
            long[] times = server.getTickTimesNanos();
            int idx = server.getTickCount() % times.length;
            double max = 0, sum = 0;
            for (int i = 1; i <= 20; i++) {
                double ms = times[Math.floorMod(idx - i, times.length)] / 1e6;
                sum += ms;
                max = Math.max(max, ms);
            }
            double mspt = sum / 20;
            w.msptSum += mspt;
            w.msptSamples++;
            w.msptMax = Math.max(w.msptMax, max);
            w.budget = mspt > 40 ? Math.max(2, w.budget / 2) : mspt < 25 ? Math.min(40, w.budget + 2) : w.budget;
            w.peakFighters = Math.max(w.peakFighters, w.sides[0].alive.size() + w.sides[1].alive.size());
        }
        if (w.endedAt >= 0) {
            if (now - w.endedAt > (w.test ? 40 : 300)) {
                dismiss(w);
            }
            return;
        }
        boolean mustered = w.sides[0].toSpawn.isEmpty() && w.sides[1].toSpawn.isEmpty();
        if (mustered) {
            for (int s = 0; s < 2; s++) {
                Army a = w.sides[s];
                if (a.alive.size() * 10 <= a.raised) {
                    end(w, w.sides[1 - s].name);
                    return;
                }
            }
            if (now >= w.deadline) {
                double k = strength(w.sides[0]), h = strength(w.sides[1]);
                end(w, k == h ? null : k > h ? w.sides[0].name : w.sides[1].name);
                return;
            }
        }
        direct(w, now);
    }

    private static double strength(Army a) {
        double s = 0;
        for (Mob m : a.alive) {
            s += m.getHealth() / Math.max(1F, m.getMaxHealth());
        }
        return s / Math.max(1, a.raised);
    }

    /** Gives soldiers without a living enemy the nearest one, at most budget of them a tick, and keeps them on the field. */
    @SuppressWarnings("unchecked")
    private static void direct(War w, long now) {
        Map<Long, List<Mob>>[] grids = new Map[2];
        for (int s = 0; s < 2; s++) {
            grids[s] = new HashMap<>();
            for (Mob m : w.sides[s].alive) {
                grids[s].computeIfAbsent(cell(m.getX(), m.getZ()), k -> new ArrayList<>()).add(m);
            }
        }
        int used = 0;
        for (int s = 0; s < 2 && used < w.budget; s++) {
            for (Mob m : w.sides[s].alive) {
                if (used >= w.budget) {
                    break;
                }
                if ((m.getId() + now) % 10 != 0) {
                    continue;
                }
                LivingEntity t = m.getTarget();
                boolean enemy = t != null && t.isAlive() && w.sides[1 - s].ids.contains(t.getUUID());
                if (enemy && t.distanceToSqr(m) < 48 * 48) {
                    continue;
                }
                used++;
                Mob foe = nearest(grids[1 - s], m);
                if (foe != null) {
                    m.setTarget(foe);
                    if (m.getVehicle() == null && foe.distanceToSqr(m) > 20 * 20) {
                        m.getNavigation().moveTo(foe, 1.1);
                    }
                } else if (m.position().distanceToSqr(w.center) > FIELD * FIELD) {
                    m.getNavigation().moveTo(w.center.x, w.center.y, w.center.z, 1.0);
                }
            }
        }
        for (Entity machine : w.machines) {
            if (machine.isAlive()) {
                WarMachines.command(machine, w.center, FIELD);
            }
        }
    }

    private static long cell(double x, double z) {
        return ChunkPos.asLong(Math.floorDiv((int) x, CELL), Math.floorDiv((int) z, CELL));
    }

    private static Mob nearest(Map<Long, List<Mob>> grid, Mob m) {
        int cx = Math.floorDiv((int) m.getX(), CELL), cz = Math.floorDiv((int) m.getZ(), CELL);
        Mob best = null;
        double bestD = Double.MAX_VALUE;
        for (int r = 0; r <= FIELD * 2 / CELL; r++) {
            for (int dx = -r; dx <= r; dx++) {
                for (int dz = -r; dz <= r; dz++) {
                    if (Math.max(Math.abs(dx), Math.abs(dz)) != r) {
                        continue;
                    }
                    for (Mob o : grid.getOrDefault(ChunkPos.asLong(cx + dx, cz + dz), List.of())) {
                        double d = o.distanceToSqr(m);
                        if (d < bestD && o.isAlive()) {
                            bestD = d;
                            best = o;
                        }
                    }
                }
            }
            if (best != null && Math.sqrt(bestD) <= r * CELL) {
                break;
            }
        }
        return best;
    }

    private static void end(War w, String winner) {
        w.endedAt = w.level.getGameTime();
        w.winner = winner;
        Army k = w.sides[0], h = w.sides[1];
        long ticks = w.endedAt - w.started;
        String line = String.format(Locale.ROOT,
            "{\"size\":%d,\"winner\":\"%s\",\"kingdom\":{\"raised\":%d,\"alive\":%d,\"lost\":%d},\"host\":{\"raised\":%d,\"alive\":%d,\"lost\":%d},"
                + "\"machines\":%s,\"seconds\":%.1f,\"msptAvg\":%.2f,\"msptMax\":%.2f,\"peakFighters\":%d,\"budget\":%d,\"test\":%b,"
                + "\"tickCost\":{%s},\"onField\":{%s}}",
            w.size, winner == null ? "draw" : winner, k.raised, k.alive.size(), k.lost, h.raised, h.alive.size(), h.lost,
            WarMachines.report(w.machines), ticks / 20.0, w.msptSamples == 0 ? 0 : w.msptSum / w.msptSamples, w.msptMax, w.peakFighters,
            w.budget, w.test, costs(ticks), onField(w));
        LOG.info("WAR-RESULT {}", line);
        resultLogged = true;
        announce(w, "百人戦終了：" + (winner == null ? "引き分け" : winner + "の勝利") + "（" + k.name + " 残り" + k.alive.size() + "/" + k.raised
            + "、" + h.name + " 残り" + h.alive.size() + "/" + h.raised + "、" + (int) (ticks / 20) + "秒）");
    }

    /** Per fighter type: milliseconds of server tick it took on average, and microseconds per entity tick. */
    private static String costs(long ticks) {
        List<String> out = new ArrayList<>();
        COST.entrySet().stream().sorted((a, b) -> Long.compare(b.getValue()[0], a.getValue()[0])).limit(10).forEach(en ->
            out.add(String.format(Locale.ROOT, "\"%s\":[%.2f,%.0f]", en.getKey(), en.getValue()[0] / 1e6 / Math.max(1, ticks),
                en.getValue()[0] / 1e3 / Math.max(1, en.getValue()[1]))));
        COST.clear();
        TICKING.clear();
        return String.join(",", out);
    }

    /** What is on the field at the end, by entity type (the ten commonest): arrows, spells and shells included. */
    private static String onField(War w) {
        Map<String, Integer> n = new HashMap<>();
        for (Entity e : w.level.getEntities((Entity) null, new net.minecraft.world.phys.AABB(w.center, w.center).inflate(FIELD, 64, FIELD), x -> true)) {
            n.merge(net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).getPath(), 1, Integer::sum);
        }
        List<String> out = new ArrayList<>();
        n.entrySet().stream().sorted((a, b) -> b.getValue() - a.getValue()).limit(10)
            .forEach(en -> out.add("\"" + en.getKey() + "\":" + en.getValue()));
        return String.join(",", out);
    }

    @SubscribeEvent
    public static void beforeTick(EntityTickEvent.Pre e) {
        if (war != null && war.endedAt < 0 && !e.getEntity().level().isClientSide && e.getEntity().getTags().contains(TAG)) {
            TICKING.put(e.getEntity().getId(), System.nanoTime());
        }
    }

    @SubscribeEvent
    public static void afterTick(EntityTickEvent.Post e) {
        Long t0 = TICKING.isEmpty() ? null : TICKING.remove(e.getEntity().getId());
        if (t0 != null) {
            long[] c = COST.computeIfAbsent(net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.getKey(e.getEntity().getType()).getPath(),
                k -> new long[2]);
            c[0] += System.nanoTime() - t0;
            c[1]++;
        }
    }

    /** After the battle the survivors and machines leave the field and the chunks are released. */
    private static void dismiss(War w) {
        for (Army a : w.sides) {
            for (Mob m : a.alive) {
                if (m.getVehicle() != null) {
                    m.stopRiding();
                }
                m.discard();
            }
        }
        for (Entity e : w.machines) {
            e.ejectPassengers();
            e.discard();
        }
        for (ChunkPos p : w.forced) {
            w.level.setChunkForced(p.x, p.z, false);
        }
        war = null;
    }

    private static int stop(CommandSourceStack src) {
        War w = war;
        if (w == null) {
            src.sendFailure(Component.literal("戦闘はありません。"));
            return 0;
        }
        if (w.endedAt < 0) {
            end(w, null);
        }
        dismiss(w);
        return 1;
    }

    private static int status(CommandSourceStack src) {
        War w = war;
        if (w == null) {
            src.sendFailure(Component.literal("戦闘はありません。"));
            return 0;
        }
        src.sendSuccess(() -> Component.literal(String.format(Locale.ROOT, "%s %d/%d 対 %s %d/%d、%d秒、平均%.1fms、AI予算 %d",
            w.sides[0].name, w.sides[0].alive.size(), w.sides[0].raised, w.sides[1].name, w.sides[1].alive.size(), w.sides[1].raised,
            (w.level.getGameTime() - w.started) / 20, w.msptSamples == 0 ? 0 : w.msptSum / w.msptSamples, w.budget)), false);
        return 1;
    }

    private static void announce(War w, String text) {
        for (ServerPlayer p : w.level.players()) {
            if (p.position().distanceToSqr(w.center) < 512 * 512) {
                p.displayClientMessage(Component.literal(text).withStyle(ChatFormatting.GOLD), false);
            }
        }
    }

    private static int side(Entity e) {
        War w = war;
        if (w == null || !e.getTags().contains(TAG)) {
            return -1;
        }
        return w.sides[0].ids.contains(e.getUUID()) ? 0 : w.sides[1].ids.contains(e.getUUID()) ? 1 : -1;
    }

    @SubscribeEvent
    public static void death(LivingDeathEvent e) {
        int s = side(e.getEntity());
        if (s >= 0) {
            war.sides[s].lost++;
        }
    }

    @SubscribeEvent
    public static void drops(LivingDropsEvent e) {
        if (e.getEntity().getTags().contains(TAG)) {
            e.setCanceled(true);
        }
    }

    @SubscribeEvent
    public static void experience(LivingExperienceDropEvent e) {
        if (e.getEntity().getTags().contains(TAG)) {
            e.setCanceled(true);
        }
    }

    @SubscribeEvent
    public static void stopped(ServerStoppedEvent e) {
        war = null;
    }
}
