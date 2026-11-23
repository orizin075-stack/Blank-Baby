package jp.oror.reborn.mixin;

import jp.oror.reborn.ci.GameTestFixes;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

/** (r66) CompatibilityGameTests: each exact-version pack in the state CompatibilityPacks gives it (GameTestFixes). */
@Mixin(targets = "jp.oror.reborn.CompatibilityGameTests", remap = false)
public abstract class GameTestFixesCompatibilityMixin {
    @Redirect(method = "external_mobs_and_oror_share_combat", at = @At(value = "INVOKE", target = "Ljava/util/Collection;contains(Ljava/lang/Object;)Z",
        ordinal = 0, remap = false), remap = false)
    private static boolean oror$pack(java.util.Collection<String> selected, Object id) {
        return GameTestFixes.packAsItShouldBe(selected, id);
    }
}
