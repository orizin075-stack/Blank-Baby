package jp.oror.reborn;

import com.google.gson.JsonObject;
import java.util.Map;
import java.util.Map.Entry;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.ItemLike;
import net.neoforged.fml.ModList;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;
import net.neoforged.neoforge.registries.DeferredItem;

@GameTestHolder("oror_supreme_bosses")
@PrefixGameTestTemplate(false)
public final class FusionGameTests {
   @GameTest(
      template = "empty",
      setupTicks = 40L,
      timeoutTicks = 120,
      batch = "fusion"
   )
   public static void latest_nightfall_chapter_graph_and_counterparts_are_registered(GameTestHelper h) {
      h.assertTrue(
         NightfallFusion.SOURCE.get("source_version").getAsString().equals("2.2.9.7") && NightfallFusion.QUESTS.size() == 232,
         "Actual latest source chapter graph loaded"
      );

      // v0.17.4: the 70 stand-ins are gone; items of NightfallCraft mods missing from the pack count as unported
      h.assertTrue(FusionItems.ITEMS.isEmpty(), "No stand-in items are registered");
      h.assertTrue(
         FusionItems.unported("efn:hf_blade") && FusionItems.resolve("efn:hf_blade") == Items.AIR && !FusionItems.unported("minecraft:diamond"),
         "Unported NightfallCraft items are recognised"
      );
      h.succeed();
   }

   @GameTest(
      template = "empty",
      setupTicks = 40L,
      timeoutTicks = 120,
      batch = "fusion"
   )
   public static void quest_accept_and_claim_pay_native_experience_once(GameTestHelper h) {
      Player p = h.makeMockPlayer(GameType.SURVIVAL);
      Entry<String, JsonObject> entry = NightfallFusion.QUESTS
         .entrySet()
         .stream()
         .filter(
            e -> e.getValue().get("chapter").getAsString().equals("xu_zhang")
                  && e.getValue().getAsJsonArray("tasks").get(0).getAsJsonObject().get("type").getAsString().equals("checkmark")
                  && !e.getValue().has("dependencies")
         )
         .findFirst()
         .orElseThrow();
      h.assertTrue(!NightfallFusion.ready(p, entry.getValue()), "Checkmark is not silently completed");
      int before = p.totalExperience;
      h.assertTrue(
         NightfallFusion.accept(p, entry.getKey()) && NightfallFusion.claim(p, entry.getKey()) && p.totalExperience > before,
         "Native experience was granted after explicit acceptance"
      );
      int after = p.totalExperience;
      h.assertTrue(!NightfallFusion.claim(p, entry.getKey()) && p.totalExperience == after, "Reconnect/repeat claim cannot duplicate reward");
      h.succeed();
   }

   @GameTest(
      template = "empty",
      setupTicks = 40L,
      timeoutTicks = 120,
      batch = "fusion"
   )
   public static void quests_for_missing_mods_pay_nothing_and_let_the_next_ones_through(GameTestHelper h) {
      // v0.17.18: the three Fantasy Armor helmet sets paid 100 levels each after a single kill
      Player p = h.makeMockPlayer(GameType.SURVIVAL);
      NightfallFusion.data(p).putInt("Defeats", 50);
      int levels = p.totalExperience;
      h.assertTrue(
         ModList.get().isLoaded("fantasy_armor")
            || !NightfallFusion.available(NightfallFusion.QUESTS.get("7B9624C198F07020"))
               && !NightfallFusion.claim(p, "7B9624C198F07020")
               && p.totalExperience == levels,
         "A quest for a mod this pack lacks pays nothing"
      );
      // Tidal Claws (Cataclysm) waits behind the Nightfall claw of a missing mod: that one is passed through
      h.assertTrue(NightfallFusion.claim(p, "2F9F109962C8ADF4"), "The weapon chapter opens after a defeat");
      h.assertTrue(
         !ModList.get().isLoaded("cataclysm") || ModList.get().isLoaded("efn") || NightfallFusion.open(p, NightfallFusion.QUESTS.get("12C6899DBC971D90")),
         "A quest after an unported one is open"
      );
      h.succeed();
   }

   @GameTest(
      template = "empty",
      setupTicks = 40L,
      timeoutTicks = 120,
      batch = "fusion"
   )
   public static void tempering_requires_material_and_preserves_actual_item_components(GameTestHelper h) {
      Player p = h.makeMockPlayer(GameType.SURVIVAL);
      p.setItemInHand(InteractionHand.MAIN_HAND, Items.NETHERITE_SWORD.getDefaultInstance());
      h.assertTrue(!NightfallFusion.temper(p), "No free tempering without resource");
      p.getInventory().add(new ItemStack((ItemLike)AdventureContent.MANA.get(), 4));
      h.assertTrue(
         NightfallFusion.temper(p)
            && ((CustomData)p.getMainHandItem().getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY)).copyTag().getInt("OrorTemper") == 1,
         "Actual item components store upgrade"
      );
      h.assertTrue(
         p.getInventory().items.stream().noneMatch(s -> s.is((Item)AdventureContent.MANA.get())) && !NightfallFusion.temper(p),
         "Four real materials consumed, next level needs eight"
      );
      h.succeed();
   }

   @GameTest(
      template = "empty",
      setupTicks = 40L,
      timeoutTicks = 120,
      batch = "fusion"
   )
   public static void cataclysm_humanoid_quests_resolve_loaded_native_bosses(GameTestHelper h) {
      for (Entry<String, String> pair : Map.of(
            "tcr_bosses:netherite_humanoid",
            "cataclysm:netherite_monstrosity",
            "tcr_bosses:leviathan_humanoid",
            "cataclysm:the_leviathan",
            "tcr_bosses:harbinger_humanoid",
            "cataclysm:the_harbinger"
         )
         .entrySet()) {
         String actual = NightfallFusion.resolveEntity(pair.getKey());
         h.assertTrue(
            actual.equals(pair.getValue()) && BuiltInRegistries.ENTITY_TYPE.containsKey(ResourceLocation.parse(actual)),
            "Original humanoid quest resolves to an installed native Cataclysm boss: " + pair.getKey()
         );
      }

      h.succeed();
   }
}
