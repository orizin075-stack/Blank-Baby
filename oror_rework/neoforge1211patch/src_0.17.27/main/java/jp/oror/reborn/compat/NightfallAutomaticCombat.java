package jp.oror.reborn.compat;

import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.Locale;
import java.util.Set;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.item.ItemStack;
import yesman.epicfight.world.capabilities.EpicFightCapabilities;

/**
 * NightfallCraft's weapons: the 433 items its Epic Fight client config prefers for combat (oror_combat_preferred025.json,
 * added by the other 0.17.25), and any item Epic Fight gives a weapon category other than fists and digging tools.
 *
 * 0.17.26: this was also a server player tick that forced combat mode every tick while a weapon was held, so pressing R
 * did nothing until the weapon was put away. NightfallAutomaticCombatClient now switches when a weapon is taken and
 * when the player enters a world (a player saved in the vanilla mode), and Epic Fight sends the mode to the server.
 */
public final class NightfallAutomaticCombat {
    public static final Set<String> ORIGINAL_PREFERRED = readOriginal();
    private static final Set<String> NOT_WEAPONS = Set.of("NOT_WEAPON", "FIST", "PICKAXE", "SHOVEL", "HOE");

    private static Set<String> readOriginal() {
        Set<String> values = new LinkedHashSet<>();
        try (InputStream stream = NightfallAutomaticCombat.class.getResourceAsStream("/oror_combat_preferred025.json")) {
            if (stream != null) {
                for (JsonElement element : JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8)).getAsJsonArray()) {
                    values.add(element.getAsString());
                }
            }
        } catch (Exception error) {
            System.err.println("[OROR] NightfallCraft's weapon list not read: " + error);
        }
        return Collections.unmodifiableSet(values);
    }

    public static boolean weapon(ItemStack stack) {
        if (stack.isEmpty()) {
            return false;
        }
        if (ORIGINAL_PREFERRED.contains(BuiltInRegistries.ITEM.getKey(stack.getItem()).toString())) {
            return true;
        }
        var capability = EpicFightCapabilities.getItemStackCapability(stack);
        return !capability.isEmpty() && !NOT_WEAPONS.contains(capability.getWeaponCategory().toString().toUpperCase(Locale.ROOT));
    }

    private NightfallAutomaticCombat() {
    }
}
