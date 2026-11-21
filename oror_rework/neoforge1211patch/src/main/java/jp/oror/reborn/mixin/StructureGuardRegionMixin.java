package jp.oror.reborn.mixin;

import jp.oror.reborn.worldgen.StructureGuard;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.WorldGenRegion;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** (r63) A neighbouring chunk's features may not write through an OROR building already standing (StructureGuard). */
@Mixin(WorldGenRegion.class)
public abstract class StructureGuardRegionMixin {
    @Inject(method = "setBlock(Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;II)Z", at = @At("HEAD"), cancellable = true)
    private void oror$guard(BlockPos pos, BlockState state, int flags, int recursionLeft, CallbackInfoReturnable<Boolean> cir) {
        if (StructureGuard.refuse(pos)) {
            cir.setReturnValue(false);
        }
    }
}
