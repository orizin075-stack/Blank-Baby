package jp.oror.reborn.mixin;

import jp.oror.reborn.VillagerLife;
import jp.oror.reborn.village.BuildingGuard;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.npc.Villager;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** (053) No villager huts in the capital, nor before doors and on paths in villages (BuildingGuard). */
@Mixin(value = VillagerLife.class, remap = false)
public abstract class VillagerBuildMixin {
    @Inject(method = "startBuild", at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$site(Villager v, ServerLevel sl, BlockPos at, CallbackInfoReturnable<Boolean> cir) {
        if (!BuildingGuard.hutMay(sl, at)) {
            cir.setReturnValue(false);
        }
    }

    @Inject(method = "build", at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$giveUp(Villager v, ServerLevel sl, CallbackInfoReturnable<Boolean> cir) {
        // the hut's corner is kept with the villager's life data (VillagerLife.data)
        CompoundTag life = VillagerLife.data(v);
        if (life.contains("BuildOrigin") && BuildingGuard.inCapital(BlockPos.of(life.getLong("BuildOrigin")), 64)) {
            life.remove("BuildOrigin");
            life.remove("BuildStep");
            cir.setReturnValue(false);
        }
    }
}
