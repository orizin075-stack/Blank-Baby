package jp.oror.reborn.royal;

import java.util.EnumMap;
import java.util.Map;
import java.util.Set;
import net.minecraft.client.model.AnimationUtils;
import net.minecraft.client.model.ArmedModel;
import net.minecraft.client.model.HeadedModel;
import net.minecraft.client.model.HierarchicalModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ProjectileWeaponItem;

/**
 * The royals' model: a villager's head and long robe on a body with arms of its own (so a soldier swings his sword and
 * a mage raises his hands), with the crown, the helmet's crest, pauldrons and a cape each role wears. The boxes and
 * texture offsets are those of tools/royal_skins.py, which paints the 128 x 64 skins.
 */
public final class RoyalModel extends HierarchicalModel<RoyalMob> implements ArmedModel, HeadedModel {
    private static final Map<RoyalRole, Set<String>> WEARS = new EnumMap<>(RoyalRole.class);

    static {
        WEARS.put(RoyalRole.KING, Set.of("crown", "cape"));
        WEARS.put(RoyalRole.GENERAL, Set.of("hat", "crest", "pauldrons", "cape"));
        WEARS.put(RoyalRole.IMPERIAL, Set.of("hat", "crest", "pauldrons", "cape"));
        WEARS.put(RoyalRole.BODYGUARD, Set.of("hat", "pauldrons"));
        WEARS.put(RoyalRole.GUARD, Set.of("hat"));
        WEARS.put(RoyalRole.MAGE, Set.of("hat"));
        WEARS.put(RoyalRole.ARCHMAGE, Set.of("hat", "cape"));
        WEARS.put(RoyalRole.SAGE, Set.of("hat"));
    }

    private final ModelPart root, head, hat, crown, crest, body, cape, rightArm, leftArm, rightPauldron, leftPauldron, rightLeg, leftLeg;

    public RoyalModel(ModelPart root) {
        this.root = root;
        this.head = root.getChild("head");
        this.hat = this.head.getChild("hat");
        this.crown = this.head.getChild("crown");
        this.crest = this.head.getChild("crest");
        this.body = root.getChild("body");
        this.cape = this.body.getChild("cape");
        this.rightArm = root.getChild("right_arm");
        this.leftArm = root.getChild("left_arm");
        this.rightPauldron = this.rightArm.getChild("right_pauldron");
        this.leftPauldron = this.leftArm.getChild("left_pauldron");
        this.rightLeg = root.getChild("right_leg");
        this.leftLeg = root.getChild("left_leg");
    }

    public static LayerDefinition createLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        PartDefinition head = root.addOrReplaceChild("head", CubeListBuilder.create().texOffs(0, 0).addBox(-4F, -10F, -4F, 8F, 10F, 8F), PartPose.ZERO);
        head.addOrReplaceChild("nose", CubeListBuilder.create().texOffs(24, 0).addBox(-1F, -1F, -6F, 2F, 4F, 2F), PartPose.offset(0F, -2F, 0F));
        head.addOrReplaceChild("hat", CubeListBuilder.create().texOffs(32, 0).addBox(-4F, -10F, -4F, 8F, 10F, 8F, new CubeDeformation(0.45F)), PartPose.ZERO);
        head.addOrReplaceChild("crown", CubeListBuilder.create().texOffs(64, 0).addBox(-4.5F, -13F, -4.5F, 9F, 3F, 9F), PartPose.ZERO);
        head.addOrReplaceChild("crest", CubeListBuilder.create().texOffs(100, 0).addBox(-0.5F, -15F, -3F, 1F, 5F, 7F), PartPose.ZERO);
        PartDefinition body = root.addOrReplaceChild("body", CubeListBuilder.create().texOffs(0, 18).addBox(-4F, 0F, -3F, 8F, 12F, 6F), PartPose.ZERO);
        body.addOrReplaceChild("robe", CubeListBuilder.create().texOffs(28, 18).addBox(-4F, 0F, -3F, 8F, 20F, 6F, new CubeDeformation(0.5F)), PartPose.ZERO);
        body.addOrReplaceChild("cape", CubeListBuilder.create().texOffs(88, 30).addBox(-5F, 0F, 0F, 10F, 20F, 1F), PartPose.offset(0F, 0.5F, 3.6F));
        PartDefinition rightArm = root.addOrReplaceChild("right_arm", CubeListBuilder.create().texOffs(56, 18).addBox(-3F, -2F, -2F, 4F, 12F, 4F), PartPose.offset(-5F, 2F, 0F));
        PartDefinition leftArm = root.addOrReplaceChild("left_arm", CubeListBuilder.create().texOffs(72, 18).addBox(-1F, -2F, -2F, 4F, 12F, 4F), PartPose.offset(5F, 2F, 0F));
        rightArm.addOrReplaceChild("right_pauldron", CubeListBuilder.create().texOffs(88, 12).addBox(-3.5F, -2.6F, -2.5F, 5F, 4F, 5F, new CubeDeformation(0.1F)), PartPose.ZERO);
        leftArm.addOrReplaceChild("left_pauldron", CubeListBuilder.create().texOffs(108, 12).addBox(-1.5F, -2.6F, -2.5F, 5F, 4F, 5F, new CubeDeformation(0.1F)), PartPose.ZERO);
        root.addOrReplaceChild("right_leg", CubeListBuilder.create().texOffs(56, 34).addBox(-2F, 0F, -2F, 4F, 12F, 4F), PartPose.offset(-2F, 12F, 0F));
        root.addOrReplaceChild("left_leg", CubeListBuilder.create().texOffs(72, 34).addBox(-2F, 0F, -2F, 4F, 12F, 4F), PartPose.offset(2F, 12F, 0F));
        return LayerDefinition.create(mesh, 128, 64);
    }

    @Override
    public ModelPart root() {
        return this.root;
    }

    @Override
    public ModelPart getHead() {
        return this.head;
    }

    @Override
    public void setupAnim(RoyalMob mob, float walk, float walkAmount, float age, float yaw, float pitch) {
        this.root.getAllParts().forEach(ModelPart::resetPose);
        Set<String> wears = WEARS.getOrDefault(mob.role(), Set.of());
        // (054) the king's forms: pauldrons from his first return, a crest (of flame, of light) from his second
        int form = mob.role() == RoyalRole.KING ? mob.lifePhase() : 0;
        this.hat.visible = wears.contains("hat");
        this.crown.visible = wears.contains("crown");
        this.crest.visible = wears.contains("crest") || form >= 2;
        this.cape.visible = wears.contains("cape");
        this.rightPauldron.visible = this.leftPauldron.visible = wears.contains("pauldrons") || form >= 1;

        this.head.yRot = yaw * Mth.DEG_TO_RAD;
        this.head.xRot = pitch * Mth.DEG_TO_RAD;
        float stride = walk * 0.6662F;
        this.rightLeg.xRot = Mth.cos(stride) * 1.4F * walkAmount * 0.5F;
        this.leftLeg.xRot = Mth.cos(stride + Mth.PI) * 1.4F * walkAmount * 0.5F;
        this.rightArm.xRot = Mth.cos(stride + Mth.PI) * 2.0F * walkAmount * 0.5F;
        this.leftArm.xRot = Mth.cos(stride) * 2.0F * walkAmount * 0.5F;
        this.cape.xRot = 0.08F + walkAmount * 0.7F;

        if (this.riding) {
            this.rightArm.xRot = -0.63F;
            this.leftArm.xRot = -0.63F;
            this.rightLeg.xRot = -1.4137167F;
            this.rightLeg.yRot = Mth.PI / 10F;
            this.rightLeg.zRot = 0.07853982F;
            this.leftLeg.xRot = -1.4137167F;
            this.leftLeg.yRot = -Mth.PI / 10F;
            this.leftLeg.zRot = -0.07853982F;
            this.cape.xRot = 0.5F;
        }

        ItemStack main = mob.getMainHandItem(), off = mob.getOffhandItem();
        boolean casting = mob.isCasting();
        if (casting) {
            // both hands raised, as an illager casts
            this.rightArm.xRot = Mth.cos(age * 0.6662F) * 0.25F;
            this.leftArm.xRot = Mth.cos(age * 0.6662F) * 0.25F;
            this.rightArm.zRot = Mth.PI * 0.75F;
            this.leftArm.zRot = -Mth.PI * 0.75F;
        } else if (mob.isAggressive() && shoots(main)) {
            // a gun or a bow levelled at the enemy with both hands
            this.rightArm.yRot = -0.1F + this.head.yRot;
            this.leftArm.yRot = 0.1F + this.head.yRot + 0.4F;
            this.rightArm.xRot = -Mth.HALF_PI + this.head.xRot;
            this.leftArm.xRot = -Mth.HALF_PI + this.head.xRot;
        } else {
            if (!main.isEmpty()) {
                this.rightArm.xRot = this.rightArm.xRot * 0.5F - Mth.PI / 10F;
            }
            if (!off.isEmpty()) {
                this.leftArm.xRot = this.leftArm.xRot * 0.5F - Mth.PI / 10F;
            }
            if (mob.isAggressive() && !main.isEmpty() && this.attackTime <= 0F) {
                // sword ready, held out in front
                this.rightArm.xRot = -0.9F + Mth.cos(age * 0.09F) * 0.05F;
                this.rightArm.yRot = -0.15F;
            }
            AnimationUtils.bobArms(this.rightArm, this.leftArm, age);
        }
        roleStyle(mob, walkAmount, age, casting);
        swing(mob);
        roleSwing(mob);
        react(mob, age);
        kingMove(mob, age);
    }

    /**
     * (059d) V20 07_royal_roles_8.md, each role's bearing. The general looks over his men at rest with his sword's
     * point lowered, and gives his orders with the sword arm raised high and swept forward over the line (not with a
     * mage's two raised hands). The bodyguard and the imperial guard hold their shields before them in a fight; the
     * guard on his rounds turns his head now one way, now the other, and looks about when he stops. The mage casts from
     * one hand reached toward the foe, the other hand held back; the archmage with both hands forward, turning slowly
     * over the circles at his feet (RoyalRoleFx); the sage with the palm before the chest, the fingers' small work, the
     * head a little bowed.
     */
    private void roleStyle(RoyalMob mob, float walkAmount, float age, boolean casting) {
        boolean fighting = mob.isAggressive();
        boolean shield = mob.getOffhandItem().getItem() instanceof net.minecraft.world.item.ShieldItem;
        float still = 1F - Math.min(1F, walkAmount * 2F);
        boolean armed = !mob.getMainHandItem().isEmpty();
        switch (mob.role()) {
            case GENERAL -> {
                if (casting) {
                    float c = 0.5F + 0.5F * Mth.sin(age * 0.18F);
                    this.rightArm.zRot = 0.1F;
                    this.rightArm.xRot = Mth.lerp(c, -2.9F, -1.35F);
                    this.leftArm.zRot = -0.45F;
                    this.leftArm.xRot = 0.15F;
                    this.head.xRot -= 0.2F * (1F - c);
                } else if (!fighting) {
                    this.head.yRot += Mth.sin(age * 0.035F) * 0.55F * still;
                    if (armed) {
                        this.rightArm.xRot = 0.12F + this.rightArm.xRot * 0.3F;
                        this.rightArm.zRot = 0.08F;
                    }
                }
            }
            case BODYGUARD, IMPERIAL -> {
                if (casting) {
                    this.rightArm.zRot = 0.1F;
                    this.leftArm.zRot = -0.1F;
                    this.rightArm.xRot = -2.4F + Mth.sin(age * 0.2F) * 0.2F;
                    this.leftArm.xRot = shield ? -1.0F : -0.3F;
                } else if (fighting && shield) {
                    this.leftArm.xRot = -1.05F;
                    this.leftArm.yRot = 0.55F;
                    this.leftArm.zRot = 0F;
                }
                if (mob.role() == RoyalRole.IMPERIAL && fighting) {
                    // the weight of the armour: a lower stance
                    this.body.xRot += 0.08F;
                    this.head.xRot -= 0.08F;
                }
            }
            case GUARD -> {
                if (casting) {
                    this.rightArm.zRot = 0.1F;
                    this.leftArm.zRot = -0.1F;
                    this.rightArm.xRot = -2.2F;
                } else if (fighting) {
                    if (shield) {
                        this.leftArm.xRot = -0.9F;
                        this.leftArm.yRot = 0.4F;
                    }
                } else {
                    float look = Mth.sin(age * 0.045F) + 0.35F * Mth.sin(age * 0.11F);
                    this.head.yRot += look * (0.25F + 0.45F * still);
                }
            }
            case MAGE -> {
                if (casting) {
                    float tremble = Mth.sin(age * 0.9F) * 0.03F;
                    this.rightArm.zRot = 0F;
                    this.rightArm.xRot = -Mth.HALF_PI + this.head.xRot + tremble;
                    this.rightArm.yRot = this.head.yRot - 0.1F;
                    this.leftArm.zRot = -0.35F;
                    this.leftArm.xRot = -0.45F;
                    this.leftArm.yRot = 0.2F;
                }
            }
            case ARCHMAGE -> {
                if (casting) {
                    float turn = Mth.sin(age * 0.25F) * 0.18F;
                    this.rightArm.zRot = 0.25F;
                    this.leftArm.zRot = -0.25F;
                    this.rightArm.xRot = -1.95F + turn;
                    this.leftArm.xRot = -1.95F - turn;
                    this.rightArm.yRot = this.head.yRot - 0.25F;
                    this.leftArm.yRot = this.head.yRot + 0.25F;
                    this.head.xRot += 0.15F;
                }
            }
            case SAGE -> {
                if (casting) {
                    float work = Mth.sin(age * 0.8F) * 0.04F;
                    this.rightArm.zRot = 0.05F;
                    this.rightArm.xRot = -1.15F + work;
                    this.rightArm.yRot = -0.3F + work;
                    this.leftArm.zRot = -0.1F;
                    this.leftArm.xRot = armed ? -0.55F : -0.25F;
                    this.head.xRot += 0.18F;
                }
            }
            default -> {
            }
        }
    }

    /**
     * (059d) The blow by role: the general steps in on his right foot as he cuts; the bodyguard thrusts short and
     * straight; the imperial guard's lunge is short and heavy, the body behind it; the rest swing as before.
     */
    private void roleSwing(RoyalMob mob) {
        if (this.attackTime <= 0F || this.riding) {
            return;
        }
        float s = Mth.sin(this.attackTime * Mth.PI);
        switch (mob.role()) {
            case GENERAL -> {
                this.rightLeg.xRot = -0.6F * s;
                this.leftLeg.xRot = 0.35F * s;
                this.body.xRot += 0.12F * s;
            }
            case BODYGUARD -> {
                this.rightArm.xRot = Mth.lerp(s, -1.0F, -1.6F);
                this.rightArm.yRot = -0.05F;
                this.rightArm.zRot = 0F;
                this.rightArm.z -= 2.5F * s;
                this.body.yRot *= 0.3F;
            }
            case IMPERIAL -> {
                this.body.xRot += 0.25F * s;
                this.rightLeg.xRot = -0.5F * s;
                this.leftLeg.xRot = 0.2F * s;
                this.root.z -= 1.5F * s;
            }
            default -> {
            }
        }
    }

    /**
     * (054) The villager king's deeds in his forms (KingForms, TechniqueShow "move:king_..."), each its own motion:
     * his return (kneeling, then rising with the arms flung wide and the head thrown back), the rally (the right arm
     * raised high, then swept forward), the hellfire ring (the arms crossed at the chest, then flung out), the leap (a
     * crouch, then a spring), the thunder (both arms raised to the sky, then the right brought down at the enemy), the
     * flies (the arms spread, palms up, swaying, then thrust forward) and the clubs (both raised over the head, then
     * brought down together). A windup, a snap at the moment it goes off, held, then eased home.
     */
    private void kingMove(RoyalMob mob, float age) {
        if (mob.role() != RoyalRole.KING) {
            return;
        }
        jp.oror.reborn.show.TechniqueShow.Active show = jp.oror.reborn.show.TechniqueShow.ACTIVE.get(mob.getId());
        if (show == null || !show.mechanic().startsWith("MOVE_KING_")) {
            return;
        }
        float time = mob.level().getGameTime() - show.start() + (age - (float) ((int) age));
        float len = Math.max(1, show.length());
        float u = time / len;
        if (u < 0 || u > 1) {
            return;
        }
        float wind = Math.max(1, show.windup()) / len;
        // 0..1 through the windup, then the strike's snap, eased home over the last third
        float a = u < wind ? u / wind : 1F;
        float b = u < wind ? 0F : Math.min(1F, (u - wind) / Math.max(0.05F, (1F - wind) * 0.25F));
        float out = u > 0.7F ? 1F - (u - 0.7F) / 0.3F : 1F;
        a = a * a * (3F - 2F * a) * out;
        b = b * b * (3F - 2F * b) * out;
        switch (show.mechanic()) {
            case "MOVE_KING_REVIVE" -> {
                this.root.y += 6F * a * (1F - b);
                this.head.xRot = Mth.lerp(b, this.head.xRot + 0.6F * a, -0.7F);
                this.rightArm.zRot = Mth.lerp(b, 0.2F * a, 1.6F);
                this.leftArm.zRot = Mth.lerp(b, -0.2F * a, -1.6F);
                this.rightArm.xRot = Mth.lerp(b, -0.3F * a, -0.4F);
                this.leftArm.xRot = Mth.lerp(b, -0.3F * a, -0.4F);
                this.body.xRot = Mth.lerp(b, 0.5F * a, -0.25F);
            }
            case "MOVE_KING_RALLY" -> {
                this.rightArm.xRot = Mth.lerp(b, -2.9F * a, -1.4F);
                this.rightArm.zRot = Mth.lerp(b, 0.2F * a, -0.1F);
                this.leftArm.zRot = -0.3F * a;
                this.head.xRot -= 0.3F * a;
            }
            case "MOVE_KING_FLAME" -> {
                this.rightArm.xRot = Mth.lerp(b, -1.2F * a, -1.3F);
                this.leftArm.xRot = Mth.lerp(b, -1.2F * a, -1.3F);
                this.rightArm.yRot = Mth.lerp(b, -0.9F * a, 0.8F);
                this.leftArm.yRot = Mth.lerp(b, 0.9F * a, -0.8F);
                this.rightArm.zRot = Mth.lerp(b, 0F, 1.2F);
                this.leftArm.zRot = Mth.lerp(b, 0F, -1.2F);
                this.body.xRot += 0.2F * a * (1F - b);
            }
            case "MOVE_KING_BLINK" -> {
                this.root.y += 4F * a * (1F - b);
                this.body.xRot += 0.5F * a * (1F - b);
                this.rightArm.xRot = Mth.lerp(b, 0.4F * a, -2.6F);
                this.leftArm.xRot = Mth.lerp(b, 0.4F * a, -2.6F);
            }
            case "MOVE_KING_STORM" -> {
                this.rightArm.xRot = Mth.lerp(b, -3.0F * a, -1.6F + this.head.xRot);
                this.leftArm.xRot = Mth.lerp(b, -3.0F * a, -0.3F);
                this.rightArm.zRot = Mth.lerp(b, 0.25F * a, 0F);
                this.leftArm.zRot = Mth.lerp(b, -0.25F * a, -0.6F);
                this.head.xRot = Mth.lerp(a * (1F - b), this.head.xRot, -0.8F);
                this.body.xRot -= 0.15F * a * (1F - b);
            }
            case "MOVE_KING_SWARM" -> {
                float sway = Mth.sin(age * 0.5F) * 0.25F * a;
                this.rightArm.zRot = Mth.lerp(b, 1.3F * a, 0.3F);
                this.leftArm.zRot = Mth.lerp(b, -1.3F * a, -0.3F);
                this.rightArm.xRot = Mth.lerp(b, -0.6F * a + sway, -1.55F);
                this.leftArm.xRot = Mth.lerp(b, -0.6F * a - sway, -1.55F);
                this.body.yRot += sway;
                this.head.xRot -= 0.25F * a;
            }
            case "MOVE_KING_SLAM" -> {
                this.rightArm.xRot = Mth.lerp(b, -3.1F * a, -0.4F);
                this.leftArm.xRot = Mth.lerp(b, -3.1F * a, -0.4F);
                this.body.xRot = Mth.lerp(b, -0.3F * a, 0.55F);
                this.root.y += 3F * b;
                this.head.xRot += 0.3F * b;
            }
            default -> {
            }
        }
    }

    /**
     * (052) A guard's moment (MobGuard, TechniqueShow): a parry sweeps the sword up and out across the blow (a shield
     * thrown up into it), a block crosses the arms and sinks under it, a broken guard flings the arms wide and arches
     * back, a parried royal is thrown back with the sword knocked high. In a second's snap, held, then eased home.
     */
    private void react(RoyalMob mob, float age) {
        jp.oror.reborn.show.TechniqueShow.Active show = jp.oror.reborn.show.TechniqueShow.REACT.get(mob.getId());
        if (show == null) {
            return;
        }
        float time = mob.level().getGameTime() - show.start() + (age - (float) ((int) age));
        float u = time / Math.max(1, show.length());
        if (u < 0 || u > 1) {
            return;
        }
        float w = u < 0.12F ? u / 0.12F : u < 0.45F ? 1F : 1F - (u - 0.45F) / 0.55F;
        if (show.mechanic().equals("GUARD")) {
            // (059f) the guard raised: up in two ticks and a half, held, lowered in the last three
            float len = Math.max(1, show.length());
            w = Math.min(Mth.clamp(time / 2.5F, 0F, 1F), Mth.clamp((len - time) / 3F, 0F, 1F));
        }
        w = w * w * (3F - 2F * w);
        boolean shield = mob.getOffhandItem().getItem() instanceof net.minecraft.world.item.ShieldItem;
        switch (show.mechanic()) {
            case "GUARD" -> {
                // (059f) the guard raised: the shield lifted before the body, or the sword brought across it, blade up
                if (shield) {
                    this.leftArm.xRot = Mth.lerp(w, this.leftArm.xRot, -1.4F);
                    this.leftArm.yRot = Mth.lerp(w, this.leftArm.yRot, 0.5F);
                    this.rightArm.xRot = Mth.lerp(w, this.rightArm.xRot, -0.55F);
                } else {
                    this.rightArm.xRot = Mth.lerp(w, this.rightArm.xRot, -1.0F);
                    this.rightArm.yRot = Mth.lerp(w, this.rightArm.yRot, -0.6F);
                    this.leftArm.xRot = Mth.lerp(w, this.leftArm.xRot, -0.45F);
                    this.leftArm.yRot = Mth.lerp(w, this.leftArm.yRot, 0.2F);
                }
                this.head.xRot += 0.15F * w;
            }
            case "PARRY" -> {
                if (shield) {
                    this.leftArm.xRot = Mth.lerp(w, this.leftArm.xRot, -1.75F);
                    this.leftArm.yRot = Mth.lerp(w, this.leftArm.yRot, 0.6F);
                    this.rightArm.xRot = Mth.lerp(w, this.rightArm.xRot, -0.6F);
                } else {
                    this.rightArm.xRot = Mth.lerp(w, this.rightArm.xRot, -2.3F);
                    this.rightArm.yRot = Mth.lerp(w, this.rightArm.yRot, 0.9F);
                    this.rightArm.zRot = Mth.lerp(w, this.rightArm.zRot, 0.5F);
                    this.body.yRot += 0.4F * w;
                }
                this.head.xRot -= 0.15F * w;
            }
            case "BLOCK" -> {
                if (shield) {
                    this.leftArm.xRot = Mth.lerp(w, this.leftArm.xRot, -1.55F);
                    this.leftArm.yRot = Mth.lerp(w, this.leftArm.yRot, 0.5F);
                } else {
                    this.rightArm.xRot = Mth.lerp(w, this.rightArm.xRot, -1.45F);
                    this.rightArm.yRot = Mth.lerp(w, this.rightArm.yRot, -0.65F);
                    this.leftArm.xRot = Mth.lerp(w, this.leftArm.xRot, -1.45F);
                    this.leftArm.yRot = Mth.lerp(w, this.leftArm.yRot, 0.65F);
                }
                this.root.y += 0.8F * w;
            }
            case "BREAK" -> {
                this.rightArm.xRot = Mth.lerp(w, this.rightArm.xRot, -2.6F);
                this.rightArm.zRot = Mth.lerp(w, this.rightArm.zRot, 0.7F);
                this.leftArm.xRot = Mth.lerp(w, this.leftArm.xRot, -2.6F);
                this.leftArm.zRot = Mth.lerp(w, this.leftArm.zRot, -0.7F);
                this.head.xRot -= 0.5F * w;
                this.body.xRot -= 0.3F * w;
            }
            case "PARRIED" -> {
                this.rightArm.xRot = Mth.lerp(w, this.rightArm.xRot, -2.5F);
                this.rightArm.yRot = Mth.lerp(w, this.rightArm.yRot, 0.4F);
                this.leftArm.zRot = Mth.lerp(w, this.leftArm.zRot, -0.6F);
                this.head.xRot -= 0.3F * w;
                this.body.xRot -= 0.25F * w;
            }
            default -> {
            }
        }
    }

    private static boolean shoots(ItemStack stack) {
        return stack.getItem() instanceof ProjectileWeaponItem || stack.getItem().getClass().getName().contains("GunItem");
    }

    /** The swing of the arm that struck, the body turning into the blow (as a player's or a zombie's). */
    private void swing(RoyalMob mob) {
        if (this.attackTime <= 0F) {
            return;
        }
        HumanoidArm side = mob.getMainArm();
        ModelPart arm = side == HumanoidArm.LEFT ? this.leftArm : this.rightArm;
        float t = this.attackTime;
        this.body.yRot = Mth.sin(Mth.sqrt(t) * Mth.TWO_PI) * 0.2F * (side == HumanoidArm.LEFT ? -1F : 1F);
        this.rightArm.z = Mth.sin(this.body.yRot) * 5.0F;
        this.rightArm.x = -Mth.cos(this.body.yRot) * 5.0F;
        this.leftArm.z = -Mth.sin(this.body.yRot) * 5.0F;
        this.leftArm.x = Mth.cos(this.body.yRot) * 5.0F;
        this.rightArm.yRot += this.body.yRot;
        this.leftArm.yRot += this.body.yRot;
        this.leftArm.xRot += this.body.yRot;
        float f = 1.0F - t;
        f *= f;
        f *= f;
        f = 1.0F - f;
        float lift = Mth.sin(f * Mth.PI);
        float down = Mth.sin(t * Mth.PI) * -(this.head.xRot - 0.7F) * 0.75F;
        arm.xRot -= lift * 1.2F + down;
        arm.yRot += this.body.yRot * 2.0F;
        arm.zRot += Mth.sin(t * Mth.PI) * -0.4F;
    }

    @Override
    public void translateToHand(HumanoidArm side, com.mojang.blaze3d.vertex.PoseStack pose) {
        this.root.translateAndRotate(pose);
        (side == HumanoidArm.LEFT ? this.leftArm : this.rightArm).translateAndRotate(pose);
    }
}
