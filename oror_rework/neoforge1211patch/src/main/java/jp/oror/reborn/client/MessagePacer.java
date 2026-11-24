package jp.oror.reborn.client;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashMap;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientChatReceivedEvent;
import net.neoforged.neoforge.client.event.ClientTickEvent;

/**
 * (r70) The user: "同時に複数のテキスト出るのやめて". The game's own messages (not a player's chat) came several at once:
 * a story's lines, the kingdom's and the villages' news, other mods' notices, all in the same moment, piled up in the
 * chat. Now they come one at a time, a second apart, in the order they were sent; the same line twice within three
 * seconds is shown once, and if more than eight wait, the oldest waiting goes. The line above the hotbar (one at a
 * time already) is as it was.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses", value = Dist.CLIENT)
public final class MessagePacer {
    private static final int GAP = 20, SAME = 60, WAITING = 8;
    private static final Deque<Component> QUEUE = new ArrayDeque<>();
    private static final Map<String, Long> SEEN = new HashMap<>();
    private static long ticks, lastShown = -GAP;

    private MessagePacer() {
    }

    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void received(ClientChatReceivedEvent.System e) {
        if (e.isCanceled() || e.isOverlay() || e.getMessage() == null) {
            return;
        }
        Component c = e.getMessage();
        String key = c.getString();
        Long at = SEEN.get(key);
        e.setCanceled(true);
        if (at != null && ticks - at < SAME) {
            return;
        }
        SEEN.put(key, ticks);
        if (QUEUE.isEmpty() && ticks - lastShown >= GAP) {
            show(c);
            return;
        }
        if (QUEUE.size() >= WAITING) {
            QUEUE.pollFirst();
        }
        QUEUE.addLast(c);
    }

    @SubscribeEvent
    public static void tick(ClientTickEvent.Post e) {
        ticks++;
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null) {
            QUEUE.clear();
            SEEN.clear();
            return;
        }
        if (!QUEUE.isEmpty() && ticks - lastShown >= GAP) {
            show(QUEUE.pollFirst());
        }
        if (ticks % 200 == 0) {
            SEEN.values().removeIf(t -> ticks - t > SAME);
        }
    }

    private static void show(Component c) {
        lastShown = ticks;
        try {
            Minecraft.getInstance().gui.getChat().addMessage(c);
        } catch (RuntimeException ignored) {
        }
    }
}
