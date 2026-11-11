package jp.oror.reborn.mixin;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * (058) Mobs no longer set blocks into the world while they fight: no bridges or pillars of their own, no water set
 * under a fall and taken away after (TerrainPlay). With the digging stopped beside it (MobDiggingOffMixin) a fight no
 * longer leaves holes and stray blocks in the houses it passes (the user's broken buildings).
 */
@Mixin(targets = "jp.oror.reborn.TerrainPlay", remap = false)
public abstract class MobTerrainOffMixin {
    @Inject(method = "place(Lnet/minecraft/world/entity/Mob;Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/core/BlockPos;"
        + "Lnet/minecraft/world/level/block/state/BlockState;)Z", at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$noPlacing(Mob mob, ServerLevel level, BlockPos pos, BlockState state, CallbackInfoReturnable<Boolean> cir) {
        cir.setReturnValue(false);
    }

    @Inject(method = "fallRescue(Lnet/minecraft/world/entity/Mob;Lnet/minecraft/server/level/ServerLevel;)V", at = @At("HEAD"), cancellable = true,
        remap = false)
    private static void oror$noWaterUnderAFall(Mob mob, ServerLevel level, CallbackInfo ci) {
        ci.cancel();
    }
}
