package jp.oror.reborn.mixin;

import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.attributes.RangedAttribute;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * (059g, the user: "それぞれ１０００００ぐらいにして　上限なんて関係ない") Minecraft holds a living thing's maximum health to 1,024;
 * the gods have 100,000 now (GodStrength). The cap is lifted to a billion.
 */
@Mixin(RangedAttribute.class)
public abstract class MaxHealthCapMixin {
    @Inject(method = "sanitizeValue(D)D", at = @At("HEAD"), cancellable = true, remap = false)
    private void oror$noHealthCap(double value, CallbackInfoReturnable<Double> cir) {
        if ((Object) this == Attributes.MAX_HEALTH.value()) {
            cir.setReturnValue(Double.isNaN(value) ? 1.0 : Math.max(1.0, Math.min(1.0E9, value)));
        }
    }
}
