package jp.oror.reborn.client;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.AxeItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.TridentItem;
import org.joml.Matrix3f;
import org.joml.Matrix4f;
import org.joml.Quaternionf;
import org.joml.Vector3f;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (r64, the user: "ナイトフォールクラフトの動きとパリイ ... このバージョンに合うように作り直して あと村人王や衛兵や村人もそれらのモーションを行えるように")
 * Epic Fight's own animations (1.21.1: Epic Fight, EpicFight Nightfall, Epic Fight Extra) played on OROR's own models, the
 * kingdom's people and the armed villagers, who have no Epic Fight body (an Epic Fight body draws its own mesh, and the
 * royals' capes, crowns and pauldrons and the villagers' robes broke under it: r62).
 * <p>
 * An animation is read from its file (assets/&lt;ns&gt;/animmodels/animations/&lt;path&gt;.json: per joint, its times and its
 * local 4x4, row by row), its joints posed by their parents (the biped's tree and resting pose from
 * epicfight:animmodels/entity/biped.json), and each joint's move from its resting pose (Epic Fight's space: x to the right,
 * y forward, z up, in blocks from the feet) carried into the model's (pixels, x to the left, y down from the neck, z back):
 * the head by the Head joint, the body by the Chest, the arms by their hands' turn about their shoulders, the legs by the
 * thighs. The step forward an attack takes (its Root's) is left out: the mob moves itself.
 * <p>
 * Which animation: a swing starts the next of its weapon's combo, which ends in its skill (a dash, Flash Block, Rushing
 * Tempo, Grasping Spire, as the pack's own mobs use them); OROR's dodge Epic Fight Nightfall's step to that side (Nightfall's sword, Epic Fight's axe, longsword, tachi,
 * Epic Fight Extra's greatsword, spear, dagger, fists), OROR's guard moments (TechniqueShow) Epic Fight's guard, parry,
 * guarded blow, broken guard and parried stagger, a blow taken its short stagger. Blended in and out over a tenth of a
 * second; an animation a pack does not have is skipped and the model keeps its own pose.
 */
public final class EfMotion {
    private static final Logger LOG = LoggerFactory.getLogger("OROR EF Motion");
    private static final String[] TREE = {"Root", null, "Thigh_R", "Root", "Leg_R", "Thigh_R", "Thigh_L", "Root", "Leg_L", "Thigh_L",
        "Torso", "Root", "Chest", "Torso", "Head", "Chest", "Shoulder_R", "Chest", "Arm_R", "Shoulder_R", "Hand_R", "Arm_R",
        "Shoulder_L", "Chest", "Arm_L", "Shoulder_L", "Hand_L", "Arm_L", "Tool_R", "Hand_R", "Tool_L", "Hand_L"};
    private static final Map<String, String> PARENT = new HashMap<>();
    static {
        for (int i = 0; i < TREE.length; i += 2) {
            PARENT.put(TREE[i], TREE[i + 1]);
        }
    }

    /**
     * (r65, the user: "現物と見比べると若干の違和感が多い") Epic Fight's own reading of an animation, not this class's: read from the
     * files directly, the joints came out turned otherwise than Epic Fight turns them (the player's own body, set beside
     * them, showed it: the chest's twist and the thigh's lift the other way about). The pose is Epic Fight's
     * (StaticAnimation.getRawPose), the joints' places Epic Fight's armature's (the biped's, getBoundTransformFor), and the
     * axes of its space found from its own resting pose (the head is up, the right arm to the right).
     */
    record Clip(ResourceLocation id, float length) {
    }

    private static final Map<ResourceLocation, Optional<Clip>> CLIPS = new ConcurrentHashMap<>();
    private static Map<String, Matrix4f> bindWorld;
    private static boolean bindTried;
    private static yesman.epicfight.model.armature.HumanoidArmature armature;
    private static final java.util.Set<ResourceLocation> TOLD = ConcurrentHashMap.newKeySet();

    private static yesman.epicfight.api.animation.types.StaticAnimation anim(ResourceLocation id) {
        try {
            yesman.epicfight.api.animation.AnimationManager.AnimationAccessor<yesman.epicfight.api.animation.types.StaticAnimation> acc =
                yesman.epicfight.api.animation.AnimationManager.byKey(id);
            return acc == null ? null : acc.get();
        } catch (Throwable t) {
            return null;
        }
    }

    static Clip clip(ResourceLocation id) {
        Optional<Clip> have = CLIPS.get(id);
        if (have != null) {
            return have.orElse(null);
        }
        yesman.epicfight.api.animation.types.StaticAnimation a = anim(id);
        if (a == null) {
            if (TOLD.add(id)) {
                LOG.info("EF-MOTION {\"missing\":\"{}\"}", id);
            }
            return null;
        }
        Clip c = new Clip(id, a.getTotalTime());
        CLIPS.put(id, Optional.of(c));
        return c;
    }

    private static Matrix4f joml(yesman.epicfight.api.utils.math.OpenMatrix4f o, boolean transpose) {
        Matrix4f m = new Matrix4f(o.m00, o.m01, o.m02, o.m03, o.m10, o.m11, o.m12, o.m13, o.m20, o.m21, o.m22, o.m23, o.m30, o.m31, o.m32, o.m33);
        return transpose ? m.transpose() : m;
    }

    private static boolean transposed;
    // the axes of Epic Fight's space, found from its resting pose
    private static Vector3f up = new Vector3f(0, 0, 1), right = new Vector3f(1, 0, 0), forward = new Vector3f(0, 1, 0);
    private static Matrix3f A = new Matrix3f(-1, 0, 0, 0, 0, -1, 0, -1, 0);

    private static Vector3f axisOf(Vector3f v, Vector3f not) {
        float[] c = {Math.abs(v.x), Math.abs(v.y), Math.abs(v.z)};
        if (not != null) {
            if (Math.abs(not.x) > 0.5F) c[0] = -1;
            if (Math.abs(not.y) > 0.5F) c[1] = -1;
            if (Math.abs(not.z) > 0.5F) c[2] = -1;
        }
        int i = c[0] >= c[1] && c[0] >= c[2] ? 0 : c[1] >= c[2] ? 1 : 2;
        float s = Math.signum(i == 0 ? v.x : i == 1 ? v.y : v.z);
        return new Vector3f(i == 0 ? s : 0, i == 1 ? s : 0, i == 2 ? s : 0);
    }

    /** The biped's resting pose, joint by joint, in Epic Fight's space; and that space's axes. */
    private static Map<String, Matrix4f> bind() {
        if (bindTried) {
            return bindWorld;
        }
        bindTried = true;
        try {
            armature = yesman.epicfight.gameasset.Armatures.BIPED.get();
            yesman.epicfight.api.animation.Pose empty = new yesman.epicfight.api.animation.Pose();
            yesman.epicfight.api.animation.Joint head = armature.searchJointByName("Head");
            yesman.epicfight.api.utils.math.OpenMatrix4f h = armature.getBoundTransformFor(empty, head);
            Vector3f ht = joml(h, false).getTranslation(new Vector3f());
            if (ht.length() < 0.3F && new Vector3f(h.m03, h.m13, h.m23).length() > 0.3F) {
                transposed = true;
            }
            Map<String, Matrix4f> w = new HashMap<>();
            for (String j : PARENT.keySet()) {
                yesman.epicfight.api.animation.Joint jt = armature.searchJointByName(j);
                if (jt != null) {
                    w.put(j, joml(armature.getBoundTransformFor(empty, jt), transposed));
                }
            }
            Vector3f headAt = w.get("Head").getTranslation(new Vector3f());
            Vector3f armAt = w.get("Arm_R").getTranslation(new Vector3f());
            up = axisOf(headAt, null);
            right = axisOf(armAt, up);
            forward = new Vector3f(up).cross(right);
            A = new Matrix3f().setRow(0, new Vector3f(right).negate()).setRow(1, new Vector3f(up).negate()).setRow(2, new Vector3f(forward).negate());
            bindWorld = w;
            LOG.info("EF-MOTION {\"bind\":{},\"transposed\":{},\"up\":\"{}\",\"right\":\"{}\",\"forward\":\"{}\",\"head\":\"{}\",\"armR\":\"{}\"}",
                w.size(), transposed, up, right, forward, headAt, armAt);
        } catch (Throwable t) {
            LOG.info("EF-MOTION {\"bind\":\"{}\"}", String.valueOf(t).replace('"', '\''));
            bindWorld = null;
        }
        return bindWorld;
    }

    /** Each joint's move from rest at time t, in Epic Fight's space (the step forward taken out). */
    static Map<String, Matrix4f> moves(Clip c, float t) {
        Map<String, Matrix4f> rest = bind();
        yesman.epicfight.api.animation.types.StaticAnimation a = anim(c.id());
        if (rest == null || a == null || armature == null) {
            return null;
        }
        yesman.epicfight.api.animation.Pose pose;
        try {
            pose = a.getRawPose(t);
        } catch (Throwable ex) {
            return null;
        }
        Map<String, Matrix4f> now = new HashMap<>();
        for (String j : rest.keySet()) {
            yesman.epicfight.api.animation.Joint jt = armature.searchJointByName(j);
            if (jt != null) {
                now.put(j, joml(armature.getBoundTransformFor(pose, jt), transposed));
            }
        }
        Vector3f root = now.containsKey("Root") ? now.get("Root").getTranslation(new Vector3f()) : new Vector3f();
        Vector3f root0 = rest.containsKey("Root") ? rest.get("Root").getTranslation(new Vector3f()) : new Vector3f();
        Vector3f step = new Vector3f(root).sub(root0);
        // the step forward and aside taken out (kept: up and down)
        Vector3f flat = new Vector3f(right).mul(step.dot(right)).add(new Vector3f(forward).mul(step.dot(forward)));
        Matrix4f unstep = new Matrix4f().translation(-flat.x, -flat.y, -flat.z);
        Map<String, Matrix4f> out = new HashMap<>();
        for (Map.Entry<String, Matrix4f> en : now.entrySet()) {
            Matrix4f b = rest.get(en.getKey());
            if (b != null) {
                out.put(en.getKey(), new Matrix4f(unstep).mul(en.getValue()).mul(new Matrix4f(b).invert()));
            }
        }
        return out;
    }

    /** (look 'motion') Epic Fight's own pose of an animation at time t, joint by joint (local translation and turn). */
    static String rawPose(ResourceLocation id, float t, String... joints) {
        yesman.epicfight.api.animation.types.StaticAnimation a = anim(id);
        if (a == null) {
            return "no animation";
        }
        StringBuilder b = new StringBuilder();
        yesman.epicfight.api.animation.Pose pose = a.getRawPose(t);
        for (String j : joints) {
            yesman.epicfight.api.animation.JointTransform jt = pose.get(j);
            if (jt == null) {
                continue;
            }
            Quaternionf q = jt.rotation();
            b.append(String.format(java.util.Locale.ROOT, "%s t(%.2f,%.2f,%.2f) q(%.2f,%.2f,%.2f,%.2f) ", j, jt.translation().x, jt.translation().y,
                jt.translation().z, q.x, q.y, q.z, q.w));
        }
        return b.toString();
    }

    static final float AMP = 0.75F;

    /** Between two joints' moves (the body hinged between its waist and its chest, so its hips stay on its legs). */
    public static Matrix4f mix(Matrix4f a, Matrix4f b, float u) {
        if (a == null || b == null) {
            return a == null ? b : a;
        }
        Quaternionf qa = a.getNormalizedRotation(new Quaternionf()), qb = b.getNormalizedRotation(new Quaternionf());
        Vector3f ta = a.getTranslation(new Vector3f()), tb = b.getTranslation(new Vector3f());
        return new Matrix4f().translationRotate(ta.lerp(tb, u), qa.slerp(qb, u));
    }

    // Epic Fight's space to the model's (pixels; x to the model's left, y down from the neck, z back): A's rows are -right,
    // -up and -forward
    private static Vector3f toEf(float x, float y, float z) {
        return new Vector3f(right).mul(-x / 16F).add(new Vector3f(up).mul((24F - y) / 16F)).add(new Vector3f(forward).mul(-z / 16F));
    }

    private static Vector3f toModel(Vector3f e) {
        return new Vector3f(-e.dot(right) * 16F, 24F - e.dot(up) * 16F, -e.dot(forward) * 16F);
    }

    /** Poses one part by a joint's move, blended over its own pose by w; the rotation from 'turn' (a joint) if given. */
    public static void pose(ModelPart part, Matrix4f move, Matrix4f turn, float w) {
        if (part == null || move == null || w <= 0) {
            return;
        }
        poseRot(part, move, (turn == null ? move : turn).getNormalizedRotation(new Quaternionf()), w);
    }

    /** Poses one part: its pivot carried by 'move', turned by 'rot' (Epic Fight's space), blended over its own pose by w. */
    static void poseRot(ModelPart part, Matrix4f move, Quaternionf rot, float w) {
        if (part == null || move == null || rot == null || w <= 0) {
            return;
        }
        Vector3f pivot = toEf(part.x, part.y, part.z);
        Vector3f moved = move.transformPosition(pivot, new Vector3f());
        // (r65, look run) Epic Fight's swings turn the body 70 to 90 degrees and lift a leg level, which its bending mesh
        // carries and a block model (no waist, no knees) does not: three quarters of every turn and shift
        moved = new Vector3f(pivot).lerp(moved, AMP);
        Vector3f at = toModel(moved);
        Matrix3f r = new Matrix3f().rotation(rot);
        // the turn in the model's axes: A r A^T (A is its own inverse's transpose)
        Matrix3f rm = new Matrix3f(A).mul(r).mul(new Matrix3f(A).transpose());
        Quaternionf q = new Quaternionf().slerp(new Quaternionf().setFromNormalized(rm), AMP);
        Vector3f eul = q.getEulerAnglesZYX(new Vector3f());
        part.x = Mth.lerp(w, part.x, at.x);
        part.y = Mth.lerp(w, part.y, at.y);
        part.z = Mth.lerp(w, part.z, at.z);
        part.xRot = Mth.lerp(w, part.xRot, eul.x);
        part.yRot = Mth.lerp(w, part.yRot, eul.y);
        part.zRot = Mth.lerp(w, part.zRot, eul.z);
    }

    /**
     * (r65, the user: "パリイのモーション壊れてない？ 腕とか おかしいよ") An arm of a block model is one straight block from shoulder to
     * hand; Epic Fight's bends at the elbow and turns at the wrist, and the block set by the forearm alone (a parry's sharp
     * bend and turn) pointed wherever the forearm did. It is aimed from the shoulder to the wrist instead (so the hand, and
     * what it holds, is where Epic Fight puts it), with only the forearm's own twist about that line.
     */
    public static void arm(ModelPart part, Pose p, String arm, String hand, String tool, float w) {
        Quaternionf q = armTurn(p, arm, hand, tool);
        if (q == null) {
            pose(part, p.get(arm), p.get(hand), w);
            return;
        }
        poseRot(part, p.get(arm), q, w);
    }

    /** The arm's turn (Epic Fight's space): aimed from shoulder to wrist, with the forearm's own twist; null if unknown. */
    static Quaternionf armTurn(Pose p, String arm, String hand, String tool) {
        Map<String, Matrix4f> rest = bind();
        Matrix4f ma = p.get(arm), mh = p.get(hand), mt = p.get(tool);
        if (rest == null || ma == null || mh == null || mt == null || !rest.containsKey(arm) || !rest.containsKey(tool)) {
            return mh == null ? null : mh.getNormalizedRotation(new Quaternionf());
        }
        Vector3f shoulder0 = rest.get(arm).getTranslation(new Vector3f()), wrist0 = rest.get(tool).getTranslation(new Vector3f());
        Vector3f shoulder = ma.transformPosition(new Vector3f(shoulder0)), wrist = mt.transformPosition(new Vector3f(wrist0));
        Vector3f d0 = new Vector3f(wrist0).sub(shoulder0), d = new Vector3f(wrist).sub(shoulder);
        if (d0.lengthSquared() < 1e-6F || d.lengthSquared() < 1e-6F) {
            return mh.getNormalizedRotation(new Quaternionf());
        }
        d0.normalize();
        d.normalize();
        Quaternionf aim = new Quaternionf().rotationTo(d0, d);
        // the forearm's twist about the arm's own line (swing and twist apart)
        Quaternionf rest2 = new Quaternionf(aim).conjugate().mul(mh.getNormalizedRotation(new Quaternionf()));
        Vector3f v = new Vector3f(rest2.x, rest2.y, rest2.z);
        float along = v.dot(d0);
        Quaternionf twist = new Quaternionf(d0.x * along, d0.y * along, d0.z * along, rest2.w);
        if (twist.lengthSquared() < 1e-8F) {
            twist.identity();
        } else {
            twist.normalize();
        }
        return new Quaternionf(aim).mul(twist);
    }

    /** A turn of Epic Fight's space as a turn of the model's, three quarters of it. */
    private static Quaternionf modelTurn(Quaternionf ef) {
        Matrix3f r = new Matrix3f().rotation(ef);
        Matrix3f rm = new Matrix3f(A).mul(r).mul(new Matrix3f(A).transpose());
        return new Quaternionf().slerp(new Quaternionf().setFromNormalized(rm), AMP);
    }

    private static Quaternionf turnOf(ModelPart part) {
        return new Quaternionf().rotationZYX(part.zRot, part.yRot, part.xRot);
    }

    private static void setTurn(ModelPart part, Quaternionf q) {
        Vector3f eul = q.getEulerAnglesZYX(new Vector3f());
        part.xRot = eul.x;
        part.yRot = eul.y;
        part.zRot = eul.z;
    }

    /**
     * (r65, the user: "腕が体から離れてるんすけど") The whole body at once, joined: each part placed by its own joint drifted from
     * the others (the body alone was blended between waist and chest and brought to three quarters, so the shoulders the
     * arms followed were not the body's), and the arms stood off from it. Now the legs go first; the body sets its hips
     * on theirs and turns about them; the head sits on the body's neck and the arms on its shoulders, each turning there
     * by its own joint. Nothing parts from anything.
     */
    public static void biped(Pose p, ModelPart head, ModelPart body, ModelPart rightArm, ModelPart leftArm, ModelPart rightLeg,
                             ModelPart leftLeg, float w) {
        if (p == null || body == null || w <= 0) {
            return;
        }
        Vector3f bodyRest = new Vector3f(body.x, body.y, body.z);
        Vector3f headRest = head == null ? null : new Vector3f(head.x, head.y, head.z);
        Vector3f rArmRest = rightArm == null ? null : new Vector3f(rightArm.x, rightArm.y, rightArm.z);
        Vector3f lArmRest = leftArm == null ? null : new Vector3f(leftArm.x, leftArm.y, leftArm.z);
        Vector3f rLegRest = new Vector3f(rightLeg.x, rightLeg.y, rightLeg.z), lLegRest = new Vector3f(leftLeg.x, leftLeg.y, leftLeg.z);
        // the legs
        pose(rightLeg, p.get("Thigh_R"), null, w);
        pose(leftLeg, p.get("Thigh_L"), null, w);
        Vector3f hipRest = new Vector3f(rLegRest).add(lLegRest).mul(0.5F);
        Vector3f hip = new Vector3f(rightLeg.x, rightLeg.y, rightLeg.z).add(leftLeg.x, leftLeg.y, leftLeg.z).mul(0.5F);
        // the body: turned about its hips, which sit on the legs'
        Matrix4f bm = mix(p.get("Torso"), p.get("Chest"), 0.5F);
        Quaternionf qb = turnOf(body);
        if (bm != null) {
            qb.slerp(modelTurn(bm.getNormalizedRotation(new Quaternionf())), w);
        }
        Vector3f neck = qb.transform(new Vector3f(bodyRest).sub(hipRest)).add(hip);
        body.x = neck.x;
        body.y = neck.y;
        body.z = neck.z;
        setTurn(body, qb);
        // the head on the neck
        if (head != null) {
            Vector3f at = qb.transform(new Vector3f(headRest).sub(bodyRest)).add(neck);
            head.x = at.x;
            head.y = at.y;
            head.z = at.z;
            Matrix4f hm = p.get("Head");
            if (hm != null) {
                setTurn(head, turnOf(head).slerp(modelTurn(hm.getNormalizedRotation(new Quaternionf())), w));
            }
        }
        // the arms on the shoulders
        Object[][] arms = {{rightArm, rArmRest, "Arm_R", "Hand_R", "Tool_R"}, {leftArm, lArmRest, "Arm_L", "Hand_L", "Tool_L"}};
        for (Object[] a : arms) {
            ModelPart part = (ModelPart) a[0];
            if (part == null) {
                continue;
            }
            Vector3f at = qb.transform(new Vector3f((Vector3f) a[1]).sub(bodyRest)).add(neck);
            part.x = at.x;
            part.y = at.y;
            part.z = at.z;
            Quaternionf q = armTurn(p, (String) a[2], (String) a[3], (String) a[4]);
            if (q != null) {
                setTurn(part, turnOf(part).slerp(modelTurn(q), w));
            }
        }
    }

    // ---- which animation, per mob ----
    record Active(ResourceLocation id, float start, float speed, boolean hold) {
    }

    static final Map<Integer, Active> ACTIVE = new ConcurrentHashMap<>();
    private static final Map<Integer, int[]> SEEN = new ConcurrentHashMap<>();

    static String kind(ItemStack s) {
        if (s.isEmpty()) {
            return "fist";
        }
        String id = net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(s.getItem()).getPath();
        if (id.contains("greatsword") || id.contains("claymore") || id.contains("colossal")) {
            return "greatsword";
        }
        if (id.contains("tachi") || id.contains("katana") || id.contains("uchigatana")) {
            return "tachi";
        }
        if (id.contains("longsword") || id.contains("long_sword")) {
            return "longsword";
        }
        if (id.contains("dagger") || id.contains("knife")) {
            return "dagger";
        }
        if (id.contains("spear") || id.contains("halberd") || id.contains("glaive") || s.getItem() instanceof TridentItem) {
            return "spear";
        }
        if (s.getItem() instanceof AxeItem || id.contains("axe")) {
            return "axe";
        }
        if (s.getItem() instanceof SwordItem || id.contains("sword") || id.contains("blade") || id.contains("saber")) {
            return "sword";
        }
        return null;
    }

    private static final Map<String, String[]> COMBOS = Map.of(
        "sword", new String[]{"efn:biped/nf_sword/nf_sword_auto1", "efn:biped/nf_sword/nf_sword_auto2", "efn:biped/nf_sword/nf_sword_auto3",
            "efn:biped/nf_sword/nf_sword_auto4", "efn:biped/nf_sword/nf_sword_dash", "efn:biped/nf_skill/biped_flashblock1"},
        "axe", new String[]{"epicfight:biped/combat/axe_auto1", "epicfight:biped/combat/axe_auto2"},
        "longsword", new String[]{"epicfight:biped/combat/longsword_auto1", "epicfight:biped/combat/longsword_auto2", "epicfight:biped/combat/longsword_auto3"},
        "tachi", new String[]{"epicfight:biped/combat/tachi_auto1", "epicfight:biped/combat/tachi_auto2", "epicfight:biped/combat/tachi_auto3",
            "epicfightx:biped/combat/tachi_dash", "epicfightx:biped/skill/rushing_tempo1"},
        "greatsword", new String[]{"epicfightx:biped/combat/greatsword_auto1", "epicfightx:biped/combat/greatsword_auto2", "epicfightx:biped/combat/greatsword_dash",
            "efn:biped/ng_greatsword/ng_great_dash"},
        "spear", new String[]{"epicfightx:biped/combat/spear_twohand_auto1", "epicfightx:biped/combat/spear_twohand_auto2", "epicfightx:biped/skill/grasping_spire_second"},
        "dagger", new String[]{"epicfightx:biped/combat/dagger_auto1", "epicfightx:biped/combat/dagger_auto2", "epicfightx:biped/combat/dagger_auto3",
            "epicfightx:biped/combat/dagger_dash"},
        "fist", new String[]{"epicfightx:biped/combat/fist_auto1", "epicfightx:biped/combat/fist_auto2", "epicfight:biped/combat/fist_auto1"});

    private static ResourceLocation pick(String[] ids, int index) {
        List<ResourceLocation> have = new ArrayList<>();
        for (String s : ids) {
            ResourceLocation r = ResourceLocation.tryParse(s);
            if (r != null && clip(r) != null) {
                have.add(r);
            }
        }
        return have.isEmpty() ? null : have.get(Math.floorMod(index, have.size()));
    }

    private static ResourceLocation first(String... ids) {
        return pick(ids, 0);
    }

    /**
     * (r65, look 'motion') What this reads of an animation at time t, joint by joint (its local translation and its local
     * turn as a quaternion), for comparing with Epic Fight's own pose of the same moment.
     */
    public static String debugLocals(String id, float t, String... joints) {
        ResourceLocation r = ResourceLocation.tryParse(id);
        return r == null ? "no id" : rawPose(r, t, joints);
    }

    /** The mob's animation and its time now (seconds), or null. */
    public static String nowAt(LivingEntity e, float partial) {
        Active a = ACTIVE.get(e.getId());
        return a == null ? null : a.id() + "@" + String.format(java.util.Locale.ROOT, "%.3f", (e.tickCount + partial - a.start()) / 20F * a.speed());
    }

    /** (r65) Starts an animation on a mob outright (the look check's side by side with Epic Fight's own); whether it could. */
    public static boolean start(LivingEntity e, String id) {
        ResourceLocation r = ResourceLocation.tryParse(id);
        if (r == null || clip(r) == null) {
            return false;
        }
        ACTIVE.put(e.getId(), new Active(r, e.tickCount, 1F, false));
        return true;
    }

    /** What the mob does now, decided from what the client sees of it; then its pose. Returns false if nothing plays. */
    public static boolean update(LivingEntity mob, float age) {
        int id = mob.getId();
        int[] seen = SEEN.computeIfAbsent(id, k -> new int[]{0, 0, -1000});
        float now = age;
        // OROR's guard moments first
        jp.oror.reborn.show.TechniqueShow.Active show = jp.oror.reborn.show.TechniqueShow.REACT.get(id);
        ResourceLocation want = null;
        boolean hold = false;
        float startAt = now;
        if (show != null) {
            float into = mob.level().getGameTime() - show.start();
            String k0 = kind(mob.getMainHandItem());
            boolean armedEf = k0 != null && !"fist".equals(k0);
            boolean dodge = show.mechanic().startsWith("DODGE");
            if (into >= 0 && into <= show.length() && (armedEf || dodge || "PARRIED".equals(show.mechanic()) || "BROKEN".equals(show.mechanic()))) {
                String k = k0;
                boolean big = "greatsword".equals(k) || "spear".equals(k) || "longsword".equals(k) || "tachi".equals(k);
                switch (show.mechanic()) {
                    case "GUARD" -> {
                        want = big ? first("epicfight:biped/skill/guard_longsword", "epicfight:biped/skill/guard_sword") : first("epicfight:biped/skill/guard_sword");
                        hold = true;
                    }
                    case "PARRY" -> want = pick(new String[]{big ? "epicfight:biped/skill/guard_longsword_hit_active1" : "epicfight:biped/skill/guard_sword_hit_active1",
                        big ? "epicfight:biped/skill/guard_longsword_hit_active2" : "epicfight:biped/skill/guard_sword_hit_active2"}, (int) (show.start() & 1));
                    case "BLOCK" -> want = first(big ? "epicfight:biped/skill/guard_longsword_hit" : "epicfight:biped/skill/guard_sword_hit", "epicfight:biped/skill/guard_sword_hit");
                    case "BROKEN" -> want = first("epicfightx:biped/skill/guard_break1", "epicfight:biped/skill/guard_break", "epicfight:biped/combat/hit_long");
                    case "PARRIED" -> want = first("epicfight:biped/combat/hit_long", "epicfight:biped/combat/hit_short");
                    // (r65) OROR's dodge: Epic Fight Nightfall's step to that side
                    case "DODGE_L" -> want = first("efn:biped/dodge/step_l", "epicfight:biped/skill/step_left");
                    case "DODGE_R" -> want = first("efn:biped/dodge/step_r", "epicfight:biped/skill/step_right");
                    default -> {
                    }
                }
                startAt = now - into;
            }
        }
        // a new swing: the next of its weapon's combo
        boolean swinging = mob.swinging;
        if (want == null && swinging && seen[0] == 0) {
            String k = kind(mob.getMainHandItem());
            String[] combo = k == null ? null : COMBOS.get(k);
            if (combo != null) {
                seen[1] = now - seen[2] < 40 ? seen[1] + 1 : 0;
                seen[2] = (int) now;
                want = pick(combo, seen[1]);
            }
        }
        seen[0] = swinging ? 1 : 0;
        if (want == null && mob.hurtTime == mob.hurtDuration - 1 && mob.hurtTime > 0) {
            want = first("epicfight:biped/combat/hit_short");
        }
        Active cur = ACTIVE.get(id);
        if (want != null && (cur == null || !cur.id().equals(want) || !cur.hold())) {
            if (cur == null || !cur.id().equals(want) || startAt - cur.start() > 2) {
                cur = new Active(want, startAt, 1F, hold);
                ACTIVE.put(id, cur);
            }
        }
        if (cur == null) {
            return false;
        }
        Clip c = clip(cur.id());
        if (c == null) {
            ACTIVE.remove(id);
            return false;
        }
        float t = (now - cur.start()) / 20F * cur.speed();
        boolean held = cur.hold() && show != null && "GUARD".equals(show.mechanic());
        if (!held && t > c.length() + 0.1F) {
            ACTIVE.remove(id);
            return false;
        }
        return true;
    }

    /** The blend weight and the joints' moves of the mob's animation now (null when nothing plays). */
    public static Pose now(LivingEntity mob, float age) {
        Active cur = ACTIVE.get(mob.getId());
        if (cur == null) {
            return null;
        }
        Clip c = clip(cur.id());
        if (c == null) {
            return null;
        }
        float t = (age - cur.start()) / 20F * cur.speed();
        float len = Math.max(0.05F, c.length());
        float w = cur.hold() ? Mth.clamp(t / 0.1F, 0F, 1F) : Math.min(Mth.clamp(t / 0.1F, 0F, 1F), Mth.clamp((len + 0.1F - t) / 0.1F, 0F, 1F));
        Map<String, Matrix4f> m = moves(c, cur.hold() ? Math.min(t, len) : Math.min(t, len));
        return m == null ? null : new Pose(m, w * w * (3F - 2F * w), cur.id());
    }

    public record Pose(Map<String, Matrix4f> moves, float weight, ResourceLocation id) {
        public Matrix4f get(String joint) {
            return moves.get(joint);
        }
    }
}
