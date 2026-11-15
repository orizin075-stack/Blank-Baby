package jp.oror.reborn.mixin;

import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** (059g) A trade aircraft's engine fuelled from the village's coal and charcoal (VillageFuel), not from nothing. */
@Mixin(targets = "jp.oror.reborn.VillageFlights", remap = false)
public abstract class VillageFlightFuelMixin {
    @Inject(method = "fuel(Lnet/minecraft/world/entity/Entity;Ljava/lang/String;)V", at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$fuel(Entity craft, String type, CallbackInfo ci) {
        if (jp.oror.reborn.VillageFuel.fuel(craft, type)) {
            ci.cancel();
        }
    }
}
