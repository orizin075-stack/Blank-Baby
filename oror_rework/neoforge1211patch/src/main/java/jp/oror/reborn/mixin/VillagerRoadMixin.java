package jp.oror.reborn.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * (059g) A villager on the road between villages (VillageRoads) walks it instead of living his village's day: VillagerLife's
 * work, bed and chores would have turned him round for home. A fight or a flight still goes the village's own way.
 */
@Mixin(targets = "jp.oror.reborn.VillagerLife", remap = false)
public abstract class VillagerRoadMixin {
    @Inject(method = "tick(Lnet/neoforged/neoforge/event/tick/EntityTickEvent$Post;)V", at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$road(net.neoforged.neoforge.event.tick.EntityTickEvent.Post e, CallbackInfo ci) {
        if (jp.oror.reborn.VillageRoads.onLife(e.getEntity())) {
            ci.cancel();
        }
    }
}
