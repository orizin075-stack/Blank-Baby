package jp.oror.reborn.mixin;

import jp.oror.reborn.MobMind;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.util.Locale;

/** (r66) PowerGameTests' six ranks: the duel under way, every ten seconds (POWER-DUEL), to see a rank that does not finish. */
@Mixin(targets = "jp.oror.reborn.PowerGameTests", remap = false)
public abstract class GameTestFixesPowerMixin {
    @Inject(method = "lambda$all_six_ranks_defeat_fully_armored_scripted_survival_fighters$3", at = @At("HEAD"), remap = false, require = 0)
    private static void oror$watch(int[] rank, Villager[] bot, Player[] opponent, GameTestHelper h, long[] started, int[] armor, double[] toughness,
                                   Runnable spawn, CallbackInfo ci) {
        Villager v = bot[0];
        Player p = opponent[0];
        if (rank[0] > 6 || v == null || p == null) {
            return;
        }
        long elapsed = h.getLevel().getGameTime() - started[0];
        if (elapsed <= 0 || elapsed % 200 != 0) {
            return;
        }
        int arrows = h.getLevel().getEntitiesOfClass(Projectile.class, v.getBoundingBox().inflate(32), a -> a.getOwner() == v).size();
        org.slf4j.LoggerFactory.getLogger("OROR GameTest").info(String.format(Locale.ROOT,
            "POWER-DUEL {\"rank\":%d,\"ticks\":%d,\"villager\":\"%.1f/%.1f\",\"alive\":%b,\"player\":\"%.1f\",\"dist\":%.2f,\"main\":\"%s\",\"off\":\"%s\","
                + "\"using\":%b,\"strikes\":%d,\"shots\":%d,\"projectiles\":%d,\"target\":\"%s\",\"playerInWorld\":%b}",
            rank[0], elapsed, v.getHealth(), v.getMaxHealth(), v.isAlive(), p.getHealth(), v.distanceTo(p), v.getMainHandItem().getItem(),
            v.getOffhandItem().getItem(), v.isUsingItem(), MobMind.data(v).getInt("SuccessfulStrikes"), MobMind.data(v).getInt("Shots"), arrows,
            v.getTarget() == null ? "none" : v.getTarget().getType().toShortString(), h.getLevel().getEntity(p.getId()) == p));
    }
}
