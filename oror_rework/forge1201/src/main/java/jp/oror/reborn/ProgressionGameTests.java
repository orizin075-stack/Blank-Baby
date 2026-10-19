package jp.oror.reborn;

import com.mojang.authlib.GameProfile;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.Holder.Reference;
import net.minecraft.core.registries.Registries;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.world.Container;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.village.poi.PoiType;
import net.minecraft.world.entity.ai.village.poi.PoiTypes;
import net.minecraft.world.entity.monster.Husk;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.npc.VillagerProfession;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.GameRules.BooleanValue;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.level.block.entity.FurnaceBlockEntity;
import net.minecraftforge.common.util.FakePlayer;
import net.minecraftforge.common.util.FakePlayerFactory;
import net.minecraftforge.event.ServerChatEvent;
import net.minecraftforge.event.entity.player.PlayerInteractEvent.EntityInteract;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

@GameTestHolder("oror_supreme_bosses")
@PrefixGameTestTemplate(false)
public final class ProgressionGameTests {
    private static <T extends Mob> T mob(GameTestHelper h, EntityType<T> type, int x, int z) {
        T m = (T)type.create(h.getLevel());
        BlockPos p = h.absolutePos(new BlockPos(x, 2, z));
        m.moveTo((double)p.getX() + 0.5, (double)p.getY(), (double)p.getZ() + 0.5, 0.0F, 0.0F);
        m.setPersistenceRequired();
        h.getLevel().addFreshEntity(m);
        MobLevels.set(m, 1);
        return m;
    }

    private static Villager worker(GameTestHelper h, int x, int z, int rank) {
        for (int dx = x - 4; dx <= x + 8; dx++) {
            for (int dz = z - 4; dz <= z + 4; dz++) {
                h.setBlock(dx, 1, dz, Blocks.STONE);
            }
        }

        Villager v = mob(h, EntityType.VILLAGER, x, z);
        MobLevels.set(v, rank);
        BlockPos at = h.absolutePos(new BlockPos(x - 2, 2, z));
        h.getLevel().setBlock(at, Blocks.FURNACE.defaultBlockState(), 3);
        h.getLevel().setBlock(at.north(), Blocks.CHEST.defaultBlockState(), 3);
        ((ChestBlockEntity)h.getLevel().getBlockEntity(at.north())).setItem(0, new ItemStack(Items.COAL, 16));
        h.assertTrue(VillagerIndustry.hire(v, at, null), "Real furnace assigned");
        ((BooleanValue)h.getLevel().getGameRules().getRule(GameRules.RULE_MOBGRIEFING)).set(true, h.getLevel().getServer());
        return v;
    }

    private static int count(Container c, Item item) {
        int total = 0;

        for (int i = 0; i < c.getContainerSize(); i++) {
            if (c.getItem(i).is(item)) {
                total += c.getItem(i).getCount();
            }
        }

        return total;
    }

    private static ChestBlockEntity box(GameTestHelper h, Villager v) {
        return (ChestBlockEntity)h.getLevel().getBlockEntity(VillagerIndustry.station(v).north());
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 180,
        batch = "progression"
    )
    public static void critical_attack_waits_for_actual_descending_jump(GameTestHelper h) {
        Villager v = mob(h, EntityType.VILLAGER, 8, 8);
        MobLevels.set(v, 5);
        AdaptiveCombat.arm(v);
        MobMind.data(v).putString("Stance", "aggressive");
        Husk t = mob(h, EntityType.HUSK, 10, 8);
        t.setNoAi(true);
        t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1024.0);
        t.setHealth(1024.0F);
        v.setTarget(t);
        h.succeedWhen(
            () -> h.assertTrue(
                    MobMind.data(v).getInt("CriticalHits") > 0 && t.getHealth() < 1024.0F, "A real jump descends before a critical strike is counted"
                )
        );
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 140,
        batch = "progression"
    )
    public static void master_villager_defeats_fully_enchanted_netherite_player(GameTestHelper h) {
        Villager v = mob(h, EntityType.VILLAGER, 8, 8);
        MobLevels.set(v, 5);
        AdaptiveCombat.arm(v);
        Player p = h.makeMockPlayer(GameType.SURVIVAL);
        p.moveTo(v.getX() + 2.0, v.getY(), v.getZ());
        Enchantment protection = Enchantments.ALL_DAMAGE_PROTECTION;

        for (EquipmentSlot slot : List.of(EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET)) {
            Item item = switch (slot) {
                case HEAD -> Items.NETHERITE_HELMET;
                case CHEST -> Items.NETHERITE_CHESTPLATE;
                case LEGS -> Items.NETHERITE_LEGGINGS;
                default -> Items.NETHERITE_BOOTS;
            };
            ItemStack stack = item.getDefaultInstance();
            stack.enchant(protection, 4);
            p.setItemSlot(slot, stack);
        }

        p.tick();
        h.assertTrue(
            p.getArmorValue() == 20 && p.getItemBySlot(EquipmentSlot.CHEST).isEnchanted(), "Survival player actually wears full Protection-IV netherite"
        );
        v.setTarget(p);
        h.succeedWhen(
            () -> h.assertTrue(
                    !p.isAlive() && MobMind.data(v).getInt("SuccessfulStrikes") > 0 && MobMind.data(v).getInt("Strikes") <= 5,
                    "Native master combat defeats armored survival target within five attacks"
                )
        );
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "progression"
    )
    public static void one_time_level_lottery_has_all_ranks_and_rare_six(GameTestHelper h) {
        int[] counts = new int[7];

        for (int i = 0; i < 100000; i++) {
            counts[MobLevels.initial(new UUID((long)i * 117L, (long)i * 6329L), 5.0E-4)]++;
        }

        for (int i = 1; i <= 5; i++) {
            h.assertTrue(counts[i] > 1000, "All ordinary ranks generated " + i);
        }

        h.assertTrue(counts[6] >= 20 && counts[6] <= 90, "Default elite is approximately one in 2000, actual=" + counts[6]);
        System.out.println("[OROR_LEVELS] lottery=" + Arrays.toString(counts));
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "progression"
    )
    public static void rank_and_elite_do_not_reroll_on_native_reload(GameTestHelper h) {
        Husk m = mob(h, EntityType.HUSK, 8, 8);
        MobLevels.set(m, 6);
        CompoundTag save = new CompoundTag();
        m.saveWithoutId(save);
        Husk copy = (Husk)EntityType.HUSK.create(h.getLevel());
        copy.load(save);
        h.assertTrue(MobLevels.level(copy) == 6 && copy.getUUID().equals(m.getUUID()), "Elite rank and identity persist");
        MobLevels.set(m, 2);
        m.saveWithoutId(save);
        copy.load(save);
        h.assertTrue(MobLevels.level(copy) == 2 && !MobMind.data(copy).getBoolean("Elite"), "Ordinary rank also persists");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "progression"
    )
    public static void every_trade_rank_has_its_actual_armor_and_weapon(GameTestHelper h) {
        double previous = 0.0;

        for (int rank = 1; rank <= 5; rank++) {
            Villager v = mob(h, EntityType.VILLAGER, 8, 8);
            MobLevels.set(v, rank);
            AdaptiveCombat.arm(v);
            Item expected = rank == 1 ? Items.IRON_CHESTPLATE : (rank < 4 ? Items.DIAMOND_CHESTPLATE : Items.NETHERITE_CHESTPLATE);
            h.assertTrue(v.getItemBySlot(EquipmentSlot.CHEST).is(expected) && MobLevels.level(v) == rank, "Trade equipment rank " + rank);
            h.assertTrue(v.getAttribute(Attributes.MAX_HEALTH).getBaseValue() > previous, "Health rises per trade rank " + rank);
            previous = v.getAttribute(Attributes.MAX_HEALTH).getBaseValue();
            if (rank >= 3) {
                h.assertTrue(v.getMainHandItem().isEnchanted() && v.getItemBySlot(EquipmentSlot.CHEST).isEnchanted(), "Real enchantments rank " + rank);
            }

            v.discard();
        }

        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 180,
        batch = "progression"
    )
    public static void trading_promotion_updates_equipment_on_real_ticks(GameTestHelper h) {
        Villager v = mob(h, EntityType.VILLAGER, 8, 8);
        AdaptiveCombat.arm(v);
        h.assertTrue(v.getMainHandItem().is(Items.IRON_SWORD), "Novice iron equipment");
        v.setVillagerData(v.getVillagerData().setProfession(VillagerProfession.FLETCHER).setLevel(5));
        h.succeedWhen(
            () -> h.assertTrue(
                    MobMind.data(v).getInt("LoadoutLevel") == 5 && v.getMainHandItem().is(Items.NETHERITE_SWORD) && v.getMainHandItem().isEnchanted(),
                    "Master promotion changed real held item"
                )
        );
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "progression"
    )
    public static void elite_has_legend_weapon_real_buffs_and_lethal_damage(GameTestHelper h) {
        Husk m = mob(h, EntityType.HUSK, 8, 8);
        m.setNoAi(true);
        MobLevels.set(m, 6);
        MobLevels.refresh(m);
        h.assertTrue(
            m.getMainHandItem().is((Item)CharacterRelics.ITEMS.get("kokuhaku_legend").get()) && m.getItemBySlot(EquipmentSlot.CHEST).isEnchanted(),
            "Elite actually holds rare strongest blade and enchanted netherite"
        );
        m.setHealth(100.0F);
        MobLevels.refresh(m);
        h.assertTrue(
            m.hasEffect(MobEffects.DAMAGE_BOOST) && m.hasEffect(MobEffects.DAMAGE_RESISTANCE) && m.hasEffect(MobEffects.ABSORPTION) && m.getHealth() > 100.0F,
            "Real rank-six buffs include regeneration for immune undead"
        );
        Husk target = mob(h, EntityType.HUSK, 10, 8);
        target.setNoAi(true);
        AdaptiveCombat.strike(m, target, "sword", h.getLevel());
        h.assertTrue(!target.isAlive(), "Elite actual damage kills target");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "progression"
    )
    public static void age_and_learning_improve_rank_reaction_and_aim(GameTestHelper h) {
        Husk m = mob(h, EntityType.HUSK, 8, 8);
        float before = MobLevels.accuracy(m, "bow");
        CompoundTag n = MobMind.data(m);
        n.putLong("LastClock", h.getLevel().getGameTime() - 1440000L);
        MobMind.clock(m);
        MobMind.practice(m, "bow", 100);
        h.assertTrue(
            MobLevels.level(m) == 5 && MobLevels.decisionTicks(m) == 2 && MobLevels.accuracy(m, "bow") < before && MobMind.strength(m) > 4.0,
            "Long lived individual has faster, more accurate and stronger behavior"
        );
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "progression"
    )
    public static void furnace_is_a_real_natural_profession_workstation(GameTestHelper h) {
        Optional<Holder<PoiType>> holder = PoiTypes.forState(Blocks.FURNACE.defaultBlockState());
        h.assertTrue(
            holder.isPresent()
                && holder.get().is(VillagerIndustry.FURNACE_POI.getKey())
                && ((VillagerProfession)VillagerIndustry.MINER.get()).heldJobSite().test(holder.get()),
            "Furnace is registered in actual vanilla POI registry"
        );
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "industry"
    )
    public static void giving_furnace_hires_and_consumes_one_item(GameTestHelper h) {
        Villager v = mob(h, EntityType.VILLAGER, 8, 8);
        BlockPos pos = h.absolutePos(new BlockPos(6, 2, 8));
        h.getLevel().setBlock(pos, Blocks.FURNACE.defaultBlockState(), 3);
        FakePlayer p = FakePlayerFactory.get(h.getLevel(), new GameProfile(UUID.randomUUID(), "IndustryTester"));
        p.moveTo(v.getX() + 1.0, v.getY(), v.getZ());
        p.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.FURNACE, 2));
        EntityInteract event = new EntityInteract(p, InteractionHand.MAIN_HAND, v);
        VillagerIndustry.interact(event);
        h.assertTrue(
            event.isCanceled() && VillagerIndustry.miner(v) && VillagerIndustry.station(v).equals(pos) && p.getMainHandItem().getCount() == 1,
            "Real interaction hires with a supplied furnace"
        );
        h.assertTrue(!v.getOffers().isEmpty(), "Miner has functioning trades");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 700,
        batch = "industry"
    )
    public static void unemployed_villager_claims_placed_furnace_naturally(GameTestHelper h) {
        Villager v = mob(h, EntityType.VILLAGER, 8, 8);
        h.getLevel().setBlock(h.absolutePos(new BlockPos(10, 2, 8)), Blocks.FURNACE.defaultBlockState(), 3);
        h.getLevel().setDayTime(4000L);
        h.succeedWhen(() -> h.assertTrue(VillagerIndustry.miner(v) && VillagerIndustry.station(v) != null, "Vanilla job acquisition found a placed furnace"));
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 1400,
        batch = "industry"
    )
    public static void buried_ore_is_excavated_smelted_and_collected(GameTestHelper h) {
        Villager v = worker(h, 8, 8, 5);
        h.setBlock(11, 2, 8, Blocks.STONE);
        h.setBlock(11, 3, 8, Blocks.STONE);
        h.setBlock(12, 2, 8, Blocks.STONE);
        h.setBlock(13, 2, 8, Blocks.IRON_ORE);
        h.succeedWhen(
            () -> {
                h.assertTrue(
                    VillagerIndustry.data(v).getInt("OresMined") >= 1 && count(box(h, v), Items.IRON_INGOT) == 1,
                    "Actual excavation, transport, coal burning and vanilla recipe: " + VillagerIndustry.status(v) + " pos=" + v.blockPosition()
                );
                h.assertTrue(
                    h.getBlockState(new BlockPos(13, 2, 8)).isAir() && VillagerIndustry.data(v).getInt("BlocksMined") >= 2,
                    "Embedded ore and an obstructing stone block actually disappeared"
                );
                h.assertTrue(count(box(h, v), Items.COAL) < 16, "Real coal was consumed rather than free smelting");
                System.out
                    .println(
                        "[OROR_INDUSTRY] pipeline=PASS mined="
                            + VillagerIndustry.data(v).getInt("BlocksMined")
                            + " products="
                            + VillagerIndustry.data(v).getInt("ProductsCollected")
                    );
            }
        );
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 850,
        batch = "industry"
    )
    public static void no_fuel_waits_then_real_fuel_resumes_smelting(GameTestHelper h) {
        Villager v = worker(h, 8, 8, 2);
        box(h, v).clearContent();
        box(h, v).setItem(0, Items.RAW_IRON.getDefaultInstance());
        h.runAfterDelay(
            210L,
            () -> {
                FurnaceBlockEntity f = (FurnaceBlockEntity)h.getLevel().getBlockEntity(VillagerIndustry.station(v));
                h.assertTrue(
                    f.getItem(0).is(Items.RAW_IRON) && count(box(h, v), Items.IRON_INGOT) == 0 && VillagerIndustry.data(v).getString("State").equals("燃料待ち"),
                    "No fuel means no product"
                );
                box(h, v).setItem(1, Items.COAL.getDefaultInstance());
            }
        );
        h.succeedWhen(() -> h.assertTrue(count(box(h, v), Items.IRON_INGOT) == 1, "Provided actual coal resumed furnace and output collection"));
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "industry"
    )
    public static void full_storage_keeps_products_in_the_real_furnace(GameTestHelper h) {
        Villager v = worker(h, 8, 8, 1);
        v.setNoAi(true);
        ChestBlockEntity box = box(h, v);

        for (int i = 0; i < box.getContainerSize(); i++) {
            box.setItem(i, new ItemStack(Items.DIRT, 64));
        }

        FurnaceBlockEntity f = (FurnaceBlockEntity)h.getLevel().getBlockEntity(VillagerIndustry.station(v));
        f.setItem(2, new ItemStack(Items.IRON_INGOT, 3));
        VillagerIndustry.service(v, f, new SimpleContainer(9), VillagerIndustry.station(v), h.getLevel());
        h.assertTrue(
            f.getItem(2).is(Items.IRON_INGOT) && f.getItem(2).getCount() == 3 && VillagerIndustry.data(v).getString("State").equals("保管場所が満杯"),
            "Full chest preserves product count"
        );
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "industry"
    )
    public static void station_cargo_and_progress_survive_native_save_load(GameTestHelper h) {
        Villager v = worker(h, 8, 8, 4);
        v.setNoAi(true);
        SimpleContainer c = new SimpleContainer(9);
        c.setItem(0, new ItemStack(Items.RAW_GOLD, 3));
        VillagerIndustry.data(v).put("Cargo", c.createTag());
        VillagerIndustry.data(v).putInt("OresMined", 7);
        CompoundTag n = new CompoundTag();
        v.saveWithoutId(n);
        Villager restored = (Villager)EntityType.VILLAGER.create(h.getLevel());
        restored.load(n);
        h.assertTrue(
            VillagerIndustry.miner(restored)
                && VillagerIndustry.station(restored).equals(VillagerIndustry.station(v))
                && count(VillagerIndustry.cargo(restored), Items.RAW_GOLD) == 3
                && VillagerIndustry.data(restored).getInt("OresMined") == 7,
            "Native NBT preserves work and exact materials"
        );
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "industry"
    )
    public static void miners_keep_containers_liquids_and_outside_ores_intact(GameTestHelper h) {
        Villager v = worker(h, 8, 8, 3);
        v.setNoAi(true);
        SimpleContainer c = new SimpleContainer(9);
        ItemStack tool = MobLevels.weapon(v, "pickaxe");
        BlockPos chest = h.absolutePos(new BlockPos(9, 2, 8));
        h.getLevel().setBlock(chest, Blocks.CHEST.defaultBlockState(), 3);
        h.assertTrue(!VillagerIndustry.excavate(v, chest, c, h.getLevel(), tool) && h.getLevel().getBlockState(chest).is(Blocks.CHEST), "Container protected");
        BlockPos ore = h.absolutePos(new BlockPos(9, 2, 10));
        h.getLevel().setBlock(ore, Blocks.IRON_ORE.defaultBlockState(), 3);
        h.getLevel().setBlock(ore.east(), Blocks.LAVA.defaultBlockState(), 3);
        h.assertTrue(!VillagerIndustry.excavate(v, ore, c, h.getLevel(), tool), "Adjacent lava makes drilling stop");
        BlockPos far = h.absolutePos(new BlockPos(60, 2, 8));
        h.getLevel().setBlock(far, Blocks.DIAMOND_ORE.defaultBlockState(), 3);
        h.assertTrue(
            !VillagerIndustry.excavate(v, far, c, h.getLevel(), tool) && h.getLevel().getBlockState(far).is(Blocks.DIAMOND_ORE),
            "Outside assigned range is untouched"
        );
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "industry"
    )
    public static void furnace_claim_and_mob_griefing_prevent_duplicate_work(GameTestHelper h) {
        Villager a = worker(h, 8, 8, 1);
        a.setNoAi(true);
        Villager b = mob(h, EntityType.VILLAGER, 10, 8);
        h.assertTrue(!VillagerIndustry.hire(b, VillagerIndustry.station(a), null), "One furnace cannot be owned by two individuals");
        BlockPos pos = h.absolutePos(new BlockPos(9, 2, 8));
        h.getLevel().setBlock(pos, Blocks.IRON_ORE.defaultBlockState(), 3);
        ((BooleanValue)h.getLevel().getGameRules().getRule(GameRules.RULE_MOBGRIEFING)).set(false, h.getLevel().getServer());
        boolean mined = VillagerIndustry.excavate(a, pos, new SimpleContainer(9), h.getLevel(), MobLevels.weapon(a, "pickaxe"));
        ((BooleanValue)h.getLevel().getGameRules().getRule(GameRules.RULE_MOBGRIEFING)).set(true, h.getLevel().getServer());
        h.assertTrue(!mined && h.getLevel().getBlockState(pos).is(Blocks.IRON_ORE), "Disabled griefing cannot mine");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 1600,
        batch = "industry"
    )
    public static void three_miners_work_simultaneously_without_material_duplication(GameTestHelper h) {
        ArrayList<Villager> workers = new ArrayList<>();

        for (int x : List.of(8, 45, 82)) {
            Villager v = worker(h, x, 8, 5);
            workers.add(v);
            h.setBlock(x + 3, 2, 8, Blocks.IRON_ORE);
        }

        h.succeedWhen(
            () -> {
                int products = 0;

                for (Villager vx : workers) {
                    h.assertTrue(
                        VillagerIndustry.data(vx).getInt("OresMined") == 1 && count(box(h, vx), Items.IRON_INGOT) == 1,
                        "Each independent furnace produced exactly one ingot"
                    );
                    products += count(box(h, vx), Items.IRON_INGOT);
                }

                h.assertTrue(products == 3, "Three ore blocks produced three products");
                System.out.println("[OROR_INDUSTRY] simultaneous=3 products=3 PASS");
            }
        );
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "progression"
    )
    public static void chat_prefix_targets_npc_and_changes_executable_skill(GameTestHelper h) {
        Villager m = mob(h, EntityType.VILLAGER, 8, 8);
        m.setNoAi(true);
        FakePlayer p = FakePlayerFactory.get(h.getLevel(), new GameProfile(UUID.randomUUID(), "ChatTester"));
        p.moveTo(m.getX() + 1.0, m.getY(), m.getZ());
        MobConversation.focus(m, p);
        ServerChatEvent event = new ServerChatEvent(p, "話：空手を鍛えて", Component.literal("話：空手を鍛えて"));
        MobConversation.chat(event);
        h.assertTrue(
            event.isCanceled() && MobMind.stance(m).equals("unarmed") && MobMind.skill(m, "unarmed") >= 12,
            "Actual chat event routes into persistent combat training"
        );
        h.succeed();
    }
}
