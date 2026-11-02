package jp.oror.reborn.show;

import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * (052) Each kind of technique, each big move, and a guard's moments (parry, block, a broken guard, being parried),
 * danced its own way on the characters' rigs. A technique runs windup, blow, hold and
 * recovery: through the windup the body goes into the technique's gathering pose (W), on the moment it goes off it
 * snaps through to the striking pose (R), a touch past it and back, holds it, and eases home; a few techniques move
 * within the blow as well (alternating thrusts, a hammer's beat, a hand drawing a clock face backwards, a whirl). The
 * poses are offsets in radians on the rig's parts by their role (arms, legs, head, torso, root, jaw, wings, tail), so
 * a rig without arms (a dragon, the turtle-mountain) still rears its head, opens its jaw, spreads its wings and lashes
 * its tail. Laid over the rig's own idle and walk.
 */
public final class TechniquePoses {
    private TechniquePoses() {
    }

    /** A part of a rig and its role. */
    record Ref(ModelPart part, String role, boolean left, float index) {
    }

    record Choreo(Map<String, float[]> windup, Map<String, float[]> release, String beat) {
    }

    private static final Map<String, Choreo> CHOREO = new HashMap<>();
    private static final float PI = (float) Math.PI;

    /** pose("arm_r", x, y, z, "root", x, y, z, lift, ...): roles with their three turns (and the root a lift, in pixels). */
    private static Map<String, float[]> pose(Object... a) {
        Map<String, float[]> m = new HashMap<>();
        int i = 0;
        while (i < a.length) {
            String role = (String) a[i++];
            int n = role.equals("root") ? 4 : 3;
            float[] v = new float[4];
            for (int k = 0; k < n; k++) {
                v[k] = ((Number) a[i++]).floatValue();
            }
            m.put(role, v);
        }
        return m;
    }

    private static void def(String mechanic, Map<String, float[]> w, Map<String, float[]> r, String beat) {
        CHOREO.put(mechanic, new Choreo(w, r, beat));
    }

    static {
        // a dash and one sweeping cut: drawn back high over the right shoulder, swept across the body in a lunge
        def("SLASH", pose("arm_r", -2.2, 0.9, 0.3, "arm_l", -0.6, 0, -0.3, "torso", 0, 0.6, 0, "root", 0.1, 0, 0, 0, "leg_r", 0.3, 0, 0,
                "leg_l", -0.4, 0, 0, "head", -0.2, 0, 0),
            pose("arm_r", -1.3, -1.3, 0.1, "arm_l", -0.2, 0, -0.6, "torso", 0.2, -0.75, 0, "root", 0.25, 0, 0, 0, "leg_r", -0.6, 0, 0,
                "leg_l", 0.5, 0, 0, "head", 0.1, 0, 0), "");
        // erasure: both hands high over the head, brought straight down
        def("ERASE", pose("arm_r", -3.0, 0, 0.1, "arm_l", -3.0, 0, -0.1, "torso", -0.3, 0, 0, "head", -0.35, 0, 0, "root", -0.1, 0, 0, 2),
            pose("arm_r", -0.5, 0, 0.05, "arm_l", -0.5, 0, -0.05, "torso", 0.5, 0, 0, "head", 0.2, 0, 0, "root", 0.2, 0, 0, -2, "leg_r", -0.5, 0, 0,
                "leg_l", 0.35, 0, 0), "");
        // reflection: arms crossed before the chest, flung apart
        def("REFLECT", pose("arm_r", -1.5, -0.7, -0.2, "arm_l", -1.5, 0.7, 0.2, "torso", 0.1, 0, 0, "head", 0.15, 0, 0),
            pose("arm_r", -1.2, 1.0, 0.7, "arm_l", -1.2, -1.0, -0.7, "torso", -0.15, 0, 0, "head", -0.1, 0, 0), "");
        // growth: bowed down with the hands to the ground, rising with the arms to the sky as it blooms
        def("GROW", pose("torso", 0.75, 0, 0, "arm_r", -0.5, 0, 0.25, "arm_l", -0.5, 0, -0.25, "head", 0.45, 0, 0, "leg_r", -0.35, 0, 0,
                "leg_l", -0.35, 0, 0, "root", 0, 0, 0, -1.5),
            pose("torso", -0.2, 0, 0, "arm_r", -2.8, 0, 0.6, "arm_l", -2.8, 0, -0.6, "head", -0.5, 0, 0, "root", 0, 0, 0, 1.5), "");
        // rewinding: the right hand held up and drawing a clock face backwards
        def("REWIND", pose("arm_r", -1.6, 0, 0, "arm_l", -0.5, 0.3, 0, "head", 0, 0, 0.2, "root", 0, 0, 0, 1),
            pose("arm_r", -1.6, 0, 0, "arm_l", -0.7, 0.4, 0, "head", -0.1, 0, 0.2, "root", 0, 0, 0, 2), "clock");
        // weather: arms low and back, then up to the sky
        def("WEATHER", pose("arm_r", 0.5, 0, 0.3, "arm_l", 0.5, 0, -0.3, "head", 0.2, 0, 0),
            pose("arm_r", -2.9, 0, 0.5, "arm_l", -2.9, 0, -0.5, "head", -0.7, 0, 0, "torso", -0.2, 0, 0, "root", 0, 0, 0, 3), "");
        // sealing: hands drawn back to the shoulders, both palms thrust forward together
        def("SEAL", pose("arm_r", -0.9, 0.3, 0.2, "arm_l", -0.9, -0.3, -0.2, "torso", -0.2, 0, 0),
            pose("arm_r", -1.6, -0.3, -0.25, "arm_l", -1.6, 0.3, 0.25, "torso", 0.3, 0, 0, "root", 0.15, 0, 0, 0, "head", 0.1, 0, 0), "");
        // guard: arms crossed, feet planted wide, sunk into the stance
        def("GUARD", pose("arm_r", -1.3, -0.7, -0.3, "arm_l", -1.3, 0.7, 0.3, "head", 0.2, 0, 0),
            pose("arm_r", -1.5, -0.8, -0.4, "arm_l", -1.5, 0.8, 0.4, "leg_r", 0, 0, 0.3, "leg_l", 0, 0, -0.3, "torso", -0.1, 0, 0,
                "root", 0, 0, 0, -1.2), "");
        // a shift: a whirl in place, arms out
        def("SHIFT", pose("arm_r", -0.3, 0, 0.6, "arm_l", -0.3, 0, -0.6, "torso", 0, 0.5, 0),
            pose("arm_r", -0.3, 0, 1.4, "arm_l", -0.3, 0, -1.4, "head", -0.2, 0, 0, "root", 0, 0, 0, 2), "spin");
        // law: the right hand raised to heaven as a gavel, brought down to point at the condemned; the left on the heart
        def("LAW", pose("arm_r", -3.0, 0, 0.2, "arm_l", -0.8, 0.6, 0, "head", -0.3, 0, 0),
            pose("arm_r", -1.45, 0, 0, "arm_l", -0.8, 0.6, 0, "head", 0.15, 0, 0, "torso", 0.2, 0, 0), "");
        // adaptation: drawn in, then opened wide, trembling with what it takes in
        def("ADAPT", pose("arm_r", -0.8, 0, -0.2, "arm_l", -0.8, 0, 0.2, "torso", 0.3, 0, 0, "head", 0.3, 0, 0),
            pose("arm_r", -0.4, 0, 1.5, "arm_l", -0.4, 0, -1.5, "head", -0.45, 0, 0, "torso", -0.3, 0, 0, "root", 0, 0, 0, 1.5), "tremble");
        // transmutation: hands clapped together before the chest, opened outward
        def("TRANSMUTE", pose("arm_r", -1.4, -0.5, -0.4, "arm_l", -1.4, 0.5, 0.4, "head", 0.2, 0, 0),
            pose("arm_r", -1.6, 0.6, 0.7, "arm_l", -1.6, -0.6, -0.7, "head", -0.1, 0, 0), "");
        // summoning: arms raised wide over the head, rising, then thrust down and forward to command
        def("SUMMON", pose("arm_r", -0.3, 0, 2.1, "arm_l", -0.3, 0, -2.1, "head", -0.55, 0, 0, "root", 0, 0, 0, 3, "torso", -0.15, 0, 0),
            pose("arm_r", -1.8, 0, 0.4, "arm_l", -1.8, 0, -0.4, "torso", 0.3, 0, 0, "head", 0.1, 0, 0), "");
        // mana: sat in the air, hands before the chest, rising and bobbing
        def("MANA", pose("arm_r", -1.1, -0.6, -0.2, "arm_l", -1.1, 0.6, 0.2, "leg_r", -1.2, 0.3, 0, "leg_l", -1.2, -0.3, 0, "head", 0.2, 0, 0,
                "root", 0, 0, 0, 3),
            pose("arm_r", -1.2, -0.7, -0.2, "arm_l", -1.2, 0.7, 0.2, "leg_r", -1.2, 0.3, 0, "leg_l", -1.2, -0.3, 0, "head", -0.2, 0, 0,
                "root", 0, 0, 0, 5), "bob");
        // barrage: arms drawn back, then thrust in turn again and again
        def("BARRAGE", pose("arm_r", 0.4, 0, 0.2, "arm_l", 0.4, 0, -0.2, "torso", -0.15, 0, 0),
            pose("arm_r", -1.6, 0, 0, "arm_l", -1.6, 0, 0, "torso", 0.15, 0, 0), "alternate");
        // burst: crouched and drawn in, then flung open and up
        def("BURST", pose("torso", 0.6, 0, 0, "arm_r", -0.6, 0, -0.3, "arm_l", -0.6, 0, 0.3, "leg_r", -0.5, 0, 0, "leg_l", -0.5, 0, 0,
                "root", 0, 0, 0, -2, "head", 0.3, 0, 0),
            pose("arm_r", -0.6, 0, 1.9, "arm_l", -0.6, 0, -1.9, "head", -0.6, 0, 0, "torso", -0.4, 0, 0, "root", 0, 0, 0, 3), "");
        // repair: bent over the work, the right hand beating like a smith's hammer
        def("REPAIR", pose("arm_r", -2.0, 0, 0, "arm_l", -0.9, 0.3, 0, "torso", 0.25, 0, 0, "head", 0.35, 0, 0),
            pose("arm_r", -1.6, 0, 0, "arm_l", -0.9, 0.3, 0, "torso", 0.3, 0, 0, "head", 0.4, 0, 0), "hammer");
        // healing: palms opened upward to the sides, face to the sky, lifted
        def("HEAL", pose("arm_r", -0.2, 0, 0.2, "arm_l", -0.2, 0, -0.2, "head", 0.2, 0, 0),
            pose("arm_r", -0.9, 0, 0.9, "arm_l", -0.9, 0, -0.9, "head", -0.5, 0, 0, "root", 0, 0, 0, 2), "bob");
        // drain: a clawed hand reaches out, then hauls back to the chest
        def("DRAIN", pose("arm_r", -1.7, -0.2, 0, "arm_l", -0.4, 0, -0.2, "torso", 0.3, 0, 0),
            pose("arm_r", -0.6, 0.35, -0.35, "arm_l", -0.4, 0, -0.3, "torso", -0.35, 0, 0, "head", -0.2, 0, 0, "root", -0.15, 0, 0, 0), "");
        // curse: hunched, hands hanging forward, jerking out and twitching
        def("CURSE", pose("torso", 0.5, 0, 0, "head", 0.5, 0, 0, "arm_r", -0.9, 0, 0.2, "arm_l", -0.9, 0, -0.2),
            pose("torso", 0.35, 0, 0, "head", 0.15, 0, 0, "arm_r", -1.55, 0, 0.45, "arm_l", -1.55, 0, -0.45), "twitch");
        // pull: both hands out, then yanked back with a twist of the body, as if hauling a rope
        def("PULL", pose("arm_r", -1.6, -0.1, 0, "arm_l", -1.5, 0.2, 0, "torso", 0.2, 0, 0),
            pose("arm_r", -0.4, 0.5, 0.2, "arm_l", -0.5, 0.4, 0, "torso", -0.3, 0.5, 0, "root", -0.15, 0, 0, 0, "leg_l", -0.4, 0, 0), "");
        // fate: a card drawn up toward the sky, flicked across at the enemy
        def("FATE", pose("arm_r", -2.6, 0.3, 0.3, "arm_l", -1.0, 0.2, 0, "head", -0.3, 0, 0),
            pose("arm_r", -1.4, -0.9, 0, "arm_l", -0.6, 0.2, 0, "torso", 0, -0.45, 0), "");
        // copy: both hands mirrored forward, then crossed to take the other's form
        def("COPY", pose("arm_r", -1.5, 0, 0.2, "arm_l", -1.5, 0, -0.2, "head", 0, 0, 0.2),
            pose("arm_r", -1.5, -0.5, -0.3, "arm_l", -1.5, 0.5, 0.3, "head", 0, 0, -0.3), "");
        // toy: a playful twirl with the arms out
        def("TOY", pose("arm_r", -0.6, 0, 0.8, "arm_l", -0.6, 0, -0.8, "head", 0, 0, 0.3),
            pose("arm_r", -0.6, 0, 1.3, "arm_l", -0.6, 0, -1.3, "head", -0.2, 0, -0.3, "root", 0, 0, 0, 3), "spin");
        // the base abilities: a two-cut combo for the swordfolk, a one-handed bolt for the casters, a swoop for flyers
        def("COMBO", pose("arm_r", -2.1, 0.8, 0.3, "arm_l", -0.7, 0, -0.3, "torso", 0, 0.5, 0, "leg_l", -0.3, 0, 0),
            pose("arm_r", -1.3, -1.1, 0, "arm_l", -0.5, 0, -0.4, "torso", 0.2, -0.5, 0, "leg_r", -0.5, 0, 0, "leg_l", 0.4, 0, 0), "combo");
        def("BOLT", pose("arm_r", 0.3, 0.2, 0.3, "arm_l", -1.3, 0.3, 0, "torso", 0, 0.35, 0, "head", 0, 0, 0),
            pose("arm_r", -1.65, -0.1, 0, "arm_l", -0.4, 0, -0.3, "torso", 0.15, -0.3, 0), "");
        def("SWOOP", pose("root", -0.35, 0, 0, 3, "head", -0.4, 0, 0, "arm_r", -0.3, 0, 0.9, "arm_l", -0.3, 0, -0.9),
            pose("root", 0.45, 0, 0, -2, "head", 0.3, 0, 0, "arm_r", -1.4, 0, 0.3, "arm_l", -1.4, 0, -0.3), "");

        // ---- a guard's moments (MobGuard): over in half a second, the blow taking the place of the windup
        // parry: the weapon swept up and out across the blow, the body turning from it, leaning back off it
        def("PARRY", pose("arm_r", -1.0, -0.3, 0, "torso", 0, -0.2, 0),
            pose("arm_r", -2.3, 0.9, 0.5, "arm_l", -0.5, 0, -0.4, "torso", 0, 0.45, 0, "head", -0.15, 0, 0, "root", -0.15, 0, 0, 0,
                "leg_l", -0.3, 0, 0), "");
        def("PARRY_shield", pose("arm_l", -1.2, 0.3, 0),
            pose("arm_l", -1.75, 0.6, 0.2, "arm_r", -0.6, 0, 0.25, "torso", 0, -0.3, 0, "head", 0.1, 0, 0, "root", -0.1, 0, 0, 0), "");
        def("PARRY_heavy", pose("arm_r", -1.0, 0, 0, "arm_l", -1.0, 0, 0),
            pose("arm_r", -1.9, -0.35, -0.2, "arm_l", -1.9, 0.35, 0.2, "torso", -0.2, 0, 0, "head", -0.2, 0, 0, "root", -0.15, 0, 0, 0), "");
        def("PARRY_polearm", pose("arm_r", -1.0, 0.3, 0, "arm_l", -1.0, -0.3, 0),
            pose("arm_r", -1.5, 0.6, 0.3, "arm_l", -1.5, -0.6, -0.3, "torso", 0, 0.35, 0, "root", -0.15, 0, 0, 0), "");
        def("PARRY_fist", pose("arm_r", -1.2, -0.3, 0),
            pose("arm_r", -2.0, -0.7, -0.1, "arm_l", -1.2, 0.3, 0, "torso", 0, -0.45, 0, "leg_r", -0.3, 0, 0), "");
        def("PARRY_magic", pose("arm_r", -1.2, 0, 0),
            pose("arm_r", -1.65, 0, -0.25, "arm_l", -1.0, 0.3, 0, "head", 0.1, 0, 0, "torso", -0.1, 0, 0, "root", -0.1, 0, 0, 0), "");
        // block: arms (the weapon) across the body, feet planted, sunk under the blow and driven back a little
        def("BLOCK", pose("arm_r", -1.3, -0.5, -0.2, "arm_l", -1.3, 0.5, 0.2),
            pose("arm_r", -1.45, -0.65, -0.3, "arm_l", -1.45, 0.65, 0.3, "torso", 0.15, 0, 0, "head", 0.15, 0, 0, "leg_r", -0.3, 0, 0.1,
                "leg_l", 0.3, 0, -0.1, "root", -0.12, 0, 0, -0.8), "");
        def("BLOCK_shield", pose("arm_l", -1.3, 0.4, 0),
            pose("arm_l", -1.55, 0.5, 0, "arm_r", -0.7, 0, 0.2, "torso", 0.15, 0, 0, "head", 0.1, 0, 0, "leg_r", -0.35, 0, 0,
                "root", -0.1, 0, 0, -0.8), "");
        // the guard broken: the arms flung wide and up, the body arched back, reeling
        def("BREAK", pose("arm_r", -1.4, 0, 0.2, "arm_l", -1.4, 0, -0.2),
            pose("arm_r", -2.6, 0, 0.7, "arm_l", -2.6, 0, -0.7, "torso", -0.45, 0, 0, "head", -0.5, 0, 0, "root", -0.3, 0, 0, -1,
                "leg_l", -0.4, 0, 0), "tremble");
        // parried: the weapon knocked up and back, the body thrown back off its feet a step
        def("PARRIED", pose("arm_r", -1.6, 0, 0),
            pose("arm_r", -2.5, 0.4, 0.45, "arm_l", -0.3, 0, -0.6, "torso", -0.35, 0.25, 0, "head", -0.3, 0, 0, "root", -0.25, 0, 0, 0,
                "leg_l", -0.35, 0, 0), "");

        // ---- the big moves (BossMoves): each danced its own way, over the moves' own motion
        // a dash and a cut: crouched with the blade drawn low behind, a long lunge sweeping it across
        def("MOVE_DASH_SLASH", pose("arm_r", 0.6, 0.6, 0.3, "torso", 0.35, 0.5, 0, "leg_r", -0.6, 0, 0, "leg_l", 0.4, 0, 0, "root", 0.3, 0, 0, -1),
            pose("arm_r", -1.4, -1.4, 0, "arm_l", -0.3, 0, -0.6, "torso", 0.25, -0.8, 0, "leg_r", 0.5, 0, 0, "leg_l", -0.7, 0, 0,
                "root", 0.35, 0, 0, 0), "");
        // a blink and a stab: the point levelled, then thrust home at full stretch
        def("MOVE_BLINK_STRIKE", pose("arm_r", -1.0, 0, 0, "arm_l", -0.4, 0, -0.3, "torso", 0.2, 0, 0, "head", 0.1, 0, 0),
            pose("arm_r", -1.6, 0, 0, "arm_l", 0.3, 0, -0.3, "torso", 0.4, 0, 0, "root", 0.35, 0, 0, 0, "leg_r", -0.8, 0, 0, "leg_l", 0.6, 0, 0), "");
        // a rush of cuts: three, back and forth
        def("MOVE_COMBO_RUSH", pose("arm_r", -2.1, 0.8, 0.3, "arm_l", -0.7, 0, -0.3, "torso", 0, 0.5, 0, "leg_l", -0.3, 0, 0),
            pose("arm_r", -1.3, -1.1, 0, "arm_l", -0.5, 0, -0.4, "torso", 0.2, -0.5, 0, "leg_r", -0.5, 0, 0, "leg_l", 0.4, 0, 0), "combo3");
        // a whirlwind of the blade: held out flat and spun twice round
        def("MOVE_SPIN_SLASH", pose("arm_r", -1.4, 0.9, 0.9, "arm_l", -0.5, 0, -1.0, "torso", 0, 0.7, 0, "root", 0, 0, 0, -1),
            pose("arm_r", -1.5, 0, 1.4, "arm_l", -0.4, 0, -1.3, "head", -0.1, 0, 0), "spin2");
        // a wave off the blade: both hands high overhead, brought down in one great cut
        def("MOVE_BLADE_WAVE", pose("arm_r", -3.0, 0, 0.1, "arm_l", -3.0, 0, -0.1, "torso", -0.35, 0, 0, "head", -0.3, 0, 0, "root", 0, 0, 0, 1),
            pose("arm_r", -0.6, 0, 0.05, "arm_l", -0.6, 0, -0.05, "torso", 0.55, 0, 0, "head", 0.2, 0, 0, "root", 0.25, 0, 0, -2,
                "leg_r", -0.6, 0, 0, "leg_l", 0.4, 0, 0), "");
        // a leap and a slam: crouched to spring, the arms swung up over the head in the air, and down with the landing
        def("MOVE_LEAP_SLAM", pose("torso", 0.5, 0, 0, "leg_r", -0.6, 0, 0, "leg_l", -0.6, 0, 0, "arm_r", 0.6, 0, 0.2, "arm_l", 0.6, 0, -0.2,
                "root", 0, 0, 0, -2),
            pose("arm_r", -0.4, 0, 0.2, "arm_l", -0.4, 0, -0.2, "torso", 0.7, 0, 0, "head", 0.3, 0, 0, "leg_r", -0.9, 0, 0, "leg_l", 0.2, 0, 0,
                "root", 0.3, 0, 0, -3), "leap");
        // an uppercut: down low with the fist back, rising with it to the sky
        def("MOVE_UPPERCUT", pose("arm_r", 0.5, 0, 0.2, "torso", 0.45, 0.3, 0, "leg_r", -0.4, 0, 0, "leg_l", -0.4, 0, 0, "root", 0, 0, 0, -2),
            pose("arm_r", -2.9, 0, 0.2, "arm_l", -0.5, 0, -0.3, "torso", -0.3, -0.3, 0, "head", -0.4, 0, 0, "leg_l", -0.5, 0, 0, "root", 0, 0, 0, 3), "");
        // spikes from the ground: the hand raised, driven down into the earth on one knee
        def("MOVE_GROUND_SPIKES", pose("arm_r", -2.6, 0, 0.3, "arm_l", -0.6, 0, -0.3, "torso", -0.2, 0, 0, "head", -0.2, 0, 0),
            pose("arm_r", -0.2, 0, 0.3, "arm_l", -0.4, 0, -0.4, "torso", 0.8, 0, 0, "head", 0.5, 0, 0, "leg_r", -1.2, 0, 0, "leg_l", 0.3, 0, 0,
                "root", 0.2, 0, 0, -3), "");
        // a nova: curled in about itself, then everything flung open, trembling with the light
        def("MOVE_NOVA", pose("torso", 0.7, 0, 0, "arm_r", -1.2, -0.5, -0.3, "arm_l", -1.2, 0.5, 0.3, "leg_r", -0.5, 0, 0, "leg_l", -0.5, 0, 0,
                "head", 0.4, 0, 0, "root", 0, 0, 0, -2),
            pose("arm_r", -0.6, 0, 2.2, "arm_l", -0.6, 0, -2.2, "head", -0.6, 0, 0, "torso", -0.45, 0, 0, "leg_r", 0, 0, 0.35, "leg_l", 0, 0, -0.35,
                "root", 0, 0, 0, 4), "tremble");
        // a vortex: arms out, turning and turning, lifted on it
        def("MOVE_VORTEX", pose("arm_r", -0.3, 0, 1.0, "arm_l", -0.3, 0, -1.0, "torso", 0, 0.4, 0),
            pose("arm_r", -0.5, 0, 1.5, "arm_l", -0.5, 0, -1.5, "head", -0.3, 0, 0, "root", 0, 0, 0, 2), "spin3");
        // a meteor called down: both arms to the sky, then thrust down at the enemy
        def("MOVE_METEOR", pose("arm_r", -3.0, 0, 0.3, "arm_l", -3.0, 0, -0.3, "head", -0.7, 0, 0, "torso", -0.25, 0, 0, "root", 0, 0, 0, 2),
            pose("arm_r", -1.2, 0, 0.2, "arm_l", -1.2, 0, -0.2, "torso", 0.4, 0, 0, "head", 0.1, 0, 0, "leg_r", -0.4, 0, 0), "");
        // a beam: both hands drawn back to the hip, gathering, then thrust out together and held, shaking with it
        def("MOVE_BEAM", pose("arm_r", 0.3, 0.6, 0.3, "arm_l", 0.3, -0.6, -0.3, "torso", 0, 0.5, 0, "leg_r", -0.3, 0, 0, "root", 0, 0, 0, -1),
            pose("arm_r", -1.6, 0.15, 0, "arm_l", -1.6, -0.15, 0, "torso", 0.1, -0.2, 0, "leg_r", -0.4, 0, 0, "leg_l", 0.3, 0, 0), "tremble");
        // orbs set loose: the hands raised at the sides, then conducting them in turn
        def("MOVE_HOMING_ORBS", pose("arm_r", -1.0, 0, 0.9, "arm_l", -1.0, 0, -0.9, "head", -0.3, 0, 0, "root", 0, 0, 0, 1),
            pose("arm_r", -1.5, 0, 0.4, "arm_l", -1.0, 0, -0.9, "head", -0.1, 0, 0, "root", 0, 0, 0, 2), "conduct");
        // a rain of arrows: the bow raised to the sky and drawn, loosed again and again
        def("MOVE_ARROW_RAIN", pose("arm_l", -2.6, 0.2, 0, "arm_r", -2.4, -0.5, 0, "head", -0.8, 0, 0, "torso", -0.25, 0, 0),
            pose("arm_l", -2.7, 0.2, 0, "arm_r", -1.8, -0.7, 0, "head", -0.8, 0, 0, "torso", -0.25, 0, 0), "recoil");
        // a barrage of bolts: thrust after thrust
        def("MOVE_BOLT_BARRAGE", pose("arm_r", 0.4, 0, 0.2, "arm_l", 0.4, 0, -0.2, "torso", -0.15, 0, 0),
            pose("arm_r", -1.6, 0, 0, "arm_l", -1.6, 0, 0, "torso", 0.15, 0, 0), "alternate");
        // a storm of bullets: levelled and held on the enemy, shaken by every shot
        def("MOVE_BULLET_STORM", pose("arm_r", -1.4, 0, 0, "arm_l", -1.4, 0.4, 0, "torso", 0.1, 0, 0),
            pose("arm_r", -1.55, 0, 0, "arm_l", -1.5, 0.4, 0, "torso", 0.05, 0, 0, "leg_r", -0.3, 0, 0, "leg_l", 0.3, 0, 0), "recoil");
        // a barrage of shells: braced wide, kicked back hard by each
        def("MOVE_SHELL_BARRAGE", pose("arm_r", -1.2, 0, 0, "arm_l", -1.2, 0.3, 0, "torso", 0.25, 0, 0, "leg_r", -0.4, 0, 0.2, "leg_l", 0.4, 0, -0.2,
                "root", 0, 0, 0, -1),
            pose("arm_r", -1.7, 0, 0, "arm_l", -1.6, 0.3, 0, "torso", -0.1, 0, 0, "leg_r", -0.4, 0, 0.2, "leg_l", 0.4, 0, -0.2,
                "root", 0, 0, 0, -1), "heavy_recoil");
        // a barrier: the arms crossed, then spread with the palms out, raising the dome
        def("MOVE_BARRIER", pose("arm_r", -1.3, -0.7, -0.3, "arm_l", -1.3, 0.7, 0.3, "head", 0.2, 0, 0),
            pose("arm_r", -1.7, 0, 1.2, "arm_l", -1.7, 0, -1.2, "head", -0.2, 0, 0, "root", 0, 0, 0, 1), "");
        // a chain: flung out overarm, then hauled back with the whole body
        def("MOVE_CHAIN_PULL", pose("arm_r", -2.6, 0.4, 0.3, "arm_l", -0.6, 0, -0.3, "torso", 0, 0.5, 0),
            pose("arm_r", -0.3, 0.6, 0.2, "arm_l", -0.5, 0.4, 0, "torso", -0.3, -0.5, 0, "root", -0.2, 0, 0, 0, "leg_l", -0.5, 0, 0), "");
        // a reaping: the blade low and back, swept round low through a whole turn
        def("MOVE_REAP", pose("arm_r", -0.6, 1.2, 0.6, "arm_l", -0.8, 1.0, 0, "torso", 0.3, 0.8, 0, "root", 0, 0, 0, -1.5),
            pose("arm_r", -0.9, -1.6, 0.2, "arm_l", -0.9, -1.3, 0, "torso", 0.3, -0.9, 0, "root", 0, 0, 0, -1.5), "spin");
        // a ricochet: drawn back and flicked across
        def("MOVE_RICOCHET", pose("arm_r", -2.2, 0.6, 0.5, "arm_l", -0.8, 0.2, 0, "torso", 0, 0.4, 0),
            pose("arm_r", -1.2, -1.0, 0, "arm_l", -0.5, 0.2, 0, "torso", 0, -0.5, 0), "");
        // afterimages: low and running, weaving from side to side
        def("MOVE_AFTERIMAGE", pose("torso", 0.5, 0, 0, "arm_r", 0.7, 0, 0.2, "arm_l", 0.7, 0, -0.2, "head", 0.2, 0, 0, "root", 0.2, 0, 0, -1.5),
            pose("arm_r", -1.4, -1.0, 0, "arm_l", 0.6, 0, -0.3, "torso", 0.3, -0.6, 0, "root", 0.3, 0, 0, -1), "weave");
        // a charge: the head down and the shoulder forward, the arms swept back, running
        def("MOVE_CHARGE", pose("torso", 0.6, 0, 0, "head", 0.5, 0, 0, "arm_r", 0.6, 0, 0.2, "arm_l", 0.6, 0, -0.2, "leg_r", -0.5, 0, 0,
                "root", 0.3, 0, 0, -1),
            pose("torso", 0.7, 0, 0, "head", 0.4, 0, 0, "arm_r", -0.3, 0, 0.3, "arm_l", -0.3, 0, -0.3, "root", 0.45, 0, 0, -1), "run");
        // a breath: the head thrown back to draw it in, the chest swelling, then thrust forward with it
        def("MOVE_BREATH", pose("head", -0.8, 0, 0, "torso", -0.4, 0, 0, "arm_r", 0.5, 0, 0.3, "arm_l", 0.5, 0, -0.3, "root", 0, 0, 0, 1),
            pose("head", 0.35, 0, 0, "torso", 0.35, 0, 0, "arm_r", 0.8, 0, 0.4, "arm_l", 0.8, 0, -0.4, "root", 0.2, 0, 0, 0), "tremble");
    }

    /** A guard's moments: weapon-held poses of their own, so the weapon's manner is not laid over them. */
    private static final java.util.Set<String> DEFENCE = java.util.Set.of("PARRY", "BLOCK", "BREAK", "PARRIED");

    // ------------------------------------------------------------------------------------------- the weapon's manner

    /** The techniques worked with a hand (a sign, a seal, a draw), rather than with the weapon. */
    private static final java.util.Set<String> HAND = java.util.Set.of("SEAL", "HEAL", "MANA", "TRANSMUTE", "REWIND", "COPY", "ADAPT", "CURSE",
        "DRAIN", "PULL", "FATE", "LAW", "REPAIR", "GROW", "WEATHER");
    private static Map<String, String> styles;

    /** The character's weapon, grouped: blade, polearm, heavy, fist, whip, ranged, shield, chakram, magic. */
    static String style(String character) {
        if (styles == null) {
            Map<String, String> m = new HashMap<>();
            try (java.io.InputStream in = TechniquePoses.class.getResourceAsStream("/assets/oror_supreme_bosses/weapon_kinds.json")) {
                if (in != null) {
                    com.google.gson.JsonObject chars = com.google.gson.JsonParser.parseReader(new java.io.InputStreamReader(in,
                        java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonObject("characters");
                    for (Map.Entry<String, com.google.gson.JsonElement> e : chars.entrySet()) {
                        String kind = e.getValue().isJsonPrimitive() ? e.getValue().getAsString() : "magic";
                        m.put(e.getKey(), switch (kind) {
                            case "katana", "sword", "greatsword", "rapier", "scythe" -> "blade";
                            case "polearm" -> "polearm";
                            case "heavy", "toyhammer" -> "heavy";
                            case "fist" -> "fist";
                            case "whip" -> "whip";
                            case "gatling", "cannon", "bow" -> "ranged";
                            case "shield" -> "shield";
                            case "chakram" -> "chakram";
                            default -> "magic";
                        });
                    }
                }
            } catch (java.io.IOException | RuntimeException ex) {
                // no styles: every character works as a caster
            }
            styles = m;
        }
        return styles.getOrDefault(character, "magic");
    }

    /** The weapon held at the ready while the other hand works a sign. */
    private static final Map<String, float[]> READY = Map.of(
        "blade", new float[]{-1.05F, -0.25F, 0.1F}, "polearm", new float[]{-0.75F, -0.3F, 0}, "heavy", new float[]{-0.35F, 0, 0.25F},
        "fist", new float[]{-1.25F, -0.35F, -0.2F}, "whip", new float[]{-0.5F, 0, 0.35F}, "ranged", new float[]{-1.45F, 0, 0},
        "shield", new float[]{-1.2F, 0.3F, 0}, "chakram", new float[]{-0.8F, 0.4F, 0.3F});

    /** The weapon's manner laid over a technique worked with the weapon: windup and release offsets by role. */
    private static final Map<String, Map<String, float[][]>> MANNER = new HashMap<>();

    static {
        MANNER.put("blade", Map.of("arm_r", new float[][]{{-0.4F, 0.5F, 0}, {0.1F, -0.6F, 0}}, "torso", new float[][]{{0, 0.3F, 0}, {0.1F, -0.35F, 0}}));
        MANNER.put("polearm", Map.of("arm_r", new float[][]{{0.3F, 0.2F, 0}, {-0.35F, 0, 0}}, "arm_l", new float[][]{{0.3F, -0.2F, 0}, {-0.35F, 0, 0}},
            "torso", new float[][]{{-0.15F, 0, 0}, {0.25F, 0, 0}}));
        MANNER.put("heavy", Map.of("arm_r", new float[][]{{-1.0F, 0, 0}, {0.6F, 0, 0}}, "arm_l", new float[][]{{-1.0F, 0, 0}, {0.6F, 0, 0}},
            "torso", new float[][]{{-0.25F, 0, 0}, {0.35F, 0, 0}}));
        MANNER.put("fist", Map.of("arm_r", new float[][]{{0.4F, 0.3F, 0}, {-0.3F, -0.2F, 0}}, "torso", new float[][]{{0, 0.4F, 0}, {0.15F, -0.45F, 0}}));
        MANNER.put("whip", Map.of("arm_r", new float[][]{{-0.7F, 0.7F, 0.4F}, {0.2F, -0.9F, -0.2F}}));
        MANNER.put("ranged", Map.of("arm_r", new float[][]{{-0.2F, 0, 0}, {-0.3F, 0, 0}}, "arm_l", new float[][]{{-0.9F, 0.3F, 0}, {-1.1F, 0.3F, 0}},
            "torso", new float[][]{{0, 0, 0}, {-0.12F, 0, 0}}));
        MANNER.put("shield", Map.of("arm_l", new float[][]{{-1.1F, 0.4F, 0}, {-1.3F, 0.2F, -0.2F}}, "torso", new float[][]{{0.1F, 0, 0}, {0.2F, 0, 0}}));
        MANNER.put("chakram", Map.of("arm_r", new float[][]{{0, 1.1F, 0.3F}, {0, -1.3F, 0.6F}}, "torso", new float[][]{{0, 0.5F, 0}, {0, -0.5F, 0}}));
    }

    // ------------------------------------------------------------------------------------------------ the rig's parts

    private static final Map<Object, List<Ref>> PARTS = new WeakHashMap<>();
    private static Field animatedField, partField, animField, leftField;
    private static java.lang.reflect.Method fMethod;

    static List<Ref> parts(Object model) {
        List<Ref> got = PARTS.get(model);
        if (got != null) {
            return got;
        }
        List<Ref> list = new ArrayList<>();
        try {
            if (animatedField == null) {
                animatedField = jp.oror.reborn.client.RigModel.class.getDeclaredField("animated");
                animatedField.setAccessible(true);
                Class<?> a = Class.forName("jp.oror.reborn.client.RigModel$Animated");
                partField = a.getDeclaredField("part");
                animField = a.getDeclaredField("anim");
                leftField = a.getDeclaredField("left");
                fMethod = a.getDeclaredMethod("f", String.class, float.class);
                partField.setAccessible(true);
                animField.setAccessible(true);
                leftField.setAccessible(true);
                fMethod.setAccessible(true);
            }
            for (Object a : (List<?>) animatedField.get(model)) {
                String anim = (String) animField.get(a);
                String role = switch (anim) {
                    case "arm_r", "arm_l", "leg_r", "leg_l", "head", "root", "jaw", "tail", "elbow", "knee" -> anim;
                    case "breath" -> "torso";
                    case "wing_r", "wing_l" -> "wing";
                    default -> null;
                };
                if (role != null) {
                    list.add(new Ref((ModelPart) partField.get(a), role, (Boolean) leftField.get(a), (Float) fMethod.invoke(a, "i", 0F)));
                }
            }
        } catch (ReflectiveOperationException | RuntimeException ex) {
            list.clear();
        }
        PARTS.put(model, list);
        return list;
    }

    // ---------------------------------------------------------------------------------------------------- the dance

    /** Lays the technique's pose over the rig. time: ticks since the technique began. */
    public static void apply(Object model, TechniqueShow.Active show, float time) {
        String style0 = style(show.character());
        Choreo c = CHOREO.get(show.mechanic() + "_" + (style0.equals("chakram") || style0.equals("whip") || style0.equals("ranged") ? "blade" : style0));
        if (c == null) {
            c = CHOREO.getOrDefault(show.mechanic(), CHOREO.get("BOLT"));
        }
        float total = show.length();
        float t = time / total;
        if (t < 0 || t > 1) {
            return;
        }
        float wf = Mth.clamp(show.windup() / total, 0.04F, 0.8F);
        float ww, wr, u = -1;
        if (t < wf) {
            ww = smooth(t / wf);
            wr = 0;
        } else {
            u = (t - wf) / (1 - wf);
            if (u < 0.18F) {
                float b = outBack(u / 0.18F);
                ww = 1 - b;
                wr = b;
            } else if (u < 0.45F) {
                ww = 0;
                wr = 1;
            } else {
                ww = 0;
                wr = 1 - smooth((u - 0.45F) / 0.55F);
            }
        }
        boolean hasArms = false;
        List<Ref> parts = parts(model);
        for (Ref r : parts) {
            hasArms |= r.role().startsWith("arm");
        }
        String style = style(show.character());
        // a sign worked by a warrior: the weapon held ready in the right hand, the sign made with the left (mirrored)
        boolean leftHand = !style.equals("magic") && HAND.contains(show.mechanic());
        Map<String, float[][]> manner = HAND.contains(show.mechanic()) || DEFENCE.contains(show.mechanic()) ? null : MANNER.get(style);
        for (Ref r : parts) {
            String role = r.role();
            boolean mirror = false;
            if (leftHand && role.equals("arm_l")) {
                role = "arm_r";
                mirror = true;
            }
            float[] w = c.windup().get(role), re = c.release().get(role);
            if (leftHand && r.role().equals("arm_r")) {
                float[] ready = READY.getOrDefault(style, READY.get("blade"));
                w = new float[]{ready[0], ready[1], ready[2], 0};
                re = w;
            }
            if (mirror) {
                w = w == null ? null : new float[]{w[0], -w[1], -w[2], w[3]};
                re = re == null ? null : new float[]{re[0], -re[1], -re[2], re[3]};
            }
            float x = 0, y = 0, z = 0, lift = 0;
            float[][] m = manner == null ? null : manner.get(r.role());
            if (m != null) {
                x += m[0][0] * ww + m[1][0] * wr;
                y += m[0][1] * ww + m[1][1] * wr;
                z += m[0][2] * ww + m[1][2] * wr;
            }
            if (w != null) {
                x += w[0] * ww;
                y += w[1] * ww;
                z += w[2] * ww;
                lift += w[3] * ww;
            }
            if (re != null) {
                x += re[0] * wr;
                y += re[1] * wr;
                z += re[2] * wr;
                lift += re[3] * wr;
            }
            // what every rig does: the jaw opens on the blow, the wings spread, the tail lashes, the elbows and knees
            // bend into it; a rig without arms rears its head through the windup and thrusts it out on the blow
            switch (r.role()) {
                case "jaw" -> x += 0.55F * wr - 0.1F * ww;
                case "wing" -> y += (r.left() ? -1 : 1) * (0.8F * wr - 0.35F * ww);
                case "tail" -> y += (0.6F * wr - 0.3F * ww) / (1 + r.index() * 0.3F) * (r.left() ? -1 : 1);
                case "elbow" -> x -= 0.5F * ww + 0.2F * wr;
                case "knee" -> x += 0.45F * ww + 0.2F * wr;
                case "head" -> {
                    if (!hasArms) {
                        x += -0.45F * ww + 0.35F * wr;
                    }
                }
                default -> {
                }
            }
            String beatRole = !leftHand ? r.role() : r.role().equals("arm_l") ? "arm_r" : r.role().equals("arm_r") ? "weapon" : r.role();
            float[] beat = beat(c.beat(), new Ref(r.part(), beatRole, r.left(), r.index()), u, time, wr);
            if (mirror) {
                beat[1] = -beat[1];
                beat[2] = -beat[2];
            }
            r.part().xRot += x + beat[0];
            r.part().yRot += y + beat[1];
            r.part().zRot += z + beat[2];
            if (r.role().equals("root")) {
                r.part().y -= lift + beat[3];
            }
        }
    }

    /** The movement within the blow: u is the time since the blow (0 to 1, -1 before it), weight the release's. */
    private static float[] beat(String beat, Ref r, float u, float time, float weight) {
        float[] v = new float[4];
        if (u < 0 || beat.isEmpty() || weight <= 0) {
            return v;
        }
        float live = u < 0.7F ? 1 : Math.max(0, 1 - (u - 0.7F) / 0.3F);
        switch (beat) {
            case "alternate" -> {
                // thrust after thrust, the arms in turn and the body turning into each
                float s = Mth.sin(time * 1.6F);
                if (r.role().equals("arm_r")) {
                    v[0] = s * 0.75F * live;
                } else if (r.role().equals("arm_l")) {
                    v[0] = -s * 0.75F * live;
                } else if (r.role().equals("torso")) {
                    v[1] = s * 0.3F * live;
                }
            }
            case "hammer" -> {
                if (r.role().equals("arm_r")) {
                    v[0] = -Math.abs(Mth.sin(time * 0.9F)) * 0.8F * live;
                } else if (r.role().equals("torso")) {
                    v[0] = Math.abs(Mth.sin(time * 0.9F)) * 0.12F * live;
                }
            }
            case "clock" -> {
                // a hand round a clock face, backwards
                float a = -u * 2 * PI * 1.5F;
                if (r.role().equals("arm_r")) {
                    v[0] = Mth.cos(a) * 0.55F * live;
                    v[2] = Mth.sin(a) * 0.55F * live;
                }
            }
            case "spin" -> {
                if (r.role().equals("root")) {
                    v[1] = 2 * PI * smooth(Math.min(1, u / 0.55F));
                }
            }
            case "tremble" -> v[2] = Mth.sin(time * 3.1F + r.index()) * 0.05F * live;
            case "twitch" -> {
                if (r.role().startsWith("arm") || r.role().equals("head")) {
                    v[0] = (Mth.sin(time * 4.3F + (r.left() ? 1.7F : 0)) > 0.6F ? 0.25F : 0) * live;
                }
            }
            case "bob" -> {
                if (r.role().equals("root")) {
                    v[3] = Mth.sin(time * 0.35F) * 1.2F * live;
                }
            }
            case "combo3" -> {
                // three cuts, back and forth, across the blow
                float k = Mth.sin(Math.min(1F, u / 0.9F) * 3 * PI);
                if (r.role().equals("arm_r")) {
                    v[1] = 1.8F * k * live;
                    v[0] = 0.3F * Math.abs(k) * live;
                } else if (r.role().equals("torso")) {
                    v[1] = 0.7F * k * live;
                }
            }
            case "spin2", "spin3" -> {
                if (r.role().equals("root")) {
                    float turns = beat.equals("spin2") ? 2 : 3;
                    v[1] = 2 * PI * turns * smooth(Math.min(1, u / (beat.equals("spin2") ? 0.7F : 0.85F)));
                }
            }
            case "leap" -> {
                // the arms swung up over the head in the air, and brought down with the landing
                if (u < 0.4F) {
                    float k = Mth.sin(u / 0.4F * PI);
                    if (r.role().startsWith("arm")) {
                        v[0] = -2.4F * k;
                    } else if (r.role().equals("torso")) {
                        v[0] = -0.7F * k;
                    } else if (r.role().equals("root")) {
                        v[3] = 3F * k;
                    }
                }
            }
            case "conduct" -> {
                float a = time * 0.45F + (r.left() ? PI : 0);
                if (r.role().startsWith("arm")) {
                    v[0] = Mth.cos(a) * 0.3F * live;
                    v[2] = Mth.sin(a) * 0.45F * live * (r.left() ? -1 : 1);
                }
            }
            case "recoil" -> {
                float k = Math.max(0, Mth.sin(time * 2.4F));
                if (r.role().startsWith("arm")) {
                    v[0] = 0.22F * k * live;
                } else if (r.role().equals("torso")) {
                    v[0] = -0.05F * k * live;
                }
            }
            case "heavy_recoil" -> {
                float k = Math.max(0, Mth.sin(time * 0.8F));
                k = k * k;
                if (r.role().startsWith("arm")) {
                    v[0] = 0.55F * k * live;
                } else if (r.role().equals("torso")) {
                    v[0] = -0.18F * k * live;
                } else if (r.role().equals("root")) {
                    v[0] = -0.12F * k * live;
                }
            }
            case "weave" -> {
                if (r.role().equals("root")) {
                    v[2] = Mth.sin(time * 0.7F) * 0.25F * live;
                    v[1] = Mth.sin(time * 0.7F) * 0.4F * live;
                }
            }
            case "run" -> {
                float k = Mth.sin(time * 1.4F);
                if (r.role().equals("leg_r")) {
                    v[0] = 0.9F * k * live;
                } else if (r.role().equals("leg_l")) {
                    v[0] = -0.9F * k * live;
                } else if (r.role().equals("arm_r")) {
                    v[0] = -0.5F * k * live;
                } else if (r.role().equals("arm_l")) {
                    v[0] = 0.5F * k * live;
                }
            }
            case "combo" -> {
                // the second cut back the other way
                if (u > 0.3F && u < 0.75F) {
                    float k = Mth.sin((u - 0.3F) / 0.45F * PI);
                    if (r.role().equals("arm_r")) {
                        v[1] = 2.0F * k;
                        v[0] = 0.4F * k;
                    } else if (r.role().equals("torso")) {
                        v[1] = 0.9F * k;
                    }
                }
            }
            default -> {
            }
        }
        return v;
    }

    private static float smooth(float u) {
        u = Mth.clamp(u, 0F, 1F);
        return u * u * (3F - 2F * u);
    }

    private static float outBack(float u) {
        u = Mth.clamp(u, 0F, 1F) - 1F;
        float c = 1.70158F;
        return 1F + (c + 1F) * u * u * u + c * u * u;
    }
}
