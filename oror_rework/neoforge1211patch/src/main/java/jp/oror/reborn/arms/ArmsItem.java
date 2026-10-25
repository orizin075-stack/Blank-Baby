package jp.oror.reborn.arms;

import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;

/** An ammunition or material item with {@code lines} tooltip lines under item.oror_supreme_bosses.<name>.desc<n>. */
public class ArmsItem extends Item {
    private final int lines;

    public ArmsItem(Properties properties, int lines) {
        super(properties);
        this.lines = lines;
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> tooltip, TooltipFlag flag) {
        tooltip(getDescriptionId(), lines, tooltip);
    }

    public static void tooltip(String key, int lines, List<Component> tooltip) {
        for (int i = 1; i <= lines; i++) {
            tooltip.add(Component.translatable(key + ".desc" + i).withStyle(i == 1 ? ChatFormatting.GOLD : ChatFormatting.GRAY));
        }
    }
}
