package jp.oror.reborn.mixin;

import jp.oror.reborn.worldgen.StructureGuard;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * (r66) An Ice and Fire dragon breaks no block of one of OROR's buildings (a god's stage, the capital, a village) as it
 * moves. Its breaking asks only Ice and Fire's own setting and the game rule, never the mob-griefing event OROR answers
 * elsewhere: eleven fire dragons by the chaos citadel's spawner took 140 of the 208 blocks round it in two seconds
 * (GOD-SPAWNER-AREA), the floor of the god's stage among them.
 */
@Pseudo
@Mixin(targets = "com.iafenvoy.iceandfire.entity.DragonBaseEntity", remap = false)
public abstract class IafStageGuardMixin {
    @Inject(method = "canDestroyBlock(Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;)Z", at = @At("HEAD"),
        cancellable = true, remap = false, require = 0)
    private void oror$stage(BlockPos pos, BlockState state, CallbackInfoReturnable<Boolean> cir) {
        if (StructureGuard.insideOrUnder(pos)) {
            jp.oror.reborn.village.BuildingGuard.dragonSpared(pos);
            cir.setReturnValue(false);
        }
    }
}
