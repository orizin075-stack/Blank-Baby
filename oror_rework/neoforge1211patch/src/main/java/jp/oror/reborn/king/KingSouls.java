package jp.oror.reborn.king;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;
import jp.oror.reborn.royal.RoyalMob;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Vex;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingChangeTargetEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.server.ServerStoppedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * (054) Baal Zebul's demon's work that lasts (the user: a field covered with a host of flies; pale blue flames and souls,
 * many ills that go on, and when they have run their full time the soul is taken):
 * <ul>
 * <li>魂喰らい, the soul-eating: pale blue fire on the foe; while it burns, withering, weakness, slowness, heavy
 * hands, hunger, sickness and darkness go on; a foe that strikes him three times breaks the chain; one that lets it burn
 * its full fifteen seconds has its soul taken (ten blows each its whole life, half its levels).</li>
 * <li>蝿の帳, the veil of flies: for twelve seconds the ground for twenty-eight blocks about him is black with flies:
 * blind, dark, hungry, poisoned, eaten a little every second, and flies of his (vexes) loose in it.</li>
 * <li>His creatures (the flies, the twisted angels, the black wings, the broken one's errors) are never his foes or his
 * targets, and they go when their time is up.</li>
 * </ul>
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class KingSouls {
    static final int LIMIT = 300;
    static final String SPAWN = "OrorKingSpawn";

    private static final class Mark {
        final RoyalMob king;
        int burnt, struck;

        Mark(RoyalMob king) {
            this.king = king;
        }
    }

    private static final Map<LivingEntity, Mark> MARKS = new WeakHashMap<>();

    private record Veil(RoyalMob king, ServerLevel level, long until) {
    }

    private static final List<Veil> VEILS = new ArrayList<>();

    private KingSouls() {
    }

    /** Sets the soul fire on a foe (a fresh mark, or more burnt on one it has). */
    static void feed(RoyalMob king, LivingEntity v, int ticks) {
        Mark m = MARKS.computeIfAbsent(v, x -> new Mark(king));
        m.burnt = Math.min(LIMIT - 1, m.burnt + ticks);
        if (v instanceof ServerPlayer p) {
            p.displayClientMessage(Component.literal("魂が青白い炎に灼かれている（王に3回攻撃を当てれば鎖が切れる）").withStyle(ChatFormatting.AQUA), true);
        }
    }

    static void mark(RoyalMob king, LivingEntity v) {
        MARKS.put(v, new Mark(king));
        feed(king, v, 0);
    }

    public static boolean marked(LivingEntity v) {
        return MARKS.containsKey(v);
    }

    static void veil(RoyalMob king, ServerLevel sl, int ticks) {
        VEILS.add(new Veil(king, sl, sl.getGameTime() + ticks));
        for (int i = 0; i < 8; i++) {
            Vex fly = EntityType.VEX.create(sl);
            if (fly == null) {
                continue;
            }
            double a = i * Math.PI / 4;
            fly.moveTo(king.getX() + Math.cos(a) * 3, king.getY() + 2.5, king.getZ() + Math.sin(a) * 3, 0F, 0F);
            fly.setOwner(king);
            fly.setLimitedLife(20 * 24);
            spawned(fly, "蝿の眷属", ChatFormatting.DARK_GRAY);
            sl.addFreshEntity(fly);
            if (king.getTarget() != null) {
                fly.setTarget(king.getTarget());
            }
        }
    }

    /** One of his creatures: named, never his foe or his target. */
    static void spawned(Mob m, String name, ChatFormatting style) {
        m.getPersistentData().putBoolean(SPAWN, true);
        m.setCustomName(Component.literal(name).withStyle(style));
        m.setPersistenceRequired();
    }

    public static boolean his(Entity e) {
        return e != null && e.getPersistentData().getBoolean(SPAWN);
    }

    @SubscribeEvent
    public static void notHisTarget(LivingChangeTargetEvent e) {
        LivingEntity who = e.getEntity(), t = e.getNewAboutToBeSetTarget();
        if (t == null) {
            return;
        }
        if ((KingCourt.isKing(who) || who instanceof RoyalMob) && his(t)) {
            e.setCanceled(true);
        } else if (his(who) && (KingCourt.isKing(t) || t instanceof RoyalMob || his(t))) {
            e.setCanceled(true);
        }
    }

    /** A blow on him by a marked foe loosens its chain; three break it. */
    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void strikes(LivingIncomingDamageEvent e) {
        if (!KingCourt.isKing(e.getEntity()) || !(e.getSource().getEntity() instanceof LivingEntity by)) {
            return;
        }
        Mark m = MARKS.get(by);
        if (m != null && ++m.struck >= 3) {
            MARKS.remove(by);
            if (by instanceof ServerPlayer p) {
                p.displayClientMessage(Component.literal("魂の鎖を断ち切った").withStyle(ChatFormatting.GREEN), true);
            }
            if (by.level() instanceof ServerLevel sl) {
                sl.sendParticles(ParticleTypes.END_ROD, by.getX(), by.getY() + 1, by.getZ(), 30, 0.4, 0.6, 0.4, 0.1);
            }
        }
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        if (MARKS.isEmpty() && VEILS.isEmpty()) {
            return;
        }
        for (Iterator<Map.Entry<LivingEntity, Mark>> it = MARKS.entrySet().iterator(); it.hasNext(); ) {
            Map.Entry<LivingEntity, Mark> en = it.next();
            LivingEntity v = en.getKey();
            Mark m = en.getValue();
            if (!v.isAlive() || !m.king.isAlive() || !(v.level() instanceof ServerLevel sl) || v.distanceTo(m.king) > 96) {
                it.remove();
                continue;
            }
            if (sl.getGameTime() % 10 != 0) {
                continue;
            }
            m.burnt += 10;
            sl.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, v.getX(), v.getY() + v.getBbHeight() * 0.5, v.getZ(), 12, 0.35, 0.6, 0.35, 0.02);
            sl.sendParticles(ParticleTypes.SOUL, v.getX(), v.getY() + v.getBbHeight(), v.getZ(), 3, 0.3, 0.3, 0.3, 0.02);
            for (var ef : List.of(MobEffects.WITHER, MobEffects.WEAKNESS, MobEffects.MOVEMENT_SLOWDOWN, MobEffects.DIG_SLOWDOWN, MobEffects.HUNGER)) {
                v.addEffect(new MobEffectInstance(ef, 40, 1));
            }
            v.addEffect(new MobEffectInstance(MobEffects.CONFUSION, 80, 0));
            v.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 40, 0));
            if (v instanceof ServerPlayer p && m.burnt % 40 == 0) {
                int left = Math.max(0, (LIMIT - m.burnt) / 20);
                p.displayClientMessage(Component.literal("魂が奪われるまで あと" + left + "秒（王に攻撃を当てて鎖を断て）").withStyle(ChatFormatting.AQUA), true);
            }
            if (m.burnt >= LIMIT) {
                it.remove();
                take(m.king, sl, v);
            }
        }
        for (Iterator<Veil> it = VEILS.iterator(); it.hasNext(); ) {
            Veil vl = it.next();
            ServerLevel sl = vl.level;
            long now = sl.getGameTime();
            if (now >= vl.until || !vl.king.isAlive()) {
                it.remove();
                continue;
            }
            Vec3 c = vl.king.position();
            if (now % 3 == 0) {
                for (int i = 0; i < 40; i++) {
                    double a = sl.random.nextDouble() * Math.PI * 2, r = Math.sqrt(sl.random.nextDouble()) * 28;
                    sl.sendParticles(i % 3 == 0 ? KingDeeds.BLACK : ParticleTypes.SQUID_INK, c.x + Math.cos(a) * r, c.y + 0.3 + sl.random.nextDouble() * 4,
                        c.z + Math.sin(a) * r, 1, 0.1, 0.1, 0.1, 0.01);
                }
            }
            if (now % 20 == 0) {
                for (LivingEntity v : KingForms.foes(vl.king, sl, 28)) {
                    sl.sendParticles(ParticleTypes.SQUID_INK, v.getX(), v.getY() + 1, v.getZ(), 20, 0.5, 0.8, 0.5, 0.02);
                    v.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 40, 0));
                    v.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 60, 0));
                    v.addEffect(new MobEffectInstance(MobEffects.HUNGER, 60, 2));
                    v.addEffect(new MobEffectInstance(MobEffects.POISON, 60, 0));
                    v.invulnerableTime = 0;
                    KingDeeds.hit(vl.king, "veil", v, 2F, true);
                }
                KingDeeds.sound(sl, c, SoundEvents.BEE_LOOP_AGGRESSIVE, 3F, 0.4F);
            }
        }
    }

    /** The soul taken: ten blows each its whole life, and half its levels. */
    private static void take(RoyalMob king, ServerLevel sl, LivingEntity v) {
        Vec3 c = v.position();
        for (int i = 0; i < 10; i++) {
            v.invulnerableTime = 0;
            KingDeeds.hit(king, "soul", v, v.getMaxHealth() + 10F, true);
        }
        if (v instanceof ServerPlayer p) {
            p.giveExperienceLevels(-p.experienceLevel / 2);
        }
        KingDeeds.line(sl, ParticleTypes.SOUL, c.add(0, 1, 0), king.getEyePosition(), 0.4);
        sl.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, c.x, c.y + 1, c.z, 80, 0.5, 1, 0.5, 0.1);
        KingDeeds.sound(sl, c, SoundEvents.SOUL_ESCAPE.value(), 4F, 0.5F);
        KingDeeds.sound(sl, c, SoundEvents.WITHER_DEATH, 1.5F, 1.4F);
        KingDeeds.KingCinemaSay.near(sl, king, "バアル＝ゼブル：その魂、我が饗宴に供されたり。", ChatFormatting.DARK_AQUA);
        KingDeeds.count(king, KingDeeds.COUNT, "soul_taken");
    }

    @SubscribeEvent
    public static void stopped(ServerStoppedEvent e) {
        MARKS.clear();
        VEILS.clear();
    }
}
