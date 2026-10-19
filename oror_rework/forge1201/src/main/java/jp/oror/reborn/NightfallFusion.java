package jp.oror.reborn;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.UUID;
import net.minecraft.ChatFormatting;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.network.chat.Style;
import net.minecraft.resources.ResourceKey;
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
import net.minecraftforge.fml.ModList;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.event.entity.living.LivingHurtEvent;
import net.minecraftforge.event.entity.player.PlayerEvent.Clone;
import net.minecraftforge.event.TickEvent.PlayerTickEvent;

public final class NightfallFusion {
   public static final JsonObject SOURCE = load();
   public static final Map<String, JsonObject> QUESTS = new LinkedHashMap<>();
   private static final Map<String, Boolean> AVAILABLE = new HashMap<>();

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
         if (BuiltInRegistries.ENTITY_TYPE.containsKey(new ResourceLocation("cataclysm", path))) {
            return "cataclysm:" + path;
         }
      }

      return source;
   }

   private static int required(JsonObject task) {
      return task.has("count") ? Math.max(1, task.get("count").getAsInt()) : (task.has("value") ? Math.max(1, task.get("value").getAsInt()) : 1);
   }

   /** Iron's Spells' container API, looked up once; null when it is missing or has changed. */
   private static Method[] spellApi;
   private static boolean spellApiLooked;

   private static Method[] spellApi() {
      if (!spellApiLooked) {
         spellApiLooked = true;
         try {
            Class<?> api = Class.forName("io.redspace.ironsspellbooks.api.spells.ISpellContainer");
            Class<?> data = Class.forName("io.redspace.ironsspellbooks.api.spells.SpellData");
            spellApi = new Method[]{
               api.getMethod("get", ItemStack.class),
               api.getMethod("getSpellAtIndex", int.class),
               data.getMethod("getSpell"),
               data.getMethod("getLevel"),
               Class.forName("io.redspace.ironsspellbooks.api.spells.AbstractSpell").getMethod("getSpellId"),
               Class.forName("io.redspace.ironsspellbooks.api.registry.SpellRegistry").getMethod("getSpell", String.class)
            };
         } catch (LinkageError | ReflectiveOperationException | RuntimeException var3) {
            spellApi = null;
         }
      }

      return spellApi;
   }

   /** Whether the scroll holds the spells at the levels asked; null when Iron's Spells cannot be asked. */
   private static Boolean scroll(ItemStack stack, JsonObject expected) {
      Method[] m = spellApi();
      if (m == null) {
         return null;
      } else {
         try {
            JsonArray entries = expected.getAsJsonObject("tag").getAsJsonObject("irons_spellbooks:spell_container").getAsJsonArray("data");
            Object container = m[0].invoke(null, stack);

            for (JsonElement entry : entries) {
               JsonObject e = entry.getAsJsonObject();
               Object actual = m[1].invoke(container, e.has("index") ? e.get("index").getAsInt() : 0);
               String key = (String)m[4].invoke(m[2].invoke(actual));
               int level = (Integer)m[3].invoke(actual);
               if (!key.equals(e.get("id").getAsString()) || level < e.get("level").getAsInt()) {
                  return false;
               }
            }

            return true;
         } catch (ReflectiveOperationException | RuntimeException var10) {
            return false;
         }
      }
   }

   /** The ids a task's 1.20 NBT names: the spell of a scroll, the skill of a skill book, a book's enchantments. */
   static List<String> needles(JsonElement item) {
      List<String> out = new ArrayList<>();
      if (item != null && item.isJsonObject() && item.getAsJsonObject().has("tag")) {
         collect(item.getAsJsonObject().get("tag"), out);
      }

      return out;
   }

   private static void collect(JsonElement e, List<String> out) {
      if (e.isJsonObject()) {
         for (Entry<String, JsonElement> x : e.getAsJsonObject().entrySet()) {
            collect(x.getValue(), out);
         }
      } else if (e.isJsonArray()) {
         for (JsonElement x : e.getAsJsonArray()) {
            collect(x, out);
         }
      } else if (e.isJsonPrimitive() && e.getAsJsonPrimitive().isString() && ResourceLocation.tryParse(e.getAsString()) != null && e.getAsString().indexOf(58) > 0) {
         out.add(e.getAsString());
      }
   }

   /** Stacks saved as text during one pass over the quests (same player, same tick): each is encoded once. */
   private static final Map<ItemStack, String> ENCODED = new IdentityHashMap<>();
   private static long encodedTick = Long.MIN_VALUE;
   private static UUID encodedFor;

   /**
    * v0.17.18: a skill book or an enchanted book has no spell container, so the old check refused every one of them
    * and those quests could never be finished. A scroll is still checked through Iron's Spells (spell and level); the
    * others by the ids in the saved stack, where the 1.21 data components keep what 1.20 held in NBT. An id is looked
    * for with its quotes, so "heal" is not found inside "healing_circle".
    */
   private static boolean matches(Player p, ItemStack stack, JsonObject expected, List<String> needles) {
      if (needles.isEmpty()) {
         return true;
      } else {
         if (expected.has("tag") && expected.getAsJsonObject("tag").has("irons_spellbooks:spell_container")) {
            Boolean spell = scroll(stack, expected);
            if (spell != null) {
               return spell;
            }
         }

         long now = p.level().getGameTime();
         if (now != encodedTick || !p.getUUID().equals(encodedFor)) {
            ENCODED.clear();
            encodedTick = now;
            encodedFor = p.getUUID();
         }

         String saved = ENCODED.get(stack);
         if (saved == null) {
            try {
               saved = stack.save(p.level().registryAccess()).toString();
            } catch (RuntimeException var8) {
               saved = "";
            }

            ENCODED.put(stack, saved);
         }

         for (String needle : needles) {
            if (!saved.contains("\"" + needle + "\"")) {
               return false;
            }
         }

         return true;
      }
   }

   public static boolean task(Player p, JsonObject task) {
      String type = task.get("type").getAsString();
      switch (type) {
         case "item":
            Item item = resolveItem(task.get("item"));
            if (item == Items.AIR) {
               // v0.17.18: no longer done for free (it paid the three 100-level armour quests after one kill);
               // available() hides such a quest and lets the quests after it through instead
               return false;
            } else {
               int count = 0;
               List<String> needles = needles(task.get("item"));

               for (int slot = 0; slot < p.getInventory().getContainerSize(); slot++) {
                  ItemStack stack = p.getInventory().getItem(slot);
                  if (stack.is(item) && (needles.isEmpty() || matches(p, stack, task.getAsJsonObject("item"), needles))) {
                     count += stack.getCount();
                  }
               }

               return count >= required(task);
            }
         case "kill":
            return data(p).getCompound("Kills").getInt(resolveEntity(task.get("entity").getAsString())) >= required(task);
         case "dimension":
            // v0.17.18: a visit counts (tick() remembers it), and a dimension this pack does not have is skipped
            String dimension = task.get("dimension").getAsString();
            return data(p).getCompound("Visited").getBoolean(dimension) || !dimensionExists(p, dimension);
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

               AdvancementHolder advancement = player.server.getAdvancements().get(new ResourceLocation(key));
               return advancement != null && player.getAdvancements().getOrStartProgress(advancement).isDone();
            }
         default:
            return false;
      }
   }

   private static boolean dimensionExists(Player p, String dimension) {
      if (p.level().getServer() == null) {
         return true;
      } else {
         for (Object key : p.level().getServer().levelKeys()) {
            if (((ResourceKey<?>)key).location().toString().equals(dimension)) {
               return true;
            }
         }

         return false;
      }
   }

   /**
    * v0.17.18: whether this pack can do the quest at all. Its items, the bosses it asks to defeat and the spells,
    * skills and enchantments its items name must all exist; a quest for a NightfallCraft mod the pack does not ship
    * is left out of the list. The registries are fixed once the game runs, so the answer is kept.
    */
   public static boolean available(JsonObject quest) {
      String id = quest.get("id").getAsString();
      Boolean known = AVAILABLE.get(id);
      if (known != null) {
         return known;
      } else {
         // FTB Quests: optional tasks are not needed, unless nothing else is asked; then any one of them will do
         boolean ok = true;
         boolean asked = false;
         boolean any = false;

         for (JsonElement element : quest.getAsJsonArray("tasks")) {
            JsonObject task = element.getAsJsonObject();
            boolean possible = possible(task);
            if (optional(task)) {
               any |= possible;
            } else {
               ok &= possible;
               asked |= !task.get("type").getAsString().equals("dimension");
            }
         }

         ok &= asked || any;
         AVAILABLE.put(id, ok);
         return ok;
      }
   }

   private static boolean optional(JsonObject task) {
      return task.has("optional_task") && task.get("optional_task").getAsBoolean();
   }

   /** Whether this pack has what a task asks for (a dimension is checked when the quest is done, see task()). */
   private static boolean possible(JsonObject task) {
      String type = task.get("type").getAsString();
      if (type.equals("item")) {
         if (resolveItem(task.get("item")) == Items.AIR) {
            return false;
         } else {
            boolean spells = task.get("item").isJsonObject()
               && task.getAsJsonObject("item").has("tag")
               && task.getAsJsonObject("item").getAsJsonObject("tag").has("irons_spellbooks:spell_container");
            for (String needle : needles(task.get("item"))) {
               String mod = needle.substring(0, needle.indexOf(58));
               if (!mod.equals("minecraft") && !ModList.get().isLoaded(mod) || spells && !spellExists(needle)) {
                  return false;
               }
            }

            return true;
         }
      } else if (type.equals("kill")) {
         ResourceLocation entity = ResourceLocation.tryParse(resolveEntity(task.get("entity").getAsString()));
         return entity != null && BuiltInRegistries.ENTITY_TYPE.containsKey(entity);
      } else {
         return true;
      }
   }

   /** Whether Iron's Spells knows the spell (a scroll quest for a spell it dropped could never be done). */
   private static boolean spellExists(String id) {
      Method[] m = spellApi();
      if (m == null) {
         return true;
      } else {
         try {
            Object spell = m[5].invoke(null, id);
            return spell != null && id.equals(m[4].invoke(spell));
         } catch (ReflectiveOperationException | RuntimeException var3) {
            return true;
         }
      }
   }

   /** A finished dependency, or one this pack cannot offer whose own dependencies are met. */
   private static boolean satisfied(Player p, String id, int depth) {
      if (completed(p, id)) {
         return true;
      } else {
         JsonObject q = QUESTS.get(id);
         return q != null && depth < 16 && !available(q) && dependencies(p, q, depth + 1);
      }
   }

   private static boolean dependencies(Player p, JsonObject quest, int depth) {
      if (quest.has("dependencies")) {
         for (JsonElement dependency : quest.getAsJsonArray("dependencies")) {
            if (!satisfied(p, dependency.getAsString(), depth)) {
               return false;
            }
         }
      }

      return true;
   }

   /** Every dependency met (or passed through) and the quest itself possible: it can be accepted or worked on. */
   public static boolean open(Player p, JsonObject quest) {
      return available(quest) && dependencies(p, quest, 0);
   }

   public static boolean ready(Player p, JsonObject quest) {
      if (!open(p, quest)) {
         return false;
      } else {
         // the required tasks; a dimension this pack lacks is not asked, and when nothing is left any optional one
         boolean asked = false;
         boolean any = false;

         for (JsonElement element : quest.getAsJsonArray("tasks")) {
            JsonObject task = element.getAsJsonObject();
            if (optional(task)) {
               any = any || possible(task) && task(p, task);
            } else if (!task.get("type").getAsString().equals("dimension") || dimensionExists(p, task.get("dimension").getAsString())) {
               if (!task(p, task)) {
                  return false;
               }

               asked = true;
            }
         }

         return asked || any;
      }
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
         // v0.17.18: a reward item no mod of this pack provides (the Epic Skills ability stones of the boss quests,
         // the Tudigong spell) is paid in experience like the other unported ones; it used to block the claim forever
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
                     break;
                  default:
                     break;
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
         // v0.17.18: this chapter has no file name in the source, so it showed up under its raw id
         case "ji_chu_wu_qi", "404D35C74CC7C412" -> "基礎武器";
         case "wu_qi" -> "武器";
         case "zhuang_bei" -> "装備";
         case "zhong_yao_wu_pin" -> "重要アイテム";
         case "cui_ling" -> "淬霊";
         case "lun_hui" -> "輪廻";
         case "shen_mo" -> "神魔";
         default -> name;
      };
   }

   private static boolean accepted(Player p, JsonObject quest) {
      for (JsonElement task : quest.getAsJsonArray("tasks")) {
         JsonObject t = task.getAsJsonObject();
         if (t.get("type").getAsString().equals("checkmark") && !data(p).getCompound("Accepted").getBoolean(t.get("id").getAsString())) {
            return false;
         }
      }

      return true;
   }

   /** v0.17.18: what a quest asks for, in words; the list used to show only chapter names and hex ids. */
   public static MutableComponent label(JsonObject quest) {
      MutableComponent out = Component.empty();
      boolean anyOf = quest.getAsJsonArray("tasks").size() > 1;
      for (JsonElement element : quest.getAsJsonArray("tasks")) {
         anyOf &= optional(element.getAsJsonObject());
      }

      if (anyOf) {
         out.append("いずれか：");
      }

      int shown = 0;
      JsonArray tasks = quest.getAsJsonArray("tasks");

      for (JsonElement element : tasks) {
         if (shown == 3) {
            out.append("ほか" + (tasks.size() - 3) + "件");
            break;
         }

         if (shown > 0) {
            out.append("・");
         }

         JsonObject task = element.getAsJsonObject();
         String type = task.get("type").getAsString();
         switch (type) {
            case "item":
               out.append(new ItemStack(resolveItem(task.get("item"))).getHoverName());
               JsonObject tag = task.get("item").isJsonObject() && task.getAsJsonObject("item").has("tag") ? task.getAsJsonObject("item").getAsJsonObject("tag") : new JsonObject();
               String prefix = tag.has("irons_spellbooks:spell_container") ? "spell." : (tag.has("skill") ? "skill." : (tag.has("StoredEnchantments") ? "enchantment." : null));
               if (prefix != null) {
                  for (String needle : needles(task.get("item"))) {
                     String path = needle.substring(needle.indexOf(58) + 1);
                     out.append("（").append(Component.translatableWithFallback(prefix + needle.replace(':', '.'), path)).append("）");
                  }
               }
               break;
            case "kill":
               ResourceLocation entity = ResourceLocation.tryParse(resolveEntity(task.get("entity").getAsString()));
               out.append(entity != null && BuiltInRegistries.ENTITY_TYPE.containsKey(entity) ? BuiltInRegistries.ENTITY_TYPE.get(entity).getDescription() : Component.literal(task.get("entity").getAsString()));
               out.append("を討伐");
               break;
            case "dimension":
               out.append("次元「" + task.get("dimension").getAsString() + "」へ行く");
               break;
            case "checkmark":
               out.append("物語を読む");
               break;
            case "advancement":
               out.append(task.get("advancement").getAsString().contains("epic") ? "魔物を10体倒す" : "魔物を1体倒す");
               break;
            default:
               out.append(type);
         }

         shown++;
      }

      return out;
   }

   private static void line(Player p, JsonObject quest, String command) {
      p.sendSystemMessage(
         Component.literal(chapter(quest.get("chapter").getAsString()) + "：")
            .append(label(quest))
            .append(
               Component.literal("　" + command)
                  .setStyle(Style.EMPTY.withColor(ChatFormatting.AQUA).withClickEvent(new ClickEvent(ClickEvent.Action.RUN_COMMAND, command)))
            )
      );
   }

   public static void list(Player p) {
      int done = 0;
      int total = 0;
      int shown = 0;
      int working = 0;
      List<JsonObject> next = new ArrayList<>();

      for (Entry<String, JsonObject> e : QUESTS.entrySet()) {
         JsonObject q = e.getValue();
         if (!available(q)) {
            continue;
         }

         total++;
         if (completed(p, e.getKey())) {
            done++;
         } else if (ready(p, q)) {
            if (shown < 12) {
               line(p, q, "/oror quest claim " + e.getKey());
            }

            shown++;
         } else if (open(p, q)) {
            if (!accepted(p, q)) {
               line(p, q, "/oror quest accept " + e.getKey());
            } else {
               working++;
               if (next.size() < 5) {
                  next.add(q);
               }
            }
         }
      }

      for (JsonObject q : next) {
         p.sendSystemMessage(Component.literal("次の目標（" + chapter(q.get("chapter").getAsString()) + "）：").append(label(q)));
      }

      p.sendSystemMessage(
         Component.literal(
            "Nightfall 8章 / 任務 " + done + "/" + total + "（このパックで遂行できるもの。全" + QUESTS.size() + "件）/ 受け取れる報酬 " + shown + " / 進行中 " + working + " / 難易度 "
               + (data(p).getString("Difficulty").isEmpty() ? "normal" : data(p).getString("Difficulty"))
         )
      );
   }

   public static boolean temper(Player p) {
      ItemStack held = p.getMainHandItem();
      // relic bows, shields and catalysts temper like swords (they stopped being SwordItems in v0.17.3)
      if (!held.isEmpty()
         && (held.getItem() instanceof SwordItem || held.getItem() instanceof CharacterRelics.Wielded w && w.wield().kind != null)
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

   public static void damage(LivingHurtEvent e) {
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

   public static void tick(PlayerTickEvent e) {
        if (e.phase != net.minecraftforge.event.TickEvent.Phase.END) {
            return;
        }
      Player p = e.player;
      if (!p.level().isClientSide && p.tickCount % 20 == 0) {
         // v0.17.18: a dimension counts once visited (looked at every second, so a short stay is not missed)
         CompoundTag visited = data(p).getCompound("Visited");
         if (!visited.getBoolean(p.level().dimension().location().toString())) {
            visited.putBoolean(p.level().dimension().location().toString(), true);
            data(p).put("Visited", visited);
         }

         long last = data(p).getLong("Notice");
         if (p.tickCount % 200 == 0 && p.level().getGameTime() - last >= 2400L) {
            int ready = 0;

            for (JsonObject q : QUESTS.values()) {
               if (!completed(p, q.get("id").getAsString()) && ready(p, q)) {
                  ready++;
               }
            }

            if (ready > 0) {
               data(p).putLong("Notice", p.level().getGameTime());
               p.displayClientMessage(Component.literal("Nightfall：受け取れる任務報酬 " + ready + "件 /oror quest list"), true);
            }
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
