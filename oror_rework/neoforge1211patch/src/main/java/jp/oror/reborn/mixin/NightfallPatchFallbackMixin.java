package jp.oror.reborn.mixin;

import com.google.gson.JsonElement;
import com.nameless.indestructible.data.AdvancedMobpatchReloader;
import java.util.HashMap;
import java.util.Map;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.packs.resources.ResourceManager;
import net.minecraft.util.profiling.ProfilerFiller;
import net.neoforged.fml.ModList;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * (r79, the r78 audit: "13 mob patches depend on Nightfall"; the user: "全体的に挙動が変") The pack's Indestructible mob
 * patches for zombies, skeletons, strays, husks, drowned, pillagers, vindicators, piglins, piglin brutes, zombified piglins,
 * wither skeletons and Iron's summoned zombie and skeleton name Nightfall's motions (efn:..., some 2,000 places). Without
 * Nightfall installed (SETUP_NIGHTFALL.cmd not run) those motions are not there: r77 kept the game from crashing, but the
 * mobs then walked up and never struck, and their guard, dodge and strafing hung on motions that never played. Now, when
 * Nightfall is not loaded, a patch that names a Nightfall motion is not read at all, and those mobs fight with Epic Fight's
 * own patches (its standard motions) instead. With Nightfall installed nothing changes.
 */
@Mixin(value = AdvancedMobpatchReloader.class, remap = false)
public abstract class NightfallPatchFallbackMixin {
    @Inject(method = "prepare(Lnet/minecraft/server/packs/resources/ResourceManager;Lnet/minecraft/util/profiling/ProfilerFiller;)Ljava/util/Map;",
        at = @At("RETURN"), cancellable = true, require = 0)
    private void oror$withoutNightfall(ResourceManager manager, ProfilerFiller profiler, CallbackInfoReturnable<Map<ResourceLocation, JsonElement>> cir) {
        Map<ResourceLocation, JsonElement> found = cir.getReturnValue();
        if (found == null || found.isEmpty() || ModList.get() == null || ModList.get().isLoaded("efn")) {
            return;
        }
        Map<ResourceLocation, JsonElement> kept = new HashMap<>();
        int dropped = 0;
        for (Map.Entry<ResourceLocation, JsonElement> e : found.entrySet()) {
            if (e.getValue() != null && e.getValue().toString().contains("\"efn:")) {
                dropped++;
            } else {
                kept.put(e.getKey(), e.getValue());
            }
        }
        if (dropped > 0) {
            System.out.println("[OROR] Nightfall is not installed: " + dropped + " mob patches that use its motions left out (those mobs fight with Epic Fight's own motions; run SETUP_NIGHTFALL.cmd for Nightfall's)");
            cir.setReturnValue(kept);
        }
    }
}
