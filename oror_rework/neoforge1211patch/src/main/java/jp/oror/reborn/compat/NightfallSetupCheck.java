package jp.oror.reborn.compat;

import java.util.ArrayList;
import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.ModList;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;

/**
 * 0.17.24: the import ZIP leaves Nightfall and the Sword Soaring compatibility port to SETUP_NIGHTFALL.cmd, run once in
 * the profile folder. A game started without it still loads, only without their weapons and skills: say so on joining.
 * 0.17.25: also Indestructible, whose compatibility build carries NightfallCraft's enemy behaviour (it ships in the
 * import's mods folder, so an update by hand can miss it).
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class NightfallSetupCheck {
    @SubscribeEvent
    public static void login(PlayerEvent.PlayerLoggedInEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer player)) {
            return;
        }
        List<String> missing = new ArrayList<>();
        if (!ModList.get().isLoaded("efn")) {
            missing.add("Nightfall");
        }
        if (!ModList.get().isLoaded("sword_soaring")) {
            missing.add("Sword Soaring");
        }
        if (!ModList.get().isLoaded("indestructible")) {
            missing.add("Indestructible (indestructible-21.16.3-oror.1.jar)");
        }
        if (!missing.isEmpty()) {
            player.sendSystemMessage(Component.translatableWithFallback("oror.patch.setup_missing",
                "%s is not installed. Quit the game and run SETUP_NIGHTFALL.cmd in this profile's folder once (Indestructible comes in the import's mods folder).",
                String.join(" / ", missing)).withStyle(ChatFormatting.GOLD));
        }
    }

    private NightfallSetupCheck() {
    }
}
