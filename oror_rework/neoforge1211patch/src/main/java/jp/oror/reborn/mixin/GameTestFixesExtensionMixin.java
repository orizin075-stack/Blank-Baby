package jp.oror.reborn.mixin;

import jp.oror.reborn.ci.GameTestFixes;
import net.minecraft.gametest.framework.GameTestHelper;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** (r66) ExtensionGameTests: no water under a falling mob since 058 (GameTestFixes). */
@Mixin(targets = "jp.oror.reborn.ExtensionGameTests", remap = false)
public abstract class GameTestFixesExtensionMixin {
    @Inject(method = "skilled_mob_places_actual_water_before_landing", at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$landing(GameTestHelper h, CallbackInfo ci) {
        GameTestFixes.landingWater(h);
        ci.cancel();
    }
}
