package jp.oror.reborn;

import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.WeakHashMap;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.fml.ModList;
import org.joml.Quaternionf;

/**
 * Tanks and fighter jets (v0.17.15): Superb Warfare's own vehicles, driven and flown by the village's strong villagers.
 * - A 城下町 with guns builds a tank (M1A2, T-90A or ZTZ-99A) from its chests; after the Nether it adds a fighter jet (J-16,
 *   or the A-10A). Both are kept in the village's motor pool (not in the world) until they are needed.
 * - When something serious comes near the village (a creature of 80 health or more, or six hostiles at once), the tank
 *   is brought out: two strong villagers walk over and board it, the driver drives it with Superb Warfare's own
 *   controls (throttle and steering inputs, its own tracks and physics) toward the threat and holds at about 18 blocks,
 *   and the crew's target is the vehicle's target, so its turret aims and its cannon and machine guns fire by its own
 *   gunnery. Something flying, or of 200 health or more, brings out the jet instead: it scrambles over the village with
 *   its crew and circles the threat with Superb Warfare's own autopilot (loiter), firing its cannon and missiles.
 * - Once the threat has been gone for half a minute the tank drives back to the motor pool and is put away; the jet
 *   flies home. A vehicle wrecked in battle is lost and has to be built again. Each sortie costs gunpowder and iron for
 *   its shells and rounds; its energy is charged at the motor pool.
 * - Players are not let into a village vehicle (in Superb Warfare a player boarding takes the driver's seat).
 */
public final class VillageVehicles {
    private static final Map<Entity, UUID> ACTIVE = new WeakHashMap<>();
    private static final Map<String, Method> METHODS = new HashMap<>();
    private static final String[] TANKS = {"m_1a_2", "t_90a", "ztz_99a"};
    private static final String[] JETS = {"j_16", "a_10a"};
    private static int failures;
    private static boolean broken;

    private VillageVehicles() {
    }

    static boolean present() {
        return !broken && ModList.get().isLoaded("superbwarfare");
    }

    private static EntityType<?> type(String[] ids) {
        for (String id : ids) {
            ResourceLocation rl = new ResourceLocation("superbwarfare", id);
            if (BuiltInRegistries.ENTITY_TYPE.containsKey(rl)) {
                return (EntityType<?>)BuiltInRegistries.ENTITY_TYPE.get(rl);
            }
        }
        return null;
    }

    private static boolean ours(Entity e) {
        ResourceLocation id = BuiltInRegistries.ENTITY_TYPE.getKey(e.getType());
        return id.getNamespace().equals("superbwarfare") && (List.of(TANKS).contains(id.getPath()) || List.of(JETS).contains(id.getPath()));
    }

    private static String label(String kind) {
        return kind.equals("jet") ? "戦闘機" : "戦車";
    }

    // ------------------------------------------------------------------------------------- the review (every 30 s)
    static void review(ServerLevel sl, VillageWork.Survey s, VillageProgress.Record r) {
        if (!present() || !r.guns) {
            return;
        }
        long now = sl.getGameTime();
        if (r.sortie != null) {
            advance(sl, s, r, now);
            return;
        }
        if (r.stage >= 3 && !r.vehicles.contains("tank") && type(TANKS) != null && s.stock("iron_ingot") >= 96 && s.stock("gunpowder") >= 24
            && s.stock("redstone") >= 16 && s.stock("emerald") >= 48) {
            VillageExpeditions.take(sl, s, "iron_ingot", 96);
            VillageExpeditions.take(sl, s, "gunpowder", 24);
            VillageExpeditions.take(sl, s, "redstone", 16);
            VillageExpeditions.take(sl, s, "emerald", 48);
            r.vehicles = r.vehicles + "tank,";
            VillageProgress.get(sl).setDirty();
            VillageProgress.announce(sl, s.village, "村の工房で戦車を製造しました（危険が迫ると強い村人が乗って出撃します）", true);
            return;
        }
        if (r.stage >= 4 && !r.vehicles.contains("jet") && type(JETS) != null && s.stock("iron_ingot") >= 80 && s.stock("gold_ingot") >= 16
            && s.stock("redstone") >= 24 && s.stock("gunpowder") >= 16 && s.stock("emerald") >= 64) {
            VillageExpeditions.take(sl, s, "iron_ingot", 80);
            VillageExpeditions.take(sl, s, "gold_ingot", 16);
            VillageExpeditions.take(sl, s, "redstone", 24);
            VillageExpeditions.take(sl, s, "gunpowder", 16);
            VillageExpeditions.take(sl, s, "emerald", 64);
            r.vehicles = r.vehicles + "jet,";
            VillageProgress.get(sl).setDirty();
            VillageProgress.announce(sl, s.village, "村の工房で戦闘機を製造しました（空の脅威や強敵には緊急発進します）", true);
            return;
        }
        if (now < r.nextSortie || r.vehicles.isEmpty()) {
            return;
        }
        LivingEntity t = threat(sl, s.village);
        if (t == null) {
            return;
        }
        boolean air = flying(t) || t.getMaxHealth() >= 200.0F;
        String kind = air && r.vehicles.contains("jet") ? "jet" : (r.vehicles.contains("tank") ? "tank" : (r.vehicles.contains("jet") ? "jet" : null));
        if (kind != null) {
            sortie(sl, s, r, kind, t, now);
        }
    }

    /** Something serious near the village: the strongest hostile within 64 blocks, if it is big or comes with many others. */
    static LivingEntity threat(ServerLevel sl, VillageLedger.Village v) {
        // not what is down in the caves below
        List<LivingEntity> foes = sl.getEntitiesOfClass(LivingEntity.class, new AABB(v.center).inflate(64.0, 48.0, 64.0),
            e -> hostile(e) && e.getY() > v.center.getY() - 12.0);
        if (foes.isEmpty()) {
            return null;
        }
        LivingEntity big = foes.stream().max(Comparator.comparingDouble(LivingEntity::getMaxHealth)).get();
        return big.getMaxHealth() >= 80.0F || foes.size() >= 6 ? big : null;
    }

    private static boolean hostile(LivingEntity e) {
        if (!e.isAlive() || e instanceof Villager || e instanceof Player) {
            return false;
        }
        return e instanceof Enemy || e instanceof Mob m && m.getTarget() instanceof Villager;
    }

    private static boolean flying(LivingEntity e) {
        String id = BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).getPath();
        return id.contains("phantom") || id.contains("ghast") || id.contains("blaze") || id.contains("dragon") || id.contains("wither") || id.contains("vex")
            || !e.onGround() && e.isNoGravity();
    }

    // ------------------------------------------------------------------------------------- sorties
    private static void sortie(ServerLevel sl, VillageWork.Survey s, VillageProgress.Record r, String kind, LivingEntity t, long now) {
        boolean jet = kind.equals("jet");
        EntityType<?> type = type(jet ? JETS : TANKS);
        BlockPos pool = pool(sl, s);
        if (type == null || pool == null) {
            r.nextSortie = now + 1200L;
            return;
        }
        String id = BuiltInRegistries.ENTITY_TYPE.getKey(type).getPath();
        int seats = id.equals("a_10a") ? 1 : 2;
        List<Villager> crew = sl.getEntitiesOfClass(Villager.class, new AABB(s.village.center).inflate(64.0, 24.0, 64.0),
                v -> v.isAlive() && VillageAI.strong(v) && !v.isSleeping() && !VillagerIndustry.miner(v) && !v.isPassenger()
                    && !VillagerLife.data(v).contains("Trip") && !VillagerLife.data(v).hasUUID("Flight") && !VillagerLife.data(v).hasUUID("Sortie")
                    && !v.getPersistentData().getBoolean("OrorWanderer") && VillageLedger.of(v) == s.village)
            .stream()
            .sorted(Comparator.comparingInt(VillageExpeditions::power).reversed())
            .limit(seats)
            .toList();
        if (crew.isEmpty()) {
            r.nextSortie = now + 600L;
            return;
        }
        Entity vehicle = type.create(sl);
        if (vehicle == null) {
            return;
        }
        Vec3 dir = t.position().subtract(Vec3.atCenterOf(pool)).multiply(1.0, 0.0, 1.0);
        dir = dir.lengthSqr() < 1.0E-4 ? new Vec3(0.0, 0.0, 1.0) : dir.normalize();
        float yaw = (float)(Math.atan2(dir.z, dir.x) * 180.0 / Math.PI) - 90.0F;
        if (jet) {
            vehicle.moveTo(pool.getX() + 0.5 - dir.x * 30.0, pool.getY() + 45.0, pool.getZ() + 0.5 - dir.z * 30.0, yaw, 0.0F);
        } else {
            vehicle.moveTo(pool.getX() + 0.5, pool.getY(), pool.getZ() + 0.5, yaw, 0.0F);
        }
        if (!sl.addFreshEntity(vehicle)) {
            return;
        }
        VillageFlights.mark(vehicle, s.village.id);
        charge(vehicle);
        arm(sl, s, vehicle, jet);
        CompoundTag so = new CompoundTag();
        so.putString("Kind", kind);
        so.putUUID("Vehicle", vehicle.getUUID());
        so.putString("Phase", jet ? "fight" : "board");
        so.putLong("Since", now);
        so.putLong("Started", now);
        so.putLong("Pool", pool.asLong());
        ListTag ids = new ListTag();
        for (Villager v : crew) {
            ids.add(VillageProgress.uuid(v.getUUID()));
            VillagerLife.data(v).putUUID("Sortie", s.village.id);
            if (jet) {
                // a scramble: the crew is aboard as the jet comes over the village
                sl.sendParticles(ParticleTypes.CLOUD, v.getX(), v.getY() + 1.0, v.getZ(), 10, 0.3, 0.5, 0.3, 0.05);
                v.startRiding(vehicle, true);
            }
        }
        so.put("Crew", ids);
        if (jet) {
            call(vehicle, "setPower", 1.0F);
            call(vehicle, "setEngineStart", true);
            call(vehicle, "setEngineStartOver", true);
            vehicle.setDeltaMovement(dir.scale(1.2));
            loiter(vehicle, t.position(), 36.0, t.getY() + 30.0);
        }
        r.sortie = so;
        ACTIVE.put(vehicle, s.village.id);
        VillageProgress.get(sl).setDirty();
        VillageProgress.announce(sl, s.village, t.getName().getString() + "の接近に、" + label(kind) + (jet ? "が緊急発進しました" : "が出撃します"), false);
    }

    /** The motor pool: a level open patch near the centre (the airfield's finder). */
    private static BlockPos pool(ServerLevel sl, VillageWork.Survey s) {
        if (s.pool != null && VillageFlights.clear(sl, s.pool)) {
            return s.pool;
        }
        BlockPos c = s.village.center;
        for (int i = 0; i < 16; i++) {
            double a = sl.random.nextDouble() * Math.PI * 2.0;
            double d = 10.0 + sl.random.nextDouble() * 14.0;
            BlockPos p = VillageExpeditions.top(sl, c.offset((int)Math.round(Math.cos(a) * d), 0, (int)Math.round(Math.sin(a) * d)));
            if (p != null && Math.abs(p.getY() - c.getY()) <= 4 && VillageFlights.clear(sl, p)) {
                s.pool = p;
                return p;
            }
        }
        return null;
    }

    /** Full energy at the motor pool. */
    private static void charge(Entity vehicle) {
        if (Boolean.TRUE.equals(call(vehicle, "hasEnergyStorage"))) {
            Object max = call(vehicle, "getMaxEnergy");
            if (max instanceof Number n) {
                call(vehicle, "setEnergy", n.intValue());
            }
        }
    }

    /** Shells, rounds and missiles into the vehicle's own hold; the village pays gunpowder and iron for them. */
    private static void arm(ServerLevel sl, VillageWork.Survey s, Entity vehicle, boolean jet) {
        int paid = VillageExpeditions.take(sl, s, "gunpowder", 8) + VillageExpeditions.take(sl, s, "iron_ingot", 4);
        int scale = paid >= 12 ? 2 : 1;
        String[][] load = jet
            ? new String[][]{{"small_shell_ap", "64"}, {"small_shell_ap", "64"}, {"large_anti_ground_missile", "4"}, {"small_rocket", "16"}}
            : new String[][]{{"large_shell_he", "8"}, {"large_shell_ap", "6"}, {"rifle_ammo", "64"}, {"heavy_ammo", "64"}};
        int slot = 0;
        for (String[] l : load) {
            ResourceLocation rl = new ResourceLocation("superbwarfare", l[0]);
            if (!BuiltInRegistries.ITEM.containsKey(rl)) {
                continue;
            }
            Item item = (Item)BuiltInRegistries.ITEM.get(rl);
            int n = Math.min(item.getDefaultInstance().getMaxStackSize(), Integer.parseInt(l[1]) * scale);
            call(vehicle, "setItem", slot++, item.getDefaultInstance().copyWithCount(n));
        }
    }

    private static void loiter(Entity jet, Vec3 over, double radius, double altitude) {
        call(jet, "setLoiterParams", new Quaternionf((float)over.x, (float)altitude, (float)over.z, (float)radius));
        call(jet, "setLoiterActive", true);
    }

    // ------------------------------------------------------------------------------------- under way (every 30 s)
    private static void advance(ServerLevel sl, VillageWork.Survey s, VillageProgress.Record r, long now) {
        CompoundTag so = r.sortie;
        Entity vehicle = so.hasUUID("Vehicle") ? sl.getEntity(so.getUUID("Vehicle")) : null;
        if (vehicle == null && !VillageFlights.gone(so)) {
            return;
        }
        if (vehicle == null || !vehicle.isAlive() || Boolean.TRUE.equals(call(vehicle, "isWreck"))) {
            lost(sl, s, r, vehicle);
            return;
        }
        so.remove("Missing");
        ACTIVE.put(vehicle, s.village.id);
        if (so.getString("Phase").equals("board") && now - so.getLong("Started") > 900L && vehicle.getPassengers().isEmpty()) {
            // nobody came: put it away again
            home(sl, r, vehicle, now);
        }
    }

    private static void lost(ServerLevel sl, VillageWork.Survey s, VillageProgress.Record r, Entity vehicle) {
        String kind = r.sortie.getString("Kind");
        release(sl, r);
        r.vehicles = r.vehicles.replace(kind + ",", "");
        r.sortie = null;
        r.nextSortie = sl.getGameTime() + 2400L;
        VillageProgress.get(sl).setDirty();
        VillageProgress.announce(sl, s.village, label(kind) + "が撃破されました。村は資材を集めて作り直します", false);
    }

    private static void release(ServerLevel sl, VillageProgress.Record r) {
        for (Tag t : r.sortie.getList("Crew", 10)) {
            if (sl.getEntity(((CompoundTag)t).getUUID("Id")) instanceof Villager v) {
                VillagerLife.data(v).remove("Sortie");
            }
        }
    }

    /** Back in the motor pool: the crew gets out (on the ground at the pool), the vehicle is put away. */
    private static void home(ServerLevel sl, VillageProgress.Record r, Entity vehicle, long now) {
        BlockPos pool = BlockPos.of(r.sortie.getLong("Pool"));
        for (Entity p : List.copyOf(vehicle.getPassengers())) {
            p.stopRiding();
            if (p instanceof Villager v && v.distanceToSqr(Vec3.atCenterOf(pool)) > 9.0) {
                v.moveTo(pool.getX() + 0.5, pool.getY(), pool.getZ() + 0.5, v.getYRot(), 0.0F);
            }
        }
        release(sl, r);
        sl.sendParticles(ParticleTypes.CLOUD, vehicle.getX(), vehicle.getY() + 1.0, vehicle.getZ(), 30, 1.5, 0.8, 1.5, 0.02);
        ACTIVE.remove(vehicle);
        vehicle.discard();
        String kind = r.sortie.getString("Kind");
        r.sortie = null;
        r.nextSortie = now + 1200L;
        VillageProgress.get(sl).setDirty();
        VillageLedger.Village village = VillageLedger.get(sl).villages.get(r.id);
        if (village != null) {
            VillageProgress.announce(sl, village, label(kind) + "が帰還しました", false);
        }
    }

    // ------------------------------------------------------------------------------------- every tick
    /** Every tick for a village vehicle on a sortie (VillagerLife.tick hands non-villagers here). */
    static void tick(Entity e) {
        if (e.tickCount % 40 == 13 && !ACTIVE.containsKey(e) && e.level() instanceof ServerLevel sl && present() && ours(e)) {
            UUID owner = VillageFlights.owner(e);
            if (owner != null && !Boolean.TRUE.equals(call(e, "isWreck"))) {
                VillageProgress.Record r = VillageProgress.get(sl).villages.get(owner);
                if (r != null && r.sortie != null && e.getUUID().equals(r.sortie.getUUID("Vehicle"))) {
                    ACTIVE.put(e, owner);
                } else {
                    VillageFlights.abandon(sl, e);
                }
            }
        }
        if (ACTIVE.isEmpty()) {
            return;
        }
        UUID village = ACTIVE.get(e);
        if (village == null || !(e.level() instanceof ServerLevel sl)) {
            return;
        }
        VillageProgress.Record r = VillageProgress.get(sl).villages.get(village);
        VillageLedger.Village home = VillageLedger.get(sl).villages.get(village);
        if (r == null || home == null || r.sortie == null || !e.isAlive() || !e.getUUID().equals(r.sortie.getUUID("Vehicle"))) {
            ACTIVE.remove(e);
            return;
        }
        CompoundTag so = r.sortie;
        long now = sl.getGameTime();
        List<Villager> crew = new ArrayList<>();
        for (Tag t : so.getList("Crew", 10)) {
            if (sl.getEntity(((CompoundTag)t).getUUID("Id")) instanceof Villager v && v.isAlive()) {
                crew.add(v);
            }
        }
        for (Entity p : List.copyOf(e.getPassengers())) {
            if (p instanceof Player) {
                // a player would take the driver's seat
                p.stopRiding();
            }
        }
        boolean jet = so.getString("Kind").equals("jet");
        String phase = so.getString("Phase");
        if (phase.equals("board")) {
            // aboard from beside the hull; after a quarter of a minute anyone close enough climbs in
            boolean late = now - so.getLong("Started") > 300L;
            for (Villager v : crew) {
                if (v.getVehicle() != e && (e.getBoundingBox().inflate(2.5, 1.5, 2.5).contains(v.position()) || late && v.distanceToSqr(e) < 144.0)) {
                    v.startRiding(e, true);
                }
            }
            if (!e.getPassengers().isEmpty() && (e.getPassengers().size() >= crew.size() || now - so.getLong("Started") > 400L)) {
                so.putString("Phase", "fight");
            }
            inputs(e, false, false, false, false);
            return;
        }
        if (e.getPassengers().isEmpty()) {
            // crew gone (killed or thrown out): back to the pool by itself is not possible, put it away
            if (now - so.getLong("Started") > 100L) {
                home(sl, r, e, now);
            }
            return;
        }
        if (now % 20L == 0L) {
            LivingEntity t = threat(sl, home);
            if (t == null && so.hasUUID("Target") && sl.getEntity(so.getUUID("Target")) instanceof LivingEntity old && old.isAlive() && hostile(old)
                && old.distanceToSqr(Vec3.atCenterOf(home.center)) < 96.0 * 96.0) {
                t = old;
            }
            if (t != null) {
                so.putUUID("Target", t.getUUID());
                so.putLong("Since", now);
                so.putString("Phase", "fight");
                for (Villager v : crew) {
                    if (v.getVehicle() == e && v.getTarget() != t) {
                        v.setTarget(t);
                    }
                }
                if (jet) {
                    loiter(e, t.position(), 36.0, t.getY() + 30.0);
                }
            } else {
                so.remove("Target");
                for (Villager v : crew) {
                    v.setTarget(null);
                }
                if (now - so.getLong("Since") > 600L) {
                    so.putString("Phase", "return");
                }
                if (jet) {
                    loiter(e, Vec3.atCenterOf(home.center), 64.0, home.center.getY() + 50.0);
                }
            }
            if (now % 200L == 0L) {
                charge(e);
            }
        }
        BlockPos pool = BlockPos.of(so.getLong("Pool"));
        if (jet) {
            if (so.getString("Phase").equals("return") && now - so.getLong("Since") > 900L) {
                home(sl, r, e, now);
            }
            return;
        }
        Entity target = so.hasUUID("Target") ? sl.getEntity(so.getUUID("Target")) : null;
        boolean fighting = target != null && so.getString("Phase").equals("fight");
        Vec3 to = fighting ? target.position() : Vec3.atBottomCenterOf(pool);
        // keep the fight near the village
        Vec3 c = Vec3.atBottomCenterOf(home.center);
        if (to.subtract(c).horizontalDistance() > 72.0) {
            to = c.add(to.subtract(c).multiply(1.0, 0.0, 1.0).normalize().scale(72.0));
        }
        drive(e, to, fighting ? 18.0 : 2.5, fighting);
        if (!fighting && so.getString("Phase").equals("return")
            && (e.position().subtract(Vec3.atBottomCenterOf(pool)).horizontalDistance() < 4.0 || now - so.getLong("Since") > 2400L)) {
            home(sl, r, e, now);
        }
    }

    /**
     * The driver's hands on Superb Warfare's controls: steer toward the point (right turns the hull clockwise), throttle
     * up when roughly facing it and still far, back off when too close in a fight. If steering one way makes the heading
     * error grow, the sense is flipped (so a vehicle that steers the other way round is still driven right).
     */
    private static void drive(Entity e, Vec3 to, double hold, boolean fighting) {
        Vec3 d = to.subtract(e.position()).multiply(1.0, 0.0, 1.0);
        double dist = d.length();
        float want = (float)(Math.atan2(d.z, d.x) * 180.0 / Math.PI) - 90.0F;
        float err = wrap(want - e.getYRot());
        CompoundTag n = e.getPersistentData();
        int sign = n.getInt("OrorSteer") == 0 ? 1 : n.getInt("OrorSteer");
        if (e.tickCount % 40 == 0) {
            float before = n.getFloat("OrorSteerErr");
            if (n.getBoolean("OrorTurning") && Math.abs(err) > Math.abs(before) + 10.0F && dist > 6.0) {
                sign = -sign;
                n.putInt("OrorSteer", sign);
            }
            n.putFloat("OrorSteerErr", err);
        }
        boolean right = dist > hold && err * sign > 10.0F;
        boolean left = dist > hold && err * sign < -10.0F;
        n.putBoolean("OrorTurning", right || left);
        boolean forward = dist > hold && Math.abs(err) < 60.0F;
        boolean back = fighting && dist < 8.0;
        inputs(e, forward, back && !forward, left, right);
    }

    private static float wrap(float a) {
        a %= 360.0F;
        if (a >= 180.0F) {
            a -= 360.0F;
        }
        if (a < -180.0F) {
            a += 360.0F;
        }
        return a;
    }

    private static void inputs(Entity e, boolean forward, boolean back, boolean left, boolean right) {
        call(e, "setForwardInputDown", forward);
        call(e, "setBackInputDown", back);
        call(e, "setLeftInputDown", left);
        call(e, "setRightInputDown", right);
        call(e, "setUpInputDown", false);
        call(e, "setSprintInputDown", false);
    }

    /** VillagerLife.tick: a crew member walks to its vehicle while it boards; aboard, it does nothing else. */
    static boolean crew(Villager v, ServerLevel sl) {
        if (v.isPassenger() && v.getVehicle() != null && ACTIVE.containsKey(v.getVehicle())) {
            return true;
        }
        CompoundTag n = VillagerLife.data(v);
        if (!n.hasUUID("Sortie")) {
            return false;
        }
        VillageProgress.Record r = VillageProgress.get(sl).villages.get(n.getUUID("Sortie"));
        if (r == null || r.sortie == null || !r.sortie.getString("Phase").equals("board")
            || r.sortie.getList("Crew", 10).stream().noneMatch(t -> ((CompoundTag)t).getUUID("Id").equals(v.getUUID()))) {
            n.remove("Sortie");
            return false;
        }
        Entity vehicle = sl.getEntity(r.sortie.getUUID("Vehicle"));
        if (vehicle == null) {
            n.remove("Sortie");
            return false;
        }
        if ((v.tickCount + v.getId()) % 20 == 0) {
            VillageAI.walk(v, vehicle.blockPosition(), VillageAI.pace(v, VillageAI.FLEE), 1);
            n.putString("Task", "出撃準備");
        }
        return true;
    }

    /** True for a village vehicle on a sortie (its crew is left to the vehicle's own gunnery). */
    static boolean manned(Entity vehicle) {
        return vehicle != null && ACTIVE.containsKey(vehicle);
    }

    // ------------------------------------------------------------------------------------- reflection
    /** Call a public method by name and argument count, converting numbers to the parameter types. Null on failure. */
    private static Object call(Object o, String name, Object... args) {
        if (broken) {
            return null;
        }
        try {
            String key = o.getClass().getName() + "#" + name + "/" + args.length;
            Method m = METHODS.get(key);
            if (m == null && !METHODS.containsKey(key)) {
                for (Method c : o.getClass().getMethods()) {
                    if (c.getName().equals(name) && c.getParameterCount() == args.length) {
                        m = c;
                        break;
                    }
                }
                METHODS.put(key, m);
            }
            if (m == null) {
                return null;
            }
            Class<?>[] types = m.getParameterTypes();
            Object[] a = new Object[args.length];
            for (int i = 0; i < args.length; i++) {
                a[i] = convert(args[i], types[i]);
            }
            return m.invoke(o, a);
        } catch (ReflectiveOperationException | RuntimeException | LinkageError ex) {
            if (++failures > 40) {
                broken = true;
                System.out.println("[OROR_VILLAGE_VEHICLES] Superb Warfare vehicles disabled: " + ex);
            }
            return null;
        }
    }

    private static Object convert(Object v, Class<?> type) {
        if (v instanceof Number n) {
            if (type == float.class || type == Float.class) {
                return n.floatValue();
            } else if (type == double.class || type == Double.class) {
                return n.doubleValue();
            } else if (type == int.class || type == Integer.class) {
                return n.intValue();
            }
        }
        return v;
    }
}
