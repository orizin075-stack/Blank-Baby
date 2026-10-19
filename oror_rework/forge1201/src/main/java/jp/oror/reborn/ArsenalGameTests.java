package jp.oror.reborn;

import com.google.gson.JsonObject;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Husk;
import net.minecraft.world.entity.projectile.Arrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.GameRules.BooleanValue;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CropBlock;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

@GameTestHolder("oror_supreme_bosses")
@PrefixGameTestTemplate(false)
public final class ArsenalGameTests {
    private static SupremeEntity boss(GameTestHelper h, String id, boolean lore) {
        SupremeEntity b = (SupremeEntity)((EntityType)OrorReborn.TYPES.get(id).get()).create(h.getLevel());
        BlockPos p = h.absolutePos(new BlockPos(8, 3, 8));
        b.moveTo((double)p.getX() + 0.5, (double)p.getY(), (double)p.getZ() + 0.5, 0.0F, 0.0F);
        b.balanced = !lore;
        b.arena = true;
        b.setNoAi(true);
        h.getLevel().addFreshEntity(b);
        b.setHealth(b.getMaxHealth() * 0.5F);
        b.mana(1.0F);
        return b;
    }

    private static Mob target(GameTestHelper h, SupremeEntity b) {
        Husk t = (Husk)EntityType.HUSK.create(h.getLevel());
        t.moveTo(b.getX() + 3.0, b.getY(), b.getZ(), 0.0F, 0.0F);
        t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1024.0);
        t.setHealth(1024.0F);
        t.setNoAi(true);
        t.setPersistenceRequired();
        t.setItemInHand(InteractionHand.MAIN_HAND, Items.DIAMOND_AXE.getDefaultInstance());
        h.getLevel().addFreshEntity(t);
        b.setTarget(t);
        return t;
    }

    private static String state(SupremeEntity b, Mob t) {
        return b.getHealth()
            + ":"
            + b.shield
            + ":"
            + b.form()
            + ":"
            + b.evolution
            + ":"
            + b.position()
            + ":"
            + b.getMainHandItem()
            + ":"
            + b.targetSpecies
            + ":"
            + t.getHealth()
            + ":"
            + t.getActiveEffects().size()
            + ":"
            + t.getDeltaMovement()
            + ":"
            + t.getPersistentData().getLong("ororFreezeUntil")
            + ":"
            + t.getPersistentData().getLong("ororGameUntil")
            + ":"
            + t.getPersistentData().getLong("OrorSilencedUntil")
            + ":"
            + t.getScale();
    }

    private static long familiars(SupremeEntity b) {
        return (long)b.level().getEntitiesOfClass(FamiliarEntity.class, b.getBoundingBox().inflate(24.0), f -> b.getUUID().equals(f.creator)).size();
    }

    private static void clean(SupremeEntity b, Mob t) {
        for (FamiliarEntity f : b.level().getEntitiesOfClass(FamiliarEntity.class, b.getBoundingBox().inflate(64.0), fx -> b.getUUID().equals(fx.creator))) {
            f.discard();
        }

        b.discard();
        t.discard();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 120,
        batch = "arsenal"
    )
    public static void all_41_primary_attacks_all_four_branches_have_native_effects(GameTestHelper h) {
        int tested = 0;

        for (CharacterSpec spec : CharacterSpec.ALL.values()) {
            for (int phase = 0; phase < 4; phase++) {
                SupremeEntity b = boss(h, spec.id, false);
                Mob t = target(h, b);
                b.tickCount = phase * spec.cooldown;
                b.mana(b.manaCap());
                String before = state(b, t);
                long summons = familiars(b);
                Abilities.cast(b, h.getLevel(), t);
                h.assertTrue(!state(b, t).equals(before) || familiars(b) > summons, "Primary has an actual effect: " + spec.id + " branch " + phase);
                JsonObject row = new JsonObject();
                row.addProperty("character", spec.id);
                row.addProperty("mode", "primary");
                row.addProperty("branch", phase);
                row.addProperty("target_health", t.getHealth());
                row.addProperty("effects", t.getActiveEffects().size());
                row.addProperty("shield", b.shield);
                System.out.println("[OROR_ABILITY_CHECK] " + row);
                clean(b, t);
                tested++;
            }
        }

        h.assertTrue(tested == 164, "All 41 primary attacks and time-selected branches exercised");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 240,
        batch = "arsenal"
    )
    public static void all_123_new_techniques_affect_native_targets_and_support(GameTestHelper h) {
        int delay = 0;
        int[] count = new int[]{0};

        for (CharacterSpec spec : CharacterSpec.ALL.values()) {
            for (int index = 0; index < 3; index++) {
                int i = index;
                h.runAfterDelay(
                    (long)(++delay),
                    () -> {
                        SupremeEntity b = boss(h, spec.id, false);
                        Mob t = target(h, b);
                        b.mana(50.0F);
                        CharacterArsenal.Skill skill = CharacterArsenal.ALL.get(spec.id).get(i);
                        if (skill.mechanic().equals("MANA")) {
                            b.mana(30.0F);
                        }

                        if (skill.mechanic().equals("SEAL")) {
                            t.setHealth(900.0F);
                        }

                        if (skill.mechanic().equals("REPAIR")) {
                            ItemStack damaged = Items.DIAMOND_SWORD.getDefaultInstance();
                            damaged.setDamageValue(100);
                            b.setItemInHand(InteractionHand.MAIN_HAND, damaged);
                        }

                        BlockPos crop = b.blockPosition().east(2);
                        if (skill.mechanic().equals("GROW")) {
                            ((BooleanValue)h.getLevel().getGameRules().getRule(GameRules.RULE_MOBGRIEFING)).set(true, h.getLevel().getServer());
                            h.getLevel().setBlock(crop.below(), Blocks.FARMLAND.defaultBlockState(), 3);
                            h.getLevel().setBlock(crop, Blocks.WHEAT.defaultBlockState(), 3);
                        }

                        if (skill.mechanic().equals("WEATHER")) {
                            b.addEffect(new MobEffectInstance(MobEffects.POISON, 200, 0));
                        }

                        float health = b.getHealth();
                        float mana = b.mana();
                        String before = state(b, t);
                        long summons = familiars(b);
                        Arrow arrow = (Arrow)EntityType.ARROW.create(h.getLevel());
                        arrow.moveTo(b.getX() + 1.0, b.getEyeY(), b.getZ());
                        arrow.setOwner(t);
                        arrow.setDeltaMovement(-1.0, 0.0, 0.0);
                        h.getLevel().addFreshEntity(arrow);
                        boolean cast = CharacterArsenal.cast(b, h.getLevel(), t, i);
                        boolean changed = !state(b, t).equals(before)
                            || familiars(b) > summons
                            || skill.mechanic().equals("MANA") && b.mana() > mana
                            || skill.mechanic().equals("REFLECT") && arrow.getOwner() == b && arrow.getDeltaMovement().x > 0.0;
                        h.assertTrue(cast && changed, "Actual technique effect " + spec.id + " / " + skill.name());
                        String row = skill.mechanic();
                        switch (row) {
                            case "SUMMON":
                                h.assertTrue(familiars(b) > summons, "Actual owned familiar spawned for " + spec.id);
                                break;
                            case "REPAIR":
                                h.assertTrue(b.getMainHandItem().getDamageValue() == 60, "Actual weapon repaired by exactly 40 durability");
                                break;
                            case "REFLECT":
                                h.assertTrue(arrow.getOwner() == b && arrow.getDeltaMovement().x > 0.0, "Projectile owner and direction changed");
                                break;
                            case "TOY":
                                h.assertTrue((double)Math.abs(t.getScale() - 0.15F) < 0.001, "Real target hitbox scale changed");
                                break;
                            case "SEAL":
                                t.heal(20.0F);
                                h.assertTrue(
                                    t.getHealth() == 900.0F && t.getPersistentData().getLong("OrorSilencedUntil") > h.getLevel().getGameTime(),
                                    "Native healing blocked while sealed"
                                );
                                break;
                            case "HEAL":
                            case "FATE":
                            case "DRAIN":
                                h.assertTrue(b.getHealth() > health, "Actual caster health restored");
                                break;
                            case "GROW":
                                h.assertTrue(
                                    h.getLevel().getBlockState(crop).is(Blocks.WHEAT) && (Integer)h.getLevel().getBlockState(crop).getValue(CropBlock.AGE) == 7,
                                    "Real crop matured"
                                );
                                break;
                            case "WEATHER":
                                h.assertTrue(!b.hasEffect(MobEffects.POISON), "Native harmful effect cleansed");
                        }

                        h.assertTrue(b.motion() == skill.motion(), "Intended synchronized motion");
                        JsonObject row = new JsonObject();
                        row.addProperty("character", spec.id);
                        row.addProperty("mode", "extra");
                        row.addProperty("branch", i);
                        row.addProperty("name", skill.name());
                        row.addProperty("mechanic", skill.mechanic());
                        row.addProperty("motion", b.motion());
                        row.addProperty("target_health", t.getHealth());
                        row.addProperty("owned_summons", familiars(b));
                        System.out.println("[OROR_ABILITY_CHECK] " + row);
                        arrow.discard();
                        clean(b, t);
                        if (++count[0] == 123) {
                            h.succeed();
                        }
                    }
                );
            }
        }
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 120,
        batch = "arsenal"
    )
    public static void all_41_lore_techniques_run_without_mana_stall(GameTestHelper h) {
        for (CharacterSpec spec : CharacterSpec.ALL.values()) {
            for (int i = 0; i < 3; i++) {
                SupremeEntity b = boss(h, spec.id, true);
                Mob t = target(h, b);
                b.mana(0.0F);
                h.assertTrue(CharacterArsenal.cast(b, h.getLevel(), t, i), "Lore technique replenishes necessary energy " + spec.id + "/" + i);
                h.assertTrue(Float.isFinite(b.getHealth()) && Float.isFinite(b.mana()) && Float.isFinite(t.getHealth()), "No invalid state from lore technique");
                clean(b, t);
            }
        }

        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 180,
        batch = "arsenal"
    )
    public static void queued_hundred_fists_and_word_growth_act_after_cast(GameTestHelper h) {
        SupremeEntity m = boss(h, "mels", false);
        Mob t = target(h, m);
        m.setNoAi(false);
        m.cooldown = 1000;
        m.mana(50.0F);
        CharacterArsenal.cast(m, h.getLevel(), t, 0);
        float hp = t.getHealth();
        h.runAfterDelay(
            12L,
            () -> {
                System.out
                    .println(
                        "[OROR_BARRAGE_DIAGNOSTIC] hp="
                            + hp
                            + " current="
                            + t.getHealth()
                            + " sourceTick="
                            + m.tickCount
                            + " targetTick="
                            + t.tickCount
                            + " valid="
                            + m.validEnemy(t)
                            + " now="
                            + h.getLevel().getGameTime()
                            + " tag="
                            + t.getPersistentData()
                    );
                h.assertTrue(
                    t.getHealth() < hp && t.getPersistentData().getInt("OrorBarrageRemaining") < 100,
                    "Hundred fists deliver real subsequent damage, not only one initial hit"
                );
                clean(m, t);
                SupremeEntity b = boss(h, "riha", false);
                Mob other = target(h, b);
                BlockPos crop = b.blockPosition().east();
                h.getLevel().setBlock(crop.below(), Blocks.FARMLAND.defaultBlockState(), 3);
                h.getLevel().setBlock(crop, Blocks.WHEAT.defaultBlockState(), 3);
                b.mana(50.0F);
                CharacterArsenal.cast(b, h.getLevel(), other, 0);
                h.assertTrue(
                    h.getLevel().getBlockState(crop).is(Blocks.WHEAT) && (Integer)h.getLevel().getBlockState(crop).getValue(CropBlock.AGE) == 7,
                    "Word of growth matures a real crop"
                );
                clean(b, other);
                h.succeed();
            }
        );
    }
}
