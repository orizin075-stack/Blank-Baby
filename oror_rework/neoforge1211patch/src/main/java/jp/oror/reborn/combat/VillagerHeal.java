package jp.oror.reborn.combat;

import jp.oror.reborn.MobMind;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.EntityTickEvent;

/**
 * (r66) An armed villager low on health in a fight heals, as every OROR fighter does (AdaptiveCombat: a fifth of its health
 * or twelve times its strength, whichever is less, then not again for eight seconds, with a hop back from its foe). Its
 * heal sits in AdaptiveCombat after the turn the village's fighters take elsewhere (VillageAI) and the one for a mob with
 * a goal of its own for its weapon, so a fighting villager never reached it: it backed off but never healed (GameTest
 * low_health_mob_retreats_during_healing, failing since 052: health 12.0 of 45.3 before and after, healing 0). Same rule,
 * same timer (NextHeal), so a villager the old way reaches is never healed twice.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class VillagerHeal {
    private VillagerHeal() {
    }

    @SubscribeEvent
    public static void tick(EntityTickEvent.Post e) {
        if (!(e.getEntity() instanceof Villager v) || !(v.level() instanceof ServerLevel sl) || (v.tickCount + v.getId()) % 5 != 0
            || !v.isAlive() || v.getMainHandItem().isEmpty() || !jp.oror.reborn.RebornConfig.SMART_MOBS.get()) {
            return;
        }
        // its foe: the one it fights, or the one that just struck it, or the hostile its senses hold (an armed villager
        // that backs off from a husk has given up its target to the panic its brain runs: the GameTest's villager)
        LivingEntity t = v.getTarget();
        if (t == null || !t.isAlive()) {
            t = v.getLastHurtByMob() != null && v.tickCount - v.getLastHurtByMobTimestamp() < 200 ? v.getLastHurtByMob() : null;
        }
        if (t == null || !t.isAlive()) {
            t = v.getBrain().getMemory(net.minecraft.world.entity.ai.memory.MemoryModuleType.NEAREST_HOSTILE).orElse(null);
        }
        if (t == null || !t.isAlive() || t.level() != sl || v.distanceToSqr(t) > 32 * 32) {
            return;
        }
        CompoundTag n = MobMind.data(v);
        long now = sl.getGameTime();
        double share = MobMind.stance(v).equals("defensive") ? 0.6 : 0.35;
        if (n.getLong("NextHeal") > now || v.getHealth() >= v.getMaxHealth() * share) {
            return;
        }
        v.heal((float) Math.min(v.getMaxHealth() * 0.2, 12.0 * MobMind.strength(v)));
        MobMind.practice(v, "healing", 2);
        n.putLong("NextHeal", now + 160L);
        if (v.onGround()) {
            Vec3 away = v.position().subtract(t.position());
            Vec3 hop = new Vec3(away.x, 0, away.z);
            hop = hop.lengthSqr() < 1.0E-4 ? Vec3.ZERO : hop.normalize().scale(0.45);
            v.setDeltaMovement(new Vec3(hop.x, 0.32, hop.z));
        }
        n.putLong("RetreatUntil", now + 32L);
    }
}
