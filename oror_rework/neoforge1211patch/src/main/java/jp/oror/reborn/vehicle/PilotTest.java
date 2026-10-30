package jp.oror.reborn.vehicle;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.server.ServerStoppedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * /oror pilots test: a flight and drive check on a dedicated server. 800 blocks east of the caller it lays a stone runway,
 * parks a crewed ground-attack aircraft at its west end and a crewed tank beside it, and stands two still pillagers as
 * targets (one 160 blocks down the runway for the aircraft, one 60 blocks off for the tank). The aircraft should take
 * off, attack, and once its target is gone (killed, or taken away after 90 seconds) fly back and land; the tank should
 * drive up and fire. Every change of mode is logged with its time, and FLIGHT-RESULT sums it up.
 * /oror pilots status lists the crewed vehicles within 300 blocks.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class PilotTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Vehicles");
    private static Run run;

    private static final class Run {
        ServerLevel level;
        long started;
        Entity plane, tank;
        Mob planeTarget, tankTarget;
        String lastMode = "";
        final List<String> modes = new ArrayList<>();
        final List<ChunkPos> forced = new ArrayList<>();
        double tankClosest = Double.MAX_VALUE;
        boolean targetGone;
    }

    private PilotTest() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("pilots").requires(s -> s.hasPermission(2))
            .then(Commands.literal("test").executes(c -> start(c.getSource())))
            .then(Commands.literal("status").executes(c -> {
                ServerLevel level = c.getSource().getLevel();
                List<Entity> list = RoyalPilots.near(level, c.getSource().getPosition(), 300);
                c.getSource().sendSuccess(() -> Component.literal(list.isEmpty() ? "近くに王国の車両はありません。"
                    : String.join("\n", list.stream().map(RoyalPilots::report).toList())), false);
                return list.size();
            }))));
    }

    private static int start(CommandSourceStack src) {
        if (run != null || !Sbw.present()) {
            src.sendFailure(Component.literal(run != null ? "試験中です。" : "Superb Warfareがありません。"));
            return 0;
        }
        ServerLevel level = src.getLevel();
        Run r = new Run();
        r.level = level;
        BlockPos origin = BlockPos.containing(src.getPosition()).offset(800, 0, 0);
        for (int dx = -12; dx <= 20; dx++) {
            for (int dz = -9; dz <= 9; dz++) {
                ChunkPos p = new ChunkPos((origin.getX() >> 4) + dx, (origin.getZ() >> 4) + dz);
                if (level.setChunkForced(p.x, p.z, true)) {
                    r.forced.add(p);
                }
            }
        }
        int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, origin.getX(), origin.getZ());
        // runway: 230 x 9 of stone, cleared 14 blocks up, heading east (yaw -90)
        for (int x = -10; x < 220; x++) {
            for (int z = -4; z <= 4; z++) {
                level.setBlock(new BlockPos(origin.getX() + x, y - 1, origin.getZ() + z), Blocks.SMOOTH_STONE.defaultBlockState(), 2);
                for (int h = 0; h < 14; h++) {
                    level.setBlock(new BlockPos(origin.getX() + x, y + h, origin.getZ() + z), Blocks.AIR.defaultBlockState(), 2);
                }
            }
        }
        Vec3 start = new Vec3(origin.getX() + 0.5, y, origin.getZ() + 0.5);
        r.plane = RoyalPilots.deploy(level, start, -90F, Sbw.has("a_10a") ? "a_10a" : "j_16", 1, null);
        Vec3 tankAt = start.add(0, 0, 30);
        int ty = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, (int) tankAt.x, (int) tankAt.z);
        r.tank = RoyalPilots.deploy(level, new Vec3(tankAt.x, ty, tankAt.z), -90F, "m_1a_2", 2, null);
        r.planeTarget = target(level, start.add(160, 0, 0));
        r.tankTarget = target(level, tankAt.add(60, 0, 8));
        r.started = level.getGameTime();
        run = r;
        LOG.info("FLIGHT-START {\"runway\":[{},{},{}],\"plane\":{},\"tank\":{}}", origin.getX(), y, origin.getZ(), r.plane != null, r.tank != null);
        src.sendSuccess(() -> Component.literal("飛行・走行試験を開始しました（" + origin.getX() + ", " + y + ", " + origin.getZ() + "）"), false);
        return 1;
    }

    private static Mob target(ServerLevel level, Vec3 at) {
        Mob m = EntityType.PILLAGER.create(level);
        if (m == null) {
            return null;
        }
        int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, (int) at.x, (int) at.z);
        m.moveTo(at.x, y, at.z, 90F, 0F);
        m.setNoAi(true);
        m.setPersistenceRequired();
        m.addTag("oror_pilot_test_target");
        level.addFreshEntity(m);
        return m;
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        Run r = run;
        if (r == null) {
            return;
        }
        long t = r.level.getGameTime() - r.started;
        if (r.plane != null) {
            String mode = r.plane.getPersistentData().getCompound("OrorPilot").getString("Mode");
            if (!mode.equals(r.lastMode)) {
                r.modes.add("[" + t + ",\"" + mode + "\"," + (int) r.plane.getY() + "]");
                r.lastMode = mode;
            }
        }
        if (r.tank != null && r.tankTarget != null) {
            r.tankClosest = Math.min(r.tankClosest, r.tank.distanceTo(r.tankTarget));
        }
        if (!r.targetGone && r.planeTarget != null && (!r.planeTarget.isAlive() || t > 1800)) {
            r.targetGone = true;
            r.modes.add("[" + t + ",\"target-gone:" + (r.planeTarget.isAlive() ? "removed" : "killed") + "\",0]");
            r.planeTarget.discard();
        }
        boolean landed = r.plane != null && r.plane.getPersistentData().getCompound("OrorPilot").getBoolean("Landed")
            && r.lastMode.equals("parked");
        if (landed || t > 7200 || r.plane == null || !r.plane.isAlive()) {
            String line = String.format(Locale.ROOT, "{\"seconds\":%.1f,\"plane\":%s,\"modes\":[%s],\"tank\":%s,\"tankClosest\":%.1f,"
                    + "\"tankTargetHealth\":%.1f,\"planeTarget\":\"%s\"}",
                t / 20.0, r.plane == null ? "null" : RoyalPilots.report(r.plane), String.join(",", r.modes),
                r.tank == null ? "null" : RoyalPilots.report(r.tank), r.tankClosest,
                r.tankTarget == null ? -1F : r.tankTarget.isAlive() ? r.tankTarget.getHealth() : 0F,
                r.planeTarget == null ? "none" : r.planeTarget.isAlive() ? "alive" : "gone");
            LOG.info("FLIGHT-RESULT {}", line);
            for (Entity x : new Entity[]{r.plane, r.tank, r.planeTarget, r.tankTarget}) {
                if (x != null && x.isAlive()) {
                    x.getPassengers().forEach(Entity::discard);
                    x.discard();
                }
            }
            for (ChunkPos p : r.forced) {
                r.level.setChunkForced(p.x, p.z, false);
            }
            run = null;
        }
    }

    @SubscribeEvent
    public static void stopped(ServerStoppedEvent e) {
        run = null;
    }
}
