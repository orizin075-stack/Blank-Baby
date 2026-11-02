package jp.oror.reborn;

import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;

/**
 * (051) What every player starts with, once, the first time they come into a world: a full set of iron armour (worn,
 * where the slot is free), sixteen steaks, a Superb Warfare Glock 17 and 96 rounds of handgun ammunition. The mark that
 * they had it is kept with the player's persisted data, so dying and coming back does not give it again.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class StarterKit {
    public static final String MARK = "OrorStarterKit";

    private StarterKit() {
    }

    @SubscribeEvent
    public static void joined(PlayerEvent.PlayerLoggedInEvent e) {
        Player player = e.getEntity();
        if (player.level().isClientSide) {
            return;
        }
        CompoundTag kept = player.getPersistentData().getCompound(Player.PERSISTED_NBT_TAG);
        if (kept.getBoolean(MARK)) {
            return;
        }
        List<String> given = give(player);
        kept.putBoolean(MARK, true);
        player.getPersistentData().put(Player.PERSISTED_NBT_TAG, kept);
        player.sendSystemMessage(Component.translatable("message.oror_supreme_bosses.starter_kit"));
        org.slf4j.LoggerFactory.getLogger("OROR").info("STARTER-KIT {} {}", player.getGameProfile().getName(), given);
    }

    /** Gives the kit; returns what was given, as item ids with their counts. */
    public static List<String> give(Player player) {
        List<String> given = new ArrayList<>();
        Item[] armour = {Items.IRON_HELMET, Items.IRON_CHESTPLATE, Items.IRON_LEGGINGS, Items.IRON_BOOTS};
        EquipmentSlot[] slots = {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET};
        for (int i = 0; i < armour.length; i++) {
            ItemStack piece = new ItemStack(armour[i]);
            if (player.getItemBySlot(slots[i]).isEmpty()) {
                player.setItemSlot(slots[i], piece);
            } else {
                hand(player, piece);
            }
            given.add(BuiltInRegistries.ITEM.getKey(armour[i]) + "x1");
        }
        hand(player, new ItemStack(Items.COOKED_BEEF, 16));
        given.add("minecraft:cooked_beefx16");
        Item pistol = BuiltInRegistries.ITEM.get(ResourceLocation.fromNamespaceAndPath("superbwarfare", "glock_17"));
        Item rounds = BuiltInRegistries.ITEM.get(ResourceLocation.fromNamespaceAndPath("superbwarfare", "handgun_ammo"));
        if (pistol != Items.AIR) {
            hand(player, new ItemStack(pistol));
            given.add("superbwarfare:glock_17x1");
        }
        if (rounds != Items.AIR) {
            int left = 96;
            while (left > 0) {
                int n = Math.min(left, new ItemStack(rounds).getMaxStackSize());
                hand(player, new ItemStack(rounds, n));
                left -= n;
            }
            given.add("superbwarfare:handgun_ammox96");
        }
        return given;
    }

    private static void hand(Player player, ItemStack stack) {
        if (!player.getInventory().add(stack)) {
            player.drop(stack, false);
        }
    }
}
