package jp.oror.reborn.vehicle;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.TreeSet;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.royal.RoyalRegistry;
import jp.oror.reborn.royal.RoyalRole;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Husk;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.entity.living.LivingDamageEvent;
import net.neoforged.neoforge.event.server.ServerStoppedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (059g) CI check "gunposts" (/oror gunposts test), the user: "設置してる砲台とかもきちんと乗り込んで操作できてるか見てみて".
 * The capital's walls, batteries, casemates, redoubts and anti-aircraft posts stand five kinds of gun (garrison.json:
 * HPJ-11, Mle 1934, BL-132, Mk 42, TOW), each brought out and manned by its own guard the first time he acts; the CI
 * checks so far tried only the HPJ-11 (crew, aa). Here each of the five gets a post of its own on a stone floor high
 * above the ground, far from the capital, with its guard posted to it exactly as the garrison posts him (CitadelGarrison:
 * the gun's id, one seat, its facing, a still gun, the post's place), and a husk (no mind, made very hard to kill) 34
 * blocks off, 30 degrees right of where the gun faces, so that the gun must turn to it. In 45 seconds: was the gun
 * brought out, did its guard get in, did it turn, how many rounds left its muzzle and how many struck the husk.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class GunPostTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Vehicles");
    /** (CI 44: a gunner left his own mind fired the four no more than one without: GunLayer pulls their triggers now) */
    private static final String[] KINDS = {"hpj_11", "mle_1934", "bl_132", "mk_42", "tow"};
    private static final int LANE = 64, RANGE = 34, OFF = 30;
    private static final long TIME = 900;
    public static volatile boolean resultLogged;
    private static Run run;

    private static final class Lane {
        String kind;
        BlockPos post;
        RoyalMob guard;
        Entity gun;
        Husk foe;
        long mannedAt = -1, firstShot = -1, firstHit = -1;
        int shots, hits, gunHits, kills;
        float damage, yaw0 = Float.NaN, maxTurn;
        final TreeSet<String> shotTypes = new TreeSet<>();
        final TreeSet<String> hitBy = new TreeSet<>();
    }

    private static final class Run {
        ServerLevel level;
        long started;
        final List<Lane> lanes = new ArrayList<>();
        final List<ChunkPos> forced = new ArrayList<>();
    }

    private GunPostTest() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("gunposts").requires(s -> s.hasPermission(2))
            .then(Commands.literal("test").executes(c -> start(c.getSource())))));
    }

    private static int start(CommandSourceStack src) {
        if (run != null) {
            return 0;
        }
        try {
            return begin(src);
        } catch (RuntimeException ex) {
            LOG.warn("GUNPOST-TEST failed to start", ex);
            LOG.info("GUNPOST-RESULT {\"present\":true,\"error\":\"" + ex.toString().replace('"', '\'') + "\",\"pass\":false}");
            resultLogged = true;
            return 0;
        }
    }

    private static int begin(CommandSourceStack src) {
        ServerLevel level = src.getServer().overworld();
        if (!Sbw.present()) {
            LOG.info("GUNPOST-RESULT {\"present\":false,\"pass\":true}");
            resultLogged = true;
            return 0;
        }
        Run r = new Run();
        r.level = level;
        BlockPos c = BlockPos.containing(src.getPosition()).offset(-2600, 0, 2600);
        int x0 = c.getX() - 30, x1 = c.getX() + LANE * (KINDS.length - 1) + 12, z0 = c.getZ() - 12, z1 = c.getZ() + RANGE + 12;
        for (int cx = x0 >> 4; cx <= x1 >> 4; cx++) {
            for (int cz = z0 >> 4; cz <= z1 >> 4; cz++) {
                if (level.setChunkForced(cx, cz, true)) {
                    r.forced.add(new ChunkPos(cx, cz));
                }
            }
        }
        // the floor well above whatever grows or stands there (a stone deck in the air: nothing in the line of fire)
        int high = level.getMinBuildHeight();
        for (int x = x0; x <= x1; x += 8) {
            for (int z = z0; z <= z1; z += 8) {
                high = Math.max(high, level.getHeight(Heightmap.Types.MOTION_BLOCKING, x, z));
            }
        }
        int floorY = Math.min(high + 8, level.getMaxBuildHeight() - 40);
        float bearing = OFF;
        double fx = -Mth.sin(bearing * Mth.DEG_TO_RAD), fz = Mth.cos(bearing * Mth.DEG_TO_RAD);
        for (int i = 0; i < KINDS.length; i++) {
            Lane l = new Lane();
            l.kind = KINDS[i];
            l.post = new BlockPos(c.getX() + i * LANE, floorY + 1, c.getZ());
            for (int dx = -RANGE + 10; dx <= 8; dx++) {
                for (int dz = -8; dz <= RANGE + 4; dz++) {
                    level.setBlock(l.post.offset(dx, -1, dz), Blocks.STONE.defaultBlockState(), 2);
                }
            }
            r.lanes.add(l);
            if (!Sbw.has(id(l))) {
                continue;
            }
            // (CI 47) the kingdom's depot beside the gun, as at the capital's posts: the TOW's missiles come from it
            Supply.placeDepot(level, l.post.offset(-3, 0, -3), id(l));
            // the guard posted to the gun as the capital's garrison posts him
            RoyalMob g = RoyalRegistry.TYPES.get(RoyalRole.GUARD).create(level);
            if (g != null) {
                g.getPersistentData().putString("OrorMotor", id(l));
                g.getPersistentData().putInt("OrorMotorSeats", 1);
                g.getPersistentData().putFloat("OrorMotorYaw", 0F);
                g.getPersistentData().putBoolean("OrorMotorStill", true);
                g.getPersistentData().putLong("OrorMotorAt", l.post.asLong());
                g.moveTo(l.post.getX() + 0.5, l.post.getY(), l.post.getZ() + 0.5, 0F, 0F);
                g.setYHeadRot(0F);
                g.setYBodyRot(0F);
                g.setPersistenceRequired();
                if (level.addFreshEntity(g)) {
                    l.guard = g;
                }
            }
            l.foe = foe(level, l, fx, fz);
        }
        r.started = level.getGameTime();
        run = r;
        LOG.info("GUNPOST-START {\"at\":[{},{},{}],\"kinds\":{},\"guards\":{}}", c.getX(), floorY + 1, c.getZ(), KINDS.length,
            r.lanes.stream().filter(l -> l.guard != null).count());
        return 1;
    }

    /** The lane's husk: no mind, two thousand health kept topped up, 34 blocks off 30 degrees right of the gun's facing. */
    private static Husk foe(ServerLevel level, Lane l, double fx, double fz) {
        Husk h = EntityType.HUSK.create(level);
        if (h == null) {
            return null;
        }
        h.moveTo(l.post.getX() + 0.5 + fx * RANGE, l.post.getY(), l.post.getZ() + 0.5 + fz * RANGE, 180F, 0F);
        h.setNoAi(true);
        h.setPersistenceRequired();
        var max = h.getAttribute(Attributes.MAX_HEALTH);
        if (max != null) {
            max.setBaseValue(2000.0);
        }
        h.setHealth(h.getMaxHealth());
        return level.addFreshEntity(h) ? h : null;
    }

    private static Lane laneOf(Entity e) {
        Run r = run;
        if (r == null) {
            return null;
        }
        for (Lane l : r.lanes) {
            if (l.foe == e) {
                return l;
            }
        }
        return null;
    }

    /** A round leaving a gun: whatever of Superb Warfare's (not a living thing) comes into the world by a lane's gun. */
    @SubscribeEvent
    public static void joined(EntityJoinLevelEvent e) {
        Run r = run;
        if (r == null || e.getLevel() != r.level || e.getEntity() instanceof LivingEntity) {
            return;
        }
        ResourceLocation id = BuiltInRegistries.ENTITY_TYPE.getKey(e.getEntity().getType());
        if (!"superbwarfare".equals(id.getNamespace())) {
            return;
        }
        for (Lane l : r.lanes) {
            if (l.gun != null && l.gun != e.getEntity() && l.gun.distanceToSqr(e.getEntity()) < 14 * 14) {
                l.shots++;
                if (l.firstShot < 0) {
                    l.firstShot = r.level.getGameTime() - r.started;
                }
                if (l.shotTypes.size() < 6) {
                    l.shotTypes.add(id.getPath());
                }
                return;
            }
        }
    }

    @SubscribeEvent
    public static void hurt(LivingDamageEvent.Post e) {
        Lane l = laneOf(e.getEntity());
        if (l == null) {
            return;
        }
        Run r = run;
        Entity by = e.getSource().getEntity(), direct = e.getSource().getDirectEntity();
        boolean gun = l.gun != null && (by == l.gun || direct == l.gun || l.gun.getPassengers().contains(by)
            || direct != null && "superbwarfare".equals(BuiltInRegistries.ENTITY_TYPE.getKey(direct.getType()).getNamespace()));
        l.hits++;
        l.damage += e.getNewDamage();
        if (gun) {
            l.gunHits++;
            if (l.firstHit < 0) {
                l.firstHit = r.level.getGameTime() - r.started;
            }
        }
        if (l.hitBy.size() < 6) {
            l.hitBy.add(e.getSource().getMsgId() + (direct != null ? "/" + BuiltInRegistries.ENTITY_TYPE.getKey(direct.getType()).getPath() : ""));
        }
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        Run r = run;
        if (r == null) {
            return;
        }
        long t = r.level.getGameTime() - r.started;
        double fx = -Mth.sin(OFF * Mth.DEG_TO_RAD), fz = Mth.cos(OFF * Mth.DEG_TO_RAD);
        for (Lane l : r.lanes) {
            if (l.guard != null && l.guard.getVehicle() != null) {
                l.gun = l.guard.getVehicle();
                if (l.mannedAt < 0) {
                    l.mannedAt = t;
                }
            } else if (l.gun == null && t % 20 == 3) {
                for (Entity v : RoyalPilots.near(r.level, net.minecraft.world.phys.Vec3.atBottomCenterOf(l.post), 4)) {
                    if (BuiltInRegistries.ENTITY_TYPE.getKey(v.getType()).getPath().equals(id(l))) {
                        l.gun = v;
                    }
                }
            }
            if (l.kind.endsWith("+ai") && l.guard != null && l.guard.isPassenger() && l.guard.isNoAi()) {
                l.guard.setNoAi(false);
            }
            if (l.gun != null && l.gun.isAlive()) {
                float yaw = turret(l.gun);
                if (Float.isNaN(l.yaw0)) {
                    l.yaw0 = yaw;
                }
                l.maxTurn = Math.max(l.maxTurn, Math.abs(Mth.wrapDegrees(yaw - l.yaw0)));
            }
            if (l.foe != null) {
                if (!l.foe.isAlive()) {
                    l.kills++;
                    l.foe = foe(r.level, l, fx, fz);
                } else if (l.foe.getHealth() < l.foe.getMaxHealth()) {
                    l.foe.setHealth(l.foe.getMaxHealth());
                }
            }
        }
        if (t % 200 == 100) {
            StringBuilder s = new StringBuilder("GUNPOST-TRACK {\"t\":").append(t);
            for (Lane l : r.lanes) {
                s.append(String.format(Locale.ROOT, ",\"%s\":\"gun=%b manned=%b turn=%.0f shots=%d hits=%d\"", l.kind, l.gun != null,
                    l.mannedAt >= 0, l.maxTurn, l.shots, l.gunHits));
            }
            LOG.info(s.append('}').toString());
        }
        if (t >= TIME || t > 300 && r.lanes.stream().allMatch(l -> l.gunHits >= 3 || !Sbw.has(id(l)))) {
            finish(r, t);
        }
    }

    private static String id(Lane l) {
        return l.kind.replace("+ai", "");
    }

    /** The gun's turret heading where Superb Warfare keeps one, else the gun's own. */
    private static float turret(Entity v) {
        Object y = Sbw.call(v, "getTurretYRot");
        return y instanceof Number n ? n.floatValue() : v.getYRot();
    }

    private static void finish(Run r, long t) {
        StringBuilder s = new StringBuilder(String.format(Locale.ROOT, "GUNPOST-RESULT {\"present\":true,\"seconds\":%.1f,\"lanes\":[", t / 20.0));
        boolean pass = true;
        for (int i = 0; i < r.lanes.size(); i++) {
            Lane l = r.lanes.get(i);
            boolean has = Sbw.has(id(l));
            Entity v = l.gun;
            boolean manned = l.mannedAt >= 0;
            boolean noAi = l.guard != null && l.guard.isNoAi();
            boolean aimed = v != null && v.getPersistentData().getCompound(RoyalPilots.KEY).hasUUID("Target");
            pass &= !has || l.kind.endsWith("+ai") || v != null && manned && l.gunHits > 0;
            s.append(i == 0 ? "" : ",").append(String.format(Locale.ROOT,
                "{\"kind\":\"%s\",\"registered\":%b,\"brought\":%b,\"engine\":\"%s\",\"manned\":%b,\"mannedSeconds\":%.1f,\"gunnerNoAi\":%b,"
                    + "\"stillAboard\":%b,\"targeted\":%b,\"turned\":%.1f,\"shots\":%d,\"firstShot\":%.1f,\"hits\":%d,\"gunHits\":%d,"
                    + "\"firstHit\":%.1f,\"damage\":%.0f,\"kills\":%d,\"health\":%.2f,\"layerFired\":%d,\"layWhy\":\"%s\",\"shotTypes\":\"%s\",\"hitBy\":\"%s\"}",
                l.kind, has, v != null, v == null ? "" : Sbw.engine(v), manned, manned ? l.mannedAt / 20.0 : -1, noAi,
                l.guard != null && v != null && l.guard.getVehicle() == v, aimed, l.maxTurn, l.shots, l.firstShot < 0 ? -1 : l.firstShot / 20.0,
                l.hits, l.gunHits, l.firstHit < 0 ? -1 : l.firstHit / 20.0, l.damage, l.kills, v == null ? 0F : Sbw.health(v),
                v == null ? 0 : v.getPersistentData().getCompound(RoyalPilots.KEY).getInt("Fired"),
                v == null ? "" : (v.getPersistentData().getCompound(RoyalPilots.KEY).getString("LayWhy")
                    + (l.guard != null && l.guard.getVehicle() == v ? " | " + GunLayer.state(v, l.guard) : "")).replace('"', '\''),
                String.join(" ", l.shotTypes), String.join(" ", l.hitBy).replace('"', '\'')));
        }
        s.append("],\"pass\":").append(pass).append('}');
        LOG.info(s.toString());
        for (Lane l : r.lanes) {
            if (l.gun != null) {
                for (Entity rider : List.copyOf(l.gun.getPassengers())) {
                    rider.discard();
                }
                l.gun.discard();
            }
            for (Entity x : new Entity[]{l.guard, l.foe}) {
                if (x != null && !x.isRemoved()) {
                    x.discard();
                }
            }
        }
        for (ChunkPos p : r.forced) {
            r.level.setChunkForced(p.x, p.z, false);
        }
        run = null;
        resultLogged = true;
    }

    @SubscribeEvent
    public static void stopped(ServerStoppedEvent e) {
        run = null;
    }
}
