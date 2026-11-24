package jp.oror.reborn.combat.client;

import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.config.ConfigTracker;
import net.neoforged.fml.config.ModConfig;
import net.neoforged.fml.event.lifecycle.FMLClientSetupEvent;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.common.ModConfigSpec;
import net.neoforged.neoforge.common.NeoForge;

/**
 * (r75, the user: "HPバー二つあるのおかしくない") OROR draws a mob's health and stamina together over it (StaminaBars), so
 * the pack's other health bar over a hurt mob made two. Two mods can draw it: Epic Fight (its option
 * health_bar_show_option, an enum HealthBarVisibility) and Weapons of Miracles (its own HealthBarShowOptions); both say
 * HURT unless told. Setting Epic Fight's config value alone was not enough (the look run: the option set to NONE in the
 * file, the green bar still there): they read the option into their own fields. So every health-bar option of theirs, in
 * their config specs and in their config classes' fields, is set to NONE when the game starts and again once a world is
 * entered, whatever the files say.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public final class OneHealthBar {
    private static final String[] MODS = {"epicfight", "wom"};
    private static final String[] CLASSES = {"yesman.epicfight.config.ClientConfig", "reascer.wom.config.WOMClientConfig"};
    private static boolean inWorld;

    private OneHealthBar() {
    }

    @SubscribeEvent
    public static void setup(FMLClientSetupEvent e) {
        e.enqueueWork(OneHealthBar::off);
        NeoForge.EVENT_BUS.addListener((ClientTickEvent.Post t) -> {
            net.minecraft.client.Minecraft mc = net.minecraft.client.Minecraft.getInstance();
            if (mc.level != null && !inWorld) {
                inWorld = true;
                off();
            } else if (mc.level == null) {
                inWorld = false;
            }
        });
    }

    private static boolean healthBarEnum(Object v) {
        return v instanceof Enum<?> en && en.getDeclaringClass().getSimpleName().toLowerCase(java.util.Locale.ROOT).contains("healthbar");
    }

    @SuppressWarnings({"unchecked", "rawtypes"})
    private static Object none(Enum<?> en) {
        try {
            return Enum.valueOf((Class) en.getDeclaringClass(), "NONE");
        } catch (IllegalArgumentException ex) {
            return null;
        }
    }

    static void off() {
        int changed = 0;
        // their config specs' values
        try {
            for (ModConfig c : configs()) {
                if (c.getType() == ModConfig.Type.CLIENT && java.util.Arrays.asList(MODS).contains(c.getModId()) && c.getSpec() instanceof ModConfigSpec spec) {
                    changed += walk(spec.getValues());
                }
            }
        } catch (RuntimeException | LinkageError ex) {
            System.out.println("[OROR] health bar config specs not reached: " + ex);
        }
        // their config classes' own fields (what they read when they draw)
        for (String cn : CLASSES) {
            try {
                Class<?> c = Class.forName(cn);
                changed += fields(c, null, 0);
            } catch (ClassNotFoundException | LinkageError ex) {
                // that mod is not here
            } catch (RuntimeException ex) {
                System.out.println("[OROR] " + cn + " not reached: " + ex);
            }
        }
        if (changed > 0) {
            System.out.println("[OROR] other health bars over mobs turned off (" + changed + " options set to NONE): OROR shows health and stamina together");
        }
    }

    @SuppressWarnings({"unchecked", "rawtypes"})
    private static int walk(com.electronwill.nightconfig.core.UnmodifiableConfig cfg) {
        int n = 0;
        for (Object v : cfg.valueMap().values()) {
            if (v instanceof com.electronwill.nightconfig.core.UnmodifiableConfig sub) {
                n += walk(sub);
            } else if (v instanceof ModConfigSpec.ConfigValue cv) {
                try {
                    Object now = cv.get();
                    if (healthBarEnum(now) && !((Enum<?>) now).name().equals("NONE")) {
                        Object none = none((Enum<?>) now);
                        if (none != null) {
                            cv.set(none);
                            cv.save();
                            n++;
                        }
                    }
                } catch (RuntimeException ex) {
                    // a value not loaded yet
                }
            }
        }
        return n;
    }

    private static int fields(Class<?> c, Object on, int depth) {
        int n = 0;
        for (Field f : c.getDeclaredFields()) {
            boolean stat = Modifier.isStatic(f.getModifiers());
            if (on == null != stat || f.getType().isPrimitive()) {
                continue;
            }
            try {
                f.setAccessible(true);
                Object v = f.get(on);
                if (healthBarEnum(v) && !((Enum<?>) v).name().equals("NONE") && !Modifier.isFinal(f.getModifiers())) {
                    Object none = none((Enum<?>) v);
                    if (none != null) {
                        f.set(on, none);
                        n++;
                    }
                } else if (depth == 0 && v != null && v.getClass().getName().startsWith(c.getName().substring(0, c.getName().lastIndexOf('.')))
                    && !(v instanceof Enum<?>)) {
                    // an instance of their config (ClientConfig.INSTANCE and the like)
                    n += fields(v.getClass(), v, 1);
                }
            } catch (ReflectiveOperationException | RuntimeException ex) {
                // another field
            }
        }
        return n;
    }

    /** Every mod's configs the tracker holds (read from its fields: its accessors differ between FML versions). */
    private static Set<ModConfig> configs() {
        Set<ModConfig> out = new HashSet<>();
        for (Field f : ConfigTracker.class.getDeclaredFields()) {
            if (Modifier.isStatic(f.getModifiers()) || !Map.class.isAssignableFrom(f.getType())) {
                continue;
            }
            try {
                f.setAccessible(true);
                for (Object v : ((Map<?, ?>) f.get(ConfigTracker.INSTANCE)).values()) {
                    if (v instanceof ModConfig mc) {
                        out.add(mc);
                    } else if (v instanceof java.util.Collection<?> col) {
                        for (Object o : col) {
                            if (o instanceof ModConfig mc) {
                                out.add(mc);
                            }
                        }
                    }
                }
            } catch (ReflectiveOperationException | RuntimeException ex) {
                // another field
            }
        }
        return out;
    }
}
