package jp.oror.reborn.mixin;

import java.util.List;
import java.util.Set;
import org.objectweb.asm.tree.ClassNode;
import org.spongepowered.asm.mixin.extensibility.IMixinConfigPlugin;
import org.spongepowered.asm.mixin.extensibility.IMixinInfo;

public final class CompatibilityMixinPlugin implements IMixinConfigPlugin {
    /**
     * Forge 1.20.1 port: only the vanilla mixins remain (the arrow-save fix, the Suppression config broadcast and the
     * offline TenshiLib supporter list were for the 1.21.1 builds of those mods).
     */
    public boolean shouldApplyMixin(String target, String mixin) {
        return true;
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
