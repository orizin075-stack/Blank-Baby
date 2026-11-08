package jp.oror.reborn.waza.client;

import jp.oror.reborn.waza.Waza;
import jp.oror.reborn.waza.WazaNet;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.neoforged.neoforge.network.PacketDistributor;

/**
 * (057) A contract offered by a character (the design's 同意式契約): its terms, what it gives and what it costs, set out
 * before anything is signed. Nothing is paid unless the player presses 同意する; closing the screen is a refusal.
 */
public final class PactScreen extends Screen {
    private final WazaNet.Offer offer;
    private final Waza w;
    private final String who;
    private boolean answered;

    PactScreen(WazaNet.Offer offer, Waza w, String who) {
        super(Component.literal(w == null ? "契約" : "契約〈" + w.name() + "〉"));
        this.offer = offer;
        this.w = w;
        this.who = who;
    }

    @Override
    protected void init() {
        int cx = this.width / 2, y = this.height / 2 + 34;
        this.addRenderableWidget(Button.builder(Component.literal("同意する"), b -> this.answer(true)).bounds(cx - 104, y, 100, 20).build());
        this.addRenderableWidget(Button.builder(Component.literal("断る"), b -> this.answer(false)).bounds(cx + 4, y, 100, 20).build());
    }

    private void answer(boolean accept) {
        if (!this.answered) {
            this.answered = true;
            PacketDistributor.sendToServer(new WazaNet.Answer(this.offer.contract(), accept));
        }
        this.onClose();
    }

    @Override
    public void removed() {
        if (!this.answered) {
            this.answered = true;
            PacketDistributor.sendToServer(new WazaNet.Answer(this.offer.contract(), false));
        }
        super.removed();
    }

    @Override
    public void render(GuiGraphics g, int mx, int my, float partial) {
        super.render(g, mx, my, partial);
        int cx = this.width / 2, y = this.height / 2 - 60;
        g.drawCenteredString(this.font, this.title, cx, y, 0xF2C230);
        g.drawCenteredString(this.font, Component.literal(this.who + " が契約を差し出している"), cx, y + 16, 0xFFFFFF);
        g.drawCenteredString(this.font, Component.literal("恩恵: " + this.offer.benefit()), cx, y + 36, 0xA0F0A0);
        g.drawCenteredString(this.font, Component.literal("代償: " + this.offer.cost()), cx, y + 50, 0xF0A0A0);
        g.drawCenteredString(this.font, Component.literal("同意するまで代償は生じない。閉じれば断ったことになる。"), cx, y + 70, 0xB0B0B0);
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }
}
