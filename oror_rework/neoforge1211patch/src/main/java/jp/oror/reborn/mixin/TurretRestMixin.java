package jp.oror.reborn.mixin;

import jp.oror.reborn.perf.TurretRest;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.phys.Vec3;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** (059d) A still turret of the kingdom at rest on its floor skips most of its moves ({@link TurretRest}). */
@Pseudo
@Mixin(targets = "com.atsuishio.superbwarfare.entity.vehicle.base.VehicleEntity", remap = false)
public abstract class TurretRestMixin {
    @Inject(method = "move(Lnet/minecraft/world/entity/MoverType;Lnet/minecraft/world/phys/Vec3;)V", at = @At("HEAD"), cancellable = true,
        remap = false, require = 0)
    private void oror$rest(MoverType type, Vec3 step, CallbackInfo ci) {
        if (type == MoverType.SELF && TurretRest.resting((Entity) (Object) this, step)) {
            ci.cancel();
        }
    }
}
