package jp.oror.reborn.mixin;

import jp.oror.reborn.combat.Guns;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * (053) A royal with a gun in its hand neither parries nor blocks (the user: think whether they parry holding a gun). A
 * kingdom guard keeps its pistol at range and changes to its sword and shield within four blocks; until the sword is in
 * its hand, a blow lands.
 */
@Mixin(targets = "jp.oror.reborn.royal.RoyalMob", remap = false)
public abstract class RoyalGunGuardMixin {
    @Inject(method = "defend(Lnet/neoforged/neoforge/event/entity/living/LivingIncomingDamageEvent;)Z", at = @At("HEAD"), cancellable = true,
        remap = false)
    private void oror$noGuardWithGun(LivingIncomingDamageEvent e, CallbackInfoReturnable<Boolean> cir) {
        if (Guns.held(((net.minecraft.world.entity.LivingEntity) (Object) this).getMainHandItem())) {
            cir.setReturnValue(false);
        }
    }
}
