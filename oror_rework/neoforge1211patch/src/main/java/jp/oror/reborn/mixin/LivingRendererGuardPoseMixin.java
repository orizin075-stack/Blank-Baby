package jp.oror.reborn.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import jp.oror.reborn.combat.client.GuardPoses;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.LivingEntityRenderer;
import net.minecraft.world.entity.LivingEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * (059e) Every mob drawn by Minecraft's renderers moves with its guard (GuardPoses): its model, once set up for the frame
 * (its walk, its swing, its head), is given the guard's pose before it and its layers (what it holds, its armour) are drawn.
 */
@Mixin(LivingEntityRenderer.class)
public abstract class LivingRendererGuardPoseMixin<T extends LivingEntity, M extends EntityModel<T>> {
    @Inject(method = "render(Lnet/minecraft/world/entity/LivingEntity;FFLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;I)V",
        at = @At(value = "INVOKE", target = "Lnet/minecraft/client/model/EntityModel;setupAnim(Lnet/minecraft/world/entity/Entity;FFFFF)V", shift = At.Shift.AFTER),
        require = 0)
    private void oror$guardPose(T entity, float yaw, float partial, PoseStack pose, MultiBufferSource buffers, int light, CallbackInfo ci) {
        GuardPoses.apply(((LivingEntityRenderer<?, ?>) (Object) this).getModel(), entity, partial, pose);
    }
}
