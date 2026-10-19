package jp.oror.reborn.mixin;

import java.util.Collections;
import java.util.Map;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(
    targets = {"io.github.flemmli97.tenshilib.patreon.PatreonDataManager"},
    remap = false
)
public abstract class OfflinePatreonMixin {
    @Shadow
    private static Map<String, ?> PLAYERS;
    @Shadow
    private static boolean READING;

    @Inject(
        method = {"init"},
        at = {@At("HEAD")},
        cancellable = true
    )
    private static void oror$offlineCosmetics(CallbackInfo ci) {
        if (Boolean.getBoolean("oror.offlineValidation")) {
            PLAYERS = Collections.emptyMap();
            READING = false;
            ci.cancel();
            System.out.println("[OROR_OFFLINE] Cosmetic supporter-list request disabled");
        }
    }
}
