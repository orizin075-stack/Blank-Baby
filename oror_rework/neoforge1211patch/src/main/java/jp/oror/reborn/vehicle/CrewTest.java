package jp.oror.reborn.vehicle;

import java.util.ArrayList;
import java.util.List;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.royal.RoyalRegistry;
import jp.oror.reborn.royal.RoyalRole;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (059e) CI check "crew" (/oror crew test), the user: soldiers should get into an empty turret and shoot. A close-in gun
 * of the kingdom's stands empty; a kingdom guard twenty blocks off is fighting (a zombie before him). Within half a
 * minute he must be at the gun (TurretCare: ten seconds empty, then the nearest guard, a fighting one too).
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class CrewTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Vehicles");
    public static volatile boolean resultLogged;
    private static ServerLevel level;
    private static Entity gun;
    private static RoyalMob guard;
    private static Zombie foe;
    private static long started;
    private static final List<ChunkPos> FORCED = new ArrayList<>();

    private CrewTest() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("crew").then(Commands.literal("test")
            .requires(s -> s.hasPermission(2)).executes(c -> start(c.getSource())))));
    }

    private static int start(CommandSourceStack src) {
        ServerLevel lv = src.getServer().overworld();
        if (!Sbw.present() || !Sbw.has("hpj_11")) {
            LOG.info("CREW-RESULT {\"present\":false,\"pass\":true}");
            resultLogged = true;
            return 0;
        }
        BlockPos c = BlockPos.containing(src.getPosition()).offset(-1400, 0, -900);
        for (int dx = -3; dx <= 3; dx++) {
            for (int dz = -3; dz <= 3; dz++) {
                ChunkPos p = new ChunkPos((c.getX() >> 4) + dx, (c.getZ() >> 4) + dz);
                if (lv.setChunkForced(p.x, p.z, true)) {
                    FORCED.add(p);
                }
            }
        }
        int y = lv.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, c.getX(), c.getZ());
        c = new BlockPos(c.getX(), y, c.getZ());
        for (int dx = -6; dx <= 26; dx++) {
            for (int dz = -6; dz <= 6; dz++) {
                lv.setBlock(c.offset(dx, -1, dz), Blocks.STONE.defaultBlockState(), 2);
                for (int h = 0; h < 5; h++) {
                    lv.setBlock(c.offset(dx, h, dz), Blocks.AIR.defaultBlockState(), 2);
                }
            }
        }
        gun = RoyalPilots.deploy(lv, Vec3.atBottomCenterOf(c), 0F, "hpj_11", 0, null);
        guard = RoyalRegistry.TYPES.get(RoyalRole.GUARD).create(lv);
        foe = EntityType.ZOMBIE.create(lv);
        if (gun == null || guard == null || foe == null) {
            LOG.info("CREW-RESULT {\"present\":true,\"made\":false,\"pass\":false}");
            resultLogged = true;
            return 0;
        }
        guard.moveTo(c.getX() + 20.5, c.getY(), c.getZ() + 0.5, 90F, 0F);
        guard.setPersistenceRequired();
        lv.addFreshEntity(guard);
        foe.moveTo(c.getX() + 25.5, c.getY(), c.getZ() + 0.5, -90F, 0F);
        foe.setNoAi(true);
        foe.setPersistenceRequired();
        lv.addFreshEntity(foe);
        guard.setTarget(foe);
        level = lv;
        started = lv.getGameTime();
        return 1;
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        if (level == null) {
            return;
        }
        long t = level.getGameTime() - started;
        if (foe != null && foe.isAlive()) {
            foe.setHealth(foe.getMaxHealth());
            if (guard != null && guard.isAlive() && !guard.isPassenger()) {
                guard.setTarget(foe);
            }
        }
        boolean manned = gun != null && guard != null && guard.getVehicle() == gun;
        if (manned || t > 600) {
            LOG.info("CREW-RESULT {\"present\":true,\"manned\":{},\"seconds\":{},\"gunAlive\":{},\"pass\":{}}", manned,
                String.format(java.util.Locale.ROOT, "%.1f", t / 20.0), gun != null && gun.isAlive(), manned);
            for (Entity x : new Entity[]{guard, foe, gun}) {
                if (x != null) {
                    x.discard();
                }
            }
            for (ChunkPos p : FORCED) {
                level.setChunkForced(p.x, p.z, false);
            }
            FORCED.clear();
            level = null;
            resultLogged = true;
        }
    }
}
