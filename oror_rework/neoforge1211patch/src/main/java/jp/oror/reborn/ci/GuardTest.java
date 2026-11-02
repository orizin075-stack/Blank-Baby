package jp.oror.reborn.ci;

import com.mojang.authlib.GameProfile;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import jp.oror.reborn.combat.MobGuard;
import jp.oror.reborn.royal.RoyalArmory;
import jp.oror.reborn.royal.RoyalMob;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.projectile.Arrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (052) The guard check, /oror guards test: OROR's guard and parry on mobs that had none (a vindicator with an axe, a
 * wither skeleton with a sword, a bare-handed zombie, a skeleton with a bow, a spider, a piglin brute), each struck from the front by a fake
 * player every half second for twelve seconds, counting its parries, blocks and broken guards and the tester's being
 * parried; a parried zombie's stagger; then a kingdom guard's weapons against an enemy held at two, ten and twenty-six
 * blocks and twelve blocks up (sword, pistol, bow, bow), what he holds and what he fires; then a village guard with a
 * pistol, the enemy at two blocks and at ten. Logged as GUARD-MOBS, GUARD-ROYAL, GUARD-VILLAGE and GUARD-RESULT.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class GuardTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Guard");
    public static volatile boolean resultLogged;

    static final class Tester extends FakePlayer {
        Tester(ServerLevel level) {
            super(level, new GameProfile(UUID.fromString("0f0e0d0c-0b0a-4908-8706-050403020101"), "[OROR Guard]"));
        }

        void ready() {
            this.attackStrengthTicker = 200;
        }
    }

    static final class Run {
        ServerLevel level;
        BlockPos origin;
        final List<ChunkPos> forced = new ArrayList<>();
        final List<Entity> made = new ArrayList<>();
        String phase = "load";
        long phaseAt;
        Tester tester;
        final List<Mob> duelists = new ArrayList<>();
        final List<BlockPos> spots = new ArrayList<>();
        final Map<String, Object> result = new LinkedHashMap<>();
        Mob guard, villageGuard, dummy;
        int stage;
        int shotsBefore, arrowsBefore;
        final List<String> stages = new ArrayList<>();
    }

    private static Run run;

    private GuardTest() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("guards").then(Commands.literal("test")
            .requires(s -> s.hasPermission(2)).executes(c -> start(c.getSource())))));
    }

    private static int start(CommandSourceStack src) {
        if (run != null) {
            return 0;
        }
        Run r = new Run();
        r.level = src.getServer().overworld();
        r.origin = BlockPos.containing(src.getPosition()).offset(-2600, 0, 2600);
        for (int a = 0; a < 3; a++) {
            BlockPos at = r.origin.offset(a * 64, 0, 0);
            for (int dx = -2; dx <= 2; dx++) {
                for (int dz = -2; dz <= 2; dz++) {
                    ChunkPos p = new ChunkPos((at.getX() >> 4) + dx, (at.getZ() >> 4) + dz);
                    if (r.level.setChunkForced(p.x, p.z, true)) {
                        r.forced.add(p);
                    }
                }
            }
        }
        r.phaseAt = r.level.getGameTime();
        run = r;
        LOG.info("GUARD-START {\"at\":[{},{}]}", r.origin.getX(), r.origin.getZ());
        return 1;
    }

    private static BlockPos floor(ServerLevel level, BlockPos at) {
        level.getChunk(at);
        int y = Math.max(level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, at.getX(), at.getZ()), level.getSeaLevel() + 1);
        for (int dx = -18; dx <= 34; dx++) {
            for (int dz = -8; dz <= 8; dz++) {
                level.setBlock(new BlockPos(at.getX() + dx, y - 1, at.getZ() + dz), Blocks.STONE.defaultBlockState(), 2);
                for (int h = 0; h < 20; h++) {
                    BlockPos q = new BlockPos(at.getX() + dx, y + h, at.getZ() + dz);
                    if (!level.getBlockState(q).isAir()) {
                        level.setBlock(q, Blocks.AIR.defaultBlockState(), 2);
                    }
                }
            }
        }
        return new BlockPos(at.getX(), y, at.getZ());
    }

    private static Mob spawn(Run r, String id, BlockPos at, ItemStack main, double health) {
        EntityType<?> type = BuiltInRegistries.ENTITY_TYPE.getOptional(ResourceLocation.parse(id)).orElse(null);
        if (type == null) {
            return null;
        }
        Entity e = type.create(r.level);
        if (!(e instanceof Mob m)) {
            if (e != null) {
                e.discard();
            }
            return null;
        }
        m.moveTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5, 0, 0);
        m.setPersistenceRequired();
        r.level.addFreshEntity(m);
        if (main != null) {
            m.setItemSlot(EquipmentSlot.MAINHAND, main);
        }
        if (health > 0 && m.getAttribute(Attributes.MAX_HEALTH) != null) {
            m.getAttribute(Attributes.MAX_HEALTH).setBaseValue(health);
            m.setHealth((float) health);
        }
        r.made.add(m);
        return m;
    }

    private static void face(Mob m, Vec3 at) {
        Vec3 d = at.subtract(m.position());
        float yaw = (float) (Math.atan2(d.z, d.x) * 180 / Math.PI) - 90F;
        m.setYRot(yaw);
        m.setYHeadRot(yaw);
        m.yBodyRot = yaw;
        m.setXRot(0);
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
            r.result.put("error", ex.toString());
            LOG.error("GUARD-ERROR", ex);
            finish(r);
        }
    }

    private static void next(Run r, String phase) {
        r.phase = phase;
        r.phaseAt = r.level.getGameTime();
    }

    private static void step(Run r, long t) {
        switch (r.phase) {
            case "load" -> {
                if (t < 40) {
                    return;
                }
                BlockPos a = floor(r.level, r.origin);
                r.tester = new Tester(r.level);
                r.tester.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(Items.IRON_SWORD));
                String[][] who = {{"minecraft:vindicator", "iron_axe"}, {"minecraft:wither_skeleton", "stone_sword"}, {"minecraft:zombie", ""},
                    {"minecraft:skeleton", "bow"}, {"minecraft:spider", ""}, {"minecraft:piglin_brute", "golden_axe"}};
                for (int i = 0; i < who.length; i++) {
                    BlockPos spot = a.offset(-15 + i * 8, 0, 0);
                    ItemStack held = who[i][1].isEmpty() ? ItemStack.EMPTY
                        : new ItemStack(BuiltInRegistries.ITEM.get(ResourceLocation.withDefaultNamespace(who[i][1])));
                    Mob m = spawn(r, who[i][0], spot, held, 150);
                    if (m != null) {
                        m.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 100000, 10, false, false));
                        r.duelists.add(m);
                        r.spots.add(spot);
                    }
                }
                next(r, "duel");
            }
            case "duel" -> {
                // each mob held in its place facing the tester, who stands two blocks in front of it and strikes in turn
                for (int i = 0; i < r.duelists.size(); i++) {
                    Mob m = r.duelists.get(i);
                    BlockPos spot = r.spots.get(i);
                    Vec3 me = new Vec3(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
                    Vec3 front = me.add(0, 0, 2);
                    m.moveTo(me.x, me.y, me.z, m.getYRot(), 0);
                    m.setDeltaMovement(Vec3.ZERO);
                    face(m, front);
                    m.setTarget(r.tester);
                    m.setHealth(m.getMaxHealth());
                    if (t % 10 == (i * 2L) % 10 && t > 20) {
                        r.tester.moveTo(front.x, front.y, front.z, 180F, 0);
                        r.tester.ready();
                        r.tester.attack(m);
                    }
                }
                if (t >= 260) {
                    Map<String, String> tallies = new LinkedHashMap<>();
                    for (Mob m : r.duelists) {
                        tallies.put(BuiltInRegistries.ENTITY_TYPE.getKey(m.getType()).getPath(), MobGuard.describe(m) + " parry/block/break/parried "
                            + MobGuard.tally(m));
                    }
                    r.result.put("mobs", tallies);
                    r.result.put("testerParried", r.tester.getPersistentData().getInt("OrorParried"));
                    // a player's parry against a mob: the zombie thrown back and staggered
                    Mob zombie = r.duelists.stream().filter(m -> m.getType() == EntityType.ZOMBIE).findFirst().orElse(null);
                    if (zombie != null) {
                        zombie.removeAllEffects();
                        Vec3 before = zombie.getDeltaMovement();
                        MobGuard.parried(zombie, zombie.position().add(0, 0, 2));
                        r.result.put("parriedZombie", "push " + String.format("%.2f", zombie.getDeltaMovement().subtract(before).horizontalDistance())
                            + " slowed " + zombie.hasEffect(MobEffects.MOVEMENT_SLOWDOWN) + " count " + zombie.getPersistentData().getInt("OrorParried"));
                    }
                    LOG.info("GUARD-MOBS {}", json(r.result));
                    for (Mob m : r.duelists) {
                        m.discard();
                    }
                    next(r, "royal");
                }
            }
            case "royal" -> {
                BlockPos b = floor(r.level, r.origin.offset(64, 0, 0));
                r.guard = spawn(r, "oror_supreme_bosses:kingdom_guard", b, null, 0);
                r.dummy = spawn(r, "minecraft:pillager", b.offset(0, 0, 2), null, 4000);
                if (r.guard == null || r.dummy == null) {
                    r.result.put("royal", "no kingdom guard or no pillager");
                    next(r, "village");
                    return;
                }
                r.dummy.setNoAi(true);
                r.stage = 0;
                next(r, "royal_stage");
            }
            case "royal_stage" -> {
                double[][] at = {{2, 0}, {10, 0}, {26, 0}, {12, 12}};
                String[] names = {"2 blocks", "10 blocks", "26 blocks", "12 up"};
                double[] place = at[r.stage];
                Vec3 g = r.guard.position();
                Vec3 to = new Vec3(g.x + place[0], r.guard.getY() + place[1], g.z);
                r.dummy.moveTo(to.x, to.y, to.z, 0, 0);
                r.dummy.setDeltaMovement(Vec3.ZERO);
                r.dummy.setHealth(r.dummy.getMaxHealth());
                r.guard.setTarget(r.dummy);
                if (t == 1) {
                    CompoundTag d = r.guard.getPersistentData();
                    r.shotsBefore = d.getInt("RoyalNativeShots") + d.getInt("RoyalMeleeHits");
                    r.arrowsBefore = d.getInt("OrorArrows");
                }
                if (t >= 80) {
                    CompoundTag d = r.guard.getPersistentData();
                    int arrows = d.getInt("OrorArrows") - r.arrowsBefore;
                    r.stages.add(names[r.stage] + ": " + RoyalArmory.arm((RoyalMob) r.guard) + " "
                        + BuiltInRegistries.ITEM.getKey(r.guard.getMainHandItem().getItem()).getPath() + "+"
                        + BuiltInRegistries.ITEM.getKey(r.guard.getOffhandItem().getItem()).getPath()
                        + " hits/shots " + (d.getInt("RoyalNativeShots") + d.getInt("RoyalMeleeHits") - r.shotsBefore)
                        + " arrows " + arrows + " dist " + String.format("%.1f", r.guard.distanceTo(r.dummy)));
                    for (Arrow a : r.level.getEntitiesOfClass(Arrow.class, new AABB(r.guard.blockPosition()).inflate(60), a -> a.getOwner() == r.guard)) {
                        a.discard();
                    }
                    r.stage++;
                    if (r.stage >= at.length) {
                        r.result.put("royal", new ArrayList<>(r.stages));
                        LOG.info("GUARD-ROYAL {}", json(Map.of("stages", r.stages)));
                        r.guard.discard();
                        r.dummy.discard();
                        next(r, "village");
                    } else {
                        next(r, "royal_stage");
                    }
                }
            }
            case "village" -> {
                BlockPos c = floor(r.level, r.origin.offset(128, 0, 0));
                ItemStack pistol = new ItemStack(BuiltInRegistries.ITEM.get(ResourceLocation.parse("superbwarfare:glock_17")));
                r.villageGuard = spawn(r, "guardvillagers:guard", c, pistol, 0);
                r.dummy = spawn(r, "minecraft:pillager", c.offset(0, 0, 2), null, 4000);
                if (r.villageGuard == null || r.dummy == null) {
                    r.result.put("village", "no guard villager or no pillager");
                    finish(r);
                    return;
                }
                r.dummy.setNoAi(true);
                r.stage = 0;
                r.stages.clear();
                next(r, "village_stage");
            }
            case "village_stage" -> {
                double dist = r.stage == 0 ? 2 : 10;
                Vec3 g = r.villageGuard.position();
                r.dummy.moveTo(g.x + dist, r.villageGuard.getY(), g.z, 0, 0);
                r.dummy.setHealth(r.dummy.getMaxHealth());
                r.villageGuard.setTarget(r.dummy);
                if (t >= 80) {
                    r.stages.add((r.stage == 0 ? "2 blocks: " : "10 blocks: ") + BuiltInRegistries.ITEM.getKey(r.villageGuard.getMainHandItem().getItem()).getPath()
                        + " holstered " + r.villageGuard.getPersistentData().contains("OrorHolsteredGun"));
                    r.stage++;
                    if (r.stage >= 2) {
                        r.result.put("village", new ArrayList<>(r.stages));
                        LOG.info("GUARD-VILLAGE {}", json(Map.of("stages", r.stages)));
                        finish(r);
                    } else {
                        next(r, "village_stage");
                    }
                }
            }
            default -> finish(r);
        }
    }

    private static void finish(Run r) {
        for (Entity e : r.made) {
            if (!e.isRemoved()) {
                e.discard();
            }
        }
        for (ChunkPos p : r.forced) {
            r.level.setChunkForced(p.x, p.z, false);
        }
        LOG.info("GUARD-RESULT {}", json(r.result));
        run = null;
        resultLogged = true;
    }

    private static String json(Object o) {
        if (o instanceof Map<?, ?> m) {
            StringBuilder b = new StringBuilder("{");
            for (Map.Entry<?, ?> e : m.entrySet()) {
                if (b.length() > 1) {
                    b.append(',');
                }
                b.append('"').append(e.getKey()).append("\":").append(json(e.getValue()));
            }
            return b.append('}').toString();
        }
        if (o instanceof List<?> l) {
            StringBuilder b = new StringBuilder("[");
            for (Object x : l) {
                if (b.length() > 1) {
                    b.append(',');
                }
                b.append(json(x));
            }
            return b.append(']').toString();
        }
        if (o instanceof Number || o instanceof Boolean) {
            return String.valueOf(o);
        }
        return "\"" + String.valueOf(o).replace("\\", "\\\\").replace("\"", "'") + "\"";
    }
}
