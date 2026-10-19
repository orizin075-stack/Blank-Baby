package jp.oror.reborn.client;

import java.util.Map;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod.EventBusSubscriber;
import net.minecraftforge.event.entity.player.ItemTooltipEvent;

@EventBusSubscriber(
    modid = "oror_supreme_bosses",
    value = {Dist.CLIENT}
)
public final class AdventureTooltips {
    private static final Map<String, String> TIPS = Map.of(
        "azure_blade",
        "右クリック：24ブロックの蒼白斬撃。再使用2秒。",
        "star_staff",
        "右クリック：周囲14ブロックの敵へ魔力攻撃と自己治癒。",
        "forge_tool",
        "右クリック：装備を64耐久修復。",
        "rewind_talisman",
        "オフハンド：致死を一度取消。護符を消費、再発動10秒。",
        "dragon_coat",
        "装備：継続再生と火炎耐性。",
        "teia_boots",
        "装備：移動速度IVと跳躍III。",
        "purifying_dew",
        "右クリック：負の効果を浄化、HP6回復。1個消費。",
        "mana_crystal",
        "NPCへ右クリック：MP100回復。自分にはHP8と防御。",
        "dungeon_key",
        "封門へ右クリック：鍵1個を消費して主を解放。",
        "field_guide",
        "右クリック：遭遇と契約の案内を表示。"
    );

    @SubscribeEvent
    public static void tooltip(ItemTooltipEvent e) {
        ResourceLocation id = BuiltInRegistries.ITEM.getKey(e.getItemStack().getItem());
        if (id.getNamespace().equals("oror_supreme_bosses") && TIPS.containsKey(id.getPath())) {
            e.getToolTip().add(Component.literal(TIPS.get(id.getPath())));
        }
    }
}
