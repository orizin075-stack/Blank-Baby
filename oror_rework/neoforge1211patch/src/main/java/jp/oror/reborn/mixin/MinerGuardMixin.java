package jp.oror.reborn.mixin;

import jp.oror.reborn.VillagerIndustry;
import jp.oror.reborn.village.BuildingGuard;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** (053) The villagers' miners dig only underground, and never where the capital stands (BuildingGuard). */
@Mixin(value = VillagerIndustry.class, remap = false)
public abstract class MinerGuardMixin {
    @Inject(method = "excavate", at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$underground(Villager v, BlockPos p, SimpleContainer c, ServerLevel sl, ItemStack tool, CallbackInfoReturnable<Boolean> cir) {
        if (!BuildingGuard.minerMay(sl, p)) {
            cir.setReturnValue(false);
        }
    }
}
