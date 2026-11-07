package jp.oror.reborn.mixin;

import io.redspace.ironsspellbooks.api.spells.SpellData;
import java.util.List;
import jp.oror.reborn.royal.RoyalRole;
import jp.oror.reborn.royal.RoyalSpellSafety;
import jp.oror.reborn.royal.RoyalSpells;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** (053) The royals' spells: only Iron's own fighting spells (RoyalSpellSafety). */
@Mixin(value = RoyalSpells.class, remap = false)
public abstract class RoyalSpellsCatalogMixin {
    @Inject(method = "catalog", at = @At("RETURN"), cancellable = true, remap = false)
    private static void oror$safe(RoyalRole role, CallbackInfoReturnable<List<SpellData>> cir) {
        cir.setReturnValue(RoyalSpellSafety.filter(cir.getReturnValue()));
    }
}
