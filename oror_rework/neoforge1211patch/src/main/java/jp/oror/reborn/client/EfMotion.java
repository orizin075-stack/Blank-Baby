package jp.oror.reborn.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.Reader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.packs.resources.Resource;
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

    /** One joint's keyframes. */
    private record Sheet(float[] time, Vector3f[] pos, Quaternionf[] rot) {
        Matrix4f at(float t, Matrix4f out) {
            int n = time.length;
            if (n == 1 || t <= time[0]) {
                return out.translationRotate(pos[0], rot[0]);
            }
            if (t >= time[n - 1]) {
                return out.translationRotate(pos[n - 1], rot[n - 1]);
            }
            int i = 0;
            while (i + 1 < n && time[i + 1] < t) {
                i++;
            }
            float u = (t - time[i]) / Math.max(1e-4F, time[i + 1] - time[i]);
            Vector3f p = new Vector3f(pos[i]).lerp(pos[i + 1], u);
            Quaternionf q = new Quaternionf(rot[i]).slerp(rot[i + 1], u);
            return out.translationRotate(p, q);
        }
    }

    record Clip(Map<String, Sheet> joints, float length) {
    }

    private static final Map<ResourceLocation, Optional<Clip>> CLIPS = new ConcurrentHashMap<>();
    private static Map<String, Matrix4f> bindWorld;
    private static boolean bindTried;

    private EfMotion() {
    }

    private static JsonElement read(ResourceLocation file) {
        try {
            Optional<Resource> r = Minecraft.getInstance().getResourceManager().getResource(file);
            if (r.isEmpty()) {
                return null;
            }
            try (Reader in = r.get().openAsReader()) {
                return JsonParser.parseReader(in);
            }
        } catch (Exception e) {
            return null;
        }
    }

    private static Matrix4f rowMajor(JsonArray a) {
        float[] f = new float[16];
        for (int i = 0; i < 16; i++) {
            f[i] = a.get(i).getAsFloat();
        }
        // JOML takes its arrays column by column
        return new Matrix4f().set(f).transpose();
    }

    static Clip clip(ResourceLocation id) {
        return CLIPS.computeIfAbsent(id, k -> {
            JsonElement e = read(ResourceLocation.fromNamespaceAndPath(k.getNamespace(), "animmodels/animations/" + k.getPath() + ".json"));
            if (e == null || !e.isJsonObject() || !e.getAsJsonObject().has("animation")) {
                LOG.info("EF-MOTION {\"missing\":\"{}\"}", k);
                return Optional.empty();
            }
            Map<String, Sheet> joints = new HashMap<>();
            float length = 0;
            for (JsonElement je : e.getAsJsonObject().getAsJsonArray("animation")) {
                JsonObject j = je.getAsJsonObject();
                String name = j.get("name").getAsString();
                if (!PARENT.containsKey(name)) {
                    continue;
                }
                JsonArray times = j.getAsJsonArray("time"), mats = j.getAsJsonArray("transform");
                int n = Math.min(times.size(), mats.size());
                float[] t = new float[n];
                Vector3f[] p = new Vector3f[n];
                Quaternionf[] q = new Quaternionf[n];
                for (int i = 0; i < n; i++) {
                    t[i] = times.get(i).getAsFloat();
                    Matrix4f m = rowMajor(mats.get(i).getAsJsonArray());
                    p[i] = m.getTranslation(new Vector3f());
                    q[i] = m.getNormalizedRotation(new Quaternionf());
                    length = Math.max(length, t[i]);
                }
                if (n > 0) {
                    joints.put(name, new Sheet(t, p, q));
                }
            }
            return joints.isEmpty() ? Optional.empty() : Optional.of(new Clip(joints, length));
        }).orElse(null);
    }

    /** The biped's resting pose, joint by joint in Epic Fight's space. */
    private static Map<String, Matrix4f> bind() {
        if (bindTried) {
            return bindWorld;
        }
        bindTried = true;
        JsonElement e = read(ResourceLocation.fromNamespaceAndPath("epicfight", "animmodels/entity/biped.json"));
        if (e == null) {
            LOG.info("EF-MOTION {\"bind\":false}");
            return null;
        }
        Map<String, Matrix4f> local = new HashMap<>();
        try {
            JsonObject arm = e.getAsJsonObject().getAsJsonObject("armature");
            List<JsonObject> todo = new ArrayList<>();
            for (JsonElement r : arm.getAsJsonArray("hierarchy")) {
                todo.add(r.getAsJsonObject());
            }
            while (!todo.isEmpty()) {
                JsonObject node = todo.remove(todo.size() - 1);
                if (node.has("transform")) {
                    local.put(node.get("name").getAsString(), rowMajor(node.getAsJsonArray("transform")));
                }
                if (node.has("children")) {
                    for (JsonElement c : node.getAsJsonArray("children")) {
                        todo.add(c.getAsJsonObject());
                    }
                }
            }
        } catch (RuntimeException ex) {
            LOG.info("EF-MOTION {\"bind\":\"{}\"}", ex.toString().replace('"', '\''));
            return null;
        }
        bindWorld = world(name -> local.get(name));
        LOG.info("EF-MOTION {\"bind\":{}}", bindWorld.size());
        return bindWorld;
    }

    private static Map<String, Matrix4f> world(java.util.function.Function<String, Matrix4f> localOf) {
        Map<String, Matrix4f> w = new HashMap<>();
        for (int i = 0; i < TREE.length; i += 2) {
            String j = TREE[i], p = TREE[i + 1];
            Matrix4f l = localOf.apply(j);
            if (l == null) {
                continue;
            }
            Matrix4f pw = p == null ? null : w.get(p);
            w.put(j, pw == null ? new Matrix4f(l) : new Matrix4f(pw).mul(l));
        }
        return w;
    }

    /** Each joint's move from rest at time t, in Epic Fight's space (the step forward taken out). */
    static Map<String, Matrix4f> moves(Clip c, float t) {
        Map<String, Matrix4f> rest = bind();
        if (rest == null) {
            return null;
        }
        Map<String, Matrix4f> cache = new HashMap<>();
        Map<String, Matrix4f> now = world(name -> {
            Sheet s = c.joints().get(name);
            if (s == null) {
                Matrix4f b = rest.get(name);
                Matrix4f pb = PARENT.get(name) == null ? null : rest.get(PARENT.get(name));
                return b == null ? null : pb == null ? new Matrix4f(b) : new Matrix4f(pb).invert().mul(b);
            }
            return s.at(t, cache.computeIfAbsent(name, k -> new Matrix4f()));
        });
        Vector3f root = now.containsKey("Root") ? now.get("Root").getTranslation(new Vector3f()) : new Vector3f();
        Vector3f root0 = rest.containsKey("Root") ? rest.get("Root").getTranslation(new Vector3f()) : new Vector3f();
        Matrix4f unstep = new Matrix4f().translation(root0.x - root.x, root0.y - root.y, 0);
        Map<String, Matrix4f> out = new HashMap<>();
        for (Map.Entry<String, Matrix4f> en : now.entrySet()) {
            Matrix4f b = rest.get(en.getKey());
            if (b != null) {
                out.put(en.getKey(), new Matrix4f(unstep).mul(en.getValue()).mul(new Matrix4f(b).invert()));
            }
        }
        return out;
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

    // Epic Fight's space to the model's: x_m = -16 x, y_m = 24 - 16 z, z_m = -16 y
    private static final Matrix3f A = new Matrix3f(-1, 0, 0, 0, 0, -1, 0, -1, 0);

    private static Vector3f toEf(float x, float y, float z) {
        return new Vector3f(-x / 16F, -z / 16F, (24F - y) / 16F);
    }

    private static Vector3f toModel(Vector3f e) {
        return new Vector3f(-e.x * 16F, 24F - e.z * 16F, -e.y * 16F);
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
        Map<String, Matrix4f> rest = bind();
        Matrix4f ma = p.get(arm), mh = p.get(hand), mt = p.get(tool);
        if (part == null || rest == null || ma == null || mh == null || mt == null || !rest.containsKey(arm) || !rest.containsKey(tool)) {
            pose(part, ma, mh, w);
            return;
        }
        Vector3f shoulder0 = rest.get(arm).getTranslation(new Vector3f()), wrist0 = rest.get(tool).getTranslation(new Vector3f());
        Vector3f shoulder = ma.transformPosition(new Vector3f(shoulder0)), wrist = mt.transformPosition(new Vector3f(wrist0));
        Vector3f d0 = new Vector3f(wrist0).sub(shoulder0), d = new Vector3f(wrist).sub(shoulder);
        if (d0.lengthSquared() < 1e-6F || d.lengthSquared() < 1e-6F) {
            pose(part, ma, mh, w);
            return;
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
        poseRot(part, ma, new Quaternionf(aim).mul(twist), w);
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
        Clip c = r == null ? null : clip(r);
        if (c == null) {
            return "no clip";
        }
        StringBuilder b = new StringBuilder();
        Matrix4f m = new Matrix4f();
        for (String j : joints) {
            Sheet s = c.joints().get(j);
            if (s == null) {
                continue;
            }
            s.at(t, m);
            Vector3f p = m.getTranslation(new Vector3f());
            Quaternionf q = m.getNormalizedRotation(new Quaternionf());
            b.append(String.format(java.util.Locale.ROOT, "%s t(%.2f,%.2f,%.2f) q(%.2f,%.2f,%.2f,%.2f) ", j, p.x, p.y, p.z, q.x, q.y, q.z, q.w));
        }
        return b.toString();
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
