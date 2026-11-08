package jp.oror.reborn.royal;

import java.lang.reflect.Field;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import jp.oror.reborn.client.RigModel;
import jp.oror.reborn.king.KingMotions;
import jp.oror.reborn.show.TechniqueShow;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.world.entity.monster.Evoker;

/**
 * (056) Azazel's rig (tools/mc/azazel3d.py) on the evoker he is: RigModel's idle and walk; both arms raised while he
 * casts an evoker's spell (his fangs, his vexes); his own ten arts' motions (TechniqueShow "move:azazel_*",
 * KingMotions "azazel_*", played as KingRig plays the king's).
 */
public final class AzazelRig extends RigModel<Evoker> {
    private static final float[] NO_HOLD = {0F, 0F, 0F, 0F};
    private static Field partsField;
    private final Map<String, ModelPart> named = new HashMap<>();

    @SuppressWarnings("unchecked")
    public AzazelRig() {
        super("azazel", -1);
        try {
            if (partsField == null) {
                partsField = RigModel.class.getDeclaredField("parts");
                partsField.setAccessible(true);
            }
            this.named.putAll((Map<String, ModelPart>) partsField.get(this));
        } catch (ReflectiveOperationException | RuntimeException ex) {
            // drawn still, only without his motions
        }
    }

    private void add(String part, float x, float y, float z) {
        ModelPart m = this.named.get(part);
        if (m != null) {
            m.xRot += x;
            m.yRot += y;
            m.zRot += z;
        }
    }

    @Override
    public void setupAnim(Evoker e, float swing, float amount, float age, float yaw, float pitch) {
        this.animate(e, swing, amount, age, yaw, pitch, 0, 0F, 0, 0);
        if (e.isCastingSpell()) {
            float bob = (float) Math.sin(age * 0.6F) * 0.15F;
            add("arm_r", -2.5F + bob, 0F, 0.45F);
            add("arm_l", -2.5F - bob, 0F, -0.45F);
            add("head", -0.3F, 0F, 0F);
        }
        TechniqueShow.Active show = TechniqueShow.ACTIVE.get(e.getId());
        if (show == null || !show.mechanic().startsWith("MOVE_AZAZEL_")) {
            return;
        }
        KingMotions.Motion mo = KingMotions.get(show.mechanic().substring(5).toLowerCase(Locale.ROOT));
        if (mo == null) {
            return;
        }
        float partial = age - (float) ((int) age);
        int len = Math.max(1, show.length());
        float t = e.level().getGameTime() - show.start() + partial;
        if (t < 0F || t > len) {
            return;
        }
        play(KingRig.motion(mo, t, show.windup(), len, NO_HOLD));
    }

    private void play(float[] v) {
        add("arm_r", v[0], v[1], v[2]);
        add("arm_l", v[3], v[4], v[5]);
        add("torso", v[6], v[7], v[19]);
        add("head", v[8], v[20], v[21]);
        ModelPart root = this.named.get("root");
        if (root != null) {
            root.y += v[9];
        }
        add("fore_r", v[10], 0, 0);
        add("fore_l", v[11], 0, 0);
        add("sword", v[12], 0, 0);
        add("leg_r", v[14], 0, 0);
        add("leg_l", v[15], 0, 0);
        add("shin_r", v[16], 0, 0);
        add("shin_l", v[17], 0, 0);
        add("hips", 0, v[18], 0);
    }
}
