package jp.oror.reborn.mixin;

import com.nameless.indestructible.world.capability.AdvancedCustomHumanoidMobPatch;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import yesman.epicfight.api.event.types.entity.TakeDamageEvent;
import yesman.epicfight.world.capabilities.EpicFightCapabilities;

/**
 * 0.17.24 (native combat line): the NeoForge fork's event bridge only covers its newer IAdvancedCapability API, so a
 * player's parry is passed on to the attacker's original Indestructible patch here.
 *
 * 0.17.25: damage without a direct entity (no attacker to tell) is skipped instead of being looked up.
 */
@Mixin(value = TakeDamageEvent.Income.class, remap = false)
public abstract class NightfallNativeParryFeedbackMixin {
    @Inject(method = "setParried", at = @At("TAIL"))
    private void oror$notifyOriginalPatch(boolean parried, CallbackInfo ci) {
        TakeDamageEvent.Income event = (TakeDamageEvent.Income)(Object)this;
        Entity attacker = event.getDamageSource().getDirectEntity();
        if (attacker == null) {
            return;
        }
        AdvancedCustomHumanoidMobPatch<?> patch = EpicFightCapabilities.getEntityPatch(attacker, AdvancedCustomHumanoidMobPatch.class);
        if (patch != null) {
            patch.setParried(parried);
        }
    }
}
