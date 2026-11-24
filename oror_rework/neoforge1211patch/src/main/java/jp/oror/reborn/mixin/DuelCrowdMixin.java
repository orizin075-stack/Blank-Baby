package jp.oror.reborn.mixin;

import jp.oror.reborn.duel.DuelCrowd;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** (r71) A Duel Dominion duel's start and end, for the ring of mobs that watches it ({@link DuelCrowd}). */
@Pseudo
@Mixin(targets = "jp.oror.dueldominion.DuelManager", remap = false)
public abstract class DuelCrowdMixin {
    @Inject(method = "start(Lnet/minecraft/server/level/ServerPlayer;Lnet/minecraft/world/entity/LivingEntity;)Z", at = @At("RETURN"), require = 0)
    private static void oror$watch(ServerPlayer p, LivingEntity target, CallbackInfoReturnable<Boolean> cir) {
        if (Boolean.TRUE.equals(cir.getReturnValue())) {
            try {
                DuelCrowd.begun(p, target);
            } catch (RuntimeException ignored) {
            }
        }
    }

    @Inject(method = "stop(Ljp/oror/dueldominion/DuelManager$Duel;Ljava/lang/String;)V", at = @At("HEAD"), require = 0)
    private static void oror$cheered(jp.oror.dueldominion.DuelManager.Duel duel, String why, CallbackInfo ci) {
        try {
            if (duel != null) {
                DuelCrowd.ended(duel.challenger(), duel.defender());
            }
        } catch (RuntimeException ignored) {
        }
    }
}
