package jp.oror.reborn.client;

import jp.oror.reborn.CharacterRelics;
import jp.oror.reborn.CharacterSpec;
import jp.oror.reborn.RelicSpec;
import net.minecraft.network.chat.Component;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod.EventBusSubscriber;
import net.minecraftforge.event.entity.player.ItemTooltipEvent;

@EventBusSubscriber(
    modid = "oror_supreme_bosses",
    value = {Dist.CLIENT}
)
public final class CharacterRelicTooltips {
    @SubscribeEvent
    public static void tooltip(ItemTooltipEvent e) {
        RelicSpec s = CharacterRelics.of(e.getItemStack());
        if (s != null) {
            e.getToolTip().add(Component.literal(CharacterSpec.ALL.get(s.character).name + "の特殊装備"));
            e.getToolTip().add(Component.literal("右クリックでアーツ発動。待機 " + (float)jp.oror.reborn.RelicArts.cooldown(s.id, s.cooldown) / 20.0F + "秒。"));
            if (s.rank == 3) {
                e.getToolTip().add(Component.literal("伝説・独立5%ドロップ。手に持つと存在断絶を拒む。"));
            }
        }
    }
}
