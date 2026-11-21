package jp.oror.reborn.mixin;

import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.raid.Raider;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * (r63, run 201) Ice and Fire's dragon takes any passenger but its owner for prey: it holds it in its mouth, shakes it,
 * bites it and drops it (DragonBaseEntity.updatePreyInMouth, from positionRider). That is what took Azazel's riders off
 * their dragons in run 200 (SIEGE-DISMOUNT). An illager of the siege rides on the dragon's back instead: no shaking, no
 * bite, sat a little behind the shoulders. Both sides do it, so the client draws the rider where the server has him.
 * A dragon with any other passenger in its mouth (a cow, a villager, a player not its owner) is left as it was.
 */
@Pseudo
@Mixin(targets = "com.iafenvoy.iceandfire.entity.DragonBaseEntity", remap = false)
public abstract class DragonRiderMixin {
    @Inject(method = "updatePreyInMouth", at = @At("HEAD"), cancellable = true, remap = false, require = 0)
    private void oror$rideOnBack(CallbackInfo ci) {
        Entity dragon = (Entity) (Object) this;
        if (dragon.getPassengers().isEmpty()) {
            return;
        }
        for (Entity p : dragon.getPassengers()) {
            if (!(p instanceof Raider)) {
                return;
            }
        }
        if (!dragon.level().isClientSide() && !dragon.getPersistentData().getBoolean("OrorAzazelSiegeAir")) {
            return;
        }
        float yaw = (dragon instanceof net.minecraft.world.entity.LivingEntity l ? l.yBodyRot : dragon.getYRot()) * Mth.DEG_TO_RAD;
        double back = dragon.getBbWidth() * 0.15;
        double up = dragon.getBbHeight() * 0.8;
        for (Entity p : dragon.getPassengers()) {
            p.setPos(dragon.getX() + Mth.sin(yaw) * back, dragon.getY() + up, dragon.getZ() - Mth.cos(yaw) * back);
        }
        ci.cancel();
    }
}
