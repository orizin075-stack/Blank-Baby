package jp.oror.reborn;

import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

@GameTestHolder("oror_supreme_bosses")
@PrefixGameTestTemplate(false)
public final class RebornGameTests {
    private static SupremeEntity mob(GameTestHelper h, String id, int x) {
        SupremeEntity b = (SupremeEntity)((EntityType)OrorReborn.TYPES.get(id).get()).create(h.getLevel());
        b.balanced = true;
        b.mana(b.spec.mana);
        BlockPos p = h.absolutePos(new BlockPos(x, 2, 8));
        b.moveTo((double)p.getX() + 0.5, (double)p.getY(), (double)p.getZ() + 0.5, 0.0F, 0.0F);
        h.getLevel().addFreshEntity(b);
        return b;
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100
    )
    public static void all_roster_types_and_eggs(GameTestHelper h) {
        h.assertTrue(CharacterSpec.ALL.size() == 41, "41 definitions");

        for (CharacterSpec s : CharacterSpec.ALL.values()) {
            SupremeEntity b = mob(h, s.id, 8);
            h.assertTrue(b.getMaxHealth() == s.health, "Attributes " + s.id);
            h.assertTrue(OrorReborn.EGGS.get(s.id).get() != null, "Egg " + s.id);
            b.discard();
        }

        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100
    )
    public static void all_41_abilities_execute(GameTestHelper h) {
        for (CharacterSpec s : CharacterSpec.ALL.values()) {
            SupremeEntity b = mob(h, s.id, 4);
            Zombie z = (Zombie)EntityType.ZOMBIE.create(h.getLevel());
            z.setPersistenceRequired();
            BlockPos p = h.absolutePos(new BlockPos(10, 2, 8));
            z.moveTo((double)p.getX(), (double)p.getY(), (double)p.getZ(), 0.0F, 0.0F);
            h.getLevel().addFreshEntity(z);
            b.setTarget(z);
            float mp = b.mana();
            Abilities.cast(b, h.getLevel(), z);
            h.assertTrue(b.mana() == mp - 20.0F, "Ability consumed mana " + s.id);
            b.discard();
            z.discard();

            for (FamiliarEntity f : h.getLevel().getEntitiesOfClass(FamiliarEntity.class, b.getBoundingBox().inflate(20.0))) {
                f.discard();
            }
        }

        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100
    )
    public static void adaptation_persists_through_nbt(GameTestHelper h) {
        SupremeEntity b = mob(h, "hakyoku", 6);
        b.memory.observe("minecraft:magic");
        b.memory.observe("minecraft:magic");
        b.evolution = 7;
        b.revivals = 1;
        b.mana(50.0F);
        CompoundTag n = new CompoundTag();
        b.addAdditionalSaveData(n);
        SupremeEntity c = mob(h, "hakyoku", 14);
        c.readAdditionalSaveData(n);
        h.assertTrue(c.memory.count("minecraft:magic") == 2, "Resistance saved");
        h.assertTrue(c.evolution == 7 && c.revivals == 1 && c.mana() == 50.0F, "Progress saved");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100
    )
    public static void mana_storage_and_regen_differ(GameTestHelper h) {
        CharacterSpec a = CharacterSpec.ALL.get("elseria");
        CharacterSpec d = CharacterSpec.ALL.get("huang_linghua");
        h.assertTrue(a.mana < d.mana && a.regen > d.regen, "Small reservoir, large flow");
        SupremeEntity b = mob(h, "elseria", 8);
        b.mana(0.0F);
        h.runAfterDelay(21L, () -> {
            h.assertTrue(b.mana() > 0.0F, "Live regeneration");
            h.succeed();
        });
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100
    )
    public static void immortality_has_balanced_revival(GameTestHelper h) {
        SupremeEntity b = mob(h, "mary_sue", 8);
        b.setHealth(0.0F);
        b.die(b.damageSources().generic());
        h.assertTrue(b.isAlive() && b.revivals == 1 && b.evolution > 0, "Awakened from lethal crisis");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100
    )
    public static void fabrication_obeys_owner_cap(GameTestHelper h) {
        SupremeEntity b = mob(h, "hephaistos", 8);
        FamiliarEntity.create(b, h.getLevel(), 0, 40);
        long n = (long)h.getLevel().getEntitiesOfClass(FamiliarEntity.class, b.getBoundingBox().inflate(20.0), f -> b.getUUID().equals(f.creator)).size();
        h.assertTrue(n > 0L && n <= (long)((Integer)RebornConfig.MAX_SUMMONS.get()).intValue(), "Summons created within cap");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100
    )
    public static void newly_spawned_characters_are_neutral(GameTestHelper h) {
        SupremeEntity b = mob(h, "kokuhaku", 8);
        h.runAfterDelay(45L, () -> {
            h.assertTrue(b.getTarget() == null, "No unsolicited target");
            h.succeed();
        });
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100
    )
    public static void yggdrasil_form_changes_dimensions(GameTestHelper h) {
        SupremeEntity b = mob(h, "yggdrasil", 8);
        b.refreshDimensions();
        float t = b.getBbHeight();
        b.setForm(1);
        h.assertTrue(b.getBbHeight() < t, "Smaller synchronized avatar");
        b.setForm(0);
        h.assertTrue(Math.abs(b.getBbHeight() - t) < 1.0E-4F, "Tree restored respecting external scale");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100
    )
    public static void freeze_expires_by_world_clock(GameTestHelper h) {
        Zombie z = (Zombie)EntityType.ZOMBIE.create(h.getLevel());
        z.setPersistenceRequired();
        BlockPos p = h.absolutePos(new BlockPos(8, 2, 8));
        z.moveTo((double)p.getX(), (double)p.getY(), (double)p.getZ(), 0.0F, 0.0F);
        h.getLevel().addFreshEntity(z);
        z.setRemainingFireTicks(1000);
        Abilities.stun(z, 20);
        int before = z.getRemainingFireTicks();
        h.runAfterDelay(15L, () -> h.assertTrue(z.getRemainingFireTicks() == before, "Burn timer suspended"));
        h.runAfterDelay(
            32L,
            () -> {
                System.out
                    .println(
                        "[OROR_FREEZE] before="
                            + before
                            + " after="
                            + z.getRemainingFireTicks()
                            + " ticks="
                            + z.tickCount
                            + " alive="
                            + z.isAlive()
                            + " y="
                            + z.getY()
                            + " until="
                            + z.getPersistentData().getLong("ororFreezeUntil")
                            + " clock="
                            + z.level().getGameTime()
                    );
                h.assertTrue(z.isAlive() && z.getRemainingFireTicks() < before, "Frozen entity resumed");
                h.succeed();
            }
        );
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100
    )
    public static void memory_and_evolution_are_bounded(GameTestHelper h) {
        CombatMemory m = new CombatMemory();

        for (int i = 0; i < 200; i++) {
            m.observe("test:" + i);
        }

        h.assertTrue(m.entries().size() == 128, "Bounded memory");
        h.assertTrue(CombatMemory.boundedEvolution(Integer.MAX_VALUE) == 1000, "Finite evolution");
        h.succeed();
    }
}
