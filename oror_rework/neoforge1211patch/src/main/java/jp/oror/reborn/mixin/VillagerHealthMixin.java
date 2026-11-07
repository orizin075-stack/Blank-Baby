package jp.oror.reborn.mixin;

import jp.oror.reborn.MobLevels;
import jp.oror.reborn.village.VillagerHealth;
import net.minecraft.world.entity.Mob;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** (053) A villager taking up arms gets its level's health (VillagerHealth), not 256 + 128 a level. */
@Mixin(value = MobLevels.class, remap = false)
public abstract class VillagerHealthMixin {
    @Inject(method = "arm", at = @At("TAIL"), remap = false)
    private static void oror$villagerHealth(Mob m, CallbackInfo ci) {
        VillagerHealth.cap(m);
    }
}
