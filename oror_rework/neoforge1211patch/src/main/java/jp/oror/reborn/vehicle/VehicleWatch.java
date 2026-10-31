package jp.oror.reborn.vehicle;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;
import java.util.Locale;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingDeathEvent;
import net.neoforged.neoforge.event.level.ExplosionEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * What happens to the crewed vehicles, for the logs: every loss of health with what was about it (explosions of the
 * last two seconds, projectiles nearby, its speed, whether it was against a block, how high above the ground), every
 * crew member lost and how, and a vehicle's end. The aircraft and tank tests read these to find what destroys them.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class VehicleWatch {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Vehicles");
    private record Blast(Vec3 at, long time, String by) {
    }

    private static final Deque<Blast> BLASTS = new ArrayDeque<>();
    private static int lines;

    private VehicleWatch() {
    }

    @SubscribeEvent
    public static void blast(ExplosionEvent.Detonate e) {
        if (e.getLevel().isClientSide) {
            return;
        }
        Entity by = e.getExplosion().getDirectSourceEntity();
        synchronized (BLASTS) {
            BLASTS.addLast(new Blast(e.getExplosion().center(), e.getLevel().getGameTime(),
                by == null ? "none" : BuiltInRegistries.ENTITY_TYPE.getKey(by.getType()).getPath()));
            while (BLASTS.size() > 256) {
                BLASTS.removeFirst();
            }
        }
    }

    @SubscribeEvent
    public static void crewDeath(LivingDeathEvent e) {
        LivingEntity dead = e.getEntity();
        Entity v = dead.getVehicle();
        if (v != null && v.getTags().contains(RoyalPilots.CREWED) && events()) {
            Entity by = e.getSource().getEntity(), direct = e.getSource().getDirectEntity();
            LOG.info("VEHICLE-CREW-DEATH {\"vehicle\":\"{}\",\"cause\":\"{}\",\"by\":\"{}\",\"direct\":\"{}\",\"y\":{}}",
                id(v), e.getSource().getMsgId(), by == null ? "none" : id(by), direct == null ? "none" : id(direct), (int) dead.getY());
        }
    }

    /** Called every tick for a crewed vehicle (RoyalPilots.tick), alive or wrecked. */
    static void watch(Entity v, CompoundTag p) {
        float health = Sbw.health(v);
        float before = p.contains("LastHealth") ? p.getFloat("LastHealth") : health;
        int crew = v.getPassengers().size();
        int crewBefore = p.contains("LastCrew") ? p.getInt("LastCrew") : crew;
        p.putFloat("LastHealth", health);
        p.putInt("LastCrew", crew);
        if (crew < crewBefore && events()) {
            LOG.info("VEHICLE-CREW-LOST {\"vehicle\":\"{}\",\"mode\":\"{}\",\"crew\":{},\"was\":{},\"y\":{}}", id(v), p.getString("Mode"), crew, crewBefore,
                (int) v.getY());
        }
        int hurtLines = p.getInt("HurtLines");
        if (health < before - 0.01F && hurtLines < 30 && budget()) {
            p.putInt("HurtLines", hurtLines + 1);
            Level level = v.level();
            long now = level.getGameTime();
            List<String> near = new ArrayList<>();
            synchronized (BLASTS) {
                for (Blast b : BLASTS) {
                    if (now - b.time() <= 40 && b.at().distanceTo(v.position()) < 16) {
                        near.add(String.format(Locale.ROOT, "\"%s@%.0f\"", b.by(), b.at().distanceTo(v.position())));
                    }
                }
            }
            int projectiles = level.getEntitiesOfClass(Projectile.class, v.getBoundingBox().inflate(6)).size();
            Vec3 m = v.getDeltaMovement();
            int ground = level.getHeight(net.minecraft.world.level.levelgen.Heightmap.Types.MOTION_BLOCKING, (int) Math.floor(v.getX()), (int) Math.floor(v.getZ()));
            LOG.info(String.format(Locale.ROOT, "VEHICLE-HURT {\"vehicle\":\"%s\",\"mode\":\"%s\",\"health\":%.3f,\"lost\":%.3f,\"y\":%.1f,\"aboveGround\":%.1f,"
                    + "\"speed\":%.2f,\"vy\":%.2f,\"onGround\":%b,\"against\":%b,\"landedHard\":%b,\"inWater\":%b,\"crew\":%d,\"blasts\":[%s],\"projectiles\":%d}",
                id(v), p.getString("Mode"), health, before - health, v.getY(), v.getY() - ground, m.length(), m.y, v.onGround(), v.horizontalCollision,
                v.verticalCollision && m.y < -0.3, v.isInWater(), crew, String.join(",", near), projectiles));
        }
        if (!p.getBoolean("EndLogged") && (health <= 0F || Sbw.wreck(v) || !v.isAlive())) {
            p.putBoolean("EndLogged", true);
            LOG.info("VEHICLE-END {}", RoyalPilots.report(v));
        }
        double home = p.getDouble("RunwayY");
        if (!"AIRCRAFT".equals(Sbw.engine(v)) && !p.getBoolean("FellLogged") && v.getY() < home - 3) {
            p.putBoolean("FellLogged", true);
            List<String> near = new ArrayList<>();
            long now = v.level().getGameTime();
            synchronized (BLASTS) {
                for (Blast b : BLASTS) {
                    if (now - b.time() <= 200 && b.at().distanceTo(v.position()) < 12) {
                        near.add(String.format(Locale.ROOT, "\"%s@%.0f,%ds\"", b.by(), b.at().distanceTo(v.position()), (now - b.time()) / 20));
                    }
                }
            }
            LOG.info("VEHICLE-FELL {\"vehicle\":\"{}\",\"y\":{},\"post\":{},\"blastsLast10s\":[{}]}", id(v), (int) v.getY(), (int) home, String.join(",", near));
        }
    }

    private static int events;

    private static boolean budget() {
        return lines++ < 600;
    }

    /** Crew losses, deaths, falls and ends: a budget of their own, never used up by the damage lines. */
    private static boolean events() {
        return events++ < 300;
    }

    private static String id(Entity e) {
        return BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).getPath();
    }
}
