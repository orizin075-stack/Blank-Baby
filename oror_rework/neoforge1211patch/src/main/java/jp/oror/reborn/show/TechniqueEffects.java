package jp.oror.reborn.show;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import org.joml.Vector3f;

/**
 * (052) The magic of each technique, drawn on the client in the character's own two colours (taken from its skin):
 * through the windup a double magic circle turns under its feet, the outer ring one way and the inner the other, with
 * runes rising from it; on the moment the technique goes off its kind gives it its own shape: a crescent of the cut,
 * a white line of erasure, a hexagon of reflection, a spiral of growth, a clock face turning back, rays from the sky,
 * the square seal on the enemy, a dome of guard, portals at both ends of a shift, the pillar of a judgement, a
 * prismatic sphere, gold drawn into the hands, a summoning circle with its five fires, a helix of mana, streaks of a
 * barrage, a shockwave ring, a smith's sparks, rising light and hearts, a red stream drawn out of the enemy, a dark
 * spiral of a curse, a pulling line, cards in orbit, a mirror's flash, confetti, a bolt's beam, a flyer's gust.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses", value = Dist.CLIENT)
public final class TechniqueEffects {
    private static final Map<String, int[]> COLOURS = new HashMap<>();
    private static final Map<Integer, Long> RELEASED = new HashMap<>();

    static {
        String[][] c = {
            {"ain_sof_aur", "6d5cbf", "f2e6a0"}, {"angra_mainyu", "bf7b5a", "bf3e60"}, {"arcana", "eed78a", "693ebf"}, {"bahamut", "307fbf", "bf577b"},
            {"berit", "bf9039", "64e4a2"}, {"brutality", "bf7857", "bf274e"}, {"chaos", "823bbf", "d97b34"}, {"cursed_love", "bf4579", "ffb0d0"},
            {"demiurgos", "7c5cbf", "bf44a5"}, {"elseria", "2f61bf", "a8d8ff"}, {"enkou", "63bee2", "bf3b55"}, {"eomaia", "bf914c", "61bf96"},
            {"fallen_savior", "bfae6b", "bf7f72"}, {"ferdinand", "bf964f", "bf4855"}, {"forbidden_arcana", "966de3", "216ebf"},
            {"gokuka", "ac4bbf", "228dbf"}, {"hakyoku", "df4a69", "ffd27a"}, {"hephaistos", "72ecf7", "ee8522"}, {"huang_linghua", "bfa04c", "bf1425"},
            {"innocence", "875bbf", "ecc356"}, {"kokuhaku", "3b59bf", "70c6de"}, {"kurma", "5bbf48", "bf834e"}, {"lucifara", "bf3369", "3a1030"},
            {"magna_mater", "6cbf87", "8bbf67"}, {"mary_sue", "bf954d", "bf1d38"}, {"mels", "5292bf", "c8f0ff"}, {"merlinus", "7534bf", "bfab55"},
            {"miyohime", "8b5bc5", "d3b252"}, {"nortia", "bfa153", "3c4dbf"}, {"nun", "c7b15b", "7a52bf"}, {"ouroboros", "bf9247", "6786bf"},
            {"relentless_research", "6bbfb2", "bf6b66"}, {"riha", "bf245f", "f1d373"}, {"savior", "bfab65", "324dbf"}, {"shinra", "bf517d", "ffd0e0"},
            {"sweet_pact", "bf9a60", "ff8faf"}, {"taika", "bf2d32", "c59f47"}, {"teia", "60e1eb", "ff8af0"}, {"tenki", "c29e3f", "6297c2"},
            {"valeria", "bf8e4b", "fff0c0"}, {"yggdrasil", "48bf51", "bf825d"}};
        for (String[] e : c) {
            COLOURS.put(e[0], new int[]{Integer.parseInt(e[1], 16), Integer.parseInt(e[2], 16)});
        }
    }

    private TechniqueEffects() {
    }

    /** The colour as a glowing dust: brightened toward white a little, so that magic reads as light. */
    private static DustParticleOptions dust(int rgb, float scale) {
        float r = ((rgb >> 16) & 255) / 255F, g = ((rgb >> 8) & 255) / 255F, b = (rgb & 255) / 255F;
        float m = Math.max(r, Math.max(g, b));
        float lift = m < 0.95F ? 0.95F / Math.max(0.05F, m) : 1F;
        r = Math.min(1, r * lift);
        g = Math.min(1, g * lift);
        b = Math.min(1, b * lift);
        return new DustParticleOptions(new Vector3f(r * 0.85F + 0.15F, g * 0.85F + 0.15F, b * 0.85F + 0.15F), scale);
    }

    @SubscribeEvent
    public static void tick(ClientTickEvent.Post e) {
        Minecraft mc = Minecraft.getInstance();
        ClientLevel level = mc.level;
        if (level == null || mc.isPaused()) {
            if (level == null) {
                TechniqueShow.ACTIVE.clear();
                TechniqueShow.REACT.clear();
                RELEASED.clear();
            }
            return;
        }
        long now = level.getGameTime();
        // a guard's moments are poses only (their sparks are the server's): forgotten once over
        TechniqueShow.REACT.values().removeIf(r -> now - r.start() > r.length() + 4 || now - r.start() < -40 || level.getEntity(r.entity()) == null);
        Iterator<TechniqueShow.Active> it = TechniqueShow.ACTIVE.values().iterator();
        while (it.hasNext()) {
            TechniqueShow.Active show = it.next();
            Entity b = level.getEntity(show.entity());
            long age = now - show.start();
            if (b == null || !b.isAlive() || age > show.length() + 4 || age < -40) {
                it.remove();
                RELEASED.remove(show.entity());
                continue;
            }
            int[] col = COLOURS.getOrDefault(show.character(), new int[]{0xb090ff, 0xffe0a0});
            Entity target = show.target() < 0 ? null : level.getEntity(show.target());
            try {
                if (age < show.windup()) {
                    windup(level, b, col, age, show);
                } else {
                    long since = age - show.windup();
                    Long done = RELEASED.get(show.entity());
                    if (done == null || done != show.start()) {
                        RELEASED.put(show.entity(), show.start());
                    }
                    release(level, b, target, col, (int) since, show.mechanic(), level.getRandom());
                }
            } catch (RuntimeException ex) {
                it.remove();
            }
        }
    }

    // ------------------------------------------------------------------------------------------------------ the windup

    private static void windup(ClientLevel level, Entity b, int[] col, long age, TechniqueShow.Active show) {
        double r = 0.8 + b.getBbWidth() * 0.9;
        double y = b.getY() + 0.05;
        float spin = age * 0.18F;
        float grow = Math.min(1F, (age + 1) / 6F);
        int n = 14;
        for (int i = 0; i < n; i++) {
            float a = spin + i * Mth.TWO_PI / n;
            level.addParticle(dust(col[0], 1.1F), b.getX() + Mth.cos(a) * r * grow, y, b.getZ() + Mth.sin(a) * r * grow, 0, 0, 0);
        }
        for (int i = 0; i < 8; i++) {
            float a = -spin * 1.6F + i * Mth.TWO_PI / 8;
            level.addParticle(dust(col[1], 0.9F), b.getX() + Mth.cos(a) * r * 0.55 * grow, y + 0.02, b.getZ() + Mth.sin(a) * r * 0.55 * grow, 0, 0, 0);
        }
        // the runes rising from the circle, and light gathering at the hands (the chest of a beast)
        if (age % 2 == 0) {
            float a = spin * 2.3F;
            level.addParticle(ParticleTypes.ENCHANT, b.getX() + Mth.cos(a) * r, y + 0.2, b.getZ() + Mth.sin(a) * r, 0, 0.6, 0);
            Vec3 hand = hand(b);
            for (int i = 0; i < 2; i++) {
                double ox = (level.getRandom().nextDouble() - 0.5) * 1.6, oy = (level.getRandom().nextDouble() - 0.5) * 1.2, oz = (level.getRandom().nextDouble() - 0.5) * 1.6;
                level.addParticle(ParticleTypes.END_ROD, hand.x + ox, hand.y + oy, hand.z + oz, -ox * 0.12, -oy * 0.12, -oz * 0.12);
            }
        }
    }

    private static Vec3 hand(Entity b) {
        Vec3 look = Vec3.directionFromRotation(0, b.getYRot());
        Vec3 side = new Vec3(-look.z, 0, look.x);
        return b.position().add(0, b.getBbHeight() * 0.62, 0).add(look.scale(b.getBbWidth() * 0.6 + 0.3)).add(side.scale(-b.getBbWidth() * 0.35));
    }

    private static Vec3 chest(Entity e) {
        return e.position().add(0, e.getBbHeight() * 0.6, 0);
    }

    // ------------------------------------------------------------------------------------------------------ the blow

    private static void release(ClientLevel level, Entity b, Entity target, int[] col, int since, String mechanic, RandomSource rnd) {
        if (mechanic.startsWith("MOVE_")) {
            // a big move draws its own sparks on the server; the blades' moves add their crescent, the blasts their
            // shockwave, the barrier its dome, in the character's colours
            String like = switch (mechanic) {
                case "MOVE_DASH_SLASH", "MOVE_COMBO_RUSH", "MOVE_SPIN_SLASH", "MOVE_BLADE_WAVE", "MOVE_REAP" -> "SLASH";
                case "MOVE_NOVA", "MOVE_LEAP_SLAM", "MOVE_GROUND_SPIKES", "MOVE_METEOR", "MOVE_UPPERCUT" -> "BURST";
                case "MOVE_BARRIER" -> "GUARD";
                default -> "";
            };
            if (!like.isEmpty()) {
                release(level, b, target, col, since, like, rnd);
            }
            return;
        }
        Vec3 c = chest(b);
        Vec3 look = Vec3.directionFromRotation(0, b.getYRot());
        Vec3 side = new Vec3(-look.z, 0, look.x);
        Vec3 aim = target != null ? chest(target) : c.add(look.scale(8));
        Vec3 at = target != null ? target.position() : b.position().add(look.scale(6));
        double w = b.getBbWidth();
        switch (mechanic) {
            case "SLASH", "COMBO" -> {
                if (since < 4 || ("COMBO".equals(mechanic) && since >= 8 && since < 12)) {
                    boolean back = since >= 8;
                    int k = since % 4;
                    for (int i = 0; i <= 10; i++) {
                        float a = (back ? 1 : -1) * (-1.2F + 2.4F * (i / 10F)) * Math.min(1, (k + 1) / 3F);
                        Vec3 p = c.add(look.scale((2.0 + w) * Mth.cos(a))).add(side.scale((2.0 + w) * Mth.sin(a))).add(0, -0.2 + i * 0.03, 0);
                        level.addParticle(dust(i % 3 == 0 ? col[1] : col[0], 1.6F), p.x, p.y, p.z, 0, 0, 0);
                    }
                    if (k == 0) {
                        Vec3 p = c.add(look.scale(1.8 + w));
                        level.addParticle(ParticleTypes.SWEEP_ATTACK, p.x, p.y, p.z, 0, 0, 0);
                    }
                }
            }
            case "ERASE" -> {
                if (since < 6) {
                    for (int i = 0; i < 24; i++) {
                        level.addParticle(dust(0xffffff, 1.4F), at.x, at.y + i * 0.25, at.z, 0, 0, 0);
                    }
                    for (int i = 0; i < 6; i++) {
                        level.addParticle(ParticleTypes.REVERSE_PORTAL, at.x, at.y + 1, at.z, (rnd.nextDouble() - 0.5) * 1.5, rnd.nextDouble(),
                            (rnd.nextDouble() - 0.5) * 1.5);
                    }
                    if (since == 0) {
                        for (int i = -6; i <= 6; i++) {
                            level.addParticle(dust(col[0], 1.2F), at.x + i * 0.25, at.y + 1.5 + i * 0.25, at.z, 0, 0, 0);
                            level.addParticle(dust(col[0], 1.2F), at.x + i * 0.25, at.y + 1.5 - i * 0.25, at.z, 0, 0, 0);
                        }
                    }
                }
            }
            case "REFLECT" -> {
                if (since < 8) {
                    Vec3 o = c.add(look.scale(1.2 + w * 0.5));
                    for (int s = 0; s < 6; s++) {
                        float a0 = s * Mth.TWO_PI / 6, a1 = (s + 1) * Mth.TWO_PI / 6;
                        for (int i = 0; i < 5; i++) {
                            float a = Mth.lerp(i / 5F, a0, a1);
                            double rr = 1.4 * (Mth.lerp(i / 5F, 1F, 1F));
                            Vec3 p = o.add(side.scale(Mth.cos(a) * rr)).add(0, Mth.sin(a) * rr, 0);
                            level.addParticle(dust(col[1], 1.0F), p.x, p.y, p.z, 0, 0, 0);
                        }
                        Vec3 v = o.add(side.scale(Mth.cos(a0) * 1.4)).add(0, Mth.sin(a0) * 1.4, 0);
                        level.addParticle(ParticleTypes.ELECTRIC_SPARK, v.x, v.y, v.z, 0, 0, 0);
                    }
                }
            }
            case "GROW" -> {
                if (since < 14) {
                    for (int arm = 0; arm < 3; arm++) {
                        float a = since * 0.45F + arm * Mth.TWO_PI / 3;
                        double rr = 0.6 + since * 0.12;
                        level.addParticle(dust(col[0], 1.2F), b.getX() + Mth.cos(a) * rr, b.getY() + since * 0.18, b.getZ() + Mth.sin(a) * rr, 0, 0, 0);
                        level.addParticle(ParticleTypes.HAPPY_VILLAGER, b.getX() + Mth.cos(a) * rr, b.getY() + since * 0.18, b.getZ() + Mth.sin(a) * rr, 0, 0, 0);
                    }
                    if (since % 3 == 0) {
                        level.addParticle(ParticleTypes.CHERRY_LEAVES, b.getX() + (rnd.nextDouble() - 0.5) * 3, b.getY() + 2.5, b.getZ() + (rnd.nextDouble() - 0.5) * 3, 0, 0, 0);
                    }
                }
            }
            case "REWIND" -> {
                if (since < 14) {
                    Vec3 o = c.add(look.scale(0.6)).add(0, 0.5, 0);
                    for (int i = 0; i < 12; i++) {
                        float a = i * Mth.TWO_PI / 12;
                        Vec3 p = o.add(side.scale(Mth.cos(a) * 1.7)).add(0, Mth.sin(a) * 1.7, 0);
                        level.addParticle(dust(col[0], i % 3 == 0 ? 1.6F : 0.9F), p.x, p.y, p.z, 0, 0, 0);
                    }
                    for (float hand : new float[]{-since * 0.6F, -since * 0.05F}) {
                        double len = hand == -since * 0.6F ? 1.4 : 0.9;
                        for (int i = 1; i <= 6; i++) {
                            Vec3 p = o.add(side.scale(Mth.sin(hand) * len * i / 6)).add(0, Mth.cos(hand) * len * i / 6, 0);
                            level.addParticle(dust(col[1], 1.0F), p.x, p.y, p.z, 0, 0, 0);
                        }
                    }
                    level.addParticle(ParticleTypes.REVERSE_PORTAL, o.x, o.y, o.z, (rnd.nextDouble() - 0.5) * 0.4, (rnd.nextDouble() - 0.5) * 0.4, (rnd.nextDouble() - 0.5) * 0.4);
                }
            }
            case "WEATHER" -> {
                if (since < 16) {
                    for (int i = 0; i < 4; i++) {
                        double x = b.getX() + (rnd.nextDouble() - 0.5) * 10, z = b.getZ() + (rnd.nextDouble() - 0.5) * 10;
                        level.addParticle(ParticleTypes.END_ROD, x, b.getY() + 7, z, 0, -0.6, 0);
                    }
                    level.addParticle(ParticleTypes.CLOUD, b.getX() + (rnd.nextDouble() - 0.5) * 6, b.getY() + 7, b.getZ() + (rnd.nextDouble() - 0.5) * 6, 0, 0, 0);
                }
            }
            case "SEAL" -> {
                if (since < 12) {
                    double s = 1.6;
                    for (int i = 0; i <= 8; i++) {
                        double u = -s + 2 * s * i / 8;
                        for (double[] p : new double[][]{{u, -s}, {u, s}, {-s, u}, {s, u}, {u, u}, {u, -u}}) {
                            level.addParticle(dust(col[0], 1.0F), at.x + p[0], at.y + 0.05, at.z + p[1], 0, 0, 0);
                        }
                    }
                    if (since % 2 == 0) {
                        level.addParticle(ParticleTypes.ENCHANT, at.x, at.y + 2.2, at.z, 0, -1.2, 0);
                    }
                }
            }
            case "GUARD" -> {
                if (since < 10) {
                    double rr = 1.4 + w;
                    for (int i = 0; i < 26; i++) {
                        double th = rnd.nextDouble() * Mth.TWO_PI, ph = rnd.nextDouble() * Math.PI / 2;
                        level.addParticle(dust(col[1], 0.9F), b.getX() + Math.cos(th) * Math.cos(ph) * rr, b.getY() + Math.sin(ph) * rr,
                            b.getZ() + Math.sin(th) * Math.cos(ph) * rr, 0, 0, 0);
                    }
                }
            }
            case "SHIFT" -> {
                if (since < 6) {
                    for (Vec3 p : new Vec3[]{c, aim}) {
                        for (int i = 0; i < 8; i++) {
                            level.addParticle(ParticleTypes.PORTAL, p.x, p.y, p.z, (rnd.nextDouble() - 0.5) * 2, (rnd.nextDouble() - 0.5) * 2, (rnd.nextDouble() - 0.5) * 2);
                        }
                    }
                    line(level, c, aim, dust(col[0], 0.8F), 0.6);
                }
            }
            case "LAW" -> {
                if (since < 10) {
                    for (int i = 0; i < 10; i++) {
                        level.addParticle(ParticleTypes.END_ROD, at.x, at.y + 6 - i * 0.6, at.z, 0, -0.2, 0);
                    }
                    for (int i = 0; i < 16; i++) {
                        float a = i * Mth.TWO_PI / 16 + since * 0.1F;
                        level.addParticle(dust(col[0], 1.2F), at.x + Mth.cos(a) * 1.1, at.y + 3.5, at.z + Mth.sin(a) * 1.1, 0, 0, 0);
                    }
                }
            }
            case "ADAPT" -> {
                if (since < 12) {
                    double rr = 1.2 + w * 0.6 + since * 0.05;
                    for (int i = 0; i < 18; i++) {
                        double th = rnd.nextDouble() * Mth.TWO_PI, ph = (rnd.nextDouble() - 0.5) * Math.PI;
                        int rgb = Mth.hsvToRgb((float) ((th / Mth.TWO_PI + since * 0.05) % 1.0), 0.8F, 1.0F);
                        level.addParticle(dust(rgb, 1.0F), c.x + Math.cos(th) * Math.cos(ph) * rr, c.y + Math.sin(ph) * rr, c.z + Math.sin(th) * Math.cos(ph) * rr, 0, 0, 0);
                    }
                }
            }
            case "TRANSMUTE" -> {
                if (since < 12) {
                    Vec3 h = hand(b);
                    double rr = 2.0 * (1 - since / 12.0) + 0.2;
                    for (int i = 0; i < 8; i++) {
                        float a = since * 0.5F + i * Mth.TWO_PI / 8;
                        level.addParticle(dust(0xffd75a, 1.1F), h.x + Mth.cos(a) * rr, h.y + Mth.sin(a * 0.5F) * 0.3, h.z + Mth.sin(a) * rr, 0, 0, 0);
                    }
                    level.addParticle(ParticleTypes.WAX_ON, h.x, h.y, h.z, (rnd.nextDouble() - 0.5), (rnd.nextDouble() - 0.5), (rnd.nextDouble() - 0.5));
                }
            }
            case "SUMMON" -> {
                if (since < 16) {
                    double rr = 3.0;
                    for (int i = 0; i < 24; i++) {
                        float a = i * Mth.TWO_PI / 24 + since * 0.04F;
                        level.addParticle(dust(col[0], 1.2F), b.getX() + Mth.cos(a) * rr, b.getY() + 0.05, b.getZ() + Mth.sin(a) * rr, 0, 0, 0);
                    }
                    for (int s = 0; s < 5; s++) {
                        float a0 = s * Mth.TWO_PI / 5 * 2 + since * 0.04F, a1 = (s + 1) * Mth.TWO_PI / 5 * 2 + since * 0.04F;
                        Vec3 p0 = new Vec3(b.getX() + Mth.cos(a0) * rr, b.getY() + 0.05, b.getZ() + Mth.sin(a0) * rr);
                        Vec3 p1 = new Vec3(b.getX() + Mth.cos(a1) * rr, b.getY() + 0.05, b.getZ() + Mth.sin(a1) * rr);
                        line(level, p0, p1, dust(col[1], 1.0F), 0.45);
                        if (since % 3 == 0) {
                            level.addParticle(ParticleTypes.SOUL_FIRE_FLAME, p0.x, p0.y + 0.1, p0.z, 0, 0.12, 0);
                        }
                    }
                }
            }
            case "MANA" -> {
                if (since < 16) {
                    for (int i = 0; i < 2; i++) {
                        float a = since * 0.6F + i * Mth.PI;
                        level.addParticle(dust(col[0], 1.1F), b.getX() + Mth.cos(a) * (0.8 + w), b.getY() + (since % 16) * 0.2, b.getZ() + Mth.sin(a) * (0.8 + w), 0, 0, 0);
                    }
                    level.addParticle(ParticleTypes.ENCHANT, c.x, c.y + 1, c.z, (rnd.nextDouble() - 0.5) * 2, -0.5, (rnd.nextDouble() - 0.5) * 2);
                }
            }
            case "BARRAGE" -> {
                if (since < 14 && since % 2 == 0) {
                    Vec3 from = hand(b).add(side.scale(since % 4 == 0 ? 0.4 : -0.4));
                    Vec3 jitter = new Vec3((rnd.nextDouble() - 0.5) * 1.2, (rnd.nextDouble() - 0.5) * 1.2, (rnd.nextDouble() - 0.5) * 1.2);
                    line(level, from, aim.add(jitter), dust(since % 4 == 0 ? col[0] : col[1], 1.0F), 0.5);
                }
            }
            case "BURST" -> {
                if (since < 8) {
                    double rr = 0.6 + since * 0.6;
                    for (int i = 0; i < 28; i++) {
                        float a = i * Mth.TWO_PI / 28;
                        level.addParticle(dust(col[0], 1.4F), b.getX() + Mth.cos(a) * rr, b.getY() + 0.2, b.getZ() + Mth.sin(a) * rr, 0, 0, 0);
                    }
                    if (since % 2 == 0) {
                        level.addParticle(ParticleTypes.ELECTRIC_SPARK, b.getX() + (rnd.nextDouble() - 0.5) * rr * 2, b.getY() + 0.3, b.getZ() + (rnd.nextDouble() - 0.5) * rr * 2, 0, 0.2, 0);
                    }
                    if (since == 0) {
                        level.addParticle(ParticleTypes.EXPLOSION, c.x, c.y, c.z, 0, 0, 0);
                    }
                }
            }
            case "REPAIR" -> {
                if (since < 14) {
                    Vec3 h = hand(b).add(0, -0.4, 0);
                    if (since % 3 == 0) {
                        for (int i = 0; i < 6; i++) {
                            level.addParticle(ParticleTypes.WAX_OFF, h.x, h.y, h.z, (rnd.nextDouble() - 0.5) * 2, rnd.nextDouble(), (rnd.nextDouble() - 0.5) * 2);
                        }
                    }
                    for (int i = 0; i < 16; i++) {
                        float a = i * Mth.TWO_PI / 16 + since * 0.15F;
                        double rr = i % 2 == 0 ? 1.0 : 0.8;
                        level.addParticle(dust(0xb8b8c8, 0.8F), b.getX() + Mth.cos(a) * rr * (1 + w), b.getY() + 0.1, b.getZ() + Mth.sin(a) * rr * (1 + w), 0, 0, 0);
                    }
                }
            }
            case "HEAL" -> {
                if (since < 16) {
                    for (int i = 0; i < 5; i++) {
                        double x = b.getX() + (rnd.nextDouble() - 0.5) * (2 + w), z = b.getZ() + (rnd.nextDouble() - 0.5) * (2 + w);
                        level.addParticle(dust(col[0], 1.0F), x, b.getY() + rnd.nextDouble() * 2.5, z, 0, 0, 0);
                    }
                    if (since % 4 == 0) {
                        level.addParticle(ParticleTypes.HEART, c.x, c.y + 1.2, c.z, 0, 0, 0);
                    }
                }
            }
            case "DRAIN" -> {
                if (since < 14) {
                    for (int i = 0; i < 4; i++) {
                        double u = ((since * 4 + i) % 16) / 16.0;
                        Vec3 p = aim.lerp(c, u).add(0, Math.sin(u * Math.PI) * 0.8, 0);
                        level.addParticle(dust(col[1] == col[0] ? 0xd02030 : col[1], 1.3F), p.x, p.y, p.z, 0, 0, 0);
                    }
                    if (since % 3 == 0) {
                        level.addParticle(ParticleTypes.DAMAGE_INDICATOR, aim.x, aim.y, aim.z, 0, 0.2, 0);
                    }
                }
            }
            case "CURSE" -> {
                if (since < 16) {
                    for (int i = 0; i < 3; i++) {
                        float a = since * 0.7F + i * Mth.TWO_PI / 3;
                        level.addParticle(dust(0x40104a, 1.4F), at.x + Mth.cos(a) * 1.2, at.y + since * 0.12, at.z + Mth.sin(a) * 1.2, 0, 0, 0);
                    }
                    level.addParticle(ParticleTypes.WITCH, at.x, at.y + 1, at.z, 0, 0, 0);
                    if (since % 4 == 0) {
                        level.addParticle(ParticleTypes.SQUID_INK, at.x, at.y + 1.5, at.z, 0, 0.05, 0);
                    }
                }
            }
            case "PULL" -> {
                if (since < 10) {
                    double u = 1 - since / 10.0;
                    line(level, c, aim, dust(col[0], 0.9F), 0.4);
                    Vec3 head = c.lerp(aim, u);
                    level.addParticle(ParticleTypes.ELECTRIC_SPARK, head.x, head.y, head.z, 0, 0, 0);
                }
            }
            case "FATE" -> {
                if (since < 16) {
                    for (int k = 0; k < 5; k++) {
                        float a = since * 0.2F + k * Mth.TWO_PI / 5;
                        Vec3 o = c.add(Mth.cos(a) * (1.4 + w), 0.6 + Mth.sin(since * 0.3F + k) * 0.3, Mth.sin(a) * (1.4 + w));
                        for (int i = 0; i < 4; i++) {
                            level.addParticle(dust(k % 2 == 0 ? col[0] : col[1], 0.7F), o.x + Mth.cos(a + Mth.HALF_PI) * (i % 2) * 0.25, o.y + (i / 2) * 0.35,
                                o.z + Mth.sin(a + Mth.HALF_PI) * (i % 2) * 0.25, 0, 0, 0);
                        }
                    }
                    if (since == 6) {
                        line(level, c, aim, ParticleTypes.END_ROD, 0.7);
                    }
                }
            }
            case "COPY" -> {
                if (since < 8) {
                    if (since == 0) {
                        level.addParticle(ParticleTypes.FLASH, c.x, c.y, c.z, 0, 0, 0);
                    }
                    double rr = (target != null ? target.getBbWidth() : 1) + 0.5;
                    for (int i = 0; i < 20; i++) {
                        float a = i * Mth.TWO_PI / 20;
                        level.addParticle(dust(col[1], 1.0F), at.x + Mth.cos(a) * rr, at.y + 0.1 + since * 0.25, at.z + Mth.sin(a) * rr, 0, 0, 0);
                    }
                }
            }
            case "TOY" -> {
                if (since < 12) {
                    for (int i = 0; i < 6; i++) {
                        int rgb = Mth.hsvToRgb(rnd.nextFloat(), 0.8F, 1.0F);
                        level.addParticle(dust(rgb, 1.0F), c.x + (rnd.nextDouble() - 0.5) * 3, c.y + rnd.nextDouble() * 2, c.z + (rnd.nextDouble() - 0.5) * 3, 0, 0, 0);
                    }
                    if (since % 3 == 0) {
                        level.addParticle(ParticleTypes.NOTE, c.x, c.y + 1.4, c.z, rnd.nextDouble(), 0, 0);
                    }
                }
            }
            case "SWOOP" -> {
                if (since < 10) {
                    double rr = 1.0 + w + since * 0.3;
                    for (int i = 0; i < 16; i++) {
                        float a = i * Mth.TWO_PI / 16;
                        level.addParticle(ParticleTypes.CLOUD, c.x + Mth.cos(a) * rr, c.y - 0.5, c.z + Mth.sin(a) * rr, 0, 0, 0);
                    }
                }
            }
            default -> {
                // BOLT and any other: a beam from the hand to the enemy, a flash where it lands
                if (since < 4) {
                    line(level, hand(b), aim, dust(col[0], 1.2F), 0.35);
                    if (since == 0) {
                        for (int i = 0; i < 10; i++) {
                            level.addParticle(dust(col[1], 1.5F), aim.x + (rnd.nextDouble() - 0.5), aim.y + (rnd.nextDouble() - 0.5), aim.z + (rnd.nextDouble() - 0.5), 0, 0, 0);
                        }
                        level.addParticle(ParticleTypes.FLASH, aim.x, aim.y, aim.z, 0, 0, 0);
                    }
                }
            }
        }
    }

    private static void line(ClientLevel level, Vec3 a, Vec3 b, ParticleOptions p, double step) {
        double d = a.distanceTo(b);
        int n = Math.min(80, Math.max(2, (int) (d / step)));
        for (int i = 0; i <= n; i++) {
            Vec3 q = a.lerp(b, i / (double) n);
            level.addParticle(p, q.x, q.y, q.z, 0, 0, 0);
        }
    }
}
