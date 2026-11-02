package jp.oror.reborn.client;

import java.lang.reflect.Field;
import jp.oror.reborn.SupremeEntity;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.util.Mth;

/**
 * The characters' rig, posed by RigModel's motions. (052) A motion used to run as one smooth swell, sin(pi t) over its
 * whole length: no drawing back before the blow, its height a fifth of a second after the blow had already landed (the
 * ability goes off at the end of the windup, 24 ticks before the motion ends), and an even ease back. Now the motion's
 * time is reshaped before RigModel reads it: the body draws back the other way through the windup, whips through to the
 * full pose on the tick the ability goes off (a touch past it, and back), holds it a moment, and eases home.
 */
public final class CharacterModel extends RigModel<SupremeEntity> {
    private static Field durationField;
    private static boolean durationLooked;

    public CharacterModel(String key) {
        this(key, -1);
    }

    public CharacterModel(String key, int tint) {
        super(key, tint);
    }

    @Override
    public void setupAnim(SupremeEntity e, float swing, float amount, float age, float yaw, float pitch) {
        float partial = age - (float) ((int) age);
        // (052) a guard's moment (a parry, a block, the guard broken, parried): its pose for its half second, over
        // whatever else the character was doing (a technique under way goes on afterwards)
        jp.oror.reborn.show.TechniqueShow.Active react = jp.oror.reborn.show.TechniqueShow.REACT.get(e.getId());
        if (react != null) {
            float time = e.level().getGameTime() - react.start() + partial;
            if (time >= 0 && time <= react.length()) {
                this.animate(e, swing, amount, age, yaw, pitch, 0, 0F, e.action(), e.form());
                jp.oror.reborn.show.TechniquePoses.apply(this, react, time);
                return;
            }
        }
        // (052) a technique or a big move under way: its own dance (TechniquePoses) over the rig's idle and walk,
        // instead of the shared motion its windup was given
        jp.oror.reborn.show.TechniqueShow.Active show = jp.oror.reborn.show.TechniqueShow.ACTIVE.get(e.getId());
        if (show != null) {
            float time = e.level().getGameTime() - show.start() + partial;
            if (time >= 0 && time <= show.length()) {
                this.animate(e, swing, amount, age, yaw, pitch, 0, 0F, e.action(), e.form());
                jp.oror.reborn.show.TechniquePoses.apply(this, show, time);
                return;
            }
        }
        int motion = e.motion();
        float progress = e.motionProgress(partial);
        if (motion != 0) {
            progress = shape(progress, strike(e));
        }
        this.animate(e, swing, amount, age, yaw, pitch, motion, progress, e.action(), e.form());
    }

    /** Where in the motion the ability goes off: the windup is the motion's length less 24 ticks. */
    private static float strike(SupremeEntity e) {
        int duration = 40;
        try {
            if (!durationLooked) {
                durationLooked = true;
                durationField = SupremeEntity.class.getDeclaredField("MOTION_DURATION");
                durationField.setAccessible(true);
            }
            if (durationField != null) {
                @SuppressWarnings("unchecked")
                EntityDataAccessor<Integer> key = (EntityDataAccessor<Integer>) durationField.get(null);
                duration = Math.max(1, e.getEntityData().get(key));
            }
        } catch (ReflectiveOperationException | RuntimeException ex) {
            durationField = null;
        }
        return Mth.clamp((duration - 24) / (float) duration, 0.08F, 0.6F);
    }

    /**
     * The motion's time as RigModel should see it. RigModel's swell is sin(pi t): below 0 it runs the other way (the
     * drawing back), 0.5 is the full pose, 1 is rest again.
     */
    static float shape(float t, float strike) {
        float windEnd = strike * 0.85F;
        float hitEnd = Math.min(strike + 0.08F, 0.95F);
        float holdEnd = Math.min(hitEnd + 0.12F, 0.97F);
        float back = -0.14F;
        if (t < windEnd) {
            return back * smooth(t / windEnd);
        }
        if (t < hitEnd) {
            return back + (0.5F - back) * outBack((t - windEnd) / (hitEnd - windEnd));
        }
        if (t < holdEnd) {
            return 0.5F;
        }
        return 0.5F + 0.5F * smooth((t - holdEnd) / (1.0F - holdEnd));
    }

    private static float smooth(float u) {
        u = Mth.clamp(u, 0F, 1F);
        return u * u * (3F - 2F * u);
    }

    /** Out fast, a little past the mark and back to it. */
    private static float outBack(float u) {
        u = Mth.clamp(u, 0F, 1F) - 1F;
        float c = 1.70158F;
        return 1F + (c + 1F) * u * u * u + c * u * u;
    }
}
