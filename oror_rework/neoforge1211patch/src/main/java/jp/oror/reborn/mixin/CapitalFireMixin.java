package jp.oror.reborn.mixin;

import jp.oror.reborn.village.BuildingGuard;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.FireBlock;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * (059f) No fire eats the capital (the user: "宮殿や破壊されるバグも見直し"). A god's lightning, a fire charge, a burning
 * mob, lava by a wall: a fire that caught in the capital spread across its wooden roofs, beams and floors and burned them
 * away block by block, and nothing in the town put it out. A fire in the capital goes out at its first tick now, before
 * it spreads or burns anything, unless it burns on a block that burns for ever (netherrack in a hearth: it stays lit, and
 * spreads nowhere). The capital holds no fire of its own (none in its template). Elsewhere fire is as it was.
 */
@Mixin(FireBlock.class)
public abstract class CapitalFireMixin {
    @Inject(method = "tick", at = @At("HEAD"), cancellable = true, require = 0)
    private void oror$capital(BlockState state, ServerLevel level, BlockPos pos, RandomSource random, CallbackInfo ci) {
        if (!BuildingGuard.inCapital(pos, 64)) {
            return;
        }
        ci.cancel();
        BuildingGuard.firesOut++;
        if (!level.getBlockState(pos.below()).is(level.dimensionType().infiniburn())) {
            level.removeBlock(pos, false);
        }
    }
}
