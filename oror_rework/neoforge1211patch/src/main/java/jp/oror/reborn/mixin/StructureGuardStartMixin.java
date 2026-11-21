package jp.oror.reborn.mixin;

import jp.oror.reborn.worldgen.StructureGuard;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import net.minecraft.world.level.levelgen.structure.pieces.PiecesContainer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** (r63) Each structure start, made or loaded: its OROR pieces' boxes to StructureGuard. */
@Mixin(StructureStart.class)
public abstract class StructureGuardStartMixin {
    @Inject(method = "<init>", at = @At("RETURN"))
    private void oror$guard(Structure structure, ChunkPos chunkPos, int references, PiecesContainer pieces, CallbackInfo ci) {
        StructureGuard.started((StructureStart) (Object) this);
    }
}
