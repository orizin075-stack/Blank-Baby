package jp.oror.reborn.ci;

import jp.oror.reborn.AdaptiveCombat;
import jp.oror.reborn.MobLevels;
import jp.oror.reborn.MobMind;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Husk;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.npc.VillagerProfession;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;

import java.util.Locale;

/**
 * (r66) The base jar's game tests that still asked for what the user had changed since (053: an armed villager's health,
 * 40 at level one; 053: a miner digs only under a roof; 058: no mob sets a block in a fight; the Modular Golems curios pack
 * left off where Accessories runs), asked again for what the game is meant to do now. Each replaces the test of the same
 * name (GameTestFixesMixins); a failure says what it saw.
 */
public final class GameTestFixes {
    private GameTestFixes() {
    }

    /** As the tests' own helper: the mob at (x, 2, z), kept, a villager at level one. */
    static <T extends Mob> T mob(GameTestHelper h, EntityType<T> type, int x, int z) {
        T m = type.create(h.getLevel());
        BlockPos pos = h.absolutePos(new BlockPos(x, 2, z));
        m.moveTo(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, 0F, 0F);
        m.setPersistenceRequired();
        h.getLevel().addFreshEntity(m);
        if (m instanceof Villager) {
            MobLevels.set(m, 1);
        }
        return m;
    }

    /**
     * An armed villager of trade level one (sword and shield, 40 health since 053) beats an ordinary survival player:
     * struck again and again, as in a fight (the mock player never ticks, so its hurt time is let go before each blow).
     */
    public static void villagerArms(GameTestHelper h) {
        Villager v = mob(h, EntityType.VILLAGER, 8, 8);
        AdaptiveCombat.arm(v);
        Player p = h.makeMockPlayer(GameType.SURVIVAL);
        p.moveTo(v.getX() + 1.0, v.getY(), v.getZ());
        v.setTarget(p);
        float max = v.getMaxHealth();
        h.assertTrue(v.getMainHandItem().is(Items.IRON_SWORD) && v.getOffhandItem().is(Items.SHIELD),
            "Trade level one villager is armed: " + v.getMainHandItem() + " / " + v.getOffhandItem());
        h.assertTrue(max >= 40F && max < 60F, "Trade level one villager has the level-one health of 053 (40): " + max);
        int[] tick = {0}, strikes = {0};
        h.onEachTick(() -> {
            if (p.isAlive() && tick[0]++ % 10 == 0) {
                p.invulnerableTime = 0;
                AdaptiveCombat.strike(v, p, "sword", h.getLevel());
                strikes[0]++;
            }
        });
        h.succeedWhen(() -> h.assertTrue(!p.isAlive(), String.format(Locale.ROOT,
            "Trade level one villager kills ordinary survival player: %d blows, player health %.1f", strikes[0], p.getHealth())));
    }

    /** A fighting villager low on health heals and steps back from its foe while it does. */
    public static void lowHealthRetreat(GameTestHelper h) {
        Villager v = mob(h, EntityType.VILLAGER, 8, 8);
        v.setVillagerData(v.getVillagerData().setProfession(VillagerProfession.ARMORER));
        AdaptiveCombat.arm(v);
        // a third of its health (it was 40 of 256 before 053; 40 is a level-one villager's whole health now)
        float low = v.getMaxHealth() * 0.3F;
        v.setHealth(low);
        Husk t = mob(h, EntityType.HUSK, 10, 8);
        t.setNoAi(true);
        v.setTarget(t);
        double start = v.distanceTo(t);
        h.succeedWhen(() -> h.assertTrue(v.getHealth() > low && v.distanceTo(t) > start && MobMind.skill(v, "healing") > 0,
            String.format(Locale.ROOT, "Actual movement retreats while recovering: health %.1f of %.1f (from %.1f), %.2f from the husk (from %.2f), healing %d",
                v.getHealth(), v.getMaxHealth(), low, v.distanceTo(t), start, MobMind.skill(v, "healing"))));
    }

    /**
     * Since 058 a mob builds nothing to reach its foe (no pillar, no bridge: the buildings broken in fights), and a chest
     * in its way is never broken.
     */
    public static void terrainPillar(GameTestHelper h) {
        Villager v = mob(h, EntityType.VILLAGER, 8, 8);
        v.setNoAi(true);
        v.setOnGround(true);
        Zombie t = mob(h, EntityType.ZOMBIE, 12, 8);
        t.setNoAi(true);
        t.teleportTo(t.getX(), v.getY() + 5.0, t.getZ());
        GameRules.BooleanValue rule = h.getLevel().getGameRules().getRule(GameRules.RULE_MOBGRIEFING);
        boolean grief = rule.get();
        rule.set(true, h.getLevel().getServer());
        try {
            BlockPos pos = v.blockPosition();
            boolean built = AdaptiveCombat.terrain(v, t, h.getLevel());
            h.assertTrue(!built && !h.getLevel().getBlockState(pos).is(Blocks.COBBLESTONE),
                "No pillar of its own under a mob in a fight (058): " + h.getLevel().getBlockState(pos));
            MobMind.data(v).putLong("NextTerrain", 0L);
            t.teleportTo(t.getX(), v.getY(), t.getZ());
            BlockPos front = v.blockPosition().east();
            h.getLevel().setBlock(front, Blocks.CHEST.defaultBlockState(), 3);
            h.assertTrue(!AdaptiveCombat.terrain(v, t, h.getLevel()) && h.getLevel().getBlockState(front).is(Blocks.CHEST),
                "Chest cannot be destroyed for pathing");
        } finally {
            rule.set(grief, h.getLevel().getServer());
        }
        h.succeed();
    }

    /** Since 058 no water is set under a falling mob (and taken away after): the fall is the fall. */
    public static void landingWater(GameTestHelper h) {
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
        GameRules.BooleanValue rule = h.getLevel().getGameRules().getRule(GameRules.RULE_MOBGRIEFING);
        boolean old = rule.get();
        rule.set(true, h.getLevel().getServer());
        try {
            jp.oror.reborn.TerrainPlay.fallRescue(m, h.getLevel());
        } finally {
            rule.set(old, h.getLevel().getServer());
        }
        h.assertTrue(!h.getBlockState(new BlockPos(8, 2, 8)).is(Blocks.WATER) && !h.getBlockState(new BlockPos(8, 3, 8)).is(Blocks.WATER),
            "No water set under a falling mob (058)");
        h.succeed();
    }

    /** (053) a miner digs only where no sky is over it: the tests' ore is put under a roof, as ore lies underground. */
    public static void roof(GameTestHelper h, int x0, int x1, int z0, int z1) {
        for (int x = x0; x <= x1; x++) {
            for (int z = z0; z <= z1; z++) {
                h.setBlock(x, 6, z, Blocks.STONE);
            }
        }
    }

    /**
     * The Modular Golems curios pack goes on only where none of Accessories' mods run (CompatibilityPacks: their slots
     * would clash). "Is it on" asks whether it is in the state it should be.
     */
    public static boolean packAsItShouldBe(java.util.Collection<String> selected, Object id) {
        if (id instanceof String s && s.endsWith("modulargolems_3143")
            && java.util.stream.Stream.of("l2artifacts", "l2hostility", "artifacts", "accessories").anyMatch(net.neoforged.fml.ModList.get()::isLoaded)) {
            return !selected.contains(s);
        }
        return selected.contains(id);
    }

    private static final java.util.Map<Villager, float[]> MASTER = new java.util.WeakHashMap<>();
    private static final org.slf4j.Logger LOG = org.slf4j.LoggerFactory.getLogger("OROR GameTest");

    /**
     * (r68) The master villager's duel with the netherite player, strike by strike: on each new strike its count, those
     * the game took and turned away, the player's health before and after, his hurt time, the distance and whether the
     * master was coming down from a jump (a critical). Called each tick from the test's own check.
     */
    public static void masterTrace(Player p, Villager v) {
        net.minecraft.nbt.CompoundTag d = MobMind.data(v);
        int strikes = d.getInt("Strikes");
        float[] last = MASTER.computeIfAbsent(v, k -> new float[]{0, p.getHealth()});
        if (strikes != (int) last[0]) {
            LOG.info(String.format(Locale.ROOT, "MASTER-DUEL {\"strike\":%d,\"landed\":%d,\"rejected\":%d,\"health\":\"%.1f>%.1f\",\"hurtTime\":%d,"
                    + "\"dist\":%.2f,\"falling\":%b,\"age\":%d}", strikes, d.getInt("SuccessfulStrikes"), d.getInt("RejectedStrikes"), last[1], p.getHealth(),
                p.invulnerableTime, v.distanceTo(p), v.fallDistance > 0 && !v.onGround(), v.tickCount));
            last[0] = strikes;
            last[1] = p.getHealth();
        }
    }

    /**
     * A fighting villager waits for a real descending jump before it counts a critical strike. As one of the village's
     * fighters (an armorer): a villager without a trade is a civilian, which fights back only while cornered and backs
     * off once a dodge takes it out of reach (the test failed now and then since 0.17.14 for that).
     */
    public static void criticalJump(GameTestHelper h) {
        Villager v = mob(h, EntityType.VILLAGER, 8, 8);
        v.setVillagerData(v.getVillagerData().setProfession(VillagerProfession.ARMORER));
        MobLevels.set(v, 5);
        AdaptiveCombat.arm(v);
        MobMind.data(v).putString("Stance", "aggressive");
        Husk t = mob(h, EntityType.HUSK, 10, 8);
        t.setNoAi(true);
        t.getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.MAX_HEALTH).setBaseValue(1024.0);
        t.setHealth(1024.0F);
        v.setTarget(t);
        h.succeedWhen(() -> h.assertTrue(MobMind.data(v).getInt("CriticalHits") > 0 && t.getHealth() < 1024.0F,
            String.format(Locale.ROOT, "A real jump descends before a critical strike is counted: criticals %d, husk %.0f, %.2f apart, target %s",
                MobMind.data(v).getInt("CriticalHits"), t.getHealth(), v.distanceTo(t), v.getTarget() == null ? "none" : v.getTarget().getType().toShortString())));
    }
}
