package jp.oror.reborn.mixin;

import jp.oror.reborn.AdaptiveCombat;
import jp.oror.reborn.combat.Sidearm;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** (052) A village guard's gun holstered for a blade up close, and drawn again at range (Sidearm). */
@Mixin(value = AdaptiveCombat.class, remap = false)
public abstract class GuardSidearmMixin {
    @Inject(method = "select", at = @At("HEAD"), remap = false)
    private static void oror$sidearm(Mob m, LivingEntity t, double distance, CallbackInfoReturnable<String> cir) {
        Sidearm.choose(m, t, distance);
    }
}
