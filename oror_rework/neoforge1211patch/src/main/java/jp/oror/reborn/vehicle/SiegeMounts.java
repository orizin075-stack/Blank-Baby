package jp.oror.reborn.vehicle;

import java.lang.reflect.Method;
import jp.oror.reborn.citadel.CitadelSites;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.EntityTickEvent;

/**
 * (r63) Azazel's air wing flies (the user: "ピリジャーのドラゴンとかきちんと飛んでる？"). In run 193 the siege's dragons and
 * amphitheres, each with a pillager on its back, hung where they had risen, 22 blocks up and 686 from the capital, for the
 * whole test: the siege's steering (r61) leaves a mount that has a target to its own mind, and an Ice and Fire dragon
 * ridden by anyone but a player does not fly by itself. Each mount of the siege (OrorAzazelSiegeAir) is flown here every
 * tick: toward its target (or its rider's), circling it fourteen blocks out and ten up and every ten seconds diving on
 * it, a bite or a claw when it is close; with no target, toward the capital. It keeps at least fourteen blocks over the
 * ground, turns to face where it goes and is held up (no gravity) while it lives in the siege.
 * <p>
 * The air wing gathers far out (run 194: 686 blocks from the capital), where no player is: there the chunks are loaded
 * but nothing in them moves, and the dragons hung in the air unticked for the whole siege (a hippogryph flew 57 blocks
 * and stopped where it left the chunk it was born in). So each mount carries the world with it: a ticket on the chunks
 * around it (three by three, where things move), renewed while it flies, for as long as a siege lasts after the mount
 * was first seen; then it is left to the world as any creature is.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class SiegeMounts {
    public static final String TAG = "OrorAzazelSiegeAir";
    private static final double SPEED = 0.62, CLIMB = 0.4;
    private static final java.util.Map<Class<?>, java.util.Optional<Method>> SET_FLYING = new java.util.concurrent.ConcurrentHashMap<>();

    /** Twelve minutes, the length of a siege (AzazelCapitalSiege). */
    private static final long CARRY = 14400;
    private static final net.minecraft.server.level.TicketType<net.minecraft.world.level.ChunkPos> TICKET =
        net.minecraft.server.level.TicketType.create("oror_siege_air", java.util.Comparator.comparingLong(net.minecraft.world.level.ChunkPos::toLong), 100);

    private SiegeMounts() {
    }

    /** Once a second: every mount of the siege, ticking or not, keeps the chunks around it moving. */
    @SubscribeEvent
    public static void carry(net.neoforged.neoforge.event.tick.LevelTickEvent.Post e) {
        if (!(e.getLevel() instanceof ServerLevel level) || level.getGameTime() % 20 != 0) {
            return;
        }
        for (Entity v : level.getAllEntities()) {
            if (v instanceof Mob m && m.isAlive() && !m.isPassenger() && m.getPersistentData().getBoolean(TAG)) {
                hold(level, m);
            }
        }
    }

    static void hold(ServerLevel level, Mob m) {
        var data = m.getPersistentData();
        long now = level.getGameTime();
        if (!data.contains("OrorSiegeAirSince")) {
            data.putLong("OrorSiegeAirSince", now);
        }
        long since = data.getLong("OrorSiegeAirSince");
        if (now - since > CARRY || now < since) {
            return;
        }
        net.minecraft.world.level.ChunkPos cp = m.chunkPosition();
        level.getChunkSource().addRegionTicket(TICKET, cp, 3, cp);
    }

    @SubscribeEvent
    public static void tick(EntityTickEvent.Post e) {
        Entity v = e.getEntity();
        if (v.level().isClientSide() || !(v instanceof Mob m) || !m.isAlive() || m.isPassenger()
            || !m.getPersistentData().getBoolean(TAG) || !(v.level() instanceof ServerLevel level)) {
            return;
        }
        fly(level, m);
    }

    static LivingEntity target(Mob m) {
        LivingEntity t = m.getTarget();
        if (t == null || !t.isAlive() || t.level() != m.level() || t.distanceToSqr(m) > 256 * 256) {
            t = null;
            for (Entity r : m.getPassengers()) {
                if (r instanceof Mob rm && rm.getTarget() != null && rm.getTarget().isAlive() && rm.getTarget().level() == m.level()
                    && rm.getTarget().distanceToSqr(m) < 256 * 256) {
                    t = rm.getTarget();
                    break;
                }
            }
        }
        return t;
    }

    private static void fly(ServerLevel level, Mob m) {
        long now = level.getGameTime();
        Vec3 pos = m.position();
        LivingEntity target = target(m);
        Vec3 goal;
        boolean dive = false;
        double phase = (m.getUUID().getLeastSignificantBits() & 1023) / 1023.0 * Math.PI * 2;
        if (target != null) {
            double a = now * 0.035 + phase;
            dive = (now + (long) (phase * 100)) % 200 < 50 && pos.distanceTo(target.position()) < 40;
            goal = dive ? target.position().add(0, 1.5, 0)
                : target.position().add(Math.cos(a) * 14, 10, Math.sin(a) * 14);
        } else {
            CitadelSites.Site site = level.dimension() == net.minecraft.world.level.Level.OVERWORLD ? CitadelSites.capital() : null;
            if (site == null) {
                return;
            }
            BlockPos c = site.center();
            // to the capital, each to its own side of it, 60 blocks out from the centre
            goal = new Vec3(c.getX() + 0.5 + Math.cos(phase) * 60, c.getY() + 40, c.getZ() + 0.5 + Math.sin(phase) * 60);
        }
        int ground = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, Mth.floor(pos.x), Mth.floor(pos.z));
        if (!dive) {
            goal = new Vec3(goal.x, Math.max(goal.y, ground + 14), goal.z);
        }
        Vec3 d = goal.subtract(pos);
        Vec3 flat = new Vec3(d.x, 0, d.z);
        double h = flat.length();
        Vec3 want = h > 1e-3 ? flat.scale(Math.min(SPEED, h * 0.08) / h) : Vec3.ZERO;
        double vy = Mth.clamp(d.y * 0.08, -CLIMB, CLIMB);
        if (pos.y < ground + 3 && !dive) {
            vy = CLIMB;
        }
        Vec3 old = m.getDeltaMovement();
        Vec3 vel = new Vec3(old.x * 0.6 + want.x * 0.4, old.y * 0.5 + vy * 0.5, old.z * 0.6 + want.z * 0.4);
        m.setNoGravity(true);
        flying(m);
        m.setDeltaMovement(vel);
        m.move(MoverType.SELF, vel);
        if (h > 0.5) {
            float yaw = (float) (Mth.atan2(d.z, d.x) * (180F / Math.PI)) - 90F;
            float turned = Mth.approachDegrees(m.getYRot(), yaw, 8F);
            m.setYRot(turned);
            m.yBodyRot = turned;
            m.yHeadRot = turned;
        }
        if (target != null && now % 20 == 0 && m.distanceToSqr(target) < 7 * 7) {
            m.doHurtTarget(target);
        }
        m.getPersistentData().putString("OrorSiegeMountMode", target == null ? "capital" : dive ? "dive" : "circle");
    }

    /** Ice and Fire's mounts keep their own "flying" flag; set it so they spread their wings. */
    private static void flying(Mob m) {
        Method f = SET_FLYING.computeIfAbsent(m.getClass(), c -> {
            for (Class<?> k = c; k != null; k = k.getSuperclass()) {
                for (Method x : k.getDeclaredMethods()) {
                    if (x.getName().equals("setFlying") && x.getParameterCount() == 1 && x.getParameterTypes()[0] == boolean.class) {
                        try {
                            x.setAccessible(true);
                            return java.util.Optional.of(x);
                        } catch (RuntimeException ex) {
                            return java.util.Optional.empty();
                        }
                    }
                }
            }
            return java.util.Optional.empty();
        }).orElse(null);
        if (f != null) {
            try {
                f.invoke(m, true);
            } catch (ReflectiveOperationException | RuntimeException ignored) {
            }
        }
    }
}
