package jp.oror.reborn.compat;

import java.util.Set;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import yesman.epicfight.client.world.capabilites.entitypatch.player.LocalPlayerPatch;
import yesman.epicfight.config.ClientConfig;
import yesman.epicfight.world.capabilities.EpicFightCapabilities;

/**
 * NightfallCraft's weapons fight without pressing R first (from the other 0.17.25). Taking a weapon, or holding one
 * while entering a world (a player saved in the vanilla mode), turns on Epic Fight's combat mode, and any weapon held is
 * added to Epic Fight's combat items so its own switching knows it next time.
 *
 * 0.17.27: local manual switches stop the entry reconciliation window. Selecting another hotbar slot also
 * counts as taking a weapon, including a second stack of the same item.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses", value = Dist.CLIENT)
public final class NightfallAutomaticCombatClient {
    /** Ticks after entering a world in which the mode the server restores may still arrive, and is overruled. */
    private static final int ENTERING_TICKS = 60;
    private static Set<Item> prepared;
    private static LocalPlayer player;
    private static Item held;
    private static int heldSlot = -1;
    private static int ticks;

    @SubscribeEvent
    public static void tick(ClientTickEvent.Post event) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.level == null) {
            player = null;
            return;
        }
        if (mc.player != player) {
            player = mc.player;
            held = null;
            heldSlot = -1;
            ticks = 0;
        }
        ticks++;
        ItemStack stack = mc.player.getMainHandItem();
        boolean taken = stack.getItem() != held || mc.player.getInventory().selected != heldSlot;
        heldSlot = mc.player.getInventory().selected;
        held = stack.getItem();
        if (!mc.player.isAlive() || mc.player.isSpectator() || !(taken || ticks <= ENTERING_TICKS)) {
            return;
        }
        preferences();
        if (!NightfallAutomaticCombat.weapon(stack)) {
            return;
        }
        if (ClientConfig.combatCategorizedItems != null) {
            ClientConfig.combatCategorizedItems.add(stack.getItem());
        }
        LocalPlayerPatch patch = EpicFightCapabilities.getEntityPatch(mc.player, LocalPlayerPatch.class);
        if (patch != null && !patch.isEpicFightMode()) {
            patch.toEpicFightMode(true);
        }
    }

    /** NightfallCraft's combat items that this pack has, once per loaded Epic Fight client config. */
    private static void preferences() {
        Set<Item> items = ClientConfig.combatCategorizedItems;
        if (items == null || items == prepared) {
            return;
        }
        for (String id : NightfallAutomaticCombat.ORIGINAL_PREFERRED) {
            ResourceLocation key = ResourceLocation.tryParse(id);
            if (key != null && BuiltInRegistries.ITEM.containsKey(key)) {
                items.add(BuiltInRegistries.ITEM.get(key));
            }
        }
        // An unknown id in the config list reads as air; an empty hand stays a mining hand.
        items.remove(Items.AIR);
        if (ClientConfig.miningCategorizedItems != null) {
            ClientConfig.miningCategorizedItems.add(Items.AIR);
        }
        prepared = items;
    }

    /** A local mode choice must also win during the initial server-mode reconciliation window. */
    public static void manualVanillaMode(boolean synchronize) {
        if (synchronize) {
            ticks = ENTERING_TICKS + 1;
        }
    }

    private NightfallAutomaticCombatClient() {
    }
}
