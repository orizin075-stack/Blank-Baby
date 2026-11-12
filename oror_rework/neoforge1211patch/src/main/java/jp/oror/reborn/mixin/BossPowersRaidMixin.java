package jp.oror.reborn.mixin;

import jp.oror.reborn.raid.Raid;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * (059e) In a raid ({@link Raid}) a god's own damage compression gives way: BossPowers.incoming squeezes every blow over
 * 20 to 20 + (blow - 20)^0.65 and then to 8% of the god's own health (82 at most), made for a god of 1,024 health. On
 * a raid's health of 9,000 to 102,400 it made every good weapon alike (a legend's 1,860 and a relic's 700 both came to
 * 82) and the raid's own caps never came into play: the CI 21 measure had the biggest gods at 10 to 28 minutes alone
 * and no faster with four. The raid's caps (5% a blow, a share a second) take its place.
 */
@Mixin(targets = "jp.oror.reborn.BossPowers", remap = false)
public abstract class BossPowersRaidMixin {
    @Inject(method = "incoming(Lnet/neoforged/neoforge/event/entity/living/LivingIncomingDamageEvent;Ljp/oror/reborn/SupremeEntity;)V",
        at = @At("HEAD"), cancellable = true, require = 0)
    private static void oror$raidUncompressed(LivingIncomingDamageEvent e, jp.oror.reborn.SupremeEntity b, CallbackInfo ci) {
        if (Raid.struck(b)) {
            ci.cancel();
        }
    }
}
