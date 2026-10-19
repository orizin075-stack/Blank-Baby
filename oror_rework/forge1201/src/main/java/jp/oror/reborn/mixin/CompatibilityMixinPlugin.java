package jp.oror.reborn.mixin;

import java.util.List;
import java.util.Set;
import net.minecraftforge.fml.loading.LoadingModList;
import org.objectweb.asm.tree.ClassNode;
import org.spongepowered.asm.mixin.extensibility.IMixinConfigPlugin;
import org.spongepowered.asm.mixin.extensibility.IMixinInfo;

public final class CompatibilityMixinPlugin implements IMixinConfigPlugin {
    public boolean shouldApplyMixin(String target, String mixin) {
        if (mixin.endsWith("OfflinePatreonMixin")) {
            LoadingModList loaded = LoadingModList.get();
            return loaded != null && loaded.getMods().stream().anyMatch(mod -> mod.getModId().equals("tenshilib"));
        } else if (!mixin.endsWith("SuppressionConfigSyncMixin")) {
            return true;
        } else {
            LoadingModList mods = LoadingModList.get();
            return mods != null
                && mods.getMods().stream().anyMatch(mod -> mod.getModId().equals("suppressionmod") && mod.getVersion().toString().equals("1.2.0"));
        }
    }

    public void onLoad(String mixinPackage) {
    }

    public String getRefMapperConfig() {
        return null;
    }

    public void acceptTargets(Set<String> mine, Set<String> others) {
    }

    public List<String> getMixins() {
        return null;
    }

    public void preApply(String target, ClassNode node, String mixin, IMixinInfo info) {
    }

    public void postApply(String target, ClassNode node, String mixin, IMixinInfo info) {
    }
}
