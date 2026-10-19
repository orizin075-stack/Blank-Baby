package jp.oror.reborn;

import java.util.LinkedHashMap;
import java.util.Map;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.minecraftforge.registries.RegistryObject;

/**
 * NightfallCraft items the fused quest book asks for. Until v0.17.3 the mod registered 70 English-named stand-ins
 * ("Air Tachi（融合版）" ...) for the ones whose mods are not in this pack; v0.17.4 removed them, and NightfallFusion
 * now counts a task for such an unported item as done and pays its reward in experience instead.
 */
public final class FusionItems {
    /** Kept empty: OrorReborn still touches it to load the class and fills the creative tab from it. */
    public static final Map<String, RegistryObject<Item>> ITEMS = new LinkedHashMap<>();

    public static Item resolve(String source) {
        return source.equals("wom:tormented_mind") ? (Item)BuiltInRegistries.ITEM.get(new ResourceLocation("wom:herrscher")) : Items.AIR;
    }

    /** True for the NightfallCraft items that had a stand-in: their mods are not part of this pack. */
    public static boolean unported(String source) {
        return source.startsWith("tcrcore:") || source.startsWith("efn:") || source.startsWith("fantasy_armor:");
    }

    private FusionItems() {
    }
}
