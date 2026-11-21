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
            sturdy(m);
        }
        long since = data.getLong("OrorSiegeAirSince");
        if (now - since > CARRY || now < since) {
            return;
        }
        net.minecraft.world.level.ChunkPos cp = m.chunkPosition();
        level.getChunkSource().addRegionTicket(TICKET, cp, 3, cp);
    }

    /**
     * (run 203) The air wing fell before it was a wing: all eight mounts down within fifty seconds of rising (a fire dragon
     * in fifteen), six hundred blocks out, to the kingdom's guards and mages there. A mount of Azazel's siege has at
     * least {@value #STURDY} health, so it reaches the capital and the fight is in the capital's sky.
     */
    static final double STURDY = 400;
    private static final net.minecraft.resources.ResourceLocation STURDY_ID =
        net.minecraft.resources.ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "siege_air_sturdy");

    static void sturdy(Mob m) {
        var hp = m.getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.MAX_HEALTH);
        // a modifier, not the base: Ice and Fire sets a dragon's base health again as it grows
        if (hp != null && hp.getValue() < STURDY && hp.getModifier(STURDY_ID) == null) {
            hp.addPermanentModifier(new net.minecraft.world.entity.ai.attributes.AttributeModifier(STURDY_ID, STURDY - hp.getValue(),
                net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.ADD_VALUE));
            m.setHealth(m.getMaxHealth());
        }
    }

    /** What brings a mount of the siege down, and when, for the next look. */
    @SubscribeEvent
    public static void fell(net.neoforged.neoforge.event.entity.living.LivingDeathEvent e) {
        if (!(e.getEntity() instanceof Mob m) || m.level().isClientSide() || !m.getPersistentData().getBoolean(TAG)) {
            return;
        }
        var src = e.getSource();
        Entity by = src.getEntity();
        long since = m.getPersistentData().getLong("OrorSiegeAirSince");
        org.slf4j.LoggerFactory.getLogger("OROR Siege").info(
            "SIEGE-FELL {\"mount\":\"{}\",\"max\":{},\"seconds\":{},\"source\":\"{}\",\"by\":\"{}\",\"direct\":\"{}\"}",
            net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.getKey(m.getType()).getPath(), (int) m.getMaxHealth(),
            since > 0 ? (m.level().getGameTime() - since) / 20 : -1, src.getMsgId(),
            by == null ? "none" : net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.getKey(by.getType()).getPath(),
            src.getDirectEntity() == null ? "none" : net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.getKey(src.getDirectEntity().getType()).getPath());
    }

    @SubscribeEvent
    public static void tick(EntityTickEvent.Post e) {
        Entity v = e.getEntity();
        if (v.level().isClientSide() || !(v instanceof Mob m) || !m.isAlive() || m.isPassenger()
            || !m.getPersistentData().getBoolean(TAG) || !(v.level() instanceof ServerLevel level)) {
            return;
        }
        if (modelDead(m)) {
            // a fallen dragon's body falls, and lies where it fell
            m.setNoGravity(false);
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

    /**
     * (run 200) The riders came off: of eight mounts only three kept their pillager or vindicator, the fire dragons'
     * riders gone within ten seconds of the rising, far from the capital and before any fight. The air wing is not the
     * air wing without its riders, so while rider and mount both live in the same world, a rider of the siege stays on
     * its mount (what took it off is told once per mount, for the next look). A rider that dies, a mount that dies, and
     * anything leaving the world, still get off.
     */
    private static final java.util.Set<java.util.UUID> TOLD = java.util.concurrent.ConcurrentHashMap.newKeySet();

    @SubscribeEvent
    public static void keepRider(net.neoforged.neoforge.event.entity.EntityMountEvent e) {
        if (!e.isDismounting() || e.getLevel().isClientSide() || !(e.getEntityBeingMounted() instanceof Mob mount)
            || !mount.getPersistentData().getBoolean(TAG)) {
            return;
        }
        Entity rider = e.getEntityMounting();
        // only the siege's own riders (its illagers): a defender a dragon has taken in its mouth is let go as before (run 202);
        // and a dragon that falls (Ice and Fire's dead dragon stays as a body, tickDeath) lets its rider down
        if (!(rider instanceof net.minecraft.world.entity.raid.Raider) || !rider.isAlive() || rider.isRemoved()
            || !mount.isAlive() || mount.isRemoved() || mount.isDeadOrDying() || mount.deathTime > 0 || modelDead(mount)
            || rider.level() != mount.level()) {
            return;
        }
        if (TOLD.add(mount.getUUID())) {
            StringBuilder why = new StringBuilder();
            int n = 0;
            for (StackTraceElement f : Thread.currentThread().getStackTrace()) {
                String c = f.getClassName();
                if (c.startsWith("java.") || c.startsWith("net.neoforged.bus") || c.contains("SiegeMounts") || c.contains("EventHooks")
                    || c.startsWith("jdk.") || c.contains("$$Lambda")) {
                    continue;
                }
                if (why.length() > 0) {
                    why.append(" < ");
                }
                why.append(c.substring(c.lastIndexOf('.') + 1)).append('.').append(f.getMethodName());
                if (++n >= 6) {
                    break;
                }
            }
            org.slf4j.LoggerFactory.getLogger("OROR Siege").info("SIEGE-DISMOUNT {\"mount\":\"{}\",\"rider\":\"{}\",\"kept\":true,\"by\":\"{}\"}",
                net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.getKey(mount.getType()).getPath(),
                net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.getKey(rider.getType()).getPath(), why);
        }
        e.setCanceled(true);
    }

    private static final java.util.Map<Class<?>, java.util.Optional<Method>> MODEL_DEAD = new java.util.concurrent.ConcurrentHashMap<>();

    /** Ice and Fire's dragon, dead, lies as a body that is still "alive" to the game (isModelDead). */
    private static boolean modelDead(Mob m) {
        Method f = MODEL_DEAD.computeIfAbsent(m.getClass(), c -> {
            try {
                Method x = c.getMethod("isModelDead");
                return x.getReturnType() == boolean.class ? java.util.Optional.of(x) : java.util.Optional.empty();
            } catch (ReflectiveOperationException | RuntimeException ex) {
                return java.util.Optional.empty();
            }
        }).orElse(null);
        if (f == null) {
            return false;
        }
        try {
            return (boolean) f.invoke(m);
        } catch (ReflectiveOperationException | RuntimeException ex) {
            return false;
        }
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
