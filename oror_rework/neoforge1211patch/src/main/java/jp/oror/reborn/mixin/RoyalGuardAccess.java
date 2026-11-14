package jp.oror.reborn.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;

/** (059f) A royal's own guard (RoyalMob.defend), for MobGuard to show its raising as every other mob's. */
@Mixin(targets = "jp.oror.reborn.royal.RoyalMob", remap = false)
public interface RoyalGuardAccess {
    @Accessor(value = "guardRemaining", remap = false)
    int oror$guardRemaining();

    @Accessor(value = "guardAge", remap = false)
    int oror$guardAge();
}
