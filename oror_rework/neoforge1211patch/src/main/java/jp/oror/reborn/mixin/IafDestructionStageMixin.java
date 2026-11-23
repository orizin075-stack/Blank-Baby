package jp.oror.reborn.mixin;

import jp.oror.reborn.worldgen.StructureGuard;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * (r66) Nor its breath and its charge (IafDragonDestructionManager: each block it burns, freezes, shocks or breaks): the
 * blocks of OROR's buildings stay as they are; what the breath does to bodies is as before.
 */
@Pseudo
@Mixin(targets = "com.iafenvoy.iceandfire.entity.util.dragon.IafDragonDestructionManager", remap = false)
public abstract class IafDestructionStageMixin {
    @Inject(method = "attackBlock(Lnet/minecraft/world/level/Level;Lcom/iafenvoy/iceandfire/entity/DragonBaseEntity;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;)V",
        at = @At("HEAD"), cancellable = true, remap = false, require = 0)
    private static void oror$attack(Level level, @org.spongepowered.asm.mixin.injection.Coerce Entity dragon, BlockPos pos, BlockState state, CallbackInfo ci) {
        if (StructureGuard.insideOrUnder(pos)) {
            jp.oror.reborn.village.BuildingGuard.dragonSpared(pos);
            ci.cancel();
        }
    }

    @Inject(method = "attackBlock(Lnet/minecraft/world/level/Level;Lcom/iafenvoy/iceandfire/entity/DragonBaseEntity;Lnet/minecraft/core/BlockPos;)V",
        at = @At("HEAD"), cancellable = true, remap = false, require = 0)
    private static void oror$attack2(Level level, @org.spongepowered.asm.mixin.injection.Coerce Entity dragon, BlockPos pos, CallbackInfo ci) {
        if (StructureGuard.insideOrUnder(pos)) {
            jp.oror.reborn.village.BuildingGuard.dragonSpared(pos);
            ci.cancel();
        }
    }

    /** destroyBlocks' block by block (its lambda: the centre, the radius, the level, the dragon, the block). */
    @Inject(method = "lambda$destroyBlocks$6(Lnet/minecraft/core/BlockPos;DLnet/minecraft/world/level/Level;Lnet/minecraft/world/entity/Entity;Lnet/minecraft/core/BlockPos;)V",
        at = @At("HEAD"), cancellable = true, remap = false, require = 0)
    private static void oror$destroy(BlockPos centre, double radius, Level level, Entity dragon, BlockPos pos, CallbackInfo ci) {
        if (StructureGuard.insideOrUnder(pos)) {
            jp.oror.reborn.village.BuildingGuard.dragonSpared(pos);
            ci.cancel();
        }
    }

    @Inject(method = "lambda$destroyAreaCharge$4(Lnet/minecraft/core/BlockPos;FLnet/minecraft/world/level/Level;Lcom/iafenvoy/iceandfire/entity/DragonBaseEntity;Lnet/minecraft/core/BlockPos;)V",
        at = @At("HEAD"), cancellable = true, remap = false, require = 0)
    private static void oror$charge(BlockPos centre, float radius, Level level, @org.spongepowered.asm.mixin.injection.Coerce Entity dragon, BlockPos pos, CallbackInfo ci) {
        if (StructureGuard.insideOrUnder(pos)) {
            jp.oror.reborn.village.BuildingGuard.dragonSpared(pos);
            ci.cancel();
        }
    }

    @Inject(method = "lambda$destroyAreaCharge$3(Lnet/minecraft/world/level/Level;Lcom/iafenvoy/iceandfire/entity/DragonBaseEntity;Lnet/minecraft/core/BlockPos;Lnet/minecraft/core/BlockPos;)V",
        at = @At("HEAD"), cancellable = true, remap = false, require = 0)
    private static void oror$charge2(Level level, @org.spongepowered.asm.mixin.injection.Coerce Entity dragon, BlockPos centre, BlockPos pos, CallbackInfo ci) {
        if (StructureGuard.insideOrUnder(pos)) {
            jp.oror.reborn.village.BuildingGuard.dragonSpared(pos);
            ci.cancel();
        }
    }
}
