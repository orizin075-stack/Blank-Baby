package jp.oror.reborn.waza.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import jp.oror.reborn.waza.Waza;
import jp.oror.reborn.waza.WazaNet;
import net.minecraft.client.Camera;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.client.event.RenderLevelStageEvent;
import org.joml.Matrix4f;
import org.joml.Vector3f;

/**
 * (057) The client's side of the 984 techniques: what the server said is under way, played. Each technique's own
 * motion on its caster's rig (CharacterModel asks playing()), its sounds at its moments (the gathering, the release,
 * each hit; a song heard further than it reaches), its particles in its own colours (the gathering about the body, the
 * blade's ribbon along its path, the warnings where a blow, a fall or a beam will come), the things it put into the
 * world (shots in their own shapes, beams, fields, rings, growths by stage, devices by stage, guards that crack, chains
 * and threads, summoning circles), and the props it grows on the body (a halo, a crown, a robe, tomes, orbs, fruit, a
 * wheel, a core, a blade's ribbon, fins). A contract offered to this player opens its screen.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses", value = Dist.CLIENT)
public final class WazaClient {
    /** A technique playing on an entity. */
    public record Play(Waza w, long start, long seed, int target) {
    }

    static final class Obj {
        int kind, owner, index, life, stage;
        Waza w;
        Vec3 pos, dir;
        float radius;
        long born;
    }

    private static final Map<Integer, Play> PLAYS = new HashMap<>();
    private static final Map<Integer, Obj> OBJS = new HashMap<>();
    private static final RandomSource R = RandomSource.create();

    private WazaClient() {
    }

    /** The technique playing on this entity now, if any (CharacterModel lays its motion over the rig). */
    public static Play playing(int entity) {
        Play p = PLAYS.get(entity);
        if (p == null) {
            return null;
        }
        ClientLevel level = Minecraft.getInstance().level;
        if (level == null || level.getGameTime() - p.start() > p.w().length() + 2) {
            PLAYS.remove(entity);
            return null;
        }
        return p;
    }

    public static void receive(String what, Object payload) {
        ClientLevel level = Minecraft.getInstance().level;
        if (level == null) {
            return;
        }
        switch (what) {
            case "show" -> {
                WazaNet.Show s = (WazaNet.Show) payload;
                if (s.index() < 0) {
                    PLAYS.remove(s.entity());
                    if (s.reason() >= 2) {
                        // its caster died or left: everything it put into the world goes with it
                        OBJS.values().removeIf(o -> o.owner == s.entity());
                    }
                    return;
                }
                Waza w = Waza.of(s.index());
                if (w != null) {
                    PLAYS.put(s.entity(), new Play(w, s.start(), s.seed(), s.target()));
                    Entity e = level.getEntity(s.entity());
                    if (e != null) {
                        sound(level, e.position(), w.sounds()[0], 0.9F, 0.9F + (s.seed() & 7) * 0.03F);
                    }
                }
            }
            case "obj" -> {
                WazaNet.Obj o = (WazaNet.Obj) payload;
                if (o.op() == 2) {
                    OBJS.remove(o.id());
                    return;
                }
                Obj ob = OBJS.computeIfAbsent(o.id(), k -> new Obj());
                ob.kind = o.kind();
                ob.owner = o.owner();
                ob.index = o.index();
                ob.w = Waza.of(o.index());
                ob.pos = new Vec3(o.x(), o.y(), o.z());
                ob.dir = new Vec3(o.dx(), o.dy(), o.dz());
                ob.radius = o.radius();
                ob.life = o.life();
                ob.stage = o.stage();
                ob.born = o.born();
            }
            case "fx" -> fx(level, (WazaNet.Fx) payload);
            case "offer" -> {
                WazaNet.Offer o = (WazaNet.Offer) payload;
                Waza w = Waza.of(o.index());
                Entity owner = level.getEntity(o.owner());
                Minecraft.getInstance().setScreen(new PactScreen(o, w, owner == null ? "？" : owner.getDisplayName().getString()));
            }
            default -> {
            }
        }
    }

    // --------------------------------------------------------------------------------------------------------- sound

    static void sound(ClientLevel level, Vec3 at, String id, float volume, float pitch) {
        SoundEvent s = BuiltInRegistries.SOUND_EVENT.get(ResourceLocation.tryParse(id));
        if (s != null) {
            level.playLocalSound(at.x, at.y, at.z, s, SoundSource.HOSTILE, volume, pitch, false);
        }
    }

    // ----------------------------------------------------------------------------------------------------- particles

    static Vector3f rgb(int c) {
        return new Vector3f(((c >> 16) & 0xFF) / 255F, ((c >> 8) & 0xFF) / 255F, (c & 0xFF) / 255F);
    }

    static ParticleOptions dust(Waza w, int which, float size) {
        int[] c = w == null ? new int[]{0xE8E0FF} : w.colours();
        return new DustParticleOptions(rgb(c[Math.min(which, c.length - 1)]), size);
    }

    static ParticleOptions named(Waza w, int which) {
        String n = w == null || w.particles().length == 0 ? "end_rod" : w.particles()[Math.min(which, w.particles().length - 1)];
        return switch (n) {
            case "dust" -> dust(w, which, 1.0F);
            case "splash" -> ParticleTypes.SPLASH;
            case "poof" -> ParticleTypes.POOF;
            case "happy_villager" -> ParticleTypes.HAPPY_VILLAGER;
            case "crit" -> ParticleTypes.CRIT;
            case "soul" -> ParticleTypes.SOUL;
            case "electric_spark" -> ParticleTypes.ELECTRIC_SPARK;
            case "flame" -> ParticleTypes.FLAME;
            case "snowflake" -> ParticleTypes.SNOWFLAKE;
            case "witch" -> ParticleTypes.WITCH;
            default -> ParticleTypes.END_ROD;
        };
    }

    static void put(ClientLevel l, ParticleOptions p, Vec3 at, double vx, double vy, double vz) {
        l.addParticle(p, at.x, at.y, at.z, vx, vy, vz);
    }

    static void circle(ClientLevel l, ParticleOptions p, Vec3 c, double r, int n, double turn) {
        for (int i = 0; i < n; i++) {
            double a = turn + i * Mth.TWO_PI / n;
            put(l, p, c.add(Math.cos(a) * r, 0.05, Math.sin(a) * r), 0, 0.005, 0);
        }
    }

    static void line(ClientLevel l, ParticleOptions p, Vec3 a, Vec3 b, double step) {
        double len = a.distanceTo(b);
        int n = (int) Math.min(64, Math.max(2, len / step));
        for (int i = 0; i <= n; i++) {
            put(l, p, a.lerp(b, i / (double) n), 0, 0, 0);
        }
    }

    @SubscribeEvent
    public static void tick(ClientTickEvent.Post e) {
        Minecraft mc = Minecraft.getInstance();
        ClientLevel l = mc.level;
        if (l == null || mc.isPaused()) {
            if (l == null) {
                PLAYS.clear();
                OBJS.clear();
            }
            return;
        }
        long now = l.getGameTime();
        for (Iterator<Map.Entry<Integer, Play>> it = PLAYS.entrySet().iterator(); it.hasNext(); ) {
            Map.Entry<Integer, Play> en = it.next();
            Play p = en.getValue();
            Entity ent = l.getEntity(en.getKey());
            int t = (int) (now - p.start());
            if (ent == null || t > p.w().length() + 2) {
                it.remove();
                continue;
            }
            playTick(l, ent, p, t);
        }
        for (Iterator<Map.Entry<Integer, Obj>> it = OBJS.entrySet().iterator(); it.hasNext(); ) {
            Obj o = it.next().getValue();
            int age = (int) (now - o.born);
            // a thing outlives neither its life nor its owner (an owner gone from the world can no longer be heard
            // taking its things down: no one tracks it)
            if (o.w == null || age > o.life + 40 || l.getEntity(o.owner) == null) {
                it.remove();
                continue;
            }
            objTick(l, o, age);
        }
    }

    /** The technique's own moments on its caster: the gathering, the release, the hits and the ribbon, the fading. */
    private static void playTick(ClientLevel l, Entity e, Play p, int t) {
        Waza w = p.w();
        int wu = w.windup(), al = w.activeLength();
        float h = e.getBbHeight();
        Vec3 chest = e.position().add(0, h * 0.6, 0);
        float scale = 1 + w.tier() * 0.5F;
        if (t < wu) {
            // the gathering: motes drawn in toward the body, closer and quicker as the windup ends
            float u = t / (float) Math.max(1, wu);
            int n = 1 + w.tier();
            for (int k = 0; k < n; k++) {
                double a = R.nextDouble() * Mth.TWO_PI;
                double r = (1.6 - u) * scale;
                Vec3 at = chest.add(Math.cos(a) * r, (R.nextDouble() - 0.5) * h * 0.8, Math.sin(a) * r);
                Vec3 v = chest.subtract(at).scale(0.12);
                put(l, dust(w, k % 2, 0.8F + w.tier() * 0.2F), at, v.x, v.y, v.z);
            }
            if (w.tier() >= 2 && t % 2 == 0) {
                circle(l, dust(w, 1, 1.2F), e.position(), (1.2 + u) * scale, 10 + 4 * w.tier(), t * 0.2);
            }
            return;
        }
        int a = t - wu;
        if (a == 0) {
            sound(l, e.position(), w.sounds()[1], 1.0F + (w.behaviour() == Waza.Behaviour.SONG ? (w.range() + 8) / 16F : 0),
                1.0F + (p.seed() & 3) * 0.05F);
            for (int k = 0; k < 6 + 4 * w.tier(); k++) {
                put(l, named(w, 0), chest, (R.nextDouble() - 0.5) * 0.4, R.nextDouble() * 0.2, (R.nextDouble() - 0.5) * 0.4);
            }
        }
        for (int hit : w.hits()) {
            if (hit == a) {
                sound(l, e.position(), w.sounds()[2], 0.8F, 1.0F + (hit % 4) * 0.06F);
            }
        }
        if (a <= al && w.behaviour() == Waza.Behaviour.MELEE) {
            ribbon(l, e, p, a);
        }
        if (a > al && (t & 1) == 0) {
            // the leftovers taken down: a few motes falling away
            put(l, dust(w, 2, 0.6F), chest.add((R.nextDouble() - 0.5) * 1.2, (R.nextDouble() - 0.5) * h * 0.6, (R.nextDouble() - 0.5) * 1.2), 0,
                -0.02, 0);
        }
    }

    /** The blade's ribbon: the tip's path through the two ticks before each hit, as the server sweeps it. */
    private static void ribbon(ClientLevel l, Entity e, Play p, int a) {
        Waza w = p.w();
        int[] hits = w.hits();
        Entity target = p.target() >= 0 ? l.getEntity(p.target()) : null;
        Vec3 fwd = target != null ? target.position().subtract(e.position()) : e.getLookAngle();
        fwd = new Vec3(fwd.x, 0, fwd.z);
        fwd = fwd.lengthSqr() < 1e-4 ? new Vec3(0, 0, 1) : fwd.normalize();
        Vec3 side = new Vec3(-fwd.z, 0, fwd.x);
        float reach = w.range() + e.getBbWidth() * 0.5F;
        for (int i = 0; i < hits.length; i++) {
            if (a < hits[i] - 2 || a > hits[i] + 1) {
                continue;
            }
            int arc = w.arcs().length > 0 ? w.arcs()[i % w.arcs().length] : 0;
            Vec3 shoulder = e.position().add(0, e.getBbHeight() * (arc == 5 ? 0.1 : arc == 6 ? 0.45 : 0.62), 0);
            for (int k = 0; k <= 8; k++) {
                double u = k / 8.0;
                Vec3 d = switch (arc) {
                    case 1 -> fwd.scale(Math.cos(Mth.lerp(u, -1.1, 1.1) * 0.8)).add(side.scale(Math.sin(Mth.lerp(u, -1.1, 1.1)) * 0.9))
                        .add(0, -Mth.lerp(u, -1.1, 1.1) * 0.6, 0);
                    case 2 -> fwd.scale(Math.cos(Mth.lerp(u, -1.1, 1.1) * 0.8)).add(side.scale(-Math.sin(Mth.lerp(u, -1.1, 1.1)) * 0.9))
                        .add(0, Mth.lerp(u, -1.1, 1.1) * 0.6, 0);
                    case 3 -> fwd.scale(0.4 + 0.6 * u);
                    case 4 -> fwd.scale(Math.cos(Mth.lerp(u, -1.3, 0.9))).add(0, -Math.sin(Mth.lerp(u, -1.3, 0.9)), 0);
                    case 5 -> fwd.scale(Math.cos(u * Mth.TWO_PI)).add(side.scale(Math.sin(u * Mth.TWO_PI)));
                    case 6 -> fwd.scale(Math.cos(Mth.lerp(u, -Math.PI, Math.PI))).add(side.scale(Math.sin(Mth.lerp(u, -Math.PI, Math.PI))));
                    default -> fwd.scale(Math.cos(Mth.lerp(u, -1.2, 1.2))).add(side.scale(Math.sin(Mth.lerp(u, -1.2, 1.2))));
                };
                Vec3 tip = shoulder.add(d.normalize().scale(arc == 3 ? reach * (0.4 + 0.6 * u) : reach));
                put(l, dust(w, k % 2, 1.1F), tip, 0, 0, 0);
                if (k % 3 == 0) {
                    put(l, named(w, 1), tip, 0, 0, 0);
                }
            }
        }
    }

    /** The things in the world, each its own way. */
    private static void objTick(ClientLevel l, Obj o, int age) {
        Waza w = o.w;
        switch (o.kind) {
            case 0 -> { // a shot, in its own shape, carried on as the server last said it was going
                o.pos = o.pos.add(o.dir);
                shape(l, w, o.pos, o.dir, age);
            }
            case 1 -> { // a beam
                Vec3 end = o.pos.add(o.dir.normalize().scale(o.radius));
                line(l, dust(w, 0, 1.6F + w.tier() * 0.4F), o.pos, end, 0.35);
                if ((age & 1) == 0) {
                    line(l, named(w, 1), o.pos, end, 1.2);
                }
            }
            case 2 -> { // a field: its edge turning on the ground, motes rising within
                circle(l, dust(w, 0, 1.2F), o.pos, o.radius, Math.min(40, 12 + (int) o.radius * 2), age * 0.05);
                for (int k = 0; k < 2 + w.tier(); k++) {
                    double a = R.nextDouble() * Mth.TWO_PI, r = Math.sqrt(R.nextDouble()) * o.radius;
                    put(l, dust(w, 1, 0.8F), o.pos.add(Math.cos(a) * r, 0.1, Math.sin(a) * r), 0, 0.05, 0);
                }
            }
            case 3 -> { // a ring of sound spreading
                float r = o.radius * age / Math.max(1F, o.life);
                circle(l, w.particles().length > 0 && w.particles()[0].equals("dust") ? dust(w, 0, 1.3F) : ParticleTypes.NOTE, o.pos.add(0, 0.6, 0),
                    r, Math.min(48, 10 + (int) (r * 3)), 0);
            }
            case 4 -> { // a growth, by its stage
                ParticleOptions g = switch (o.stage) {
                    case 0 -> dust(w, 1, 0.6F);
                    case 1 -> ParticleTypes.HAPPY_VILLAGER;
                    case 2 -> dust(w, 0, 1.3F);
                    default -> ParticleTypes.ASH;
                };
                double height = switch (o.stage) {
                    case 0 -> 0.3;
                    case 1 -> 1.0;
                    case 2 -> 2.2 + w.tier() * 0.4;
                    default -> 1.0;
                };
                for (int k = 0; k < 3; k++) {
                    put(l, g, o.pos.add((R.nextDouble() - 0.5) * 0.5, R.nextDouble() * height, (R.nextDouble() - 0.5) * 0.5), 0, 0.01, 0);
                }
                if (o.stage == 2 && age % 4 == 0) {
                    circle(l, dust(w, 1, 0.9F), o.pos, 1.8 + w.tier() * 0.4, 12, age * 0.1);
                }
            }
            case 5 -> { // a device: drawn, built, finished, at work
                double s = 0.7;
                ParticleOptions edge = switch (o.stage) {
                    case 0 -> new DustParticleOptions(new Vector3f(0.4F, 0.8F, 1.0F), 0.7F);
                    case 1 -> ParticleTypes.ELECTRIC_SPARK;
                    default -> dust(w, 0, 1.0F);
                };
                if (age % 3 == 0) {
                    for (int k = 0; k < 4; k++) {
                        double a = k * Mth.HALF_PI;
                        Vec3 c0 = o.pos.add(Math.cos(a) * s, 0, Math.sin(a) * s), c1 = o.pos.add(Math.cos(a + Mth.HALF_PI) * s, 0, Math.sin(a + Mth.HALF_PI) * s);
                        line(l, edge, c0, c1, 0.3);
                        line(l, edge, c0.add(0, 1.4, 0), c1.add(0, 1.4, 0), 0.3);
                        line(l, edge, c0, c0.add(0, 1.4, 0), 0.3);
                    }
                }
                if (o.stage == 3 && age % 2 == 0) {
                    put(l, ParticleTypes.END_ROD, o.pos.add(0, 1.6, 0), (R.nextDouble() - 0.5) * 0.05, 0.03, (R.nextDouble() - 0.5) * 0.05);
                }
            }
            case 6 -> { // a guard: a disc before its owner, cracking
                Entity owner = l.getEntity(o.owner);
                Vec3 base = owner != null ? owner.position() : o.pos;
                float h = owner != null ? owner.getBbHeight() : 2;
                Vec3 f = new Vec3(o.dir.x, 0, o.dir.z).normalize();
                Vec3 side = new Vec3(-f.z, 0, f.x);
                Vec3 c = base.add(0, h * 0.55, 0).add(f.scale(o.radius * 0.9 + 0.4));
                int n = 18;
                for (int k = 0; k < n; k++) {
                    if (o.stage >= 2 && (k % (5 - o.stage)) == 0) {
                        continue;
                    }
                    double a = k * Mth.TWO_PI / n + age * 0.04;
                    double r = h * 0.5;
                    put(l, dust(w, o.stage >= 1 ? 2 : 0, 1.0F), c.add(side.scale(Math.cos(a) * r)).add(0, Math.sin(a) * r, 0), 0, 0, 0);
                }
                if (o.stage >= 1 && age % 5 == 0) {
                    put(l, ParticleTypes.CRIT, c, 0, 0, 0);
                }
            }
            case 8 -> { // a summoning circle
                circle(l, dust(w, 0, 1.1F), o.pos, o.radius, 20, age * 0.15);
                circle(l, ParticleTypes.PORTAL, o.pos, o.radius * 0.6, 8, -age * 0.2);
            }
            case 9 -> warn(l, o, age);
            case 10 -> { // a chain, a thread, a curse's tie
                Entity owner = l.getEntity(o.owner);
                if (owner != null) {
                    Vec3 from = owner.position().add(0, owner.getBbHeight() * 0.6, 0);
                    line(l, o.stage == 1 ? ParticleTypes.SOUL_FIRE_FLAME : dust(w, 1, 0.8F), from, o.pos.add(o.dir).add(0, 1, 0), 0.5);
                }
            }
            default -> {
            }
        }
    }

    /** The warnings: where a blow, a fall, a beam or a field will come. Red-edged, in the technique's colour. */
    private static void warn(ClientLevel l, Obj o, int age) {
        Waza w = o.w;
        DustParticleOptions red = new DustParticleOptions(new Vector3f(1.0F, 0.15F, 0.1F), 1.0F);
        switch (o.stage) {
            case 0 -> { // a blow's reach: an arc on the ground before the caster
                Vec3 f = new Vec3(o.dir.x, 0, o.dir.z).normalize();
                for (int k = -6; k <= 6; k++) {
                    Vec3 d = f.yRot(k * 0.15F);
                    put(l, k % 3 == 0 ? red : dust(w, 0, 0.8F), o.pos.add(d.scale(o.radius)).add(0, 0.1, 0), 0, 0, 0);
                }
            }
            case 1 -> circle(l, (age & 1) == 0 ? red : dust(w, 0, 1.0F), o.pos, o.radius, Math.min(36, 10 + (int) (o.radius * 2)), 0);
            case 2 -> {
                if (age % 2 == 0) {
                    line(l, dust(w, 0, 0.6F), o.pos, o.pos.add(o.dir.normalize().scale(Math.min(o.radius, 12))), 0.8);
                }
            }
            case 3 -> line(l, red, o.pos, o.pos.add(o.dir.normalize().scale(o.radius)), 0.6);
            case 4 -> circle(l, ParticleTypes.NOTE, o.pos.add(0, 0.2, 0), 1.0 + age * 0.05, 8, age * 0.3);
            default -> {
                Vec3 c = o.pos.add(0, 0.05, 0);
                DustParticleOptions blue = new DustParticleOptions(new Vector3f(0.4F, 0.8F, 1.0F), 0.8F);
                double s = 0.8;
                line(l, blue, c.add(-s, 0, -s), c.add(s, 0, -s), 0.25);
                line(l, blue, c.add(s, 0, -s), c.add(s, 0, s), 0.25);
                line(l, blue, c.add(s, 0, s), c.add(-s, 0, s), 0.25);
                line(l, blue, c.add(-s, 0, s), c.add(-s, 0, -s), 0.25);
            }
        }
    }

    /** A shot in its technique's own shape: a star, a coin, a rock, a feather, a blade, a card, an arrow, a letter... */
    private static void shape(ClientLevel l, Waza w, Vec3 at, Vec3 dir, int age) {
        Vec3 f = dir.lengthSqr() < 1e-6 ? new Vec3(0, 0, 1) : dir.normalize();
        Vec3 s = new Vec3(-f.z, 0, f.x);
        if (s.lengthSqr() < 1e-6) {
            s = new Vec3(1, 0, 0);
        }
        s = s.normalize();
        Vec3 u = f.cross(s).normalize();
        float r = 0.25F + w.tier() * 0.1F;
        switch (w.shape()) {
            case 0 -> { // star: five points turning
                for (int k = 0; k < 5; k++) {
                    double a = age * 0.4 + k * Mth.TWO_PI / 5;
                    put(l, dust(w, 0, 0.9F), at.add(s.scale(Math.cos(a) * r * 1.6)).add(u.scale(Math.sin(a) * r * 1.6)), 0, 0, 0);
                }
                put(l, ParticleTypes.END_ROD, at, 0, 0, 0);
            }
            case 1 -> { // coin: a spinning disc
                double a = age * 0.6;
                for (int k = 0; k < 6; k++) {
                    double b = k * Mth.TWO_PI / 6;
                    put(l, dust(w, 0, 0.7F), at.add(s.scale(Math.cos(b) * r * Math.cos(a))).add(u.scale(Math.sin(b) * r)), 0, 0, 0);
                }
            }
            case 2 -> { // rock
                put(l, dust(w, 0, 2.0F), at, 0, 0, 0);
                put(l, ParticleTypes.POOF, at.subtract(f.scale(0.4)), 0, 0.02, 0);
            }
            case 3 -> { // feather: a soft trail
                put(l, ParticleTypes.END_ROD, at, 0, 0, 0);
                put(l, dust(w, 1, 0.8F), at.subtract(f.scale(0.3)).add(u.scale(Math.sin(age) * 0.15)), 0, 0, 0);
            }
            case 4 -> line(l, dust(w, 0, 0.9F), at.add(s.scale(r * 2)), at.subtract(s.scale(r * 2)), 0.15); // blade: a crescent edge
            case 5 -> { // card
                for (int k = 0; k < 4; k++) {
                    double a = age * 0.3 + k * Mth.HALF_PI;
                    put(l, dust(w, 0, 0.6F), at.add(s.scale(Math.cos(a) * r)).add(u.scale(Math.sin(a) * r * 1.4)), 0, 0, 0);
                }
            }
            case 6 -> line(l, dust(w, 0, 0.7F), at, at.subtract(f.scale(1.0)), 0.2); // arrow, needle, spear
            case 7 -> { // letter: glyphs
                put(l, ParticleTypes.ENCHANT, at, (R.nextDouble() - 0.5) * 0.2, 0, (R.nextDouble() - 0.5) * 0.2);
                put(l, dust(w, 0, 1.0F), at, 0, 0, 0);
            }
            case 8 -> { // flower
                put(l, ParticleTypes.CHERRY_LEAVES, at, 0, 0, 0);
                put(l, dust(w, 0, 1.0F), at, 0, 0, 0);
            }
            case 9 -> put(l, ParticleTypes.BUBBLE_POP, at, 0, 0, 0);
            case 10 -> put(l, ParticleTypes.ELECTRIC_SPARK, at, (R.nextDouble() - 0.5) * 0.3, (R.nextDouble() - 0.5) * 0.3, 0);
            case 11 -> put(l, ParticleTypes.FLAME, at, 0, 0, 0);
            case 12 -> put(l, ParticleTypes.SPLASH, at, 0, 0, 0);
            case 13 -> put(l, ParticleTypes.SOUL, at, 0, 0.01, 0);
            case 14 -> { // cube
                for (int k = 0; k < 4; k++) {
                    double a = k * Mth.HALF_PI + age * 0.2;
                    put(l, dust(w, 0, 0.7F), at.add(s.scale(Math.cos(a) * r)).add(u.scale(Math.sin(a) * r)), 0, 0, 0);
                }
            }
            default -> { // an orb of light
                put(l, dust(w, 0, 1.2F + w.tier() * 0.3F), at, 0, 0, 0);
                if ((age & 1) == 0) {
                    put(l, named(w, 1), at.subtract(f.scale(0.3)), 0, 0, 0);
                }
            }
        }
    }

    private static void fx(ClientLevel l, WazaNet.Fx f) {
        Waza w = f.index() >= 0 ? Waza.of(f.index()) : null;
        Vec3 at = new Vec3(f.x(), f.y(), f.z());
        switch (f.kind()) {
            case 0 -> { // a hit
                for (int k = 0; k < 8; k++) {
                    put(l, ParticleTypes.CRIT, at, (R.nextDouble() - 0.5) * 0.6, R.nextDouble() * 0.4, (R.nextDouble() - 0.5) * 0.6);
                    put(l, dust(w, 0, 1.0F), at.add((R.nextDouble() - 0.5) * 0.6, (R.nextDouble() - 0.5) * 0.6, (R.nextDouble() - 0.5) * 0.6), 0, 0, 0);
                }
            }
            case 1 -> { // an impact
                circle(l, dust(w, 0, 1.3F), at, Math.max(0.6, f.a()), 16, 0);
                put(l, ParticleTypes.POOF, at, 0, 0.05, 0);
            }
            case 2 -> { // a guard broken
                for (int k = 0; k < 16; k++) {
                    put(l, ParticleTypes.CRIT, at, (R.nextDouble() - 0.5), R.nextDouble() * 0.5, (R.nextDouble() - 0.5));
                }
                if (w != null) {
                    sound(l, at, "item.shield.break", 1, 0.8F);
                }
            }
            case 3 -> { // a rewind: a clock face turning backwards where it was
                for (int k = 0; k < 24; k++) {
                    double a = -k * Mth.TWO_PI / 24;
                    put(l, dust(w, 0, 1.0F), at.add(Math.cos(a) * 1.2, 1 + Math.sin(a) * 1.2, 0), 0, 0, 0);
                }
                sound(l, at, "block.respawn_anchor.charge", 0.8F, 1.6F);
            }
            case 4 -> { // something learned
                for (int k = 0; k < 20; k++) {
                    put(l, ParticleTypes.ENCHANT, at.add((R.nextDouble() - 0.5) * 2, R.nextDouble(), (R.nextDouble() - 0.5) * 2), 0, -0.3, 0);
                }
                sound(l, at, "block.enchantment_table.use", 0.8F, 1.2F);
            }
            case 5 -> { // a heal
                for (int k = 0; k < 6; k++) {
                    put(l, ParticleTypes.HEART, at.add((R.nextDouble() - 0.5), R.nextDouble() * 0.6, (R.nextDouble() - 0.5)), 0, 0.05, 0);
                }
            }
            case 6 -> {
                for (int k = 0; k < 20; k++) {
                    put(l, ParticleTypes.TOTEM_OF_UNDYING, at, (R.nextDouble() - 0.5) * 0.8, R.nextDouble() * 0.8, (R.nextDouble() - 0.5) * 0.8);
                }
            }
            case 7 -> { // a curse goes off
                for (int k = 0; k < 14; k++) {
                    put(l, k % 2 == 0 ? ParticleTypes.SOUL : ParticleTypes.WITCH, at, (R.nextDouble() - 0.5) * 0.4, R.nextDouble() * 0.3,
                        (R.nextDouble() - 0.5) * 0.4);
                }
                sound(l, at, "entity.wither.ambient", 0.6F, 1.4F);
            }
            case 8 -> { // a contract sealed or paid
                circle(l, new DustParticleOptions(new Vector3f(0.95F, 0.78F, 0.2F), 1.2F), at, 1.0, 20, 0);
                sound(l, at, f.a() > 1.5F ? "block.chain.break" : "block.amethyst_block.chime", 0.9F, 1.0F);
            }
            case 9 -> { // a step across space: a trail from where it was
                Entity e = f.entity() >= 0 ? l.getEntity(f.entity()) : null;
                if (e != null) {
                    line(l, ParticleTypes.PORTAL, at.add(0, 1, 0), e.position().add(0, 1, 0), 0.5);
                }
            }
            case 10 -> {
                for (int k = 0; k < 8; k++) {
                    put(l, ParticleTypes.WITCH, at.add((R.nextDouble() - 0.5), 0, (R.nextDouble() - 0.5)), 0, 0.05, 0);
                }
            }
            case 11 -> {
                for (int k = 0; k < 10; k++) {
                    put(l, ParticleTypes.PORTAL, at, (R.nextDouble() - 0.5), R.nextDouble(), (R.nextDouble() - 0.5));
                }
            }
            case 12 -> put(l, ParticleTypes.EXPLOSION, at, 0, 0, 0);
            case 13 -> line(l, ParticleTypes.END_ROD, at, at.add(0, 6, 0), 0.3);
            default -> {
            }
        }
    }

    // ---------------------------------------------------------------------------------------------- props on the body

    @SubscribeEvent
    public static void render(RenderLevelStageEvent e) {
        if (e.getStage() != RenderLevelStageEvent.Stage.AFTER_ENTITIES || PLAYS.isEmpty()) {
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        ClientLevel l = mc.level;
        if (l == null) {
            return;
        }
        Camera cam = e.getCamera();
        Vec3 cp = cam.getPosition();
        float partial = e.getPartialTick().getGameTimeDeltaPartialTick(false);
        MultiBufferSource.BufferSource buffers = mc.renderBuffers().bufferSource();
        VertexConsumer vc = buffers.getBuffer(RenderType.lightning());
        PoseStack ps = e.getPoseStack();
        boolean any = false;
        for (Map.Entry<Integer, Play> en : PLAYS.entrySet()) {
            Play p = en.getValue();
            if (p.w().props() == 0) {
                continue;
            }
            Entity ent = l.getEntity(en.getKey());
            if (!(ent instanceof LivingEntity le) || ent.distanceToSqr(cp) > 96 * 96) {
                continue;
            }
            float t = l.getGameTime() - p.start() + partial;
            float total = p.w().length();
            float fade = Math.min(1, Math.min(t / 6F, (total - t) / 8F));
            if (fade <= 0) {
                continue;
            }
            Vec3 at = ent.getPosition(partial);
            ps.pushPose();
            ps.translate(at.x - cp.x, at.y - cp.y, at.z - cp.z);
            ps.mulPose(com.mojang.math.Axis.YP.rotationDegrees(-Mth.rotLerp(partial, le.yBodyRotO, le.yBodyRot)));
            props(ps.last().pose(), vc, p.w(), ent.getBbHeight(), ent.getBbWidth(), t, fade);
            ps.popPose();
            any = true;
        }
        if (any) {
            buffers.endBatch(RenderType.lightning());
        }
    }

    private static void quad(VertexConsumer vc, Matrix4f m, Vec3 a, Vec3 b, Vec3 c, Vec3 d, int argb) {
        int A = argb >>> 24, R0 = (argb >> 16) & 0xFF, G = (argb >> 8) & 0xFF, B = argb & 0xFF;
        vc.addVertex(m, (float) a.x, (float) a.y, (float) a.z).setColor(R0, G, B, A);
        vc.addVertex(m, (float) b.x, (float) b.y, (float) b.z).setColor(R0, G, B, A);
        vc.addVertex(m, (float) c.x, (float) c.y, (float) c.z).setColor(R0, G, B, A);
        vc.addVertex(m, (float) d.x, (float) d.y, (float) d.z).setColor(R0, G, B, A);
        // both faces
        vc.addVertex(m, (float) d.x, (float) d.y, (float) d.z).setColor(R0, G, B, A);
        vc.addVertex(m, (float) c.x, (float) c.y, (float) c.z).setColor(R0, G, B, A);
        vc.addVertex(m, (float) b.x, (float) b.y, (float) b.z).setColor(R0, G, B, A);
        vc.addVertex(m, (float) a.x, (float) a.y, (float) a.z).setColor(R0, G, B, A);
    }

    private static int argb(int rgb, float alpha) {
        return ((int) (Mth.clamp(alpha, 0, 1) * 200) << 24) | (rgb & 0xFFFFFF);
    }

    /** A ring in the plane of u and v, about c. */
    private static void ring(VertexConsumer vc, Matrix4f m, Vec3 c, Vec3 u, Vec3 v, double r, double width, int n, int argb) {
        for (int k = 0; k < n; k++) {
            double a0 = k * Mth.TWO_PI / n, a1 = (k + 1) * Mth.TWO_PI / n;
            Vec3 o0 = c.add(u.scale(Math.cos(a0) * r)).add(v.scale(Math.sin(a0) * r)), o1 = c.add(u.scale(Math.cos(a1) * r)).add(v.scale(Math.sin(a1) * r));
            Vec3 i0 = c.add(u.scale(Math.cos(a0) * (r - width))).add(v.scale(Math.sin(a0) * (r - width)));
            Vec3 i1 = c.add(u.scale(Math.cos(a1) * (r - width))).add(v.scale(Math.sin(a1) * (r - width)));
            quad(vc, m, o0, o1, i1, i0, argb);
        }
    }

    private static void cube(VertexConsumer vc, Matrix4f m, Vec3 c, double s, int argb) {
        Vec3 x = new Vec3(s, 0, 0), y = new Vec3(0, s, 0), z = new Vec3(0, 0, s);
        quad(vc, m, c.subtract(x).subtract(y).add(z), c.add(x).subtract(y).add(z), c.add(x).add(y).add(z), c.subtract(x).add(y).add(z), argb);
        quad(vc, m, c.subtract(x).subtract(y).subtract(z), c.subtract(x).add(y).subtract(z), c.add(x).add(y).subtract(z), c.add(x).subtract(y).subtract(z),
            argb);
        quad(vc, m, c.subtract(x).add(y).subtract(z), c.subtract(x).add(y).add(z), c.add(x).add(y).add(z), c.add(x).add(y).subtract(z), argb);
        quad(vc, m, c.subtract(x).subtract(y).subtract(z), c.add(x).subtract(y).subtract(z), c.add(x).subtract(y).add(z), c.subtract(x).subtract(y).add(z),
            argb);
        quad(vc, m, c.add(x).subtract(y).subtract(z), c.add(x).add(y).subtract(z), c.add(x).add(y).add(z), c.add(x).subtract(y).add(z), argb);
        quad(vc, m, c.subtract(x).subtract(y).subtract(z), c.subtract(x).subtract(y).add(z), c.subtract(x).add(y).add(z), c.subtract(x).add(y).subtract(z),
            argb);
    }

    /** The technique's props, in the body's frame (facing +z). */
    private static void props(Matrix4f m, VertexConsumer vc, Waza w, float h, float wd, float t, float fade) {
        int c0 = w.colours()[0], c1 = w.colours()[1], c2 = w.colours()[2];
        Vec3 X = new Vec3(1, 0, 0), Y = new Vec3(0, 1, 0), Z = new Vec3(0, 0, 1);
        float k = h / 2F;
        if (w.prop("halo")) {
            Vec3 c = new Vec3(0, h + 0.3 * k, -0.1 * k);
            ring(vc, m, c, X.yRot(t * 0.03F), Z.yRot(t * 0.03F), 0.4 * k, 0.07 * k, 24, argb(c0, fade));
        }
        if (w.prop("crown")) {
            Vec3 c = new Vec3(0, h + 0.05 * k, 0);
            ring(vc, m, c, X, Z, 0.28 * k, 0.05 * k, 16, argb(c1, fade));
            for (int i = 0; i < 6; i++) {
                double a = i * Mth.TWO_PI / 6;
                Vec3 base = c.add(Math.cos(a) * 0.26 * k, 0, Math.sin(a) * 0.26 * k);
                Vec3 side = new Vec3(-Math.sin(a), 0, Math.cos(a)).scale(0.06 * k);
                quad(vc, m, base.subtract(side), base.add(side), base.add(0, 0.22 * k, 0), base.add(0, 0.22 * k, 0), argb(c1, fade));
            }
        }
        if (w.prop("robe")) {
            for (int i = 0; i < 6; i++) {
                double y0 = h * 0.75 - i * h * 0.12, y1 = y0 - h * 0.12;
                double wave0 = Math.sin(t * 0.2 + i) * 0.15 * k, wave1 = Math.sin(t * 0.2 + i + 1) * 0.15 * k;
                quad(vc, m, new Vec3(-0.35 * k, y0, -0.25 * k - wave0), new Vec3(0.35 * k, y0, -0.25 * k - wave0),
                    new Vec3(0.4 * k, y1, -0.3 * k - wave1), new Vec3(-0.4 * k, y1, -0.3 * k - wave1), argb(c2, fade * 0.7F));
            }
        }
        if (w.prop("tomes")) {
            for (int i = 0; i < 3; i++) {
                double a = t * 0.08 + i * Mth.TWO_PI / 3;
                cube(vc, m, new Vec3(Math.cos(a) * 0.9 * k, h * 0.6 + Math.sin(t * 0.1 + i) * 0.1, Math.sin(a) * 0.9 * k), 0.12 * k, argb(c1, fade));
            }
        }
        for (int i = 0; i < 2; i++) {
            if (w.prop(i == 0 ? "orb1" : "orb2")) {
                double a = t * 0.12 + i * Math.PI;
                cube(vc, m, new Vec3(Math.cos(a) * 0.75 * k, h * 0.75, Math.sin(a) * 0.75 * k), 0.09 * k, argb(c0, fade));
            }
            if (w.prop(i == 0 ? "fruit1" : "fruit2")) {
                cube(vc, m, new Vec3((i == 0 ? -0.5 : 0.5) * k, h * 0.9 + Math.sin(t * 0.15 + i) * 0.08, 0.2 * k), 0.08 * k, argb(c2, fade));
            }
        }
        if (w.prop("wheel")) {
            Vec3 c = new Vec3(0, h * 0.65, -0.45 * k);
            Vec3 u = X.zRot(t * 0.05F), v = Y.zRot(t * 0.05F);
            ring(vc, m, c, u, v, 0.6 * k, 0.06 * k, 28, argb(c0, fade));
            for (int i = 0; i < 6; i++) {
                double a = t * 0.05 + i * Mth.TWO_PI / 6;
                Vec3 d = X.scale(Math.cos(a)).add(Y.scale(Math.sin(a)));
                Vec3 n = new Vec3(-d.y, d.x, 0).scale(0.02 * k);
                quad(vc, m, c.add(n), c.subtract(n), c.add(d.scale(0.55 * k)).subtract(n), c.add(d.scale(0.55 * k)).add(n), argb(c1, fade));
            }
        }
        if (w.prop("core")) {
            float pulse = 0.12F + 0.03F * Mth.sin(t * 0.4F);
            cube(vc, m, new Vec3(0, h * 0.62, 0.2 * k), pulse * k, argb(c0, fade));
        }
        if (w.prop("grip_r")) {
            int wu = w.windup();
            float a = t - wu;
            if (a >= 0 && a <= w.activeLength()) {
                for (int i = 0; i < 6; i++) {
                    double a0 = -1.2 + i * 0.4, a1 = a0 + 0.4;
                    double r = (w.range() * 0.6 + wd * 0.5);
                    Vec3 p0 = new Vec3(Math.sin(a0) * r, h * 0.6, Math.cos(a0) * r), p1 = new Vec3(Math.sin(a1) * r, h * 0.6, Math.cos(a1) * r);
                    quad(vc, m, p0, p1, p1.add(0, 0.12 * k, 0), p0.add(0, 0.12 * k, 0), argb(c0, fade * (1 - Math.abs(i - 2.5F) / 3F)));
                }
            }
        }
        if (w.prop("fin_r")) {
            for (int s = -1; s <= 1; s += 2) {
                double flap = Math.sin(t * 0.3) * 0.2;
                Vec3 base = new Vec3(s * wd * 0.5, h * 0.5, 0);
                quad(vc, m, base, base.add(s * 0.5 * k, 0.2 * k + flap, -0.2 * k), base.add(s * 0.6 * k, -0.3 * k + flap, -0.4 * k),
                    base.add(0, -0.3 * k, -0.1 * k), argb(c1, fade * 0.8F));
            }
        }
    }
}
