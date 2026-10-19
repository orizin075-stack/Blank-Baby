package jp.oror.reborn.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.events.GuiEventListener;
import net.minecraft.network.chat.Component;

public final class SmokeScreens {
    public static void acknowledge(Minecraft mc) {
        if (mc.screen != null && mc.screen.getClass().getName().equals("ttv.migami.jeg.client.MagazineModeClient$1")) {
            for (GuiEventListener child : mc.screen.children()) {
                if (child instanceof Button button
                    && button.active
                    && button.getMessage().getString().equals(Component.translatable("gui.jeg.magazine_mode.confirm").getString())) {
                    button.onPress();
                    System.out.println("[OROR_SMOKE_UI] JEG magazine notice acknowledged through native button");
                    break;
                }
            }
        }
    }

    private SmokeScreens() {
    }
}
