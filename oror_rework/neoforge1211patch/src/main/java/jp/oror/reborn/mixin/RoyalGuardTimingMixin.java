package jp.oror.reborn.mixin;

import jp.oror.reborn.royal.RoyalMob;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.Constant;
import org.spongepowered.asm.mixin.injection.ModifyConstant;

/**
 * (059e) The royals' own guard (RoyalMob.defend), the user: "敵も味方もパリイシステム使わない". A royal raised his guard
 * for half a second every two and a half seconds and parried only a blow in its first three ticks, so the kingdom's
 * soldiers were seen to block, almost never to parry. Now the first five ticks of the guard parry, and the guard comes
 * up every 1.7 seconds (the King's every 1.2, as before).
 */
@Mixin(value = RoyalMob.class, remap = false)
public abstract class RoyalGuardTimingMixin {
    @ModifyConstant(method = "defend", constant = @Constant(intValue = 2), require = 0, remap = false)
    private int oror$parryWindow(int ticks) {
        return 5;
    }

    @ModifyConstant(method = "battle", constant = @Constant(intValue = 50), require = 0, remap = false)
    private int oror$guardCycle(int ticks) {
        return 34;
    }
}
