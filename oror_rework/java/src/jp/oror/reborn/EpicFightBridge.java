package jp.oror.reborn;

import java.lang.reflect.Method;
import net.minecraft.world.entity.Entity;
import net.neoforged.fml.ModList;

/**
 * Epic Fight, reached by reflection (it is not needed to build or run this mod): its entity patches and the player's
 * battle/vanilla mode. If its API differs from what this expects, every call quietly answers "no patch".
 */
final class EpicFightBridge {
    private static boolean broken;
    private static Method patchOf;
    private static Class<?> mobPatch;
    private static Class<?> playerPatch;

    private EpicFightBridge() {
    }

    /** The entity's Epic Fight patch of the given kind ("mob" or "player"), or null. */
    static Object patch(Entity e, boolean player) {
        if (broken || !ModList.get().isLoaded("epicfight")) {
            return null;
        }
        try {
            if (patchOf == null) {
                Class<?> caps = Class.forName("yesman.epicfight.world.capabilities.EpicFightCapabilities");
                mobPatch = Class.forName("yesman.epicfight.world.capabilities.entitypatch.MobPatch");
                playerPatch = Class.forName("yesman.epicfight.world.capabilities.entitypatch.player.PlayerPatch");
                patchOf = caps.getMethod("getEntityPatch", Entity.class, Class.class);
            }
            return patchOf.invoke(null, e, player ? playerPatch : mobPatch);
        } catch (LinkageError | ReflectiveOperationException | RuntimeException x) {
            broken = true;
            System.out.println("[OROR_EPICFIGHT] entity patch lookup disabled: " + x.getClass().getSimpleName());
            return null;
        }
    }

    /** True when Epic Fight animates this mob with combat AI of its own. */
    static boolean animates(Entity e) {
        return patch(e, false) != null;
    }

    static void broken(Throwable x) {
        broken = true;
        System.out.println("[OROR_EPICFIGHT] disabled: " + x.getClass().getSimpleName());
    }
}
