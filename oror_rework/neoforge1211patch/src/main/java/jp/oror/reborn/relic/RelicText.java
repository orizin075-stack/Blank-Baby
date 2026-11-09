package jp.oror.reborn.relic;

import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.neoforged.fml.loading.FMLEnvironment;

/**
 * (058) The relics' tooltips as the V9 design rewrote them, one relic at a time: what it is and whose, its numbers,
 * its blows and their punishment, its powers in the words of the design, and the three technique keys of a weapon (by
 * the keys the player has set). Shift shows the rest: the motions, the V8 programs in words, the enchantments, the
 * design's promise for the god's four relics.
 */
public final class RelicText {
    private RelicText() {
    }

    /** Adds the V9 lines of this relic; false when it has none (the old lines then). */
    public static boolean tooltip(String id, List<Component> lines) {
        RelicV9.Info i = RelicV9.info(id);
        if (i == null) {
            return false;
        }
        boolean shift = FMLEnvironment.dist.isClient() && jp.oror.reborn.relic.client.RelicClient.shift();
        for (RelicV9.Line l : i.summary) {
            lines.add(Component.literal(keys(l.text())).withStyle(style(l.style())));
        }
        if (shift) {
            for (RelicV9.Line l : i.detail) {
                lines.add(Component.literal(keys(l.text())).withStyle(style(l.style())));
            }
        } else {
            lines.add(Component.literal("Shiftで動き・既存権能・エンチャントの詳細").withStyle(ChatFormatting.DARK_GRAY));
        }
        return true;
    }

    private static String keys(String s) {
        if (!s.contains("{K")) {
            return s;
        }
        for (int k = 0; k < 3; k++) {
            String name = FMLEnvironment.dist.isClient() ? jp.oror.reborn.relic.client.RelicClient.keyName(k) : new String[]{"G", "H", "J"}[k];
            s = s.replace("{K" + k + "}", name);
        }
        return s;
    }

    static ChatFormatting style(String s) {
        ChatFormatting f = ChatFormatting.getByName(s);
        return f != null ? f : ChatFormatting.GRAY;
    }
}
