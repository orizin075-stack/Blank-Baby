package jp.oror.reborn.mixin;

import net.minecraft.client.gui.components.toasts.ToastComponent;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * (r70) The user: "同時に複数のテキスト出るのやめて". The corner's notices (advancements, recipes, the pack's own) stood up
 * to five at once, one under another. Now one shows at a time: while any is on screen no room is left for the next,
 * which waits its turn as before.
 */
@Mixin(ToastComponent.class)
public abstract class ToastOneAtATimeMixin {
    @Inject(method = "freeSlots()I", at = @At("RETURN"), cancellable = true, require = 0)
    private void oror$oneAtATime(CallbackInfoReturnable<Integer> cir) {
        if (cir.getReturnValueI() < 5) {
            cir.setReturnValue(0);
        }
    }
}
