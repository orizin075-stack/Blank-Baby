package jp.oror.reborn;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Map.Entry;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.component.CustomData;
import net.neoforged.neoforge.event.entity.living.LivingDeathEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent.Clone;
import net.neoforged.neoforge.event.tick.PlayerTickEvent.Post;

public final class NightfallFusion {
   public static final JsonObject SOURCE = load();
   public static final Map<String, JsonObject> QUESTS = new LinkedHashMap<>();

   private static JsonObject load() {
      try {
         JsonObject var1;
         try (InputStream stream = NightfallFusion.class.getResourceAsStream("/assets/oror_supreme_bosses/nightfall_quests.json")) {
            if (stream == null) {
               throw new IllegalStateException("Missing Nightfall chapters");
            }

            var1 = JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8)).getAsJsonObject();
         }

         return var1;
      } catch (IOException var5) {
         throw new ExceptionInInitializerError(var5);
      }
   }

   public static CompoundTag data(Player p) {
      CompoundTag root = p.getPersistentData();
      if (!root.contains("OrorNightfall", 10)) {
         root.put("OrorNightfall", new CompoundTag());
      }

      return root.getCompound("OrorNightfall");
   }

   public static boolean completed(Player p, String id) {
      return data(p).getCompound("Completed").getBoolean(id);
   }

   private static String id(JsonElement value) {
      if (value == null) {
         return "";
      } else {
         return value.isJsonPrimitive() ? value.getAsString() : (value.getAsJsonObject().has("id") ? value.getAsJsonObject().get("id").getAsString() : "");
      }
   }

   public static Item resolveItem(JsonElement source) {
      String name = id(source);
      ResourceLocation key = ResourceLocation.tryParse(name);
      if (key == null) {
         return Items.AIR;
      } else {
         Item existing = (Item)BuiltInRegistries.ITEM.get(key);
         return existing != Items.AIR ? existing : FusionItems.resolve(name);
      }
   }

   public static String resolveEntity(String source) {
      if (source.startsWith("tcr_bosses:")) {
         String path = source.substring(source.indexOf(58) + 1).replace("_humanoid", "");

         path = switch (path) {
            case "netherite" -> "netherite_monstrosity";
            case "leviathan" -> "the_leviathan";
            case "harbinger" -> "the_harbinger";
            default -> path;
         };
         if (BuiltInRegistries.ENTITY_TYPE.containsKey(ResourceLocation.fromNamespaceAndPath("cataclysm", path))) {
            return "cataclysm:" + path;
         }
      }

      return source;
   }

   private static int required(JsonObject task) {
      return task.has("count") ? Math.max(1, task.get("count").getAsInt()) : (task.has("value") ? Math.max(1, task.get("value").getAsInt()) : 1);
   }

   private static boolean scroll(ItemStack stack, JsonObject expected) {
      if (!expected.has("tag")) {
         return true;
      } else {
         JsonObject tag = expected.getAsJsonObject("tag");
         if (!tag.has("irons_spellbooks:spell_container")) {
            return false;
         } else {
            try {
               JsonArray entries = tag.getAsJsonObject("irons_spellbooks:spell_container").getAsJsonArray("data");
               Class<?> api = Class.forName("io.redspace.ironsspellbooks.api.spells.ISpellContainer");
               Object container = api.getMethod("get", ItemStack.class).invoke(null, stack);
               Class<?> spells = Class.forName("io.redspace.ironsspellbooks.api.spells.SpellData");

               for (JsonElement entry : entries) {
                  JsonObject e = entry.getAsJsonObject();
                  Object actual = api.getMethod("getSpellAtIndex", int.class).invoke(container, e.has("index") ? e.get("index").getAsInt() : 0);
                  Object spell = spells.getMethod("getSpell").invoke(actual);
                  String key = (String)Class.forName("io.redspace.ironsspellbooks.api.spells.AbstractSpell").getMethod("getSpellId").invoke(spell);
                  int level = (Integer)spells.getMethod("getLevel").invoke(actual);
                  if (!key.equals(e.get("id").getAsString()) || level < e.get("level").getAsInt()) {
                     return false;
                  }
               }

               return true;
            } catch (LinkageError | ReflectiveOperationException var14) {
               return false;
            }
         }
      }
   }

   public static boolean task(Player p, JsonObject task) {
      String type = task.get("type").getAsString();
      switch (type) {
         case "item":
            Item item = resolveItem(task.get("item"));
            if (item == Items.AIR) {
               // an item from a NightfallCraft mod this pack does not ship cannot be gathered: the task counts as done
               return FusionItems.unported(id(task.get("item")));
            } else {
               int count = 0;
               boolean strict = task.has("match_nbt") && task.get("match_nbt").getAsBoolean();

               for (int slot = 0; slot < p.getInventory().getContainerSize(); slot++) {
                  ItemStack stack = p.getInventory().getItem(slot);
                  if (stack.is(item) && (!strict || task.get("item").isJsonObject() && scroll(stack, task.getAsJsonObject("item")))) {
                     count += stack.getCount();
                  }
               }

               return count >= required(task);
            }
         case "kill":
            return data(p).getCompound("Kills").getInt(resolveEntity(task.get("entity").getAsString())) >= required(task);
         case "dimension":
            return p.level().dimension().location().toString().equals(task.get("dimension").getAsString());
         case "checkmark":
            return data(p).getCompound("Accepted").getBoolean(task.get("id").getAsString());
         case "advancement":
            String key = task.get("advancement").getAsString();
            if (key.startsWith("tcrcore:unlock_")) {
               return data(p).getInt("Defeats") >= (key.contains("epic") ? 10 : 1);
            } else {
               if (!(p instanceof ServerPlayer player)) {
                  return false;
               }

               AdvancementHolder advancement = player.server.getAdvancements().get(ResourceLocation.parse(key));
               return advancement != null && player.getAdvancements().getOrStartProgress(advancement).isDone();
            }
         default:
            return false;
      }
   }

   public static boolean ready(Player p, JsonObject quest) {
      if (quest.has("dependencies")) {
         for (JsonElement dependency : quest.getAsJsonArray("dependencies")) {
            if (!completed(p, dependency.getAsString())) {
               return false;
            }
         }
      }

      for (JsonElement task : quest.getAsJsonArray("tasks")) {
         if (!task(p, task.getAsJsonObject())) {
            return false;
         }
      }

      return true;
   }

   public static boolean accept(Player p, String id) {
      JsonObject q = QUESTS.get(id);
      if (q == null) {
         return false;
      } else {
         CompoundTag accepted = data(p).getCompound("Accepted");

         for (JsonElement task : q.getAsJsonArray("tasks")) {
            JsonObject t = task.getAsJsonObject();
            if (t.get("type").getAsString().equals("checkmark")) {
               accepted.putBoolean(t.get("id").getAsString(), true);
            }
         }

         data(p).put("Accepted", accepted);
         return true;
      }
   }

   public static boolean claim(Player p, String id) {
      JsonObject q = QUESTS.get(id);
      if (q != null && !completed(p, id) && ready(p, q)) {
         if (q.has("rewards")) {
            for (JsonElement reward : q.getAsJsonArray("rewards")) {
               JsonObject r = reward.getAsJsonObject();
               if (r.get("type").getAsString().equals("item") && resolveItem(r.get("item")) == Items.AIR && !FusionItems.unported(id(r.get("item")))) {
                  p.sendSystemMessage(Component.literal("この報酬は現在利用できません。任務の達成と報酬受領権は保持します：" + id(r.get("item"))));
                  return false;
               }
            }
         }

         CompoundTag n = data(p);
         CompoundTag finished = n.getCompound("Completed");
         finished.putBoolean(id, true);
         n.put("Completed", finished);
         if (q.has("rewards")) {
            for (JsonElement rewardx : q.getAsJsonArray("rewards")) {
               JsonObject r = rewardx.getAsJsonObject();
               String var8 = r.get("type").getAsString();
               switch (var8) {
                  case "xp":
                     p.giveExperiencePoints(r.get("xp").getAsInt());
                     break;
                  case "xp_levels":
                     p.giveExperienceLevels(r.get("xp_levels").getAsInt());
                     break;
                  case "item":
                     Item item = resolveItem(r.get("item"));
                     if (item == Items.AIR) {
                        // unported NightfallCraft reward: paid in experience instead
                        int xp = 30 * Math.clamp(r.has("count") ? r.get("count").getAsInt() : 1, 1, 64);
                        p.giveExperiencePoints(xp);
                        p.sendSystemMessage(Component.literal("未移植の報酬（" + id(r.get("item")) + "）は経験値 " + xp + " に置き換えました"));
                     } else {
                        int count = r.has("count")
                           ? r.get("count").getAsInt()
                           : (r.get("item").isJsonObject() && r.getAsJsonObject("item").has("Count") ? r.getAsJsonObject("item").get("Count").getAsInt() : 1);
                        int left = Math.clamp((long)count, 1, 512);

                        while (left > 0) {
                           int part = Math.min(left, item.getDefaultMaxStackSize());
                           ItemStack stack = new ItemStack(item, part);
                           if (!p.getInventory().add(stack) && !stack.isEmpty()) {
                              p.drop(stack, false);
                           }

                           left -= part;
                        }
                     }
                     break;
                  case "choice":
                     p.sendSystemMessage(Component.literal("難易度選択：/oror difficulty easy | normal | hard"));
               }
            }
         }

         p.sendSystemMessage(Component.literal("Nightfall任務の報酬を受領：" + id));
         return true;
      } else {
         return false;
      }
   }

   public static String chapter(String name) {
      return switch (name) {
         case "xu_zhang" -> "序章";
         case "ji_chu_wu_qi" -> "基礎武器";
         case "wu_qi" -> "武器";
         case "zhuang_bei" -> "装備";
         case "zhong_yao_wu_pin" -> "重要アイテム";
         case "cui_ling" -> "淬霊";
         case "lun_hui" -> "輪廻";
         case "shen_mo" -> "神魔";
         default -> name;
      };
   }

   public static void list(Player p) {
      int done = 0;
      int shown = 0;

      for (Entry<String, JsonObject> e : QUESTS.entrySet()) {
         if (completed(p, e.getKey())) {
            done++;
         } else if (shown < 12 && ready(p, e.getValue())) {
            p.sendSystemMessage(Component.literal(chapter(e.getValue().get("chapter").getAsString()) + "：/oror quest claim " + e.getKey()));
            shown++;
         }
      }

      p.sendSystemMessage(
         Component.literal("Nightfall 8章 / 任務 " + done + "/" + QUESTS.size() + " / 未取得の報酬 " + shown + " / 難易度 " + data(p).getString("Difficulty"))
      );
   }

   public static boolean temper(Player p) {
      ItemStack held = p.getMainHandItem();
      if (!held.isEmpty()
         && held.getItem() instanceof SwordItem
         && ((CustomData)held.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY)).copyTag().getInt("OrorTemper") < 5) {
         Inventory inv = p.getInventory();
         int material = 0;

         for (ItemStack s : inv.items) {
            if (s.is((Item)AdventureContent.MANA.get())) {
               material += s.getCount();
            }
         }

         int rank = ((CustomData)held.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY)).copyTag().getInt("OrorTemper");
         int cost = 4 * (rank + 1);
         if (material < cost) {
            return false;
         } else {
            for (ItemStack sx : inv.items) {
               if (cost > 0 && sx.is((Item)AdventureContent.MANA.get())) {
                  int take = Math.min(cost, sx.getCount());
                  sx.shrink(take);
                  cost -= take;
               }
            }

            CustomData.update(DataComponents.CUSTOM_DATA, held, n -> ((CompoundTag)n).putInt("OrorTemper", rank + 1));
            return true;
         }
      } else {
         return false;
      }
   }

   public static void kill(LivingDeathEvent e) {
      if (e.getSource().getEntity() instanceof Player p && e.getEntity() != p) {
         CompoundTag n = data(p);
         CompoundTag kills = n.getCompound("Kills");
         String key = BuiltInRegistries.ENTITY_TYPE.getKey(e.getEntity().getType()).toString();
         kills.putInt(key, Math.min(1000000, kills.getInt(key) + 1));
         n.put("Kills", kills);
         n.putInt("Defeats", Math.min(1000000, n.getInt("Defeats") + 1));
         return;
      }
   }

   public static void clone(Clone e) {
      if (e.getOriginal().getPersistentData().contains("OrorNightfall", 10)) {
         e.getEntity().getPersistentData().put("OrorNightfall", data(e.getOriginal()).copy());
      }
   }

   public static void damage(LivingIncomingDamageEvent e) {
      if (e.getSource().getEntity() instanceof Player p) {
         int temper = ((CustomData)p.getMainHandItem().getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY)).copyTag().getInt("OrorTemper");
         if (temper > 0) {
            e.setAmount(e.getAmount() * (1.0F + (float)Math.min(5, temper) * 0.16F));
         }
      }

      if (e.getEntity() instanceof Player px && e.getSource().getEntity() instanceof Mob) {
         String difficulty = data(px).getString("Difficulty");
         if (difficulty.equals("easy")) {
            e.setAmount(e.getAmount() * 0.75F);
         }

         if (difficulty.equals("hard")) {
            e.setAmount(e.getAmount() * 1.25F);
         }
      }
   }

   public static void tick(Post e) {
      if (!e.getEntity().level().isClientSide && e.getEntity().tickCount % 200 == 0) {
         Player p = e.getEntity();
         long last = data(p).getLong("Notice");
         int ready = 0;

         for (JsonObject q : QUESTS.values()) {
            if (!completed(p, q.get("id").getAsString()) && ready(p, q)) {
               ready++;
            }
         }

         if (ready > 0 && p.level().getGameTime() - last >= 2400L) {
            data(p).putLong("Notice", p.level().getGameTime());
            p.displayClientMessage(Component.literal("Nightfall：受け取れる任務報酬 " + ready + "件 /oror quest list"), true);
         }
      }
   }

   private NightfallFusion() {
   }

   static {
      for (JsonElement value : SOURCE.getAsJsonArray("quests")) {
         JsonObject q = value.getAsJsonObject();
         QUESTS.put(q.get("id").getAsString(), q);
      }
   }
}
