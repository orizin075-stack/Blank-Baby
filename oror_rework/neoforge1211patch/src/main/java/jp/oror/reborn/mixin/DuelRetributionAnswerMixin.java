package jp.oror.reborn.mixin;

import jp.oror.reborn.duel.TalismanShow;
import net.neoforged.neoforge.event.entity.living.LivingDamageEvent;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

/** (r71) Retribution answers the blow an effigy took as well as what got through ({@link DuelRetributionMixin}). */
@Pseudo
@Mixin(targets = "jp.oror.dueldominion.RitualReprisal", remap = false)
public abstract class DuelRetributionAnswerMixin {
    @Redirect(method = "afterDamage(Lnet/neoforged/neoforge/event/entity/living/LivingDamageEvent$Post;)V",
        at = @At(value = "INVOKE", target = "Lnet/neoforged/neoforge/event/entity/living/LivingDamageEvent$Post;getNewDamage()F"), require = 0)
    private static float oror$shoulderedToo(LivingDamageEvent.Post e) {
        return Math.max(e.getNewDamage(), TalismanShow.shouldered(e.getEntity()));
    }
}
