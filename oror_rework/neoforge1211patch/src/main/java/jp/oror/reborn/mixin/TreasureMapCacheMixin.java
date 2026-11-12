package jp.oror.reborn.mixin;

import jp.oror.reborn.perf.MapSearchCache;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.levelgen.structure.Structure;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

/**
 * (059d) A cartographer's explorer map leads where the town's last search found its structure ({@link MapSearchCache}).
 * Nothing here is required: if the game's code is not as expected, maps are made as before.
 */
@Mixin(targets = "net.minecraft.world.entity.npc.VillagerTrades$TreasureMapForEmeralds")
public abstract class TreasureMapCacheMixin {
    @Redirect(method = "getOffer", at = @At(value = "INVOKE",
        target = "Lnet/minecraft/server/level/ServerLevel;findNearestMapStructure(Lnet/minecraft/tags/TagKey;Lnet/minecraft/core/BlockPos;IZ)Lnet/minecraft/core/BlockPos;"),
        require = 0)
    private BlockPos oror$sharedSearch(ServerLevel level, TagKey<Structure> tag, BlockPos from, int radius, boolean skipKnown) {
        return MapSearchCache.find(level, tag, from, radius, skipKnown);
    }
}
