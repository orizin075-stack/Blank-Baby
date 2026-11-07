package jp.oror.reborn.mixin;

import net.minecraft.server.level.ServerBossEvent;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;

/** (054) The villager king's boss bars, for KingCourt to show to his enemies alone. */
@Mixin(targets = "jp.oror.reborn.royal.RoyalMob", remap = false)
public interface RoyalMobBossAccess {
    @Accessor(value = "boss", remap = false)
    ServerBossEvent oror$boss();

    @Accessor(value = "atBoss", remap = false)
    ServerBossEvent oror$atBoss();
}
