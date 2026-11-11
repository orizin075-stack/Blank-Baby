package jp.oror.reborn.mixin;

import jp.oror.reborn.safety.SaneMoves;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyVariable;

/** (059) A step of more than 64 blocks, or not a number, is cut before its collisions are sought (see {@link SaneMoves}). */
@Mixin(Entity.class)
public abstract class SaneMoveMixin {
    @ModifyVariable(method = "move(Lnet/minecraft/world/entity/MoverType;Lnet/minecraft/world/phys/Vec3;)V", at = @At("HEAD"), argsOnly = true,
        require = 0)
    private Vec3 oror$saneStep(Vec3 step) {
        return SaneMoves.check((Entity) (Object) this, step);
    }
}
