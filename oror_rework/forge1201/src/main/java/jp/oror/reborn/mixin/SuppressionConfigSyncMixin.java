package jp.oror.reborn.mixin;

import net.minecraftforge.server.ServerLifecycleHooks;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Pseudo
@Mixin(
    targets = {"ru.liko.suppressionmod.network.NetworkHandler"},
    remap = false
)
public abstract class SuppressionConfigSyncMixin {
    @Inject(
        method = {"sendToAll"},
        at = {@At("HEAD")},
        cancellable = true,
        remap = false
    )
    private static void oror$skipClientConfigBroadcast(CallbackInfo callback) {
        if (ServerLifecycleHooks.getCurrentServer() == null) {
            callback.cancel();
            System.out.println("[OROR_COMPAT] suppressionmod=1.2.0 remoteClientConfigBroadcastSkipped=true");
        }
    }
}
