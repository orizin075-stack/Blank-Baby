package jp.oror.reborn.ci;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;
import jp.oror.reborn.combat.Guns;
import jp.oror.reborn.mixin.MobGoalSelectorAccess;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.WrappedGoal;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.ai.memory.MemoryStatus;
import net.minecraft.world.entity.animal.IronGolem;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.living.LivingDamageEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (053) /oror gunmobs test: the mobs that carry guns (the user: "the mobs have guns too; that is probably where it is
 * broken, and monsters move badly"). First a census: twelve of each hostile humanoid of Minecraft and every mob of the
 * gun mods (TACZ Bandits, Pillagers Gun, Pillager Guns, JEG) spawned as in the wild, and what they hold. Then each kind
 * that came with a gun, and the hand-to-hand monsters handed the gun found most, in two lanes against an iron golem that
 * does not move: in the open twenty-four blocks off, and with a wall between them fourteen off (a way round on either
 * side). Fifteen seconds each: hits, how near it came, how far it walked, how long it stood while out of sight or reach,
 * the goals running half-way, and whether it still holds the gun at the end. GUN-CENSUS {...} and GUN-MOBS {...}.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class GunMobTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Gun Mobs");
    public static volatile boolean resultLogged;
    static final String[] VANILLA = {"pillager", "vindicator", "evoker", "zombie", "husk", "drowned", "skeleton", "stray", "wither_skeleton", "piglin",
        "piglin_brute", "zombified_piglin", "zombie_villager", "witch"};
    static final Set<String> GUN_MOD_MOBS = Set.of("tacz_bandits", "pillagers_gun", "pillagerguns", "jeg", "jegn");
    static final String[] HANDED = {"zombie", "skeleton", "wither_skeleton", "vindicator"};
    static final int CENSUS = 12, TICKS = 300, SPACING = 14;

    static final class Lane {
        String name;
        Mob mob;
        IronGolem golem;
        boolean walled;
        double minDist = 99, moved, lx, lz;
        int hits, still, pathTicks;
        String held = "", heldEnd = "";
        List<String> goals = new ArrayList<>();
    }

    private static final class Run {
        ServerLevel level;
        BlockPos at;
        int phase;
        long started;
        final List<Mob> census = new ArrayList<>();
        final List<Lane> lanes = new ArrayList<>();
        final List<int[]> chunks = new ArrayList<>();
    }

    private static Run run;

    private GunMobTest() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("gunmobs").then(Commands.literal("test")
            .requires(s -> s.hasPermission(2)).executes(c -> start(c.getSource())))));
    }

    private static List<EntityType<?>> kinds() {
        List<EntityType<?>> out = new ArrayList<>();
        for (String v : VANILLA) {
            out.add(BuiltInRegistries.ENTITY_TYPE.get(ResourceLocation.withDefaultNamespace(v)));
        }
        for (EntityType<?> t : BuiltInRegistries.ENTITY_TYPE) {
            if (GUN_MOD_MOBS.contains(BuiltInRegistries.ENTITY_TYPE.getKey(t).getNamespace())) {
                out.add(t);
            }
        }
        return out;
    }

    private static int start(CommandSourceStack src) {
        if (run != null) {
            return 0;
        }
        Run r = new Run();
        r.level = src.getServer().overworld();
        BlockPos o = BlockPos.containing(src.getPosition()).offset(4000, 0, 4000);
        for (int dx = -2; dx <= 22; dx++) {
            for (int dz = -4; dz <= 3; dz++) {
                int cx = (o.getX() >> 4) + dx, cz = (o.getZ() >> 4) + dz;
                r.level.setChunkForced(cx, cz, true);
                r.chunks.add(new int[]{cx, cz});
            }
        }
        r.level.getChunk(o);
        int y = Math.max(r.level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, o.getX(), o.getZ()), r.level.getSeaLevel() + 1) + 8;
        r.at = new BlockPos(o.getX(), y, o.getZ());
        r.level.setDayTime(18000L);
        // the census pen: a floor with a roof, where the spawned stand still until they are counted
        floor(r, -4, 330, -40, -20);
        List<EntityType<?>> kinds = kinds();
        int i = 0;
        for (EntityType<?> t : kinds) {
            for (int k = 0; k < CENSUS; k++) {
                Entity ent;
                try {
                    ent = t.create(r.level);
                } catch (RuntimeException ex) {
                    break;
                }
                if (!(ent instanceof Mob mob)) {
                    break;
                }
                mob.moveTo(r.at.getX() + (i % 80) * 4 + 0.5, r.at.getY(), r.at.getZ() - 30.5 + (k % 4) * 2, 0F, 0F);
                try {
                    mob.finalizeSpawn(r.level, r.level.getCurrentDifficultyAt(mob.blockPosition()), MobSpawnType.NATURAL, null);
                } catch (RuntimeException ex) {
                    LOG.warn("GUN-CENSUS-SPAWN {} {}", BuiltInRegistries.ENTITY_TYPE.getKey(t), ex.toString());
                }
                mob.setPersistenceRequired();
                r.level.addFreshEntity(mob);
                mob.setNoAi(true);
                r.census.add(mob);
            }
            i++;
        }
        r.started = r.level.getGameTime();
        run = r;
        LOG.info("GUN-MOBS-START {\"kinds\":{},\"spawned\":{}}", kinds.size(), r.census.size());
        return 1;
    }

    private static void floor(Run r, int x0, int x1, int z0, int z1) {
        for (int dx = x0; dx <= x1; dx++) {
            for (int dz = z0; dz <= z1; dz++) {
                r.level.setBlock(r.at.offset(dx, -1, dz), Blocks.STONE.defaultBlockState(), 2);
                for (int h = 0; h < 6; h++) {
                    r.level.setBlock(r.at.offset(dx, h, dz), Blocks.AIR.defaultBlockState(), 2);
                }
            }
        }
    }

    private static String id(ItemStack s) {
        return s.isEmpty() ? "empty" : BuiltInRegistries.ITEM.getKey(s.getItem()).toString();
    }

    /** The census (a few ticks after they joined, so that what a mod hands them on joining is there too), then the lanes. */
    private static void census(Run r) {
        Map<String, Map<String, Integer>> held = new TreeMap<>();
        Map<String, Integer> guns = new TreeMap<>();
        Map<String, ItemStack> gunOf = new LinkedHashMap<>();
        Map<String, Integer> gunCount = new TreeMap<>();
        for (Mob m : r.census) {
            String type = BuiltInRegistries.ENTITY_TYPE.getKey(m.getType()).toString();
            ItemStack main = m.getMainHandItem();
            held.computeIfAbsent(type, k -> new TreeMap<>()).merge(id(main), 1, Integer::sum);
            if (Guns.held(main)) {
                guns.merge(type, 1, Integer::sum);
                gunOf.putIfAbsent(type, main.copy());
                gunCount.merge(id(main), 1, Integer::sum);
            }
        }
        StringBuilder b = new StringBuilder("{");
        held.forEach((type, items) -> {
            b.append(b.length() > 1 ? "," : "").append('"').append(type).append("\":{\"guns\":").append(guns.getOrDefault(type, 0)).append(",\"held\":{");
            StringBuilder c = new StringBuilder();
            items.forEach((it, n) -> c.append(c.length() > 0 ? "," : "").append('"').append(it).append("\":").append(n));
            b.append(c).append("}}");
        });
        LOG.info("GUN-CENSUS {}}", b);
        for (Mob m : r.census) {
            m.discard();
        }
        r.census.clear();
        // the gun found most, for the hand-to-hand monsters
        String common = gunCount.entrySet().stream().max(Map.Entry.comparingByValue()).map(Map.Entry::getKey).orElse(null);
        ItemStack handed = null;
        for (ItemStack s : gunOf.values()) {
            if (id(s).equals(common)) {
                handed = s;
                break;
            }
        }
        List<String[]> plan = new ArrayList<>();
        for (String type : gunOf.keySet()) {
            plan.add(new String[]{type, ""});
        }
        if (handed != null) {
            for (String h : HANDED) {
                plan.add(new String[]{"minecraft:" + h, "handed"});
            }
        }
        floor(r, -4, plan.size() * 2 * SPACING + 4, -4, 30);
        int lane = 0;
        for (String[] p : plan) {
            for (boolean walled : new boolean[]{false, true}) {
                EntityType<?> t = BuiltInRegistries.ENTITY_TYPE.get(ResourceLocation.parse(p[0]));
                Entity ent = t.create(r.level);
                if (!(ent instanceof Mob mob)) {
                    continue;
                }
                int x = r.at.getX() + lane * SPACING;
                // walls between the lanes
                for (int dz = -4; dz <= 30; dz++) {
                    for (int h = 0; h < 5; h++) {
                        r.level.setBlock(new BlockPos(x - SPACING / 2, r.at.getY() + h, r.at.getZ() + dz), Blocks.STONE.defaultBlockState(), 2);
                    }
                }
                double gz = walled ? 14.5 : 24.5;
                if (walled) {
                    // a wall across the middle of the lane, five wide and five high: a way round on either side
                    for (int dx = -2; dx <= 2; dx++) {
                        for (int h = 0; h < 5; h++) {
                            r.level.setBlock(new BlockPos(x + dx, r.at.getY() + h, r.at.getZ() + 7), Blocks.STONE.defaultBlockState(), 2);
                        }
                    }
                }
                mob.moveTo(x + 0.5, r.at.getY(), r.at.getZ() + 0.5, 0F, 0F);
                mob.finalizeSpawn(r.level, r.level.getCurrentDifficultyAt(mob.blockPosition()), MobSpawnType.NATURAL, null);
                if (!p[1].isEmpty()) {
                    mob.setItemSlot(net.minecraft.world.entity.EquipmentSlot.MAINHAND, handed.copy());
                } else if (!Guns.held(mob.getMainHandItem()) && gunOf.containsKey(p[0])) {
                    mob.setItemSlot(net.minecraft.world.entity.EquipmentSlot.MAINHAND, gunOf.get(p[0]).copy());
                }
                mob.setPersistenceRequired();
                r.level.addFreshEntity(mob);
                IronGolem golem = EntityType.IRON_GOLEM.create(r.level);
                golem.moveTo(x + 0.5, r.at.getY(), r.at.getZ() + gz, 180F, 0F);
                golem.setNoAi(true);
                golem.getAttribute(Attributes.MAX_HEALTH).setBaseValue(2000);
                golem.setHealth(2000F);
                r.level.addFreshEntity(golem);
                Lane l = new Lane();
                l.name = p[0].replace("minecraft:", "") + (p[1].isEmpty() ? "" : "+gun") + (walled ? "/walled" : "/open");
                l.mob = mob;
                l.golem = golem;
                l.walled = walled;
                l.held = id(mob.getMainHandItem());
                l.lx = mob.getX();
                l.lz = mob.getZ();
                aim(mob, golem);
                r.lanes.add(l);
                lane++;
            }
        }
        r.phase = 1;
        r.started = r.level.getGameTime();
        LOG.info("GUN-MOBS-LANES {\"lanes\":{},\"handed\":\"{}\"}", r.lanes.size(), handed == null ? "" : id(handed));
    }

    private static void aim(Mob m, IronGolem golem) {
        m.setTarget(golem);
        if (m.getBrain().checkMemory(MemoryModuleType.ATTACK_TARGET, MemoryStatus.REGISTERED)) {
            m.getBrain().setMemory(MemoryModuleType.ATTACK_TARGET, golem);
        }
    }

    @SubscribeEvent
    public static void hit(LivingDamageEvent.Post e) {
        Run r = run;
        if (r == null || r.phase != 1 || !(e.getEntity() instanceof IronGolem g)) {
            return;
        }
        for (Lane l : r.lanes) {
            if (l.golem == g && (e.getSource().getEntity() == l.mob || e.getSource().getDirectEntity() == l.mob)) {
                l.hits++;
            }
        }
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        Run r = run;
        if (r == null) {
            return;
        }
        long age = r.level.getGameTime() - r.started;
        if (r.phase == 0) {
            if (age >= 5) {
                census(r);
            }
            return;
        }
        for (Lane l : r.lanes) {
            Mob m = l.mob;
            if (!m.isAlive()) {
                continue;
            }
            if (age % 10 == 0 && m.getTarget() != l.golem) {
                aim(m, l.golem);
            }
            double d = m.distanceTo(l.golem);
            l.minDist = Math.min(l.minDist, d);
            double step = Math.hypot(m.getX() - l.lx, m.getZ() - l.lz);
            l.moved += step;
            boolean sees = m.getSensing().hasLineOfSight(l.golem);
            if (step < 0.01 && (!sees || d > 20)) {
                l.still++;
            }
            if (m.getNavigation().getPath() != null && !m.getNavigation().isDone()) {
                l.pathTicks++;
            }
            l.lx = m.getX();
            l.lz = m.getZ();
            if (age == TICKS / 2) {
                TreeSet<String> running = new TreeSet<>();
                for (WrappedGoal w : ((MobGoalSelectorAccess) m).oror$getGoals().getAvailableGoals()) {
                    if (w.isRunning()) {
                        running.add(w.getGoal().getClass().getName().replaceAll("^.*\\.", ""));
                    }
                }
                l.goals.addAll(running);
            }
        }
        if (age < TICKS) {
            return;
        }
        run = null;
        StringBuilder b = new StringBuilder("{");
        int ok = 0;
        for (Lane l : r.lanes) {
            l.heldEnd = id(l.mob.getMainHandItem());
            // a gunner does its work if it hits the golem; out of sight it has to find a way round to do so
            boolean fine = l.hits >= 1;
            ok += fine ? 1 : 0;
            b.append(b.length() > 1 ? "," : "").append('"').append(l.name).append("\":").append(String.format(Locale.ROOT,
                "{\"held\":\"%s\",\"heldEnd\":\"%s\",\"hits\":%d,\"minDist\":%.1f,\"moved\":%.1f,\"stillTicks\":%d,\"pathTicks\":%d,\"alive\":%b,\"ok\":%b,\"goals\":%s}",
                l.held, l.heldEnd, l.hits, l.minDist, l.moved, l.still, l.pathTicks, l.mob.isAlive(), fine,
                l.goals.stream().map(s -> "\"" + s + "\"").toList()));
        }
        b.append(",\"lanes\":").append(r.lanes.size()).append(",\"ok\":").append(ok).append('}');
        LOG.info("GUN-MOBS {}", b);
        for (Entity x : r.level.getEntities((Entity) null, new AABB(r.at).inflate(400, 30, 60), x -> !(x instanceof Player))) {
            x.discard();
        }
        for (int[] c : r.chunks) {
            r.level.setChunkForced(c[0], c[1], false);
        }
        resultLogged = true;
    }
}
