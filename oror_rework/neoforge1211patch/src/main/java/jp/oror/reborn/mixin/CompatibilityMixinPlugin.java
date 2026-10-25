package jp.oror.reborn.mixin;

import java.util.List;
import java.util.Map;
import java.util.Set;
import net.neoforged.fml.loading.LoadingModList;
import org.objectweb.asm.tree.ClassNode;
import org.spongepowered.asm.mixin.extensibility.IMixinConfigPlugin;
import org.spongepowered.asm.mixin.extensibility.IMixinInfo;

/**
 * Applies a mixin only when the mods it needs are present.
 *
 * 0.17.25: the mixins on Nightfall's and Indestructible's classes (or that call them) are skipped without those mods.
 * The config is "required", so before, a profile where SETUP_NIGHTFALL.cmd had not been run, or an update without the
 * Indestructible compatibility jar, stopped at start-up on a mixin error instead of loading and saying what is missing.
 */
public final class CompatibilityMixinPlugin implements IMixinConfigPlugin {
    private static final Map<String, String> NEEDS = Map.ofEntries(
        Map.entry("OfflinePatreonMixin", "tenshilib"),
        Map.entry("NightfallGuardInputMixin", "efn"),
        Map.entry("NightfallParryWeaponsMixin", "efn"),
        Map.entry("NightfallGradualHealMixin", "efn"),
        Map.entry("NightfallEnemyGoalsMixin", "indestructible"),
        Map.entry("NightfallEnemyParryWindowMixin", "indestructible"),
        Map.entry("NightfallEnemyRecoveryMixin", "indestructible"),
        Map.entry("NightfallIntegratedProviderMixin", "indestructible"),
        Map.entry("NightfallNativeParryFeedbackMixin", "indestructible"));

    @Override
    public boolean shouldApplyMixin(String target, String mixin) {
        String name = mixin.substring(mixin.lastIndexOf('.') + 1);
        if (name.equals("SuppressionConfigSyncMixin")) {
            LoadingModList mods = LoadingModList.get();
            return mods != null && mods.getMods().stream()
                .anyMatch(mod -> mod.getModId().equals("suppressionmod") && mod.getVersion().toString().equals("1.2.0"));
        }
        String needed = NEEDS.get(name);
        return needed == null || loaded(needed);
    }

    private static boolean loaded(String modId) {
        LoadingModList mods = LoadingModList.get();
        return mods != null && mods.getMods().stream().anyMatch(mod -> mod.getModId().equals(modId));
    }

    @Override
    public void onLoad(String mixinPackage) {
    }

    @Override
    public String getRefMapperConfig() {
        return null;
    }

    @Override
    public void acceptTargets(Set<String> mine, Set<String> others) {
    }

    @Override
    public List<String> getMixins() {
        return null;
    }

    @Override
    public void preApply(String target, ClassNode node, String mixin, IMixinInfo info) {
    }

    @Override
    public void postApply(String target, ClassNode node, String mixin, IMixinInfo info) {
    }
}
