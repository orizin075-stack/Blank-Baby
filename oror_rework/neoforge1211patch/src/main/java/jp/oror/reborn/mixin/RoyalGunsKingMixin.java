package jp.oror.reborn.mixin;

import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.royal.RoyalRole;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** (054) From his first return the villager king puts his guns away: the hero's holy sword, then Baal's arms (KingForms.arm). */
@Mixin(targets = "jp.oror.reborn.royal.RoyalGuns", remap = false)
public abstract class RoyalGunsKingMixin {
    @Shadow(remap = false)
    @Final
    private RoyalMob mob;

    @Inject(method = "enabled()Z", at = @At("RETURN"), cancellable = true, remap = false)
    private void oror$clubs(CallbackInfoReturnable<Boolean> cir) {
        if (cir.getReturnValueZ() && this.mob.role() == RoyalRole.KING && this.mob.lifePhase() >= 1) {
            cir.setReturnValue(false);
        }
    }
}
