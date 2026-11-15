package jp.oror.reborn.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.Constant;
import org.spongepowered.asm.mixin.injection.ModifyConstant;

/**
 * (059g, the user: "それぞれ１０００００ぐらいにして　上限なんて関係ない") A god's definition may give it more than 1,024 health:
 * CharacterSpec's loader held every definition's health to Minecraft's old cap and refused the 41 gods' 100,000
 * (CI 56: "Invalid kokuhaku", the game would not start). MaxHealthCapMixin lifts the cap itself.
 */
@Mixin(targets = "jp.oror.reborn.CharacterSpec", remap = false)
public abstract class CharacterHealthCapMixin {
    @ModifyConstant(method = "load()Ljava/util/Map;", constant = @Constant(floatValue = 1024.0F), remap = false)
    private static float oror$noCap(float cap) {
        return 1.0E9F;
    }
}
