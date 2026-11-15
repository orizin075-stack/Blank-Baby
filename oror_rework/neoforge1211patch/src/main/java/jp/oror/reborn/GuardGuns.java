package jp.oror.reborn;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.EntityTickEvent;

/**
 * (059g) The village's guards (Guard Villagers) fire the guns its gunsmith gives them. VillageArms hands its first guns to
 * the guards, but a guard is no villager: his own mod's mind knows swords, bows and crossbows and nothing of Superb
 * Warfare's guns, so he held his and never fired it (CI 43 to 47: ten blocks from a target, not one round; a weaponsmith
 * of the village with the same pistol struck five times). A guard with a gun in hand and a living target he can see more
 * than three blocks off now fires it as the village's own armed do (MobEquipmentUse, the same reloading and pace);
 * closer, he fights as his own mod has him.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class GuardGuns {
    private GuardGuns() {
    }

    @SubscribeEvent
    public static void tick(EntityTickEvent.Post e) {
        if (!(e.getEntity() instanceof Mob m) || !(m.level() instanceof ServerLevel level) || (m.tickCount + m.getId()) % 5 != 0) {
            return;
        }
        if (!"guardvillagers".equals(BuiltInRegistries.ENTITY_TYPE.getKey(m.getType()).getNamespace())) {
            return;
        }
        LivingEntity t = m.getTarget();
        if (t == null || !t.isAlive() || !"gun".equals(MobEquipmentUse.kind(m.getMainHandItem()))) {
            return;
        }
        double d = m.distanceToSqr(t);
        if (d < 3 * 3 || d > 48 * 48 || !m.hasLineOfSight(t)) {
            return;
        }
        m.getLookControl().setLookAt(t, 30F, 30F);
        MobEquipmentUse.use(m, t, level, "gun");
    }
}
