package jp.oror.reborn.combat.client;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Map;
import jp.oror.reborn.show.TechniqueShow;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.neoforged.neoforge.common.ItemAbilities;

/**
 * (059e) The guard raised, on the mobs Epic Fight draws (EfGuardStanceMixin). Most of the mobs that fight are drawn by
 * Epic Fight in the pack, and its zombies', skeletons' and illagers' patches have no guard stance of their own: while
 * OROR's guard is up (or a block is taken) the mob's composite motion is set to Epic Fight's BLOCK (BLOCK_SHIELD with a
 * shield) on this client, so it stands in the guard of what it holds (Epic Fight's sword, long sword, spear or shield
 * guard), as a player in guard does; when the guard goes down its own motion comes back the next tick. A mob whose
 * weapon has no guard in Epic Fight (bare hands, an axe) is left as it is: its parry and block still play Epic Fight's
 * guard hits (MobGuard.Ef).
 */
public final class EfGuardStance {
    private static Field patchField, compositeMap, compositeMotion;
    private static Method original;
    private static Object block, blockShield;
    private static boolean looked, broken;

    private EfGuardStance() {
    }

    private static void look(Object animator) throws ReflectiveOperationException {
        looked = true;
        Class<?> animatorClass = Class.forName("yesman.epicfight.api.animation.Animator");
        patchField = animatorClass.getDeclaredField("entitypatch");
        patchField.setAccessible(true);
        compositeMap = Class.forName("yesman.epicfight.api.client.animation.ClientAnimator").getDeclaredField("compositeLivingAnimations");
        compositeMap.setAccessible(true);
        Class<?> livingPatch = Class.forName("yesman.epicfight.world.capabilities.entitypatch.LivingEntityPatch");
        compositeMotion = livingPatch.getField("currentCompositeMotion");
        original = Class.forName("yesman.epicfight.world.capabilities.entitypatch.EntityPatch").getMethod("getOriginal");
        Class<?> motions = Class.forName("yesman.epicfight.api.animation.LivingMotions");
        for (Object c : motions.getEnumConstants()) {
            String name = ((Enum<?>) c).name();
            if (name.equals("BLOCK")) {
                block = c;
            } else if (name.equals("BLOCK_SHIELD")) {
                blockShield = c;
            }
        }
    }

    /** Called on a client animator's tick, after its base layer set the patch's motions for this tick. */
    public static void apply(Object animator) {
        if (broken) {
            return;
        }
        try {
            if (!looked) {
                look(animator);
            }
            if (block == null) {
                return;
            }
            Object patch = patchField.get(animator);
            Object entity = patch == null ? null : original.invoke(patch);
            if (!(entity instanceof Mob mob)) {
                return;
            }
            LivingEntity living = mob;
            TechniqueShow.Active show = TechniqueShow.REACT.get(mob.getId());
            if (show == null || !(show.mechanic().equals("GUARD") || show.mechanic().equals("BLOCK"))) {
                return;
            }
            long time = living.level().getGameTime() - show.start();
            if (time < 0 || time > show.length()) {
                return;
            }
            Map<?, ?> composite = (Map<?, ?>) compositeMap.get(animator);
            boolean shield = living.getOffhandItem().canPerformAction(ItemAbilities.SHIELD_BLOCK);
            Object motion = shield && blockShield != null && composite.containsKey(blockShield) ? blockShield : composite.containsKey(block) ? block : null;
            if (motion != null) {
                compositeMotion.set(patch, motion);
            }
        } catch (ReflectiveOperationException | RuntimeException | LinkageError ex) {
            broken = true;
            System.out.println("[OROR] Epic Fight guard stance disabled: " + ex);
        }
    }
}
