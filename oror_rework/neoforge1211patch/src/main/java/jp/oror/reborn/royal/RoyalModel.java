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
        this.hat.visible = wears.contains("hat");
        this.crown.visible = wears.contains("crown");
        this.crest.visible = wears.contains("crest");
        this.cape.visible = wears.contains("cape");
        this.rightPauldron.visible = this.leftPauldron.visible = wears.contains("pauldrons");

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
        swing(mob);
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
