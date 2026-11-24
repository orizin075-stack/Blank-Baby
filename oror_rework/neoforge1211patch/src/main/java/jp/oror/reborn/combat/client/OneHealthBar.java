package jp.oror.reborn.combat.client;

import java.util.List;
import java.util.Map;
import java.util.Set;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.config.ConfigTracker;
import net.neoforged.fml.config.ModConfig;
import net.neoforged.fml.event.lifecycle.FMLClientSetupEvent;
import net.neoforged.neoforge.common.ModConfigSpec;

/**
 * (r75, the user: "HPバー二つあるのおかしくない") OROR draws a mob's health and stamina together over it (StaminaBars), so
 * Epic Fight's own health bar over a hurt mob made two. The pack's config leaves Epic Fight's off, but a profile that
 * kept its own config, or took only OROR's jar, still had it: so Epic Fight's option (ingame.health_bar_show_option) is
 * set to NONE when the game starts, whatever the file says.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public final class OneHealthBar {
    private OneHealthBar() {
    }

    @SubscribeEvent
    public static void setup(FMLClientSetupEvent e) {
        e.enqueueWork(OneHealthBar::off);
    }

    @SuppressWarnings({"unchecked", "rawtypes"})
    static void off() {
        try {
            Map<ModConfig.Type, Set<ModConfig>> sets = ConfigTracker.INSTANCE.configSets();
            for (ModConfig c : sets.getOrDefault(ModConfig.Type.CLIENT, Set.of())) {
                if (!"epicfight".equals(c.getModId()) || !(c.getSpec() instanceof ModConfigSpec spec)) {
                    continue;
                }
                Object v = spec.getValues().get(List.of("ingame", "health_bar_show_option"));
                if (v instanceof ModConfigSpec.ConfigValue cv) {
                    Object now = cv.get();
                    if (now instanceof Enum<?> en && !en.name().equals("NONE")) {
                        cv.set(Enum.valueOf((Class) en.getDeclaringClass(), "NONE"));
                        cv.save();
                        System.out.println("[OROR] Epic Fight's own health bar turned off (" + en.name() + " -> NONE): OROR shows health and stamina together");
                    }
                }
            }
        } catch (RuntimeException | LinkageError ex) {
            System.out.println("[OROR] Epic Fight's health bar option not reached: " + ex);
        }
    }
}
