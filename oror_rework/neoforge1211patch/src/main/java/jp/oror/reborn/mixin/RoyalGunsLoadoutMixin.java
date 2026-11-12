package jp.oror.reborn.mixin;

import jp.oror.reborn.royal.RoyalArmory;
import jp.oror.reborn.royal.RoyalGuns;
import jp.oror.reborn.royal.RoyalMob;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Constant;
import org.spongepowered.asm.mixin.injection.ModifyConstant;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * (052) A kingdom guard changes weapons as the fight needs (RoyalArmory): his guns' tick stands aside while he holds
 * his sword or his bow, and shoots his pistol when he holds that. (059e) And his rifle, out to 72 blocks (a guard's
 * guns shoot within 18).
 */
@Mixin(value = RoyalGuns.class, remap = false)
public abstract class RoyalGunsLoadoutMixin {
    @Shadow
    @Final
    private RoyalMob mob;

    @Shadow
    private String selected;

    @Inject(method = "tick", at = @At("HEAD"), cancellable = true, remap = false)
    private void oror$loadout(CallbackInfo ci) {
        String arm = RoyalArmory.tick(this.mob, (RoyalGuns) (Object) this);
        if (arm == null) {
            return;
        }
        if (arm.isEmpty()) {
            ci.cancel();
        } else {
            this.selected = arm;
        }
    }

    @ModifyConstant(method = "tick", constant = @Constant(intValue = 18), require = 0, remap = false)
    private int oror$rifleRange(int range) {
        return "rifle".equals(RoyalArmory.arm(this.mob)) ? 72 : range;
    }
}
