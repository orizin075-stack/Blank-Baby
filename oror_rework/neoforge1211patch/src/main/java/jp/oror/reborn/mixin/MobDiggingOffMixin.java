package jp.oror.reborn.mixin;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * (058) Mobs no longer break blocks to reach their enemy (AdaptiveCombat.terrain): they went through the walls of the
 * capital and the villages. Their pursuit, their weapons and their techniques are as before.
 */
@Mixin(targets = "jp.oror.reborn.AdaptiveCombat", remap = false)
public abstract class MobDiggingOffMixin {
    @Inject(method = "terrain(Lnet/minecraft/world/entity/Mob;Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/server/level/ServerLevel;)Z",
        at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$noDigging(Mob mob, LivingEntity target, ServerLevel level, CallbackInfoReturnable<Boolean> cir) {
        cir.setReturnValue(false);
    }
}
