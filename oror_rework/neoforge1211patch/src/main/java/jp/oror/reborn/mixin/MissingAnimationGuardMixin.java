package jp.oror.reborn.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import yesman.epicfight.api.animation.ServerAnimator;
import yesman.epicfight.api.asset.AssetAccessor;

/**
 * (r77) The user's game crashed ("Ticking entity", nextAnimation is null) the moment a zombie struck: the pack's mob
 * patches (Indestructible's, for zombies, skeletons, pillagers and the rest) name Nightfall's attack motions (efn:...),
 * and without Nightfall installed (SETUP_NIGHTFALL.cmd not run) those motions are not there, so Epic Fight was asked to
 * play nothing and threw. A motion that is not there is now skipped (that one attack is not made) instead of ending the
 * game; it is logged once.
 */
@Mixin(value = ServerAnimator.class, remap = false)
public abstract class MissingAnimationGuardMixin {
    private static boolean oror$told;

    @Inject(method = "playAnimation(Lyesman/epicfight/api/asset/AssetAccessor;F)V", at = @At("HEAD"), cancellable = true, require = 0)
    private void oror$skipMissing(AssetAccessor<?> next, float transitionTime, CallbackInfo ci) {
        if (next == null) {
            if (!oror$told) {
                oror$told = true;
                System.out.println("[OROR] an Epic Fight motion that is not installed was asked for and skipped (is Nightfall installed? run SETUP_NIGHTFALL.cmd)");
            }
            ci.cancel();
        }
    }
}
