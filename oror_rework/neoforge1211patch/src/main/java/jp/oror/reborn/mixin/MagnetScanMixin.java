package jp.oror.reborn.mixin;

import java.util.stream.Stream;
import jp.oror.reborn.perf.MagnetScan;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Alex's Caves' magnet scans answered "none" from MagnetScan where no magnet can be near (see there). */
@Pseudo
@Mixin(targets = "com.github.alexmodguy.alexscaves.server.entity.util.MagnetUtil", remap = false)
public abstract class MagnetScanMixin {
    @Shadow(remap = false)
    private static Stream<BlockPos> getNearbyAttractingMagnets(BlockPos pos, ServerLevel level, int range) {
        throw new AssertionError();
    }

    @Shadow(remap = false)
    private static Stream<BlockPos> getNearbyRepellingMagnets(BlockPos pos, ServerLevel level, int range) {
        throw new AssertionError();
    }

    @Inject(method = "getNearbyAttractingMagnets", at = @At("HEAD"), cancellable = true, remap = false, require = 0)
    private static void oror$attracting(BlockPos pos, ServerLevel level, int range, CallbackInfoReturnable<Stream<BlockPos>> cir) {
        if (MagnetScan.none(level, pos, range, 0, (c, r) -> getNearbyAttractingMagnets(c, level, r).findAny().isPresent())) {
            cir.setReturnValue(Stream.empty());
        }
    }

    @Inject(method = "getNearbyRepellingMagnets", at = @At("HEAD"), cancellable = true, remap = false, require = 0)
    private static void oror$repelling(BlockPos pos, ServerLevel level, int range, CallbackInfoReturnable<Stream<BlockPos>> cir) {
        if (MagnetScan.none(level, pos, range, 1, (c, r) -> getNearbyRepellingMagnets(c, level, r).findAny().isPresent())) {
            cir.setReturnValue(Stream.empty());
        }
    }
}
