package jp.oror.reborn.mixin;

import it.unimi.dsi.fastutil.longs.LongSet;
import jp.oror.reborn.safety.EntityUnloads;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.entity.PersistentEntitySectionManager;
import net.minecraft.world.level.entity.Visibility;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * (058) Entities' chunks unload from a copy of their list (see {@link EntityUnloads}). Nothing here is required: if
 * the game's code is not as expected, the game runs as it did (the log says whether this is active).
 */
@Mixin(PersistentEntitySectionManager.class)
public abstract class SafeEntityUnloadMixin {
    @Redirect(method = "processUnloads", at = @At(value = "INVOKE",
        target = "Lit/unimi/dsi/fastutil/longs/LongSet;removeIf(Lit/unimi/dsi/fastutil/longs/LongPredicate;)Z", remap = false), require = 0)
    private boolean oror$unloadFromCopy(LongSet set, it.unimi.dsi.fastutil.longs.LongPredicate each) {
        return EntityUnloads.safely(set, each);
    }

    @Redirect(method = "processUnloads", at = @At(value = "INVOKE",
        target = "Lit/unimi/dsi/fastutil/longs/LongSet;removeIf(Ljava/util/function/LongPredicate;)Z", remap = false), require = 0)
    private boolean oror$unloadFromCopyJava(LongSet set, java.util.function.LongPredicate each) {
        return EntityUnloads.safely(set, each);
    }

    @Inject(method = "updateChunkStatus(Lnet/minecraft/world/level/ChunkPos;Lnet/minecraft/world/level/entity/Visibility;)V", at = @At("HEAD"),
        require = 0)
    private void oror$noteStatusChange(ChunkPos pos, Visibility visibility, CallbackInfo ci) {
        EntityUnloads.statusChanged();
    }
}
