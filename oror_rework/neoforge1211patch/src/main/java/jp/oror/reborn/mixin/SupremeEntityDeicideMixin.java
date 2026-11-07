package jp.oror.reborn.mixin;

import jp.oror.reborn.king.GodSlayer;
import net.minecraft.world.entity.LivingEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * (054) 神殺し: the gods' undying denied. An OROR being whose lore keeps it from death (LorePowers.IMMORTAL, its
 * revivals in die()) stays dead when a god-slayer was the last to strike it.
 */
@Mixin(targets = "jp.oror.reborn.SupremeEntity", remap = false)
public abstract class SupremeEntityDeicideMixin {
    @Inject(method = "immortal()Z", at = @At("HEAD"), cancellable = true, remap = false)
    private void oror$deicide(CallbackInfoReturnable<Boolean> cir) {
        LivingEntity self = (LivingEntity) (Object) this;
        if (GodSlayer.has(self.getLastHurtByMob()) || GodSlayer.has(self.getKillCredit())) {
            cir.setReturnValue(false);
        }
    }
}
