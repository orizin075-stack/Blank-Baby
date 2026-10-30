package jp.oror.reborn.mixin;

import jp.oror.reborn.citadel.CitadelSites;
import net.minecraft.core.RegistryAccess;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.chunk.ChunkGeneratorStructureState;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplateManager;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** No other structure starts in or near a Grand Citadel (sites avoid strongholds, so the End stays reachable). */
@Mixin(ChunkGenerator.class)
public abstract class CitadelStructureMixin {
    @Inject(method = "createStructures", at = @At("HEAD"), cancellable = true)
    private void oror$keepCitadelClear(RegistryAccess registries, ChunkGeneratorStructureState state, StructureManager structures,
                                       ChunkAccess chunk, StructureTemplateManager templates, CallbackInfo ci) {
        if (CitadelSites.excludesStructures((ChunkGenerator) (Object) this, chunk.getPos())) {
            ci.cancel();
        }
    }
}
