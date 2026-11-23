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

/** (r66) PowerGameTests' six ranks: the fighter walks after the villager; the duel under way, every ten seconds (POWER-DUEL). */
@Mixin(targets = "jp.oror.reborn.PowerGameTests", remap = false)
public abstract class GameTestFixesPowerMixin {
    @Inject(method = "lambda$all_six_ranks_defeat_fully_armored_scripted_survival_fighters$3", at = @At("HEAD"), remap = false, require = 1)
    private static void oror$watch(int[] rank, Villager[] bot, Player[] opponent, GameTestHelper h, long[] started, int[] armor, double[] toughness,
                                   Runnable spawn, CallbackInfo ci) {
        Villager v = bot[0];
        Player p = opponent[0];
        if (rank[0] > 6 || v == null || p == null) {
            return;
        }
        long elapsed = h.getLevel().getGameTime() - started[0];
        // (r66) the scripted fighter goes after the villager as a player does (a walk, 0.22 blocks a tick, to arm's
        // reach). It stood still: a villager that backed out of its reach (a dodge, a roll) and was no longer cornered
        // put its weapon away and stood off ten blocks for good, a civilian, and the rank never ended (POWER-DUEL, rank 2)
        if (p.isAlive() && v.isAlive() && v.distanceToSqr(p) > 2.2 * 2.2) {
            net.minecraft.world.phys.Vec3 to = v.position().subtract(p.position());
            net.minecraft.world.phys.Vec3 step = new net.minecraft.world.phys.Vec3(to.x, 0, to.z);
            if (step.lengthSqr() > 1.0E-4) {
                step = step.normalize().scale(Math.min(0.22, Math.sqrt(step.lengthSqr()) - 2.0));
                float yaw = (float) (Math.atan2(to.z, to.x) * 180.0 / Math.PI) - 90.0F;
                p.moveTo(p.getX() + step.x, v.getY(), p.getZ() + step.z, yaw, 0.0F);
            }
        }
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
