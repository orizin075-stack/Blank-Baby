package jp.oror.reborn.combat;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import jp.oror.reborn.EfStamina;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.entity.player.AttackEntityEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;
import net.neoforged.neoforge.network.PacketDistributor;

/**
 * (r73, the user: "ナイトフォールクラフトとかのスタミナシステムとバーも追加　プレイヤーだけじゃなく全モブに　スタミナがなくなった時や
 * その際に攻撃した時の処理も確認して実装") Stamina for everyone, as NightfallCraft has it (Epic Fight's stamina, its bar under the
 * health in Ares HUD), and what running out of it means.
 * <p>
 * The players: their stamina is Epic Fight's (the bar the pack shows; OROR keeps one of its own only for a player Epic
 * Fight has no patch for). Epic Fight's dodges and guard draw on it as before; now a swing at something draws on it too
 * (an eighth of it, more for a heavy, slow weapon), and so do running (about a twelfth a second) and jumping (a
 * twenty-fifth). The mobs: every mob's own blow draws on its stamina (MobStamina; it was only the fighters'), and every
 * mob running (fleeing, charging, a beast in panic) wears it down; their bars, over their heads, show when not full.
 * <p>
 * Out of it (under a fiftieth for a player, a tenth for a mob): exhausted (息切れ) until it is back to three tenths:
 * <ul>
 * <li>no running, slowed; no dodge and no guard (Epic Fight's and OROR's ask for stamina it has not got);</li>
 * <li>a blow struck exhausted lands at half its weight for a player, and its rest begins again (striking on does not get
 * one's wind back); a mob's at six tenths (its rest goes on: the village fighters' trials, CI 68);</li>
 * <li>a blow taken exhausted lands a quarter harder (nothing to meet it with);</li>
 * <li>seen and heard: breathing hard, sweat; a player's own screen pulses red at its edges (ExhaustionHud), and its bar
 * flashes red over its head for the others, as a mob's does.</li>
 * </ul>
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class Exhaustion {
    public static final float OUT = 0.02F, BACK = 0.30F, STRUCK = 0.5F, STRUCK_MOB = 0.6F, TAKEN = 1.25F;

    /** OROR's own store for a player Epic Fight keeps none for, and every player's exhausted state. */
    static final class Wind {
        float own = -1F, ownMax = 15F;
        boolean exhausted;
        long since, spentAt = -100, sentAt = -100;
        int sentPercent = -1;
        boolean sentExhausted;
    }

    private static final Map<UUID, Wind> WINDS = new ConcurrentHashMap<>();
    public static int exhaustedBlows, exhaustedHits, exhaustions;

    private Exhaustion() {
    }

    static Wind wind(Player p) {
        return WINDS.computeIfAbsent(p.getUUID(), k -> new Wind());
    }

    /** {stamina, max} of a player: Epic Fight's, or OROR's own. */
    public static float[] of(Player p) {
        float[] ef = EfStamina.of(p);
        if (ef != null && ef[1] > 0) {
            return ef;
        }
        Wind w = wind(p);
        if (w.own < 0) {
            w.own = w.ownMax;
        }
        return new float[]{w.own, w.ownMax};
    }

    public static void put(Player p, float value) {
        if (!EfStamina.put(p, value)) {
            Wind w = wind(p);
            w.own = Math.max(0F, Math.min(w.ownMax, value));
        }
    }

    /** Takes from a player's stamina (no lower than nothing). */
    public static void spend(Player p, float cost) {
        float[] s = of(p);
        put(p, Math.max(0F, s[0] - cost));
        wind(p).spentAt = p.level().getGameTime();
        check(p);
    }

    public static boolean exhausted(LivingEntity e) {
        if (e instanceof Player p) {
            Wind w = WINDS.get(p.getUUID());
            return w != null && w.exhausted;
        }
        return e instanceof Mob m && MobStamina.winded(m);
    }

    /** Whether the player has just run out, or has its wind back; and what it shows. */
    public static void check(Player p) {
        if (p.level().isClientSide || p.isCreative() || p.isSpectator()) {
            return;
        }
        Wind w = wind(p);
        float[] s = of(p);
        float frac = s[1] <= 0 ? 1F : s[0] / s[1];
        long now = p.level().getGameTime();
        if (!w.exhausted && frac <= OUT) {
            w.exhausted = true;
            w.since = now;
            exhaustions++;
            p.getPersistentData().putInt("OrorExhausted", p.getPersistentData().getInt("OrorExhausted") + 1);
            if (p.level() instanceof ServerLevel sl) {
                sl.playSound(null, p.blockPosition(), SoundEvents.HORSE_BREATHE, SoundSource.PLAYERS, 0.9F, 0.75F);
                sl.sendParticles(ParticleTypes.POOF, p.getX(), p.getEyeY() - 0.1, p.getZ(), 5, 0.15, 0.05, 0.15, 0.01);
            }
        } else if (w.exhausted && frac >= BACK && now - w.since >= 30) {
            w.exhausted = false;
        }
        send(p, w, frac);
    }

    private static void send(Player p, Wind w, float frac) {
        if (!(p instanceof ServerPlayer sp) || sp.connection == null) {
            return;
        }
        long now = p.level().getGameTime();
        int percent = Math.round(frac * 100F);
        if (now - w.sentAt < 5 || Math.abs(percent - w.sentPercent) < 3 && w.exhausted == w.sentExhausted && !(percent == 100 && w.sentPercent != 100)) {
            return;
        }
        w.sentAt = now;
        w.sentPercent = percent;
        w.sentExhausted = w.exhausted;
        try {
            PacketDistributor.sendToPlayersTrackingEntityAndSelf(sp, new MobStamina.Payload(sp.getId(), percent, w.exhausted));
        } catch (RuntimeException ignored) {
            // a fake player, a connection going
        }
    }

    // ------------------------------------------------------------------------------------------------ the players

    @SubscribeEvent
    public static void playerTick(PlayerTickEvent.Post e) {
        Player p = e.getEntity();
        if (p.level().isClientSide || !p.isAlive() || p.isCreative() || p.isSpectator()) {
            return;
        }
        Wind w = wind(p);
        long now = p.level().getGameTime();
        float[] s = of(p);
        // running wears it down (about a twelfth of it a second)
        if (p.isSprinting() && p.getDeltaMovement().horizontalDistanceSqr() > 0.01) {
            put(p, Math.max(0F, s[0] - s[1] * 0.004F));
            w.spentAt = now;
        } else if (EfStamina.of(p) == null && w.own < w.ownMax && now - w.spentAt > 20) {
            // OROR's own store comes back as Epic Fight's would: full in about four seconds
            w.own = Math.min(w.ownMax, w.own + w.ownMax / (w.exhausted ? 110F : 80F));
        }
        if (w.exhausted) {
            if (p.isSprinting()) {
                p.setSprinting(false);
            }
            if ((now - w.since) % 20 == 0) {
                p.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 30, 0, false, false, true));
                if (p.level() instanceof ServerLevel sl) {
                    sl.sendParticles(ParticleTypes.SPLASH, p.getX(), p.getEyeY() + 0.1, p.getZ(), 5, 0.2, 0.1, 0.2, 0.05);
                    if ((now - w.since) % 40 == 0) {
                        sl.playSound(null, p.blockPosition(), SoundEvents.HORSE_BREATHE, SoundSource.PLAYERS, 0.6F, 0.8F);
                    }
                }
            }
        }
        if ((now + p.getId()) % 2 == 0) {
            check(p);
        }
    }

    @SubscribeEvent
    public static void jumped(LivingEvent.LivingJumpEvent e) {
        if (e.getEntity() instanceof Player p && !p.level().isClientSide && !p.isCreative() && !p.isSpectator()) {
            float[] s = of(p);
            spend(p, s[1] * 0.04F);
        }
    }

    /** A swing at something: an eighth of a player's stamina, more for a heavy, slow weapon. */
    @SubscribeEvent
    public static void swung(AttackEntityEvent e) {
        Player p = e.getEntity();
        if (p.level().isClientSide || p.isCreative() || p.isSpectator()) {
            return;
        }
        float[] s = of(p);
        double speed = p.getAttributeValue(Attributes.ATTACK_SPEED);
        float cost = s[1] * (0.12F + (float) Math.max(0.0, 1.6 - speed) * 0.06F);
        spend(p, cost);
    }

    // ---------------------------------------------------------------------------------------- the mobs' running

    /** Every mob running (fleeing, charging, in panic) wears its stamina down; a mob walking does not. */
    @SubscribeEvent
    public static void mobTick(EntityTickEvent.Post e) {
        if (!(e.getEntity() instanceof Mob m) || m.level().isClientSide || (m.tickCount + m.getId()) % 5 != 0 || m.isNoAi() || !m.isAlive()
            || m.isPassenger()) {
            return;
        }
        double v = m.getDeltaMovement().horizontalDistanceSqr();
        // (CI: a cow driven at a run was off the ground as often as on it) its pace over the ground, whether or not a foot is on it
        if (v > 0.2 * 0.2 && !m.isInWater() && m.getNavigation() instanceof net.minecraft.world.entity.ai.navigation.GroundPathNavigation) {
            // tired by running, never broken by it (a down comes of a fight: MobDown)
            if (MobStamina.fraction(m) > 0.12F) {
                MobStamina.drain(m, MobStamina.max(m) * 0.006F);
            }
        }
    }

    // ----------------------------------------------------------------------------------- blows struck and taken

    @SubscribeEvent(priority = EventPriority.LOW)
    public static void blows(LivingIncomingDamageEvent e) {
        LivingEntity victim = e.getEntity();
        if (victim.level().isClientSide) {
            return;
        }
        // struck exhausted: half its weight, and the striker's rest begins again
        if (e.getSource().getEntity() instanceof LivingEntity attacker && e.getSource().getDirectEntity() == attacker && exhausted(attacker)) {
            e.setAmount(e.getAmount() * (attacker instanceof Player ? STRUCK : STRUCK_MOB));
            exhaustedBlows++;
            if (attacker instanceof Player p) {
                put(p, 0F);
                wind(p).spentAt = p.level().getGameTime();
                p.getPersistentData().putInt("OrorExhaustedBlows", p.getPersistentData().getInt("OrorExhaustedBlows") + 1);
            }
        }
        // taken exhausted: nothing to meet it with
        if (exhausted(victim) && !MobDown.isDown(victim) && !e.getSource().is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            e.setAmount(e.getAmount() * TAKEN);
            exhaustedHits++;
        }
    }

    /** For the CI check: a player's state forgotten. */
    public static void forget(Player p) {
        WINDS.remove(p.getUUID());
    }
}
