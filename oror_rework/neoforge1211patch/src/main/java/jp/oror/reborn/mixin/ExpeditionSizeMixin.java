package jp.oror.reborn.mixin;

import jp.oror.reborn.VillageExpeditions;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.Constant;
import org.spongepowered.asm.mixin.injection.ModifyConstant;

/**
 * (053) More expeditions (the user: there could be more of them). A village's expedition takes up to six of its
 * strongest (four before); the parties met out in the wild are four to seven strong (three to five) and are met twice
 * as often (a one in eight chance every two minutes away from villages, one in sixteen before).
 */
@Mixin(value = VillageExpeditions.class, remap = false)
public abstract class ExpeditionSizeMixin {
    @ModifyConstant(method = "party(Lnet/minecraft/server/level/ServerLevel;Ljp/oror/reborn/VillageWork$Survey;)Ljava/util/List;",
        constant = @Constant(longValue = 4L), remap = false)
    private static long oror$villageParty(long four) {
        return 6L;
    }

    @ModifyConstant(method = "wanderers", constant = @Constant(intValue = 3), remap = false)
    private static int oror$wanderingParty(int three) {
        return 4;
    }

    @ModifyConstant(method = "wanderers", constant = @Constant(doubleValue = 0.06), remap = false)
    private static double oror$wanderingChance(double chance) {
        return 0.12;
    }
}
