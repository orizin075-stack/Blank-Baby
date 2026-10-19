package jp.oror.reborn.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.renderer.ItemInHandRenderer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;

public final class MindHeldItems<T extends LivingEntity, M extends EntityModel<T>> extends RenderLayer<T, M> {
    private final ItemInHandRenderer items;
    private final boolean character;

    public MindHeldItems(RenderLayerParent<T, M> parent, ItemInHandRenderer items, boolean character) {
        super(parent);
        this.items = items;
        this.character = character;
    }

    public void render(PoseStack p, MultiBufferSource buffers, int light, T e, float swing, float amount, float tick, float age, float yaw, float pitch) {
        for (boolean left : new boolean[]{false, true}) {
            ItemStack stack = left ? e.getOffhandItem() : e.getMainHandItem();
            if (!stack.isEmpty()) {
                p.pushPose();
                boolean rigged = false;
                if (this.character && this.getParentModel() instanceof RigModel<?> model) {
                    rigged = model.translateToHand(p, left);
                    if (!rigged) {
                        p.translate(left ? -0.3 : 0.3, 0.8, 0.0);
                    }
                } else {
                    p.translate(left ? -0.22 : 0.22, 0.85, -0.2);
                }

                p.mulPose(Axis.XP.rotationDegrees(-90.0F));
                p.mulPose(Axis.YP.rotationDegrees(180.0F));
                p.translate(0.0, 0.05, rigged ? 0.0 : -0.42);
                this.items
                    .renderItem(
                        e, stack, left ? ItemDisplayContext.THIRD_PERSON_LEFT_HAND : ItemDisplayContext.THIRD_PERSON_RIGHT_HAND, left, p, buffers, light
                    );
                p.popPose();
            }
        }
    }
}
