package jp.oror.reborn.relic.client;

import com.google.gson.JsonObject;
import com.mojang.blaze3d.vertex.VertexConsumer;
import jp.oror.reborn.relic.RelicV9;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;
import org.joml.Matrix4f;

/**
 * (058) How each of the relic techniques' 3D shapes is drawn (additive light, both faces, relative to the camera):
 * the blade's crescent sweeping its arc, the travelling wave, the beam with its white core, the ring spreading on the
 * ground, the magic circle turning (flat, or upright before the bearer), the pillar of light, the spikes rising along a
 * line, the rain of streaks, the jagged chain, the dome of bands, the orb gathering, the star of a flash, the wings,
 * the branching tree, the clock with its hands, the fist, the volley of arrows; and the warnings while a technique is
 * readied, and the units and fields set down.
 */
final class RelicShapes {
    private RelicShapes() {
    }

    // ------------------------------------------------------------------------------------------------------ helpers

    static void quad(VertexConsumer vc, Matrix4f m, Vec3 a, Vec3 b, Vec3 c, Vec3 d, int argb) {
        int A = argb >>> 24, R = (argb >> 16) & 0xFF, G = (argb >> 8) & 0xFF, B = argb & 0xFF;
        if (A <= 2) {
            return;
        }
        vc.addVertex(m, (float) a.x, (float) a.y, (float) a.z).setColor(R, G, B, A);
        vc.addVertex(m, (float) b.x, (float) b.y, (float) b.z).setColor(R, G, B, A);
        vc.addVertex(m, (float) c.x, (float) c.y, (float) c.z).setColor(R, G, B, A);
        vc.addVertex(m, (float) d.x, (float) d.y, (float) d.z).setColor(R, G, B, A);
        vc.addVertex(m, (float) d.x, (float) d.y, (float) d.z).setColor(R, G, B, A);
        vc.addVertex(m, (float) c.x, (float) c.y, (float) c.z).setColor(R, G, B, A);
        vc.addVertex(m, (float) b.x, (float) b.y, (float) b.z).setColor(R, G, B, A);
        vc.addVertex(m, (float) a.x, (float) a.y, (float) a.z).setColor(R, G, B, A);
    }

    static int argb(int rgb, float alpha) {
        return ((int) (Mth.clamp(alpha, 0, 1) * 170) << 24) | (rgb & 0xFFFFFF);
    }

    static int lighter(int rgb, float f) {
        int r = (rgb >> 16) & 255, g = (rgb >> 8) & 255, b = rgb & 255;
        r = (int) (r + (255 - r) * f);
        g = (int) (g + (255 - g) * f);
        b = (int) (b + (255 - b) * f);
        return (r << 16) | (g << 8) | b;
    }

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

    /** A bar from a to b turned to face the camera (at the origin), w wide. */
    static void beam(VertexConsumer vc, Matrix4f m, Vec3 a, Vec3 b, double w, int argb) {
        Vec3 d = b.subtract(a);
        Vec3 side = d.cross(a.add(b).scale(0.5));
        if (side.lengthSqr() < 1.0E-8) {
            side = d.cross(new Vec3(0, 1, 0));
        }
        if (side.lengthSqr() < 1.0E-8) {
            side = new Vec3(1, 0, 0);
        }
        side = side.normalize().scale(w * 0.5);
        quad(vc, m, a.add(side), b.add(side), b.subtract(side), a.subtract(side), argb);
    }

    static Vec3 flat(Vec3 d) {
        Vec3 f = new Vec3(d.x, 0, d.z);
        return f.lengthSqr() < 1.0E-6 ? new Vec3(0, 0, 1) : f.normalize();
    }

    static Vec3 side(Vec3 d) {
        Vec3 f = flat(d);
        return new Vec3(-f.z, 0, f.x);
    }

    private static double hash(long seed, int i) {
        long x = seed * 6364136223846793005L + i * 1442695040888963407L;
        x ^= x >>> 33;
        return ((x & 0xFFFFFF) / (double) 0xFFFFFF);
    }

    // -------------------------------------------------------------------------------------------------- the shapes

    static void draw(ClientLevel l, VertexConsumer vc, Matrix4f m, Vec3 cp, RelicClient.Shape s, float age, float partial) {
        float t = age / s.life;
        float fade = Math.min(1F, Math.min(age / 3F, (s.life - age) / Math.max(3F, s.life * 0.35F)));
        if (fade <= 0) {
            return;
        }
        Vec3 c = s.at.subtract(cp);
        // what is drawn at the camera (the caster's own wings and flashes, in first person) dims, or it would fill the screen
        fade *= (float) Mth.clamp(c.length() / 5.0, 0.2, 1.0);
        Vec3 d = s.dir.lengthSqr() < 1.0E-6 ? new Vec3(0, 0, 1) : s.dir.normalize();
        Vec3 up = new Vec3(0, 1, 0);
        int col = s.colour, hi = lighter(s.colour, 0.6F);
        switch (s.kind) {
            case 0 -> { // slash: a crescent of light sweeping its arc, tilted by a
                double tilt = Math.toRadians(s.a);
                Vec3 f = flat(d), sd = side(d);
                Vec3 u = f, v = sd.scale(Math.cos(tilt)).add(up.scale(Math.sin(tilt)));
                double sweep = Math.PI * 1.1, head = -sweep / 2 + sweep * Math.min(1, t * 2.2);
                int n = 18;
                for (int k = 0; k < n; k++) {
                    double a0 = head - sweep * 0.8 * k / n, a1 = head - sweep * 0.8 * (k + 1) / n;
                    float w = 0.55F * s.size * 0.18F * (1 - k / (float) n);
                    float al = fade * (1 - k / (float) n);
                    Vec3 o0 = c.add(u.scale(Math.cos(a0) * s.size)).add(v.scale(Math.sin(a0) * s.size));
                    Vec3 o1 = c.add(u.scale(Math.cos(a1) * s.size)).add(v.scale(Math.sin(a1) * s.size));
                    Vec3 i0 = c.add(u.scale(Math.cos(a0) * (s.size - w))).add(v.scale(Math.sin(a0) * (s.size - w)));
                    Vec3 i1 = c.add(u.scale(Math.cos(a1) * (s.size - w))).add(v.scale(Math.sin(a1) * (s.size - w)));
                    quad(vc, m, o0, o1, i1, i0, argb(k < 3 ? 0xFFFFFF : col, al));
                }
            }
            case 1 -> { // wave: a crescent travelling along the line
                Vec3 f = flat(d), sd = side(d);
                Vec3 at = c.add(d.scale(s.size * Math.min(1, t * 1.3)));
                double w = 1.4 + s.size * 0.06;
                for (int k = -6; k < 6; k++) {
                    double a0 = k / 6.0 * 1.2, a1 = (k + 1) / 6.0 * 1.2;
                    Vec3 p0 = at.add(sd.scale(Math.sin(a0) * w)).subtract(f.scale((1 - Math.cos(a0)) * w));
                    Vec3 p1 = at.add(sd.scale(Math.sin(a1) * w)).subtract(f.scale((1 - Math.cos(a1)) * w));
                    quad(vc, m, p0.add(0, 0.5, 0), p1.add(0, 0.5, 0), p1.add(0, -0.3, 0), p0.add(0, -0.3, 0), argb(col, fade * 0.8F));
                    quad(vc, m, p0.add(0, 0.2, 0), p1.add(0, 0.2, 0), p1, p0, argb(0xFFFFFF, fade * 0.5F));
                }
            }
            case 2 -> { // beam: from the point along its way, a white core in its colour
                double w = Math.max(0.12, s.a > 0 ? s.a : 0.4) * (0.7 + 0.3 * Math.sin(age * 1.7));
                Vec3 b = c.add(d.scale(s.size));
                beam(vc, m, c, b, w * 2.2, argb(col, fade * 0.55F));
                beam(vc, m, c, b, w * 0.7, argb(0xFFFFFF, fade * 0.9F));
            }
            case 3 -> { // ring: spreading on the ground
                double r = 0.3 + (s.size - 0.3) * Math.min(1, t * 1.2);
                ring(vc, m, c.add(0, 0.06, 0), new Vec3(1, 0, 0), new Vec3(0, 0, 1), r, Math.max(0.2, s.size * 0.05), 48, argb(col, fade * 0.8F), 0, Math.PI * 2);
                ring(vc, m, c.add(0, 0.08, 0), new Vec3(1, 0, 0), new Vec3(0, 0, 1), r * 0.92, 0.08, 48, argb(hi, fade), 0, Math.PI * 2);
            }
            case 4 -> { // circle: a magic circle turning; upright before its bearer when a is 1
                Vec3 u, v;
                if (s.a >= 1) {
                    u = side(d);
                    v = up;
                    c = c.add(flat(d).scale(1.2));
                } else {
                    u = new Vec3(1, 0, 0);
                    v = new Vec3(0, 0, 1);
                    c = c.add(0, 0.07, 0);
                }
                double spin = age * 0.06, r = s.size * Math.min(1, age / 6F);
                ring(vc, m, c, u, v, r, Math.max(0.08, r * 0.05), 64, argb(col, fade * 0.85F), spin, Math.PI * 2);
                ring(vc, m, c, u, v, r * 0.78, Math.max(0.05, r * 0.025), 48, argb(hi, fade * 0.8F), -spin, Math.PI * 2);
                ring(vc, m, c, u, v, r * 0.4, Math.max(0.05, r * 0.03), 32, argb(col, fade * 0.7F), spin * 2, Math.PI * 2);
                for (int k = 0; k < 6; k++) {
                    double a0 = spin + k * Math.PI / 3, a1 = a0 + Math.PI * 2 / 3;
                    Vec3 p0 = c.add(u.scale(Math.cos(a0) * r * 0.78)).add(v.scale(Math.sin(a0) * r * 0.78));
                    Vec3 p1 = c.add(u.scale(Math.cos(a1) * r * 0.78)).add(v.scale(Math.sin(a1) * r * 0.78));
                    Vec3 n = u.cross(v);
                    Vec3 w = p1.subtract(p0).cross(n).normalize().scale(Math.max(0.03, r * 0.012));
                    quad(vc, m, p0.add(w), p1.add(w), p1.subtract(w), p0.subtract(w), argb(hi, fade * 0.6F));
                }
            }
            case 5 -> { // pillar of light
                double h = s.h > 0 ? s.h : 12, r = s.size * (0.6 + 0.4 * Math.min(1, age / 4F));
                Vec3 top = c.add(0, h, 0);
                beam(vc, m, c, top, r * 2.0, argb(col, fade * 0.5F));
                beam(vc, m, c, top, r * 0.7, argb(0xFFFFFF, fade * 0.85F));
                ring(vc, m, c.add(0, 0.06, 0), new Vec3(1, 0, 0), new Vec3(0, 0, 1), r * 1.6, 0.15, 32, argb(col, fade), age * 0.1, Math.PI * 2);
            }
            case 6 -> { // spikes: rising along the line (or round the point)
                int n = (int) Math.min(24, 4 + s.size * 1.2);
                boolean radial = Math.abs(d.y) > 0.9 || s.size < 2.5;
                Vec3 f = flat(d), sd = side(d);
                for (int k = 0; k < n; k++) {
                    double rise = Mth.clamp(age * 1.4 - k * 0.6, 0, 1);
                    if (rise <= 0) {
                        continue;
                    }
                    Vec3 base;
                    if (radial) {
                        double ang = k * 2.39996, rr = s.size * Math.sqrt((k + 0.5) / n);
                        base = c.add(Math.cos(ang) * rr, 0, Math.sin(ang) * rr);
                    } else {
                        base = c.add(f.scale(s.size * (k + 0.5) / n)).add(sd.scale((hash(s.seed, k) - 0.5) * 2.2)).add(0, -1.2, 0);
                    }
                    double h = (0.8 + hash(s.seed, k + 99) * 1.4) * rise;
                    Vec3 tip = base.add((hash(s.seed, k + 7) - 0.5) * 0.4, h, (hash(s.seed, k + 11) - 0.5) * 0.4);
                    double w = 0.25;
                    quad(vc, m, base.add(-w, 0, 0), base.add(w, 0, 0), tip, tip, argb(col, fade * 0.85F));
                    quad(vc, m, base.add(0, 0, -w), base.add(0, 0, w), tip, tip, argb(hi, fade * 0.7F));
                }
            }
            case 7 -> { // rain of streaks
                int n = (int) Math.min(30, 6 + s.size * 3);
                for (int k = 0; k < n; k++) {
                    double ph = (age * 0.09 + hash(s.seed, k)) % 1.0;
                    double ang = hash(s.seed, k + 3) * Math.PI * 2, rr = s.size * Math.sqrt(hash(s.seed, k + 5));
                    Vec3 g = c.add(Math.cos(ang) * rr, 0, Math.sin(ang) * rr);
                    Vec3 top = g.add(0, 14 * (1 - ph) + 2, 0), bot = g.add(0, 14 * (1 - ph), 0);
                    beam(vc, m, bot, top, 0.18, argb(col, fade * 0.8F));
                }
            }
            case 8 -> { // chain: a jagged thread from the point along its way
                Vec3 b = c.add(s.dir);
                int n = 10;
                Vec3 prev = c;
                for (int k = 1; k <= n; k++) {
                    Vec3 q = c.add(b.subtract(c).scale(k / (double) n));
                    if (k < n) {
                        double j = 0.35 * Math.sin(age * 2.3 + k * 1.7 + s.seed);
                        q = q.add(j, Math.cos(age * 1.9 + k) * 0.25, -j);
                    }
                    beam(vc, m, prev, q, 0.16, argb(col, fade));
                    beam(vc, m, prev, q, 0.05, argb(0xFFFFFF, fade));
                    prev = q;
                }
            }
            case 9 -> { // dome of bands
                double r = s.size * Math.min(1, age / 5F);
                for (int k = 1; k < 6; k++) {
                    double lat = k / 6.0 * Math.PI / 2;
                    ring(vc, m, c.add(0, Math.sin(lat) * r, 0), new Vec3(1, 0, 0), new Vec3(0, 0, 1), Math.cos(lat) * r, 0.06 + r * 0.015, 40,
                        argb(k % 2 == 0 ? hi : col, fade * 0.45F), age * 0.03 * (k % 2 == 0 ? 1 : -1), Math.PI * 2);
                }
                for (int k = 0; k < 8; k++) {
                    double lon = k * Math.PI / 4 + age * 0.02;
                    ring(vc, m, c, new Vec3(Math.cos(lon), 0, Math.sin(lon)), up, r, 0.05 + r * 0.01, 16, argb(col, fade * 0.35F), 0, Math.PI / 2);
                }
            }
            case 11 -> { // orb gathering
                double r = s.size * (1.2 - 0.6 * t) * (0.9 + 0.1 * Math.sin(age));
                for (int k = 0; k < 5; k++) {
                    double lon = k * Math.PI / 5 + age * 0.08;
                    ring(vc, m, c, new Vec3(Math.cos(lon), 0, Math.sin(lon)), up, r, Math.min(0.2, r * 0.06), 24, argb(k == 0 ? 0xFFFFFF : col, fade * 0.5F), 0, Math.PI * 2);
                }
            }
            case 12 -> { // flash: a star of rays
                double r = s.size * (0.4 + 1.2 * t);
                for (int k = 0; k < 8; k++) {
                    double ang = k * Math.PI / 4 + hash(s.seed, 1);
                    Vec3 dir = new Vec3(Math.cos(ang), Math.sin(ang * 1.3) * 0.6, Math.sin(ang)).normalize();
                    beam(vc, m, c, c.add(dir.scale(r * (k % 2 == 0 ? 1 : 0.6))), Math.min(0.22, 0.05 + s.size * 0.015), argb(k % 2 == 0 ? 0xFFFFFF : col, fade * 0.7F));
                }
            }
            case 13 -> { // wings: two fans of feathers behind
                Vec3 f = flat(d), sd = side(d);
                Vec3 back = c.subtract(f.scale(0.4)).add(0, 0.3, 0);
                double open = Math.min(1, age / 8F) * (0.85 + 0.15 * Math.sin(age * 0.3));
                for (int sgn = -1; sgn <= 1; sgn += 2) {
                    for (int k = 0; k < 7; k++) {
                        double ang = (0.15 + 0.14 * k) * Math.PI * open;
                        Vec3 dir = sd.scale(sgn * Math.cos(ang)).add(up.scale(Math.sin(ang) * 0.9)).subtract(f.scale(0.25));
                        double len = s.size * (1.4 - k * 0.09);
                        Vec3 tip = back.add(dir.scale(len));
                        beam(vc, m, back, tip, 0.07 + 0.015 * (7 - k), argb(k % 3 == 0 ? hi : col, fade * 0.4F));
                    }
                }
            }
            case 14 -> { // tree: a trunk and branching limbs
                branch(vc, m, c, up, s.size * 1.6 * Math.min(1, age / 10F), 0, s.seed, col, hi, fade);
            }
            case 15 -> { // clock: a face and its hands
                Vec3 at = c.add(0, 1.6, 0);
                Vec3 u = side(d), v = up;
                double r = s.size;
                ring(vc, m, at, u, v, r, 0.1, 48, argb(col, fade), 0, Math.PI * 2);
                for (int k = 0; k < 12; k++) {
                    double a = k * Math.PI / 6;
                    Vec3 o = at.add(u.scale(Math.cos(a) * r)).add(v.scale(Math.sin(a) * r));
                    Vec3 i = at.add(u.scale(Math.cos(a) * r * 0.85)).add(v.scale(Math.sin(a) * r * 0.85));
                    beam(vc, m, i, o, 0.08, argb(hi, fade));
                }
                double hand = -age * 0.35, hand2 = -age * 0.03;
                beam(vc, m, at, at.add(u.scale(Math.cos(hand) * r * 0.8)).add(v.scale(Math.sin(hand) * r * 0.8)), 0.1, argb(0xFFFFFF, fade));
                beam(vc, m, at, at.add(u.scale(Math.cos(hand2) * r * 0.55)).add(v.scale(Math.sin(hand2) * r * 0.55)), 0.14, argb(col, fade));
            }
            case 16 -> { // fist: a block of force driven along the way
                Vec3 at = c.add(d.scale(s.size * Math.min(1, t * 1.5)));
                double h = 0.5 + s.size * 0.05;
                Vec3 f = d, sd = side(d), uu = sd.cross(f).normalize();
                Vec3[] cs = new Vec3[8];
                for (int k = 0; k < 8; k++) {
                    cs[k] = at.add(f.scale((k & 1) == 0 ? -h : h)).add(sd.scale((k & 2) == 0 ? -h : h)).add(uu.scale((k & 4) == 0 ? -h : h));
                }
                int[][] faces = {{0, 1, 3, 2}, {4, 5, 7, 6}, {0, 1, 5, 4}, {2, 3, 7, 6}, {0, 2, 6, 4}, {1, 3, 7, 5}};
                for (int[] fc : faces) {
                    quad(vc, m, cs[fc[0]], cs[fc[1]], cs[fc[2]], cs[fc[3]], argb(col, fade * 0.45F));
                }
                ring(vc, m, at, sd, uu, h * 2.2, 0.12, 24, argb(hi, fade), 0, Math.PI * 2);
            }
            case 17 -> { // arrows: three tracers
                Vec3 sd = side(d);
                for (int k = -1; k <= 1; k++) {
                    Vec3 a = c.add(sd.scale(k * 0.8));
                    double head = s.size * Math.min(1, t * 2.0);
                    beam(vc, m, a.add(d.scale(Math.max(0, head - 6))), a.add(d.scale(head)), 0.2, argb(col, fade));
                    beam(vc, m, a.add(d.scale(Math.max(0, head - 2))), a.add(d.scale(head)), 0.08, argb(0xFFFFFF, fade));
                }
            }
            default -> {
            }
        }
    }

    private static void branch(VertexConsumer vc, Matrix4f m, Vec3 from, Vec3 dir, double len, int depth, long seed, int col, int hi, float fade) {
        if (len < 0.3 || depth > 4) {
            return;
        }
        Vec3 to = from.add(dir.scale(len));
        beam(vc, m, from, to, Math.max(0.06, 0.35 - depth * 0.07), argb(depth < 2 ? col : hi, fade * 0.7F));
        for (int k = 0; k < 3; k++) {
            double ang = hash(seed, depth * 7 + k) * Math.PI * 2;
            Vec3 nd = dir.add(Math.cos(ang) * 0.7, 0.15, Math.sin(ang) * 0.7).normalize();
            branch(vc, m, to, nd, len * 0.6, depth + 1, seed * 31 + k, col, hi, fade);
        }
    }

    // ------------------------------------------------------------------------------------------------ the warnings

    static void telegraph(VertexConsumer vc, Matrix4f m, Vec3 cp, Entity ent, RelicV9.Tech t, float f, float partial, long now) {
        JsonObject o = t.tele;
        String k = o.has("k") ? o.get("k").getAsString() : "self";
        double r = o.has("r") ? o.get("r").getAsDouble() : 4;
        Vec3 pos = ent.getPosition(partial);
        Vec3 c = pos.subtract(cp).add(0, 0.06, 0);
        Vec3 d = flat(ent.getViewVector(partial));
        Vec3 sd = side(d);
        float pulse = 0.55F + 0.45F * (float) Math.sin((now + partial) * 0.6);
        int col = t.color, warn = t.slot == 2 ? 0xFF4030 : lighter(t.color, 0.3F);
        float a = (0.25F + 0.5F * f) * pulse;
        switch (k) {
            case "line" -> {
                double w = o.has("w") ? o.get("w").getAsDouble() : 2.5;
                Vec3 far = c.add(d.scale(r * Math.min(1, f * 1.5)));
                quad(vc, m, c.add(sd.scale(w * 0.5)), far.add(sd.scale(w * 0.5)), far.subtract(sd.scale(w * 0.5)), c.subtract(sd.scale(w * 0.5)), argb(warn, a * 0.35F));
                beam(vc, m, c.add(sd.scale(w * 0.5)), far.add(sd.scale(w * 0.5)), 0.1, argb(warn, a));
                beam(vc, m, c.subtract(sd.scale(w * 0.5)), far.subtract(sd.scale(w * 0.5)), 0.1, argb(warn, a));
            }
            case "cone" -> {
                double deg = o.has("a") ? o.get("a").getAsDouble() : 110;
                double half = Math.toRadians(deg) / 2, base = Math.atan2(d.z, d.x);
                ring(vc, m, c, new Vec3(1, 0, 0), new Vec3(0, 0, 1), r * Math.min(1, f * 1.5), 0.25, 32, argb(warn, a), base - half, half * 2);
                for (int sgn = -1; sgn <= 1; sgn += 2) {
                    double ang = base + sgn * half;
                    beam(vc, m, c, c.add(Math.cos(ang) * r, 0, Math.sin(ang) * r), 0.1, argb(warn, a));
                }
            }
            case "circle" -> ring(vc, m, c, new Vec3(1, 0, 0), new Vec3(0, 0, 1), r * Math.min(1, f * 1.3), 0.3, 64, argb(warn, a), now * 0.02, Math.PI * 2);
            case "target" -> {
                double ar = o.has("ar") ? o.get("ar").getAsDouble() : 3;
                Vec3 at = RelicClient.lookPoint(ent, r).subtract(cp).add(0, 0.06, 0);
                ring(vc, m, at, new Vec3(1, 0, 0), new Vec3(0, 0, 1), ar, 0.2, 40, argb(warn, a), -now * 0.05, Math.PI * 2);
                ring(vc, m, at, new Vec3(1, 0, 0), new Vec3(0, 0, 1), ar * (1 - f) + 0.3, 0.12, 40, argb(0xFFFFFF, a), 0, Math.PI * 2);
            }
            default -> ring(vc, m, c, new Vec3(1, 0, 0), new Vec3(0, 0, 1), Math.max(1.2, r), 0.15, 40, argb(col, a), now * 0.05, Math.PI * 2);
        }
        // the light gathering at the weapon
        Vec3 hand = ent.getEyePosition(partial).add(ent.getViewVector(partial).scale(0.8)).add(0, -0.45, 0).subtract(cp);
        double orb = 0.15 + 0.45 * f * (t.slot == 2 ? 1.6 : 1.0);
        for (int i = 0; i < 3; i++) {
            double lon = i * Math.PI / 3 + now * 0.2;
            ring(vc, m, hand, new Vec3(Math.cos(lon), 0, Math.sin(lon)), new Vec3(0, 1, 0), orb, orb * 0.25, 16, argb(i == 0 ? 0xFFFFFF : col, 0.4F + 0.5F * f), 0,
                Math.PI * 2);
        }
    }

    // ------------------------------------------------------------------------------------------- units and fields

    static void thing(VertexConsumer vc, Matrix4f m, Vec3 cp, String kind, int col, Vec3 at, float radius, float age, float hp) {
        Vec3 c = at.subtract(cp);
        int hi = lighter(col, 0.6F);
        if (kind.startsWith("field:")) {
            ring(vc, m, c.add(0, 0.07, 0), new Vec3(1, 0, 0), new Vec3(0, 0, 1), radius, 0.18, 64, argb(col, 0.6F), age * 0.03, Math.PI * 2);
            ring(vc, m, c.add(0, 0.08, 0), new Vec3(1, 0, 0), new Vec3(0, 0, 1), radius * 0.7, 0.08, 48, argb(hi, 0.45F), -age * 0.05, Math.PI * 2);
            if (kind.equals("field:canopy")) {
                for (int k = 1; k < 4; k++) {
                    double lat = k / 4.0 * Math.PI / 2;
                    ring(vc, m, c.add(0, Math.sin(lat) * radius * 0.5 + 2, 0), new Vec3(1, 0, 0), new Vec3(0, 0, 1), Math.cos(lat) * radius, 0.1, 48,
                        argb(col, 0.25F), age * 0.01, Math.PI * 2);
                }
            }
            return;
        }
        // a unit: a turning crystal over a small circle; dimmer as it is worn down
        double s = 0.45, spin = age * 0.12, bob = Math.sin(age * 0.15) * 0.12;
        Vec3 mid = c.add(0, 0.8 + bob, 0);
        Vec3 top = mid.add(0, s * 1.6, 0), bot = mid.add(0, -s * 1.2, 0);
        float a = 0.45F + 0.4F * hp;
        for (int k = 0; k < 4; k++) {
            double a0 = spin + k * Math.PI / 2, a1 = a0 + Math.PI / 2;
            Vec3 p0 = mid.add(Math.cos(a0) * s, 0, Math.sin(a0) * s), p1 = mid.add(Math.cos(a1) * s, 0, Math.sin(a1) * s);
            quad(vc, m, top, p0, p1, top, argb(k % 2 == 0 ? col : hi, a));
            quad(vc, m, bot, p0, p1, bot, argb(k % 2 == 0 ? hi : col, a * 0.8F));
        }
        ring(vc, m, c.add(0, 0.06, 0), new Vec3(1, 0, 0), new Vec3(0, 0, 1), 0.9, 0.08, 24, argb(col, 0.6F), -spin, Math.PI * 2);
        switch (kind) {
            case "warden", "horn", "box" -> ring(vc, m, mid, new Vec3(1, 0, 0), new Vec3(0, 1, 0), 1.1, 0.06, 24, argb(hi, 0.5F), spin, Math.PI * 2);
            case "vine" -> ring(vc, m, c.add(0, 0.1, 0), new Vec3(1, 0, 0), new Vec3(0, 0, 1), 3.5, 0.06, 32, argb(0x80FF80, 0.4F), spin, Math.PI * 2);
            default -> {
            }
        }
    }
}
