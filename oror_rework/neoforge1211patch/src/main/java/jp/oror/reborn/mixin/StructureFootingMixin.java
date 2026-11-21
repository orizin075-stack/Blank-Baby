package jp.oror.reborn.mixin;

import jp.oror.reborn.worldgen.StructureFooting;
import net.minecraft.core.BlockPos;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.PoolElementStructurePiece;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** (r62) After one of OROR's templates is placed in a chunk: the ground left inside it cleared, a footing under it. */
@Mixin(PoolElementStructurePiece.class)
public abstract class StructureFootingMixin {
    @Inject(method = "place", at = @At("TAIL"))
    private void oror$footing(WorldGenLevel level, StructureManager structures, ChunkGenerator generator, RandomSource random,
                              BoundingBox box, BlockPos pos, boolean keepJigsaws, CallbackInfo ci) {
        StructureFooting.after((PoolElementStructurePiece) (Object) this, level, box);
    }
}
