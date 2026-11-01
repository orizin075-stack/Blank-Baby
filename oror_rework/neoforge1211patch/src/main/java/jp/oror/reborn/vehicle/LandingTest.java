package jp.oror.reborn.vehicle;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.ChunkPos;
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
 * /oror pilots landings (051): the A-10's coming home, five times over, on the pilot test's runway (that test must have
 * run first). One flight in each CI run said little of how well it lands; here, each time, a crewed aircraft with its
 * battery low and its guns empty is put in the air somewhere about the runway (beyond its far end flying on, abeam
 * flying away, short of it flying away, far out on the approach flying in, over the runway flying out the wrong way),
 * and flies home and lands by itself. LANDING-TRIAL says how each went: down on the runway (where along it, how far off
 * its centre line, how hard, the health lost), down somewhere else, lost, or out of time; LANDING-RESULT sums them up.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class LandingTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Vehicles");
    public static volatile boolean resultLogged;
    /** Where each flight starts against the runway: along its line from its start, off it, heading against the runway's. */
    private static final double[][] STARTS = {{450, 150, 0}, {50, -350, -90}, {-250, 300, 90}, {-700, -80, 0}, {150, 0, 180}};
    private static final String[] NAMES = {"beyond-far-end", "abeam-away", "short-away", "far-out-inbound", "over-runway-outbound"};
    /** 80 seconds a flight. */
    private static final int LIMIT = 1600;
    private static Run run;

    private static final class Run {
        ServerLevel level;
        Vec3 home, f, side;
        float heading;
        double runwayY;
        final Set<Long> base = new HashSet<>();
        final Set<Long> window = new HashSet<>();
        int trial = -1;
        String phase = "gap";
        long phaseAt;
        Entity plane;
        Vec3 startPos;
        float health, minHealth, healthAtTouch;
        double lastVy, lastSpeed;
        boolean touched;
        long touchAt;
        String touchMode = "";
        double touchAlong, touchOff, touchVy, touchSpeed;
        final List<String> trials = new ArrayList<>();
        int landed, elsewhere, lost, timedOut;
    }

    private LandingTest() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("pilots").requires(s -> s.hasPermission(2))
            .then(Commands.literal("landings").executes(c -> start(c.getSource())))));
    }

    private static int start(CommandSourceStack src) {
        if (run != null) {
            return 0;
        }
        boolean present = Sbw.present() && Sbw.has("a_10a");
        if (!present || PilotTest.stripOrigin == null || PilotTest.stripLevel == null) {
            LOG.info("LANDING-RESULT {\"present\":{},\"strip\":{}}", present, PilotTest.stripOrigin != null);
            resultLogged = true;
            return 0;
        }
        Run r = new Run();
        r.level = PilotTest.stripLevel;
        BlockPos o = PilotTest.stripOrigin;
        r.runwayY = PilotTest.stripY;
        r.home = new Vec3(o.getX() + 0.5, r.runwayY, o.getZ() + 0.5);
        r.heading = -90F;
        r.f = Vec3.directionFromRotation(0, r.heading);
        r.side = new Vec3(-r.f.z, 0, r.f.x);
        for (int dx = -16; dx <= 16; dx++) {
            for (int dz = -9; dz <= 9; dz++) {
                int cx = (o.getX() >> 4) + dx, cz = (o.getZ() >> 4) + dz;
                if (r.level.setChunkForced(cx, cz, true)) {
                    r.base.add(ChunkPos.asLong(cx, cz));
                }
            }
        }
        r.phaseAt = r.level.getGameTime();
        run = r;
        LOG.info("LANDING-START {\"runway\":[{},{},{}],\"flights\":{}}", o.getX(), (int) r.runwayY, o.getZ(), STARTS.length);
        src.sendSuccess(() -> Component.literal("着陸試験を開始しました"), true);
        return 1;
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        Run r = run;
        if (r == null) {
            return;
        }
        long now = r.level.getGameTime();
        long t = now - r.phaseAt;
        switch (r.phase) {
            case "gap" -> {
                if (t < 20) {
                    return;
                }
                r.trial++;
                if (r.trial >= STARTS.length) {
                    finish(r);
                    return;
                }
                double[] s = STARTS[r.trial];
                r.startPos = r.home.add(r.f.scale(s[0])).add(r.side.scale(s[1]));
                follow(r, r.startPos);
                r.phase = "load";
                r.phaseAt = now;
            }
            case "load" -> {
                int cx = Mth.floor(r.startPos.x) >> 4, cz = Mth.floor(r.startPos.z) >> 4;
                boolean ready = true;
                for (int dx = -1; dx <= 1; dx++) {
                    for (int dz = -1; dz <= 1; dz++) {
                        ready &= r.level.hasChunk(cx + dx, cz + dz);
                    }
                }
                if (ready || t > 400) {
                    launch(r, now);
                }
            }
            default -> watch(r, now, now - r.phaseAt);
        }
    }

    private static void launch(Run r, long now) {
        double[] s = STARTS[r.trial];
        int ground = r.level.getHeight(Heightmap.Types.MOTION_BLOCKING, Mth.floor(r.startPos.x), Mth.floor(r.startPos.z));
        double y = Math.max(r.runwayY + 70, ground + 45);
        float yaw = r.heading + (float) s[2];
        Entity v = RoyalPilots.deploy(r.level, new Vec3(r.startPos.x, y, r.startPos.z), yaw, "a_10a", 1, null);
        r.phaseAt = now;
        if (v == null) {
            r.trials.add(String.format(Locale.ROOT, "{\"trial\":%d,\"from\":\"%s\",\"outcome\":\"not-deployed\"}", r.trial, NAMES[r.trial]));
            r.lost++;
            r.phase = "gap";
            return;
        }
        // its stand is the runway's start; low on power and out of ammunition, it is on its way home to be supplied
        CompoundTag p = v.getPersistentData().getCompound(RoyalPilots.KEY);
        p.putLong("Home", BlockPos.containing(r.home).asLong());
        p.putFloat("Heading", r.heading);
        p.putDouble("RunwayY", r.runwayY);
        p.remove("NoRunway");
        p.putBoolean("TookOff", true);
        p.putString("Mode", "return");
        p.putLong("Since", now);
        Supply.drain(v, 0.2);
        p.putBoolean("Resupply", true);
        p.putLong("ResupplySince", now);
        v.setDeltaMovement(Vec3.directionFromRotation(0, yaw).scale(2.5));
        Sbw.call(v, "setPower", 1.2F);
        Sbw.call(v, "setEngineStart", true);
        Sbw.call(v, "setEngineStartOver", true);
        r.plane = v;
        r.health = r.minHealth = Sbw.health(v);
        r.touched = false;
        r.phase = "fly";
        LOG.info(String.format(Locale.ROOT, "LANDING-FLIGHT {\"trial\":%d,\"from\":\"%s\",\"along\":%.0f,\"off\":%.0f,\"y\":%.0f,\"yaw\":%.0f}",
            r.trial, NAMES[r.trial], s[0], s[1], y, s[2]));
    }

    private static void watch(Run r, long now, long t) {
        Entity v = r.plane;
        String outcome = null;
        CompoundTag p = v.getPersistentData().getCompound(RoyalPilots.KEY);
        String mode = p.getString("Mode");
        Vec3 rel = v.position().subtract(r.home);
        double along = rel.dot(r.f), off = rel.dot(r.side);
        if (!v.isAlive()) {
            outcome = "lost";
        } else {
            float h = Sbw.health(v);
            r.minHealth = Math.min(r.minHealth, h);
            if (t % 10 == 0) {
                Object roll = Sbw.call(v, "getRoll");
                LOG.info(String.format(Locale.ROOT, "LANDING-TRACK {\"trial\":%d,\"t\":%d,\"mode\":\"%s%s\",\"y\":%.1f,\"ground\":%d,\"speed\":%.2f,"
                        + "\"vy\":%.2f,\"pitch\":%.1f,\"yaw\":%.1f,\"roll\":%s,\"along\":%.0f,\"off\":%.0f,\"power\":%.2f,\"health\":%.2f}", r.trial, t, mode,
                    p.getBoolean("FinalLeg") ? ":final-leg" : "", v.getY(), r.level.getHeight(Heightmap.Types.MOTION_BLOCKING, Mth.floor(v.getX()),
                        Mth.floor(v.getZ())), v.getDeltaMovement().length(), v.getDeltaMovement().y, v.getXRot(),
                    Mth.wrapDegrees(v.getYRot() - r.heading), roll instanceof Number n ? String.format(Locale.ROOT, "%.1f", n.floatValue()) : "0",
                    along, off, Sbw.power(v), h));
                follow(r, v.position());
            }
            if (!r.touched && v.onGround()) {
                r.touched = true;
                r.touchAt = now;
                r.touchMode = mode;
                r.touchAlong = along;
                r.touchOff = off;
                r.touchVy = r.lastVy;
                r.touchSpeed = r.lastSpeed;
                r.healthAtTouch = r.health;
            }
            if (r.touched) {
                long since = now - r.touchAt;
                boolean stopped = v.getDeltaMovement().horizontalDistance() < 0.05 && since > 40;
                if (stopped || since > 240 || mode.equals("taxi") || mode.equals("parked")) {
                    boolean onRunway = r.touchAlong >= -2 && r.touchAlong <= 225 && Math.abs(r.touchOff) <= 4.5;
                    outcome = onRunway ? "landed" : "down-elsewhere";
                }
            }
            r.health = h;
            r.lastVy = v.getDeltaMovement().y;
            r.lastSpeed = v.getDeltaMovement().length();
            if (outcome == null && t > LIMIT) {
                outcome = "timeout";
            }
        }
        if (outcome == null) {
            return;
        }
        switch (outcome) {
            case "landed" -> r.landed++;
            case "down-elsewhere" -> r.elsewhere++;
            case "lost" -> r.lost++;
            default -> r.timedOut++;
        }
        String touch = r.touched ? String.format(Locale.ROOT, ",\"touch\":{\"mode\":\"%s\",\"along\":%.0f,\"off\":%.1f,\"vy\":%.2f,\"speed\":%.2f,"
            + "\"lost\":%.2f},\"stop\":{\"along\":%.0f,\"off\":%.1f}", r.touchMode, r.touchAlong, r.touchOff, r.touchVy, r.touchSpeed,
            r.healthAtTouch - (v.isAlive() ? Sbw.health(v) : 0F), along, off) : "";
        String line = String.format(Locale.ROOT, "{\"trial\":%d,\"from\":\"%s\",\"outcome\":\"%s\",\"seconds\":%.1f,\"goArounds\":%d,\"minHealth\":%.2f%s}",
            r.trial, NAMES[r.trial], outcome, t / 20.0, p.getInt("GoArounds"), Math.max(0, r.minHealth), touch);
        r.trials.add(line);
        LOG.info("LANDING-TRIAL {}", line);
        for (Entity rider : List.copyOf(v.getPassengers())) {
            rider.discard();
        }
        v.discard();
        r.plane = null;
        r.phase = "gap";
        r.phaseAt = now;
    }

    /** The chunks within two of the aircraft kept loaded (and ticking) while it flies; the ones it has left let go. */
    private static void follow(Run r, Vec3 at) {
        int cx = Mth.floor(at.x) >> 4, cz = Mth.floor(at.z) >> 4;
        Set<Long> want = new HashSet<>();
        for (int dx = -2; dx <= 2; dx++) {
            for (int dz = -2; dz <= 2; dz++) {
                want.add(ChunkPos.asLong(cx + dx, cz + dz));
            }
        }
        for (Iterator<Long> it = r.window.iterator(); it.hasNext(); ) {
            long c = it.next();
            if (!want.contains(c)) {
                r.level.setChunkForced(ChunkPos.getX(c), ChunkPos.getZ(c), false);
                it.remove();
            }
        }
        for (long c : want) {
            if (!r.base.contains(c) && !r.window.contains(c) && r.level.setChunkForced(ChunkPos.getX(c), ChunkPos.getZ(c), true)) {
                r.window.add(c);
            }
        }
    }

    private static void finish(Run r) {
        LOG.info(String.format(Locale.ROOT, "LANDING-RESULT {\"present\":true,\"flights\":%d,\"landed\":%d,\"downElsewhere\":%d,\"lost\":%d,"
            + "\"timedOut\":%d,\"trials\":[%s]}", r.trials.size(), r.landed, r.elsewhere, r.lost, r.timedOut, String.join(",", r.trials)));
        for (Set<Long> s : List.of(r.base, r.window)) {
            for (long c : s) {
                r.level.setChunkForced(ChunkPos.getX(c), ChunkPos.getZ(c), false);
            }
        }
        run = null;
        resultLogged = true;
    }

    @SubscribeEvent
    public static void stopped(ServerStoppedEvent e) {
        run = null;
    }
}
