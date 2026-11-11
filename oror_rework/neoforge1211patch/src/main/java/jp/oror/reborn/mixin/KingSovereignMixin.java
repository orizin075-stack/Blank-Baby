package jp.oror.reborn.mixin;

import jp.oror.reborn.king.KingForms;
import jp.oror.reborn.royal.RoyalMob;
import net.minecraft.world.damagesource.DamageSource;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** (054) The villager king's forms: his return from death (KingForms.reborn) and his deeds in each form (KingForms.tick). */
@Mixin(targets = "jp.oror.reborn.royal.RoyalSovereign", remap = false)
public abstract class KingSovereignMixin {
    @Shadow(remap = false)
    @Final
    private RoyalMob mob;

    @Shadow(remap = false)
    private int phase;

    @Unique
    private int oror$before;

    @Inject(method = "onDeath(Lnet/minecraft/world/damagesource/DamageSource;)Z", at = @At("HEAD"), remap = false)
    private void oror$beforeDeath(DamageSource src, CallbackInfoReturnable<Boolean> cir) {
        this.oror$before = this.phase;
    }

    @Inject(method = "onDeath(Lnet/minecraft/world/damagesource/DamageSource;)Z", at = @At("RETURN"), remap = false)
    private void oror$afterDeath(DamageSource src, CallbackInfoReturnable<Boolean> cir) {
        if (cir.getReturnValueZ() && this.phase > this.oror$before) {
            KingForms.reborn(this.mob, this.phase);
        }
    }

    /** (059) Where a blow met his AT field, for the membrane drawn round him (ATFieldHits; the reckoning is untouched). */
    @Inject(method = "beginHurt(Lnet/minecraft/world/damagesource/DamageSource;F)Z", at = @At("HEAD"), remap = false)
    private void oror$fieldStruck(DamageSource src, float amount, CallbackInfoReturnable<Boolean> cir) {
        jp.oror.reborn.royal.ATFieldHits.struck(this.mob, src, amount);
    }

    @Inject(method = "tick()V", at = @At("TAIL"), remap = false)
    private void oror$deeds(CallbackInfo ci) {
        KingForms.tick(this.mob, this.phase);
    }
}
