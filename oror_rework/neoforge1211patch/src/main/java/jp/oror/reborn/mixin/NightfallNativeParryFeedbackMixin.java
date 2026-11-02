package jp.oror.reborn.mixin;

import com.nameless.indestructible.world.capability.AdvancedCustomHumanoidMobPatch;
import java.lang.reflect.Method;
import jp.oror.reborn.combat.MobGuard;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import yesman.epicfight.api.event.types.entity.TakeDamageEvent.Income;
import yesman.epicfight.world.capabilities.EpicFightCapabilities;

/**
 * A player's parry (Epic Fight's, the Nightfall parry skill) told to the attacker: an Indestructible mob is told it was
 * parried, as before, and plays its own reaction; (052) any other mob is thrown back and staggered by OROR's guard
 * (MobGuard.parried), so that the parry means the same against every mob.
 */
@Mixin(value = {Income.class}, remap = false)
public abstract class NightfallNativeParryFeedbackMixin {
    @Inject(method = {"setParried"}, at = {@At("TAIL")})
    private void oror$notifyOriginalPatch(boolean parried, CallbackInfo ci) {
        Income event = (Income) (Object) this;
        Entity attacker = event.getDamageSource().getDirectEntity();
        if (attacker == null) {
            return;
        }
        AdvancedCustomHumanoidMobPatch<?> patch = (AdvancedCustomHumanoidMobPatch<?>) EpicFightCapabilities.getEntityPatch(attacker,
            AdvancedCustomHumanoidMobPatch.class);
        if (patch != null) {
            patch.setParried(parried);
        } else if (parried && attacker instanceof LivingEntity living) {
            MobGuard.parried(living, oror$defender(event, living));
        }
    }

    /** Where the parrying player stands (the event's patch's entity), or a step in front of the attacker. */
    private static Vec3 oror$defender(Object event, LivingEntity attacker) {
        for (String name : new String[]{"getEntityPatch", "getPlayerPatch", "getPatch"}) {
            try {
                Method m = event.getClass().getMethod(name);
                Object patch = m.invoke(event);
                if (patch != null) {
                    Object original = patch.getClass().getMethod("getOriginal").invoke(patch);
                    if (original instanceof Entity e && e != attacker) {
                        return e.position();
                    }
                }
            } catch (ReflectiveOperationException | RuntimeException ex) {
                // not this one
            }
        }
        return attacker.position().add(attacker.getLookAngle().multiply(1, 0, 1).scale(1.5));
    }
}
