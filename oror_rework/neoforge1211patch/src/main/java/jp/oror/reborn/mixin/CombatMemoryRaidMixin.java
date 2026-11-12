package jp.oror.reborn.mixin;

import jp.oror.reborn.raid.Raid;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * (059e) In a raid ({@link Raid}) a god that learns a kind of blow (Hakyoku, Shinra, Miyohime, Valeria) still takes
 * 40% of it at the least, not 8%: every player's sword is the same kind of blow, so the lore's floor would make the raid
 * twelve times as long.
 */
@Mixin(targets = "jp.oror.reborn.CombatMemory", remap = false)
public abstract class CombatMemoryRaidMixin {
    @Inject(method = "resistance(I)F", at = @At("RETURN"), cancellable = true, require = 0)
    private static void oror$raidFloor(int n, CallbackInfoReturnable<Float> cir) {
        if (Raid.anyStruck() && cir.getReturnValueF() < 0.4F) {
            cir.setReturnValue(0.4F);
        }
    }
}
