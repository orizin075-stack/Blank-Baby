package jp.oror.reborn.mixin;

import jp.oror.reborn.duel.TalismanShow;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.event.entity.living.LivingDamageEvent;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * (r71) Duel Dominion's Retribution (応報符) returns the damage its caster took, read after the effigies had their turn: a
 * bound effigy in the caster's hands or pack shoulders a blow first, and when it took all of it, Retribution returned
 * nothing (the look run: a vindicator's blow, the effigy's "肩代わり", the vindicator untouched). An effigy is what a
 * talisman's caster carries, so Retribution all but never answered. Here the blow an effigy took is remembered for its
 * tick, and Retribution answers the larger of what got through and what the effigy took.
 */
@Pseudo
@Mixin(targets = "jp.oror.dueldominion.SpiritEvents", remap = false)
public abstract class DuelRetributionMixin {
    @Inject(method = "tryAbsorb(Lnet/neoforged/neoforge/event/entity/living/LivingDamageEvent$Pre;Ljp/oror/dueldominion/SpiritLedger;Lnet/minecraft/server/level/ServerPlayer;Lnet/minecraft/world/item/ItemStack;F)Z",
        at = @At("HEAD"), require = 0)
    private static void oror$remember(LivingDamageEvent.Pre e, jp.oror.dueldominion.SpiritLedger ledger, ServerPlayer p, ItemStack effigy, float amount,
        CallbackInfoReturnable<Boolean> cir) {
        TalismanShow.shouldering(p, amount);
    }
}
