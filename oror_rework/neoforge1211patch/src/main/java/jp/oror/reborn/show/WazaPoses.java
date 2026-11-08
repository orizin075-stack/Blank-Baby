package jp.oror.reborn.show;

import java.util.List;
import jp.oror.reborn.waza.Waza;
import jp.oror.reborn.waza.client.WazaMotions;
import net.minecraft.util.Mth;

/**
 * (057) One of the 984 techniques danced on a character's rig: its own keyframes (WazaMotions) laid over the rig's idle
 * by the parts' roles, with its beat moving within its active window (thrusts in turn, a hammer's beat, a hand drawing
 * a clock backwards or a word in the air, a whirl, a trembling, wings beating). A rig without arms still rears its head
 * on the gathering and thrusts it on the blow, its jaw opens, its wings spread and its tail lashes.
 */
public final class WazaPoses {
    private WazaPoses() {
    }

    public static void apply(Object model, Waza w, float time, long seed) {
        WazaMotions.Motion m = WazaMotions.of(w.index());
        if (m == null) {
            return;
        }
        float[] p = WazaMotions.sample(m, time);
        int wu = w.windup(), al = w.activeLength();
        float a = time - wu;
        boolean active = a >= 0 && a <= al;
        float live = !active ? 0 : a < al * 0.8F ? 1 : Math.max(0, 1 - (a - al * 0.8F) / (al * 0.2F));
        float gather = time < wu ? Math.min(1, time / Math.max(1, wu)) : Math.max(0, 1 - a / 6F);
        String beat = WazaMotions.BEATS[Math.min(WazaMotions.BEATS.length - 1, m.beat())];
        float freq = m.freq() * 0.18F;
        float amp = m.amp() / 40F;
        List<TechniquePoses.Ref> parts = TechniquePoses.parts(model);
        boolean arms = false;
        for (TechniquePoses.Ref r : parts) {
            arms |= r.role().startsWith("arm");
        }
        // a little of each technique's own seed in its beat's phase, so two casts of it are not mirror images
        float phase = (seed & 0xFF) / 40F;
        for (TechniquePoses.Ref r : parts) {
            int i = index(r.role());
            if (i < 0) {
                continue;
            }
            float x = p[i * 3], y = p[i * 3 + 1], z = p[i * 3 + 2];
            float lift = 0;
            if (r.role().equals("root")) {
                lift = p[WazaMotions.VALUES - 1];
            }
            switch (r.role()) {
                case "wing" -> {
                    float s = r.left() ? -1 : 1;
                    y *= s;
                    z *= s;
                }
                case "tail" -> {
                    float s = (r.left() ? -1 : 1) / (1 + r.index() * 0.3F);
                    x /= 1 + r.index() * 0.3F;
                    y *= s;
                }
                case "head" -> {
                    if (!arms) {
                        // no arms: the head gathers and strikes for them
                        x += -0.4F * gather + 0.35F * live;
                    }
                }
                default -> {
                }
            }
            if (live > 0) {
                float tt = time + phase;
                switch (beat) {
                    case "alternate" -> {
                        if (r.role().equals("arm_r")) {
                            x += Mth.sin(tt * freq) * amp * live;
                        } else if (r.role().equals("arm_l")) {
                            x -= Mth.sin(tt * freq) * amp * live;
                        }
                    }
                    case "hammer" -> {
                        if (r.role().equals("arm_r")) {
                            x += Math.abs(Mth.sin(tt * freq * 0.5F)) * amp * 1.5F * live;
                        }
                    }
                    case "clock", "write" -> {
                        if (r.role().equals("arm_r")) {
                            float k = beat.equals("clock") ? -1 : 1;
                            x += Mth.cos(tt * freq * k) * amp * 0.6F * live;
                            z += Mth.sin(tt * freq * k) * amp * 0.6F * live;
                        }
                    }
                    case "spin" -> {
                        if (r.role().equals("root")) {
                            y += a / Math.max(1, al) * Mth.TWO_PI * (1 + m.freq() / 4);
                        }
                    }
                    case "tremble" -> {
                        x += Mth.sin(tt * 3.1F + r.index()) * 0.04F * live;
                        z += Mth.cos(tt * 2.7F + r.index()) * 0.04F * live;
                    }
                    case "twitch" -> {
                        if (((int) (tt * 0.7F) & 3) == 0) {
                            x += 0.18F * live * (r.left() ? -1 : 1);
                        }
                    }
                    case "bob" -> {
                        if (r.role().equals("root")) {
                            lift += Mth.sin(tt * freq * 0.5F) * amp * 4 * live;
                        }
                    }
                    case "leap" -> {
                        if (r.role().equals("root")) {
                            lift += Mth.sin(Math.min(1, a / Math.max(1, al)) * Mth.PI) * 8 * live;
                        }
                    }
                    case "conduct" -> {
                        if (r.role().startsWith("arm")) {
                            x += Mth.sin(tt * freq + (r.role().equals("arm_l") ? Mth.PI : 0)) * amp * live;
                        }
                    }
                    case "weave" -> {
                        if (r.role().equals("torso") || r.role().equals("root")) {
                            z += Mth.sin(tt * freq * 0.5F) * amp * 0.5F * live;
                        }
                    }
                    case "run" -> {
                        if (r.role().startsWith("leg")) {
                            x += Mth.sin(tt * freq + (r.role().equals("leg_l") ? Mth.PI : 0)) * amp * 1.2F * live;
                        } else if (r.role().startsWith("arm")) {
                            x -= Mth.sin(tt * freq + (r.role().equals("arm_l") ? Mth.PI : 0)) * amp * 0.8F * live;
                        }
                    }
                    case "flap" -> {
                        if (r.role().equals("wing")) {
                            y += Mth.sin(tt * freq) * amp * 1.5F * live * (r.left() ? -1 : 1);
                        }
                    }
                    default -> {
                    }
                }
            }
            r.part().xRot += x;
            r.part().yRot += y;
            r.part().zRot += z;
            if (r.role().equals("root")) {
                r.part().y -= lift;
            }
        }
    }

    private static int index(String role) {
        for (int i = 0; i < WazaMotions.ROLE_NAMES.length; i++) {
            if (WazaMotions.ROLE_NAMES[i].equals(role)) {
                return i;
            }
        }
        return -1;
    }
}
