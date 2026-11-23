package jp.oror.reborn.mixin;

import jp.oror.reborn.ci.GameTestFixes;
import net.minecraft.gametest.framework.GameTestHelper;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** (r66) ProgressionGameTests: the miners' ore under a roof, as a miner digs only underground since 053 (GameTestFixes.roof). */
@Mixin(targets = "jp.oror.reborn.ProgressionGameTests", remap = false)
public abstract class GameTestFixesProgressionMixin {
    @Inject(method = "buried_ore_is_excavated_smelted_and_collected", at = @At("RETURN"), remap = false)
    private static void oror$buried(GameTestHelper h, CallbackInfo ci) {
        GameTestFixes.roof(h, 3, 17, 3, 13);
    }

    @Inject(method = "three_miners_work_simultaneously_without_material_duplication", at = @At("RETURN"), remap = false)
    private static void oror$three(GameTestHelper h, CallbackInfo ci) {
        GameTestFixes.roof(h, 3, 91, 3, 13);
    }
}
