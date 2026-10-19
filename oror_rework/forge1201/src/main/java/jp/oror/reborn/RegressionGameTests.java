package jp.oror.reborn;

import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.entity.projectile.Arrow;
import net.minecraft.world.entity.projectile.ProjectileUtil;
import net.minecraft.world.entity.projectile.AbstractArrow.Pickup;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

@GameTestHolder("oror_supreme_bosses")
@PrefixGameTestTemplate(false)
public final class RegressionGameTests {
    private static SupremeEntity mob(GameTestHelper h, String id, int x, int z) {
        SupremeEntity b = (SupremeEntity)((EntityType)OrorReborn.TYPES.get(id).get()).create(h.getLevel());
        b.balanced = true;
        b.mana(b.spec.mana);
        BlockPos p = h.absolutePos(new BlockPos(x, 2, z));
        b.moveTo((double)p.getX() + 0.5, (double)p.getY(), (double)p.getZ() + 0.5, 0.0F, 0.0F);
        h.getLevel().addFreshEntity(b);
        return b;
    }

    private static Zombie enemy(GameTestHelper h, int x, int z) {
        Zombie b = (Zombie)EntityType.ZOMBIE.create(h.getLevel());
        b.setPersistenceRequired();
        BlockPos p = h.absolutePos(new BlockPos(x, 2, z));
        b.moveTo((double)p.getX() + 0.5, (double)p.getY(), (double)p.getZ() + 0.5, 0.0F, 0.0F);
        b.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1024.0);
        b.setHealth(1024.0F);
        b.setNoAi(true);
        h.getLevel().addFreshEntity(b);
        return b;
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100
    )
    public static void no_ai_blocks_custom_combat(GameTestHelper h) {
        SupremeEntity b = mob(h, "kokuhaku", 8, 8);
        Zombie z = enemy(h, 10, 8);
        Abilities.stun(z, 100);
        b.setNoAi(true);
        b.setTarget(z);
        b.cooldown = 0;
        float mp = b.mana();
        h.runAfterDelay(35L, () -> {
            h.assertTrue(b.action() == 0 && b.mana() == mp && z.getHealth() == 1024.0F, "NoAI blocks custom attacks and mana use");
            System.out.println("[OROR_REGRESSION] NoAI mana=" + b.mana() + " targetHealth=" + z.getHealth());
            h.succeed();
        });
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100
    )
    public static void friendly_arrows_are_not_erased(GameTestHelper h) {
        SupremeEntity b = mob(h, "tenki", 8, 8);
        SupremeEntity a = mob(h, "savior", 10, 8);
        Zombie z = enemy(h, 6, 8);
        b.setTarget(z);
        Arrow friendly = new Arrow(EntityType.ARROW, h.getLevel());
        friendly.setOwner(a);
        friendly.moveTo(b.getX() + 1.0, b.getY() + 1.0, b.getZ());
        h.getLevel().addFreshEntity(friendly);
        Arrow hostile = new Arrow(EntityType.ARROW, h.getLevel());
        hostile.setOwner(z);
        hostile.moveTo(b.getX() + 1.0, b.getY() + 1.0, b.getZ() + 1.0);
        h.getLevel().addFreshEntity(hostile);
        FamiliarEntity f = (FamiliarEntity)((EntityType)OrorReborn.FAMILIAR.get()).create(h.getLevel());
        f.creator = a.getUUID();
        Arrow summonArrow = new Arrow(h.getLevel(), f, Items.ARROW.getDefaultInstance(), null);
        summonArrow.moveTo(b.getX() + 1.0, b.getY() + 1.0, b.getZ() - 1.0);
        h.getLevel().addFreshEntity(summonArrow);
        Abilities.cast(b, h.getLevel(), z);
        h.assertTrue(!friendly.isRemoved() && !summonArrow.isRemoved() && hostile.isRemoved(), "Friendly NPC and summon arrows survive");
        h.assertTrue(!b.hurt(b.damageSources().arrow(friendly, a), 20.0F) && b.getTarget() == z, "Friendly projectile damage does not provoke allies");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100
    )
    public static void savior_and_arcana_protect_together(GameTestHelper h) {
        SupremeEntity s = mob(h, "savior", 8, 8);
        SupremeEntity a = mob(h, "arcana", 8, 8);
        SupremeEntity v = mob(h, "valeria", 10, 8);
        float sm = s.mana();
        float am = a.mana();
        v.setHealth(10.0F);
        v.hurt(v.damageSources().generic(), 100.0F);
        h.assertTrue(v.isAlive() && s.mana() == sm - 3.0F && a.mana() == am - 35.0F, "Damage reduction and lethal rescue both apply");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100
    )
    public static void forced_bow_arrows_can_be_saved(GameTestHelper h) {
        SupremeEntity b = mob(h, "ferdinand", 8, 8);
        FamiliarEntity f = (FamiliarEntity)((EntityType)OrorReborn.FAMILIAR.get()).create(h.getLevel());
        f.creator = b.getUUID();

        for (PathfinderMob owner : List.of(b, f)) {
            ItemStack bow = Items.BOW.getDefaultInstance();
            ItemStack ammo = owner.getProjectile(bow);
            h.assertTrue(!ammo.isEmpty(), "External bow AI receives valid ammunition");
            AbstractArrow a = ProjectileUtil.getMobArrow(owner, ammo, 1.0F);
            CompoundTag n = new CompoundTag();
            a.saveWithoutId(n);
            h.assertTrue(n.contains("item"), "Arrow item serialized");
        }

        Arrow invalid = new Arrow(h.getLevel(), b, ItemStack.EMPTY, null);
        invalid.pickup = Pickup.DISALLOWED;
        CompoundTag repaired = new CompoundTag();
        invalid.saveWithoutId(repaired);
        h.assertTrue(
            repaired.getCompound("item").getString("id").equals("minecraft:arrow") && repaired.getByte("pickup") == 0,
            "Malformed non-pickup arrow saved without enabling pickup"
        );
        System.out.println("[OROR_AMMO] NPC, familiar, and malformed non-pickup arrow NBT save PASS");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 500
    )
    public static void all_41_run_and_fight_together(GameTestHelper h) {
        ArrayList<SupremeEntity> group = new ArrayList<>();
        int i = 0;

        for (CharacterSpec s : CharacterSpec.ALL.values()) {
            int x = 3 + i % 6 * 4;
            int z = 3 + i / 6 * 4;
            SupremeEntity b = mob(h, s.id, x, z);
            Zombie t = enemy(h, x + 1, z);
            b.mana(20.0F);
            b.cooldown = 0;
            b.setTarget(t);
            group.add(b);
            i++;
        }

        h.runAfterDelay(
            23L,
            () -> {
                long cast = group.stream().filter(bx -> bx.mana() < 20.0F).count();
                System.out
                    .println(
                        "[OROR_CONCURRENT] firstCasts="
                            + cast
                            + " missed="
                            + group.stream()
                                .filter(bx -> bx.mana() >= 20.0F)
                                .map(
                                    bx -> bx.spec.id
                                            + ":ticks="
                                            + bx.tickCount
                                            + ":hp="
                                            + bx.getHealth()
                                            + ":mp="
                                            + bx.mana()
                                            + ":frozen="
                                            + bx.getPersistentData().getLong("ororFreezeUntil")
                                            + ":clock="
                                            + bx.level().getGameTime()
                                )
                                .toList()
                    );
                h.assertTrue(cast == 41L, "All 41 executed their first attack through normal AI");
                System.out.println("[OROR_CONCURRENT] firstCasts=" + cast + " tick=23");
            }
        );
        h.runAfterDelay(
            400L,
            () -> {
                for (SupremeEntity bx : group) {
                    h.assertTrue(
                        bx.isAlive()
                            && Double.isFinite(bx.getX())
                            && Double.isFinite(bx.getY())
                            && Double.isFinite(bx.getZ())
                            && Float.isFinite(bx.getHealth())
                            && Float.isFinite(bx.mana()),
                        "Finite live state " + bx.spec.id
                    );
                    h.assertTrue(bx.memory.entries().size() <= 128, "Bounded adaptation " + bx.spec.id);
                }

                long summons = (long)h.getLevel().getEntitiesOfClass(FamiliarEntity.class, group.get(0).getBoundingBox().inflate(48.0)).size();
                h.assertTrue(summons <= (long)((Integer)RebornConfig.LEVEL_SUMMONS.get()).intValue(), "Level summon budget");
                System.out
                    .println(
                        "[OROR_CONCURRENT] simulatedTicks=400 alive="
                            + group.size()
                            + " summons="
                            + summons
                            + " avgTickMs="
                            + (double)h.getLevel().getServer().getAverageTickTime()
                    );
                h.succeed();
            }
        );
    }
}
