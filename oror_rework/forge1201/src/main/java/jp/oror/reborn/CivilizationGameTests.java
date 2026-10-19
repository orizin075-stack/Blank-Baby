package jp.oror.reborn;

import java.util.List;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.Container;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Husk;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Arrow;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.item.trading.MerchantOffers;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.GameRules.BooleanValue;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraftforge.event.entity.player.TradeWithVillagerEvent;
import net.minecraftforge.event.entity.player.PlayerInteractEvent.EntityInteract;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

@GameTestHolder("oror_supreme_bosses")
@PrefixGameTestTemplate(false)
public final class CivilizationGameTests {
    static Villager worker(GameTestHelper h, int x, int z) {
        for (int dx = x - 6; dx <= x + 12; dx++) {
            for (int dz = z - 6; dz <= z + 12; dz++) {
                h.setBlock(dx, 1, dz, Blocks.STONE);
            }
        }

        Villager v = (Villager)EntityType.VILLAGER.create(h.getLevel());
        BlockPos p = h.absolutePos(new BlockPos(x, 2, z));
        v.moveTo((double)p.getX() + 0.5, (double)p.getY(), (double)p.getZ() + 0.5, 0.0F, 0.0F);
        v.setNoAi(true);
        v.setPersistenceRequired();
        h.getLevel().addFreshEntity(v);
        MobLevels.set(v, 5);
        VillageLedger.of(v);
        ((BooleanValue)h.getLevel().getGameRules().getRule(GameRules.RULE_MOBGRIEFING)).set(true, h.getLevel().getServer());
        return v;
    }

    private static int count(Container c, Item item) {
        int n = 0;

        for (int i = 0; i < c.getContainerSize(); i++) {
            if (c.getItem(i).is(item)) {
                n += c.getItem(i).getCount();
            }
        }

        return n;
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 120,
        batch = "civilization"
    )
    public static void reputation_isolated_between_villages_and_saved(GameTestHelper h) {
        Villager a = worker(h, 8, 8);
        Villager b = worker(h, 108, 8);
        UUID p = UUID.randomUUID();
        VillageLedger.Village av = VillageLedger.of(a);
        VillageLedger.Village bv = VillageLedger.of(b);
        VillageLedger db = VillageLedger.get(h.getLevel());
        db.change(av, p, 80, h.getLevel().getGameTime(), "trade");
        h.assertTrue(av.score(p) == 80 && bv.score(p) == 0 && !VillageReputation.sameVillage(a, b), "Only the local settlement gains reputation");
        VillageLedger copy = VillageLedger.load(db.save(new CompoundTag()));
        h.assertTrue(copy.villages.get(av.id).score(p) == 80 && copy.villages.get(bv.id).score(p) == 0, "World saved data retains both villages separately");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 120,
        batch = "civilization"
    )
    public static void actual_food_interaction_and_trade_improve_local_score(GameTestHelper h) {
        Villager v = worker(h, 8, 8);
        Player p = h.makeMockPlayer(GameType.SURVIVAL);
        p.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.BREAD, 3));
        EntityInteract interaction = new EntityInteract(p, InteractionHand.MAIN_HAND, v);
        VillageReputation.interact(interaction);
        h.assertTrue(
            interaction.isCanceled()
                && p.getMainHandItem().getCount() == 2
                && count(v.getInventory(), Items.BREAD) == 1
                && VillageReputation.score(v, p.getUUID()) == 2,
            "Donated actual food is consumed and stored"
        );
        MerchantOffer offer = new MerchantOffer(new ItemStack(Items.EMERALD, 2), Items.BREAD.getDefaultInstance(), 16, 2, 0.05F);
        VillageReputation.trade(new TradeWithVillagerEvent(p, offer, v));
        h.assertTrue(VillageReputation.score(v, p.getUUID()) == 5, "Completed trade adds local reputation");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 160,
        batch = "civilization"
    )
    public static void village_attack_and_murder_cause_severe_hostility(GameTestHelper h) {
        Villager v = worker(h, 8, 8);
        v.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1024.0);
        v.setHealth(1024.0F);
        Player p = h.makeMockPlayer(GameType.SURVIVAL);
        v.hurt(p.damageSources().playerAttack(p), 10.0F);
        h.assertTrue(VillageReputation.score(v, p.getUUID()) <= -120, "Real damage causes severe local hostility");
        v.invulnerableTime = 0;
        v.hurt(p.damageSources().playerAttack(p), 1000000.0F);
        h.assertTrue(VillageReputation.score(v, p.getUUID()) <= -520, "Actual death causes an additional murder penalty");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 120,
        batch = "civilization"
    )
    public static void benefits_change_real_merchant_prices(GameTestHelper h) {
        Villager v = worker(h, 8, 8);
        Player p = h.makeMockPlayer(GameType.SURVIVAL);
        MerchantOffers offers = new MerchantOffers();
        offers.add(new MerchantOffer(new ItemStack(Items.EMERALD, 20), Items.DIAMOND.getDefaultInstance(), 16, 2, 0.05F));
        v.setOffers(offers);
        VillageLedger.Village village = VillageLedger.of(v);

        for (int i = 0; i < 5; i++) {
            VillageLedger.get(h.getLevel()).change(village, p.getUUID(), 100, h.getLevel().getGameTime(), "benefit" + i);
        }

        VillageReputation.prices(v, p);
        h.assertTrue(((MerchantOffer)v.getOffers().get(0)).getCostA().getCount() == 10, "High local trust discounts a real offer from 20 to 10");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 120,
        batch = "civilization"
    )
    public static void chest_theft_and_sort_preserve_exact_components(GameTestHelper h) {
        Villager v = worker(h, 8, 8);
        SimpleContainer box = new SimpleContainer(27);
        box.setItem(0, new ItemStack(Items.OAK_LOG, 5));
        box.setItem(8, new ItemStack(Items.OAK_LOG, 3));
        box.setItem(9, new ItemStack(Items.DIAMOND, 2));
        List<ItemStack> before = VillageReputation.snapshot(box);
        box.removeItem(8, 1);
        h.assertTrue(VillageReputation.removed(before, box) == 1, "Actual item removal is detected independently of slot order");
        h.assertTrue(VillagerLife.sort(box) && count(box, Items.OAK_LOG) == 7 && count(box, Items.DIAMOND) == 2, "Sorting conserves all resources");
        h.assertTrue(VillageReputation.removed(VillageReputation.snapshot(box), box) == 0, "Opening/reordering without theft does not invent stolen items");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 120,
        batch = "civilization"
    )
    public static void owned_player_chests_are_not_worker_supplies(GameTestHelper h) {
        Villager v = worker(h, 8, 8);
        BlockPos at = h.absolutePos(new BlockPos(10, 2, 8));
        h.getLevel().setBlock(at, Blocks.CHEST.defaultBlockState(), 3);
        VillageLedger.Village village = VillageLedger.of(v);
        village.property.put(at.asLong(), UUID.randomUUID());
        h.assertTrue(VillageReputation.communalChest(h.getLevel(), village, at) == null, "Workers cannot use a recorded personal chest");
        village.property.remove(at.asLong());
        h.assertTrue(VillageReputation.communalChest(h.getLevel(), village, at) != null, "Shared village chest can supply workers");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 120,
        batch = "civilization"
    )
    public static void mature_crop_harvests_and_replants_real_produce(GameTestHelper h) {
        Villager v = worker(h, 8, 8);
        BlockPos at = h.absolutePos(new BlockPos(10, 2, 8));
        h.getLevel().setBlock(at.below(), Blocks.FARMLAND.defaultBlockState(), 3);
        h.getLevel().setBlock(at, (BlockState)Blocks.WHEAT.defaultBlockState().setValue(CropBlock.AGE, 7), 3);
        h.assertTrue(VillagerLife.harvest(v, h.getLevel(), at) && count(v.getInventory(), Items.WHEAT) >= 1, "Harvest creates real wheat from a mature plant");
        h.assertTrue((Integer)h.getLevel().getBlockState(at).getValue(CropBlock.AGE) == 0, "One actual seed was reserved to replant");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 120,
        batch = "civilization"
    )
    public static void farm_expansion_needs_actual_seed_and_nearby_water(GameTestHelper h) {
        Villager v = worker(h, 8, 8);
        BlockPos soil = h.absolutePos(new BlockPos(10, 1, 8));
        h.getLevel().setBlock(soil, Blocks.DIRT.defaultBlockState(), 3);
        h.getLevel().setBlock(soil.north(2), Blocks.WATER.defaultBlockState(), 3);
        v.getInventory().addItem(new ItemStack(Items.WHEAT_SEEDS, 3));
        h.assertTrue(
            VillagerLife.expandFarm(v, h.getLevel(), soil)
                && count(v.getInventory(), Items.WHEAT_SEEDS) == 2
                && h.getLevel().getBlockState(soil).is(Blocks.FARMLAND)
                && h.getLevel().getBlockState(soil.above()).is(Blocks.WHEAT),
            "Expansion spends a seed and changes actual dirt and crop blocks"
        );
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 120,
        batch = "civilization"
    )
    public static void lumber_and_registered_recipe_conserve_resources(GameTestHelper h) {
        Villager v = worker(h, 8, 8);
        BlockPos tree = h.absolutePos(new BlockPos(10, 2, 8));
        h.getLevel().setBlock(tree, Blocks.OAK_LOG.defaultBlockState(), 3);
        h.assertTrue(
            VillagerLife.fell(v, h.getLevel(), tree) && h.getLevel().getBlockState(tree).isAir() && count(v.getInventory(), Items.OAK_LOG) == 1,
            "Actual log is cut and collected"
        );
        h.assertTrue(
            VillagerLife.craft(v, h.getLevel(), new ResourceLocation("oak_planks"))
                && count(v.getInventory(), Items.OAK_LOG) == 0
                && count(v.getInventory(), Items.OAK_PLANKS) == 4,
            "A registered native recipe consumes one log and outputs four planks"
        );
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 120,
        batch = "civilization"
    )
    public static void village_blueprint_spends_supplies_and_retains_progress(GameTestHelper h) {
        Villager v = worker(h, 8, 8);
        BlockPos at = h.absolutePos(new BlockPos(12, 2, 12));
        h.assertTrue(VillagerLife.startBuild(v, h.getLevel(), at), "Valid free plot accepted");
        v.moveTo((double)(at.getX() + 2), (double)(at.getY() + 1), (double)(at.getZ() + 2), 0.0F, 0.0F);
        h.assertTrue(!VillagerLife.build(v, h.getLevel()) && VillagerLife.data(v).getInt("BuildStep") == 0, "No material means no building");
        v.getInventory().addItem(new ItemStack(Items.COBBLESTONE, 25));
        h.assertTrue(
            VillagerLife.build(v, h.getLevel())
                && count(v.getInventory(), Items.COBBLESTONE) == 24
                && h.getLevel().getBlockState(at.below()).is(Blocks.COBBLESTONE),
            "One actual block costs one material"
        );
        CompoundTag save = new CompoundTag();
        v.saveWithoutId(save);
        Villager copy = (Villager)EntityType.VILLAGER.create(h.getLevel());
        copy.load(save);
        h.assertTrue(
            VillagerLife.data(copy).getInt("BuildStep") == 1 && count(copy.getInventory(), Items.COBBLESTONE) == 24,
            "Build progress and precise stock survive native NBT reload"
        );
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 180,
        batch = "civilization"
    )
    public static void complete_house_has_real_double_door_bed_storage_and_exact_material_cost(GameTestHelper h) {
        Villager v = worker(h, 8, 8);
        BlockPos origin = h.absolutePos(new BlockPos(12, 2, 12));
        h.assertTrue(VillagerLife.startBuild(v, h.getLevel(), origin), "Free plot accepted");
        v.getInventory().addItem(new ItemStack(Items.COBBLESTONE, 25));
        v.getInventory().addItem(new ItemStack(Items.OAK_PLANKS, 64));
        v.getInventory().addItem(new ItemStack(Items.OAK_PLANKS, 7));
        v.getInventory().addItem(Items.OAK_DOOR.getDefaultInstance());
        v.getInventory().addItem(Items.WHITE_BED.getDefaultInstance());
        v.getInventory().addItem(Items.CHEST.getDefaultInstance());

        for (int i = 0; i < 110 && VillagerLife.data(v).contains("BuildOrigin"); i++) {
            int step = VillagerLife.data(v).getInt("BuildStep");
            v.moveTo((double)origin.getX() + 2.5, (double)(origin.getY() + (step < 25 ? 0 : 1)), (double)origin.getZ() + 2.5, 0.0F, 0.0F);
            h.assertTrue(VillagerLife.build(v, h.getLevel()), "Native house part " + step);
        }

        h.assertTrue(
            VillagerLife.data(v).getInt("Houses") == 1 && VillageLedger.of(v).houses == 1 && v.getInventory().isEmpty(),
            "Exactly 25 cobble, 71 planks, one door, one bed and one chest consumed"
        );
        h.runAfterDelay(
            5L,
            () -> {
                h.assertTrue(
                    h.getLevel().getBlockState(origin.offset(2, 0, 0)).is(Blocks.OAK_DOOR)
                        && h.getLevel().getBlockState(origin.offset(2, 1, 0)).is(Blocks.OAK_DOOR)
                        && h.getLevel().getBlockState(origin.offset(3, 0, 2)).is(Blocks.WHITE_BED)
                        && h.getLevel().getBlockState(origin.offset(3, 0, 3)).is(Blocks.WHITE_BED)
                        && h.getLevel().getBlockEntity(origin.offset(1, 0, 2)) instanceof ChestBlockEntity,
                    "Double blocks survive native neighbor updates and storage is a real chest"
                );
                h.succeed();
            }
        );
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 120,
        batch = "civilization"
    )
    public static void villagers_trade_with_each_other_using_real_payment(GameTestHelper h) {
        Villager buyer = worker(h, 8, 8);
        Villager seller = worker(h, 10, 8);
        MerchantOffers offers = new MerchantOffers();
        offers.add(new MerchantOffer(new ItemStack(Items.EMERALD, 2), new ItemStack(Items.BREAD, 3), 16, 2, 0.05F));
        seller.setOffers(offers);
        buyer.getInventory().addItem(new ItemStack(Items.EMERALD, 4));
        h.assertTrue(
            VillagerLife.tradeWith(buyer, seller)
                && count(buyer.getInventory(), Items.EMERALD) == 2
                && count(buyer.getInventory(), Items.BREAD) == 3
                && count(seller.getInventory(), Items.EMERALD) == 2
                && ((MerchantOffer)seller.getOffers().get(0)).getUses() == 1,
            "Trade transferred real payment and honored actual stock usage"
        );
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 120,
        batch = "civilization"
    )
    public static void villagers_pray_at_a_real_shrine_once_per_day(GameTestHelper h) {
        Villager v = worker(h, 8, 8);
        h.setBlock(10, 2, 8, Blocks.BELL);
        h.assertTrue(
            VillagerLife.pray(v, h.getLevel()) && !VillagerLife.pray(v, h.getLevel()) && !VillagerLife.data(v).getString("Faith").isEmpty(),
            "A real bell creates a named faith and one prayer per day"
        );
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 120,
        batch = "civilization"
    )
    public static void local_squad_shares_targets_and_supports_injured_allies(GameTestHelper h) {
        Villager a = worker(h, 8, 8);
        Villager b = worker(h, 10, 8);
        a.setNoAi(false);
        b.setNoAi(false);
        Husk enemy = (Husk)EntityType.HUSK.create(h.getLevel());
        enemy.moveTo(a.getX() + 5.0, a.getY(), a.getZ());
        h.getLevel().addFreshEntity(enemy);
        a.setHealth(a.getMaxHealth());
        b.setHealth(b.getMaxHealth() * 0.1F);
        float hp = b.getHealth();
        Teamplay.coordinate(a, h.getLevel(), enemy);
        h.assertTrue(
            b.getTarget() == enemy && b.getHealth() > hp && MobMind.data(a).getInt("Alerts") > 0 && MobMind.data(a).getInt("Supports") > 0,
            "Real local squad receives a shared target and costly healing"
        );
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 120,
        batch = "civilization"
    )
    public static void local_squad_rejects_accidental_melee_and_projectile_damage(GameTestHelper h) {
        Villager a = worker(h, 8, 8);
        Villager b = worker(h, 10, 8);
        a.setNoAi(false);
        b.setNoAi(false);
        float hp = b.getHealth();
        b.hurt(a.damageSources().mobAttack(a), 200.0F);
        Arrow arrow = new Arrow(h.getLevel(), a, Items.ARROW.getDefaultInstance(), Items.BOW.getDefaultInstance());
        b.invulnerableTime = 0;
        b.hurt(a.damageSources().arrow(arrow, a), 200.0F);
        h.assertTrue(VillageReputation.sameVillage(a, b) && b.getHealth() == hp && b.getTarget() != a, "Same-village friendly damage cannot start infighting");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 120,
        batch = "civilization"
    )
    public static void griefing_rule_stops_lumber_farm_and_building(GameTestHelper h) {
        Villager v = worker(h, 8, 8);
        BlockPos pos = h.absolutePos(new BlockPos(10, 2, 8));
        h.getLevel().setBlock(pos, Blocks.OAK_LOG.defaultBlockState(), 3);
        BooleanValue rule = (BooleanValue)h.getLevel().getGameRules().getRule(GameRules.RULE_MOBGRIEFING);
        rule.set(false, h.getLevel().getServer());
        boolean cut = VillagerLife.fell(v, h.getLevel(), pos);
        rule.set(true, h.getLevel().getServer());
        h.assertTrue(!cut && h.getLevel().getBlockState(pos).is(Blocks.OAK_LOG), "Disabled mob griefing preserves terrain");
        h.succeed();
    }
}
