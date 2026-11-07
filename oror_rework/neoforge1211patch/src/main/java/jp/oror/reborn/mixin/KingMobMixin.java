package jp.oror.reborn.mixin;

import jp.oror.reborn.king.KingForms;
import jp.oror.reborn.royal.RoyalThreats;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerPlayer;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * (054) The villager king's boss bars: not shown to a player he comes in sight of unless that player is his enemy
 * (KingCourt keeps them up to date each second), and named after his form (KingForms.bossName).
 */
@Mixin(targets = "jp.oror.reborn.royal.RoyalMob", remap = false)
public abstract class KingMobMixin {
    @Shadow(remap = false)
    @Final
    private ServerBossEvent boss;

    @Shadow(remap = false)
    @Final
    private ServerBossEvent atBoss;

    @Inject(method = "startSeenByPlayer(Lnet/minecraft/server/level/ServerPlayer;)V", at = @At("TAIL"), remap = false)
    private void oror$onlyEnemies(ServerPlayer p, CallbackInfo ci) {
        if (!RoyalThreats.hostilePlayer(p)) {
            this.boss.removePlayer(p);
            this.atBoss.removePlayer(p);
        }
    }

    @Inject(method = "syncSovereign(FIZ)V", at = @At("TAIL"), remap = false)
    private void oror$formName(float field, int phase, boolean breached, CallbackInfo ci) {
        this.boss.setName(KingForms.bossName(phase));
    }
}
