package jp.oror.reborn.ci;

import com.mojang.authlib.GameProfile;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import jp.oror.reborn.citadel.CitadelSites;
import jp.oror.reborn.king.RebelPact;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (r63) Azazel's siege of the capital with its air wing (the user: "ピリジャーのドラゴンとかきちんと飛んでる？"): a rebel
 * with the favour the siege asks for starts it at the capital, then every five seconds for four minutes each mount of the
 * air wing (Ice and Fire's fire and ice dragons, amphitheres, hippogryphs) and each helicopter near the capital is looked
 * at: its rider, its height over the ground, its speed, its distance to the capital. SIEGE-AIR lines and SIEGE-RESULT.
 * The siege classes (r50 to r61, kept as built) are reached by name.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class SiegeTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Siege");
    public static volatile boolean resultLogged;
    private static final int SAMPLE = 100, TICKS = 4800, RADIUS = 800;
    private static Run run;

    private SiegeTest() {
    }

    private static final class Track {
        String kind;
        int samples, ridden, airborne;
        double maxAlt, firstDist = -1, closest = 1e9, path;
        double lx = Double.NaN, lz;
    }

    private static final class Run {
        ServerLevel level;
        ServerPlayer rebel;
        BlockPos center;
        int age;
        String began;
        final Map<UUID, Track> tracks = new HashMap<>();
        final List<String> notes = new ArrayList<>();
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("siege").then(Commands.literal("test")
            .requires(s -> s.hasPermission(2)).executes(c -> start(c.getSource().getServer().overworld())))));
    }

    static Class<?> siege() throws ClassNotFoundException {
        return Class.forName("jp.oror.reborn.siege.AzazelCapitalSiege");
    }

    private static int start(ServerLevel level) {
        resultLogged = false;
        Run r = new Run();
        r.level = level;
        CitadelSites.Site site = CitadelSites.capital();
        if (site == null) {
            LOG.info("SIEGE-RESULT {\"present\":false,\"why\":\"no capital\",\"pass\":false}");
            resultLogged = true;
            return 0;
        }
        r.center = site.center();
        try {
            Class<?> c = siege();
            ServerPlayer p = FakePlayerFactory.get(level, new GameProfile(UUID.nameUUIDFromBytes("oror-siege-test".getBytes()), "[OROR Siege]"));
            p.moveTo(r.center.getX() + 0.5, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, r.center.getX(), r.center.getZ()) + 1,
                r.center.getZ() + 0.5);
            if (RebelPact.favour(p) < 30) {
                RebelPact.addFavour(p, 30 - RebelPact.favour(p));
            }
            r.rebel = p;
            Method begin = c.getDeclaredMethod("begin", ServerPlayer.class);
            begin.setAccessible(true);
            r.began = String.valueOf(begin.invoke(null, p));
        } catch (Throwable t) {
            LOG.info("SIEGE-RESULT {\"present\":false,\"why\":\"{}\",\"pass\":false}", String.valueOf(t).replace('"', '\''));
            LOG.warn("SIEGE-TEST", t);
            resultLogged = true;
            return 0;
        }
        LOG.info("SIEGE-START {\"center\":\"{}\",\"began\":\"{}\"}", r.center.toShortString(), r.began);
        run = r;
        return 1;
    }

    static String kind(Entity e) {
        String id = BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).toString();
        return switch (id) {
            case "iceandfire:fire_dragon", "iceandfire:ice_dragon", "iceandfire:lightning_dragon", "iceandfire:amphithere", "iceandfire:hippogryph" -> id;
            case "superbwarfare:ah_6", "superbwarfare:mi_28" -> id;
            default -> null;
        };
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        Run r = run;
        if (r == null) {
            return;
        }
        r.age++;
        if (r.age % SAMPLE == 0) {
            sample(r);
        }
        if (r.age >= TICKS) {
            finish(r);
            run = null;
        }
    }

    private static void sample(Run r) {
        ServerLevel l = r.level;
        StringBuilder line = new StringBuilder();
        int n = 0;
        for (Entity e : l.getEntitiesOfClass(Entity.class, new AABB(r.center).inflate(RADIUS, 200, RADIUS), x -> kind(x) != null)) {
            Track t = r.tracks.computeIfAbsent(e.getUUID(), u -> new Track());
            t.kind = kind(e);
            t.samples++;
            boolean ridden = !e.getPassengers().isEmpty();
            int ground = l.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, e.getBlockX(), e.getBlockZ());
            double alt = e.getY() - ground;
            boolean air = alt > 4 && !e.onGround();
            if (ridden) {
                t.ridden++;
            }
            if (air) {
                t.airborne++;
            }
            t.maxAlt = Math.max(t.maxAlt, alt);
            double d = Math.sqrt(e.distanceToSqr(r.center.getX() + 0.5, e.getY(), r.center.getZ() + 0.5));
            if (t.firstDist < 0) {
                t.firstDist = d;
            }
            t.closest = Math.min(t.closest, d);
            if (!Double.isNaN(t.lx)) {
                t.path += Math.hypot(e.getX() - t.lx, e.getZ() - t.lz);
            }
            t.lx = e.getX();
            t.lz = e.getZ();
            if (n++ < 8) {
                String rider = ridden ? BuiltInRegistries.ENTITY_TYPE.getKey(e.getPassengers().get(0).getType()).getPath() : "none";
                String target = e instanceof Mob m && m.getTarget() != null ? BuiltInRegistries.ENTITY_TYPE.getKey(m.getTarget().getType()).getPath() : "none";
                line.append(String.format(java.util.Locale.ROOT, "%s%s rider=%s alt=%.1f dist=%.0f target=%s", line.length() > 0 ? "; " : "",
                    t.kind.substring(t.kind.indexOf(':') + 1), rider, alt, d, target));
            }
        }
        LOG.info("SIEGE-AIR {\"t\":{},\"seen\":{},\"now\":\"{}\"}", r.age, r.tracks.size(), line);
    }

    private static void finish(Run r) {
        int mounts = 0, mountsRidden = 0, mountsFlew = 0, mountsCame = 0, helis = 0, helisFlew = 0;
        double maxAlt = 0;
        Map<String, Integer> kinds = new HashMap<>();
        for (Track t : r.tracks.values()) {
            kinds.merge(t.kind, 1, Integer::sum);
            boolean heli = t.kind.startsWith("superbwarfare:");
            boolean flew = t.samples > 0 && t.airborne * 2 >= t.samples;
            if (heli) {
                helis++;
                helisFlew += flew ? 1 : 0;
                continue;
            }
            mounts++;
            mountsRidden += t.ridden * 2 >= t.samples ? 1 : 0;
            mountsFlew += flew ? 1 : 0;
            mountsCame += t.firstDist - t.closest > 40 || t.closest < 120 ? 1 : 0;
            maxAlt = Math.max(maxAlt, t.maxAlt);
        }
        boolean pass = mounts > 0 && mountsFlew * 2 >= mounts && mountsRidden * 2 >= mounts && mountsCame > 0;
        LOG.info(String.format(java.util.Locale.ROOT,
            "SIEGE-RESULT {\"present\":true,\"began\":\"%s\",\"mounts\":%d,\"ridden\":%d,\"flew\":%d,\"cameToCapital\":%d,\"maxAlt\":%.1f,"
                + "\"helis\":%d,\"helisFlew\":%d,\"kinds\":\"%s\",\"pass\":%s}",
            r.began, mounts, mountsRidden, mountsFlew, mountsCame, maxAlt, helis, helisFlew, kinds, pass));
        try {
            Method stop = siege().getDeclaredMethod("stop", ServerPlayer.class);
            stop.setAccessible(true);
            stop.invoke(null, r.rebel);
        } catch (Throwable t) {
            LOG.warn("SIEGE-TEST stop", t);
        }
        resultLogged = true;
    }
}
