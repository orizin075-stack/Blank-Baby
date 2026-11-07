package jp.oror.reborn.mixin;

import jp.oror.reborn.village.TradeSafety;
import net.minecraft.world.entity.npc.AbstractVillager;
import net.minecraft.world.item.trading.MerchantOffers;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * (053) A villager's or wandering trader's offers, as they are handed out (to be saved, shown, traded), without the
 * trades that cannot be written down (TradeSafety): a trade of nothing stopped the server as a trader was saved.
 */
@Mixin(AbstractVillager.class)
public abstract class MerchantOffersSafetyMixin {
    @Inject(method = "getOffers", at = @At("RETURN"))
    private void oror$writable(CallbackInfoReturnable<MerchantOffers> cir) {
        AbstractVillager self = (AbstractVillager) (Object) this;
        if (!self.level().isClientSide) {
            TradeSafety.clean(self, cir.getReturnValue());
        }
    }
}
