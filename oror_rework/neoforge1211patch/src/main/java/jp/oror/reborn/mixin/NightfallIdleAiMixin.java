package jp.oror.reborn.mixin;

import jp.oror.reborn.compat.NightfallPatchSettings;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.npc.Villager;
import net.neoforged.neoforge.event.tick.EntityTickEvent;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * 0.17.22: AdaptiveCombat's extra work for an idle mob runs every idleAiInterval ticks (every distantAiInterval with no
 * player within 64 blocks), on the ticks where tickCount matches the mob's id, so its own tickCount-keyed timers still
 * line up. Mobs with a target, just hurt, in the air, and the Supreme characters run every tick.
 *
 * 0.17.24: villagers run every tick too. VillageAI keys its threat scans to the world clock ((gameTime + id) % 10 for a
 * strong villager looking for a foe, and for a civilian looking for danger to flee), which only coincides with the
 * throttled ticks for one villager in five: the rest never noticed an enemy until it hit them.
 */
@Mixin(targets = "jp.oror.reborn.AdaptiveCombat", remap = false)
public abstract class NightfallIdleAiMixin {
    @Inject(method = "tick", at = @At("HEAD"), cancellable = true)
    private static void oror$spreadIdleWork(EntityTickEvent.Post event, CallbackInfo ci) {
        if (!(event.getEntity() instanceof Mob mob) || !(mob.level() instanceof ServerLevel level)) {
            return;
        }
        if (mob instanceof Villager || mob.getTarget() != null || mob.isNoAi() || !mob.onGround() || mob.hurtTime > 0
            || mob.getLastHurtByMob() != null && mob.tickCount - mob.getLastHurtByMobTimestamp() < 100
            || mob.getClass().getName().equals("jp.oror.reborn.SupremeEntity")) {
            return;
        }
        int idle = NightfallPatchSettings.IDLE_INTERVAL;
        if (Math.floorMod(mob.tickCount, idle) != Math.floorMod(mob.getId(), idle)) {
            ci.cancel();
            return;
        }
        int distant = NightfallPatchSettings.DISTANT_INTERVAL;
        if (!level.hasNearbyAlivePlayer(mob.getX(), mob.getY(), mob.getZ(), 64.0)
            && Math.floorMod(mob.tickCount, distant) != Math.floorMod(mob.getId(), distant)) {
            ci.cancel();
        }
    }
}
