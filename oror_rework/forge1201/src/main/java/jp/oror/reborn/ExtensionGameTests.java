package jp.oror.reborn;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.List;
import java.util.Random;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Husk;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.npc.VillagerProfession;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.AxeItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.GameRules.BooleanValue;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

@GameTestHolder("oror_supreme_bosses")
@PrefixGameTestTemplate(false)
public final class ExtensionGameTests {
    private static <T extends Mob> T mob(GameTestHelper h, EntityType<T> type, int x, int z) {
        T m = (T)type.create(h.getLevel());
        BlockPos p = h.absolutePos(new BlockPos(x, 2, z));
        m.moveTo((double)p.getX() + 0.5, (double)p.getY(), (double)p.getZ() + 0.5, 0.0F, 0.0F);
        m.setPersistenceRequired();
        h.getLevel().addFreshEntity(m);
        MobLevels.set(m, 1);
        return m;
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 120,
        batch = "extension"
    )
    public static void professions_produce_distinct_actual_equipment_and_health(GameTestHelper h) {
        Husk t = mob(h, EntityType.HUSK, 12, 8);
        t.setNoAi(true);
        HashSet<Item> weapons = new HashSet<>();
        HashSet<Double> health = new HashSet<>();

        for (VillagerProfession job : List.of(
            VillagerProfession.ARMORER,
            VillagerProfession.WEAPONSMITH,
            VillagerProfession.TOOLSMITH,
            VillagerProfession.FLETCHER,
            VillagerProfession.CLERIC,
            VillagerProfession.LIBRARIAN,
            VillagerProfession.FISHERMAN,
            VillagerProfession.FARMER,
            VillagerProfession.BUTCHER,
            VillagerProfession.CARTOGRAPHER,
            VillagerProfession.LEATHERWORKER,
            VillagerProfession.MASON,
            VillagerProfession.SHEPHERD
        )) {
            Villager v = mob(h, EntityType.VILLAGER, 8, 8);
            v.setNoAi(true);
            v.setVillagerData(v.getVillagerData().setProfession(job).setLevel(5));
            MobLevels.set(v, 5);
            MobLevels.refresh(v);
            VillagerRoles.refresh(v);
            AdaptiveCombat.select(v, t, 2.0);
            weapons.add(v.getMainHandItem().getItem());
            health.add(v.getAttributeValue(Attributes.MAX_HEALTH));
            h.assertTrue(MobMind.data(v).contains("ProfessionApplied"), "Profession applied " + job);
            v.discard();
        }

        h.assertTrue(weapons.size() >= 5 && health.size() >= 3, "Actual professions produce different weapons and health");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "extension"
    )
    public static void combat_outcomes_change_the_next_actual_weapon(GameTestHelper h) {
        Villager v = mob(h, EntityType.VILLAGER, 8, 8);
        v.setNoAi(true);
        MobLevels.set(v, 5);
        Husk t = mob(h, EntityType.HUSK, 10, 8);
        t.setNoAi(true);
        String context = TacticalLearning.context(v, t);

        for (int i = 0; i < 8; i++) {
            TacticalLearning.outcome(v, context, "sword", false);
            TacticalLearning.outcome(v, context, "axe", true);
        }

        AdaptiveCombat.select(v, t, 2.0);
        h.assertTrue(
            v.getMainHandItem().getItem() instanceof AxeItem && MobMind.data(v).getString("LearnedChoice").equals("axe"),
            "Outcome table selects successful actual weapon"
        );
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 200,
        batch = "extension"
    )
    public static void private_history_survives_recent_memory_limit(GameTestHelper h) {
        Villager m = mob(h, EntityType.VILLAGER, 8, 8);
        m.setNoAi(true);
        UUID a = UUID.randomUUID();
        UUID b = UUID.randomUUID();

        for (int i = 0; i < 40; i++) {
            DialogueArchive.record(m, a, "青い花の記憶 " + i, "庭で育てよう " + i, "花");
        }

        DialogueArchive.record(m, b, "他人だけの秘密", "秘密の返答", "秘密");
        Path file = DialogueArchive.file(m);
        CompletableFuture<String[]> future = CompletableFuture.supplyAsync(() -> {
            if (!DialogueArchive.flush(3000L)) {
                throw new IllegalStateException("Journal did not flush");
            } else {
                try {
                    return new String[]{Long.toString(Files.lines(file).count()), DialogueArchive.retrieve(file, a, "青い花")};
                } catch (IOException var3x) {
                    throw new CompletionException(var3x);
                }
            }
        });
        h.succeedWhen(() -> {
            h.assertTrue(future.isDone(), "History worker finished");
            String[] result = future.join();
            h.assertTrue(result[0].equals("41") && result[1].contains("青い花") && !result[1].contains("秘密"), "All 41 records saved and player memories isolated");
        });
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 160,
        batch = "extension"
    )
    public static void rank_rewards_increase_and_native_death_pays_once(GameTestHelper h) {
        int prev = 0;

        for (int rank = 1; rank <= 6; rank++) {
            int count = LevelRewards.rewards(rank, new Random(1L), false).stream().filter(s -> s.is(Items.EMERALD)).mapToInt(ItemStack::getCount).sum();
            h.assertTrue(count > prev, "Guaranteed reward increases " + rank);
            prev = count;
        }

        Husk m = mob(h, EntityType.HUSK, 8, 8);
        m.setNoAi(true);
        MobLevels.set(m, 6);
        Player p = h.makeMockPlayer(GameType.SURVIVAL);
        p.moveTo(m.getX() + 1.0, m.getY(), m.getZ());
        m.hurt(p.damageSources().playerAttack(p), 1000000.0F);
        h.succeedWhen(
            () -> h.assertTrue(
                    h.getLevel()
                            .getEntitiesOfClass(ItemEntity.class, m.getBoundingBox().inflate(5.0), i -> i.getItem().is(Items.EMERALD))
                            .stream()
                            .mapToInt(i -> i.getItem().getCount())
                            .sum()
                        == 48,
                    "Rank-six real death paid 48 emeralds"
                )
        );
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "extension"
    )
    public static void themed_spawner_guard_loads_role_rank_and_save(GameTestHelper h) {
        CitadelGuard m = (CitadelGuard)((EntityType)LegacyContent.DUNGEON.get()).create(h.getLevel());
        CompoundTag n = new CompoundTag();
        n.putString("DungeonKind", "miyohime");
        n.putInt("DungeonRole", 1);
        n.putInt("DungeonLevel", 5);
        m.load(n);
        h.assertTrue(
            m.theme().equals("miyohime") && MobLevels.level(m) == 5 && m.getMainHandItem().is(Items.BOW), "Spawner NBT affects actual theme rank weapon"
        );
        m.saveWithoutId(n);
        CitadelGuard copy = (CitadelGuard)((EntityType)LegacyContent.DUNGEON.get()).create(h.getLevel());
        copy.load(n);
        h.assertTrue(
            copy.theme().equals("miyohime") && MobLevels.level(copy) == 5 && copy.getItemBySlot(EquipmentSlot.CHEST).is(Items.LEATHER_CHESTPLATE),
            "Native save preserves theme equipment"
        );
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "extension"
    )
    public static void boss_proximity_chests_have_richer_actual_loot(GameTestHelper h) {
        if (ModList.get().isLoaded("wom")) {
            for (String id : List.of("agony", "herrscher", "ruine", "moonless", "solar", "antitheus")) {
                h.assertTrue(
                    BuiltInRegistries.ITEM.get(new ResourceLocation("wom", id)) != Items.AIR, "Optional miracle weapon registered " + id
                );
            }
        }

        ServerLevel sl = h.getLevel();
        BlockPos at = h.absolutePos(new BlockPos(40, 2, 0));

        for (int x = at.getX() >> 4; x <= at.getX() + 37 >> 4; x++) {
            for (int z = at.getZ() >> 4; z <= at.getZ() + 37 >> 4; z++) {
                sl.getChunk(x, z);
            }
        }

        StructureTemplate template = (StructureTemplate)sl.getStructureManager()
            .get(new ResourceLocation("oror_supreme_bosses", "sword_sanctum"))
            .orElseThrow();
        h.assertTrue(template.placeInWorld(sl, at, at, new StructurePlaceSettings(), sl.random, 2), "Template placed");
        ChestBlockEntity outer = (ChestBlockEntity)sl.getBlockEntity(at.offset(4, 1, 4));
        ChestBlockEntity inner = (ChestBlockEntity)sl.getBlockEntity(at.offset(16, 1, 18));
        outer.unpackLootTable(null);
        inner.unpackLootTable(null);
        int a = 0;
        int b = 0;

        for (int i = 0; i < 27; i++) {
            if (outer.getItem(i).is(Items.DIAMOND)) {
                a += outer.getItem(i).getCount();
            }

            if (inner.getItem(i).is(Items.DIAMOND)) {
                b += inner.getItem(i).getCount();
            }
        }

        h.assertTrue(a == 1 && b == 12, "Real entrance/boss chest diamonds are 1/12");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "extension"
    )
    public static void skilled_mob_places_actual_water_before_landing(GameTestHelper h) {
        Villager m = mob(h, EntityType.VILLAGER, 8, 8);
        m.setNoAi(true);
        MobLevels.set(m, 5);

        for (int x = 7; x <= 9; x++) {
            for (int z = 7; z <= 9; z++) {
                h.setBlock(x, 1, z, Blocks.STONE);
            }
        }

        m.moveTo(m.getX(), m.getY() + 2.0, m.getZ());
        m.setOnGround(false);
        m.fallDistance = 8.0F;
        m.setDeltaMovement(0.0, -1.0, 0.0);
        BooleanValue rule = (BooleanValue)h.getLevel().getGameRules().getRule(GameRules.RULE_MOBGRIEFING);
        boolean old = rule.get();
        rule.set(true, h.getLevel().getServer());
        TerrainPlay.fallRescue(m, h.getLevel());
        rule.set(old, h.getLevel().getServer());
        h.assertTrue(
            MobMind.data(m).getInt("LandingRescues") > 0 && h.getBlockState(new BlockPos(8, 2, 8)).is(Blocks.WATER),
            "A real water source rescues the descending mob"
        );
        float hp = m.getHealth();
        h.runAfterDelay(10L, () -> {
            h.assertTrue(m.getHealth() >= hp, "Landing avoided damage");
            h.succeed();
        });
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "extension"
    )
    public static void original_parry_and_execution_work_on_native_damage(GameTestHelper h) {
        Player p = h.makeMockPlayer(GameType.SURVIVAL);
        Husk t = mob(h, EntityType.HUSK, 8, 8);
        t.setNoAi(true);
        p.moveTo(t.getX() + 1.0, t.getY(), t.getZ());
        p.setItemInHand(InteractionHand.MAIN_HAND, ((Item)NightfallArsenal.PARRY.get()).getDefaultInstance());
        ((Item)NightfallArsenal.PARRY.get()).use(h.getLevel(), p, InteractionHand.MAIN_HAND);
        float hp = p.getHealth();
        p.hurt(t.damageSources().mobAttack(t), 10.0F);
        h.assertTrue(p.getHealth() == hp && !t.isAlive(), "Timed parry canceled real damage and counterattacked");
        Husk target = mob(h, EntityType.HUSK, 10, 8);
        target.setNoAi(true);
        target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1024.0);
        target.setHealth(256.0F);
        p.setItemInHand(InteractionHand.MAIN_HAND, ((Item)NightfallArsenal.RAPIER.get()).getDefaultInstance());
        ((Item)NightfallArsenal.RAPIER.get()).use(h.getLevel(), p, InteractionHand.MAIN_HAND);
        h.assertTrue(!target.isAlive(), "Execution killed wounded native target");
        h.succeed();
    }
}
