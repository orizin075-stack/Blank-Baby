package jp.oror.reborn.combat.client;

import jp.oror.reborn.combat.MobStamina;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.ModList;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RegisterGuiLayersEvent;
import net.neoforged.neoforge.client.gui.VanillaGuiLayers;

/**
 * (r73) The player's own stamina on its screen (Exhaustion): while it is exhausted, the screen's edges pulse red with
 * its breathing; and, where Ares HUD does not show Epic Fight's stamina bar already (as the pack's does, under the
 * health), a slim bar over the hotbar while the stamina is not full: yellow, orange under a third, flashing red exhausted.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public final class ExhaustionHud {
    private ExhaustionHud() {
    }

    @SubscribeEvent
    public static void layers(RegisterGuiLayersEvent e) {
        e.registerAbove(VanillaGuiLayers.HOTBAR, ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "exhaustion"), ExhaustionHud::draw);
    }

    private static void draw(GuiGraphics g, DeltaTracker delta) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.level == null || mc.options.hideGui || mc.player.isCreative() || mc.player.isSpectator()) {
            return;
        }
        MobStamina.Seen s = MobStamina.SEEN.get(mc.player.getId());
        if (s == null) {
            return;
        }
        int w = g.guiWidth(), h = g.guiHeight();
        long now = mc.level.getGameTime();
        float t = now + delta.getGameTimeDeltaPartialTick(false);
        if (s.winded()) {
            // the edges of the screen pulse red, about once a second and a half
            float pulse = 0.5F + 0.5F * Mth.sin(t * 0.21F);
            int a = (int) (40 + 70 * pulse);
            // (the look run: a straight falloff left the inner edge seen as a box) fading out as the square of the distance in
            int edge = Math.max(24, w / 9);
            for (int i = 0; i < edge; i += 2) {
                float f = 1F - i / (float) edge;
                int alpha = (int) (a * f * f * 0.5F);
                int c = (alpha << 24) | 0x9A0E0E;
                g.fill(0, i, w, i + 2, c);
                g.fill(0, h - i - 2, w, h - i, c);
                g.fill(i, 0, i + 2, h, c);
                g.fill(w - i - 2, 0, w - i, h, c);
            }
        }
        if (ModList.get().isLoaded("ares_hud") || s.percent() >= 100 && !s.winded()) {
            return;
        }
        int bw = 120, bx = (w - bw) / 2, by = h - 32 - 6;
        float frac = Mth.clamp(s.percent() / 100F, 0F, 1F);
        int col = s.winded() ? ((now / 4) % 2 == 0 ? 0xFFE84040 : 0xFF8A2020) : frac < 0.34F ? 0xFFE8962E : 0xFFF2D24A;
        g.fill(bx - 1, by - 1, bx + bw + 1, by + 3, 0xB0101010);
        g.fill(bx, by, bx + (int) (bw * frac), by + 2, col);
    }
}
