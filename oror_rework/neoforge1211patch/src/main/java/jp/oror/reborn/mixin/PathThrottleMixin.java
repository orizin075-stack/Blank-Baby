package jp.oror.reborn.mixin;

import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Fewer path searches. The smart-mob combat and the royals' battle code ask for a path to their enemy or their
 * formation spot on every decision, and each ask runs a full search (a fifth of the server thread in the hundred-man
 * battle, by the CI's profile). A mob already on its way to (nearly) the same place, with a search less than a second
 * old, keeps its path; only the speed changes. A new destination, a finished path or a stale one searches again.
 */
@Mixin(PathNavigation.class)
public abstract class PathThrottleMixin {
    @Shadow
    @Final
    protected Mob mob;

    @Shadow
    public abstract boolean isDone();

    @Shadow
    public abstract BlockPos getTargetPos();

    @Shadow
    public abstract void setSpeedModifier(double speed);

    @Unique
    private long oror$searchedAt = Long.MIN_VALUE;

    @Unique
    private boolean oror$keep(double x, double y, double z, double speed) {
        long now = this.mob.level().getGameTime();
        BlockPos target = this.getTargetPos();
        // the farther the goal, the more it may have moved before the path is worth searching again (2 blocks at the
        // mob, 2 + a fifth of the distance farther off), and never more often than once a second while on the way
        double far = Math.sqrt(this.mob.distanceToSqr(x, y, z));
        double slack = 2.0 + far * 0.2;
        if (!this.isDone() && target != null && now - this.oror$searchedAt < 20 && target.distToCenterSqr(x, y, z) < slack * slack) {
            this.setSpeedModifier(speed);
            return true;
        }
        this.oror$searchedAt = now;
        return false;
    }

    @Inject(method = "moveTo(DDDD)Z", at = @At("HEAD"), cancellable = true)
    private void oror$throttleToPoint(double x, double y, double z, double speed, CallbackInfoReturnable<Boolean> cir) {
        if (this.oror$keep(x, y, z, speed)) {
            cir.setReturnValue(true);
        }
    }

    @Inject(method = "moveTo(Lnet/minecraft/world/entity/Entity;D)Z", at = @At("HEAD"), cancellable = true)
    private void oror$throttleToEntity(Entity entity, double speed, CallbackInfoReturnable<Boolean> cir) {
        if (this.oror$keep(entity.getX(), entity.getY(), entity.getZ(), speed)) {
            cir.setReturnValue(true);
        }
    }
}
