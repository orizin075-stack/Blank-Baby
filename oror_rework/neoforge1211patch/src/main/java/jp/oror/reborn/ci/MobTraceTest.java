package jp.oror.reborn.ci;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.TreeSet;
import jp.oror.reborn.mixin.MobGoalSelectorAccess;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.WrappedGoal;
import net.minecraft.world.entity.animal.IronGolem;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.living.LivingDamageEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (053) /oror mobs test: vanilla mobs fight as vanilla mobs do, with OROR loaded (the user found wither skeletons and
 * others behaving oddly). Each of ten hostile mobs, in its own lane, is set on an iron golem that does not move (no AI,
 * two thousand health) eight blocks off, for ten seconds: how near it came, how often it hit, how long it stood still
 * while still out of reach, and which goals were running half-way. MOBS-TRACE {...}, pass if each melee mob closed and
 * hit and each archer hit.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class MobTraceTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Mobs");
    public static volatile boolean resultLogged;
    static final String[] TYPES = {"wither_skeleton", "skeleton", "zombie", "husk", "piglin_brute", "vindicator", "spider", "blaze", "pillager",
        "zombified_piglin"};
    static final java.util.Set<String> RANGED = java.util.Set.of("skeleton", "blaze", "pillager");

    static final class Lane {
        String type;
        Mob mob;
        IronGolem golem;
        double minDist = 99, moved;
        int hits, still;
        double lx, lz;
        List<String> goals = new ArrayList<>();
    }

    private static final class Run {
        ServerLevel level;
        BlockPos at;
        final List<Lane> lanes = new ArrayList<>();
        long started;
    }

    private static Run run;

    private MobTraceTest() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("mobs").then(Commands.literal("test")
            .requires(s -> s.hasPermission(2)).executes(c -> start(c.getSource())))));
    }

    private static int start(CommandSourceStack src) {
        if (run != null) {
            return 0;
        }
        Run r = new Run();
        r.level = src.getServer().overworld();
        BlockPos o = BlockPos.containing(src.getPosition()).offset(-4000, 0, -4000);
        for (int dx = -2; dx <= 9; dx++) {
            for (int dz = -2; dz <= 2; dz++) {
                r.level.setChunkForced((o.getX() >> 4) + dx, (o.getZ() >> 4) + dz, true);
            }
        }
        r.level.getChunk(o);
        int y = Math.max(r.level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, o.getX(), o.getZ()), r.level.getSeaLevel() + 1);
        r.at = new BlockPos(o.getX(), y, o.getZ());
        r.level.setDayTime(18000L);
        for (int dx = -4; dx <= TYPES.length * 12 + 4; dx++) {
            for (int dz = -6; dz <= 14; dz++) {
                r.level.setBlock(r.at.offset(dx, -1, dz), Blocks.STONE.defaultBlockState(), 2);
                for (int h = 0; h < 8; h++) {
                    r.level.setBlock(r.at.offset(dx, h, dz), Blocks.AIR.defaultBlockState(), 2);
                }
            }
            // walls between the lanes, so that each fights its own golem
            if (dx % 12 == 6) {
                for (int dz = -6; dz <= 14; dz++) {
                    for (int h = 0; h < 4; h++) {
                        r.level.setBlock(r.at.offset(dx, h, dz), Blocks.STONE.defaultBlockState(), 2);
                    }
                }
            }
        }
        for (int i = 0; i < TYPES.length; i++) {
            Lane l = new Lane();
            l.type = TYPES[i];
            EntityType<?> type = BuiltInRegistries.ENTITY_TYPE.get(ResourceLocation.withDefaultNamespace(TYPES[i]));
            Entity ent = type.create(r.level);
            if (!(ent instanceof Mob mob)) {
                continue;
            }
            l.mob = mob;
            mob.moveTo(r.at.getX() + i * 12 + 0.5, r.at.getY(), r.at.getZ() + 0.5, 0F, 0F);
            mob.finalizeSpawn(r.level, r.level.getCurrentDifficultyAt(mob.blockPosition()), net.minecraft.world.entity.MobSpawnType.COMMAND, null);
            mob.setPersistenceRequired();
            r.level.addFreshEntity(mob);
            l.golem = EntityType.IRON_GOLEM.create(r.level);
            l.golem.moveTo(r.at.getX() + i * 12 + 0.5, r.at.getY(), r.at.getZ() + 8.5, 180F, 0F);
            l.golem.setNoAi(true);
            l.golem.getAttribute(Attributes.MAX_HEALTH).setBaseValue(2000);
            l.golem.setHealth(2000F);
            r.level.addFreshEntity(l.golem);
            mob.setTarget(l.golem);
            l.lx = mob.getX();
            l.lz = mob.getZ();
            r.lanes.add(l);
        }
        r.started = r.level.getGameTime();
        run = r;
        LOG.info("MOBS-TRACE-START {\"lanes\":{}}", r.lanes.size());
        return 1;
    }

    @SubscribeEvent
    public static void hit(LivingDamageEvent.Post e) {
        Run r = run;
        if (r == null || !(e.getEntity() instanceof IronGolem g)) {
            return;
        }
        for (Lane l : r.lanes) {
            if (l.golem == g && e.getSource().getEntity() == l.mob) {
                l.hits++;
            }
        }
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        Run r = run;
        if (r == null) {
            return;
        }
        long age = r.level.getGameTime() - r.started;
        for (Lane l : r.lanes) {
            Mob m = l.mob;
            if (!m.isAlive()) {
                continue;
            }
            if (age % 10 == 0 && m.getTarget() != l.golem) {
                m.setTarget(l.golem);
            }
            double d = m.distanceTo(l.golem);
            l.minDist = Math.min(l.minDist, d);
            double step = Math.hypot(m.getX() - l.lx, m.getZ() - l.lz);
            l.moved += step;
            if (step < 0.01 && d > 2.8 && !RANGED.contains(l.type)) {
                l.still++;
            }
            l.lx = m.getX();
            l.lz = m.getZ();
            if (age == 100) {
                TreeSet<String> running = new TreeSet<>();
                for (WrappedGoal w : ((MobGoalSelectorAccess) m).oror$getGoals().getAvailableGoals()) {
                    if (w.isRunning()) {
                        running.add(w.getGoal().getClass().getName().replaceAll("^.*\\.", ""));
                    }
                }
                l.goals.addAll(running);
            }
        }
        if (age < 200) {
            return;
        }
        run = null;
        Map<String, String> out = new LinkedHashMap<>();
        boolean pass = true;
        for (Lane l : r.lanes) {
            boolean ok = RANGED.contains(l.type) ? l.hits >= 1 : l.hits >= 2 && l.minDist < 3.0;
            pass &= ok;
            out.put(l.type, String.format(Locale.ROOT, "{\"hits\":%d,\"minDist\":%.1f,\"moved\":%.1f,\"stillTicks\":%d,\"alive\":%b,\"ok\":%b,\"goals\":%s}",
                l.hits, l.minDist, l.moved, l.still, l.mob.isAlive(), ok, l.goals.stream().map(s -> "\"" + s + "\"").toList()));
        }
        StringBuilder b = new StringBuilder("{");
        out.forEach((k, v) -> b.append(b.length() > 1 ? "," : "").append('"').append(k).append("\":").append(v));
        b.append(",\"pass\":").append(pass).append('}');
        LOG.info("MOBS-TRACE {}", b);
        for (Entity x : r.level.getEntities((Entity) null, new AABB(r.at).inflate(140, 20, 30), x -> !(x instanceof Player))) {
            x.discard();
        }
        for (int dx = -2; dx <= 9; dx++) {
            for (int dz = -2; dz <= 2; dz++) {
                r.level.setChunkForced((r.at.getX() >> 4) + dx, (r.at.getZ() >> 4) + dz, false);
            }
        }
        resultLogged = true;
    }
}
