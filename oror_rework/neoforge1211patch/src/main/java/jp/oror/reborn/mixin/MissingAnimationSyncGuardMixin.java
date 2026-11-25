package jp.oror.reborn.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import yesman.epicfight.api.asset.AssetAccessor;
import yesman.epicfight.world.capabilities.entitypatch.LivingEntityPatch;

/**
 * (r77) The motion guard on the server's animator (MissingAnimationGuardMixin) kept the game up, but the same missing motion
 * was then sent to the players (Epic Fight's animator-control packet) and failed to encode, which dropped the player from
 * the world back to the title. A missing motion (Nightfall's, when Nightfall is not installed) is stopped where a mob is told
 * to play it, before anything is sent.
 */
@Mixin(value = LivingEntityPatch.class, remap = false)
public abstract class MissingAnimationSyncGuardMixin {
    @Inject(method = "playAnimationSynchronized(Lyesman/epicfight/api/asset/AssetAccessor;F)V", at = @At("HEAD"), cancellable = true, require = 0)
    private void oror$skipMissingSync(AssetAccessor<?> next, float transitionTime, CallbackInfo ci) {
        if (next == null) {
            ci.cancel();
        }
    }

    @Inject(method = "playAnimationInstantly(Lyesman/epicfight/api/asset/AssetAccessor;)V", at = @At("HEAD"), cancellable = true, require = 0)
    private void oror$skipMissingInstant(AssetAccessor<?> next, CallbackInfo ci) {
        if (next == null) {
            ci.cancel();
        }
    }

    @Inject(method = "reserveAnimation(Lyesman/epicfight/api/asset/AssetAccessor;)V", at = @At("HEAD"), cancellable = true, require = 0)
    private void oror$skipMissingReserve(AssetAccessor<?> next, CallbackInfo ci) {
        if (next == null) {
            ci.cancel();
        }
    }
}
