package jp.oror.reborn.waza.client;

import java.io.DataInputStream;
import java.io.InputStream;

/**
 * (057) The 984 techniques' own motions (tools/t984/build_waza.py: waza/waza_motions.bin): for each, keyframes of the
 * rig's parts by role (the arms, elbows, knees, legs, head, torso, root with its lift, jaw, wings and tail) at the
 * technique's own moments (the gathering of its windup, each of its hits, the hold, the return), and a beat that moves
 * within its active window. No two are alike (the builder checks every pair).
 */
public final class WazaMotions {
    public static final int ROLES = 12, VALUES = ROLES * 3 + 1;
    public static final String[] ROLE_NAMES = {"arm_r", "arm_l", "elbow", "knee", "leg_r", "leg_l", "head", "torso", "root", "jaw", "wing", "tail"};
    public static final String[] BEATS = {"", "alternate", "hammer", "clock", "spin", "tremble", "twitch", "bob", "leap", "conduct", "weave", "run",
        "write", "flap"};

    public record Motion(int[] times, float[][] poses, int beat, int freq, int amp) {
    }

    private static Motion[] all;

    private WazaMotions() {
    }

    public static Motion of(int index) {
        if (all == null) {
            load();
        }
        return index >= 0 && index < all.length ? all[index] : null;
    }

    private static synchronized void load() {
        if (all != null) {
            return;
        }
        // the 984's motions, then (059c) the king's and Azazel's V20 actions' after them (their indexes go on from 984)
        Motion[] m = new Motion[jp.oror.reborn.waza.Waza.ALL.size()];
        read("/assets/oror_supreme_bosses/waza/waza_motions.bin", m, 0);
        read("/assets/oror_supreme_bosses/waza/waza_royal_motions.bin", m, 984);
        all = m;
    }

    private static void read(String path, Motion[] m, int base) {
        try (InputStream raw = WazaMotions.class.getResourceAsStream(path)) {
            if (raw == null) {
                return;
            }
            DataInputStream in = new DataInputStream(new java.io.BufferedInputStream(raw));
            byte[] magic = new byte[4];
            in.readFully(magic);
            int n = in.readUnsignedShort();
            for (int i = 0; i < n; i++) {
                int idx = in.readUnsignedShort() + base;
                int keys = in.readUnsignedByte();
                int beat = in.readUnsignedByte();
                int freq = in.readUnsignedByte();
                int amp = in.readUnsignedByte();
                int[] times = new int[keys];
                float[][] poses = new float[keys][VALUES];
                for (int k = 0; k < keys; k++) {
                    times[k] = in.readUnsignedShort();
                    for (int v = 0; v < VALUES; v++) {
                        byte q = in.readByte();
                        poses[k][v] = v == VALUES - 1 ? q / 10F : q / 40F;
                    }
                }
                if (idx < m.length) {
                    m[idx] = new Motion(times, poses, beat, freq, amp);
                }
            }
        } catch (Exception ex) {
            // without the table every technique still runs; the rig keeps its idle
        }
    }

    /** The pose at time (ticks since the technique began), eased between keyframes. */
    public static float[] sample(Motion m, float time) {
        float[] out = new float[VALUES];
        int[] t = m.times();
        if (t.length == 0) {
            return out;
        }
        if (time <= t[0]) {
            return m.poses()[0].clone();
        }
        for (int k = 0; k < t.length - 1; k++) {
            if (time <= t[k + 1]) {
                float span = Math.max(1, t[k + 1] - t[k]);
                float u = (time - t[k]) / span;
                // the strikes snap (fast out, a touch past and back); the gathering and the return ease
                float[] a = m.poses()[k], b = m.poses()[k + 1];
                float e = span <= 3 ? outBack(u) : smooth(u);
                for (int v = 0; v < VALUES; v++) {
                    out[v] = a[v] + (b[v] - a[v]) * e;
                }
                return out;
            }
        }
        return m.poses()[t.length - 1].clone();
    }

    static float smooth(float u) {
        u = Math.max(0, Math.min(1, u));
        return u * u * (3 - 2 * u);
    }

    static float outBack(float u) {
        u = Math.max(0, Math.min(1, u)) - 1;
        float c = 1.70158F;
        return 1 + (c + 1) * u * u * u + c * u * u;
    }
}
