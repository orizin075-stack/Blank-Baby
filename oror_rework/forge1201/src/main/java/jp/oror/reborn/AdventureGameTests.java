package jp.oror.reborn;

import com.mojang.authlib.GameProfile;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.animal.Cow;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.ItemLike;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.common.util.FakePlayer;
import net.minecraftforge.common.util.FakePlayerFactory;
import net.minecraftforge.event.entity.player.PlayerEvent.Clone;
import net.minecraftforge.event.entity.player.PlayerInteractEvent.RightClickBlock;
import net.minecraftforge.event.TickEvent.PlayerTickEvent;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

@GameTestHolder("oror_supreme_bosses")
@PrefixGameTestTemplate(false)
public final class AdventureGameTests {
    private static final List<String> NEW = List.of(
        "innocence", "brutality", "cursed_love", "relentless_research", "forbidden_arcana", "fallen_savior", "sweet_pact"
    );

    private static SupremeEntity mob(GameTestHelper h, String id, int x, int z) {
        SupremeEntity b = (SupremeEntity)((EntityType)OrorReborn.TYPES.get(id).get()).create(h.getLevel());
        BlockPos at = h.absolutePos(new BlockPos(x, 2, z));
        b.moveTo((double)at.getX() + 0.5, (double)at.getY(), (double)at.getZ() + 0.5, 0.0F, 0.0F);
        h.getLevel().addFreshEntity(b);
        return b;
    }

    private static ServerPlayer player(GameTestHelper h) {
        FakePlayer p = FakePlayerFactory.get(h.getLevel(), new GameProfile(UUID.randomUUID(), "OROR_Test"));
        p.setGameMode(GameType.SURVIVAL);
        BlockPos at = h.absolutePos(new BlockPos(8, 2, 8));
        p.moveTo((double)at.getX() + 0.5, (double)at.getY(), (double)at.getZ() + 0.5, 0.0F, 0.0F);
        return p;
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "adventure"
    )
    public static void placement_follows_biography(GameTestHelper h) {
        h.assertTrue(EncounterRules.WANDERERS.size() == 14 && EncounterRules.WANDERERS.contains("mels"), "Mels wanders");
        h.assertTrue(!EncounterRules.dungeon("sweet_pact") && !EncounterRules.WANDERERS.contains("sweet_pact"), "Pact is special only");
        h.assertTrue(CharacterSpec.ALL.keySet().stream().filter(EncounterRules::dungeon).count() == 26L, "26 dungeon residents");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "adventure"
    )
    public static void seven_new_types_save_and_restore(GameTestHelper h) {
        for (String id : NEW) {
            SupremeEntity b = mob(h, id, 5, 8);
            b.setForm(3);
            b.loreEvolution = 12345L;
            b.loreAdaptation.add("minecraft:magic");
            CompoundTag n = new CompoundTag();
            b.addAdditionalSaveData(n);
            SupremeEntity c = mob(h, id, 16, 8);
            c.readAdditionalSaveData(n);
            h.assertTrue(c.form() == 3 && c.loreEvolution == 12345L && c.loreAdaptation.contains("minecraft:magic"), "Lore state persists " + id);
            b.discard();
            c.discard();
        }

        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "adventure"
    )
    public static void lore_revives_beyond_balanced_limit(GameTestHelper h) {
        ArrayList<String> ids = new ArrayList<>(NEW);
        ids.addAll(List.of("mels", "hakyoku", "mary_sue"));

        for (String id : ids) {
            SupremeEntity b = mob(h, id, 8, 8);

            for (int i = 0; i < 8; i++) {
                b.setHealth(0.0F);
                b.die(b.damageSources().generic());
            }

            h.assertTrue(b.isAlive() && b.revivals == 8, "Unlimited lore revival " + id);
            b.discard();
        }

        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "adventure"
    )
    public static void lore_erasure_and_permanent_adaptation(GameTestHelper h) {
        SupremeEntity b = mob(h, "kokuhaku", 5, 8);
        Zombie z = (Zombie)EntityType.ZOMBIE.create(h.getLevel());
        BlockPos at = h.absolutePos(new BlockPos(10, 2, 8));
        z.moveTo((double)at.getX(), (double)at.getY(), (double)at.getZ());
        h.getLevel().addFreshEntity(z);
        b.setTarget(z);
        LorePowers.strike(b, z, 1.0F, true);
        h.assertTrue(!z.isAlive() && z.getPersistentData().getBoolean("ororErased"), "Existence erasure");
        SupremeEntity guard = mob(h, "savior", 6, 8);
        Cow cow = (Cow)EntityType.COW.create(h.getLevel());
        cow.moveTo((double)at.getX(), (double)at.getY(), (double)at.getZ());
        h.getLevel().addFreshEntity(cow);
        b.setTarget(cow);
        LorePowers.strike(b, cow, 1.0F, true);
        h.assertTrue(cow.isAlive(), "Lore sanctuary rejects erasure");
        guard.discard();
        cow.discard();
        SupremeEntity a = mob(h, "hakyoku", 18, 8);
        a.hurt(a.damageSources().magic(), 10.0F);
        float hp = a.getHealth();
        a.invulnerableTime = 0;
        a.hurt(a.damageSources().magic(), 100000.0F);
        h.assertTrue(a.getHealth() == hp, "Second attack permanently refused");
        SupremeEntity t = mob(h, "taika", 25, 8);
        t.hurt(t.damageSources().magic(), 1000000.0F);
        h.assertTrue(t.isAlive() && (double)t.getHealth() > (double)t.getMaxHealth() * 0.9, "Taika surpasses incoming force");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "adventure"
    )
    public static void relic_equipment_has_native_attributes(GameTestHelper h) {
        h.assertTrue(
            AdventureContent.CONTENT.size() == 18 && AdventureContent.BLADE.get() instanceof SwordItem && AdventureContent.COAT.get() instanceof ArmorItem,
            "Native equipment registered"
        );
        ServerPlayer p = player(h);
        ItemStack boots = ((ArmorItem)AdventureContent.BOOTS.get()).getDefaultInstance();
        ItemStack coat = ((ArmorItem)AdventureContent.COAT.get()).getDefaultInstance();
        p.setItemSlot(EquipmentSlot.FEET, boots);
        p.setItemSlot(EquipmentSlot.CHEST, coat);
        p.tickCount = 20;
        p.setHealth(10.0F);
        ((ArmorItem)AdventureContent.BOOTS.get()).inventoryTick(boots, h.getLevel(), p, 0, false);
        ((ArmorItem)AdventureContent.COAT.get()).inventoryTick(coat, h.getLevel(), p, 0, false);
        h.assertTrue(
            p.hasEffect(MobEffects.MOVEMENT_SPEED) && p.hasEffect(MobEffects.FIRE_RESISTANCE) && p.getHealth() > 10.0F, "Equipment effects activate when worn"
        );
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "adventure"
    )
    public static void consumables_repair_and_mana_work(GameTestHelper h) {
        ServerPlayer p = player(h);
        p.getInventory().clearContent();
        ItemStack sword = Items.DIAMOND_SWORD.getDefaultInstance();
        sword.setDamageValue(100);
        p.getInventory().items.set(1, sword);
        p.setItemInHand(InteractionHand.MAIN_HAND, ((Item)AdventureContent.TOOL.get()).getDefaultInstance());
        ((Item)AdventureContent.TOOL.get()).use(h.getLevel(), p, InteractionHand.MAIN_HAND);
        h.assertTrue(sword.getDamageValue() == 36, "Repair restores 64 durability");
        p.addEffect(new MobEffectInstance(MobEffects.WITHER, 200, 1));
        p.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack((ItemLike)AdventureContent.DEW.get(), 2));
        ((Item)AdventureContent.DEW.get()).use(h.getLevel(), p, InteractionHand.MAIN_HAND);
        h.assertTrue(!p.hasEffect(MobEffects.WITHER) && p.getMainHandItem().getCount() == 1, "Dew cleanses and consumes one");
        SupremeEntity b = mob(h, "elseria", 12, 8);
        b.mana(0.0F);
        p.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack((ItemLike)AdventureContent.MANA.get(), 2));
        b.mobInteract(p, InteractionHand.MAIN_HAND);
        h.assertTrue(b.mana() == b.manaCap() && p.getMainHandItem().getCount() == 1, "NPC mana dose");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "adventure"
    )
    public static void pact_is_conditional_and_requires_signature(GameTestHelper h) {
        ServerPlayer p = player(h);
        p.setHealth(p.getMaxHealth());
        h.assertTrue(!EncounterRules.pactEligible(p), "Healthy players do not trigger pact");
        p.setHealth(4.0F);
        h.assertTrue(EncounterRules.pactEligible(p), "Low health triggers pact");
        p.getPersistentData().putLong("ororPactNextVisit", h.getLevel().getGameTime() + 24000L);
        h.assertTrue(!EncounterRules.pactEligible(p), "Visit cooldown");
        SupremeEntity b = EncounterRules.spawn(h.getLevel(), "sweet_pact", p.blockPosition(), 6);
        h.assertTrue(b != null, "Special visitor can spawn near player");
        p.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.EMERALD, 2));
        PactSystem.interact(b, p);
        h.assertTrue(p.getPersistentData().getInt("ororPactDebt") == 0 && p.getMainHandItem().getCount() == 2, "Conversation never signs");
        p.setShiftKeyDown(true);
        PactSystem.interact(b, p);
        h.assertTrue(p.getPersistentData().getInt("ororPactDebt") == 1 && p.getHealth() == p.getMaxHealth(), "Explicit signature gives relief");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "adventure"
    )
    public static void pact_debt_survives_death_and_applies_cost(GameTestHelper h) {
        ServerPlayer old = player(h);
        ServerPlayer next = player(h);
        old.getPersistentData().putInt("ororPactDebt", 8);
        old.getPersistentData().putLong("ororPactNextVisit", 123456L);
        PactSystem.clone(new Clone(next, old, true));
        next.tickCount = 40;
        PactSystem.tick(new PlayerTickEvent(net.minecraftforge.event.TickEvent.Phase.END, next));
        h.assertTrue(
            next.getPersistentData().getInt("ororPactDebt") == 8
                && next.getPersistentData().getLong("ororPactNextVisit") == 123456L
                && next.hasEffect(MobEffects.WEAKNESS)
                && next.hasEffect(MobEffects.MOVEMENT_SLOWDOWN),
            "Death preserves debt and recurring cost"
        );
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "adventure"
    )
    public static void rewind_talisman_prevents_lethal_hit(GameTestHelper h) {
        Player p = h.makeMockPlayer();
        p.setHealth(4.0F);
        p.setItemInHand(InteractionHand.OFF_HAND, ((Item)AdventureContent.TALISMAN.get()).getDefaultInstance());
        p.hurt(p.damageSources().generic(), 1000.0F);
        h.assertTrue(p.isAlive() && p.getHealth() == p.getMaxHealth() && p.getOffhandItem().isEmpty(), "Fatal hit canceled, talisman consumed");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "adventure"
    )
    public static void boss_gate_requires_and_consumes_key(GameTestHelper h) {
        ServerPlayer p = player(h);
        BlockPos at = h.absolutePos(new BlockPos(18, 1, 18));
        h.getLevel().setBlock(at, ((Block)AdventureContent.GATES.get("sword_gate").get()).defaultBlockState(), 3);
        p.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
        AdventureContent.gate(new RightClickBlock(p, InteractionHand.MAIN_HAND, at, new BlockHitResult(Vec3.atCenterOf(at), Direction.UP, at, false)));
        h.assertTrue(!h.getLevel().getBlockState(at).isAir(), "No key, no entry");
        p.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack((ItemLike)AdventureContent.KEY.get(), 2));
        AdventureContent.gate(new RightClickBlock(p, InteractionHand.MAIN_HAND, at, new BlockHitResult(Vec3.atCenterOf(at), Direction.UP, at, false)));
        h.assertTrue(
            h.getLevel().getBlockState(at).isAir()
                && p.getMainHandItem().getCount() == 1
                && !h.getLevel()
                    .getEntitiesOfClass(SupremeEntity.class, new AABB(at).inflate(5.0), b -> b.spec.id.equals("kokuhaku") && b.arena && b.getTarget() == p)
                    .isEmpty(),
            "Key consumed once and arena boss released"
        );
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "adventure"
    )
    public static void dragon_furnace_has_tens_of_millions(GameTestHelper h) {
        SupremeEntity b = mob(h, "huang_linghua", 8, 8);
        h.assertTrue(b.soulHealth == 5.0E7F && b.mana() == 3.0E7F, "Large virtual HP and MP");
        b.spend(1000.0F);
        b.hurt(b.damageSources().magic(), 1000.0F);
        h.assertTrue(b.soulHealth < 5.0E7F && (double)b.getHealth() > (double)b.getMaxHealth() * 0.99, "Real reservoir takes proportional damage");
        CompoundTag n = new CompoundTag();
        b.addAdditionalSaveData(n);
        SupremeEntity c = mob(h, "huang_linghua", 18, 8);
        c.readAdditionalSaveData(n);
        h.assertTrue(c.soulHealth == b.soulHealth && c.mana() == b.mana(), "Large reservoirs survive NBT");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "adventure"
    )
    public static void major_dungeons_place_and_resolve_loot(GameTestHelper h) {
        int i = 0;

        for (String id : List.of("sword_sanctum", "forbidden_laboratory", "tragedy_theatre")) {
            ServerLevel sl = h.getLevel();
            BlockPos at = h.absolutePos(new BlockPos(40 + i * 45, 2, 0));

            for (int x = at.getX() >> 4; x <= at.getX() + 37 >> 4; x++) {
                for (int z = at.getZ() >> 4; z <= at.getZ() + 37 >> 4; z++) {
                    sl.getChunk(x, z);
                }
            }

            Optional<StructureTemplate> t = sl.getStructureManager().get(new ResourceLocation("oror_supreme_bosses", id));
            h.assertTrue(t.isPresent(), "Template registered " + id);
            h.assertTrue(t.get().placeInWorld(sl, at, at, new StructurePlaceSettings(), sl.random, 2), "Dungeon placed " + id);
            BlockEntity chest = sl.getBlockEntity(at.offset(4, 1, 4));
            h.assertTrue(chest instanceof ChestBlockEntity, "Chest exists " + id);
            ((ChestBlockEntity)chest).unpackLootTable(null);
            h.assertTrue(!((ChestBlockEntity)chest).isEmpty(), "Loot resolved " + id);
            h.assertTrue(!sl.getBlockState(at.offset(18, 1, 20)).isAir(), "Gate exists " + id);
            i++;
        }

        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 500,
        batch = "adventure"
    )
    public static void all_41_lore_fight_together(GameTestHelper h) {
        ArrayList<SupremeEntity> group = new ArrayList<>();
        int i = 0;

        for (CharacterSpec s : CharacterSpec.ALL.values()) {
            int x = 3 + i % 6 * 4;
            int z = 3 + i / 6 * 4;
            SupremeEntity b = mob(h, s.id, x, z);
            SupremeEntity t = mob(h, "innocence", x + 1, z);
            t.setNoAi(true);
            t.arena = true;
            b.setTarget(t);
            b.cooldown = 0;
            group.add(b);
            i++;
        }

        h.runAfterDelay(6L, () -> {
            long n = group.stream().filter(bx -> bx.mana() < bx.manaCap()).count();
            System.out.println("[OROR_LORE_CONCURRENT] firstCasts=" + n + " tick=6");
            h.assertTrue(n == 41L, "41 lore actors execute native AI casts");
        });
        h.runAfterDelay(
            400L,
            () -> {
                for (SupremeEntity bx : group) {
                    if (!bx.isAlive()) {
                        System.out
                            .println(
                                "[OROR_LORE_STATE] id="
                                    + bx.spec.id
                                    + " hp="
                                    + bx.getHealth()
                                    + " at="
                                    + bx.position()
                                    + " removed="
                                    + bx.isRemoved()
                                    + " damage="
                                    + bx.getLastDamageSource()
                            );
                    }

                    h.assertTrue(
                        bx.isAlive() && Double.isFinite(bx.getX()) && Double.isFinite(bx.getY()) && Float.isFinite(bx.mana()) && Float.isFinite(bx.soulHealth),
                        "Live finite lore actor " + bx.spec.id
                    );
                }

                System.out
                    .println(
                        "[OROR_LORE_CONCURRENT] simulatedTicks=400 alive="
                            + group.size()
                            + " avgTickMs="
                            + (double)h.getLevel().getServer().getAverageTickTime()
                    );
                h.succeed();
            }
        );
    }
}
