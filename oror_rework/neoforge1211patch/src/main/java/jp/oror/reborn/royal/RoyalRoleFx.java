package jp.oror.reborn.royal;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import java.util.HashMap;
import java.util.Map;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.util.Mth;
import org.joml.Matrix4f;

/**
 * (059d) What the royals' casting looks like, by role (V20 07_royal_roles_8.md), drawn on the client only and only
 * while the royal casts:
 * <ul>
 * <li>the archmage's circles at his feet, one more layer every half second (three at most), each turning faster than
 * the one inside it and against it, marked with runes;</li>
 * <li>the mage's single thin circle, turning slowly;</li>
 * <li>the sage's faint light about the hands, breathing (no great display: the light is the spell's);</li>
 * <li>the general's order: a small sign of the formation, two squares crossed, under his feet.</li>
 * </ul>
 * The guards and the guard captains have nothing of the kind (the design: no boss-sized effects on the rank and file).
 */
public final class RoyalRoleFx {
    private static final Map<Integer, Integer> CAST_FROM = new HashMap<>();

    private RoyalRoleFx() {
    }

    static void render(RoyalMob mob, float partial, PoseStack pose, MultiBufferSource buffers) {
        if (!mob.isCasting()) {
            CAST_FROM.remove(mob.getId());
            return;
        }
        RoyalRole role = mob.role();
        if (role != RoyalRole.ARCHMAGE && role != RoyalRole.MAGE && role != RoyalRole.SAGE && role != RoyalRole.GENERAL) {
            return;
        }
        if (CAST_FROM.size() > 256) {
            CAST_FROM.clear();
        }
        int from = CAST_FROM.computeIfAbsent(mob.getId(), k -> mob.tickCount);
        float t = mob.tickCount - from + partial;
        float in = Mth.clamp(t / 6F, 0F, 1F);
        VertexConsumer vc = buffers.getBuffer(RenderType.lightning());
        Matrix4f m = pose.last().pose();
        switch (role) {
            case ARCHMAGE -> {
                int layers = Math.min(3, 1 + (int) (t / 10F));
                for (int i = 0; i < layers; i++) {
                    float grow = Mth.clamp((t - i * 10F) / 6F, 0F, 1F);
                    float r = (0.75F + 0.45F * i) * grow;
                    float turn = t * (0.03F + 0.035F * i) * (i % 2 == 0 ? 1F : -1F);
                    ring(vc, m, 0.03F + 0.015F * i, r, 0.06F, turn, 40, i == 1 ? 2 : 1, 0x9A6BFF, 0.55F * grow);
                    runes(vc, m, 0.035F + 0.015F * i, r, turn, 6 + 2 * i, 0xC9A8FF, 0.6F * grow);
                }
            }
            case MAGE -> ring(vc, m, 0.03F, 0.7F, 0.05F, t * 0.02F, 32, 1, 0x7FC8FF, 0.4F * in);
            case SAGE -> {
                float breath = 0.22F + 0.08F * Mth.sin(t * 0.25F);
                ring(vc, m, 1.15F, 0.42F, 0.08F, t * 0.05F, 24, 1, 0xFFF1C2, breath * in);
                ring(vc, m, 1.15F, 0.28F, 0.05F, -t * 0.07F, 18, 1, 0xFFF8E0, breath * 0.8F * in);
            }
            case GENERAL -> {
                float a = 0.45F * in;
                square(vc, m, 0.03F, 1.05F, t * 0.01F, 0.06F, 0xF2C14E, a);
                square(vc, m, 0.035F, 1.05F, t * 0.01F + Mth.PI / 4F, 0.06F, 0xF2C14E, a * 0.8F);
            }
            default -> {
            }
        }
    }

    /** A flat ring of n segments at height y (every skip-th drawn: 2 makes it dashed). */
    private static void ring(VertexConsumer vc, Matrix4f m, float y, float r, float w, float turn, int n, int skip, int rgb, float alpha) {
        if (alpha <= 0.01F || r <= 0.02F) {
            return;
        }
        for (int i = 0; i < n; i += skip) {
            float a0 = turn + Mth.TWO_PI * i / n, a1 = turn + Mth.TWO_PI * (i + 1) / n;
            float c0 = Mth.cos(a0), s0 = Mth.sin(a0), c1 = Mth.cos(a1), s1 = Mth.sin(a1);
            float ri = r - w * 0.5F, ro = r + w * 0.5F;
            quad(vc, m, ri * c0, y, ri * s0, ro * c0, y, ro * s0, ro * c1, y, ro * s1, ri * c1, y, ri * s1, rgb, alpha);
        }
    }

    /** Short strokes across the ring, n of them: the circle's runes. */
    private static void runes(VertexConsumer vc, Matrix4f m, float y, float r, float turn, int n, int rgb, float alpha) {
        if (alpha <= 0.01F || r <= 0.1F) {
            return;
        }
        for (int i = 0; i < n; i++) {
            float a = turn + Mth.TWO_PI * (i + 0.5F) / n;
            float c = Mth.cos(a), s = Mth.sin(a), pc = -s * 0.03F, ps = c * 0.03F;
            float r0 = r - 0.14F, r1 = r + 0.14F;
            quad(vc, m, r0 * c + pc, y, r0 * s + ps, r1 * c + pc, y, r1 * s + ps, r1 * c - pc, y, r1 * s - ps, r0 * c - pc, y, r0 * s - ps, rgb, alpha);
        }
    }

    private static void square(VertexConsumer vc, Matrix4f m, float y, float r, float turn, float w, int rgb, float alpha) {
        for (int i = 0; i < 4; i++) {
            float a0 = turn + Mth.HALF_PI * i, a1 = a0 + Mth.HALF_PI;
            float x0 = r * Mth.cos(a0), z0 = r * Mth.sin(a0), x1 = r * Mth.cos(a1), z1 = r * Mth.sin(a1);
            float dx = x1 - x0, dz = z1 - z0, len = Mth.sqrt(dx * dx + dz * dz);
            float nx = -dz / len * w * 0.5F, nz = dx / len * w * 0.5F;
            quad(vc, m, x0 + nx, y, z0 + nz, x1 + nx, y, z1 + nz, x1 - nx, y, z1 - nz, x0 - nx, y, z0 - nz, rgb, alpha);
        }
    }

    private static void quad(VertexConsumer vc, Matrix4f m, float ax, float ay, float az, float bx, float by, float bz, float cx, float cy,
                             float cz, float dx, float dy, float dz, int rgb, float alpha) {
        int A = (int) (Mth.clamp(alpha, 0F, 1F) * 255), R = (rgb >> 16) & 255, G = (rgb >> 8) & 255, B = rgb & 255;
        vc.addVertex(m, ax, ay, az).setColor(R, G, B, A);
        vc.addVertex(m, bx, by, bz).setColor(R, G, B, A);
        vc.addVertex(m, cx, cy, cz).setColor(R, G, B, A);
        vc.addVertex(m, dx, dy, dz).setColor(R, G, B, A);
        vc.addVertex(m, dx, dy, dz).setColor(R, G, B, A);
        vc.addVertex(m, cx, cy, cz).setColor(R, G, B, A);
        vc.addVertex(m, bx, by, bz).setColor(R, G, B, A);
        vc.addVertex(m, ax, ay, az).setColor(R, G, B, A);
    }
}
