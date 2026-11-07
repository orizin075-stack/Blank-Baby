package jp.oror.reborn.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * (053) TUKUYO taken out (the user: "TUKUYO can go"). The bridge asked the TUKUYO service beside the game (port 8022)
 * about every mob in a fight every ten seconds, and what it answered set the mob's stance; now it asks nothing, whatever
 * the world's configuration says (a world made before keeps "tukuyo = true" in its own server configuration), and a
 * message a player says to a mob is answered as without TUKUYO. The local AI's dialogue (port 8023) is not this.
 */
@Mixin(targets = "jp.oror.reborn.TukuyoBridge", remap = false)
public abstract class TukuyoOffMixin {
    @Inject(method = "tick(Lnet/neoforged/neoforge/event/tick/EntityTickEvent$Post;)V", at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$noTick(net.neoforged.neoforge.event.tick.EntityTickEvent.Post e, CallbackInfo ci) {
        ci.cancel();
    }

    @Inject(method = "queue(Lnet/minecraft/world/entity/Mob;Lnet/minecraft/server/level/ServerPlayer;Ljava/lang/String;)V",
        at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$noQueue(net.minecraft.world.entity.Mob m, net.minecraft.server.level.ServerPlayer p, String message, CallbackInfo ci) {
        ci.cancel();
    }

    @Inject(method = "request(Lnet/minecraft/world/entity/Mob;Lnet/minecraft/server/level/ServerPlayer;Ljava/lang/String;)Z",
        at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$noRequest(net.minecraft.world.entity.Mob m, net.minecraft.server.level.ServerPlayer p, String message,
                                       CallbackInfoReturnable<Boolean> cir) {
        cir.setReturnValue(false);
    }

    @Inject(method = "status()Ljava/lang/String;", at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$status(CallbackInfoReturnable<String> cir) {
        cir.setReturnValue("なし（053で外しました）");
    }
}
