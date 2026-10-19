package jp.oror.reborn.client;

import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.VillagerModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.VillagerRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider.Context;
import net.minecraft.client.renderer.entity.layers.HumanoidArmorLayer;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.npc.Villager;

public final class VillagerArmor extends RenderLayer<Villager, VillagerModel<Villager>> {
    private final HumanoidModel<Villager> pose;
    private final HumanoidArmorLayer<Villager, HumanoidModel<Villager>, HumanoidModel<Villager>> armor;

    public VillagerArmor(final VillagerRenderer parent, Context context) {
        super(parent);
        this.pose = new HumanoidModel(context.bakeLayer(ModelLayers.PLAYER_OUTER_ARMOR));
        var bridge = new RenderLayerParent<Villager, HumanoidModel<Villager>>() {
            public HumanoidModel<Villager> getModel() {
                return VillagerArmor.this.pose;
            }

            public ResourceLocation getTextureLocation(Villager v) {
                return parent.getTextureLocation(v);
            }
        };
        this.armor = new HumanoidArmorLayer(
            bridge,
            new HumanoidModel(context.bakeLayer(ModelLayers.PLAYER_INNER_ARMOR)),
            new HumanoidModel(context.bakeLayer(ModelLayers.PLAYER_OUTER_ARMOR)),
            context.getModelManager()
        );
    }

    public void render(
        PoseStack stack, MultiBufferSource buffers, int light, Villager entity, float swing, float amount, float partial, float age, float yaw, float pitch
    ) {
        if (!entity.isBaby()) {
            this.pose.setupAnim(entity, swing, amount, age, yaw, pitch);
            this.pose.head.copyFrom(((VillagerModel)this.getParentModel()).getHead());
            this.pose.leftArm.xRot = this.pose.rightArm.xRot = -0.65F;
            this.armor.render(stack, buffers, light, entity, swing, amount, partial, age, yaw, pitch);
        }
    }
}
