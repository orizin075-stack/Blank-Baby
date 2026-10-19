package jp.oror.reborn;

import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;
import java.util.function.Consumer;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraftforge.event.entity.living.LivingAttackEvent;
import net.minecraftforge.event.entity.living.LivingHurtEvent;

/**
 * Forge 1.20.1 stand-in for NeoForge's LivingIncomingDamageEvent, which the mod's damage handlers were written for.
 * That event fired at the top of LivingEntity.hurt, and cancelling it made hurt return false: no knockback, no
 * invulnerability frames, no revenge target, no on-hit effects. Forge's LivingHurtEvent fires later, inside
 * actuallyHurt, where a cancel only skips the health loss. So the handlers run once, from LivingAttackEvent (the top of
 * hurt), on a LivingHurtEvent of their own: a cancel cancels the attack, and a changed amount is carried over to the
 * Forge LivingHurtEvent of the same hit.
 */
public final class IncomingDamage {
    // in the order the 1.21.1 build registered them; all at normal priority, so a cancel stops the rest
    private static final List<Consumer<LivingHurtEvent>> HANDLERS = List.of(
        AdaptiveCombat::damage, NightfallFusion::damage, NightfallArsenal::damage, RelicPowers::damage, AdventureContent::damage,
        WorldEvents::damage
    );
    private static final Map<LivingEntity, Pending> PENDING = new WeakHashMap<>();

    private record Pending(DamageSource source, float asked, float given) {
    }

    public static void attack(LivingAttackEvent e) {
        LivingEntity v = e.getEntity();
        PENDING.remove(v);
        DamageSource s = e.getSource();
        // the checks LivingEntity.hurt (and Player.hurt) made before NeoForge fired the event
        if (v.level().isClientSide || v.isInvulnerableTo(s) || v.isDeadOrDying()
            || s.is(DamageTypeTags.IS_FIRE) && v.hasEffect(MobEffects.FIRE_RESISTANCE)
            || v instanceof Player p && p.getAbilities().invulnerable && !s.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            return;
        }
        LivingHurtEvent incoming = new LivingHurtEvent(v, s, e.getAmount());
        for (Consumer<LivingHurtEvent> handler : HANDLERS) {
            handler.accept(incoming);
            if (incoming.isCanceled()) {
                e.setCanceled(true);
                return;
            }
        }
        if (incoming.getAmount() != e.getAmount()) {
            PENDING.put(v, new Pending(s, e.getAmount(), incoming.getAmount()));
        }
    }

    /** Registered at the highest priority, so other mods' hurt listeners see the amount the handlers settled on. */
    public static void hurt(LivingHurtEvent e) {
        Pending p = PENDING.remove(e.getEntity());
        if (p == null || p.source != e.getSource()) {
            return;
        }
        if (e.getAmount() == p.asked || p.asked <= 0.0F) {
            e.setAmount(p.given);
        } else {
            // vanilla changed the amount between the two events (invulnerability frames, a helmet, a raised shield,
            // a player's difficulty scaling): keep the handlers' proportion
            e.setAmount(e.getAmount() * (p.given / p.asked));
        }
    }

    private IncomingDamage() {
    }
}
