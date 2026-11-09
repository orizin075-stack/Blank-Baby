package jp.oror.reborn.client;

import jp.oror.reborn.CharacterRelics;
import jp.oror.reborn.CharacterSpec;
import jp.oror.reborn.RelicArts;
import jp.oror.reborn.RelicSpec;
import jp.oror.reborn.relic.RelicV9;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.player.ItemTooltipEvent;

/**
 * The relics' common tooltip lines. (058) A relic the V9 design rewrote says everything itself (its number, its
 * powers, its keys); only how its right-click art is used and when it is ready again are added here.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses", value = {Dist.CLIENT})
public final class CharacterRelicTooltips {
    @SubscribeEvent
    public static void tooltip(ItemTooltipEvent e) {
        RelicSpec s = CharacterRelics.of(e.getItemStack());
        if (s == null) {
            return;
        }
        if (RelicV9.info(s.id) != null) {
            e.getToolTip().add(Component.literal("右クリック：既存の権能（待機 " + (float) Math.max(20, RelicArts.cooldown(s.id, s.cooldown) * 3 / 4) / 20.0F + "秒）")
                .withStyle(ChatFormatting.DARK_AQUA));
            return;
        }
        e.getToolTip().add(Component.literal(((CharacterSpec) CharacterSpec.ALL.get(s.character)).name + "の特殊装備"));
        e.getToolTip().add(Component.literal("右クリックでアーツ発動。待機 " + (float) RelicArts.cooldown(s.id, s.cooldown) / 20.0F + "秒。"));
        if (s.rank == 3) {
            e.getToolTip().add(Component.literal("伝説・独立5%ドロップ。手に持つと存在断絶を拒む。"));
        }
    }
}
