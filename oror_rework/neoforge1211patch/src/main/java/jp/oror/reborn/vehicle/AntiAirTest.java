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
import net.minecraft.world.entity.monster.Phantom;
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
 * The CI check of the kingdom's defence against what flies (050): /oror aa test stands a close-in gun (HPJ-11) with its
 * gunner on a stone floor away from the capital, at night, and puts four phantoms in the air 30 to 40 blocks off and
 * 30 up. AA-RESULT says how many it brought down in 45 seconds and how long the first took.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class AntiAirTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Vehicles");
    public static volatile boolean resultLogged;
    private static Run run;

    private static final class Run {
        ServerLevel level;
        long started, firstDown = -1;
        Entity gun;
        final List<Phantom> raiders = new ArrayList<>();
        final List<ChunkPos> forced = new ArrayList<>();
        long dayTime;
    }

    private AntiAirTest() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("aa").requires(s -> s.hasPermission(2))
            .then(Commands.literal("test").executes(c -> start(c.getSource())))));
    }

    private static int start(CommandSourceStack src) {
        if (run != null) {
            return 0;
        }
        ServerLevel level = src.getServer().overworld();
        if (!Sbw.present() || !Sbw.has("hpj_11")) {
            LOG.info("AA-RESULT {\"present\":false}");
            resultLogged = true;
            return 0;
        }
        Run r = new Run();
        r.level = level;
        BlockPos from = BlockPos.containing(src.getPosition());
        BlockPos c = from.offset(-1400, 0, 900);
        for (int dx = -4; dx <= 4; dx++) {
            for (int dz = -4; dz <= 4; dz++) {
                ChunkPos p = new ChunkPos((c.getX() >> 4) + dx, (c.getZ() >> 4) + dz);
                if (level.setChunkForced(p.x, p.z, true)) {
                    r.forced.add(p);
                }
            }
        }
        int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, c.getX(), c.getZ());
        c = new BlockPos(c.getX(), y, c.getZ());
        for (int dx = -5; dx <= 5; dx++) {
            for (int dz = -5; dz <= 5; dz++) {
                level.setBlock(c.offset(dx, -1, dz), Blocks.STONE.defaultBlockState(), 2);
                for (int h = 0; h < 6; h++) {
                    level.setBlock(c.offset(dx, h, dz), Blocks.AIR.defaultBlockState(), 2);
                }
            }
        }
        r.gun = RoyalPilots.deploy(level, Vec3.atBottomCenterOf(c), 0F, "hpj_11", 1, null);
        if (r.gun == null) {
            LOG.info("AA-RESULT {\"present\":true,\"gun\":false}");
            resultLogged = true;
            return 0;
        }
        for (Entity rider : r.gun.getPassengers()) {
            if (rider instanceof Mob m) {
                m.setNoAi(true);              // a turret's gunner, as the garrison posts him
            }
        }
        r.dayTime = level.getDayTime();
        level.setDayTime(18000);
        for (int i = 0; i < 4; i++) {
            Phantom ph = EntityType.PHANTOM.create(level);
            if (ph == null) {
                continue;
            }
            double ang = i * Math.PI / 2;
            ph.moveTo(c.getX() + 0.5 + Math.cos(ang) * (30 + i * 3), c.getY() + 30, c.getZ() + 0.5 + Math.sin(ang) * (30 + i * 3), 0F, 0F);
            ph.setPersistenceRequired();
            level.addFreshEntity(ph);
            r.raiders.add(ph);
        }
        r.started = level.getGameTime();
        run = r;
        LOG.info("AA-START {\"at\":[{},{},{}],\"raiders\":{}}", c.getX(), c.getY(), c.getZ(), r.raiders.size());
        src.sendSuccess(() -> Component.literal("対空試験を開始しました"), true);
        return 1;
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        Run r = run;
        if (r == null) {
            return;
        }
        long t = r.level.getGameTime() - r.started;
        int down = (int) r.raiders.stream().filter(p -> !p.isAlive()).count();
        if (down > 0 && r.firstDown < 0) {
            r.firstDown = t;
        }
        if (t % 100 == 0) {
            LOG.info(String.format(Locale.ROOT, "AA-TRACK {\"t\":%d,\"down\":%d,\"gunAlive\":%b,\"target\":%b,\"nearest\":%.1f}", t, down,
                r.gun.isAlive(), r.gun.getPersistentData().getCompound(RoyalPilots.KEY).hasUUID("Target"),
                r.raiders.stream().filter(Entity::isAlive).mapToDouble(p -> p.distanceTo(r.gun)).min().orElse(-1)));
        }
        if (down == r.raiders.size() || t > 900) {
            LOG.info(String.format(Locale.ROOT, "AA-RESULT {\"present\":true,\"raiders\":%d,\"down\":%d,\"firstDownSeconds\":%.1f,\"seconds\":%.1f,"
                + "\"gunAlive\":%b,\"health\":%.2f}", r.raiders.size(), down, r.firstDown < 0 ? -1 : r.firstDown / 20.0, t / 20.0, r.gun.isAlive(),
                Sbw.health(r.gun)));
            for (Phantom p : r.raiders) {
                if (p.isAlive()) {
                    p.discard();
                }
            }
            for (Entity rider : List.copyOf(r.gun.getPassengers())) {
                rider.discard();
            }
            r.gun.discard();
            r.level.setDayTime(r.dayTime);
            for (ChunkPos p : r.forced) {
                r.level.setChunkForced(p.x, p.z, false);
            }
            run = null;
            resultLogged = true;
        }
    }

    @SubscribeEvent
    public static void stopped(ServerStoppedEvent e) {
        run = null;
    }
}
