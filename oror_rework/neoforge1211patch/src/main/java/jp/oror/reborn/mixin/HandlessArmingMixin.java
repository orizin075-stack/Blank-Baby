package jp.oror.reborn.mixin;

import jp.oror.reborn.HandlessCombat;
import jp.oror.reborn.MobLevels;
import net.minecraft.world.entity.Mob;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** The ranked loadout (armour, a shield and a sword) only for mobs that can wear and hold it. */
@Mixin(value = MobLevels.class, remap = false)
public abstract class HandlessArmingMixin {
    @Inject(method = "arm", at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$handsFirst(Mob m, CallbackInfo ci) {
        if (!HandlessCombat.handed(m)) {
            ci.cancel();
        }
    }
}
