package jp.oror.reborn.mixin;

import net.minecraft.nbt.CompoundTag;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * (059e) The user's OROR Duel Dominion 0.17.0-alpha: when a mob is sealed into its bound hair (SealSummoning.capture,
 * its recall and its death record), SealSummoning.sanitize means to strip the mob's save of its owner, its binding and
 * a possession's marks, but it looks for them at the top of the save, where they are not: they live in the mob's
 * persistent data (the save's "NeoForgeData"). So a sealed mob kept them, and a mob possessed when it was saved came
 * back marked as possessed (and, had it been saved while possessed, without its AI). Here they go from there too, and with them an OROR god's raid ({@code ororRaid}: a god
 * sealed by a duel it lost would come back carrying its raid's empty health). Its standing order (STAY / FOLLOW) is
 * kept. Without Duel Dominion this does nothing.
 */
@Pseudo
@Mixin(targets = "jp.oror.dueldominion.SealSummoning", remap = false)
public abstract class DuelSealSanitizeMixin {
    @Inject(method = "sanitize(Lnet/minecraft/nbt/CompoundTag;)Lnet/minecraft/nbt/CompoundTag;", at = @At("RETURN"), require = 0)
    private static void oror$persistentToo(CompoundTag raw, CallbackInfoReturnable<CompoundTag> cir) {
        CompoundTag copy = cir.getReturnValue();
        if (copy != null && copy.contains("NeoForgeData", 10)) {
            CompoundTag data = copy.getCompound("NeoForgeData");
            if (data.hasUUID("DuelPossessedBy")) {
                // saved while possessed: its own NoAI back, not the possession's
                copy.putBoolean("NoAI", data.getBoolean("DuelOriginalNoAI"));
            }
            for (String key : new String[]{"DuelDominionOwner", "DuelDominionBinding", "DuelPossessedBy", "DuelOriginalNoAI", "ororRaid"}) {
                data.remove(key);
            }
        }
    }
}
