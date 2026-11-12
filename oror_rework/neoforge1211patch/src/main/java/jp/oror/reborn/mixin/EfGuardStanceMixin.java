package jp.oror.reborn.mixin;

import jp.oror.reborn.combat.client.EfGuardStance;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * (059e) OROR's guard seen on the mobs Epic Fight draws (EfGuardStance): after the client animator's base layer has set
 * the mob's motions for the tick, and before the animator compares them with the last tick's to switch its animations.
 */
@Pseudo
@Mixin(targets = "yesman.epicfight.api.client.animation.ClientAnimator", remap = false)
public abstract class EfGuardStanceMixin {
    @Inject(method = "tick()V", at = @At(value = "INVOKE",
        target = "Lyesman/epicfight/api/client/animation/Layer;update(Lyesman/epicfight/world/capabilities/entitypatch/LivingEntityPatch;)V",
        shift = At.Shift.AFTER), require = 0, remap = false)
    private void oror$guardStance(CallbackInfo ci) {
        EfGuardStance.apply(this);
    }
}
