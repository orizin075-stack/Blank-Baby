package jp.oror.reborn.mixin;

import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.Mob;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * (059h) A villager sent somewhere he cannot find his way to (VillageAI.walk): he goes by a waypoint ten blocks toward it
 * (VillageHomeGuard.waypoint). The CI's tank crewman, 16 to 19 blocks from his tank over a level green, stood still a
 * minute with every path empty; within 16 he found it at once.
 */
@Mixin(targets = "jp.oror.reborn.VillageAI", remap = false)
public abstract class VillageWalkWaypointMixin {
    @Inject(method = "walk(Lnet/minecraft/world/entity/Mob;Lnet/minecraft/core/BlockPos;FI)V", at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$waypoint(Mob mob, BlockPos to, float speed, int close, CallbackInfo ci) {
        if (jp.oror.reborn.VillageHomeGuard.waypoint(mob, to, speed, close)) {
            ci.cancel();
        }
    }
}
