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
        int samples, ridden, airborne, shots;
        double maxAlt, firstDist = -1, closest = 1e9, path;
        double lx = Double.NaN, lz;
        /** (r65) its rider, and whether the capital shot it out of the saddle (the mount flew on without it) */
        Entity rider;
        boolean riderShot;
    }

    private static final class Foot {
        String type, group;
        int samples;
        double firstDist = -1, closest = 1e9, maxHp;
        boolean fromPortal, alive = true;
    }

    private static final class Run {
        ServerLevel level;
        ServerPlayer rebel;
        BlockPos center;
        int age;
        String began;
        final Map<UUID, Track> tracks = new HashMap<>();
        /** (r63, the user: "ネザーからきちんとモブくる？ボスは？") the siege's ground: every marked attacker, by kind. */
        final Map<UUID, Foot> foot = new HashMap<>();
        final List<String> notes = new ArrayList<>();
        /** (r67) the test's own crewed AH-6 on a pad 120 blocks out (the capital's own come only with a player near) */
        Entity heli;
        net.minecraft.world.level.ChunkPos heliChunk;
        double heliMaxAlt;
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
        // (r67) a crewed helicopter on a pad out of the capital's walls, as the capital's own stand: does it go up after
        // the air wing (it looked 64 round and 24 up before, and sat through every siege)
        if (jp.oror.reborn.vehicle.Sbw.present() && jp.oror.reborn.vehicle.Sbw.has("ah_6")) {
            // a pad with open sky over five by five, out of the capital's walls (120 out stood on a roof under a beam: it
            // pressed up at full power and never rose)
            int hx = r.center.getX() + 160, hz = r.center.getZ(), hy = 0;
            search:
            for (int d = 160; d <= 320; d += 16) {
                for (int[] dir : new int[][]{{1, 0}, {0, 1}, {-1, 0}, {0, -1}}) {
                    int x = r.center.getX() + dir[0] * d, z = r.center.getZ() + dir[1] * d;
                    level.getChunk(x >> 4, z >> 4);
                    if (jp.oror.reborn.village.BuildingGuard.inCapital(new BlockPos(x, 64, z), 8)) {
                        continue;
                    }
                    int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
                    boolean open = true;
                    for (int ox = -2; ox <= 2 && open; ox++) {
                        for (int oz = -2; oz <= 2 && open; oz++) {
                            int yy = level.getHeight(Heightmap.Types.MOTION_BLOCKING, x + ox, z + oz);
                            open = Math.abs(yy - y) <= 1 && level.getFluidState(new BlockPos(x + ox, yy, z + oz)).isEmpty()
                                && level.getFluidState(new BlockPos(x + ox, yy - 1, z + oz)).isEmpty();
                        }
                    }
                    if (open) {
                        hx = x;
                        hz = z;
                        hy = y;
                        break search;
                    }
                }
            }
            r.heliChunk = new net.minecraft.world.level.ChunkPos(hx >> 4, hz >> 4);
            level.setChunkForced(r.heliChunk.x, r.heliChunk.z, true);
            level.getChunk(r.heliChunk.x, r.heliChunk.z);
            if (hy == 0) {
                hy = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, hx, hz);
            }
            r.heli = jp.oror.reborn.vehicle.RoyalPilots.deploy(level, new net.minecraft.world.phys.Vec3(hx + 0.5, hy, hz + 0.5), -90F, "ah_6", 2, null);
        }
        LOG.info("SIEGE-START {\"center\":\"{}\",\"began\":\"{}\",\"testHeli\":\"{}\"}", r.center.toShortString(), r.began,
            r.heli == null ? "none" : r.heli.blockPosition().toShortString());
        run = r;
        return 1;
    }

    static String kind(Entity e) {
        String id = BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).toString();
        return switch (id) {
            // the siege's own mounts only (a wild dragon in its cave is not of the siege)
            case "iceandfire:fire_dragon", "iceandfire:ice_dragon", "iceandfire:lightning_dragon", "iceandfire:amphithere", "iceandfire:hippogryph" ->
                e.getPersistentData().getBoolean("OrorAzazelSiegeAir") ? id : null;
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

    private static String group(Entity e) {
        if (e.getPersistentData().getBoolean("OrorAzazelSiegeBoss")) {
            return "boss";
        }
        if (e.getPersistentData().getBoolean("OrorAzazelSiegeAir")) {
            return "air";
        }
        String id = BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).getPath();
        return switch (id) {
            case "piglin_brute", "piglin", "zombified_piglin", "blaze", "wither_skeleton", "ghast", "hoglin", "zoglin", "magma_cube" -> "nether";
            case "pillager", "vindicator", "evoker", "ravager", "illusioner", "witch", "vex" -> "illager";
            default -> "other";
        };
    }

    private static void census(Run r) {
        ServerLevel l = r.level;
        java.util.Set<UUID> seen = new java.util.HashSet<>();
        for (Entity e : l.getEntitiesOfClass(net.minecraft.world.entity.LivingEntity.class, new AABB(r.center).inflate(RADIUS, 200, RADIUS),
            x -> x.getPersistentData().getBoolean("OrorAzazelCapitalSiege"))) {
            seen.add(e.getUUID());
            Foot f = r.foot.get(e.getUUID());
            double d = Math.hypot(e.getX() - r.center.getX(), e.getZ() - r.center.getZ());
            if (f == null) {
                f = new Foot();
                f.type = BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).toString();
                f.group = group(e);
                f.firstDist = d;
                // born at a portal of the siege: a nether portal block within four blocks
                BlockPos b = e.blockPosition();
                for (BlockPos q : BlockPos.betweenClosed(b.offset(-4, -3, -4), b.offset(4, 4, 4))) {
                    if (l.getBlockState(q).is(net.minecraft.world.level.block.Blocks.NETHER_PORTAL)) {
                        f.fromPortal = true;
                        break;
                    }
                }
                r.foot.put(e.getUUID(), f);
            }
            f.samples++;
            f.closest = Math.min(f.closest, d);
            f.maxHp = Math.max(f.maxHp, ((net.minecraft.world.entity.LivingEntity) e).getMaxHealth());
        }
        for (Map.Entry<UUID, Foot> en : r.foot.entrySet()) {
            if (!seen.contains(en.getKey())) {
                en.getValue().alive = false;
            }
        }
    }

    private static void sample(Run r) {
        census(r);
        if (r.heli != null && r.heli.isAlive()) {
            int g = r.level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, r.heli.getBlockX(), r.heli.getBlockZ());
            r.heliMaxAlt = Math.max(r.heliMaxAlt, r.heli.getY() - g);
        }
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
                t.rider = e.getPassengers().get(0);
            } else if (t.rider != null && !t.rider.isAlive()) {
                t.riderShot = true;
            }
            t.shots = Math.max(t.shots, jp.oror.reborn.vehicle.SiegeGunners.shots(e));
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
                // (r63) where the rider sits: up (over the mount's feet, as a share of its height); on the back is about 0.8
                String seat = ridden ? String.format(java.util.Locale.ROOT, "%.2f", (e.getPassengers().get(0).getY() - e.getY()) / Math.max(0.1, e.getBbHeight())) : "-";
                line.append(String.format(java.util.Locale.ROOT, "%s%s rider=%s seat=%s alt=%.1f dist=%.0f path=%.0f mode=%s target=%s", line.length() > 0 ? "; " : "",
                    t.kind.substring(t.kind.indexOf(':') + 1), rider, seat, alt, d, t.path, e.getPersistentData().getString("OrorSiegeMountMode"), target));
            }
        }
        LOG.info("SIEGE-AIR {\"t\":{},\"seen\":{},\"now\":\"{}\"}", r.age, r.tracks.size(), line);
    }

    private static void finish(Run r) {
        if (r.heli != null) {
            net.minecraft.nbt.CompoundTag hp = r.heli.getPersistentData().getCompound(jp.oror.reborn.vehicle.RoyalPilots.KEY);
            LOG.info(String.format(java.util.Locale.ROOT, "SIEGE-HELI {\"alive\":%b,\"maxAlt\":%.1f,\"mode\":\"%s\",\"crew\":%d,\"target\":%b}",
                r.heli.isAlive(), r.heliMaxAlt, hp.getString("Mode"), r.heli.getPassengers().size(), hp.hasUUID("Target")));
            if (r.heliChunk != null) {
                r.level.setChunkForced(r.heliChunk.x, r.heliChunk.z, false);
            }
        }
        int mounts = 0, mountsRidden = 0, mountsFlew = 0, mountsCame = 0, mountsMoved = 0, helis = 0, helisFlew = 0, shots = 0, gunMounts = 0;
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
            shots += t.shots;
            gunMounts += t.kind.endsWith("hippogryph") || t.kind.endsWith("amphithere") ? 1 : 0;
            // (r65) a mount whose rider the capital's guns killed was ridden till then (the defence won, not the riding failed)
            mountsRidden += t.ridden * 2 >= t.samples || t.riderShot && t.ridden > 0 ? 1 : 0;
            mountsFlew += flew ? 1 : 0;
            mountsCame += t.firstDist - t.closest > 40 || t.closest < 120 ? 1 : 0;
            mountsMoved += t.path > 100 ? 1 : 0;
            maxAlt = Math.max(maxAlt, t.maxAlt);
        }
        boolean pass = mounts > 0 && mountsFlew * 2 >= mounts && mountsRidden * 2 >= mounts && mountsCame * 2 >= mounts && mountsMoved * 2 >= mounts;
        LOG.info(String.format(java.util.Locale.ROOT,
            "SIEGE-RESULT {\"present\":true,\"began\":\"%s\",\"mounts\":%d,\"ridden\":%d,\"ridersShot\":%d,\"flew\":%d,\"cameToCapital\":%d,\"maxAlt\":%.1f,"
                + "\"moved\":%d,\"helis\":%d,\"helisFlew\":%d,\"gunMounts\":%d,\"airShots\":%d,\"kinds\":\"%s\",\"pass\":%s}",
            r.began, mounts, mountsRidden, (int) r.tracks.values().stream().filter(x -> x.riderShot).count(), mountsFlew, mountsCame, maxAlt, mountsMoved, helis, helisFlew, gunMounts, shots, kinds, pass));
        // the ground: how many of each kind came, how many from the portals, how near the capital they got; the bosses one by one
        Map<String, int[]> groups = new java.util.TreeMap<>();
        Map<String, Integer> types = new java.util.TreeMap<>();
        StringBuilder bosses = new StringBuilder();
        for (Foot f : r.foot.values()) {
            int[] g = groups.computeIfAbsent(f.group, k -> new int[5]);
            g[0]++;
            g[1] += f.fromPortal ? 1 : 0;
            g[2] += f.firstDist - f.closest > 60 ? 1 : 0;
            g[3] += f.closest < 150 ? 1 : 0;
            g[4] += f.alive ? 1 : 0;
            types.merge(f.type, 1, Integer::sum);
            if (f.group.equals("boss")) {
                bosses.append(String.format(java.util.Locale.ROOT, "%s%s hp=%.0f from=%.0f closest=%.0f %s", bosses.length() > 0 ? "; " : "", f.type,
                    f.maxHp, f.firstDist, f.closest, f.alive ? "alive" : "gone"));
            }
        }
        StringBuilder gs = new StringBuilder();
        for (Map.Entry<String, int[]> en : groups.entrySet()) {
            int[] g = en.getValue();
            gs.append(String.format(java.util.Locale.ROOT, "%s\"%s\":{\"came\":%d,\"fromPortal\":%d,\"advanced\":%d,\"atCapital\":%d,\"alive\":%d}",
                gs.length() > 0 ? "," : "", en.getKey(), g[0], g[1], g[2], g[3], g[4]));
        }
        int[] nether = groups.getOrDefault("nether", new int[5]);
        int[] boss = groups.getOrDefault("boss", new int[5]);
        boolean groundPass = nether[0] > 0 && nether[2] > 0 && boss[0] > 0;
        LOG.info("SIEGE-GROUND {\"groups\":{" + gs + "},\"types\":\"" + types + "\",\"bosses\":\"" + bosses + "\",\"pass\":" + groundPass + "}");
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
