package jp.oror.reborn.royal;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;
import org.joml.Matrix4f;

/**
 * (059, the V20 design's 06_at_field.md) The villager king's AT field as a membrane of hexagonal cells round him, in
 * place of the blue line box: drawn only, the field's strength and its rules are the server's as they were.
 *
 * <ul>
 * <li>each form its own: the villager king pale blue, the hero king Arb white-gold, the broken king purple and blue
 * (cells slipping into two as the field runs low), Baal Zebul two shells, blue within and gold without;</li>
 * <li>faint while it holds (0.10 to 0.18), its colour going over to yellow-white (purple for the last two forms) and
 * cracks spreading under a quarter of its strength;</li>
 * <li>a blow against it (the server says where it came from, AtHit): a white hexagon where it struck for four ticks,
 * then a ring running out over the membrane from there (0.4 to 2.5 blocks) until the sixteenth;</li>
 * <li>broken: the cells fly apart and fade from the rim inwards in ten ticks; restored: they fill in again from the
 * crown down in twenty-four;</li>
 * <li>beyond 60 blocks only its outline, nearer fewer cells than close by (at most some 250 faces a shell).</li>
 * </ul>
 */
public final class ATFieldRenderer {
    private static final Map<Integer, State> STATES = new HashMap<>();
    /** each form's membrane, its second colour (the broken king's slipped cells, Baal Zebul's outer shell), and low */
    private static final int[] RIM = {0x8CC8FF, 0xFFEBAA, 0x9C78FF, 0x6EA0FF};
    private static final int[] SECOND = {0x8CC8FF, 0xFFEBAA, 0x5A3CC8, 0xF0C85A};
    private static final int[] LOW = {0xFFF0B4, 0xFFF0B4, 0xC060FF, 0xC060FF};

    private ATFieldRenderer() {
    }

    private static final class State {
        boolean breached;
        float breachAt = -1000F, restoreAt = -1000F, field = -1F, lastHitAt = -1000F;
        final List<float[]> hits = new ArrayList<>();   // direction x y z, tick, strength
    }

    /** A blow the field took, from the server: the direction from the king's middle to where it came from. */
    public static void hit(int id, float dx, float dy, float dz, float strength) {
        ClientLevel level = Minecraft.getInstance().level;
        Entity e = level == null ? null : level.getEntity(id);
        if (e == null) {
            return;
        }
        State s = STATES.computeIfAbsent(id, k -> new State());
        if (s.hits.size() >= 12) {
            s.hits.remove(0);
        }
        s.hits.add(new float[]{dx, dy, dz, e.tickCount, strength});
        s.lastHitAt = e.tickCount;
    }

    private static float capacity(int phase) {
        return 10000F * (float) Math.pow(4, Mth.clamp(phase, 0, 3));
    }

    /** Draws the king's field (and its breaking and mending); false when there is nothing to draw. */
    static boolean render(RoyalMob mob, float partial, PoseStack pose, MultiBufferSource buffers) {
        if (STATES.size() > 48) {
            ClientLevel level = Minecraft.getInstance().level;
            STATES.keySet().removeIf(id -> level == null || level.getEntity(id) == null);
        }
        State s = STATES.computeIfAbsent(mob.getId(), k -> new State());
        float now = mob.tickCount + partial;
        int phase = Mth.clamp(mob.lifePhase(), 0, 3);
        float cap = capacity(phase);
        float field = mob.atField();
        boolean breached = mob.atBreached() || field <= 0.0F;
        if (breached && !s.breached) {
            s.breachAt = now;
        } else if (!breached && s.breached) {
            s.restoreAt = now;
        }
        Vec3 cam = Minecraft.getInstance().gameRenderer.getMainCamera().getPosition();
        // a drop with no word from the server about it (an older server, a blow it did not see): on the side to the eye
        if (!breached && s.field > 0 && field < s.field - cap * 0.002F && now - s.lastHitAt > 3) {
            Vec3 d = cam.subtract(mob.getBoundingBox().getCenter());
            if (d.lengthSqr() > 1e-4) {
                d = d.normalize();
                s.hits.add(new float[]{(float) d.x, (float) d.y, (float) d.z, mob.tickCount, (s.field - field) / cap});
                s.lastHitAt = now;
            }
        }
        s.breached = breached;
        s.field = field;
        s.hits.removeIf(h -> now - h[3] > 17);
        float sinceBreak = now - s.breachAt;
        if (breached && sinceBreak > 10) {
            return false;
        }
        float ratio = breached ? 0.0F : Mth.clamp(field / cap, 0.0F, 1.0F);
        double dist = cam.distanceTo(mob.position());
        int bands = dist > 60 ? 0 : dist > 24 ? 6 : 9;
        double rx = mob.getBbWidth() * 0.5 + 0.55, ry = (mob.getBbHeight() + 0.5) * 0.5, cy = ry - 0.2;
        VertexConsumer vc = buffers.getBuffer(RenderType.lightning());
        Matrix4f m = pose.last().pose();
        float pulse = 0.14F + 0.04F * Mth.sin(now * 0.1F);
        int rim = RIM[phase];
        if (ratio < 0.25F) {
            rim = mix(rim, LOW[phase], (0.25F - ratio) / 0.25F);
        }
        Shell inner = new Shell(rx, ry, cy, rim, pulse);
        if (bands == 0) {
            inner.outline(vc, m);
        } else {
            inner.cells(vc, m, bands, s, now, ratio, breached ? sinceBreak : -1, now - s.restoreAt, phase == 2 ? SECOND[2] : -1, mob.getId());
            if (phase == 3) {
                new Shell(rx * 1.14, ry * 1.1, cy, mix(SECOND[3], LOW[3], ratio < 0.25F ? (0.25F - ratio) / 0.25F : 0), pulse * 0.8F)
                    .cells(vc, m, Math.max(5, bands - 3), s, now, ratio, breached ? sinceBreak : -1, now - s.restoreAt, -1, mob.getId() * 31);
            }
            if (ratio < 0.25F && !breached) {
                inner.cracks(vc, m, mob.getId(), 1 + (int) ((0.25F - ratio) / 0.25F * 8));
            }
        }
        if (!breached) {
            for (float[] h : s.hits) {
                inner.impact(vc, m, new Vec3(h[0], h[1], h[2]), now - h[3], h[4]);
            }
        }
        return true;
    }

    // ------------------------------------------------------------------------------------------------------ the shell

    private record Shell(double rx, double ry, double cy, int rgb, float alpha) {
        /** The point of the ellipsoid in a direction (unit), a little out from it by f. */
        Vec3 at(Vec3 d, double f) {
            return new Vec3(d.x * this.rx * f, this.cy + d.y * this.ry * f, d.z * this.rx * f);
        }

        static Vec3 dir(double lat, double lon) {
            double c = Math.cos(lat);
            return new Vec3(c * Math.cos(lon), Math.sin(lat), c * Math.sin(lon));
        }

        void outline(VertexConsumer vc, Matrix4f m) {
            int a = argb(this.rgb, this.alpha * 1.2F);
            for (double lat : new double[]{-0.8, 0, 0.8}) {
                for (int k = 0; k < 24; k++) {
                    edge(vc, m, at(dir(lat, k * Math.PI / 12), 1), at(dir(lat, (k + 1) * Math.PI / 12), 1), 0.05, a);
                }
            }
            for (int k = 0; k < 6; k++) {
                for (int j = 0; j < 8; j++) {
                    double l0 = -1.3 + 2.6 * j / 8, l1 = -1.3 + 2.6 * (j + 1) / 8;
                    edge(vc, m, at(dir(l0, k * Math.PI / 3), 1), at(dir(l1, k * Math.PI / 3), 1), 0.05, a);
                }
            }
        }

        void cells(VertexConsumer vc, Matrix4f m, int bands, State s, float now, float ratio, float breaking, float mending,
                   int slipped, int seed) {
            double span = Math.toRadians(150);
            double dLat = span / (bands - 1);
            for (int i = 0; i < bands; i++) {
                double lat = -span / 2 + dLat * i;
                int n = Math.max(5, (int) Math.round(2.0 * bands * Math.cos(lat)));
                double dLon = 2 * Math.PI / n;
                for (int j = 0; j < n; j++) {
                    double lon = dLon * (j + (i % 2) * 0.5) + now * 0.004;
                    Vec3 d = dir(lat, lon);
                    double size = 1.0, out = 1.0;
                    float fade = 1.0F;
                    if (breaking >= 0) {
                        // breaking: the rim (the middle band) first, the crown and the foot last
                        float delay = (float) (Math.abs(lat) / (span / 2)) * 4;
                        float t = Mth.clamp((breaking - delay) / (10 - delay), 0, 1);
                        size = 1 - t;
                        out = 1 + t * 0.8;
                        fade = 1 - t;
                    } else if (mending < 24) {
                        // mending: from the crown down
                        float from = (float) ((span / 2 - lat) / span);
                        float t = Mth.clamp((mending / 24F - from * 0.8F) * 5, 0, 1);
                        size = t;
                        fade = t;
                    }
                    if (size <= 0.02 || fade <= 0.02F) {
                        continue;
                    }
                    double ae = dLon * 0.5 * Math.cos(lat) * 0.96 * size, an = dLat * 0.62 * size;
                    hexagon(vc, m, d, lat, lon, ae, an, out, this.rgb, this.alpha * fade, 0.0F);
                    // the broken king's cells slip into two as his field runs low
                    if (slipped >= 0 && ratio < 0.6F && (Math.floorMod((int) (lon * 97 + lat * 31) + seed, 100)) < (int) ((0.6F - ratio) * 160)) {
                        hexagon(vc, m, d, lat + an * 0.35, lon + 0.04, ae * 0.9, an * 0.9, out * 1.03, slipped, this.alpha * fade * 0.8F, 0.0F);
                    }
                    // the cells at a fresh blow light white
                    for (float[] h : s.hits) {
                        float age = now - h[3];
                        if (age <= 4) {
                            double dot = d.x * h[0] + d.y * h[1] + d.z * h[2];
                            if (dot > Math.cos(dLat * 1.2)) {
                                hexagon(vc, m, d, lat, lon, ae * 1.08, an * 1.08, out * 1.01, 0xFFFFFF, 0.85F * (1 - age / 5F), 0.6F);
                            }
                        }
                    }
                }
            }
        }

        /** A hexagonal cell round direction d: its face faint, its six sides brighter. */
        private void hexagon(VertexConsumer vc, Matrix4f m, Vec3 d, double lat, double lon, double ae, double an, double out,
                             int rgb, float alpha, float fill) {
            Vec3 east = new Vec3(-Math.sin(lon), 0, Math.cos(lon));
            Vec3 north = new Vec3(-Math.sin(lat) * Math.cos(lon), Math.cos(lat), -Math.sin(lat) * Math.sin(lon));
            Vec3[] c = new Vec3[6];
            Vec3[] in = new Vec3[6];
            for (int k = 0; k < 6; k++) {
                double a = Math.PI / 3 * k + Math.PI / 6;
                Vec3 dk = d.add(east.scale(Math.cos(a) * ae)).add(north.scale(Math.sin(a) * an)).normalize();
                Vec3 dki = d.add(east.scale(Math.cos(a) * ae * 0.82)).add(north.scale(Math.sin(a) * an * 0.82)).normalize();
                c[k] = at(dk, out);
                in[k] = at(dki, out);
            }
            int face = argb(rgb, Math.max(fill, alpha * 0.45F));
            quad(vc, m, c[0], c[1], c[2], c[3], face);
            quad(vc, m, c[0], c[3], c[4], c[5], face);
            int side = argb(rgb, alpha * 1.4F);
            for (int k = 0; k < 6; k++) {
                int k1 = (k + 1) % 6;
                quad(vc, m, c[k], c[k1], in[k1], in[k], side);
            }
        }

        /** Cracks over the membrane (always the same ones for the same king): thin jagged lines. */
        void cracks(VertexConsumer vc, Matrix4f m, int seed, int count) {
            java.util.Random r = new java.util.Random(seed * 7919L);
            int a = argb(0xFFFFFF, 0.55F);
            for (int k = 0; k < count; k++) {
                double lat = (r.nextDouble() - 0.5) * 2.2, lon = r.nextDouble() * Math.PI * 2;
                Vec3 p = at(dir(lat, lon), 1.005);
                for (int j = 0; j < 6; j++) {
                    lat += (r.nextDouble() - 0.5) * 0.35;
                    lon += (r.nextDouble() - 0.3) * 0.3;
                    Vec3 q = at(dir(Mth.clamp(lat, -1.3, 1.3), lon), 1.005);
                    edge(vc, m, p, q, 0.035, a);
                    p = q;
                }
            }
        }

        /** After the white hexagon, a ring running out over the membrane from where the blow struck. */
        void impact(VertexConsumer vc, Matrix4f m, Vec3 d, float age, float strength) {
            if (age < 5 || age > 16) {
                return;
            }
            float t = (age - 5) / 11F;
            double radius = 0.4 + 2.1 * t;
            double mean = (this.rx + this.ry) * 0.5;
            double theta = Math.min(Math.PI * 0.9, radius / mean);
            Vec3 u = Math.abs(d.y) < 0.9 ? d.cross(new Vec3(0, 1, 0)).normalize() : d.cross(new Vec3(1, 0, 0)).normalize();
            Vec3 v = d.cross(u).normalize();
            int a = argb(0xFFFFFF, (0.35F + Math.min(0.4F, strength * 4)) * (1 - t));
            Vec3 prev = null;
            for (int k = 0; k <= 28; k++) {
                double phi = Math.PI * 2 * k / 28;
                Vec3 dd = d.scale(Math.cos(theta)).add(u.scale(Math.cos(phi) * Math.sin(theta))).add(v.scale(Math.sin(phi) * Math.sin(theta))).normalize();
                Vec3 p = at(dd, 1.01);
                if (prev != null) {
                    edge(vc, m, prev, p, 0.07, a);
                }
                prev = p;
            }
        }

        /** A thin band from a to b, lying across the membrane (outwards from the king's middle line). */
        private void edge(VertexConsumer vc, Matrix4f m, Vec3 a, Vec3 b, double w, int argb) {
            Vec3 mid = a.add(b).scale(0.5);
            Vec3 outward = new Vec3(mid.x, mid.y - this.cy, mid.z);
            Vec3 along = b.subtract(a);
            Vec3 side = along.cross(outward);
            if (side.lengthSqr() < 1e-8) {
                return;
            }
            side = side.normalize().scale(w * 0.5);
            quad(vc, m, a.add(side), b.add(side), b.subtract(side), a.subtract(side), argb);
        }
    }

    // ------------------------------------------------------------------------------------------------------ helpers

    private static void quad(VertexConsumer vc, Matrix4f m, Vec3 a, Vec3 b, Vec3 c, Vec3 d, int argb) {
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

    private static int argb(int rgb, float alpha) {
        return ((int) (Mth.clamp(alpha, 0.0F, 1.0F) * 255) << 24) | (rgb & 0xFFFFFF);
    }

    private static int mix(int a, int b, float t) {
        t = Mth.clamp(t, 0.0F, 1.0F);
        int r = (int) (((a >> 16) & 255) * (1 - t) + ((b >> 16) & 255) * t);
        int g = (int) (((a >> 8) & 255) * (1 - t) + ((b >> 8) & 255) * t);
        int bl = (int) ((a & 255) * (1 - t) + (b & 255) * t);
        return (r << 16) | (g << 8) | bl;
    }
}
