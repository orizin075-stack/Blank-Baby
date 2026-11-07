package jp.oror.reborn.mixin;

import jp.oror.reborn.king.GodSlayer;
import net.minecraft.world.damagesource.DamageSource;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * (054) 神殺し: an OROR being's lore does not turn aside a god-slayer's blow (LorePowers.incoming may only make it
 * greater, never less).
 */
@Mixin(targets = "jp.oror.reborn.LorePowers", remap = false)
public abstract class LorePowersDeicideMixin {
    @Inject(method = "incoming(Ljp/oror/reborn/SupremeEntity;Lnet/minecraft/world/damagesource/DamageSource;FLjava/lang/String;)F", at = @At("RETURN"),
        cancellable = true, remap = false)
    private static void oror$deicide(jp.oror.reborn.SupremeEntity e, DamageSource source, float amount, String type, CallbackInfoReturnable<Float> cir) {
        if (GodSlayer.has(source.getEntity()) && cir.getReturnValueF() < amount) {
            cir.setReturnValue(amount);
        }
    }
}
