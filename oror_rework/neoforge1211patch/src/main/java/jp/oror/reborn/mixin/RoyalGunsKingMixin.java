package jp.oror.reborn.mixin;

import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.royal.RoyalRole;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** (054) In his third form the villager king puts his guns away for the two clubs of Baal (KingForms.arm). */
@Mixin(targets = "jp.oror.reborn.royal.RoyalGuns", remap = false)
public abstract class RoyalGunsKingMixin {
    @Shadow(remap = false)
    @Final
    private RoyalMob mob;

    @Inject(method = "enabled()Z", at = @At("RETURN"), cancellable = true, remap = false)
    private void oror$clubs(CallbackInfoReturnable<Boolean> cir) {
        if (cir.getReturnValueZ() && this.mob.role() == RoyalRole.KING && this.mob.lifePhase() >= 3) {
            cir.setReturnValue(false);
        }
    }
}
