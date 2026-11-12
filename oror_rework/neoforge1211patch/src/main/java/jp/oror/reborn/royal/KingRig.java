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
    private final List<ModelPart> crumble = new ArrayList<>();
    private final Map<Integer, ModelPart> weaponR = new HashMap<>(), weaponL = new HashMap<>();
    private int stanceNow;
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
                    (n.endsWith("_l") ? this.weaponL : this.weaponR).put(i, e.getValue());
                }
            }
            if (n.startsWith("crumble")) {
                this.crumble.add(e.getValue());
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
        this.stanceNow = st;
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
        // (059c) one of his form's V20 actions (Casters: king1..king4), its own keyframed motion over the stance
        jp.oror.reborn.waza.client.WazaClient.Play waza = jp.oror.reborn.waza.client.WazaClient.playing(e.getId());
        if (waza != null) {
            float time = e.level().getGameTime() - waza.start() + (age - (float) ((int) age));
            if (time >= 0 && time <= waza.w().length()) {
                jp.oror.reborn.show.WazaPoses.apply(this, waza.w(), time, waza.seed());
            }
        }
        // the ruin
        if (this.broken) {
            float ruin = KingLook.ruin(e);
            float[] at = {0.25F, 0.5F, 0.75F};
            for (int i = 0; i < 3; i++) {
                scale(this.rot[i], Mth.clamp((ruin - at[i]) / 0.08F, 0F, 1F));
            }
            crumble(ruin, age);
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
            pop(e, ruin, age);
        } else {
            for (List<ModelPart> l : this.rot) {
                scale(l, 0F);
            }
        }
        move(e, age);
    }

    // ------------------------------------------------------------------------------------------------- the broken one

    /**
     * (054) The broken king falls apart as his life goes (the user: the broken parts and the king's parts both crumbling
     * more and more): every piece of his shattered armour and of the king he was (crumble_*) has its own moment; past it
     * the piece drops, turning, flickering, and is gone. Under a fifth of his life the monsters grown out of him come
     * apart too, flickering in and out.
     */
    private void crumble(float ruin, float age) {
        for (int i = 0; i < this.crumble.size(); i++) {
            ModelPart m = this.crumble.get(i);
            float th = 0.06F + (KingLook.hash(i * 7919 + 17, 3) & 1023) / 1023F * 0.84F;
            float over = ruin - th;
            if (over <= 0F) {
                continue;
            }
            if (over > 0.1F) {
                m.xScale = m.yScale = m.zScale = 0F;
                continue;
            }
            float f = over / 0.1F;
            m.y += f * f * 16F;
            m.x += ((i % 5) - 2) * f * 1.5F;
            m.xRot += f * 2.6F * ((i & 1) == 0 ? 1 : -1);
            m.zRot += f * 1.8F;
            if ((((int) age) + i) % 3 == 0) {
                m.xScale = m.yScale = m.zScale = 0F;
            }
        }
        if (ruin > 0.8F) {
            int beat = (int) (age / 3F);
            for (List<ModelPart> l : this.rot) {
                for (int i = 0; i < l.size(); i++) {
                    if ((KingLook.hash(i * 31 + l.size(), beat) & 7) < (int) ((ruin - 0.8F) * 25F)) {
                        ModelPart m = l.get(i);
                        m.xScale = m.yScale = m.zScale = 0F;
                    }
                }
            }
        }
    }

    /**
     * (054) A box of tricks (the user): now and then, more often the lower he is, something springs out of him for a
     * moment: a limb blown up to twice its size, his head turned right round, his whole body skipped a block aside or
     * stretched tall, his arms flung up, his body folded the wrong way.
     */
    private void pop(RoyalMob e, float ruin, float age) {
        int bucket = (int) (age / 10F);
        int h = Math.abs(KingLook.hash(e.getId() * 131 + 7, bucket) % 1000003);
        if ((h & 15) > 3 + (int) (ruin * 9F) || (age - bucket * 10F) > 4F) {
            return;
        }
        ModelPart root = p("root");
        switch ((h >> 4) % 6) {
            case 0 -> {
                if (!this.jitter.isEmpty()) {
                    ModelPart m = this.jitter.get((h >> 8) % this.jitter.size());
                    m.xScale *= 2.2F;
                    m.yScale *= 2.2F;
                    m.zScale *= 2.2F;
                }
            }
            case 1 -> add("head", 0, (float) Math.PI, 0);
            case 2 -> {
                if (root != null) {
                    root.x += ((h >> 10) % 2 == 0 ? 1 : -1) * 14F;
                }
            }
            case 3 -> {
                if (root != null) {
                    root.yScale *= 1.6F;
                }
            }
            case 4 -> {
                add("arm_r", -3.0F, 0, 1.2F);
                add("arm_l", -3.0F, 0, -1.2F);
            }
            default -> add("torso", -1.2F, 0, 0.8F);
        }
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
                // (055) the motions of jp.oror.reborn.king.KingMotions: one of his own for each of his seventy moves
                // and for every deed that had none
                jp.oror.reborn.king.KingMotions.Motion mo =
                    jp.oror.reborn.king.KingMotions.get(show.mechanic().substring(10).toLowerCase(java.util.Locale.ROOT));
                if (mo != null) {
                    float[] hold = !this.arms[this.stanceNow].isEmpty() ? HOLD[this.stanceNow] : NO_HOLD;
                    play(motion(mo, u * Math.max(1, show.length()), show.windup(), Math.max(1, show.length()), hold));
                    return;
                }
                float[][] ps = POSES.get(show.mechanic());
                if (ps == null) {
                    // the arsenal's seventy motions and the later deeds (jp.oror.reborn.king.KingArsenal)
                    ps = jp.oror.reborn.king.KingArsenal.poseFor(show.mechanic());
                }
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
                float[] v = new float[14];
                for (int i = 0; i < Math.min(14, w.length); i++) {
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
                // the forearms, and the weapons turned in the fists (a thrust levels the blade, a twirl spins the spear)
                add("fore_r", v[10], 0, 0);
                add("fore_l", v[11], 0, 0);
                ModelPart wr = this.weaponR.get(this.stanceNow), wl = this.weaponL.get(this.stanceNow);
                if (wr == null && wl == null) {
                    wr = p("sword");
                    wl = p("shield");
                }
                if (wr != null) {
                    wr.xRot += v[12];
                }
                if (wl != null) {
                    wl.xRot += v[13];
                }
            }
        }
    }

    private static final float[] NO_HOLD = {0F, 0F, 0F, 0F};
    /** KingMotions' slots that may hold whole turns (hips, torso and head turns, the weapons twirled in the fists). */
    private static final int[] TURNS = {18, 7, 12, 13, 20};

    /**
     * (055) A motion at tick t of its length: from rest into the windup key (reached a moment before the first blow
     * lands, at the windup tick, as the server lands it), then a swing into each strike key just as each blow lands
     * (the strikes alternating with the second key if there is one, a pull back towards the windup between them when
     * there is none or the motion asks it), a hold, and back to rest by the end (any whole turns dropped first, so a
     * spin never unwinds). The arms' and forearms' x in the keys are absolute: the stance's hold comes off them here.
     */
    static float[] motion(jp.oror.reborn.king.KingMotions.Motion mo, float t, int windup, int length, float[] hold) {
        int n = jp.oror.reborn.king.KingMotions.SLOTS;
        float[] rest = new float[n];
        float[] w = offHold(mo.windup(), hold), s = offHold(mo.strike(), hold);
        float[] a = mo.alt() == null ? null : offHold(mo.alt(), hold);
        int beats = Math.max(1, mo.beats());
        float step = Math.max(1, mo.step());
        float room = length - windup - 4F;
        if (beats > 1 && (beats - 1) * step > room) {
            step = Math.max(2F, room / (beats - 1));
        }
        float sw = Mth.clamp(windup / 3F, 2F, 4F);
        List<Float> ts = new ArrayList<>();
        List<float[]> ks = new ArrayList<>();
        ts.add(0F);
        ks.add(rest);
        ts.add(Math.max(1F, windup - sw));
        ks.add(w);
        float[] prev = w;
        float last = windup;
        for (int k = 0; k < beats; k++) {
            float hit = windup + k * step;
            float[] key = a != null && (k & 1) == 1 ? a : s;
            float swing = k == 0 ? sw : Math.min(sw, step * 0.6F);
            if (k > 0 && (a == null || mo.recoil()) && step >= 4F) {
                float[] r = lerp(prev, w, 0.6F);
                ts.add(hit - step + Math.min(step * 0.35F, 2F));
                ks.add(prev);
                ts.add(hit - swing);
                ks.add(r);
                prev = r;
            } else if (hit - swing > ts.get(ts.size() - 1)) {
                ts.add(hit - swing);
                ks.add(prev);
            }
            ts.add(hit);
            ks.add(key);
            prev = key;
            last = hit;
        }
        float holdEnd = Math.min(length - 1F, last + Math.max(2F, (length - last) * 0.35F));
        if (holdEnd > last) {
            ts.add(holdEnd);
            ks.add(prev);
        }
        float[] wrapped = prev.clone();
        for (int i : TURNS) {
            wrapped[i] = Mth.wrapDegrees(wrapped[i] * Mth.RAD_TO_DEG) * Mth.DEG_TO_RAD;
        }
        ts.add(Math.max(holdEnd, last));
        ks.add(wrapped);
        ts.add((float) Math.max(length, last + 2));
        ks.add(rest);
        if (t <= 0F) {
            return rest;
        }
        for (int i = 0; i + 1 < ts.size(); i++) {
            float t0 = ts.get(i), t1 = ts.get(i + 1);
            if (t >= t0 && t < t1 && t1 > t0) {
                return lerp(ks.get(i), ks.get(i + 1), smooth((t - t0) / (t1 - t0)));
            }
        }
        return rest;
    }

    private static float[] offHold(float[] v, float[] hold) {
        float[] o = v.clone();
        o[0] -= hold[0];
        o[10] -= hold[1];
        o[3] -= hold[2];
        o[11] -= hold[3];
        return o;
    }

    private static float[] lerp(float[] p, float[] q, float f) {
        float[] o = new float[p.length];
        for (int i = 0; i < p.length; i++) {
            o[i] = p[i] + (q[i] - p[i]) * f;
        }
        return o;
    }

    /** A motion's values onto his parts (KingMotions' slots). */
    private void play(float[] v) {
        add("arm_r", v[0], v[1], v[2]);
        add("arm_l", v[3], v[4], v[5]);
        add("torso", v[6], v[7], v[19]);
        add("head", v[8], v[20], v[21]);
        ModelPart root = p("root");
        if (root != null) {
            root.y += v[9];
        }
        add("fore_r", v[10], 0, 0);
        add("fore_l", v[11], 0, 0);
        ModelPart wr = this.weaponR.get(this.stanceNow), wl = this.weaponL.get(this.stanceNow);
        if (this.arms[this.stanceNow].isEmpty()) {
            wr = p("sword");
            wl = p("shield");
        }
        if (wr != null) {
            wr.xRot += v[12];
        }
        if (wl != null) {
            wl.xRot += v[13];
        }
        add("leg_r", v[14], 0, 0);
        add("leg_l", v[15], 0, 0);
        add("shin_r", v[16], 0, 0);
        add("shin_l", v[17], 0, 0);
        add("hips", 0, v[18], 0);
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
