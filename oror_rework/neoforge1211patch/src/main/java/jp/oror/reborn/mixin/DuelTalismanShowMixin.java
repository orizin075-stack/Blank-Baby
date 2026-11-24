package jp.oror.reborn.mixin;

import java.util.List;
import jp.oror.reborn.duel.TalismanShow;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** (r71) Each Duel Dominion talisman cast is seen ({@link TalismanShow}); every cast goes through this one (the other calls it). */
@Pseudo
@Mixin(targets = "jp.oror.dueldominion.RitualCasting", remap = false)
public abstract class DuelTalismanShowMixin {
    @Inject(method = "cast(Lnet/minecraft/server/level/ServerPlayer;Ljp/oror/dueldominion/RitualPolicy$Talisman;Ljava/util/List;Lnet/minecraft/world/item/ItemStack;Lnet/minecraft/world/entity/LivingEntity;)Z",
        at = @At("RETURN"), require = 0)
    private static void oror$seen(ServerPlayer p, jp.oror.dueldominion.RitualPolicy.Talisman t, List<ItemStack> spirits, ItemStack ofuda, LivingEntity target,
        CallbackInfoReturnable<Boolean> cir) {
        if (Boolean.TRUE.equals(cir.getReturnValue())) {
            try {
                TalismanShow.cast(p, t.name(), target);
            } catch (RuntimeException ignored) {
            }
        }
    }
}
