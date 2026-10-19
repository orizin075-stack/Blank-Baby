package jp.oror.reborn;

import com.google.gson.JsonObject;
import java.util.List;
import java.util.function.Consumer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.animal.Cow;
import net.minecraft.world.entity.monster.Husk;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.GameType;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.event.entity.living.LivingEvent.LivingTickEvent;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

@GameTestHolder("oror_supreme_bosses")
@PrefixGameTestTemplate(false)
public final class PowerGameTests {
    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 120,
        batch = "power"
    )
    public static void every_rank_has_measured_stronger_defense_attack_aim_and_loadout(GameTestHelper h) {
        double previous = 0.0;
        float spread = Float.MAX_VALUE;
        int cd = 100;

        for (int rank = 1; rank <= 6; rank++) {
            Villager v = CivilizationGameTests.worker(h, 8, 8);
            MobLevels.set(v, rank);
            MobLevels.refresh(v);
            double power = MobMind.strength(v);
            float accuracy = MobLevels.accuracy(v, "bow");
            int cooldown = MobLevels.cooldown(v, 20);
            h.assertTrue(power > previous && accuracy < spread && cooldown < cd, "Measured rank advancement increases power, accuracy and reaction " + rank);
            h.assertTrue(
                !v.getMainHandItem().isEmpty()
                    && v.getItemBySlot(EquipmentSlot.CHEST)
                        .is(rank >= 4 ? Items.NETHERITE_CHESTPLATE : (rank >= 2 ? Items.DIAMOND_CHESTPLATE : Items.IRON_CHESTPLATE)),
                "Actual rank loadout " + rank
            );
            Husk target = (Husk)EntityType.HUSK.create(h.getLevel());
            target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1024.0);
            target.setHealth(1024.0F);
            target.moveTo(v.getX() + 2.0, v.getY(), v.getZ());
            target.setNoAi(true);
            h.getLevel().addFreshEntity(target);
            AdaptiveCombat.strike(v, target, "sword", h.getLevel());
            JsonObject row = new JsonObject();
            row.addProperty("rank", rank);
            row.addProperty("health", v.getMaxHealth());
            row.addProperty("power", power);
            row.addProperty("aim_spread", accuracy);
            row.addProperty("attack_cooldown_ticks", cooldown);
            row.addProperty("actual_damage_to_unarmored_1024hp", 1024.0F - target.getHealth());
            row.addProperty("weapon", BuiltInRegistries.ITEM.getKey(v.getMainHandItem().getItem()).toString());
            System.out.println("[OROR_POWER_CHECK] " + row);
            previous = power;
            spread = accuracy;
            cd = cooldown;
            v.discard();
            target.discard();
        }

        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 1200,
        batch = "power"
    )
    public static void all_six_ranks_defeat_fully_armored_scripted_survival_fighters(GameTestHelper h) {
        Villager[] bot = new Villager[]{null};
        Player[] opponent = new Player[]{null};
        int[] rank = new int[]{1};
        long[] started = new long[]{0L};
        int[] armor = new int[]{0};
        double[] toughness = new double[]{0.0};
        Runnable spawn = () -> {
            Villager v = CivilizationGameTests.worker(h, 8, 8);
            v.setNoAi(false);
            MobLevels.set(v, rank[0]);
            MobLevels.refresh(v);
            Player p = h.makeMockPlayer(GameType.SURVIVAL);
            p.getInventory().clearContent();
            p.removeAllEffects();
            p.moveTo(v.getX() + 2.0, v.getY(), v.getZ());
            p.setHealth(20.0F);
            Registry<Enchantment> registry = h.getLevel().registryAccess().registryOrThrow(Registries.ENCHANTMENT);

            for (EquipmentSlot slot : List.of(EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET)) {
                Item item = switch (slot) {
                    case HEAD -> Items.NETHERITE_HELMET;
                    case CHEST -> Items.NETHERITE_CHESTPLATE;
                    case LEGS -> Items.NETHERITE_LEGGINGS;
                    default -> Items.NETHERITE_BOOTS;
                };
                ItemStack stack = item.getDefaultInstance();
                stack.enchant(registry.getHolderOrThrow(Enchantments.PROTECTION), 4);
                p.setItemSlot(slot, stack);
            }

            for (EquipmentSlot slot : List.of(EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET)) {
                p.getItemBySlot(slot).forEachModifier(slot, (attribute, modifier) -> {
                    AttributeInstance instance = p.getAttribute(attribute);
                    if (instance != null && !instance.hasModifier(modifier.id())) {
                        instance.addTransientModifier(modifier);
                    }
                });
            }

            p.tick();
            armor[0] = p.getArmorValue();
            toughness[0] = p.getAttributeValue(Attributes.ARMOR_TOUGHNESS);
            h.assertTrue(armor[0] >= 20 && toughness[0] >= 8.0, "The equipped native armor modifiers are active after the fighter ticks");
            p.setItemInHand(InteractionHand.MAIN_HAND, Items.NETHERITE_SWORD.getDefaultInstance());
            v.setTarget(p);
            bot[0] = v;
            opponent[0] = p;
            started[0] = h.getLevel().getGameTime();
        };
        spawn.run();
        h.onEachTick(() -> {
            if (rank[0] <= 6) {
                Villager v = bot[0];
                Player p = opponent[0];
                long elapsed = h.getLevel().getGameTime() - started[0];
                if (elapsed % 10L == 0L && p.isAlive() && v.distanceToSqr(p) < 9.0) {
                    p.swing(InteractionHand.MAIN_HAND);
                    v.hurt(p.damageSources().playerAttack(p), 12.0F);
                }

                h.assertTrue(v.isAlive(), "Rank " + rank[0] + " survives its independent armored duel");
                if (!p.isAlive()) {
                    JsonObject row = new JsonObject();
                    row.addProperty("rank", rank[0]);
                    row.addProperty("scenario", "independent 20hp ProtectionIV netherite scripted melee counterattack");
                    row.addProperty("kill_ticks", elapsed);
                    row.addProperty("opponent_initial_armor", armor[0]);
                    row.addProperty("opponent_initial_toughness", toughness[0]);
                    row.addProperty("successful_strikes", MobMind.data(v).getInt("SuccessfulStrikes"));
                    row.addProperty("shots", MobMind.data(v).getInt("Shots"));
                    row.addProperty("bot_remaining_health", v.getHealth());
                    row.addProperty("bot_alive", v.isAlive());
                    System.out.println("[OROR_POWER_BATTLE] " + row);

                    for (Projectile projectile : h.getLevel().getEntitiesOfClass(Projectile.class, v.getBoundingBox().inflate(64.0), a -> a.getOwner() == v)) {
                        projectile.discard();
                    }

                    v.discard();
                    p.discard();
                    rank[0]++;
                    if (rank[0] <= 6) {
                        spawn.run();
                    }
                }
            }
        });
        h.succeedWhen(() -> h.assertTrue(rank[0] > 6, "All six independent ranks defeat actual armored scripted fighters"));
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 120,
        batch = "power"
    )
    public static void elite_beats_five_netherite_targets_and_resists_native_damage(GameTestHelper h) {
        Villager v = CivilizationGameTests.worker(h, 8, 8);
        MobLevels.set(v, 6);
        MobLevels.refresh(v);
        float before = v.getHealth();
        v.hurt(v.damageSources().generic(), 40.0F);
        h.assertTrue(v.getHealth() > before - 25.0F, "Actual elite armor and resistance reduce incoming damage");
        int defeated = 0;

        for (int i = 0; i < 5; i++) {
            Husk t = (Husk)EntityType.HUSK.create(h.getLevel());
            t.moveTo(v.getX() + 2.0, v.getY(), v.getZ());
            t.setNoAi(true);
            t.setItemSlot(EquipmentSlot.CHEST, Items.NETHERITE_CHESTPLATE.getDefaultInstance());
            h.getLevel().addFreshEntity(t);
            AdaptiveCombat.strike(v, t, "sword", h.getLevel());
            if (!t.isAlive()) {
                defeated++;
            }

            t.discard();
        }

        h.assertTrue(defeated == 5, "Rank six kills all five actual armored mobs");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "power"
    )
    public static void erasure_uses_native_death_events_with_real_attacker(GameTestHelper h) {
        SupremeEntity b = (SupremeEntity)((EntityType)OrorReborn.TYPES.get("miyohime").get()).create(h.getLevel());
        BlockPos pos = h.absolutePos(new BlockPos(8, 2, 8));
        b.moveTo((double)pos.getX(), (double)pos.getY(), (double)pos.getZ());
        b.setNoAi(true);
        h.getLevel().addFreshEntity(b);
        Husk victim = (Husk)EntityType.HUSK.create(h.getLevel());
        victim.moveTo(b.getX() + 2.0, b.getY(), b.getZ());
        victim.setNoAi(true);
        victim.setItemSlot(EquipmentSlot.CHEST, Items.NETHERITE_CHESTPLATE.getDefaultInstance());
        h.getLevel().addFreshEntity(victim);
        victim.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 100, 4));
        victim.hurt(victim.damageSources().generic(), 1.0F);
        int[] events = new int[]{0};
        Consumer<LivingDeathEvent> listener = e -> {
            if (e.getEntity() == victim) {
                h.assertTrue(
                    e.getSource().getEntity() == b && e.getSource().getMsgId().equals("oror_erasure"),
                    "Native death event retains actual character and ability damage type"
                );
                events[0]++;
            }
        };
        MinecraftForge.EVENT_BUS.addListener(listener);

        try {
            LorePowers.strike(b, victim, 1.0F, true);
            h.assertTrue(
                !victim.isAlive() && events[0] == 1,
                "Erasure defeats armor, resistance and hurt cooldown through native damage, with one attributed death event"
            );
        } finally {
            MinecraftForge.EVENT_BUS.unregister(listener);
        }

        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "power"
    )
    public static void peaceful_domain_spares_unrelated_life(GameTestHelper h) {
        SupremeEntity b = (SupremeEntity)((EntityType)OrorReborn.TYPES.get("shinra").get()).create(h.getLevel());
        BlockPos pos = h.absolutePos(new BlockPos(8, 2, 8));
        b.moveTo((double)pos.getX(), (double)pos.getY(), (double)pos.getZ());
        h.getLevel().addFreshEntity(b);
        Husk enemy = (Husk)EntityType.HUSK.create(h.getLevel());
        enemy.moveTo(b.getX() + 2.0, b.getY(), b.getZ());
        enemy.setNoAi(true);
        h.getLevel().addFreshEntity(enemy);
        enemy.setTarget(b);
        Cow cow = (Cow)EntityType.COW.create(h.getLevel());
        cow.moveTo(b.getX() - 2.0, b.getY(), b.getZ());
        cow.setNoAi(true);
        h.getLevel().addFreshEntity(cow);
        float health = cow.getHealth();
        b.setTarget(enemy);
        DivineDomains.begin(b);
        DivineDomains.tick(new Post(b));
        h.assertTrue(
            !enemy.isAlive() && cow.isAlive() && cow.getHealth() == health, "Peaceful character's field defeats attackers while preserving unrelated animals"
        );
        h.succeed();
    }
}
