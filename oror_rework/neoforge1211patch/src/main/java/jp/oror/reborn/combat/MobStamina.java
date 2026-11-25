package jp.oror.reborn.combat;

import java.util.Map;
import java.util.WeakHashMap;
import java.util.concurrent.ConcurrentHashMap;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.show.TechniqueShow;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;
import net.neoforged.neoforge.network.PacketDistributor;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

/**
 * (059h) The user: "敵モブにもスタミナを". A player in this pack has Epic Fight's stamina; now every mob that fights has one
 * too, a single store that its dodges (MobDodge), its guard (MobGuard: the guard's upkeep, a parry's and a block's
 * price, the guard broken when it cannot pay) and its own blows draw on:
 * <ul>
 * <li>its depth by how good it is (MobProwess: its level, experience, strength, what it is), 40 for a fresh zombie to
 * 240 for a god, times its own gift (0.85 to 1.2): no two alike;</li>
 * <li>a dodge takes a quarter to an eighth of it (MobDodge), a parry a twentieth of the blow, a block three tenths of
 * it, a blow of its own 3% to 1.5% of its depth (nothing while winded);</li>
 * <li>it comes back after a second's rest, full in 13 seconds for the weakest down to 7 for the best;</li>
 * <li>under a tenth it is winded until it is back to a third: no dodge, no guard raised, slowed;
 * hunched and sweating, breathing hard (seen and heard), an opening for whoever fights it.</li>
 * </ul>
 * Its stamina is shown over a mob whose store is not full (StaminaBars, on the client): a thin bar over its head, yellow,
 * orange when low, flashing red when winded.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class MobStamina {
    private MobStamina() {
    }

    static final class Pool {
        float value = -1F, max;
        long spentAt = -100, windedAt = -100, sentAt = -100, shownAt = -100;
        boolean winded;
        int sentPercent = -1;
        boolean sentWinded;
    }

    private static final Map<LivingEntity, Pool> POOLS = new WeakHashMap<>();

    /**
     * How deep a mob's stamina is: (059h, the user: "スタミナも多めで　一定にしないで") by its prowess (MobProwess: its
     * level, experience, strength, what it is), 40 for a fresh zombie to 240 for a god, times its own gift (0.85 to 1.2).
     */
    public static float max(Mob m) {
        return MobProwess.lerp(MobProwess.of(m), 40F, 240F) * MobProwess.wind(m);
    }

    /** Ticks to come back from empty to full: 13 seconds for the weakest, 7 for the best. */
    static float refill(Mob m) {
        return MobProwess.lerp(MobProwess.of(m), 260F, 140F);
    }

    static Pool pool(Mob m) {
        Pool p = POOLS.get(m);
        if (p == null) {
            p = new Pool();
            POOLS.put(m, p);
        }
        if (p.value < 0) {
            p.max = max(m);
            p.value = p.max;
        }
        return p;
    }

    /** The mob's stamina now. */
    public static float value(Mob m) {
        Pool p = POOLS.get(m);
        return p == null || p.value < 0 ? max(m) : p.value;
    }

    /** Its stamina as a share of its depth (1: full). */
    public static float fraction(Mob m) {
        Pool p = POOLS.get(m);
        return p == null || p.value < 0 || p.max <= 0 ? 1F : p.value / p.max;
    }

    /** Whether it is winded (out of stamina, not yet back to a third). */
    public static boolean winded(Mob m) {
        Pool p = POOLS.get(m);
        return p != null && p.winded;
    }

    /** Whether it has the stamina for a cost (and is not winded). */
    public static boolean has(Mob m, float cost) {
        Pool p = pool(m);
        return !p.winded && p.value >= cost;
    }

    /** Takes a cost from its stamina: false (and nothing taken) when it has not got it, or is winded. */
    public static boolean spend(Mob m, float cost) {
        Pool p = pool(m);
        if (p.winded || p.value < cost) {
            return false;
        }
        take(m, p, cost, true);
        return true;
    }

    /** Takes what it can of a cost: it may wind the mob, and its stamina rests a second before it comes back. */
    public static void drain(Mob m, float cost) {
        take(m, pool(m), cost, true);
    }

    /**
     * (CI 68) A light cost, its own blow or its guard held up: taken without breaking its rest. Every cost stopping its
     * stamina coming back, a mob striking every second never got its wind back, winded for as long as it fought.
     */
    public static void tire(Mob m, float cost) {
        take(m, pool(m), cost, false);
    }

    /** Empties it (a guard broken under a blow it could not pay for): the mob is winded. */
    /** (r76) Its stamina full again and its wind back at once (up from a down: MobDown). */
    public static void refill(Mob m) {
        Pool p = pool(m);
        p.value = p.max;
        p.winded = false;
        p.spentAt = m.level().getGameTime() - 100;
        send(m, p, true);
    }

    public static void empty(Mob m) {
        Pool p = pool(m);
        take(m, p, p.value, true);
    }

    private static void take(Mob m, Pool p, float cost, boolean rest) {
        long now = m.level().getGameTime();
        p.value = Math.max(0F, p.value - Math.max(0F, cost));
        if (rest) {
            p.spentAt = now;
        }
        p.shownAt = now;
        if (!p.winded && p.value < p.max * 0.1F) {
            p.winded = true;
            // (r76) its stamina broken: it goes down (MobDown), an opening for an execution
            MobDown.down(m);
            p.windedAt = now;
            count(m, "OrorWinded");
            if (m.level() instanceof ServerLevel sl) {
                // the moment it runs out: a gasp, a puff of breath
                sl.playSound(null, m.blockPosition(), SoundEvents.WOLF_PANT, SoundSource.HOSTILE, 0.6F, 1.25F + m.getRandom().nextFloat() * 0.2F);
                sl.sendParticles(ParticleTypes.POOF, m.getX(), m.getEyeY() - 0.1, m.getZ(), 4, 0.15, 0.05, 0.15, 0.01);
            }
            TechniqueShow.send(m, "winded", 0, 1, 30, -1);
        }
        send(m, p, false);
    }

    // ------------------------------------------------------------------------------------------------- over time

    @SubscribeEvent
    public static void tick(EntityTickEvent.Post e) {
        if (!(e.getEntity() instanceof Mob m) || m.level().isClientSide) {
            return;
        }
        Pool p = POOLS.get(m);
        if (p == null || p.value < 0) {
            return;
        }
        if (!m.isAlive()) {
            POOLS.remove(m);
            return;
        }
        long now = m.level().getGameTime();
        if ((now + m.getId()) % 100 == 0) {
            // (059h) its depth follows its prowess (a level gained, experience, what it has learnt), its share kept
            float max = max(m);
            if (Math.abs(max - p.max) > 0.5F) {
                p.value = p.value * max / Math.max(1F, p.max);
                p.max = max;
            }
        }
        if (p.value < p.max && now - p.spentAt > 20) {
            // back after a second's rest: full in 7 to 13 seconds by its prowess (winded, a third slower)
            p.value = Math.min(p.max, p.value + p.max / (refill(m) * (p.winded ? 1.3F : 1F)));
        }
        if (p.winded) {
            if (p.value >= p.max * 0.35F && now - p.windedAt >= 40) {
                p.winded = false;
                send(m, p, true);
            } else if ((now - p.windedAt) % 20 == 0) {
                // hunched and sweating, breathing hard, slowed
                m.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 30, 0, false, false, false));
                if (m.level() instanceof ServerLevel sl) {
                    sl.sendParticles(ParticleTypes.SPLASH, m.getX(), m.getEyeY() + 0.1, m.getZ(), 5, m.getBbWidth() * 0.3, 0.1, m.getBbWidth() * 0.3, 0.05);
                    if ((now - p.windedAt) % 40 == 0) {
                        sl.playSound(null, m.blockPosition(), SoundEvents.WOLF_PANT, SoundSource.HOSTILE, 0.4F, 1.3F);
                    }
                }
                if ((now - p.windedAt) % 30 == 0 || (now - p.windedAt) == 20) {
                    TechniqueShow.send(m, "winded", 0, 1, 32, -1);
                }
            }
        }
        if (now - p.sentAt >= 5) {
            send(m, p, false);
        }
    }

    /** A mob's own blow (one dodged or parried too: it swung all the same): its price taken. */
    @SubscribeEvent(priority = EventPriority.LOW, receiveCanceled = true)
    public static void blow(LivingIncomingDamageEvent e) {
        // (r73, the user: "全モブに") every mob's own blow, not only a fighter's
        if (!(e.getSource().getEntity() instanceof Mob attacker) || attacker.level().isClientSide || e.getSource().getDirectEntity() != attacker
            || attacker.isNoAi()) {
            return;
        }
        Pool p = pool(attacker);
        if (p.winded) {
            // winded: nothing more taken from it (it would never get its wind back). (CI 68) Its blow was not weakened: so
            // weakened (by half), a village's fighters, winded by dodging their foes' blows, no longer beat the armoured
            // fighters of the mod's own trials. (r73, the user asked for it) It is now, but by less: to six tenths (Exhaustion)
            count(attacker, "OrorWindedBlows");
            return;
        }
        // (059h) 3% of its depth for the clumsiest, 1.5% for the best (CI 68: at 6% a zombie striking every second spent
        // as fast as it got its wind back)
        tire(attacker, p.max * MobProwess.lerp(MobProwess.of(attacker), 0.03F, 0.015F));
    }

    private static void count(LivingEntity m, String key) {
        m.getPersistentData().putInt(key, m.getPersistentData().getInt(key) + 1);
    }

    // ------------------------------------------------------------------------------------------------- the client

    /** What the client knows of a mob's stamina: its share in hundredths, whether winded, when it was told. */
    public record Seen(int percent, boolean winded, long at) {
    }

    /** The client's mobs' stamina, by entity id (written by the network thread's queued work). */
    public static final Map<Integer, Seen> SEEN = new ConcurrentHashMap<>();

    public record Payload(int entity, int percent, boolean winded) implements CustomPacketPayload {
        public static final Type<Payload> TYPE = new Type<>(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "mob_stamina"));
        public static final StreamCodec<RegistryFriendlyByteBuf, Payload> CODEC = StreamCodec.ofMember(Payload::write, Payload::read);

        void write(RegistryFriendlyByteBuf buf) {
            buf.writeVarInt(entity);
            buf.writeByte(percent);
            buf.writeBoolean(winded);
        }

        static Payload read(RegistryFriendlyByteBuf buf) {
            return new Payload(buf.readVarInt(), buf.readByte(), buf.readBoolean());
        }

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    /** Tells the players who see the mob its stamina, when it has changed enough to show (every quarter second at most). */
    private static void send(Mob m, Pool p, boolean force) {
        long now = m.level().getGameTime();
        int percent = Math.round(100F * p.value / Math.max(1F, p.max));
        if (!force && (now - p.sentAt < 5 || Math.abs(percent - p.sentPercent) < 3 && p.winded == p.sentWinded && !(percent == 100 && p.sentPercent != 100))) {
            return;
        }
        p.sentAt = now;
        p.sentPercent = percent;
        p.sentWinded = p.winded;
        PacketDistributor.sendToPlayersTrackingEntity(m, new Payload(m.getId(), percent, p.winded));
    }

    /** The payload's registration (MOD bus). */
    @EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD)
    public static final class Net {
        private Net() {
        }

        @SubscribeEvent
        public static void register(RegisterPayloadHandlersEvent e) {
            e.registrar("2").optional().playToClient(Payload.TYPE, Payload.CODEC, (pl, ctx) -> ctx.enqueueWork(() -> {
                Entity en = ctx.player().level().getEntity(pl.entity());
                if (en != null) {
                    SEEN.put(pl.entity(), new Seen(pl.percent(), pl.winded(), ctx.player().level().getGameTime()));
                }
            }));
        }
    }

    /** For the checks: stamina now, depth, winded, times winded. */
    public static String describe(Mob m) {
        return String.format(java.util.Locale.ROOT, "%.0f/%.0f%s winded %d", value(m), max(m), winded(m) ? " WINDED" : "",
            m.getPersistentData().getInt("OrorWinded"));
    }
}
