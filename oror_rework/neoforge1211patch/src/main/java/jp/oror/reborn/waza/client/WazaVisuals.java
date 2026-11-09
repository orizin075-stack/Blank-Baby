package jp.oror.reborn.waza.client;

import com.mojang.blaze3d.vertex.VertexConsumer;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import jp.oror.reborn.waza.Waza;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleType;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;
import org.joml.Matrix4f;

/**
 * (057) The techniques' light: glowing shapes drawn in the world, and particles from every mod in the pack.
 *
 * <p>Shapes (drawn additively, so that they glow): a blade's afterimage along the path the server sweeps, bright at
 * its edge and fading in a few ticks; the crescent wave a great cut sends out; the ring an impact spreads on the ground;
 * the turning magic circle under a caster through its windup (upright before it for a shot or a beam); a beam's
 * body and white core, pulsing; a field's edge and its runes; a song's spreading ring; a guard's six-sided screen,
 * cracking; a summoning circle; a curse's sigil over its bearer; a rewind's clock face turning backwards.
 *
 * <p>Particles: every simple particle type registered in the game (Minecraft's and every mod's: Iron's Spells, Epic
 * Fight, Alex's Caves, Ice and Fire and the rest) is sorted by its name into themes (a cut, sparks, fire, frost,
 * lightning, poison, darkness, holy light, water, earth, wind, magic, blood, nature); each technique takes its themes
 * from what it does and its colours, and from each theme particles of its own (chosen by its id, the mods' first),
 * so that the 984 do not all throw the same sparks. A particle type that fails to appear is not asked again.
 */
public final class WazaVisuals {
    private WazaVisuals() {
    }

    // ---------------------------------------------------------------------------------------------------- the themes

    public enum Theme { SLASH, SPARK, FIRE, FROST, LIGHTNING, POISON, DARK, HOLY, WATER, EARTH, WIND, MAGIC, BLOOD, NATURE }

    private static final Map<Theme, String[]> WORDS = new EnumMap<>(Map.ofEntries(
        Map.entry(Theme.SLASH, new String[]{"slash", "sweep", "blade", "cut", "swing", "crescent", "slice", "sword"}),
        Map.entry(Theme.SPARK, new String[]{"spark", "crit", "hit", "impact", "shine", "twinkle", "glint"}),
        Map.entry(Theme.FIRE, new String[]{"fire", "flame", "ember", "burn", "blaze", "lava", "magma", "cinder", "heat"}),
        Map.entry(Theme.FROST, new String[]{"snow", "frost", "ice", "freez", "cold", "chill", "icicle"}),
        Map.entry(Theme.LIGHTNING, new String[]{"electr", "zap", "shock", "volt", "static", "spark"}),
        Map.entry(Theme.POISON, new String[]{"poison", "acid", "toxic", "spore", "venom", "ooze", "slime"}),
        Map.entry(Theme.DARK, new String[]{"dark", "shadow", "soul", "curse", "necro", "wither", "ghost", "doom", "sculk", "ash"}),
        Map.entry(Theme.HOLY, new String[]{"holy", "light", "glow", "sparkle", "star", "wisp", "heal", "halo", "bless", "divine", "end_rod"}),
        Map.entry(Theme.WATER, new String[]{"bubble", "water", "splash", "drip", "rain", "foam"}),
        Map.entry(Theme.EARTH, new String[]{"rock", "stone", "debris", "sand", "earth", "rubble", "mud", "pebble"}),
        Map.entry(Theme.WIND, new String[]{"wind", "gust", "air", "poof", "puff", "feather"}),
        Map.entry(Theme.MAGIC, new String[]{"magic", "spell", "rune", "arcane", "enchant", "mana", "witch", "ender", "glyph"}),
        Map.entry(Theme.BLOOD, new String[]{"blood", "gore", "flesh"}),
        Map.entry(Theme.NATURE, new String[]{"leaf", "leaves", "petal", "flower", "cherry", "pollen", "vine", "happy"})));
    /**
     * Never these: what is not a mote but a scene (vortices, black holes, storms, clouds and fog, domes, waves, rings,
     * beams, explosions, flashes, portals: in the first look at the new light a mod's vortex swallowed the stage and
     * another's cloud whited it out), and what is not meant to be thrown about (items, blocks, vanilla's emitters).
     */
    private static final Set<String> NEVER = Set.of("item", "block", "falling", "vibration", "shriek", "elder_guardian", "mob_appearance",
        "dust_plume", "sonic", "trial", "ominous", "barrier", "light_block", "entity_effect", "explosion", "sculk_charge", "camera", "screen",
        "vortex", "hole", "storm", "tornado", "cloud", "fog", "mist", "haze", "dome", "wave", "ring", "beam", "laser", "aurora", "nova", "blast",
        "sphere", "aura", "shield", "wall", "pillar", "flash", "sun", "moon", "sky", "giant", "large", "big", "huge", "massive", "boss", "crater",
        "rift", "void", "abyss", "portal", "lightning", "thunder", "smoke", "swirl", "cyclone", "geyser", "eruption", "nuke", "meteor", "comet",
        "trail", "streak", "ray", "column", "tower", "circle", "emitter", "burst", "shockwave", "quake", "tremor", "flare", "glare");
    private static Map<Theme, List<SimpleParticleType>> themes;
    private static final Set<ParticleType<?>> FAILED = new HashSet<>();

    private static synchronized void sort() {
        if (themes != null) {
            return;
        }
        Map<Theme, List<SimpleParticleType>> mods = new EnumMap<>(Theme.class), vanilla = new EnumMap<>(Theme.class);
        for (Theme t : Theme.values()) {
            mods.put(t, new ArrayList<>());
            vanilla.put(t, new ArrayList<>());
        }
        for (Map.Entry<net.minecraft.resources.ResourceKey<ParticleType<?>>, ParticleType<?>> e : BuiltInRegistries.PARTICLE_TYPE.entrySet()) {
            if (!(e.getValue() instanceof SimpleParticleType simple)) {
                continue;
            }
            ResourceLocation id = e.getKey().location();
            String path = id.getPath().toLowerCase(Locale.ROOT);
            if (NEVER.stream().anyMatch(path::contains)) {
                continue;
            }
            for (Theme t : Theme.values()) {
                for (String w : WORDS.get(t)) {
                    if (path.contains(w)) {
                        (id.getNamespace().equals("minecraft") ? vanilla : mods).get(t).add(simple);
                        break;
                    }
                }
            }
        }
        Map<Theme, List<SimpleParticleType>> out = new EnumMap<>(Theme.class);
        for (Theme t : Theme.values()) {
            List<SimpleParticleType> l = new ArrayList<>(mods.get(t));
            l.addAll(vanilla.get(t));
            if (l.isEmpty()) {
                l.add(ParticleTypes.END_ROD);
            }
            out.put(t, l);
        }
        themes = out;
        org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger("OROR Waza");
        out.forEach((t, l) -> log.info("OROR WAZA-PARTICLES {} {}: {}", t, l.size(), l.stream().limit(16)
            .map(x -> String.valueOf(BuiltInRegistries.PARTICLE_TYPE.getKey(x))).toList()));
    }

    /** How many particle types each theme found (mods' first): for the log. */
    public static String census() {
        sort();
        StringBuilder b = new StringBuilder();
        themes.forEach((t, l) -> b.append(t).append('=').append(l.size()).append(' '));
        return b.toString().trim();
    }

    /** The technique's themes, from what it does, its verbs and its colours. */
    public static Theme[] themesOf(Waza w) {
        List<Theme> l = new ArrayList<>();
        for (String v : w.verbs()) {
            switch (v) {
                case "BURN" -> l.add(Theme.FIRE);
                case "FROST" -> l.add(Theme.FROST);
                case "SHOCK" -> l.add(Theme.LIGHTNING);
                case "POISON" -> l.add(Theme.POISON);
                case "WITHER", "FEAR", "CONFUSE", "BLIND" -> l.add(Theme.DARK);
                case "HEAL_ALLY", "WARD", "CLEANSE", "DEATHWARD" -> l.add(Theme.HOLY);
                case "DRAIN" -> l.add(Theme.BLOOD);
                case "KNOCK", "LIFT", "PULL" -> l.add(Theme.WIND);
                case "SLAM", "SHATTER", "BLAST" -> l.add(Theme.EARTH);
                case "STOP", "SILENCE", "DISPEL", "GRAVITY", "SWAP", "SHRINK", "MARK" -> l.add(Theme.MAGIC);
                default -> {
                }
            }
        }
        switch (w.behaviour()) {
            case MELEE -> l.add(0, Theme.SLASH);
            case GROWTH -> l.add(Theme.NATURE);
            case SONG -> l.add(Theme.WIND);
            case CURSE -> l.add(Theme.DARK);
            case HEAL -> l.add(Theme.HOLY);
            default -> l.add(Theme.MAGIC);
        }
        // the colour says what words do not: a sea-green technique is water, a deep red one blood, a gold one holy
        int c = w.colours()[0];
        float r = ((c >> 16) & 255) / 255F, g = ((c >> 8) & 255) / 255F, bl = (c & 255) / 255F;
        if (bl > 0.6F && g > 0.5F && r < 0.5F) {
            l.add(Theme.WATER);
        } else if (r > 0.6F && g < 0.3F && bl < 0.3F) {
            l.add(Theme.BLOOD);
        } else if (r > 0.8F && g > 0.6F && bl < 0.4F) {
            l.add(Theme.HOLY);
        } else if (r < 0.35F && g < 0.3F && bl < 0.4F) {
            l.add(Theme.DARK);
        }
        l.add(Theme.SPARK);
        return l.stream().distinct().limit(4).toArray(Theme[]::new);
    }

    /** A particle of the technique's k-th theme, its own choice among the theme's (by its id). */
    public static ParticleOptions particle(Waza w, int k) {
        sort();
        Theme[] ts = themesOf(w);
        Theme t = ts[Math.floorMod(k, ts.length)];
        List<SimpleParticleType> l = themes.get(t);
        int start = Math.floorMod(w.id().hashCode() * 31 + k * 7, l.size());
        for (int i = 0; i < l.size(); i++) {
            SimpleParticleType p = l.get((start + i) % l.size());
            if (!FAILED.contains(p)) {
                return p;
            }
        }
        return ParticleTypes.END_ROD;
    }

    /** (058) A particle of one theme, chosen among the theme's by the salt (the relics' techniques, which are no Waza). */
    public static ParticleOptions themed(Theme t, int salt) {
        sort();
        List<SimpleParticleType> l = themes.get(t);
        int start = Math.floorMod(salt, l.size());
        for (int i = 0; i < l.size(); i++) {
            SimpleParticleType p = l.get((start + i) % l.size());
            if (!FAILED.contains(p)) {
                return p;
            }
        }
        return ParticleTypes.END_ROD;
    }

    /** Puts a particle, forgetting a type that cannot appear (a mod's particle with no provider on this client). */
    public static void put(ClientLevel l, ParticleOptions p, double x, double y, double z, double vx, double vy, double vz) {
        try {
            l.addParticle(p, x, y, z, vx, vy, vz);
        } catch (RuntimeException ex) {
            FAILED.add(p.getType());
        }
    }

    // ---------------------------------------------------------------------------------------------------- the shapes

    enum Kind { TRAIL, WAVE, RING, CIRCLE, SIGIL, CLOCK, FLASH }

    /** A shape alive for a few ticks: where, how big, its colours, and its own points (a trail's blade positions). */
    static final class Shape {
        Kind kind;
        Vec3 at, dir, up;
        Vec3[] base, tip;
        float r0, r1, width;
        int c0, c1, life, points;
        long born;
        int follow = -1;
        boolean upright;
        float spin;
    }

    private static final List<Shape> SHAPES = new ArrayList<>();
    private static final RandomSource R = RandomSource.create();

    static Shape add(Kind kind, long now, int life, int c0, int c1) {
        Shape s = new Shape();
        s.kind = kind;
        s.born = now;
        s.life = Math.max(1, life);
        s.c0 = c0;
        s.c1 = c1;
        if (SHAPES.size() > 400) {
            SHAPES.remove(0);
        }
        SHAPES.add(s);
        return s;
    }

    /** A blade's afterimage along a path (blade base and tip at each point of it). */
    public static void trail(long now, Vec3[] base, Vec3[] tip, Waza w) {
        Shape s = add(Kind.TRAIL, now, 7 + w.tier() * 2, w.colours()[0], w.colours()[1]);
        s.base = base;
        s.tip = tip;
    }

    /** The crescent a great cut sends out: from the caster along dir, over the arc's width. */
    public static void wave(long now, Vec3 from, Vec3 dir, float reach, Waza w) {
        Shape s = add(Kind.WAVE, now, 10 + w.tier() * 3, w.colours()[0], w.colours()[1]);
        s.at = from;
        s.dir = new Vec3(dir.x, 0, dir.z).normalize();
        s.r0 = reach;
        s.r1 = reach + 4 + w.tier() * 2;
        s.width = 0.35F + w.tier() * 0.12F;
    }

    public static void ring(long now, Vec3 at, float r0, float r1, int life, int c0, int c1, float width) {
        Shape s = add(Kind.RING, now, life, c0, c1);
        s.at = at;
        s.r0 = r0;
        s.r1 = r1;
        s.width = width;
    }

    /** A magic circle: flat on the ground, or upright before the caster facing dir. */
    public static void circle(long now, Vec3 at, float r, int life, Waza w, boolean upright, Vec3 dir, int follow) {
        Shape s = add(Kind.CIRCLE, now, life, w.colours()[0], w.colours()[1]);
        s.at = at;
        s.r0 = r;
        s.upright = upright;
        s.dir = dir == null ? new Vec3(0, 0, 1) : dir;
        s.points = 5 + Math.floorMod(w.id().hashCode(), 4);
        s.spin = (Math.floorMod(w.id().hashCode() >> 3, 2) == 0 ? 1 : -1) * (0.03F + w.tier() * 0.01F);
        s.follow = follow;
    }

    public static void sigil(long now, Entity e, Waza w, int life) {
        Shape s = add(Kind.SIGIL, now, life, w.colours()[0], 0x400030);
        s.follow = e.getId();
        s.at = e.position();
        s.r0 = Math.max(0.4F, e.getBbWidth() * 0.6F);
        s.points = 3;
    }

    public static void clock(long now, Vec3 at, Waza w) {
        Shape s = add(Kind.CLOCK, now, 20, w.colours()[0], w.colours()[1]);
        s.at = at;
        s.r0 = 1.4F;
    }

    public static void flash(long now, Vec3 at, int c, float size) {
        Shape s = add(Kind.FLASH, now, 4, c, 0xFFFFFF);
        s.at = at;
        s.r0 = Math.min(1.4F, size * 0.6F);
    }

    // --------------------------------------------------------------------------------------------------- drawing

    static void quad(VertexConsumer vc, Matrix4f m, Vec3 a, Vec3 b, Vec3 c, Vec3 d, int argb) {
        int A = argb >>> 24, R0 = (argb >> 16) & 0xFF, G = (argb >> 8) & 0xFF, B = argb & 0xFF;
        if (A <= 2) {
            return;
        }
        vc.addVertex(m, (float) a.x, (float) a.y, (float) a.z).setColor(R0, G, B, A);
        vc.addVertex(m, (float) b.x, (float) b.y, (float) b.z).setColor(R0, G, B, A);
        vc.addVertex(m, (float) c.x, (float) c.y, (float) c.z).setColor(R0, G, B, A);
        vc.addVertex(m, (float) d.x, (float) d.y, (float) d.z).setColor(R0, G, B, A);
        vc.addVertex(m, (float) d.x, (float) d.y, (float) d.z).setColor(R0, G, B, A);
        vc.addVertex(m, (float) c.x, (float) c.y, (float) c.z).setColor(R0, G, B, A);
        vc.addVertex(m, (float) b.x, (float) b.y, (float) b.z).setColor(R0, G, B, A);
        vc.addVertex(m, (float) a.x, (float) a.y, (float) a.z).setColor(R0, G, B, A);
    }

    static int argb(int rgb, float alpha) {
        return ((int) (Mth.clamp(alpha, 0, 1) * 230) << 24) | (rgb & 0xFFFFFF);
    }

    /** A ring in the plane of u and v about c (relative to the camera). */
    static void ring(VertexConsumer vc, Matrix4f m, Vec3 c, Vec3 u, Vec3 v, double r, double width, int n, int argb, double from, double span) {
        for (int k = 0; k < n; k++) {
            double a0 = from + span * k / n, a1 = from + span * (k + 1) / n;
            Vec3 o0 = c.add(u.scale(Math.cos(a0) * r)).add(v.scale(Math.sin(a0) * r));
            Vec3 o1 = c.add(u.scale(Math.cos(a1) * r)).add(v.scale(Math.sin(a1) * r));
            Vec3 i0 = c.add(u.scale(Math.cos(a0) * (r - width))).add(v.scale(Math.sin(a0) * (r - width)));
            Vec3 i1 = c.add(u.scale(Math.cos(a1) * (r - width))).add(v.scale(Math.sin(a1) * (r - width)));
            quad(vc, m, o0, o1, i1, i0, argb);
        }
    }

    /** A thin bar from a to b in the plane whose normal is n. */
    static void bar(VertexConsumer vc, Matrix4f m, Vec3 a, Vec3 b, Vec3 n, double width, int argb) {
        Vec3 d = b.subtract(a);
        Vec3 side = d.cross(n);
        if (side.lengthSqr() < 1e-8) {
            return;
        }
        side = side.normalize().scale(width / 2);
        quad(vc, m, a.subtract(side), a.add(side), b.add(side), b.subtract(side), argb);
    }

    /** Draws every living shape; cam: the camera's position. */
    public static void render(ClientLevel l, VertexConsumer vc, Matrix4f m, Vec3 cam, float partial) {
        long now = l.getGameTime();
        for (Iterator<Shape> it = SHAPES.iterator(); it.hasNext(); ) {
            Shape s = it.next();
            float age = now - s.born + partial;
            if (age > s.life || age < 0) {
                if (age > s.life) {
                    it.remove();
                }
                continue;
            }
            float u = age / s.life;
            float fade = u < 0.15F ? u / 0.15F : 1 - (u - 0.15F) / 0.85F;
            Vec3 at = s.at;
            if (s.follow >= 0) {
                Entity e = l.getEntity(s.follow);
                if (e == null) {
                    it.remove();
                    continue;
                }
                at = s.kind == Kind.SIGIL ? e.getPosition(partial).add(0, e.getBbHeight() + 0.5, 0)
                    : s.upright ? e.getPosition(partial).add(0, e.getBbHeight() * 0.55, 0).add(s.dir.scale(e.getBbWidth() * 0.6 + 0.4))
                    : e.getPosition(partial).add(0, 0.06, 0);
            }
            switch (s.kind) {
                case TRAIL -> {
                    // the afterimage: revealed along the swing in its first ticks, then thinning and fading
                    int n = s.base.length - 1;
                    float reveal = Math.min(1, age / 2F);
                    int shown = Math.max(1, Math.round(n * reveal));
                    float a = 1 - u;
                    for (int i = 0; i < shown; i++) {
                        float edge = (i + 1F) / shown;
                        Vec3 b0 = s.base[i].subtract(cam), b1 = s.base[i + 1].subtract(cam), t0 = s.tip[i].subtract(cam), t1 = s.tip[i + 1].subtract(cam);
                        Vec3 m0 = b0.lerp(t0, 0.35 + 0.4 * u), m1 = b1.lerp(t1, 0.35 + 0.4 * u);
                        quad(vc, m, m0, t0, t1, m1, argb(s.c0, a * (0.35F + 0.5F * edge)));
                        Vec3 k0 = b0.lerp(t0, 0.82), k1 = b1.lerp(t1, 0.82);
                        quad(vc, m, k0, t0, t1, k1, argb(0xFFFFFF, a * a * (0.4F + 0.6F * edge)));
                    }
                }
                case WAVE -> {
                    double r = Mth.lerp(u, s.r0, s.r1);
                    Vec3 c = at.subtract(cam).add(0, 0.9, 0);
                    Vec3 side = new Vec3(-s.dir.z, 0, s.dir.x);
                    int n = 14;
                    for (int i = 0; i < n; i++) {
                        double a0 = -0.9 + 1.8 * i / n, a1 = -0.9 + 1.8 * (i + 1) / n;
                        double w0 = s.width * Math.cos(a0 * 1.6), w1 = s.width * Math.cos(a1 * 1.6);
                        Vec3 p0 = c.add(s.dir.scale(Math.cos(a0) * r)).add(side.scale(Math.sin(a0) * r));
                        Vec3 p1 = c.add(s.dir.scale(Math.cos(a1) * r)).add(side.scale(Math.sin(a1) * r));
                        quad(vc, m, p0.add(0, -w0, 0), p0.add(0, w0, 0), p1.add(0, w1, 0), p1.add(0, -w1, 0), argb(s.c0, fade * 0.8F));
                        quad(vc, m, p0.add(0, -w0 * 0.3, 0), p0.add(0, w0 * 0.3, 0), p1.add(0, w1 * 0.3, 0), p1.add(0, -w1 * 0.3, 0),
                            argb(0xFFFFFF, fade * 0.8F));
                    }
                }
                case RING -> {
                    double r = Mth.lerp(Math.sqrt(u), s.r0, s.r1);
                    ring(vc, m, at.subtract(cam).add(0, 0.08, 0), new Vec3(1, 0, 0), new Vec3(0, 0, 1), r, s.width * (1 - u * 0.6), 40,
                        argb(s.c0, fade * 0.85F), 0, Mth.TWO_PI);
                    ring(vc, m, at.subtract(cam).add(0, 0.1, 0), new Vec3(1, 0, 0), new Vec3(0, 0, 1), r * 0.97, s.width * 0.3, 40,
                        argb(0xFFFFFF, fade * 0.6F), 0, Mth.TWO_PI);
                }
                case CIRCLE -> drawCircle(vc, m, s, at.subtract(cam), age, fade);
                case SIGIL -> {
                    Vec3 c = at.subtract(cam);
                    double turn = age * 0.12;
                    Vec3 x = new Vec3(Math.cos(turn), 0, Math.sin(turn)), z = new Vec3(-Math.sin(turn), 0, Math.cos(turn));
                    ring(vc, m, c, x, z, s.r0, 0.06, 24, argb(s.c0, fade), 0, Mth.TWO_PI);
                    for (int i = 0; i < 3; i++) {
                        double a0 = turn + i * Mth.TWO_PI / 3, a1 = turn + (i + 1) * Mth.TWO_PI / 3;
                        bar(vc, m, c.add(Math.cos(a0) * s.r0, 0, Math.sin(a0) * s.r0), c.add(Math.cos(a1) * s.r0, 0, Math.sin(a1) * s.r0),
                            new Vec3(0, 1, 0), 0.06, argb(s.c0, fade));
                    }
                }
                case CLOCK -> {
                    Vec3 c = at.subtract(cam).add(0, 1.2, 0);
                    Vec3 x = new Vec3(1, 0, 0), y = new Vec3(0, 1, 0);
                    ring(vc, m, c, x, y, s.r0, 0.08, 36, argb(s.c0, fade), 0, Mth.TWO_PI);
                    for (int i = 0; i < 12; i++) {
                        double a = i * Mth.TWO_PI / 12;
                        bar(vc, m, c.add(x.scale(Math.cos(a) * s.r0 * 0.85)).add(y.scale(Math.sin(a) * s.r0 * 0.85)),
                            c.add(x.scale(Math.cos(a) * s.r0 * 0.97)).add(y.scale(Math.sin(a) * s.r0 * 0.97)), new Vec3(0, 0, 1), 0.05, argb(s.c1, fade));
                    }
                    double hand = -age * 0.5;
                    bar(vc, m, c, c.add(x.scale(Math.cos(hand) * s.r0 * 0.8)).add(y.scale(Math.sin(hand) * s.r0 * 0.8)), new Vec3(0, 0, 1), 0.07,
                        argb(0xFFFFFF, fade));
                    bar(vc, m, c, c.add(x.scale(Math.cos(hand / 12) * s.r0 * 0.5)).add(y.scale(Math.sin(hand / 12) * s.r0 * 0.5)), new Vec3(0, 0, 1),
                        0.1, argb(s.c0, fade));
                }
                case FLASH -> {
                    Vec3 c = at.subtract(cam);
                    Vec3 toCam = c.scale(-1).normalize();
                    Vec3 a = toCam.cross(new Vec3(0, 1, 0));
                    a = a.lengthSqr() < 1e-6 ? new Vec3(1, 0, 0) : a.normalize();
                    Vec3 b = toCam.cross(a).normalize();
                    double r = s.r0 * (0.6 + u * 0.8);
                    for (int i = 0; i < 4; i++) {
                        double ang = i * Mth.HALF_PI + age * 0.3;
                        Vec3 d = a.scale(Math.cos(ang)).add(b.scale(Math.sin(ang)));
                        bar(vc, m, c, c.add(d.scale(r)), toCam, 0.12 * (1 - u), argb(i % 2 == 0 ? 0xFFFFFF : s.c0, 1 - u));
                    }
                }
                default -> {
                }
            }
        }
    }

    /** A magic circle: two rings, a star of its own number of points, runes about its rim, turning. */
    private static void drawCircle(VertexConsumer vc, Matrix4f m, Shape s, Vec3 c, float age, float fade) {
        Vec3 u, v, n;
        if (s.upright) {
            n = s.dir.normalize();
            u = n.cross(new Vec3(0, 1, 0));
            u = u.lengthSqr() < 1e-6 ? new Vec3(1, 0, 0) : u.normalize();
            v = u.cross(n).normalize();
        } else {
            u = new Vec3(1, 0, 0);
            v = new Vec3(0, 0, 1);
            n = new Vec3(0, 1, 0);
        }
        double turn = age * s.spin;
        Vec3 ru = u.scale(Math.cos(turn)).add(v.scale(Math.sin(turn))), rv = v.scale(Math.cos(turn)).subtract(u.scale(Math.sin(turn)));
        double r = s.r0 * Math.min(1, 0.4 + age / 8);
        ring(vc, m, c, ru, rv, r, 0.07, 48, argb(s.c0, fade), 0, Mth.TWO_PI);
        ring(vc, m, c, ru, rv, r * 0.82, 0.05, 40, argb(s.c1, fade * 0.9F), 0, Mth.TWO_PI);
        ring(vc, m, c, rv, ru, r * 0.36, 0.05, 24, argb(s.c0, fade), 0, Mth.TWO_PI);
        int p = s.points;
        for (int i = 0; i < p; i++) {
            double a0 = i * Mth.TWO_PI / p, a1 = ((i + 2) % p) * Mth.TWO_PI / p;
            Vec3 q0 = c.add(ru.scale(Math.cos(a0) * r * 0.82)).add(rv.scale(Math.sin(a0) * r * 0.82));
            Vec3 q1 = c.add(ru.scale(Math.cos(a1) * r * 0.82)).add(rv.scale(Math.sin(a1) * r * 0.82));
            bar(vc, m, q0, q1, n, 0.05, argb(s.c0, fade * 0.85F));
        }
        // the runes: short strokes between the rings, counter-turning
        for (int i = 0; i < 16; i++) {
            double a = -turn * 2 + i * Mth.TWO_PI / 16;
            Vec3 dir = u.scale(Math.cos(a)).add(v.scale(Math.sin(a)));
            Vec3 tang = n.cross(dir).normalize();
            Vec3 at = c.add(dir.scale(r * 0.91));
            bar(vc, m, at.subtract(tang.scale(0.07)), at.add(tang.scale(0.07)), n, 0.05, argb(0xFFFFFF, fade * (i % 2 == 0 ? 0.9F : 0.5F)));
        }
    }

    /** The world's things that stay drawn (beams, fields, guards, rings of sound, summoning circles): from the client's
     * list of them each frame. */
    static void renderThing(ClientLevel l, VertexConsumer vc, Matrix4f m, Vec3 cam, WazaClient.Obj o, float partial) {
        Waza w = o.w;
        if (w == null) {
            return;
        }
        float age = l.getGameTime() - o.born + partial;
        float fade = Mth.clamp(Math.min(age / 4F, (o.life - age) / 8F), 0, 1);
        int c0 = w.colours()[0], c1 = w.colours()[1];
        switch (o.kind) {
            case 1 -> { // a beam: crossed bands and a white core, pulsing
                Vec3 a = o.pos.subtract(cam), b = o.pos.add(o.dir.normalize().scale(o.radius)).subtract(cam);
                Vec3 d = b.subtract(a).normalize();
                Vec3 n1 = d.cross(new Vec3(0, 1, 0));
                n1 = n1.lengthSqr() < 1e-6 ? new Vec3(1, 0, 0) : n1.normalize();
                Vec3 n2 = d.cross(n1).normalize();
                double pulse = 1 + 0.15 * Math.sin(age * 1.3);
                double wdt = (0.35 + 0.15 * w.tier()) * pulse;
                bar(vc, m, a, b, n1, wdt * 2, argb(c0, fade * 0.55F));
                bar(vc, m, a, b, n2, wdt * 2, argb(c0, fade * 0.55F));
                bar(vc, m, a, b, n1, wdt * 0.5, argb(0xFFFFFF, fade));
                bar(vc, m, a, b, n2, wdt * 0.5, argb(0xFFFFFF, fade));
                ring(vc, m, a, n1, n2, wdt * 1.6, 0.08, 20, argb(c1, fade), 0, Mth.TWO_PI);
            }
            case 2 -> { // a field: its edge, an inner ring of runes turning, a faint floor
                Vec3 c = o.pos.subtract(cam).add(0, 0.07, 0);
                ring(vc, m, c, new Vec3(1, 0, 0), new Vec3(0, 0, 1), o.radius, 0.18, 64, argb(c0, fade * 0.8F), 0, Mth.TWO_PI);
                double turn = age * 0.02;
                ring(vc, m, c, new Vec3(Math.cos(turn), 0, Math.sin(turn)), new Vec3(-Math.sin(turn), 0, Math.cos(turn)), o.radius * 0.9, 0.06, 48,
                    argb(c1, fade * 0.6F), 0, Mth.TWO_PI);
                for (int i = 0; i < 24; i++) {
                    double a = -turn * 3 + i * Mth.TWO_PI / 24;
                    Vec3 p = c.add(Math.cos(a) * o.radius * 0.95, 0, Math.sin(a) * o.radius * 0.95);
                    bar(vc, m, p, p.add(Math.cos(a) * 0.4, 0, Math.sin(a) * 0.4), new Vec3(0, 1, 0), 0.12, argb(0xFFFFFF, fade * 0.5F));
                }
            }
            case 3 -> { // a ring of sound
                double r = o.radius * Math.min(1, age / Math.max(1F, o.life));
                Vec3 c = o.pos.subtract(cam).add(0, 0.6, 0);
                ring(vc, m, c, new Vec3(1, 0, 0), new Vec3(0, 0, 1), r, 0.35, 64, argb(c0, fade * 0.6F), 0, Mth.TWO_PI);
                ring(vc, m, c.add(0, 0.5, 0), new Vec3(1, 0, 0), new Vec3(0, 0, 1), r * 0.98, 0.12, 64, argb(0xFFFFFF, fade * 0.5F), 0, Mth.TWO_PI);
            }
            case 6 -> { // a guard: six panels before its owner, losing panels as it cracks
                Entity owner = l.getEntity(o.owner);
                if (owner == null) {
                    return;
                }
                Vec3 f = new Vec3(o.dir.x, 0, o.dir.z);
                f = f.lengthSqr() < 1e-6 ? new Vec3(0, 0, 1) : f.normalize();
                Vec3 side = new Vec3(-f.z, 0, f.x);
                float h = owner.getBbHeight();
                Vec3 c = owner.getPosition(partial).add(0, h * 0.55, 0).add(f.scale(owner.getBbWidth() * 0.6 + 0.5)).subtract(cam);
                double r = h * 0.55;
                for (int i = 0; i < 6; i++) {
                    if (o.stage >= 2 && (i + o.stage) % 3 == 0) {
                        continue;
                    }
                    double a0 = i * Mth.TWO_PI / 6, a1 = (i + 1) * Mth.TWO_PI / 6;
                    Vec3 p0 = c.add(side.scale(Math.cos(a0) * r)).add(0, Math.sin(a0) * r, 0), p1 = c.add(side.scale(Math.cos(a1) * r)).add(0, Math.sin(a1) * r, 0);
                    quad(vc, m, c, p0, p1, c, argb(c0, fade * (o.stage >= 1 ? 0.25F : 0.35F)));
                    bar(vc, m, p0, p1, f, 0.07, argb(o.stage >= 1 ? 0xFF8060 : 0xFFFFFF, fade));
                }
            }
            case 8 -> {
                Shape s = new Shape();
                s.r0 = o.radius;
                s.c0 = c0;
                s.c1 = c1;
                s.points = 6;
                s.spin = 0.05F;
                s.dir = new Vec3(0, 0, 1);
                drawCircle(vc, m, s, o.pos.subtract(cam).add(0, 0.06, 0), age, fade);
            }
            default -> {
            }
        }
    }

    /** Sparks of the technique's own particles bursting from a point. */
    public static void burst(ClientLevel l, Waza w, Vec3 at, int n, double speed) {
        for (int i = 0; i < n; i++) {
            ParticleOptions p = particle(w, i);
            put(l, p, at.x, at.y, at.z, (R.nextDouble() - 0.5) * speed, (R.nextDouble() - 0.3) * speed, (R.nextDouble() - 0.5) * speed);
        }
    }
}
