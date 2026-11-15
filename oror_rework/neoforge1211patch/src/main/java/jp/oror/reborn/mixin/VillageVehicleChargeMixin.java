package jp.oror.reborn.mixin;

import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** (059g) A village vehicle's battery charged from the village's coal and charcoal (VillageFuel), not from nothing. */
@Mixin(targets = "jp.oror.reborn.VillageVehicles", remap = false)
public abstract class VillageVehicleChargeMixin {
    @Inject(method = "charge(Lnet/minecraft/world/entity/Entity;)V", at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$charge(Entity v, CallbackInfo ci) {
        if (jp.oror.reborn.VillageFuel.charge(v)) {
            ci.cancel();
        }
    }
}
