package jp.oror.reborn.royal;

import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import jp.oror.reborn.client.RigModel;
import jp.oror.reborn.show.TechniqueShow;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;
import net.minecraft.world.item.Items;

/**
 * (054) One of the villager king's four rigs (tools/mc/king3d.py): RigModel's idle and walk, then
 * <ul>
 * <li>his deeds' motions (TechniqueShow "move:king_*", KingDeeds), each a windup pose and a strike pose on his arms,
 * body, head and height, and his three returns from death danced out over their whole length (KingCinema);</li>
 * <li>Baal Zebul's five stances, one set of arms shown at a time by what is in his main hand (KingDeeds.stance): the
 * thunder clubs (arms_clubs_*, a mace), the fly lord's scythe (arms_scythe_*, a netherite hoe), the twin swords
 * (arms_twin_*, a netherite sword), the thunder spear (arms_spear_*, a trident), the rainbow bow (arms_bow_*, a bow);</li>
 * <li>the broken king's ruin: the stages of fused monsters (rot1_*, rot2_*, rot3_*) grown in below three quarters,
 * half and a quarter of his health, and his parts jerked out of place, the more the lower he is.</li>
 * </ul>
 * A part is hidden by scaling it to nothing (RigModel draws no part of zero scale).
 */
public final class KingRig extends RigModel<RoyalMob> {
    private static Field partsField;
    private final Map<String, ModelPart> named = new HashMap<>();
    private static final String[] STANCES = {"clubs", "scythe", "twin", "spear", "bow"};
    /** Each stance's holding pose: right upper arm, right forearm, left upper arm, left forearm (x rotations; the
     * weapons' bones in the rig are turned to stand right in it). Kept equal to king3d.HOLD_POSES. */
    private static final float[][] HOLD = {
        {-0.2F, -0.45F, -0.2F, -0.45F},
        {-0.3F, -1.25F, 0F, 0F},
        {-0.25F, -0.6F, -0.25F, -0.6F},
        {-0.3F, -1.2F, 0F, 0F},
        {0F, 0F, -0.3F, -1.25F}};
    @SuppressWarnings("unchecked")
    private final List<ModelPart>[] arms = new List[]{new ArrayList<>(), new ArrayList<>(), new ArrayList<>(), new ArrayList<>(), new ArrayList<>()};
    private final List<ModelPart>[] rot;
    private final List<ModelPart> jitter = new ArrayList<>();
    final boolean broken;

    @SuppressWarnings("unchecked")
    public KingRig(String key) {
        super(key, -1);
        this.broken = key.endsWith("broken");
        this.rot = new List[]{new ArrayList<>(), new ArrayList<>(), new ArrayList<>()};
        try {
            if (partsField == null) {
                partsField = RigModel.class.getDeclaredField("parts");
                partsField.setAccessible(true);
            }
            this.named.putAll((Map<String, ModelPart>) partsField.get(this));
        } catch (ReflectiveOperationException | RuntimeException ex) {
            // without the names the rig is still drawn, only without its stances, stages and moves
        }
        for (Map.Entry<String, ModelPart> e : this.named.entrySet()) {
            String n = e.getKey();
            for (int i = 0; i < STANCES.length; i++) {
                if (n.startsWith("arms_" + STANCES[i] + "_")) {
                    this.arms[i].add(e.getValue());
                }
            }
            if (n.startsWith("rot1_")) {
                this.rot[0].add(e.getValue());
            } else if (n.startsWith("rot2_")) {
                this.rot[1].add(e.getValue());
            } else if (n.startsWith("rot3_")) {
                this.rot[2].add(e.getValue());
            }
        }
        for (String n : new String[]{"head", "torso", "arm_r", "arm_l", "fore_r", "fore_l", "leg_r", "leg_l", "plume", "cape", "sword"}) {
            ModelPart p = this.named.get(n);
            if (p != null) {
                this.jitter.add(p);
            }
        }
    }

    /** 0 clubs, 1 scythe, 2 twin swords, 3 spear, 4 bow (KingDeeds.stance less one). */
    static int stance(RoyalMob e) {
        var m = e.getMainHandItem();
        if (m.is(Items.NETHERITE_HOE)) {
            return 1;
        }
        if (m.is(Items.NETHERITE_SWORD)) {
            return 2;
        }
        if (m.is(Items.TRIDENT)) {
            return 3;
        }
        if (m.is(Items.BOW)) {
            return 4;
        }
        return 0;
    }

    private ModelPart p(String n) {
        return this.named.get(n);
    }

    private static void scale(List<ModelPart> parts, float s) {
        for (ModelPart m : parts) {
            m.xScale = m.yScale = m.zScale = s;
        }
    }

    @Override
    public void setupAnim(RoyalMob e, float swing, float amount, float age, float yaw, float pitch) {
        this.animate(e, swing, amount, age, yaw, pitch, 0, 0F, 0, 0);
        // the stance
        int st = stance(e);
        for (int i = 0; i < this.arms.length; i++) {
            scale(this.arms[i], i == st ? 1F : 0F);
        }
        if (!this.arms[st].isEmpty()) {
            // the stance's holding pose (king3d.HOLD_POSES): each haft through the middle of the fist, square to the
            // forearm, never along it
            float[] h = HOLD[st];
            add("arm_r", h[0], 0, 0);
            add("fore_r", h[1], 0, 0);
            add("arm_l", h[2], 0, 0);
            add("fore_l", h[3], 0, 0);
        }
        // the ruin
        if (this.broken) {
            float ruin = KingLook.ruin(e);
            float[] at = {0.25F, 0.5F, 0.75F};
            for (int i = 0; i < 3; i++) {
                scale(this.rot[i], Mth.clamp((ruin - at[i]) / 0.08F, 0F, 1F));
            }
            int bucket = (int) (age / 2F);
            float amp = 0.5F + ruin * 2.5F;
            scale(this.jitter, 1F);
            for (int i = 0; i < this.jitter.size(); i++) {
                int h = KingLook.hash(e.getId() * 31 + i, bucket);
                if (h % 5 < 1 + (int) (ruin * 3)) {
                    ModelPart m = this.jitter.get(i);
                    m.x += ((h >> 4) % 5 - 2) * 0.4F * amp;
                    m.y += ((h >> 8) % 5 - 2) * 0.3F * amp;
                    m.z += ((h >> 12) % 5 - 2) * 0.4F * amp;
                    m.zRot += ((h >> 16) % 7 - 3) * 0.08F * amp;
                    if (h % 23 == 0) {
                        m.yScale = 1.4F;
                    }
                }
            }
        } else {
            for (List<ModelPart> l : this.rot) {
                scale(l, 0F);
            }
        }
        move(e, age);
    }

    // ------------------------------------------------------------------------------------------------- the moves

    /**
     * Each deed's windup and strike poses: right arm x, y, z; left arm x, y, z; body x, y; head x; height (pixels, +
     * is lower). Offsets on the idle pose.
     */
    private static final Map<String, float[][]> POSES = new HashMap<>();

    static {
        pose("RALLY", new float[]{-2.9F, 0, 0.2F, 0, 0, -0.3F, 0, 0, -0.3F, 0}, new float[]{-1.4F, 0, -0.1F, 0, 0, -0.3F, 0, 0, 0, 0});
        pose("FLAME", new float[]{-1.2F, -0.9F, 0, -1.2F, 0.9F, 0, 0.2F, 0, 0, 0}, new float[]{-1.3F, 0.8F, 1.2F, -1.3F, -0.8F, -1.2F, 0, 0, 0, 0});
        pose("BLINK", new float[]{0.4F, 0, 0, 0.4F, 0, 0, 0.5F, 0, 0, 4F}, new float[]{-2.6F, 0, 0, -2.6F, 0, 0, 0, 0, 0, 0});
        pose("STORM", new float[]{-3.0F, 0, 0.25F, -3.0F, 0, -0.25F, -0.15F, 0, -0.8F, 0}, new float[]{-1.6F, 0, 0, -0.3F, 0, -0.6F, 0, 0, 0, 0});
        pose("SWARM", new float[]{-0.6F, 0, 1.3F, -0.6F, 0, -1.3F, 0, 0, -0.25F, 0}, new float[]{-1.55F, 0, 0.3F, -1.55F, 0, -0.3F, 0, 0, 0, 0});
        pose("SLAM", new float[]{-3.1F, 0, 0, -3.1F, 0, 0, -0.3F, 0, 0, 0}, new float[]{-0.4F, 0, 0, -0.4F, 0, 0, 0.55F, 0, 0.3F, 3F});
        pose("CHARGE", new float[]{0.6F, 0, 0, -0.4F, 0, 0, 0.5F, 0, 0.2F, 1.5F}, new float[]{-1.6F, 0, 0, -0.8F, 0, 0, 0.4F, 0, 0, 1F});
        pose("CLEAVE", new float[]{-2.2F, -1.2F, 0, -0.6F, 0, 0, 0, -0.6F, 0, 0}, new float[]{-1.3F, 1.4F, 0, -0.4F, 0, 0, 0, 0.7F, 0, 0});
        pose("SPEAR", new float[]{-2.8F, 0, 0.3F, -1.2F, 0, 0, 0, -0.4F, 0, 0}, new float[]{-1.2F, 0, 0, -0.6F, 0, 0, 0.1F, 0.3F, 0, 0});
        pose("DESYNC", new float[]{0.5F, 0.6F, 0.4F, 0.5F, -0.6F, -0.4F, 0.3F, 0.5F, 0.6F, 2F}, new float[]{-1.8F, -0.8F, 0, -1.8F, 0.8F, 0, 0.2F, -0.6F, 0, 0});
        pose("ROLLBACK", new float[]{-1.6F, 0, 0, -0.2F, 0, -1.4F, 0, 0, -0.4F, 0}, new float[]{-1.6F, 0, 2.6F, -0.2F, 0, -2.6F, 0, 3.0F, 0, 0});
        pose("CORRUPT", new float[]{-2.5F, 0, 2.5F, -2.5F, 0, -2.5F, -0.2F, 0, 0.6F, 0}, new float[]{-0.4F, 0, 1.6F, -0.4F, 0, -1.6F, 0.3F, 0, -0.6F, 0});
        pose("GHOSTS", new float[]{-0.5F, 0, 0.9F, -0.5F, 0, -0.9F, 0.2F, 0, 0.3F, 0}, new float[]{0.6F, 0, 0.5F, 0.6F, 0, -0.5F, 0.4F, 0, 0.4F, 2F});
        pose("JUDGMENT", new float[]{-3.1F, 0, 0, -0.2F, 0, -0.3F, -0.2F, 0, -0.7F, 0}, new float[]{-0.6F, 0, 0, -0.2F, 0, -0.3F, 0.2F, 0, 0.1F, 0});
        pose("CHASER", new float[]{-2.8F, 0, 0.3F, -0.5F, 0, -0.4F, 0, -0.5F, 0, 0}, new float[]{-0.9F, 0, 0, -0.5F, 0, -0.4F, 0.2F, 0.4F, 0, 0});
        pose("DRIVER", new float[]{-3.1F, 0, 0, -3.1F, 0, 0, -0.4F, 0, -0.4F, 3F}, new float[]{-0.3F, 0, 0, -0.3F, 0, 0, 0.6F, 0, 0.3F, 4F});
        pose("GAZE", new float[]{-0.4F, 0, 1.4F, -0.4F, 0, -1.4F, -0.3F, 0, -0.9F, 0}, new float[]{-1.5F, 0, 0.1F, -1.5F, 0, -0.1F, 0, 0, 0, 0});
        pose("PLAGUE", new float[]{-0.3F, 0, 1.9F, -0.3F, 0, -1.9F, -0.2F, 0, -0.7F, 0}, new float[]{-1.4F, 0, 0.6F, -1.4F, 0, -0.6F, 0.2F, 2.0F, 0.2F, 0});
        pose("REAP", new float[]{-2.4F, -1.4F, 0.3F, -1.2F, 0.6F, 0, 0, -1.0F, 0, 1F}, new float[]{-1.0F, 1.6F, 0, -0.8F, -0.4F, 0, 0.2F, 1.2F, 0, 2F});
        pose("VORTEX", new float[]{-2.0F, 0, 1.0F, -2.0F, 0, -1.0F, 0, 0, -0.5F, 0}, new float[]{-2.0F, 0, 1.0F, -2.0F, 0, -1.0F, 0, 6.28F, 0, 0});
        pose("BRAND", new float[]{-2.6F, 0.4F, 0, -0.3F, 0, -0.3F, -0.1F, 0, -0.4F, 0}, new float[]{-1.5F, -0.3F, 0, -0.3F, 0, -0.3F, 0.15F, 0, 0, 0});
        // the nastier deeds: the hero's execution and sundering, the broken one's deletion, Baal Zebul's feast and the
        // day of judgment; the twin swords', the spear's and the bow's
        pose("EXECUTION", new float[]{-2.2F, 0, 0, -2.9F, 0, -0.2F, 0, -0.3F, 0, 0}, new float[]{-3.0F, 0, 0, -3.1F, 0, 0, 0.6F, 0, 0.3F, 2F});
        pose("SUNDER", new float[]{-0.6F, 0, 0, -1.8F, 0.8F, 0, 0, 0.5F, 0, 0}, new float[]{-0.4F, 0, 0, -1.6F, -0.9F, 0, 0.3F, -0.6F, 0, 1F});
        pose("VOID", new float[]{-1.6F, 0, 0.9F, -1.6F, 0, -0.9F, 0, 0, -0.3F, 0}, new float[]{-1.6F, 0, -0.4F, -1.6F, 0, 0.4F, 0.2F, 0, 0.4F, 0});
        pose("FEAST", new float[]{-0.8F, 0, 1.6F, -0.8F, 0, -1.6F, -0.4F, 0, -0.8F, 0}, new float[]{-2.0F, 0, 0.6F, -2.0F, 0, -0.6F, 0.3F, 0, 0.5F, 0});
        pose("DOOMSDAY", new float[]{-3.1F, 0, 0.5F, -3.1F, 0, -0.5F, -0.4F, 0, -1.0F, 0}, new float[]{-1.4F, 0, 1.6F, -1.4F, 0, -1.6F, 0.4F, 0, 0.6F, 2F});
        pose("FLURRY", new float[]{-1.9F, -0.8F, 0, -1.9F, 0.8F, 0, 0.3F, 0, 0, 1F}, new float[]{-1.2F, 1.2F, 0, -1.2F, -1.2F, 0, 0.2F, 3.14F, 0, 0});
        pose("CROSSSLASH", new float[]{-2.6F, 0.6F, 0.5F, -2.6F, -0.6F, -0.5F, -0.2F, 0, 0, 0}, new float[]{-0.6F, -0.9F, -0.4F, -0.6F, 0.9F, 0.4F, 0.4F, 0, 0.2F, 1F});
        pose("LUNGE", new float[]{0.5F, 0, 0, -0.6F, 0, 0, -0.2F, 0.4F, 0, 1F}, new float[]{-1.6F, 0, 0, -0.9F, 0, 0, 0.5F, -0.2F, 0, 2F});
        pose("JAVELIN", new float[]{-3.0F, 0, 0.4F, -0.9F, 0, -0.3F, -0.2F, -0.5F, 0, 0}, new float[]{-1.0F, 0, 0, -0.6F, 0, 0, 0.3F, 0.4F, 0, 0});
        pose("RAIN", new float[]{-0.4F, 0, 0, -2.9F, 0, 0.2F, -0.3F, 0, -1.0F, 0}, new float[]{-0.4F, 0, 0, -2.9F, 0, 0.2F, -0.3F, 0, -1.0F, 0});
        pose("TRIPLE", new float[]{-1.5F, 0.6F, 0, -1.6F, 0.3F, 0, 0, 0.6F, 0, 0}, new float[]{-1.5F, 0.2F, 0, -1.6F, 0.3F, 0, 0, 0.6F, 0, 0});
        pose("STANCE", new float[]{-3.0F, 0, 0.6F, -3.0F, 0, -0.6F, -0.3F, 0, -0.6F, 0}, new float[]{-1.2F, 0, 1.2F, -1.2F, 0, -1.2F, 0, 0, 0, 0});
    }

    private static void pose(String id, float[] windup, float[] strike) {
        POSES.put("MOVE_KING_" + id, new float[][]{windup, strike});
    }

    private void add(String part, float x, float y, float z) {
        ModelPart m = p(part);
        if (m != null) {
            m.xRot += x;
            m.yRot += y;
            m.zRot += z;
        }
    }

    private void move(RoyalMob e, float age) {
        TechniqueShow.Active show = TechniqueShow.ACTIVE.get(e.getId());
        if (show == null || !show.mechanic().startsWith("MOVE_KING_")) {
            return;
        }
        float partial = age - (float) ((int) age);
        float u = KingLook.progress(e, show, partial);
        if (u < 0F || u > 1F) {
            return;
        }
        switch (show.mechanic()) {
            case "MOVE_KING_REVIVE_HERO" -> reviveHero(u);
            case "MOVE_KING_REVIVE_GLITCH" -> reviveGlitch(e, u, age);
            case "MOVE_KING_REVIVE_DIVINE" -> reviveDivine(u, age);
            default -> {
                float[][] ps = POSES.get(show.mechanic());
                if (ps == null) {
                    return;
                }
                float len = Math.max(1, show.length());
                float wind = Math.max(1, show.windup()) / len;
                float a = u < wind ? u / wind : 1F;
                float b = u < wind ? 0F : Math.min(1F, (u - wind) / Math.max(0.05F, (1F - wind) * 0.3F));
                float out = u > 0.75F ? 1F - (u - 0.75F) / 0.25F : 1F;
                a = a * a * (3F - 2F * a) * out;
                b = b * b * (3F - 2F * b) * out;
                float[] w = ps[0], s = ps[1];
                float[] v = new float[10];
                for (int i = 0; i < 10; i++) {
                    v[i] = Mth.lerp(b, w[i] * a, s[i]) * (u < wind ? 1F : out);
                }
                add("arm_r", v[0], v[1], v[2]);
                add("arm_l", v[3], v[4], v[5]);
                add("torso", v[6], v[7], 0);
                add("head", v[8], 0, 0);
                ModelPart root = p("root");
                if (root != null) {
                    root.y += v[9];
                }
            }
        }
    }

    private static float smooth(float t) {
        t = Mth.clamp(t, 0F, 1F);
        return t * t * (3F - 2F * t);
    }

    /** Kneeling with the sword planted and the head bowed; rising as the light comes down; the sword raised high. */
    private void reviveHero(float u) {
        float kneel = u < 0.4F ? 1F : 1F - smooth((u - 0.4F) / 0.2F);
        float raise = u < 0.6F ? 0F : u < 0.85F ? smooth((u - 0.6F) / 0.12F) : 1F - smooth((u - 0.85F) / 0.15F) * 0.6F;
        ModelPart root = p("root");
        if (root != null) {
            root.y += 7F * kneel;
        }
        add("leg_r", -1.5F * kneel, 0, 0);
        add("shin_r", 1.4F * kneel, 0, 0);
        add("leg_l", 0.35F * kneel, 0, 0);
        add("head", 0.6F * kneel - 0.5F * raise, 0, 0);
        add("torso", 0.25F * kneel, 0, 0);
        add("arm_r", -0.9F * kneel - 2.9F * raise, 0, 0.2F * raise);
        add("arm_l", -0.6F * kneel, 0, -0.7F * raise);
    }

    /** Convulsions: arms and head jerked at random, the body twisted, flung wide at the end. */
    private void reviveGlitch(RoyalMob e, float u, float age) {
        int h = KingLook.hash(e.getId(), (int) (age / 2F));
        float k = u < 0.85F ? 1F : 0F;
        add("arm_r", k * (((h >> 3) % 9) - 4) * 0.35F, 0, k * (((h >> 7) % 9) - 4) * 0.3F);
        add("arm_l", k * (((h >> 11) % 9) - 4) * 0.35F, 0, k * (((h >> 15) % 9) - 4) * 0.3F);
        add("head", k * (((h >> 19) % 7) - 3) * 0.3F, k * (((h >> 23) % 9) - 4) * 0.3F, k * (((h >> 27) % 5) - 2) * 0.3F);
        add("torso", k * (((h >> 5) % 5) - 2) * 0.15F, k * (((h >> 9) % 5) - 2) * 0.25F, 0);
        if (u >= 0.85F) {
            float f = smooth((u - 0.85F) / 0.08F);
            add("arm_r", -0.4F * f, 0, 1.6F * f);
            add("arm_l", -0.4F * f, 0, -1.6F * f);
            add("head", -0.7F * f, 0, 0);
        }
    }

    /** Hunched with the arms crossed while the shell falls away; arms opened wide, palms up, rising; raised to heaven;
     * brought down at the world. */
    private void reviveDivine(float u, float age) {
        if (u < 0.25F) {
            float tremble = Mth.sin(age * 2.1F) * 0.05F;
            add("torso", 0.4F, 0, 0);
            add("head", 0.6F + tremble, 0, 0);
            add("arm_r", -1.4F, -0.6F, -0.3F + tremble);
            add("arm_l", -1.4F, 0.6F, 0.3F - tremble);
            return;
        }
        float open = smooth((u - 0.25F) / 0.2F) * (u < 0.7F ? 1F : 1F - smooth((u - 0.7F) / 0.1F));
        float sky = u < 0.7F ? 0F : u < 0.85F ? smooth((u - 0.7F) / 0.1F) : 1F - smooth((u - 0.85F) / 0.05F);
        float down = u < 0.85F ? 0F : smooth((u - 0.85F) / 0.05F);
        add("arm_r", -0.3F * open - 3.0F * sky - 1.4F * down, 0, 1.3F * open);
        add("arm_l", -0.3F * open - 3.0F * sky - 1.4F * down, 0, -1.3F * open);
        add("head", -0.4F * open - 0.6F * sky, 0, 0);
        add("torso", -0.1F * open, 0, 0);
    }
}
