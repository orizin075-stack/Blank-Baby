package jp.oror.reborn;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.animal.IronGolem;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.AABB;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

@GameTestHolder("oror_supreme_bosses")
@PrefixGameTestTemplate(false)
public final class RelicGameTests {
   private static SupremeEntity mob(GameTestHelper h, String id, int x) {
      SupremeEntity b = (SupremeEntity)((EntityType)OrorReborn.TYPES.get(id).get()).create(h.getLevel());
      BlockPos at = h.absolutePos(new BlockPos(x, 2, 8));
      b.moveTo((double)at.getX() + 0.5, (double)at.getY(), (double)at.getZ() + 0.5, 0.0F, 0.0F);
      h.getLevel().addFreshEntity(b);
      return b;
   }

   private static Player player(GameTestHelper h) {
      Player p = h.makeMockPlayer(GameType.SURVIVAL);
      BlockPos at = h.absolutePos(new BlockPos(8, 2, 8));
      p.moveTo((double)at.getX() + 0.5, (double)at.getY(), (double)at.getZ() + 0.5, 0.0F, 0.0F);
      return p;
   }

   @GameTest(
      template = "empty",
      setupTicks = 40L,
      timeoutTicks = 100,
      batch = "relics"
   )
   public static void every_character_has_four_real_relics(GameTestHelper h) {
      h.assertTrue(RelicSpec.ALL.size() == 164 && CharacterRelics.ITEMS.size() == 164, "164 registered equipment items");

      for (String id : CharacterSpec.ALL.keySet()) {
         List<RelicSpec> gear = RelicSpec.ALL.values().stream().filter(sx -> sx.character.equals(id)).toList();
         h.assertTrue(
            gear.size() == 4 && gear.stream().map(sx -> sx.slot).collect(Collectors.toSet()).equals(Set.of("weapon", "focus", "charm", "legend")),
            "Four roles for " + id
         );

         for (RelicSpec s : gear) {
            Item i = (Item)CharacterRelics.ITEMS.get(s.id).get();
            h.assertTrue(i instanceof CharacterRelics.Relic && BuiltInRegistries.ITEM.getKey(i).getPath().equals(s.id), "Native item registered " + s.id);
            if (s.rank == 3) {
               h.assertTrue(i.isFoil(i.getDefaultInstance()), "Legendary glows " + s.id);
            }
         }
      }

      h.succeed();
   }

   @GameTest(
      template = "empty",
      setupTicks = 40L,
      timeoutTicks = 100,
      batch = "relics"
   )
   public static void all_164_relic_activations_execute(GameTestHelper h) {
      Player p = player(h);
      int before = p.getPersistentData().getInt("ororRelicCasts");

      for (RelicSpec s : RelicSpec.ALL.values()) {
         Zombie z = (Zombie)EntityType.ZOMBIE.create(h.getLevel());
         z.setPersistenceRequired();
         z.setNoAi(true);
         z.moveTo(p.getX() + 2.0, p.getY(), p.getZ());
         h.getLevel().addFreshEntity(z);
         p.setItemInHand(InteractionHand.MAIN_HAND, ((Item)CharacterRelics.ITEMS.get(s.id).get()).getDefaultInstance());
         // bows, shields, catalysts and guns keep right-click for the weapon and use their art on sneak + right-click
         p.setShiftKeyDown(true);
         ((Item)CharacterRelics.ITEMS.get(s.id).get()).use(h.getLevel(), p, InteractionHand.MAIN_HAND);
         p.setShiftKeyDown(false);
         h.assertTrue(CharacterRelics.artCooling(p, p.getMainHandItem()), "Cooldown activated " + s.id);
         z.discard();

         for (Mob e : h.getLevel().getEntitiesOfClass(Mob.class, p.getBoundingBox().inflate(40.0), ex -> ex.getPersistentData().hasUUID("ororRelicOwner"))) {
            e.discard();
         }
      }

      h.assertTrue(p.getPersistentData().getInt("ororRelicCasts") == before + 164, "Every native item use reached its power");
      System.out.println("[OROR_RELICS] activations=164 PASS");
      h.succeed();
   }

   @GameTest(
      template = "empty",
      setupTicks = 40L,
      timeoutTicks = 100,
      batch = "relics"
   )
   public static void each_defeat_table_has_standard_and_rare_rewards(GameTestHelper h) {
      Player p = player(h);
      int legends = 0;

      for (String id : CharacterSpec.ALL.keySet()) {
         SupremeEntity b = mob(h, id, 8);
         boolean gotLegend = false;
         HashSet<String> common = new HashSet<>();

         for (int i = 1; i <= 160; i++) {
            List<ItemStack> stacks = RelicDrops.roll(b, p, p.damageSources().playerAttack(p), (long)i * 179L);
            boolean standard = false;

            for (ItemStack stack : stacks) {
               RelicSpec s = CharacterRelics.of(stack);
               if (s != null && s.character.equals(id)) {
                  if (s.rank == 3) {
                     gotLegend = true;
                     legends++;
                  } else {
                     common.add(s.slot);
                     standard = true;
                  }
               }
            }

            h.assertTrue(standard, "Guaranteed standard reward " + id);
         }

         h.assertTrue(gotLegend && common.size() == 3, "Standard variety and real rare roll " + id);
         b.discard();
      }

      System.out.println("[OROR_RELICS] lootTables=41 nativeRolls=6560 legends=" + legends);
      h.succeed();
   }

   @GameTest(
      template = "empty",
      setupTicks = 40L,
      timeoutTicks = 100,
      batch = "relics"
   )
   public static void player_defeat_drops_once_and_admin_death_drops_none(GameTestHelper h) {
      Player p = player(h);
      SupremeEntity b = mob(h, "mels", 8);
      b.setHealth(0.0F);
      b.die(p.damageSources().playerAttack(p));
      AABB box = b.getBoundingBox().inflate(5.0);
      long n = (long)h.getLevel().getEntitiesOfClass(ItemEntity.class, box, e -> CharacterRelics.of(e.getItem()) != null).size();
      h.assertTrue(b.isAlive() && n >= 1L, "Immortal returns and real item reward spawns");
      b.setHealth(0.0F);
      b.die(p.damageSources().playerAttack(p));
      h.assertTrue(
         (long)h.getLevel().getEntitiesOfClass(ItemEntity.class, box, e -> CharacterRelics.of(e.getItem()) != null).size() == n,
         "Same manifestation cannot be farmed repeatedly"
      );
      SupremeEntity a = mob(h, "tenki", 20);
      a.die(a.damageSources().genericKill());
      h.assertTrue(
         h.getLevel().getEntitiesOfClass(ItemEntity.class, a.getBoundingBox().inflate(4.0), e -> CharacterRelics.of(e.getItem()) != null).isEmpty(),
         "Admin removal yields no relics"
      );
      h.succeed();
   }

   @GameTest(
      template = "empty",
      setupTicks = 40L,
      timeoutTicks = 100,
      batch = "relics"
   )
   public static void immortal_avatar_fracture_rewards_without_weakening_god(GameTestHelper h) {
      Player p = player(h);
      SupremeEntity b = mob(h, "innocence", 10);
      float hp = b.getHealth();
      RelicDrops.fracture(b, p, 100000.0F);
      h.assertTrue(b.isAlive() && b.getHealth() >= hp && b.nextRelicDrop > h.getLevel().getGameTime(), "God intact, manifestation conquered");
      CompoundTag n = new CompoundTag();
      b.addAdditionalSaveData(n);
      SupremeEntity c = mob(h, "innocence", 20);
      c.readAdditionalSaveData(n);
      h.assertTrue(c.nextRelicDrop == b.nextRelicDrop && c.operatorLevel() == 4, "Manifestation ledger and authority persist");
      h.succeed();
   }

   @GameTest(
      template = "empty",
      setupTicks = 40L,
      timeoutTicks = 100,
      batch = "relics"
   )
   public static void operator_state_executes_real_level_four_commands(GameTestHelper h) {
      String[] ops = h.getLevel().getServer().getPlayerList().getOpNames();

      for (String id : OperatorPowers.HOLDERS) {
         SupremeEntity b = mob(h, id, 8);
         h.assertTrue(b.hasPermissions(4) && b.createCommandSourceStack().hasPermission(4), "Real entity command source authority " + id);
         OperatorPowers.execute(b, "effect give @s minecraft:resistance 10 255 true");
         h.assertTrue(
            b.hasEffect(MobEffects.DAMAGE_RESISTANCE) && b.getEffect(MobEffects.DAMAGE_RESISTANCE).getAmplifier() == 255, "Command executed on NPC " + id
         );
         h.assertTrue(!b.addEffect(new MobEffectInstance(MobEffects.WITHER, 100, 5)), "External debuff rejected " + id);
         CompoundTag n = new CompoundTag();
         b.addAdditionalSaveData(n);
         h.assertTrue(n.getInt("DivineOperatorLevel") == 4, "Authority saved " + id);
         b.balanced = true;
         h.assertTrue(!b.hasPermissions(4), "Comparison mode clears authority");
         b.discard();
      }

      h.assertTrue(Arrays.equals((Object[])ops, (Object[])h.getLevel().getServer().getPlayerList().getOpNames()), "Human operator list unchanged");
      System.out.println("[OROR_OPERATOR] holders=7 permission=4 realCommands=PASS humanOpsUnchanged=true");
      h.succeed();
   }

   @GameTest(
      template = "empty",
      setupTicks = 40L,
      timeoutTicks = 100,
      batch = "relics"
   )
   public static void legendary_gear_rejects_damage_and_existence_erasure(GameTestHelper h) {
      Player p = player(h);
      p.setHealth(4.0F);
      p.setItemInHand(InteractionHand.MAIN_HAND, ((Item)CharacterRelics.ITEMS.get("tenki_legend").get()).getDefaultInstance());
      p.hurt(p.damageSources().magic(), 10000.0F);
      h.assertTrue(p.isAlive() && p.getHealth() == 4.0F, "Held legendary rejects fatal damage");
      SupremeEntity b = mob(h, "kokuhaku", 12);
      b.setTarget(p);
      LorePowers.strike(b, p, 1.0F, true);
      h.assertTrue(p.isAlive(), "Legendary refuses existence erasure");
      p.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
      p.hurt(p.damageSources().magic(), 10000.0F);
      h.assertTrue(!p.isAlive(), "Defense belongs to equipped relic");
      h.succeed();
   }

   @GameTest(
      template = "empty",
      setupTicks = 40L,
      timeoutTicks = 100,
      batch = "relics"
   )
   public static void op_time_changes_do_not_break_freeze_world_clock(GameTestHelper h) {
      SupremeEntity b = mob(h, "miyohime", 8);
      Zombie z = (Zombie)EntityType.ZOMBIE.create(h.getLevel());
      z.setPersistenceRequired();
      z.setNoAi(true);
      BlockPos at = h.absolutePos(new BlockPos(15, 2, 8));
      z.moveTo((double)at.getX(), (double)at.getY(), (double)at.getZ());
      h.getLevel().addFreshEntity(z);
      Abilities.stun(z, 20);
      long until = z.getPersistentData().getLong("ororFreezeUntil");
      OperatorPowers.execute(b, "time set day");
      h.assertTrue(z.getPersistentData().getLong("ororFreezeUntil") == until, "Day rewrite does not change freeze expiry");
      h.runAfterDelay(25L, () -> {
         h.assertTrue(h.getLevel().getGameTime() >= until && z.isAlive(), "World clock progresses under operator state");
         h.succeed();
      });
   }

   private static int summons(GameTestHelper h) {
      int count = 0;

      for (Entity entity : h.getLevel().getAllEntities()) {
         if (entity instanceof Mob) {
            Mob m = (Mob)entity;
            if (m.isAlive() && (entity instanceof FamiliarEntity || entity.getPersistentData().hasUUID("ororRelicOwner"))) {
               count++;
            }
         }
      }

      return count;
   }

   private static void mixedOrder(GameTestHelper h, boolean playerFirst) {
      int old = (Integer)RebornConfig.LEVEL_SUMMONS.get();
      int initial = summons(h);
      Player p = player(h);
      SupremeEntity b = mob(h, "mels", 24);
      b.setNoAi(true);

      try {
         RebornConfig.LEVEL_SUMMONS.set(initial + 3);
         if (playerFirst) {
            RelicPowers.cast(RelicSpec.ALL.get("hephaistos_legend"), p);
            h.assertTrue(summons(h) == initial + 3, "Player summons fill global budget");

            for (int i = 0; i < 8; i++) {
               FamiliarEntity.create(b, h.getLevel(), 0, 6);
            }
         } else {
            for (int i = 0; i < 8; i++) {
               FamiliarEntity.create(b, h.getLevel(), 0, 6);
            }

            h.assertTrue(summons(h) == initial + 3, "NPC summons fill global budget");
            RelicPowers.cast(RelicSpec.ALL.get("hephaistos_legend"), p);
         }

         h.assertTrue(summons(h) == initial + 3, "Mixed summon order must not exceed shared limit");
      } finally {
         RebornConfig.LEVEL_SUMMONS.set(old);
         for (Mob entity : h.getLevel().getEntitiesOfClass(Mob.class, h.getBounds().inflate(40.0))) {
            if (entity instanceof FamiliarEntity f && b.getUUID().equals(f.creator)
               || entity.getPersistentData().hasUUID("ororRelicOwner") && p.getUUID().equals(entity.getPersistentData().getUUID("ororRelicOwner"))) {
               entity.discard();
            }
         }

         b.discard();
      }

      h.succeed();
   }

   @GameTest(
      template = "empty",
      setupTicks = 40L,
      timeoutTicks = 100,
      batch = "relics"
   )
   public static void relic_then_npc_summons_share_level_limit(GameTestHelper h) {
      mixedOrder(h, true);
   }

   @GameTest(
      template = "empty",
      setupTicks = 40L,
      timeoutTicks = 100,
      batch = "relics"
   )
   public static void npc_then_relic_summons_share_level_limit(GameTestHelper h) {
      mixedOrder(h, false);
   }

   @GameTest(
      template = "empty",
      setupTicks = 40L,
      timeoutTicks = 100,
      batch = "relics"
   )
   public static void dead_summons_release_budget_before_removal(GameTestHelper h) {
      Player p = player(h);
      int old = (Integer)RebornConfig.LEVEL_SUMMONS.get();
      int initial = summons(h);
      IronGolem g = (IronGolem)EntityType.IRON_GOLEM.create(h.getLevel());
      g.moveTo(p.getX() + 3.0, p.getY(), p.getZ());
      g.getPersistentData().putUUID("ororRelicOwner", p.getUUID());
      h.getLevel().addFreshEntity(g);

      try {
         RebornConfig.LEVEL_SUMMONS.set(initial + 1);
         h.assertTrue(SummonBudget.remaining(h.getLevel(), p.getUUID(), 4, 4) == 0, "Alive summon reserves a slot");
         g.setHealth(0.0F);
         h.assertTrue(SummonBudget.remaining(h.getLevel(), p.getUUID(), 4, 4) == 1, "Dead summon releases the slot immediately");
      } finally {
         RebornConfig.LEVEL_SUMMONS.set(old);
         g.discard();
      }

      h.succeed();
   }
}
