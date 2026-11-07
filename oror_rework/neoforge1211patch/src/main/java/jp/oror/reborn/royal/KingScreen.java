package jp.oror.reborn.royal;

import java.util.Random;
import jp.oror.reborn.show.TechniqueShow;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.world.entity.Entity;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RenderGuiEvent;
import net.neoforged.neoforge.client.event.ViewportEvent;

/**
 * (054) The villager king's returns from death as films, on the screens of those who see them (within 64 blocks):
 * the bars of a letterbox close in; the hero's return ends in a flash of gold; the broken one's tears the screen with
 * bars of magenta, cyan and black and squares of the missing texture, and shakes it; the god's return clears the
 * last of the tearing, brightens, and ends in a white flash. His heaviest blows close by shake the view, and the broken
 * king's glitches tear the screen of whoever they strike nearby.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses", value = Dist.CLIENT)
public final class KingScreen {
    private KingScreen() {
    }

    private record Seen(String kind, float u, double dist) {
    }

    private static Seen seen(float partial) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.player == null) {
            return null;
        }
        Seen best = null;
        for (TechniqueShow.Active a : TechniqueShow.ACTIVE.values()) {
            if (!a.mechanic().startsWith("MOVE_KING_")) {
                continue;
            }
            Entity e = mc.level.getEntity(a.entity());
            if (!(e instanceof RoyalMob)) {
                continue;
            }
            double d = e.distanceTo(mc.player);
            float u = (mc.level.getGameTime() - a.start() + partial) / Math.max(1, a.length());
            if (u < 0F || u > 1F || d > 64) {
                continue;
            }
            if (best == null || d < best.dist) {
                best = new Seen(a.mechanic(), u, d);
            }
        }
        return best;
    }

    private static int argb(float a, int rgb) {
        return ((int) (Math.max(0F, Math.min(1F, a)) * 255) << 24) | (rgb & 0xFFFFFF);
    }

    private static float bump(float u, float from, float to) {
        if (u < from || u > to) {
            return 0F;
        }
        float t = (u - from) / (to - from);
        return (float) Math.sin(t * Math.PI);
    }

    @SubscribeEvent
    public static void screen(RenderGuiEvent.Post e) {
        Seen s = seen(e.getPartialTick().getGameTimeDeltaPartialTick(false));
        if (s == null) {
            return;
        }
        GuiGraphics g = e.getGuiGraphics();
        int w = g.guiWidth(), h = g.guiHeight();
        long t = Minecraft.getInstance().level.getGameTime();
        boolean revive = s.kind.startsWith("MOVE_KING_REVIVE_");
        if (revive) {
            float in = Math.min(1F, Math.min(s.u / 0.06F, (1F - s.u) / 0.06F));
            int bar = (int) (h * 0.11F * Math.max(0F, in));
            g.fill(0, 0, w, bar, 0xFF000000);
            g.fill(0, h - bar, w, h, 0xFF000000);
        }
        switch (s.kind) {
            case "MOVE_KING_REVIVE_HERO" -> {
                g.fill(0, 0, w, h, argb(0.22F * bump(s.u, 0.38F, 0.62F), 0xFFD860));
                g.fill(0, 0, w, h, argb(0.75F * bump(s.u, 0.84F, 0.97F), 0xFFF2C0));
            }
            case "MOVE_KING_REVIVE_GLITCH" -> {
                tear(g, w, h, t, s.u < 0.85F ? 1F : 0.4F);
                g.fill(0, 0, w, h, argb(0.6F * bump(s.u, 0.82F, 0.95F), 0xFF00FF));
            }
            case "MOVE_KING_REVIVE_DIVINE" -> {
                if (s.u < 0.3F) {
                    tear(g, w, h, t, 1F - s.u / 0.3F);
                }
                g.fill(0, 0, w, h, argb(0.14F * bump(s.u, 0.3F, 0.8F), 0xFFF8E0));
                g.fill(0, 0, w, h, argb(0.85F * bump(s.u, 0.8F, 0.92F), 0xFFFFFF));
            }
            case "MOVE_KING_DESYNC", "MOVE_KING_ROLLBACK", "MOVE_KING_CORRUPT", "MOVE_KING_GHOSTS" -> {
                if (s.dist < 20) {
                    tear(g, w, h, t, 0.35F * (1F - (float) s.dist / 20F));
                }
            }
            default -> {
            }
        }
    }

    /** The screen torn: bars of magenta, cyan, black and white, and squares of the missing texture. */
    private static void tear(GuiGraphics g, int w, int h, long t, float amount) {
        if (amount <= 0F) {
            return;
        }
        Random r = new Random(t * 7919L);
        int bars = (int) (4 + 10 * amount);
        int[] cols = {0xFF00FF, 0x00FFFF, 0x000000, 0xFFFFFF};
        for (int i = 0; i < bars; i++) {
            int y = r.nextInt(Math.max(1, h));
            int bh = 1 + r.nextInt(Math.max(1, (int) (14 * amount)));
            int x0 = r.nextInt(Math.max(1, w / 3));
            g.fill(x0, y, x0 + w / 3 + r.nextInt(Math.max(1, w)), y + bh, argb(0.3F + 0.4F * amount * r.nextFloat(), cols[r.nextInt(4)]));
        }
        int squares = (int) (1 + 4 * amount);
        for (int i = 0; i < squares; i++) {
            int sz = 16 + r.nextInt(32);
            int x = r.nextInt(Math.max(1, w - sz)), y = r.nextInt(Math.max(1, h - sz));
            int c = sz / 2;
            g.fill(x, y, x + c, y + c, 0xC0FF00FF);
            g.fill(x + c, y + c, x + sz, y + sz, 0xC0FF00FF);
            g.fill(x + c, y, x + sz, y + c, 0xC0000000);
            g.fill(x, y + c, x + c, y + sz, 0xC0000000);
        }
    }

    @SubscribeEvent
    public static void shake(ViewportEvent.ComputeCameraAngles e) {
        Seen s = seen((float) e.getPartialTick());
        if (s == null) {
            return;
        }
        double t = Minecraft.getInstance().level.getGameTime() + e.getPartialTick();
        float amp = switch (s.kind) {
            case "MOVE_KING_REVIVE_HERO" -> 2.5F * bump(s.u, 0.84F, 1F);
            case "MOVE_KING_REVIVE_GLITCH" -> s.u < 0.85F ? 1.2F : 4F * bump(s.u, 0.82F, 1F);
            case "MOVE_KING_REVIVE_DIVINE" -> 0.5F * bump(s.u, 0.4F, 0.75F) + 3.5F * bump(s.u, 0.8F, 1F);
            case "MOVE_KING_SLAM", "MOVE_KING_DRIVER", "MOVE_KING_CHARGE" -> s.dist < 16 ? 3F * bump(s.u, 0.3F, 0.7F) * (1F - (float) s.dist / 16F) : 0F;
            case "MOVE_KING_DESYNC", "MOVE_KING_CORRUPT" -> s.dist < 16 ? 1.5F * (1F - (float) s.dist / 16F) : 0F;
            default -> 0F;
        };
        if (amp <= 0F) {
            return;
        }
        if (s.kind.contains("GLITCH") || s.kind.contains("DESYNC") || s.kind.contains("CORRUPT")) {
            Random r = new Random((long) (t / 2) * 31L);
            e.setRoll(e.getRoll() + (r.nextFloat() - 0.5F) * 2F * amp);
            e.setYaw(e.getYaw() + (r.nextFloat() - 0.5F) * amp);
        } else {
            e.setRoll(e.getRoll() + (float) Math.sin(t * 1.7) * amp);
            e.setPitch(e.getPitch() + (float) Math.sin(t * 2.3) * amp * 0.5F);
        }
    }
}
