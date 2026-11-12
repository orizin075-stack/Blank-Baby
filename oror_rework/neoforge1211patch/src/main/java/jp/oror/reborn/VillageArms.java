package jp.oror.reborn;

import com.mojang.authlib.GameProfile;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Random;
import java.util.UUID;
import jp.oror.reborn.VillageProgress.Record;
import jp.oror.reborn.VillageWork.Survey;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.fml.ModList;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;

/**
 * The village's guns (v0.17.15, from the 052 base, decompiled into the source in 059e to change it): once the village can
 * afford them it sets up a gunsmith's table and makes Superb Warfare guns, each with three magazines of spare rounds,
 * and hands them out; the armed fire them (MobEquipmentUse) and keep them topped up with gunpowder.
 * (059e, the user: villagers and guards should really carry guns) it came so late it hardly came: ten people, a miner,
 * sixty-four metal and sixty-four emeralds in store, then one gun every two minutes to one strong villager only. Now:
 * six people, twenty-four metal and sixteen emeralds; a gun a minute for four iron, two gunpowder and three emeralds; and
 * the village's guards (Guard Villagers) are armed first, then its strongest villagers.
 */
public final class VillageArms {
   private static final String[][] TIERS = new String[][]{
      {"glock_17", "m_1911", "mp_443"},
      {"mp_5", "vector"},
      {"ak_47", "m_4", "hk_416", "sks", "qbz_95"},
      {"svd", "mk_14", "k_98", "mosin_nagant"},
      {"rpk", "m_60", "aa_12"}
   };
   private static boolean broken;

   private VillageArms() {
   }

   static boolean present() {
      return !broken && ModList.get().isLoaded("superbwarfare");
   }

   private static Item item(String ns, String id) {
      ResourceLocation rl = ResourceLocation.fromNamespaceAndPath(ns, id);
      return BuiltInRegistries.ITEM.containsKey(rl) ? (Item)BuiltInRegistries.ITEM.get(rl) : null;
   }

   static void review(ServerLevel sl, Survey s, Record r) {
      if (present()) {
         long now = sl.getGameTime();
         if (!r.guns) {
            int metal = s.stock("iron_ingot") + s.stock("gold_ingot") + s.stock("copper_ingot") + s.raw;
            if (s.population >= 6 && metal >= 24 && s.stock("emerald") >= 16) {
               r.guns = true;
               VillageProgress.get(sl).setDirty();
               VillageProgress.announce(sl, s.village, "鉱夫の資源とエメラルドが十分に集まり、銃の製造が解禁されました（Superb Warfare）", true);
            }
         } else if (r.gunTable == null || !table(sl, r.gunTable)) {
            r.gunTable = null;
            if (s.stock("iron_ingot") >= 6) {
               BlockPos at = placeTable(sl, s);
               if (at != null) {
                  VillageExpeditions.take(sl, s, "iron_ingot", 6);
                  r.gunTable = at;
                  VillageProgress.get(sl).setDirty();
                  VillageProgress.announce(sl, s.village, "村の中心近くに銃工房（改造台）を設けました", false);
               }
            }
         } else if (now >= s.nextGun) {
            s.nextGun = now + 1200L;
            if (s.stock("iron_ingot") >= 4 && s.stock("gunpowder") >= 2 && s.stock("emerald") >= 3) {
               if (armGuard(sl, s, r)) {
                  return;
               }
               Villager who = sl.getEntitiesOfClass(
                     Villager.class,
                     new AABB(s.village.center).inflate(64.0, 24.0, 64.0),
                     v -> v.isAlive()
                           && VillageAI.strong(v)
                           && VillageLedger.of(v) == s.village
                           && !armed(v)
                           && !v.getPersistentData().getBoolean("OrorWanderer")
                  )
                  .stream()
                  .max(Comparator.comparingInt(VillageExpeditions::power))
                  .orElse(null);
               if (who != null) {
                  int tier = Math.min(TIERS.length - 1, Math.max(0, r.stage - 2) + r.gunsMade % 2);
                  ItemStack gun = gun(sl, tier);
                  if (!gun.isEmpty()) {
                     VillageExpeditions.take(sl, s, "iron_ingot", 4);
                     VillageExpeditions.take(sl, s, "gunpowder", 2);
                     VillageExpeditions.take(sl, s, "emerald", 3);
                     ItemStack rest = who.getInventory().addItem(gun);
                     if (!rest.isEmpty()) {
                        VillageProgress.get(sl).deliver(r, List.of(rest), sl.registryAccess());
                     }

                     r.gunsMade++;
                     VillageProgress.get(sl).setDirty();
                     sl.sendParticles(
                        ParticleTypes.CRIT,
                        (double)r.gunTable.getX() + 0.5,
                        (double)r.gunTable.getY() + 1.2,
                        (double)r.gunTable.getZ() + 0.5,
                        12,
                        0.4,
                        0.2,
                        0.4,
                        0.1
                     );
                     RelicEffects.sound(sl, r.gunTable, SoundEvents.ANVIL_USE, 0.8F, 1.3F);
                     VillageProgress.announce(sl, s.village, "銃工房で「" + gun.getHoverName().getString() + "」を製作し、" + who.getName().getString() + "に持たせました", false);
                  }
               }
            }
         }
      }
   }

   /** (059e) A village guard (Guard Villagers) near the village without a gun is given the new one in his hand. */
   private static boolean armGuard(ServerLevel sl, Survey s, Record r) {
      net.minecraft.world.entity.Mob guard = sl.getEntitiesOfClass(
            net.minecraft.world.entity.Mob.class,
            new AABB(s.village.center).inflate(64.0, 24.0, 64.0),
            m -> m.isAlive()
                  && "guardvillagers".equals(BuiltInRegistries.ENTITY_TYPE.getKey(m.getType()).getNamespace())
                  && !MobEquipmentUse.kind(m.getMainHandItem()).equals("gun")
                  && !m.getPersistentData().contains("OrorHolsteredGun")
         )
         .stream()
         .min(Comparator.comparingDouble(m -> m.distanceToSqr(Vec3.atCenterOf(s.village.center))))
         .orElse(null);
      if (guard == null) {
         return false;
      }
      int tier = Math.min(TIERS.length - 1, Math.max(0, r.stage - 2) + r.gunsMade % 2);
      ItemStack gun = gun(sl, tier);
      if (gun.isEmpty()) {
         return false;
      }
      VillageExpeditions.take(sl, s, "iron_ingot", 4);
      VillageExpeditions.take(sl, s, "gunpowder", 2);
      VillageExpeditions.take(sl, s, "emerald", 3);
      guard.setItemSlot(net.minecraft.world.entity.EquipmentSlot.MAINHAND, gun);
      guard.setDropChance(net.minecraft.world.entity.EquipmentSlot.MAINHAND, 0.0F);
      r.gunsMade++;
      VillageProgress.get(sl).setDirty();
      if (r.gunTable != null) {
         sl.sendParticles(ParticleTypes.CRIT, r.gunTable.getX() + 0.5, r.gunTable.getY() + 1.2, r.gunTable.getZ() + 0.5, 12, 0.4, 0.2, 0.4, 0.1);
         RelicEffects.sound(sl, r.gunTable, SoundEvents.ANVIL_USE, 0.8F, 1.3F);
      }
      VillageProgress.announce(sl, s.village, "銃工房で「" + gun.getHoverName().getString() + "」を製作し、衛兵の" + guard.getName().getString() + "に持たせました", false);
      return true;
   }

   static boolean armed(Villager v) {
      if (MobEquipmentUse.kind(v.getMainHandItem()).equals("gun")) {
         return true;
      } else {
         for (ItemStack st : v.getInventory().getItems()) {
            if (!st.isEmpty() && MobEquipmentUse.kind(st).equals("gun")) {
               return true;
            }
         }

         return false;
      }
   }

   private static Item tableItem() {
      Item reforging = item("superbwarfare", "reforging_table");
      return reforging != null ? reforging : item("minecraft", "smithing_table");
   }

   private static boolean table(ServerLevel sl, BlockPos p) {
      if (tableItem() instanceof BlockItem b && sl.hasChunkAt(p) && sl.getBlockState(p).is(b.getBlock())) {
         return true;
      }

      return false;
   }

   private static BlockPos placeTable(ServerLevel sl, Survey s) {
      if (tableItem() instanceof BlockItem block && sl.getGameRules().getBoolean(GameRules.RULE_MOBGRIEFING)) {
         BlockPos c = s.village.center;
         FakePlayer actor = FakePlayerFactory.get(sl, new GameProfile(UUID.nameUUIDFromBytes("oror_gunsmith".getBytes()), "[Village Gunsmith]"));

         for (int i = 0; i < 16; i++) {
            double a = sl.random.nextDouble() * Math.PI * 2.0;
            double d = 4.0 + sl.random.nextDouble() * 6.0;
            BlockPos p = VillageExpeditions.top(sl, c.offset((int)Math.round(Math.cos(a) * d), 0, (int)Math.round(Math.sin(a) * d)));
            if (p != null && Math.abs(p.getY() - c.getY()) <= 3 && VillageWork.open(sl, p)) {
               ItemStack stack = block.getDefaultInstance();
               actor.setItemInHand(InteractionHand.MAIN_HAND, stack);
               BlockPlaceContext context = new BlockPlaceContext(
                  actor, InteractionHand.MAIN_HAND, stack, new BlockHitResult(Vec3.atCenterOf(p.below()).add(0.0, 0.5, 0.0), Direction.UP, p.below(), false)
               );
               if (block.place(context).consumesAction() && table(sl, p)) {
                  s.village.communal.add(p.asLong());
                  return p;
               }
            }
         }

         return null;
      }

      return null;
   }

   static ItemStack gun(ServerLevel sl, int tier) {
      if (!present()) {
         return ItemStack.EMPTY;
      } else {
         try {
            for (int t = Math.min(tier, TIERS.length - 1); t >= 0; t--) {
               List<String> ids = new ArrayList<>(List.of(TIERS[t]));
               Collections.shuffle(ids, new Random(sl.random.nextLong()));

               for (String id : ids) {
                  Item item = item("superbwarfare", id);
                  if (item != null) {
                     ItemStack gun = item.getDefaultInstance();
                     if (MobEquipmentUse.kind(gun).equals("gun")) {
                        spare(gun, magazine(gun) * 3);
                        return gun;
                     }
                  }
               }
            }
         } catch (ReflectiveOperationException | RuntimeException | LinkageError var8) {
            broken = true;
            System.out.println("[OROR_VILLAGE_ARMS] Superb Warfare guns disabled: " + var8);
         }

         return ItemStack.EMPTY;
      }
   }

   private static Object data(ItemStack gun) throws ReflectiveOperationException {
      return Class.forName("com.atsuishio.superbwarfare.data.gun.GunData").getMethod("from", ItemStack.class).invoke(null, gun);
   }

   private static Object value(Object data, String field) throws ReflectiveOperationException {
      Field f = data.getClass().getField(field);
      return f.get(data);
   }

   private static int magazine(ItemStack gun) throws ReflectiveOperationException {
      Object data = data(gun);
      Object prop = Class.forName("com.atsuishio.superbwarfare.data.gun.GunProp").getField("MAGAZINE").get(null);
      Method get = null;

      for (Method m : data.getClass().getMethods()) {
         if (m.getName().equals("get") && m.getParameterCount() == 1 && m.getParameterTypes()[0].isInstance(prop)) {
            get = m;
            break;
         }
      }

      return (get == null ? null : get.invoke(data, prop)) instanceof Number num ? Math.max(1, num.intValue()) : 10;
   }

   private static int spareLeft(ItemStack gun) throws ReflectiveOperationException {
      Object virtual = value(data(gun), "virtualAmmo");
      return ((Number)virtual.getClass().getMethod("get").invoke(virtual)).intValue();
   }

   private static void spare(ItemStack gun, int rounds) throws ReflectiveOperationException {
      Object data = data(gun);
      Object virtual = value(data, "virtualAmmo");
      virtual.getClass().getMethod("set", int.class).invoke(virtual, rounds);
      Object version = value(data, "nbtVersion");
      version.getClass().getMethod("invalidateState").invoke(version);
      data.getClass().getMethod("save").invoke(data);
   }

   private static boolean warfare(ItemStack gun) {
      return !gun.isEmpty() && BuiltInRegistries.ITEM.getKey(gun.getItem()).getNamespace().equals("superbwarfare") && MobEquipmentUse.kind(gun).equals("gun");
   }

   static int ammo(Villager v, ServerLevel sl, Survey s) {
      if (present() && warfare(v.getMainHandItem())) {
         try {
            ItemStack gun = v.getMainHandItem();
            int mag = magazine(gun);
            int left = spareLeft(gun);
            if (left >= mag * 2) {
               return -1;
            } else if (VillageWork.count(v, VillageWork.is("gunpowder")) == 0) {
               return VillageWork.fetch(v, sl, s, VillageWork.is("gunpowder"), 2);
            } else {
               v.getInventory().getItem(VillageWork.slotOf(v, VillageWork.is("gunpowder"))).shrink(1);
               spare(gun, left + mag * 3);
               VillagerLife.data(v).putString("Task", "弾薬を補充");
               return 2;
            }
         } catch (ReflectiveOperationException | RuntimeException | LinkageError var6) {
            broken = true;
            return -1;
         }
      } else {
         return -1;
      }
   }

   static boolean low(Villager v) {
      if (present() && warfare(v.getMainHandItem())) {
         try {
            return spareLeft(v.getMainHandItem()) < magazine(v.getMainHandItem()) * 2;
         } catch (ReflectiveOperationException | RuntimeException | LinkageError var2) {
            broken = true;
            return false;
         }
      } else {
         return false;
      }
   }
}
