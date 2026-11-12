package jp.oror.reborn.duel.client;

import com.mojang.blaze3d.platform.Lighting;
import java.util.HashMap;
import java.util.Map;
import jp.oror.reborn.duel.GrimoireBook;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.client.resources.sounds.SimpleSoundInstance;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SpawnEggItem;
import net.neoforged.neoforge.network.PacketDistributor;
import org.lwjgl.glfw.GLFW;

/**
 * (059e) The dominion grimoire lying open ({@link GrimoireBook}). It opens: its cover swings round the spine and the
 * first leaf falls open (a little over half a second, a page's rustle and the grimoire's chime). Each spread shows two
 * pages of four sealed mobs: their likeness (the mob itself, turning to follow the pointer; its spawn egg if it cannot
 * be drawn here), its number, its name and whether it is out (召喚中), sealed (封印中) or waiting to rise (復活待ち).
 * A click chooses one (gold frame); the button under the right page calls it out or back. The arrows, or the arrow
 * keys, turn the page: the leaf lifts and turns over the spine. Gold motes drift about the open book.
 */
public final class GrimoireScreen extends Screen {
    private static final ResourceLocation TEX = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "textures/gui/grimoire_book.png");
    private static final int TW = 512, TH = 256, BW = 256, BH = 180, PAGE = 128;
    private static final int OPEN = 12, FLIP = 8, PER_PAGE = 4;
    private static final int INK = 0x3A2A1E, TITLE = 0x4A2A5E, OUT = 0x2E7D32, WAIT = 0x9A4A10, SEALED = 0x5A4A6A;

    private final InteractionHand hand;
    private int spread;
    private int openTicks;
    private int flipTicks = -1;
    private int flipDir;
    private int flipFrom;
    private int selected = -1;
    private int ticks;
    private final Map<String, LivingEntity> looks = new HashMap<>();
    private final Map<String, Boolean> unseeable = new HashMap<>();

    private GrimoireScreen(InteractionHand hand) {
        super(Component.literal("支配の魔導書"));
        this.hand = hand;
    }

    public static void open(InteractionHand hand) {
        Minecraft.getInstance().setScreen(new GrimoireScreen(hand));
    }

    private CompoundTag data() {
        Minecraft mc = Minecraft.getInstance();
        return mc.player == null ? new CompoundTag() : GrimoireBook.data(mc.player.getItemInHand(hand));
    }

    private ListTag entries() {
        return data().getList("Entries", 10);
    }

    private int spreads(int n) {
        return Math.max(1, (n + PER_PAGE * 2 - 1) / (PER_PAGE * 2));
    }

    @Override
    protected void init() {
        CompoundTag d = data();
        ListTag e = d.getList("Entries", 10);
        if (selected < 0 && !e.isEmpty()) {
            selected = Mth.clamp(d.getInt("Selected"), 0, e.size() - 1);
            spread = selected / (PER_PAGE * 2);
        }
        if (openTicks == 0) {
            play(SoundEvents.BOOK_PAGE_TURN, 0.9F);
            play(SoundEvents.ENCHANTMENT_TABLE_USE, 1.4F);
        }
    }

    private void play(SoundEvent s, float pitch) {
        Minecraft.getInstance().getSoundManager().play(SimpleSoundInstance.forUI(s, pitch));
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }

    @Override
    public void tick() {
        ticks++;
        if (openTicks < OPEN) {
            openTicks++;
        }
        if (flipTicks >= 0 && ++flipTicks >= FLIP) {
            flipTicks = -1;
        }
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || !GrimoireBook.isGrimoire(mc.player.getItemInHand(hand))) {
            onClose();
        }
    }

    private int bx() {
        return (width - BW) / 2;
    }

    private int by() {
        return (height - BH) / 2 - 8;
    }

    private void blit(GuiGraphics g, int x, int y, int u, int v, int w, int h) {
        g.blit(TEX, x, y, u, v, w, h, TW, TH);
    }

    /** Part of the sheet squeezed toward (or away from) the spine: the turning cover or leaf. */
    private void blitTurning(GuiGraphics g, int spineX, int y, int u, boolean toRight, float scale) {
        if (scale <= 0.02F) {
            return;
        }
        g.pose().pushPose();
        g.pose().translate(spineX, y, 0);
        g.pose().scale(scale, 1F, 1F);
        blit(g, toRight ? 0 : -PAGE, 0, u, 0, PAGE, BH);
        g.pose().popPose();
    }

    @Override
    public void render(GuiGraphics g, int mx, int my, float pt) {
        super.render(g, mx, my, pt);
        int x = bx(), y = by(), spine = x + PAGE;
        ListTag e = entries();
        int last = spreads(e.size()) - 1;
        spread = Mth.clamp(spread, 0, last);
        float open = Math.min(1F, (openTicks + pt) / OPEN);
        if (open < 1F) {
            // opening: the cover swings over the spine, then the first leaf falls open
            float a = open * Mth.PI;
            blit(g, spine, y, PAGE, 0, PAGE, BH);
            if (a < Mth.HALF_PI) {
                blitTurning(g, spine, y, 256, true, Mth.cos(a));
            } else {
                blitTurning(g, spine, y, 0, false, -Mth.cos(a));
            }
            motes(g, x, y, open);
            return;
        }
        if (flipTicks < 0) {
            blit(g, x, y, 0, 0, BW, BH);
            page(g, x + 8, y + 7, spread * 2, e, mx, my);
            page(g, spine + 2, y + 7, spread * 2 + 1, e, mx, my);
        } else {
            float f = Math.min(1F, (flipTicks + pt) / FLIP);
            float a = f * Mth.PI;
            blit(g, x, y, 0, 0, BW, BH);
            if (flipDir > 0) {
                // the old left page stays until the leaf lies down; the new right page is under the turning leaf
                page(g, x + 8, y + 7, flipFrom * 2, e, -1, -1);
                page(g, spine + 2, y + 7, spread * 2 + 1, e, -1, -1);
                if (a < Mth.HALF_PI) {
                    blitTurning(g, spine, y, PAGE, true, Mth.cos(a));
                } else {
                    blitTurning(g, spine, y, 0, false, -Mth.cos(a));
                }
            } else {
                page(g, x + 8, y + 7, spread * 2, e, -1, -1);
                page(g, spine + 2, y + 7, flipFrom * 2 + 1, e, -1, -1);
                if (a < Mth.HALF_PI) {
                    blitTurning(g, spine, y, 0, false, Mth.cos(a));
                } else {
                    blitTurning(g, spine, y, PAGE, true, -Mth.cos(a));
                }
            }
        }
        // the page arrows and the call button
        if (spread > 0) {
            arrow(g, x + 14, y + BH - 22, "◀", mx, my);
        }
        if (spread < last) {
            arrow(g, x + BW - 30, y + BH - 22, "▶", mx, my);
        }
        if (selected >= 0 && selected < e.size()) {
            boolean out = e.getCompound(selected).hasUUID("ActiveEntity");
            button(g, spine + 26, y + BH - 26, 76, 16, out ? "戻す" : "呼び出す", mx, my);
        }
        motes(g, x, y, 1F);
    }

    /** One page: its four sealed mobs (or, on the first page of an empty book, how to fill it). */
    private void page(GuiGraphics g, int px, int py, int pageIndex, ListTag e, int mx, int my) {
        if (pageIndex == 0) {
            g.drawString(font, "支配の魔導書", px + 6, py + 4, TITLE, false);
            g.drawString(font, "封印 " + e.size() + " / 128", px + 70, py + 4, SEALED, false);
        } else if (pageIndex % 2 == 1) {
            g.drawString(font, "第 " + (pageIndex + 1) + " 頁", px + 76, py + 4, SEALED, false);
        } else {
            g.drawString(font, "第 " + (pageIndex + 1) + " 頁", px + 6, py + 4, SEALED, false);
        }
        if (e.isEmpty() && pageIndex == 0) {
            int ly = py + 26;
            for (FormattedCharSequence line : font.split(Component.literal(
                "まだ何も封じていない。決闘に勝って得た封印髪をもう片方の手に持ち、この書を右クリックすると、ここに収められる。"), 104)) {
                g.drawString(font, line, px + 6, ly, INK, false);
                ly += 10;
            }
            return;
        }
        for (int r = 0; r < PER_PAGE; r++) {
            int i = pageIndex * PER_PAGE + r;
            if (i >= e.size()) {
                break;
            }
            CompoundTag c = e.getCompound(i);
            int rx = px + 2, ry = py + 18 + r * 36;
            boolean over = mx >= rx && mx < rx + 114 && my >= ry && my < ry + 34;
            if (i == selected) {
                g.fill(rx, ry, rx + 114, ry + 34, 0x40E3B341);
                g.renderOutline(rx, ry, 114, 34, 0xFFC8962A);
            } else if (over) {
                g.fill(rx, ry, rx + 114, ry + 34, 0x20E3B341);
            }
            likeness(g, c.getString("EntityId"), rx + 2, ry + 1, rx + 30, ry + 33, mx, my);
            String name = c.getString("DisplayName");
            if (font.width(name) > 76) {
                name = font.plainSubstrByWidth(name, 72) + "…";
            }
            g.drawString(font, "No." + (i + 1), rx + 34, ry + 3, SEALED, false);
            g.drawString(font, name, rx + 34, ry + 13, INK, false);
            boolean out = c.hasUUID("ActiveEntity");
            boolean rising = c.getBoolean("RevivePending");
            g.drawString(font, out ? "召喚中" : rising ? "復活待ち" : "封印中", rx + 34, ry + 23, out ? OUT : rising ? WAIT : SEALED, false);
        }
    }

    /** The sealed mob itself, small and turning to the pointer; its spawn egg if it cannot be drawn here. */
    private void likeness(GuiGraphics g, String id, int x1, int y1, int x2, int y2, int mx, int my) {
        Minecraft mc = Minecraft.getInstance();
        LivingEntity look = unseeable.containsKey(id) ? null : looks.computeIfAbsent(id, k -> make(mc, k));
        if (look == null) {
            unseeable.put(id, true);
            EntityType<?> type = EntityType.byString(id).orElse(null);
            SpawnEggItem egg = type == null ? null : SpawnEggItem.byId(type);
            if (egg != null) {
                g.renderItem(new ItemStack(egg), x1 + 6, y1 + 8);
            } else {
                g.drawString(font, "？", x1 + 10, y1 + 12, SEALED, false);
            }
            return;
        }
        float size = Math.max(look.getBbHeight(), look.getBbWidth());
        int scale = Mth.clamp((int) (26F / Math.max(0.5F, size)), 4, 24);
        try {
            // (it clips itself to the box)
            InventoryScreen.renderEntityInInventoryFollowsMouse(g, x1, y1, x2, y2, scale, 0.0625F, mx, my, look);
        } catch (Throwable ex) {
            // a mob that cannot be drawn outside its world: the drawing state put back, its spawn egg from now on
            while (!g.pose().clear()) {
                g.pose().popPose();
            }
            try {
                g.disableScissor();
            } catch (RuntimeException ignored) {
                // its clip had not begun
            }
            Lighting.setupFor3DItems();
            mc.getEntityRenderDispatcher().setRenderShadow(true);
            unseeable.put(id, true);
        }
    }

    private static LivingEntity make(Minecraft mc, String id) {
        try {
            EntityType<?> type = EntityType.byString(id).orElse(null);
            Entity en = type == null || mc.level == null ? null : type.create(mc.level);
            return en instanceof LivingEntity le ? le : null;
        } catch (Throwable ex) {
            return null;
        }
    }

    private void arrow(GuiGraphics g, int x, int y, String s, int mx, int my) {
        boolean over = mx >= x && mx < x + 16 && my >= y && my < y + 14;
        g.drawString(font, s, x + 4, y + 3, over ? 0xC8962A : TITLE, false);
    }

    private void button(GuiGraphics g, int x, int y, int w, int h, String s, int mx, int my) {
        boolean over = mx >= x && mx < x + w && my >= y && my < y + h;
        g.fill(x, y, x + w, y + h, over ? 0xFF6A4384 : 0xFF4A2A5E);
        g.renderOutline(x, y, w, h, 0xFFE3B341);
        g.drawString(font, s, x + (w - font.width(s)) / 2, y + 4, 0xF3E9C8, false);
    }

    /** Gold motes drifting up about the open book. */
    private void motes(GuiGraphics g, int x, int y, float strength) {
        for (int k = 0; k < 14; k++) {
            float t = ((ticks + k * 17) % 80) / 80F;
            int mx = x + (int) ((k * 53 % BW) + Mth.sin((ticks + k * 9) * 0.07F) * 6);
            int my = y + BH - (int) (t * (BH + 20));
            int alpha = (int) (strength * 200 * Mth.sin(t * Mth.PI));
            if (alpha > 8) {
                g.fill(mx, my, mx + (k % 3 == 0 ? 2 : 1), my + (k % 3 == 0 ? 2 : 1), (alpha << 24) | 0xE3B341);
            }
        }
    }

    private void turn(int dir) {
        int last = spreads(entries().size()) - 1;
        int to = Mth.clamp(spread + dir, 0, last);
        if (to == spread || flipTicks >= 0 || openTicks < OPEN) {
            return;
        }
        flipFrom = spread;
        flipDir = dir;
        spread = to;
        flipTicks = 0;
        play(SoundEvents.BOOK_PAGE_TURN, 0.9F + (ticks % 5) * 0.05F);
    }

    @Override
    public boolean mouseClicked(double mx, double my, int button) {
        if (button != 0 || openTicks < OPEN) {
            return super.mouseClicked(mx, my, button);
        }
        int x = bx(), y = by(), spine = x + PAGE;
        ListTag e = entries();
        if (mx >= x + 14 && mx < x + 30 && my >= y + BH - 22 && my < y + BH - 8) {
            turn(-1);
            return true;
        }
        if (mx >= x + BW - 30 && mx < x + BW - 14 && my >= y + BH - 22 && my < y + BH - 8) {
            turn(1);
            return true;
        }
        if (selected >= 0 && selected < e.size() && mx >= spine + 26 && mx < spine + 102 && my >= y + BH - 26 && my < y + BH - 10) {
            send(selected, GrimoireBook.TOGGLE);
            play(SoundEvents.ENCHANTMENT_TABLE_USE, 0.8F);
            return true;
        }
        for (int side = 0; side < 2 && flipTicks < 0; side++) {
            int px = (side == 0 ? x + 8 : spine + 2) + 2;
            for (int r = 0; r < PER_PAGE; r++) {
                int i = (spread * 2 + side) * PER_PAGE + r;
                int ry = y + 7 + 18 + r * 36;
                if (i < e.size() && mx >= px && mx < px + 114 && my >= ry && my < ry + 34) {
                    selected = i;
                    send(i, GrimoireBook.SELECT);
                    play(SoundEvents.UI_BUTTON_CLICK.value(), 1.6F);
                    return true;
                }
            }
        }
        return super.mouseClicked(mx, my, button);
    }

    private void send(int index, int action) {
        PacketDistributor.sendToServer(new GrimoireBook.Act(hand == InteractionHand.OFF_HAND, index, action));
    }

    @Override
    public boolean keyPressed(int key, int scan, int mods) {
        if (key == GLFW.GLFW_KEY_RIGHT || key == GLFW.GLFW_KEY_D) {
            turn(1);
            return true;
        }
        if (key == GLFW.GLFW_KEY_LEFT || key == GLFW.GLFW_KEY_A) {
            turn(-1);
            return true;
        }
        return super.keyPressed(key, scan, mods);
    }

    @Override
    public void onClose() {
        play(SoundEvents.BOOK_PUT, 1.0F);
        looks.clear();
        super.onClose();
    }
}
