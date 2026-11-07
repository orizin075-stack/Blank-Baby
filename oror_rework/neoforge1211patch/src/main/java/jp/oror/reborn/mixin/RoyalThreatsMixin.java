package jp.oror.reborn.mixin;

import jp.oror.reborn.king.KingCourt;
import net.minecraft.world.entity.player.Player;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** (054) The king's enemy (one who struck him) is the kingdom's enemy for good, not for a minute (KingCourt). */
@Mixin(targets = "jp.oror.reborn.royal.RoyalThreats", remap = false)
public abstract class RoyalThreatsMixin {
    @Inject(method = "hostilePlayer(Lnet/minecraft/world/entity/player/Player;)Z", at = @At("RETURN"), cancellable = true, remap = false)
    private static void oror$kingsEnemy(Player p, CallbackInfoReturnable<Boolean> cir) {
        if (!cir.getReturnValueZ() && p != null && !p.level().isClientSide && KingCourt.enemy(p)) {
            cir.setReturnValue(true);
        }
    }
}
