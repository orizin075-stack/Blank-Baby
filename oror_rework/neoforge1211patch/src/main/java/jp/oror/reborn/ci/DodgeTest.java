package jp.oror.reborn.ci;

import com.mojang.authlib.GameProfile;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import jp.oror.reborn.combat.MobDodge;
import jp.oror.reborn.combat.MobGuard;
import jp.oror.reborn.combat.MobStamina;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.projectile.Arrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (059h) CI check "dodge" (/oror dodge test, DODGE-RESULT): the near-miss dodge (MobDodge) and the mobs' stamina
 * (MobStamina). On a cleared floor far from anything, each in its own lane, free to move: a bare-handed zombie, a
 * vindicator with an axe, a wither skeleton with a sword, a kingdom guard and a god (Ferdinand), each struck from two
 * blocks before it by a fake player every half second for fifteen seconds (the striker following it where its steps take
 * it); and a skeleton with a sword shot at by an arrow every second from ten blocks. Measured: blows, dodges (of blows, of
 * shots landing, of shots seen coming), how far each dodge carried it, what it was dealt, its stamina's lowest and the
 * times it was winded. (059h) Two vindicators alike but for their experience (a fresh one, a veteran of 20,000). Pass:
 * four of the six struck dodge at least one blow and two at least twice, a dodge carries a mob at least 0.8 blocks on
 * average, at least one arrow is seen coming and flies past, stamina is spent (some mob below 70%), some mob is winded,
 * the veteran is the better dodger by 0.3 of prowess and has the deeper stamina, and the zombie, its stamina emptied
 * half way, is winded, dodges nothing while winded and gets its wind back. (CI 68) Each lane 56 blocks from the next.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class DodgeTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Guard");
    public static volatile boolean resultLogged;

    static final class Tester extends FakePlayer {
        Tester(ServerLevel level, int n) {
            super(level, new GameProfile(UUID.fromString("0f0e0d0c-0b0a-4908-8706-0504030202" + String.format("%02x", n)), "[OROR Dodge " + n + "]"));
        }

        void ready() {
            this.attackStrengthTicker = 200;
        }
    }

    static final class Lane {
        String id;
        Mob mob;
        Tester tester;
        boolean archery, veteran, fresh;
        int blows, arrows, dodgesSeenBefore, lastDodges, windedDodgesFrom;
        float dealt, minStamina = 1F;
        Vec3 dodgeFrom, prevPos;
        long dodgeAt = -1;
        double carried;
        int carriedCount;
        float lastHealth;
    }

    static final class Run {
        ServerLevel level;
        BlockPos origin;
        final List<ChunkPos> forced = new ArrayList<>();
        final List<Entity> made = new ArrayList<>();
        final List<Lane> lanes = new ArrayList<>();
        String phase = "load";
        long phaseAt;
        boolean forcedWinded;
        int windedDodges;
        long recoveredAt = -1;
    }

    private static Run run;
    private static final int LANES = 7, SPACING = 56;

    private DodgeTest() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("dodge").then(Commands.literal("test")
            .requires(s -> s.hasPermission(2)).executes(c -> start(c.getSource())))));
    }

    private static int start(CommandSourceStack src) {
        if (run != null) {
            return 0;
        }
        Run r = new Run();
        r.level = src.getServer().overworld();
        r.origin = BlockPos.containing(src.getPosition()).offset(2600, 0, 3400);
        // (CI 68) each lane 56 blocks from the next, out of one another's way: the god and the kingdom's guard had struck
        // down the lanes beside them (the wither skeleton, the archers' skeleton)
        for (int lane = 0; lane < LANES; lane++) {
            BlockPos at = r.origin.offset(lane * SPACING, 0, 0);
            for (int dx = -1; dx <= 1; dx++) {
                for (int dz = -1; dz <= 1; dz++) {
                    ChunkPos p = new ChunkPos((at.getX() >> 4) + dx, (at.getZ() >> 4) + dz);
                    if (!r.forced.contains(p) && r.level.setChunkForced(p.x, p.z, true)) {
                        r.forced.add(p);
                    }
                }
            }
        }
        r.phaseAt = r.level.getGameTime();
        run = r;
        LOG.info("DODGE-START {\"at\":[{},{}]}", r.origin.getX(), r.origin.getZ());
        return 1;
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        Run r = run;
        if (r == null) {
            return;
        }
        try {
            step(r, r.level.getGameTime() - r.phaseAt);
        } catch (RuntimeException ex) {
            LOG.error("DODGE-ERROR", ex);
            finish(r, ex.toString());
        }
    }

    private static void step(Run r, long t) {
        switch (r.phase) {
            case "load" -> {
                if (t < 40) {
                    return;
                }
                // (059h) two vindicators alike but for their experience: a fresh one and a veteran (MobMind's 20,000)
                String[][] who = {{"minecraft:zombie", ""}, {"minecraft:vindicator", "iron_axe"}, {"minecraft:vindicator", "iron_axe", "veteran"},
                    {"minecraft:wither_skeleton", "stone_sword"}, {"oror_supreme_bosses:kingdom_guard", "keep"}, {"oror_supreme_bosses:ferdinand", "keep"},
                    {"minecraft:skeleton", "iron_sword"}};
                for (int i = 0; i < who.length; i++) {
                    BlockPos spot = floor(r.level, r.origin.offset(i * SPACING, 0, 0));
                    EntityType<?> type = BuiltInRegistries.ENTITY_TYPE.getOptional(ResourceLocation.parse(who[i][0])).orElse(null);
                    Entity en = type == null ? null : type.create(r.level);
                    if (!(en instanceof Mob m)) {
                        if (en != null) {
                            en.discard();
                        }
                        continue;
                    }
                    m.moveTo(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5, 0F, 0F);
                    m.setPersistenceRequired();
                    if (!who[i][1].equals("keep")) {
                        m.setItemSlot(EquipmentSlot.MAINHAND, who[i][1].isEmpty() ? ItemStack.EMPTY
                            : new ItemStack(BuiltInRegistries.ITEM.get(ResourceLocation.withDefaultNamespace(who[i][1]))));
                    }
                    r.level.addFreshEntity(m);
                    if (m.getAttribute(Attributes.MAX_HEALTH) != null && !(m instanceof jp.oror.reborn.SupremeEntity)) {
                        m.getAttribute(Attributes.MAX_HEALTH).setBaseValue(400);
                    }
                    m.setHealth(m.getMaxHealth());
                    r.made.add(m);
                    Lane l = new Lane();
                    l.id = BuiltInRegistries.ENTITY_TYPE.getKey(m.getType()).getPath();
                    // its level drawn first (MobLevels' lottery at its birth), then set: the fresh one at the first, the
                    // veteran by his experience (the fifth)
                    if (who[i].length > 2) {
                        jp.oror.reborn.MobLevels.initialize(m);
                        jp.oror.reborn.MobMind.data(m).putLong("Experience", 20000L);
                        jp.oror.reborn.MobLevels.set(m, 5);
                        l.id += "_veteran";
                        l.veteran = true;
                    } else if (l.id.equals("vindicator")) {
                        jp.oror.reborn.MobLevels.initialize(m);
                        jp.oror.reborn.MobLevels.set(m, 1);
                        l.fresh = true;
                    }
                    l.mob = m;
                    l.archery = who[i][0].equals("minecraft:skeleton");
                    l.tester = new Tester(r.level, i);
                    l.tester.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(Items.IRON_SWORD));
                    l.tester.moveTo(m.getX(), m.getY(), m.getZ() + 2.0, 180F, 0F);
                    m.setTarget(l.tester);
                    l.lastHealth = m.getHealth();
                    r.lanes.add(l);
                }
                next(r, "fight");
            }
            case "fight" -> {
                for (int i = 0; i < r.lanes.size(); i++) {
                    Lane l = r.lanes.get(i);
                    Mob m = l.mob;
                    if (!m.isAlive()) {
                        continue;
                    }
                    // what it was dealt since the last tick, then made whole (it is the dodge that is measured, not a death)
                    l.dealt += Math.max(0F, l.lastHealth - m.getHealth());
                    m.setHealth(m.getMaxHealth());
                    l.lastHealth = m.getHealth();
                    l.minStamina = Math.min(l.minStamina, MobStamina.fraction(m));
                    // how far a dodge carried it: from where it stood the tick before, eight ticks on
                    int dodges = m.getPersistentData().getInt("OrorDodges");
                    if (dodges > l.lastDodges) {
                        l.lastDodges = dodges;
                        if (l.dodgeAt < 0 && l.prevPos != null) {
                            l.dodgeFrom = l.prevPos;
                            l.dodgeAt = r.level.getGameTime();
                        }
                    }
                    if (l.dodgeAt >= 0 && r.level.getGameTime() - l.dodgeAt >= 8) {
                        l.carried += m.position().subtract(l.dodgeFrom).horizontalDistance();
                        l.carriedCount++;
                        l.dodgeAt = -1;
                    }
                    m.setTarget(l.tester);
                    // (CI 68: no mob ran itself out in fifteen seconds) the zombie's stamina emptied half way: it must be
                    // winded, dodge nothing while winded, and get its wind back
                    if (l.id.equals("zombie")) {
                        if (t == 120) {
                            MobStamina.drain(m, MobStamina.max(m));
                            l.windedDodgesFrom = m.getPersistentData().getInt("OrorDodges");
                            r.forcedWinded = MobStamina.winded(m);
                        } else if (t > 120 && MobStamina.winded(m)) {
                            r.windedDodges = m.getPersistentData().getInt("OrorDodges") - l.windedDodgesFrom;
                        } else if (t > 120 && r.recoveredAt < 0) {
                            r.recoveredAt = t;
                        }
                    }
                    if (l.archery) {
                        // shot at from ten blocks every second: an arrow on course for its chest
                        l.tester.moveTo(m.getX(), m.getY(), m.getZ() + 10.0, 180F, 0F);
                        if (t > 20 && t % 20 == (i * 3L) % 20) {
                            Arrow arrow = EntityType.ARROW.create(r.level);
                            if (arrow == null) {
                                continue;
                            }
                            arrow.setPos(m.getX(), m.getY() + m.getBbHeight() * 0.55, m.getZ() + 9.0);
                            Vec3 aim = m.position().add(0, m.getBbHeight() * 0.55, 0).subtract(arrow.position());
                            arrow.shoot(aim.x, aim.y, aim.z, 1.6F, 0F);
                            r.level.addFreshEntity(arrow);
                            r.made.add(arrow);
                            l.arrows++;
                        }
                    } else {
                        // the striker two blocks before it, wherever its steps took it, striking every half second
                        l.tester.moveTo(m.getX(), m.getY(), m.getZ() + 2.0, 180F, 0F);
                        m.getLookControl().setLookAt(l.tester, 90F, 90F);
                        if (t > 20 && t % 10 == (i * 2L) % 10) {
                            l.tester.ready();
                            l.tester.attack(m);
                            l.blows++;
                        }
                    }
                }
                for (Lane l : r.lanes) {
                    l.prevPos = l.mob.position();
                }
                if (t >= 300) {
                    finish(r, "");
                }
            }
            default -> {
            }
        }
    }

    private static void next(Run r, String phase) {
        r.phase = phase;
        r.phaseAt = r.level.getGameTime();
    }

    private static BlockPos floor(ServerLevel level, BlockPos at) {
        level.getChunk(at);
        int y = Math.max(level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, at.getX(), at.getZ()), level.getSeaLevel() + 1);
        for (int dx = -12; dx <= 12; dx++) {
            for (int dz = -10; dz <= 14; dz++) {
                level.setBlock(new BlockPos(at.getX() + dx, y - 1, at.getZ() + dz), Blocks.STONE.defaultBlockState(), 2);
                for (int h = 0; h < 12; h++) {
                    BlockPos q = new BlockPos(at.getX() + dx, y + h, at.getZ() + dz);
                    if (!level.getBlockState(q).isAir()) {
                        level.setBlock(q, Blocks.AIR.defaultBlockState(), 2);
                    }
                }
            }
        }
        return new BlockPos(at.getX(), y, at.getZ());
    }

    private static void finish(Run r, String error) {
        StringBuilder out = new StringBuilder("DODGE-RESULT {\"present\":true,\"lanes\":[");
        int dodgingMelee = 0, twice = 0, meleeLanes = 0, seen = 0, winded = 0;
        double carried = 0;
        int carriedCount = 0;
        float minStamina = 1F;
        boolean first = true;
        for (Lane l : r.lanes) {
            Mob m = l.mob;
            var d = m.getPersistentData();
            int blowsDodged = d.getInt("OrorDodgedBlows"), shotsDodged = d.getInt("OrorDodgedShots"), seenDodged = d.getInt("OrorDodgedSeen");
            if (!l.archery) {
                meleeLanes++;
                dodgingMelee += blowsDodged >= 1 ? 1 : 0;
                twice += blowsDodged >= 2 ? 1 : 0;
            } else {
                seen += seenDodged + shotsDodged;
            }
            winded += d.getInt("OrorWinded");
            carried += l.carried;
            carriedCount += l.carriedCount;
            minStamina = Math.min(minStamina, l.minStamina);
            out.append(first ? "" : ",").append(String.format(Locale.ROOT,
                "{\"mob\":\"%s\",\"blows\":%d,\"arrows\":%d,\"dodges\":\"%s\",\"carried\":%.2f,\"dealt\":%.0f,\"minStamina\":%.2f,\"stamina\":\"%s\","
                    + "\"guard\":\"%s\",\"skill\":\"%s\",\"alive\":%b}",
                l.id, l.blows, l.arrows, MobDodge.tally(m), l.carriedCount == 0 ? 0 : l.carried / l.carriedCount, l.dealt, l.minStamina,
                MobStamina.describe(m), MobGuard.tally(m), jp.oror.reborn.combat.MobProwess.describe(m), m.isAlive()));
            first = false;
        }
        double avgCarry = carriedCount == 0 ? 0 : carried / carriedCount;
        // (059h) the veteran better at it and deeper of wind than the fresh one: by its prowess, not by chance
        float vetP = -1, freshP = -1, vetMax = -1, freshMax = -1;
        for (Lane l : r.lanes) {
            if (l.veteran) {
                vetP = jp.oror.reborn.combat.MobProwess.of(l.mob);
                vetMax = MobStamina.max(l.mob);
            } else if (l.fresh) {
                freshP = jp.oror.reborn.combat.MobProwess.of(l.mob);
                freshMax = MobStamina.max(l.mob);
            }
        }
        boolean seasoned = vetP >= 0 && freshP >= 0 && vetP - freshP >= 0.3F && vetMax > freshMax;
        boolean windOk = r.forcedWinded && r.windedDodges == 0 && r.recoveredAt > 0;
        boolean pass = error.isEmpty() && meleeLanes >= 6 && dodgingMelee >= 4 && twice >= 2 && avgCarry >= 0.8 && seen >= 1 && minStamina < 0.7F
            && winded >= 1 && seasoned && windOk;
        out.append(String.format(Locale.ROOT, "],\"dodgingMelee\":%d,\"twice\":%d,\"avgCarry\":%.2f,\"arrowsPassed\":%d,\"minStamina\":%.2f,\"winded\":%d,"
            + "\"veteran\":{\"prowess\":%.2f,\"stamina\":%.0f},\"fresh\":{\"prowess\":%.2f,\"stamina\":%.0f},\"seasoned\":%b,"
            + "\"emptied\":{\"winded\":%b,\"dodgesWinded\":%d,\"windBackAt\":%d},"
            + "\"error\":\"%s\",\"pass\":%b}", dodgingMelee, twice, avgCarry, seen, minStamina, winded, vetP, vetMax, freshP, freshMax, seasoned,
            r.forcedWinded, r.windedDodges, r.recoveredAt, error.replace('"', '\''), pass));
        LOG.info(out.toString());
        for (Entity en : r.made) {
            if (!en.isRemoved()) {
                en.discard();
            }
        }
        for (ChunkPos p : r.forced) {
            r.level.setChunkForced(p.x, p.z, false);
        }
        run = null;
        resultLogged = true;
    }
}
