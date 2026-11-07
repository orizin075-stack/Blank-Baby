package jp.oror.reborn.mixin;

import jp.oror.reborn.AdaptiveCombat;
import jp.oror.reborn.combat.MeleeNatives;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** (053) Hand-to-hand monsters choose their weapon as if their target were no further than eight blocks (MeleeNatives). */
@Mixin(targets = "jp.oror.reborn.AdaptiveCombat", remap = false)
public abstract class AdaptiveMeleeMixin {
    @Inject(method = "select(Lnet/minecraft/world/entity/Mob;Lnet/minecraft/world/entity/LivingEntity;D)Ljava/lang/String;",
        at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$closeIn(Mob m, LivingEntity t, double distance, CallbackInfoReturnable<String> cir) {
        if (distance > 8.0 && MeleeNatives.keepsClose(m)) {
            cir.setReturnValue(AdaptiveCombat.select(m, t, 8.0));
        }
    }
}
