package jp.oror.reborn.mixin;

import java.util.List;
import jp.oror.reborn.VillageExpeditions;
import net.minecraft.world.entity.npc.Villager;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** (059g) A village with a tank or a jet keeps two of its strong at home to crew it (VillageHomeGuard). */
@Mixin(value = VillageExpeditions.class, remap = false)
public abstract class ExpeditionHomeGuardMixin {
    @Inject(method = "party(Lnet/minecraft/server/level/ServerLevel;Ljp/oror/reborn/VillageWork$Survey;)Ljava/util/List;", at = @At("RETURN"),
        cancellable = true, remap = false)
    private static void oror$homeGuard(CallbackInfoReturnable<List<Villager>> cir) {
        List<Villager> kept = jp.oror.reborn.VillageHomeGuard.trim(cir.getReturnValue());
        if (kept != null) {
            cir.setReturnValue(kept);
        }
    }
}
