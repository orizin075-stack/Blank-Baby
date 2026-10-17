package jp.oror.reborn;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeSet;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterials;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.ArmorItem.Type;
import net.minecraft.world.item.Item.Properties;
import net.neoforged.neoforge.registries.DeferredItem;

public final class FusionItems {
   public static final Map<String, DeferredItem<Item>> ITEMS = new LinkedHashMap<>();

   public static Item resolve(String source) {
      DeferredItem<Item> own = ITEMS.get(source);
      if (own != null) {
         return (Item)own.get();
      } else {
         return source.equals("wom:tormented_mind") ? (Item)BuiltInRegistries.ITEM.get(ResourceLocation.parse("wom:herrscher")) : Items.AIR;
      }
   }

   private FusionItems() {
   }

   static {
      JsonObject source = NightfallFusion.SOURCE;
      TreeSet<String> refs = new TreeSet<>();

      for (JsonElement element : source.getAsJsonArray("quests")) {
         JsonObject q = element.getAsJsonObject();

         for (String group : new String[]{"tasks", "rewards"}) {
            if (q.has(group)) {
               for (JsonElement row : q.getAsJsonArray(group)) {
                  JsonElement value = row.getAsJsonObject().get("item");
                  if (value != null) {
                     String id = value.isJsonPrimitive()
                        ? value.getAsString()
                        : (value.getAsJsonObject().has("id") ? value.getAsJsonObject().get("id").getAsString() : "");
                     if (id.startsWith("tcrcore:") || id.startsWith("efn:") || id.startsWith("fantasy_armor:")) {
                        refs.add(id);
                     }
                  }
               }
            }
         }
      }

      for (String sourceId : refs) {
         String path = "fusion_" + sourceId.replace(':', '_');
         boolean armor = sourceId.endsWith("helmet");
         boolean weapon = sourceId.startsWith("efn:") && !sourceId.endsWith("ingot") && !sourceId.endsWith("heart")
            || sourceId.startsWith("tcrcore:magic_")
            || List.of("emberfang", "magmaheart", "ashen_crescent", "cinderwyrm", "purging_swallow").contains(sourceId.substring(sourceId.indexOf(58) + 1));
         DeferredItem<Item> item = OrorReborn.ITEMS
            .register(
               path,
               () -> (Item)(armor
                     ? new ArmorItem(ArmorMaterials.NETHERITE, Type.HELMET, new Properties().durability(600))
                     : (
                        weapon
                           ? CharacterRelics.fusion(sourceId)
                           : new Item(new Properties().stacksTo(64))
                     ))
            );
         ITEMS.put(sourceId, item);
      }
   }
}
