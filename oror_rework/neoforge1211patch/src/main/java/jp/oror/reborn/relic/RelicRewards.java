package jp.oror.reborn.relic;

import jp.oror.reborn.CharacterRelics;
import jp.oror.reborn.RelicSpec;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.enchantment.Enchantment;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;

/**
 * (058) The V8 reward enchantments: a relic that comes into the world as an item (the reward a god leaves, or one let
 * fall) carries its definition's enchantments once (耐久力 125, 修繕 1, ダメージ増加 125, …), marked so it is never
 * enchanted twice and never over what a player has put on it since.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class RelicRewards {
    public static int enchanted;

    private RelicRewards() {
    }

    @SubscribeEvent
    public static void join(EntityJoinLevelEvent e) {
        if (e.getLevel() instanceof ServerLevel sl && e.getEntity() instanceof ItemEntity it) {
            ItemStack s = it.getItem();
            if (enchant(sl, s)) {
                it.setItem(s);
            }
        }
    }

    /** Puts the relic's reward enchantments on the stack if it never had them; true when it did. */
    public static boolean enchant(ServerLevel sl, ItemStack s) {
        RelicSpec spec = CharacterRelics.of(s);
        RelicV9.Info info = spec == null ? null : RelicV9.info(spec.id);
        if (info == null || info.enchants.isEmpty()) {
            return false;
        }
        CompoundTag tag = s.getOrDefault(net.minecraft.core.component.DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        if (tag.getBoolean("ororV8Enchanted")) {
            return false;
        }
        var reg = sl.registryAccess().registryOrThrow(Registries.ENCHANTMENT);
        for (String[] en : info.enchants) {
            ResourceKey<Enchantment> key = ResourceKey.create(Registries.ENCHANTMENT, ResourceLocation.withDefaultNamespace(en[0]));
            Holder<Enchantment> h = reg.getHolder(key).orElse(null);
            if (h != null) {
                s.enchant(h, Integer.parseInt(en[1]));
            }
        }
        tag.putBoolean("ororV8Enchanted", true);
        s.set(net.minecraft.core.component.DataComponents.CUSTOM_DATA, CustomData.of(tag));
        enchanted++;
        return true;
    }
}
