package jp.oror.reborn.mixin;

import jp.oror.reborn.royal.RoyalGuns;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.royal.RoyalRole;
import jp.oror.reborn.vehicle.Supply;
import net.neoforged.neoforge.energy.IEnergyStorage;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

/**
 * A guard's electric gun (his taser) is no longer recharged from nowhere every second: only from the store of a charging
 * station within six blocks of him (the gates' and the posts' power plants), the station giving what the gun takes.
 * The king's guns are his own affair.
 */
@Mixin(value = RoyalGuns.class, remap = false)
public abstract class RoyalGunsSupplyMixin {
    @Shadow
    @Final
    private RoyalMob mob;

    @Redirect(method = "tick", at = @At(value = "INVOKE", target = "Lnet/neoforged/neoforge/energy/IEnergyStorage;receiveEnergy(IZ)I"), remap = false)
    private int oror$fromStation(IEnergyStorage gun, int amount, boolean simulate) {
        if (simulate || this.mob.role() == RoyalRole.KING) {
            return gun.receiveEnergy(amount, simulate);
        }
        return Supply.recharge(this.mob, gun, amount);
    }
}
