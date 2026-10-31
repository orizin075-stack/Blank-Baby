package jp.oror.reborn.mixin;

import jp.oror.reborn.AdaptiveCombat;
import jp.oror.reborn.HandlessCombat;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** AdaptiveCombat for mobs without hands: no weapon chosen, no arrow shot; their own spring instead (HandlessCombat). */
@Mixin(value = AdaptiveCombat.class, remap = false)
public abstract class HandlessCombatMixin {
    @Inject(method = "select", at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$handless(Mob m, LivingEntity t, double distance, CallbackInfoReturnable<String> cir) {
        if (!HandlessCombat.handed(m)) {
            cir.setReturnValue(HandlessCombat.select(m, t, distance));
        }
    }

    @Inject(method = "shoot", at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$noArrows(Mob m, LivingEntity t, String weapon, ServerLevel sl, CallbackInfo ci) {
        if (!HandlessCombat.handed(m)) {
            ci.cancel();
        }
    }
}
