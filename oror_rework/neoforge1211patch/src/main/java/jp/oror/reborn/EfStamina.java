package jp.oror.reborn;

import java.lang.reflect.Method;
import net.minecraft.world.entity.player.Player;

/**
 * (r73) A player's stamina as Epic Fight keeps it (its player patch: getStamina, getMaxStamina, setStamina; the bar the
 * pack shows, Ares HUD's and Epic Fight's own, is this one). Read by reflection, Epic Fight being the pack's and not
 * OROR's; when it is not there, or a player has no patch (a fake player), {@link #known} is false and OROR keeps its own.
 */
public final class EfStamina {
    private static boolean looked, broken;
    private static Method get, max, set;

    private EfStamina() {
    }

    private static void look(Object patch) {
        if (looked) {
            return;
        }
        looked = true;
        try {
            Class<?> c = patch.getClass();
            get = find(c, "getStamina");
            max = find(c, "getMaxStamina");
            set = find(c, "setStamina", float.class);
            broken = get == null || max == null || set == null;
        } catch (RuntimeException | LinkageError ex) {
            broken = true;
        }
        System.out.println("[OROR_EPICFIGHT] player stamina " + (broken ? "not found: OROR keeps its own" : "found: " + get + " / " + set));
    }

    private static Method find(Class<?> c, String name, Class<?>... args) {
        for (Class<?> k = c; k != null; k = k.getSuperclass()) {
            try {
                Method m = k.getDeclaredMethod(name, args);
                m.setAccessible(true);
                return m;
            } catch (NoSuchMethodException ex) {
                // up the hierarchy
            }
        }
        return null;
    }

    /** {stamina, max} from Epic Fight, or null when it does not keep this player's. */
    public static float[] of(Player p) {
        if (broken) {
            return null;
        }
        Object patch = EpicFightBridge.patch(p, true);
        if (patch == null) {
            return null;
        }
        look(patch);
        if (broken) {
            return null;
        }
        try {
            return new float[]{((Number) get.invoke(patch)).floatValue(), ((Number) max.invoke(patch)).floatValue()};
        } catch (ReflectiveOperationException | RuntimeException ex) {
            return null;
        }
    }

    public static boolean put(Player p, float value) {
        if (broken) {
            return false;
        }
        Object patch = EpicFightBridge.patch(p, true);
        if (patch == null) {
            return false;
        }
        look(patch);
        try {
            set.invoke(patch, value);
            return true;
        } catch (ReflectiveOperationException | RuntimeException ex) {
            return false;
        }
    }

    /** Whether Epic Fight's player stamina was found (once a player's patch has been looked at). */
    public static String state() {
        return !looked ? "not looked" : broken ? "absent" : "found";
    }
}
