package jp.oror.reborn.vehicle;

import java.lang.reflect.Method;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.Entity;
import net.neoforged.fml.ModList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Superb Warfare's vehicles, reached by name (as VillageVehicles does): the input flags a driver's keys set, the mouse
 * speeds a pilot's mouse sets, power, energy, the AI gunner's target. A method Superb Warfare does not have is logged
 * once and skipped.
 */
public final class Sbw {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Vehicles");
    private static final Map<String, Method> METHODS = new ConcurrentHashMap<>();
    private static final Set<String> MISSING = new HashSet<>();
    private static Class<?> vehicleClass;
    private static boolean looked;

    private Sbw() {
    }

    public static boolean present() {
        return ModList.get().isLoaded("superbwarfare");
    }

    /** Superb Warfare's VehicleEntity class, or null. */
    public static Class<?> vehicleClass() {
        if (!looked) {
            looked = true;
            try {
                vehicleClass = Class.forName("com.atsuishio.superbwarfare.entity.vehicle.base.VehicleEntity");
            } catch (ClassNotFoundException | LinkageError e) {
                vehicleClass = null;
            }
        }
        return vehicleClass;
    }

    public static boolean vehicle(Entity e) {
        Class<?> c = vehicleClass();
        return c != null && c.isInstance(e);
    }

    public static ResourceLocation id(String path) {
        return ResourceLocation.fromNamespaceAndPath("superbwarfare", path);
    }

    public static boolean has(String path) {
        return BuiltInRegistries.ENTITY_TYPE.containsKey(id(path));
    }

    /** TRACK, WHEEL, AIRCRAFT, HELICOPTER, ... or "" */
    public static String engine(Entity v) {
        Object computed = call(v, "computed");
        Object type = computed == null ? null : call(computed, "getEngineType");
        return type == null ? "" : type.toString();
    }

    public static void keys(Entity v, boolean forward, boolean back, boolean left, boolean right, boolean sprint, boolean down) {
        call(v, "setForwardInputDown", forward);
        call(v, "setBackInputDown", back);
        call(v, "setLeftInputDown", left);
        call(v, "setRightInputDown", right);
        call(v, "setSprintInputDown", sprint);
        call(v, "setDownInputDown", down);
        call(v, "setUpInputDown", false);
    }

    /** A helicopter's keys: the collective (up, down) besides forward, back, left and right. */
    public static void heliKeys(Entity v, boolean forward, boolean back, boolean left, boolean right, boolean up, boolean down) {
        call(v, "setForwardInputDown", forward);
        call(v, "setBackInputDown", back);
        call(v, "setLeftInputDown", left);
        call(v, "setRightInputDown", right);
        call(v, "setSprintInputDown", false);
        call(v, "setUpInputDown", up);
        call(v, "setDownInputDown", down);
    }

    public static void mouse(Entity v, double x, double y) {
        call(v, "mouseInput", x, y);
    }

    public static float power(Entity v) {
        return call(v, "getPower") instanceof Number n ? n.floatValue() : 0F;
    }

    public static void charge(Entity v) {
        if (call(v, "getMaxEnergy") instanceof Number max && max.intValue() > 0) {
            call(v, "setEnergy", max.intValue());
        }
    }

    public static boolean wreck(Entity v) {
        return Boolean.TRUE.equals(call(v, "isWreck"));
    }

    public static float health(Entity v) {
        Object h = call(v, "getHealth"), m = call(v, "getMaxHealth");
        return h instanceof Number a && m instanceof Number b && b.floatValue() > 0 ? a.floatValue() / b.floatValue() : 1F;
    }

    /** The target every AI turret and weapon station of the vehicle aims at ("undefined" for none). */
    public static void aim(Entity v, Entity target) {
        String id = target == null ? "undefined" : target.getStringUUID();
        call(v, "setAiTurretTargetUUID", id);
        call(v, "setAiPassengerWeaponTargetUUID", id);
    }

    public static Object call(Object o, String name, Object... args) {
        String key = o.getClass().getName() + "#" + name + "/" + args.length;
        Method m = METHODS.get(key);
        if (m == null) {
            for (Method c : o.getClass().getMethods()) {
                if (c.getName().equals(name) && c.getParameterCount() == args.length) {
                    m = c;
                    break;
                }
            }
            if (m == null) {
                synchronized (MISSING) {
                    if (MISSING.add(key)) {
                        LOG.warn("Superb Warfare has no {}", key);
                    }
                }
                return null;
            }
            METHODS.put(key, m);
        }
        try {
            Class<?>[] types = m.getParameterTypes();
            Object[] a = new Object[args.length];
            for (int i = 0; i < args.length; i++) {
                a[i] = convert(args[i], types[i]);
            }
            return m.invoke(o, a);
        } catch (ReflectiveOperationException | RuntimeException e) {
            synchronized (MISSING) {
                if (MISSING.add(key + "!")) {
                    LOG.warn("Superb Warfare {} failed: {}", key, e.toString());
                }
            }
            return null;
        }
    }

    private static Object convert(Object v, Class<?> type) {
        if (v instanceof Number n) {
            if (type == float.class || type == Float.class) {
                return n.floatValue();
            }
            if (type == double.class || type == Double.class) {
                return n.doubleValue();
            }
            if (type == int.class || type == Integer.class) {
                return n.intValue();
            }
        }
        return v;
    }
}
