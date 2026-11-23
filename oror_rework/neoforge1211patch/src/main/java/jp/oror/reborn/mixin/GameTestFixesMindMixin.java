package jp.oror.reborn.mixin;

import jp.oror.reborn.ci.GameTestFixes;
import net.minecraft.gametest.framework.GameTestHelper;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** (r66) MindGameTests asked again for what the game does since 053 and 058 (GameTestFixes). */
@Mixin(targets = "jp.oror.reborn.MindGameTests", remap = false)
public abstract class GameTestFixesMindMixin {
    @Inject(method = "villager_arms_and_defeats_survival_player", at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$villagerArms(GameTestHelper h, CallbackInfo ci) {
        GameTestFixes.villagerArms(h);
        ci.cancel();
    }

    @Inject(method = "low_health_mob_retreats_during_healing", at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$lowHealth(GameTestHelper h, CallbackInfo ci) {
        GameTestFixes.lowHealthRetreat(h);
        ci.cancel();
    }

    @Inject(method = "terrain_pillar_and_protected_chest_rules", at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$terrainPillar(GameTestHelper h, CallbackInfo ci) {
        GameTestFixes.terrainPillar(h);
        ci.cancel();
    }
}
