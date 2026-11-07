package jp.oror.reborn.mixin;

import java.util.stream.Stream;
import jp.oror.reborn.perf.MagnetRegions;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** (053) Alex's Caves' magnet searches answered "none" where its section has no magnet near (MagnetRegions). */
@Pseudo
@Mixin(targets = "com.github.alexmodguy.alexscaves.server.entity.util.MagnetUtil", remap = false)
public abstract class AcMagnetMixin {
    @Inject(method = "getNearbyAttractingMagnets(Lnet/minecraft/core/BlockPos;Lnet/minecraft/server/level/ServerLevel;I)Ljava/util/stream/Stream;",
        at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$attracting(BlockPos pos, ServerLevel level, int range, CallbackInfoReturnable<Stream<BlockPos>> cir) {
        if (MagnetRegions.none(pos, level, range, true)) {
            cir.setReturnValue(Stream.empty());
        }
    }

    @Inject(method = "getNearbyRepellingMagnets(Lnet/minecraft/core/BlockPos;Lnet/minecraft/server/level/ServerLevel;I)Ljava/util/stream/Stream;",
        at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$repelling(BlockPos pos, ServerLevel level, int range, CallbackInfoReturnable<Stream<BlockPos>> cir) {
        if (MagnetRegions.none(pos, level, range, false)) {
            cir.setReturnValue(Stream.empty());
        }
    }
}
