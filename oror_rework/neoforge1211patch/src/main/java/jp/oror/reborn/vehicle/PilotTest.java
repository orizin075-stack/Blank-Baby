package jp.oror.reborn.vehicle;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.server.ServerStoppedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * /oror pilots test: a flight and drive check on a dedicated server. 800 blocks east of the caller it lays a stone runway
 * with a paved field beside it, parks a crewed ground-attack aircraft at the runway's west end and a crewed tank on the
 * field, and stands two still pillagers as targets (one 160 blocks down the runway for the aircraft, one 60 blocks off
 * for the tank). The aircraft should take off, attack, and once its target is gone (killed, or taken away after 45
 * seconds) fly back and land; the tank should drive up and fire. Every change of mode is logged with its time, and
 * FLIGHT-RESULT sums it up.
 * /oror pilots status lists the crewed vehicles within 300 blocks.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class PilotTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Vehicles");
    private static Run run;
    /** Set when a test has ended and its FLIGHT-RESULT is logged. */
    public static volatile boolean resultLogged;

    private static final class Run {
        ServerLevel level;
        long started;
        Entity plane, tank, heli;
        Mob planeTarget, tankTarget, cow, cowFoe;
        BlockPos origin;
        boolean handlessLogged;
        String lastMode = "";
        final List<String> modes = new ArrayList<>();
        final List<ChunkPos> forced = new ArrayList<>();
        double tankClosest = Double.MAX_VALUE;
        boolean targetGone, drained, planeDrained;
        String supplyBefore = "", planeBefore = "";
    }

    private PilotTest() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("pilots").requires(s -> s.hasPermission(2))
            .then(Commands.literal("test").executes(c -> start(c.getSource())))
            .then(Commands.literal("status").executes(c -> {
                ServerLevel level = c.getSource().getLevel();
                List<Entity> list = RoyalPilots.near(level, c.getSource().getPosition(), 300);
                c.getSource().sendSuccess(() -> Component.literal(list.isEmpty() ? "近くに王国の車両はありません。"
                    : String.join("\n", list.stream().map(RoyalPilots::report).toList())), false);
                return list.size();
            }))));
    }

    private static int start(CommandSourceStack src) {
        if (run != null || !Sbw.present()) {
            src.sendFailure(Component.literal(run != null ? "試験中です。" : "Superb Warfareがありません。"));
            return 0;
        }
        ServerLevel level = src.getLevel();
        Run r = new Run();
        r.level = level;
        BlockPos origin = flattest(level, BlockPos.containing(src.getPosition()));
        r.origin = origin;
        for (int dx = -12; dx <= 20; dx++) {
            for (int dz = -9; dz <= 9; dz++) {
                ChunkPos p = new ChunkPos((origin.getX() >> 4) + dx, (origin.getZ() >> 4) + dz);
                if (level.setChunkForced(p.x, p.z, true)) {
                    r.forced.add(p);
                }
            }
        }
        int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, origin.getX(), origin.getZ());
        // runway: 230 x 9 of stone, cleared 14 blocks up, heading east (yaw -90); south of it a paved field for the tank's
        // drive to its target (the test is of the driving, not of whatever ground or water is there)
        for (int x = -10; x < 220; x++) {
            for (int z = -9; z <= (x < 90 ? 44 : 4); z++) {
                level.setBlock(new BlockPos(origin.getX() + x, y - 1, origin.getZ() + z), Blocks.SMOOTH_STONE.defaultBlockState(), 2);
                level.setBlock(new BlockPos(origin.getX() + x, y - 2, origin.getZ() + z), Blocks.STONE.defaultBlockState(), 2);
                for (int h = 0; h < 14; h++) {
                    level.setBlock(new BlockPos(origin.getX() + x, y + h, origin.getZ() + z), Blocks.AIR.defaultBlockState(), 2);
                }
            }
        }
        // a low wall round the tank's field (off the runway), so a tank that turns the wrong way stays on it
        for (int x = -11; x <= 90; x++) {
            // the north wall four blocks off the runway's edge, clear of an aircraft's wing on its take-off run
            for (int z = 9; z <= 45; z++) {
                if (x == -11 || x == 90 || z == 9 || z == 45) {
                    // three high: a tank climbs a single block
                    for (int h = 0; h < 3; h++) {
                        level.setBlock(new BlockPos(origin.getX() + x, y + h, origin.getZ() + z), Blocks.STONE_BRICKS.defaultBlockState(), 2);
                    }
                }
            }
        }
        Vec3 start = new Vec3(origin.getX() + 0.5, y, origin.getZ() + 0.5);
        r.plane = RoyalPilots.deploy(level, start, -90F, Sbw.has("a_10a") ? "a_10a" : "j_16", 1, null);
        Vec3 tankAt = start.add(0, 0, 30);
        r.tank = RoyalPilots.deploy(level, tankAt, -90F, "m_1a_2", 2, null);
        // open sky over the helicopter's pad (the test ground lies among hills: nothing within 80 blocks above it)
        for (int x = -9; x <= 1; x++) {
            for (int z = 11; z <= 21; z++) {
                for (int h = 14; h < 80; h++) {
                    level.setBlock(new BlockPos(origin.getX() + x, y + h, origin.getZ() + z), Blocks.AIR.defaultBlockState(), 2);
                }
            }
        }
        r.heli = Sbw.has("ah_6") ? RoyalPilots.deploy(level, start.add(-4, 0, 16), -90F, "ah_6", 2, null) : null;
        // the posts' supply, as the citadel's: a charging station (coal-fed) and a depot beside the tank's start, the
        // helicopter's pad and the aircraft's stand at the runway's west end
        BlockPos o = BlockPos.containing(start);
        Supply.placeStation(level, o.offset(-6, 0, 30), 2_000_000, 16);
        Supply.placeDepot(level, o.offset(-6, 0, 34), "m_1a_2");
        Supply.placeStation(level, o.offset(-9, 0, 12), 2_000_000, 16);
        Supply.placeDepot(level, o.offset(1, 0, 12), "ah_6");
        Supply.placeStation(level, o.offset(0, 0, -9), 2_000_000, 16);
        Supply.placeDepot(level, o.offset(-3, 0, -9), "a_10a");
        survey(level, start);
        // a cow at war with a pillager (a mob without hands under the smart-mob combat): no bow, no arrows, its own spring
        Vec3 pen = start.add(-100, 0, -60);
        int py = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, (int) pen.x, (int) pen.z);
        r.cowFoe = target(level, new Vec3(pen.x + 9, py, pen.z));
        net.minecraft.world.entity.animal.Cow cow = EntityType.COW.create(level);
        if (cow != null && r.cowFoe != null) {
            cow.moveTo(pen.x, py, pen.z, -90F, 0F);
            cow.setPersistenceRequired();
            level.addFreshEntity(cow);
            cow.setTarget(r.cowFoe);
            r.cow = cow;
        }
        r.planeTarget = target(level, start.add(160, 0, 0));
        r.tankTarget = target(level, tankAt.add(60, 0, 8));
        r.started = level.getGameTime();
        run = r;
        LOG.info("FLIGHT-START {\"runway\":[{},{},{}],\"plane\":{},\"tank\":{}}", origin.getX(), y, origin.getZ(), r.plane != null, r.tank != null);
        src.sendSuccess(() -> Component.literal("飛行・走行試験を開始しました（" + origin.getX() + ", " + y + ", " + origin.getZ() + "）"), false);
        return 1;
    }

    /**
     * For choosing the kingdom's turrets and the vault's arms: which Superb Warfare vehicles a soldier can sit in (each
     * deployed once with a crew of one, its riders counted, then removed), and every item id of the war mods.
     */
    private static void survey(ServerLevel level, Vec3 start) {
        String[] ids = {"mk_42", "hpj_11", "tow", "laser_tower", "mortar", "type_63", "mle_1934", "fh_77bw", "bl_132", "waveforce_tower",
            "annihilator", "lav_ad", "lav_25", "lav_150", "sodayo_pick_up_tow", "sodayo_pick_up_hmg", "sodayo_pick_up_rocket", "yx_100",
            "plz_05", "prism_tank", "kv_16", "tom_6", "ztz_99a", "bmp_2", "bradley", "t_90a", "m_1a_2", "ah_6", "mi_28", "a_10a", "j_16"};
        List<String> rows = new ArrayList<>();
        int i = 0;
        for (String id : ids) {
            if (!Sbw.has(id)) {
                rows.add("{\"id\":\"" + id + "\",\"registered\":false}");
                continue;
            }
            Vec3 at = start.add(-30 - 9 * (i % 12), 0, -40 - 14 * (i / 12));
            i++;
            int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, (int) at.x, (int) at.z);
            Entity v = RoyalPilots.deploy(level, new Vec3(at.x, y, at.z), -90F, id, 1, null);
            if (v == null) {
                rows.add("{\"id\":\"" + id + "\",\"deployed\":false}");
                continue;
            }
            Object max = Sbw.call(v, "getMaxPassengers");
            rows.add(String.format(Locale.ROOT, "{\"id\":\"%s\",\"engine\":\"%s\",\"crew\":%d,\"seats\":%s,\"autoAim\":%b,\"class\":\"%s\"}",
                id, Sbw.engine(v), v.getPassengers().size(), max, isA(v, "com.atsuishio.superbwarfare.entity.vehicle.base.AutoAimableEntity"),
                v.getClass().getSimpleName()));
            v.getPassengers().forEach(Entity::discard);
            v.discard();
        }
        LOG.info("SEAT-SURVEY [{}]", String.join(",", rows));
        for (String ns : new String[]{"superbwarfare", "sbwdroneconfig", "halovecs"}) {
            List<String> items = new ArrayList<>();
            for (net.minecraft.resources.ResourceLocation key : net.minecraft.core.registries.BuiltInRegistries.ITEM.keySet()) {
                if (key.getNamespace().equals(ns)) {
                    net.minecraft.world.item.Item item = net.minecraft.core.registries.BuiltInRegistries.ITEM.get(key);
                    net.minecraft.world.item.ItemStack stack = item.getDefaultInstance();
                    items.add(key.getPath() + ":" + stack.getRarity().name().charAt(0) + (stack.isDamageableItem() ? "d" : "") + item.getClass().getSimpleName());
                }
            }
            java.util.Collections.sort(items);
            LOG.info("ITEMS-{} {} [{}]", ns, items.size(), String.join(" ", items));
        }
    }

    /**
     * The test ground: of eight places 800 to 1340 blocks from the caller (none near the capital), the flattest dry one,
     * by twelve heights over the 230 x 55 blocks of runway and field. Hills around the strip made a trench of it before:
     * aircraft flew into its sides, the tank slid off its edge and the helicopter rose under an overhang.
     */
    private static BlockPos flattest(ServerLevel level, BlockPos from) {
        int[][] offsets = {{800, 0}, {0, 800}, {-800, 0}, {0, -800}, {1200, 600}, {-1200, -600}, {600, -1200}, {-600, 1200},
            {900, 900}, {-900, 900}, {900, -900}, {-900, -900}, {1300, 0}, {0, 1300}, {-1300, 0}, {0, -1300}, {1600, 800}, {-1600, -800},
            {800, -1600}, {-800, 1600}};
        jp.oror.reborn.citadel.CitadelSites.Site capital = jp.oror.reborn.citadel.CitadelSites.capital();
        BlockPos best = from.offset(800, 0, 0);
        double bestScore = Double.MAX_VALUE;
        for (int[] o : offsets) {
            BlockPos c = from.offset(o[0], 0, o[1]);
            if (capital != null && capital.center().distSqr(new BlockPos(c.getX() + 110, capital.center().getY(), c.getZ() + 20)) < 1100 * 1100) {
                continue;
            }
            int lo = Integer.MAX_VALUE, hi = Integer.MIN_VALUE;
            boolean wet = false;
            for (int dx : new int[]{-10, 60, 130, 210}) {
                for (int dz : new int[]{-8, 20, 44}) {
                    // the generator's own height: the ground there before any chunk is made (a chunk not yet generated reads as empty)
                    int h = level.getChunkSource().getGenerator().getBaseHeight(c.getX() + dx, c.getZ() + dz, Heightmap.Types.OCEAN_FLOOR_WG, level,
                        level.getChunkSource().randomState());
                    lo = Math.min(lo, h);
                    hi = Math.max(hi, h);
                    wet |= h <= level.getSeaLevel();
                }
            }
            double score = hi - lo + (wet ? 400 : 0);
            LOG.info("PILOT-SITE {} {} spread {} wet {}", c.getX(), c.getZ(), hi - lo, wet);
            if (score < bestScore) {
                bestScore = score;
                best = c;
            }
        }
        return best;
    }

    private static boolean isA(Object o, String name) {
        try {
            return Class.forName(name).isInstance(o);
        } catch (ClassNotFoundException | LinkageError e) {
            return false;
        }
    }

    private static Mob target(ServerLevel level, Vec3 at) {
        Mob m = EntityType.PILLAGER.create(level);
        if (m == null) {
            return null;
        }
        int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, (int) at.x, (int) at.z);
        m.moveTo(at.x, y, at.z, 90F, 0F);
        m.setNoAi(true);
        m.setPersistenceRequired();
        m.addTag("oror_pilot_test_target");
        level.addFreshEntity(m);
        return m;
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        Run r = run;
        if (r == null) {
            return;
        }
        long t = r.level.getGameTime() - r.started;
        if (r.plane != null) {
            String mode = r.plane.getPersistentData().getCompound("OrorPilot").getString("Mode");
            if (!mode.equals(r.lastMode)) {
                r.modes.add("[" + t + ",\"" + mode + "\"," + (int) r.plane.getY() + "]");
                r.lastMode = mode;
            }
        }
        if (r.cow != null && !r.handlessLogged && t >= 400) {
            r.handlessLogged = true;
            net.minecraft.nbt.CompoundTag mind = jp.oror.reborn.MobMind.data(r.cow);
            LOG.info(String.format(Locale.ROOT, "HANDLESS-CHECK {\"cowAlive\":%b,\"mainHand\":\"%s\",\"chest\":\"%s\",\"shots\":%d,\"pounced\":%b,"
                    + "\"strikes\":%d,\"foeHealth\":%.1f,\"selected\":\"%s\"}",
                r.cow.isAlive(), net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(r.cow.getMainHandItem().getItem()),
                net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(r.cow.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.CHEST).getItem()),
                mind.getInt("Shots"), mind.contains("NextPounce"), mind.getInt("Strikes"), r.cowFoe == null ? -1F : r.cowFoe.getHealth(),
                mind.getString("Selected")));
        }
        if (r.tank != null && r.tankTarget != null) {
            // the tank's orders: this target, not whatever else its crew happens to see in the hills about
            if (t % 20 == 0 && r.tankTarget.isAlive()) {
                for (Entity rider : r.tank.getPassengers()) {
                    if (rider instanceof Mob m) {
                        m.setTarget(r.tankTarget);
                    }
                }
            }
            if (t % 40 == 0) {
                net.minecraft.nbt.CompoundTag tp = r.tank.getPersistentData().getCompound("OrorPilot");
                LOG.info(String.format(Locale.ROOT, "TANK-TRACK {\"t\":%d,\"x\":%.1f,\"y\":%.1f,\"z\":%.1f,\"yaw\":%.0f,\"toTarget\":%.1f,\"mode\":\"%s\","
                        + "\"noseBack\":%b,\"facingScore\":%d,\"steerSign\":%d,\"speed\":%.2f}",
                    t, r.tank.getX() - r.origin.getX(), r.tank.getY(), r.tank.getZ() - r.origin.getZ(), r.tank.getYRot(), r.tank.distanceTo(r.tankTarget),
                    tp.getString("Mode"), tp.getBoolean("NoseBack"), tp.getInt("FacingScore"), tp.contains("SteerSign") ? tp.getInt("SteerSign") : 1,
                    r.tank.getDeltaMovement().horizontalDistance()));
            }
            r.tankClosest = Math.min(r.tankClosest, r.tank.distanceTo(r.tankTarget));
        }
        if (r.heli != null && r.planeTarget != null && r.planeTarget.isAlive() && t % 20 == 0 && t >= 200) {
            // the helicopter's orders: the aircraft's target down the runway (it lifts off, stands off and fires)
            for (Entity rider : r.heli.getPassengers()) {
                if (rider instanceof Mob m) {
                    m.setTarget(r.planeTarget);
                }
            }
        }
        if (!r.targetGone && r.planeTarget != null && (!r.planeTarget.isAlive() || t > 900)) {
            r.targetGone = true;
            r.modes.add("[" + t + ",\"target-gone:" + (r.planeTarget.isAlive() ? "removed" : "killed") + "\",0]");
            r.planeTarget.discard();
        }
        // the supply test: at 70 s the tank and the helicopter, at 100 s the aircraft, are left with a fifth of their
        // battery and no shells; each should go back to its post, be charged by its station and loaded from its depot
        if (!r.drained && t >= 1400) {
            r.drained = true;
            StringBuilder b = new StringBuilder();
            for (Entity x : new Entity[]{r.tank, r.heli}) {
                if (x != null && x.isAlive()) {
                    Supply.drain(x, 0.2);
                    b.append(b.length() > 0 ? "," : "").append(Supply.report(r.level, x));
                }
            }
            r.supplyBefore = b.toString();
            LOG.info("SUPPLY-DRAIN [{}]", r.supplyBefore);
        }
        if (!r.planeDrained && t >= 2000 && r.plane != null && r.plane.isAlive()) {
            r.planeDrained = true;
            Supply.drain(r.plane, 0.2);
            r.planeBefore = Supply.report(r.level, r.plane);
            LOG.info("SUPPLY-DRAIN [{}]", r.planeBefore);
        }
        boolean landed = r.plane != null && r.plane.getPersistentData().getCompound("OrorPilot").getBoolean("Landed")
            && r.lastMode.equals("parked") && t > 4000;
        if (landed || t > 4800 || r.plane == null || !r.plane.isAlive()) {
            StringBuilder after = new StringBuilder();
            for (Entity x : new Entity[]{r.tank, r.heli, r.plane}) {
                if (x != null && x.isAlive()) {
                    net.minecraft.nbt.CompoundTag xp = x.getPersistentData().getCompound("OrorPilot");
                    Vec3 home = Vec3.atBottomCenterOf(BlockPos.of(xp.getLong("Home")));
                    String rep = Supply.report(r.level, x);
                    after.append(after.length() > 0 ? "," : "").append(rep, 0, rep.length() - 1).append(String.format(Locale.ROOT,
                        ",\"mode\":\"%s\",\"fromPost\":%.1f,\"resupplying\":%b,\"resupplies\":%d,\"reloaded\":%d}", xp.getString("Mode"),
                        x.position().subtract(home).horizontalDistance(), xp.getBoolean("Resupply"), xp.getInt("Resupplies"), xp.getInt("Reloaded")));
                }
            }
            LOG.info("SUPPLY-TEST {\"before\":[{}{}{}],\"after\":[{}]}", r.supplyBefore, r.planeBefore.isEmpty() ? "" : ",", r.planeBefore, after);
            String line = String.format(Locale.ROOT, "{\"seconds\":%.1f,\"plane\":%s,\"modes\":[%s],\"tank\":%s,\"tankClosest\":%.1f,"
                    + "\"tankTargetHealth\":%.1f,\"planeTarget\":\"%s\"}",
                t / 20.0, r.plane == null ? "null" : RoyalPilots.report(r.plane), String.join(",", r.modes),
                r.tank == null ? "null" : RoyalPilots.report(r.tank) + ",\"heli\":" + (r.heli == null ? "null" : RoyalPilots.report(r.heli)), r.tankClosest,
                r.tankTarget == null ? -1F : r.tankTarget.isAlive() ? r.tankTarget.getHealth() : 0F,
                r.planeTarget == null ? "none" : r.planeTarget.isAlive() ? "alive" : "gone");
            LOG.info("FLIGHT-RESULT {}", line);
            resultLogged = true;
            for (Entity x : new Entity[]{r.plane, r.tank, r.heli, r.planeTarget, r.tankTarget, r.cow, r.cowFoe}) {
                if (x != null && x.isAlive()) {
                    x.getPassengers().forEach(Entity::discard);
                    x.discard();
                }
            }
            for (ChunkPos p : r.forced) {
                r.level.setChunkForced(p.x, p.z, false);
            }
            run = null;
        }
    }

    @SubscribeEvent
    public static void stopped(ServerStoppedEvent e) {
        run = null;
    }
}
