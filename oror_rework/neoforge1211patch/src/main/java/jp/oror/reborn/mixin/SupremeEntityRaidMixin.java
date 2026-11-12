package jp.oror.reborn.mixin;

import jp.oror.reborn.SupremeEntity;
import jp.oror.reborn.raid.Raid;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Constant;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.ModifyConstant;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * (059e) The raid ({@link Raid}) in the god's own code: its hurt begins and ends a raid blow (inside it the lore gives
 * way: no ABSOLUTE nothing, no thousandth), its heal and its undying follow the raid, the lore's 10% (Chaos's closed
 * core) and 25% (Riha's mana, Shinra's same kind) are 40% and 50% in a raid, and its boss bar shows the raid.
 * Nothing here is required: if the god's code is not as expected, the god is as before.
 */
@Mixin(value = SupremeEntity.class, remap = false)
public abstract class SupremeEntityRaidMixin {
    @Inject(method = "hurt(Lnet/minecraft/world/damagesource/DamageSource;F)Z", at = @At("HEAD"), require = 0)
    private void oror$raidEnter(DamageSource source, float amount, CallbackInfoReturnable<Boolean> cir) {
        Raid.enter((SupremeEntity) (Object) this, source);
    }

    @Inject(method = "hurt(Lnet/minecraft/world/damagesource/DamageSource;F)Z", at = @At("RETURN"), require = 0)
    private void oror$raidLeave(DamageSource source, float amount, CallbackInfoReturnable<Boolean> cir) {
        Raid.leave();
    }

    @Inject(method = "lore()Z", at = @At("HEAD"), cancellable = true, require = 0)
    private void oror$raidNoLore(CallbackInfoReturnable<Boolean> cir) {
        if (Raid.struck(this)) {
            cir.setReturnValue(false);
        }
    }

    @ModifyConstant(method = "hurt(Lnet/minecraft/world/damagesource/DamageSource;F)Z", constant = @Constant(floatValue = 0.1F), require = 0)
    private float oror$raidCore(float v) {
        return Raid.struck(this) ? 0.4F : v;
    }

    @ModifyConstant(method = "hurt(Lnet/minecraft/world/damagesource/DamageSource;F)Z", constant = @Constant(floatValue = 0.25F), require = 0)
    private float oror$raidQuarter(float v) {
        return Raid.struck(this) ? 0.5F : v;
    }

    @Inject(method = "heal(F)V", at = @At("HEAD"), cancellable = true, require = 0)
    private void oror$raidHeal(float amount, CallbackInfo ci) {
        SupremeEntity self = (SupremeEntity) (Object) this;
        if (!self.level().isClientSide && Raid.active(self)) {
            Raid.heal(self, amount);
            ci.cancel();
        }
    }

    @Inject(method = "immortal()Z", at = @At("HEAD"), cancellable = true, require = 0)
    private void oror$raidFall(CallbackInfoReturnable<Boolean> cir) {
        if (Raid.slainInRaid((SupremeEntity) (Object) this)) {
            cir.setReturnValue(false);
        }
    }

    @Redirect(method = "tick()V", at = @At(value = "INVOKE",
        target = "Lnet/minecraft/server/level/ServerBossEvent;setName(Lnet/minecraft/network/chat/Component;)V"), require = 0)
    private void oror$raidBarName(ServerBossEvent bar, Component name) {
        Component raid = Raid.title((SupremeEntity) (Object) this);
        bar.setName(raid != null ? raid : name);
        bar.setColor(raid != null ? BossEvent.BossBarColor.RED : BossEvent.BossBarColor.PURPLE);
        bar.setOverlay(raid != null ? BossEvent.BossBarOverlay.NOTCHED_10 : BossEvent.BossBarOverlay.PROGRESS);
    }

    @Redirect(method = "tick()V", at = @At(value = "INVOKE", target = "Lnet/minecraft/server/level/ServerBossEvent;setVisible(Z)V"), require = 0)
    private void oror$raidBarShown(ServerBossEvent bar, boolean visible) {
        bar.setVisible(visible || Raid.active((SupremeEntity) (Object) this));
    }
}
