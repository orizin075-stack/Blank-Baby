package jp.oror.reborn.compat;

import java.io.BufferedReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Properties;
import net.neoforged.fml.loading.FMLPaths;

/**
 * config/oror-nightfall-patch.properties. 0.17.25: compactHud defaults to false, so Ares HUD (stamina, guard and parry,
 * mana) shows as in NightfallCraft unless the file asks for the plain health row.
 */
public final class NightfallPatchSettings {
    private static final Properties VALUES = read();
    public static final boolean COMPACT_HUD = Boolean.parseBoolean(VALUES.getProperty("compactHud", "false"));
    public static final boolean BASIC_PARRY = Boolean.parseBoolean(VALUES.getProperty("basicParry", "true"));
    public static final int IDLE_INTERVAL = interval("idleAiInterval", 5);
    public static final int DISTANT_INTERVAL = interval("distantAiInterval", 20);

    private static Properties read() {
        Properties values = new Properties();
        Path file = FMLPaths.CONFIGDIR.get().resolve("oror-nightfall-patch.properties");
        if (Files.isRegularFile(file)) {
            try (BufferedReader reader = Files.newBufferedReader(file)) {
                values.load(reader);
            } catch (Exception error) {
                System.err.println("[OROR] Using default patch settings: " + error.getClass().getSimpleName());
            }
        }
        return values;
    }

    private static int interval(String key, int fallback) {
        try {
            int value = Integer.parseInt(VALUES.getProperty(key, fallback + ""));
            return value != 1 && value != 5 && value != 10 && value != 20 ? fallback : value;
        } catch (NumberFormatException error) {
            return fallback;
        }
    }

    private NightfallPatchSettings() {
    }
}
