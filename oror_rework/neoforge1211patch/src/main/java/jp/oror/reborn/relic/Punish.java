package jp.oror.reborn.relic;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import net.minecraft.core.Holder;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.LevelTickEvent;

/**
 * (058) 神罰: the relics' Lv125 punishments (amplifier 124: slowness, mining fatigue, weakness, wither, poison), kept by
 * the server as the design asks: each lasts exactly its own time (taken off when it is due, whatever else would have
 * kept it), and the same punishment does not land on the same foe again until a grace after it ended.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class Punish {
    public static final int LEVEL = 124;
    /** Ticks after a punishment ends before it may land again on that foe. */
    public static final int GRACE = 40;
    private static final Map<Integer, Map<String, Long>> DUE = new HashMap<>();
    public static int applied, refused, lifted;

    private Punish() {
    }

    public static Holder<MobEffect> effect(String n) {
        return switch (n) {
            case "slow", "slowness" -> MobEffects.MOVEMENT_SLOWDOWN;
            case "fatigue", "mining_fatigue" -> MobEffects.DIG_SLOWDOWN;
            case "wither" -> MobEffects.WITHER;
            case "poison" -> MobEffects.POISON;
            default -> MobEffects.WEAKNESS;
        };
    }

    /** Lands the punishment on the foe for its ticks, unless it is still under it or within the grace after it. */
    public static boolean apply(LivingEntity e, String name, int ticks) {
        if (!(e.level() instanceof ServerLevel sl) || ticks <= 0 || !e.isAlive()) {
            return false;
        }
        long now = sl.getGameTime();
        CompoundTag d = e.getPersistentData();
        String key = "ororPunish_" + name;
        if (now < d.getLong(key + "Next")) {
            refused++;
            return false;
        }
        Holder<MobEffect> h = effect(name);
        e.addEffect(new MobEffectInstance(h, ticks, LEVEL, false, true, true));
        d.putLong(key + "Until", now + ticks);
        d.putLong(key + "Next", now + ticks + GRACE);
        DUE.computeIfAbsent(e.getId(), k -> new HashMap<>()).put(name, now + ticks);
        applied++;
        return true;
    }

    /** Whether the foe is under this punishment now (for the CI and the tooltips' truth). */
    public static boolean under(LivingEntity e, String name) {
        MobEffectInstance m = e.getEffect(effect(name));
        return m != null && m.getAmplifier() == LEVEL;
    }

    @SubscribeEvent
    public static void tick(LevelTickEvent.Post e) {
        if (!(e.getLevel() instanceof ServerLevel sl) || DUE.isEmpty() || (sl.getGameTime() & 1L) != 0L) {
            return;
        }
        long now = sl.getGameTime();
        Iterator<Map.Entry<Integer, Map<String, Long>>> it = DUE.entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry<Integer, Map<String, Long>> en = it.next();
            Entity x = sl.getEntity(en.getKey());
            if (x == null) {
                // in another level, or gone: kept a while in case it is only elsewhere
                if (en.getValue().values().stream().allMatch(t -> t + 600 < now)) {
                    it.remove();
                }
                continue;
            }
            if (!(x instanceof LivingEntity le) || !le.isAlive()) {
                it.remove();
                continue;
            }
            en.getValue().entrySet().removeIf(p -> {
                if (now < p.getValue()) {
                    return false;
                }
                MobEffectInstance m = le.getEffect(effect(p.getKey()));
                if (m != null && m.getAmplifier() == LEVEL) {
                    le.removeEffect(effect(p.getKey()));
                    lifted++;
                }
                return true;
            });
            if (en.getValue().isEmpty()) {
                it.remove();
            }
        }
    }
}
