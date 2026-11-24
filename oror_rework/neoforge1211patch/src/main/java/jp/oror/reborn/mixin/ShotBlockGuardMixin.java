package jp.oror.reborn.mixin;

import jp.oror.reborn.village.BuildingGuard;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.LiquidBlock;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * (r69) Superb Warfare's rounds break the blocks they strike themselves (Level.destroyBlock from a cannon shell, a small
 * cannon shell, a rocket, a missile, a bomb, C4, a mine, the Annihilator's beam: CI's look into its classes), not by an
 * explosion, so the rule that keeps OROR's buildings from blasts never saw them: a stray round from the gun post check
 * cut a line through the Elseria citadel's floor, 25 blocks and a chest, in every full run. A round no longer breaks a
 * block of the capital, of a village or of one of OROR's stages. Vehicles pushing through blocks are as they were.
 * <p>
 * (r69, second look) With destroyBlock held, 20 strikes were spared, yet 16 blocks further along the same line still went:
 * a way that does not pass destroyBlock (Superb Warfare's own explosion, which raises no Detonate event: no STAGE-BLAST
 * was logged). So the block's removal itself is held too, setBlock to air or to a fluid, when Superb Warfare's round,
 * explosion or beam is on the stack; what took it is logged (STAGE-SHOT "via").
 */
@Mixin(Level.class)
public abstract class ShotBlockGuardMixin {
    @Inject(method = "destroyBlock(Lnet/minecraft/core/BlockPos;ZLnet/minecraft/world/entity/Entity;I)Z", at = @At("HEAD"), cancellable = true, require = 0)
    private void oror$sparedFromRounds(BlockPos pos, boolean drop, Entity breaker, int depth, CallbackInfoReturnable<Boolean> cir) {
        if ((Object) this instanceof ServerLevel sl && BuildingGuard.shotSpared(sl, pos)) {
            cir.setReturnValue(false);
        }
    }

    @Inject(method = "setBlock(Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;II)Z", at = @At("HEAD"), cancellable = true, require = 0)
    private void oror$removalSpared(BlockPos pos, BlockState state, int flags, int left, CallbackInfoReturnable<Boolean> cir) {
        if ((Object) this instanceof ServerLevel sl && (state.isAir() || state.getBlock() instanceof LiquidBlock) && BuildingGuard.removalSpared(sl, pos)) {
            cir.setReturnValue(false);
        }
    }
}
