package jp.oror.reborn.mixin;

import net.minecraft.world.entity.npc.AbstractVillager;
import net.minecraft.world.item.trading.MerchantOffers;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

/**
 * (053) A villager or wandering trader saved before it is in the world (one a structure sets down as the world is made:
 * Minecraft saves it into the chunk being made at once) does not draw its trades then. Drawing them asks every mod's
 * trades, on the thread making the world, and a trade of a map to the nearest structure searches the world from there:
 * in 053's CI the second run stopped on a trade of nothing drawn so, the third hung in the same place. Its trades are
 * drawn as before, when it is first asked for them in the world, on the server's own thread. (r69) The same for any
 * villager saved with its trades not yet drawn.
 */
@Mixin(AbstractVillager.class)
public abstract class MerchantSaveMixin {
    @Shadow
    protected MerchantOffers offers;

    @Redirect(method = "addAdditionalSaveData", at = @At(value = "INVOKE",
        target = "Lnet/minecraft/world/entity/npc/AbstractVillager;getOffers()Lnet/minecraft/world/item/trading/MerchantOffers;"))
    private MerchantOffers oror$noTradesWhileMade(AbstractVillager self) {
        // (r69) nor one saved on the server's own thread: a villager saved as its chunk unloads drew its trades there, and a
        // cartographer's map trade searched for the nearest structure, loading chunks in the middle of the unload (CI: the
        // re-entries EntityUnloads caught, traced to VillagerTrades$TreasureMapForEmeralds under addAdditionalSaveData).
        // Trades never drawn are never seen: they are drawn when the villager is first asked for them, as before.
        if (this.offers == null) {
            return new MerchantOffers();
        }
        return self.getOffers();
    }
}
