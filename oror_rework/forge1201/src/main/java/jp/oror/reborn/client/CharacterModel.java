package jp.oror.reborn.client;

import jp.oror.reborn.SupremeEntity;

/** Rig-driven model for the 41 supreme entities (and their alternate forms). */
public final class CharacterModel extends RigModel<SupremeEntity> {
    public CharacterModel(String key) {
        this(key, -1);
    }

    public CharacterModel(String key, int tint) {
        super(key, tint);
    }

    public void setupAnim(SupremeEntity e, float swing, float amount, float age, float yaw, float pitch) {
        float partial = age - (float)((int)age);
        this.animate(e, swing, amount, age, yaw, pitch, e.motion(), e.motionProgress(partial), e.action(), e.form());
    }
}
