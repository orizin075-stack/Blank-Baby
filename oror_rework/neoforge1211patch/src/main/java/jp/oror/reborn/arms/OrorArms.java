package jp.oror.reborn.arms;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.ModList;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;
import net.neoforged.neoforge.registries.RegisterEvent;
import net.neoforged.neoforge.registries.RegisterEvent.RegisterHelper;

/**
 * 0.17.27: OROR's arms on Superb Warfare. The railgun 天穿 and the laser gun 神罰 are Superb Warfare guns (data in
 * data/oror_supreme_bosses/sbw/guns, models in assets/oror_supreme_bosses/sbw/guns); their classes are only loaded
 * with Superb Warfare installed (see {@code jp.oror.reborn.arms.sbw.SbwArms}). Their ammunition, the Matter Cartridge
 * and the Blueprinter are plain items and always registered.
 */
@EventBusSubscriber(modid = OrorArms.ID, bus = EventBusSubscriber.Bus.MOD)
public final class OrorArms {
    public static final String ID = "oror_supreme_bosses";
    public static final ResourceLocation TAB = id("supreme_entities");

    public static Item BLUEPRINTER;
    public static Item MATTER_CARTRIDGE;
    public static Item RAIL_SLUG;
    public static Item FOCUS_CELL;
    public static Item RAILGUN;
    public static Item LASER_GUN;

    public static ResourceLocation id(String path) {
        return ResourceLocation.fromNamespaceAndPath(ID, path);
    }

    @SubscribeEvent
    public static void register(RegisterEvent event) {
        event.register(Registries.ITEM, helper -> {
            BLUEPRINTER = add(helper, "blueprinter", new BlueprinterItem(new Item.Properties().stacksTo(1).fireResistant().rarity(Rarity.EPIC)));
            MATTER_CARTRIDGE = add(helper, "matter_cartridge", new ArmsItem(new Item.Properties().rarity(Rarity.RARE), 2));
            RAIL_SLUG = add(helper, "rail_slug", new ArmsItem(new Item.Properties().stacksTo(16).rarity(Rarity.RARE), 2));
            FOCUS_CELL = add(helper, "focus_cell", new ArmsItem(new Item.Properties().stacksTo(16).rarity(Rarity.RARE), 2));
            if (ModList.get().isLoaded("superbwarfare")) {
                jp.oror.reborn.arms.sbw.SbwArms.register(helper);
            }
        });
    }

    static Item add(RegisterHelper<Item> helper, String name, Item item) {
        helper.register(id(name), item);
        return item;
    }

    @SubscribeEvent
    public static void tab(BuildCreativeModeTabContentsEvent event) {
        if (!event.getTabKey().location().equals(TAB)) {
            return;
        }
        for (Item item : new Item[] {RAILGUN, RAIL_SLUG, LASER_GUN, FOCUS_CELL, BLUEPRINTER, MATTER_CARTRIDGE}) {
            if (item != null) {
                event.accept(item);
            }
        }
    }

    private OrorArms() {
    }
}
