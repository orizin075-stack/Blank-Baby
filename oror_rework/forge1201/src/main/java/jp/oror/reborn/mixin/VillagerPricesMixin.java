package jp.oror.reborn.mixin;

import jp.oror.reborn.VillageReputation;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.player.Player;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin({Villager.class})
public abstract class VillagerPricesMixin {
    @Inject(
        method = {"updateSpecialPrices"},
        at = {@At("TAIL")}
    )
    private void oror$localVillagePrices(Player player, CallbackInfo ci) {
        VillageReputation.prices((Villager)(Object)this, player);
    }
}
