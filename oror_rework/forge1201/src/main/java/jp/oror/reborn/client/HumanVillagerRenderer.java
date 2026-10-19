package jp.oror.reborn.client;

import com.mojang.blaze3d.vertex.PoseStack;
import jp.oror.reborn.RebornConfig;
import jp.oror.reborn.VillagerIndustry;
import jp.oror.reborn.VillagerRoles;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.HumanoidModel.ArmPose;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.VillagerRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider.Context;
import net.minecraft.client.renderer.entity.layers.HumanoidArmorLayer;
import net.minecraft.client.renderer.entity.layers.ItemInHandLayer;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.item.BowItem;
import net.minecraft.world.item.CrossbowItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

public final class HumanVillagerRenderer extends MobRenderer<Villager, HumanoidModel<Villager>> {
    private final VillagerRenderer vanilla;
    private static final String[] SKINS = new String[]{"steve", "efe", "kai", "noor", "zuri", "ari"};

    public HumanVillagerRenderer(Context context) {
        super(context, new HumanVillagerRenderer.HumanModel(context.bakeLayer(ModelLayers.PLAYER)), 0.5F);
        this.vanilla = new VillagerRenderer(context);
        this.addLayer(new HumanVillagerRenderer.Profession(this));
        this.addLayer(
            new HumanoidArmorLayer(
                this,
                new HumanoidModel(context.bakeLayer(ModelLayers.PLAYER_INNER_ARMOR)),
                new HumanoidModel(context.bakeLayer(ModelLayers.PLAYER_OUTER_ARMOR)),
                context.getModelManager()
            )
        );
        this.addLayer(new ItemInHandLayer(this, context.getItemInHandRenderer()));
    }

    public ResourceLocation getTextureLocation(Villager v) {
        return new ResourceLocation("textures/entity/player/wide/" + SKINS[Math.floorMod(v.getUUID().hashCode(), SKINS.length)] + ".png");
    }

    protected void scale(Villager v, PoseStack p, float partial) {
        float scale = v.isBaby() ? 0.5F : 1.0F;
        p.scale(scale, scale, scale);
    }

    public void render(Villager v, float yaw, float partial, PoseStack p, MultiBufferSource b, int light) {
        if (!(Boolean)RebornConfig.HUMAN_VILLAGERS.get()) {
            this.vanilla.render(v, yaw, partial, p, b, light);
        } else {
            super.render(v, yaw, partial, p, b, light);
        }
    }

    private static final class HumanModel extends HumanoidModel<Villager> {
        HumanModel(ModelPart root) {
            super(root);
        }

        public void setupAnim(Villager v, float walk, float speed, float age, float yaw, float pitch) {
            this.rightArmPose = ArmPose.EMPTY;
            this.leftArmPose = ArmPose.EMPTY;
            ItemStack item = v.getMainHandItem();
            if (item.getItem() instanceof BowItem) {
                this.rightArmPose = ArmPose.BOW_AND_ARROW;
            } else if (item.getItem() instanceof CrossbowItem) {
                this.rightArmPose = ArmPose.CROSSBOW_HOLD;
            } else if (v.isUsingItem() && v.getUseItem().is(Items.SHIELD)) {
                this.leftArmPose = ArmPose.BLOCK;
            } else if (!item.isEmpty()) {
                this.rightArmPose = ArmPose.ITEM;
            }

            super.setupAnim(v, walk, speed, age, yaw, pitch);
        }
    }

    /**
     * The trade's mark over the skin: a coloured apron, and for miners (v0.17.14) their work clothes instead - plaid shirt,
     * denim overalls, gloves and boots (miner.png, player skin layout, drawn over body, arms and legs) and a hard hat with a
     * headlamp that stays lit in the dark (miner_gear.png).
     */
    private static final class Profession extends RenderLayer<Villager, HumanoidModel<Villager>> {
        private final ModelPart apron;
        private final ModelPart hardHat;
        private final ModelPart lamp;
        private static final ResourceLocation TEX = new ResourceLocation("textures/block/white_concrete.png");
        private static final ResourceLocation MINER = new ResourceLocation("oror_supreme_bosses", "textures/entity/villager/human/miner.png");
        private static final ResourceLocation MINER_GEAR = new ResourceLocation("oror_supreme_bosses", "textures/entity/villager/human/miner_gear.png");
        private static final int FULL_BRIGHT = 15728880;

        Profession(HumanVillagerRenderer renderer) {
            super(renderer);
            MeshDefinition mesh = new MeshDefinition();
            mesh.getRoot().addOrReplaceChild("apron", CubeListBuilder.create().texOffs(0, 0).addBox(-4.0F, 7.0F, -2.13F, 8.0F, 5.0F, 0.15F), PartPose.ZERO);
            this.apron = LayerDefinition.create(mesh, 16, 16).bakeRoot().getChild("apron");
            // in head space (the head spans y -8..0); drawn scaled 1.06 so the shell clears the skin's hat layer
            MeshDefinition hat = new MeshDefinition();
            hat.getRoot().addOrReplaceChild("shell", CubeListBuilder.create().texOffs(0, 0).addBox(-4.5F, -9.0F, -4.5F, 9.0F, 4.0F, 9.0F), PartPose.ZERO);
            hat.getRoot().addOrReplaceChild("ridge", CubeListBuilder.create().texOffs(40, 0).addBox(-1.0F, -10.0F, -4.5F, 2.0F, 1.0F, 9.0F), PartPose.ZERO);
            hat.getRoot().addOrReplaceChild("rim", CubeListBuilder.create().texOffs(0, 14).addBox(-5.0F, -5.5F, -5.0F, 10.0F, 1.0F, 10.0F), PartPose.ZERO);
            hat.getRoot().addOrReplaceChild("peak", CubeListBuilder.create().texOffs(40, 14).addBox(-4.5F, -5.5F, -7.0F, 9.0F, 1.0F, 2.0F), PartPose.ZERO);
            hat.getRoot().addOrReplaceChild("lamp", CubeListBuilder.create().texOffs(40, 20).addBox(-1.5F, -8.5F, -5.5F, 3.0F, 2.0F, 1.0F), PartPose.ZERO);
            this.hardHat = LayerDefinition.create(hat, 64, 32).bakeRoot();
            MeshDefinition lens = new MeshDefinition();
            lens.getRoot().addOrReplaceChild("lens", CubeListBuilder.create().texOffs(50, 20).addBox(-1.0F, -8.0F, -5.75F, 2.0F, 1.0F, 0.25F), PartPose.ZERO);
            this.lamp = LayerDefinition.create(lens, 64, 32).bakeRoot().getChild("lens");
        }

        public void render(PoseStack p, MultiBufferSource b, int light, Villager v, float walk, float speed, float partial, float age, float yaw, float pitch) {
            if (!v.isBaby() && VillagerIndustry.miner(v)) {
                HumanoidModel<Villager> m = (HumanoidModel<Villager>)this.getParentModel();
                var clothes = b.getBuffer(RenderType.entityCutoutNoCull(MINER));
                for (ModelPart part : new ModelPart[]{m.body, m.rightArm, m.leftArm, m.rightLeg, m.leftLeg}) {
                    RigModel.render(part, p, clothes, light, OverlayTexture.NO_OVERLAY, -1);
                }
                if (v.getItemBySlot(EquipmentSlot.HEAD).isEmpty()) {
                    p.pushPose();
                    m.head.translateAndRotate(p);
                    p.scale(1.06F, 1.06F, 1.06F);
                    var gear = b.getBuffer(RenderType.entityCutoutNoCull(MINER_GEAR));
                    RigModel.render(this.hardHat, p, gear, light, OverlayTexture.NO_OVERLAY, -1);
                    RigModel.render(this.lamp, p, gear, FULL_BRIGHT, OverlayTexture.NO_OVERLAY, -1);
                    p.popPose();
                }
            } else if (!v.isBaby()) {
                p.pushPose();
                ((HumanoidModel)this.getParentModel()).body.translateAndRotate(p);
                RigModel.render(this.apron, p, b.getBuffer(RenderType.entityCutoutNoCull(TEX)), light, OverlayTexture.NO_OVERLAY, 0xFF000000 | VillagerRoles.color(v));
                p.popPose();
            }
        }
    }
}
