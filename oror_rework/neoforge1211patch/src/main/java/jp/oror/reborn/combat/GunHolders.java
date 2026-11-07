package jp.oror.reborn.combat;

import java.util.List;
import jp.oror.reborn.MobEquipmentUse;
import jp.oror.reborn.SupremeEntity;
import jp.oror.reborn.mixin.MobGoalSelectorAccess;
import jp.oror.reborn.royal.RoyalMob;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.WrappedGoal;
import net.minecraft.world.entity.npc.AbstractVillager;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.EntityTickEvent;

/**
 * (053) Monsters that carry a gun use it (the user: the mobs carry guns too, and they behave oddly). JEG hands revolvers,
 * pistols and SMGs to zombies, skeletons, wither skeletons, husks, piglin brutes and the like as they spawn (053's CI
 * census), but Epic Fight gives such a mob its melee AI (it knows nothing of a gun: a fist), and OROR's adaptive combat
 * left any mob holding a gun to "its gun mod" before it got as far as fitting JEG's own gun goal, which it did for
 * villagers only: so they walked up and struck with the gun in hand, never firing (the CI's lanes). Now a monster holding
 * a JEG gun, with an enemy to fight, is given JEG's own tactical gun goal (MobEquipmentUse.nativeGoal: it keeps its
 * distance, takes cover and fires real rounds), and Epic Fight's and its add-ons' melee, chase and guard goals are taken
 * from it while it holds the gun: no more swinging or parrying with a gun. Epic Fight gives them back when it changes to
 * a weapon of its kind. TACZ guns have their own goals (Pillagers Gun, TACZ Bandits) and are left as they are.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class GunHolders {
    private GunHolders() {
    }

    @SubscribeEvent
    public static void tick(EntityTickEvent.Post e) {
        if (!(e.getEntity() instanceof PathfinderMob m) || m.level().isClientSide || m.tickCount % 10 != Math.floorMod(m.getId(), 10)) {
            return;
        }
        if (m instanceof AbstractVillager || m instanceof RoyalMob || m instanceof SupremeEntity || m.isNoAi()) {
            return;
        }
        LivingEntity t = m.getTarget();
        if (t == null || !t.isAlive() || !Guns.held(m.getMainHandItem())
            || !BuiltInRegistries.ITEM.getKey(m.getMainHandItem().getItem()).getNamespace().equals("jeg")) {
            return;
        }
        MobEquipmentUse.nativeGoal(m);
        meleeAway(m);
    }

    /** Epic Fight's and its add-ons' melee, chase and guard goals, taken from a mob that fights with a gun. */
    public static int meleeAway(Mob m) {
        List<Goal> melee = ((MobGoalSelectorAccess) m).oror$getGoals().getAvailableGoals().stream().map(WrappedGoal::getGoal)
            .filter(GunHolders::melee).toList();
        for (Goal g : melee) {
            ((MobGoalSelectorAccess) m).oror$getGoals().removeGoal(g);
        }
        return melee.size();
    }

    static boolean melee(Goal g) {
        String name = g.getClass().getName();
        boolean epic = name.startsWith("yesman.epicfight") || name.contains("indestructible") || name.contains("combat_evolution");
        String simple = g.getClass().getSimpleName();
        if (simple.isEmpty() && g.getClass().getEnclosingClass() != null) {
            simple = g.getClass().getEnclosingClass().getSimpleName();
        }
        return epic && (simple.contains("Attack") || simple.contains("Chasing") || simple.contains("Combat") || simple.contains("Guard"));
    }
}
