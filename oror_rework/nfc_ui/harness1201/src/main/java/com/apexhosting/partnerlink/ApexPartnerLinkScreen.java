package com.apexhosting.partnerlink;

import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/**
 * CI only. TCR Core 2.8.7's title screen mixin refers to Apex Hosting's partner-link screen, which NightfallCraft's
 * manifest does not include; without the class the mixin cannot be applied and the client stops at start-up.
 */
public class ApexPartnerLinkScreen extends Screen {
    public ApexPartnerLinkScreen() {
        super(Component.empty());
    }
}
