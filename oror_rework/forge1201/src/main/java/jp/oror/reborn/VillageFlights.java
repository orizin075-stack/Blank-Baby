package jp.oror.reborn;

import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.WeakHashMap;
import java.util.function.Predicate;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.ItemTags;
import net.minecraft.world.Container;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.levelgen.Heightmap.Types;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.fml.ModList;

/**
 * Airships and aeroplanes between villages (v0.17.15), with Immersive Aircraft's own aircraft.
 * - A 町 builds an airship (飛行船) from its chests: iron, copper (or more iron), wool, string, logs, cobblestone and
 *   redstone, about what Immersive Aircraft's recipes take; a 城下町 adds a biplane (飛行機).
 * - About once a day it loads its surplus (what the chests hold beyond a stack of a kind) and flies it to another village:
 *   the aircraft is set down on the village airfield, its crew walks over and boards, it climbs out and heads off. Out of
 *   the players' sight the journey goes on as saved data (the ground under it would not be loaded); the goods reach the
 *   other village's chests, and the crew comes back with emeralds and that village's wares, lands on the airfield,
 *   unloads and puts the aircraft away.
 * - The village's villagers fly it: Immersive Aircraft lets only players start an engine or steer, so the flight is
 *   moved here, every tick after the aircraft's own physics, with its engine running on a little coal. Players are not
 *   let aboard a trade flight (a player would take the controls).
 */
public final class VillageFlights {
    private static final Map<Entity, UUID> FLYING = new WeakHashMap<>();
    private static Method engine;
    private static boolean broken;

    private VillageFlights() {
    }

    static boolean present() {
        return !broken && ModList.get().isLoaded("immersive_aircraft");
    }

    private static EntityType<?> type(String id) {
        ResourceLocation rl = new ResourceLocation("immersive_aircraft", id);
        return BuiltInRegistries.ENTITY_TYPE.containsKey(rl) ? (EntityType<?>)BuiltInRegistries.ENTITY_TYPE.get(rl) : null;
    }

    private static String label(String type) {
        return type.equals("biplane") ? "飛行機" : "飛行船";
    }

    // ------------------------------------------------------------------------------------- the review (every 30 s)
    static void review(ServerLevel sl, VillageWork.Survey s, VillageProgress.Record r) {
        if (!present() || r.stage < 2) {
            return;
        }
        long now = sl.getGameTime();
        if (r.flight != null) {
            advance(sl, s, r, now);
            return;
        }
        if (!r.aircraftType.contains("airship")) {
            if (build(sl, s, r, "airship")) {
                VillageProgress.announce(sl, s.village, "村の資材で飛行船を建造しました", false);
            }
            return;
        }
        if (r.stage >= 3 && !r.aircraftType.contains("biplane") && build(sl, s, r, "biplane")) {
            VillageProgress.announce(sl, s.village, "村の資材で飛行機を建造しました", false);
            return;
        }
        if (sl.isDay() && now >= r.nextFlight) {
            plan(sl, s, r, now);
        }
    }

    /** Build an aircraft from the chests (once): about the iron, copper, wool, string, logs and stone its recipe takes. */
    private static boolean build(ServerLevel sl, VillageWork.Survey s, VillageProgress.Record r, String kind) {
        if (type(kind) == null) {
            return false;
        }
        boolean plane = kind.equals("biplane");
        int iron = plane ? 18 : 10;
        int copper = Math.min(7, s.stock("copper_ingot"));
        int needIron = iron + (7 - copper);
        int wool = plane ? 0 : 4;
        int string = plane ? 0 : 6;
        int logs = plane ? 12 : 6;
        if (s.stock("iron_ingot") < needIron || s.count(VillageWork.is("wool")) < wool || s.stock("string") < string
            || s.count(VillageWork.is("logs")) < logs || s.stock("cobblestone") < 16 || s.stock("redstone") < 2) {
            return false;
        }
        VillageExpeditions.take(sl, s, "iron_ingot", needIron);
        VillageExpeditions.take(sl, s, "copper_ingot", copper);
        VillageExpeditions.take(sl, s, VillageWork.is("wool"), wool);
        VillageExpeditions.take(sl, s, "string", string);
        VillageExpeditions.take(sl, s, VillageWork.is("logs"), logs);
        VillageExpeditions.take(sl, s, "cobblestone", 16);
        VillageExpeditions.take(sl, s, "redstone", 2);
        r.aircraftType = r.aircraftType + kind + ",";
        VillageProgress.get(sl).setDirty();
        return true;
    }

    private static void plan(ServerLevel sl, VillageWork.Survey s, VillageProgress.Record r, long now) {
        r.nextFlight = now + 6000L;
        // one of the three nearest (v0.17.17: of however many there are - skipping up to two of one or two found none)
        List<VillageLedger.Village> near = VillageLedger.get(sl).villages.values().stream()
            .filter(o -> !o.id.equals(s.village.id) && o.center.distSqr(s.village.center) > 96.0 * 96.0 && o.center.distSqr(s.village.center) < 5000.0 * 5000.0)
            .sorted(Comparator.comparingDouble(o -> o.center.distSqr(s.village.center)))
            .limit(3L)
            .toList();
        VillageLedger.Village dest = near.isEmpty() ? null : near.get(sl.random.nextInt(near.size()));
        if (dest == null) {
            return;
        }
        String kind = r.aircraftType.contains("biplane") && r.flights % 2 == 1 ? "biplane" : "airship";
        EntityType<?> type = type(kind);
        BlockPos field = airfield(sl, s, r);
        if (type == null || field == null) {
            return;
        }
        List<ItemStack> cargo = cargo(sl, s, kind.equals("biplane") ? 3 : 8);
        if (cargo.isEmpty()) {
            return;
        }
        int seats = kind.equals("biplane") ? 1 : 2;
        List<Villager> crew = sl.getEntitiesOfClass(Villager.class, new AABB(s.village.center).inflate(48.0, 16.0, 48.0),
                v -> v.isAlive() && !v.isBaby() && !v.isSleeping() && !VillagerIndustry.miner(v) && !VillagerLife.data(v).contains("Trip")
                    && !VillagerLife.data(v).hasUUID("Flight") && !v.getPersistentData().getBoolean("OrorWanderer") && VillageLedger.of(v) == s.village)
            .stream()
            .sorted(Comparator.comparingDouble(v -> v.distanceToSqr(Vec3.atCenterOf(field))))
            .limit(seats)
            .toList();
        if (crew.size() < seats) {
            VillageProgress.get(sl).deliver(r, cargo, sl.registryAccess());
            return;
        }
        Entity craft = type.create(sl);
        if (craft == null) {
            VillageProgress.get(sl).deliver(r, cargo, sl.registryAccess());
            return;
        }
        Vec3 dir = Vec3.atCenterOf(dest.center).subtract(Vec3.atCenterOf(s.village.center)).multiply(1.0, 0.0, 1.0).normalize();
        craft.moveTo(field.getX() + 0.5, field.getY(), field.getZ() + 0.5, yaw(dir), 0.0F);
        if (!sl.noCollision(craft, craft.getBoundingBox()) || !sl.addFreshEntity(craft)) {
            VillageProgress.get(sl).deliver(r, cargo, sl.registryAccess());
            return;
        }
        mark(craft, s.village.id);
        fuel(craft, kind);
        CompoundTag f = new CompoundTag();
        f.putString("Type", kind);
        f.putUUID("Craft", craft.getUUID());
        f.putString("Phase", "board");
        f.putLong("Until", now + 900L);
        f.putUUID("Dest", dest.id);
        f.putDouble("DirX", dir.x);
        f.putDouble("DirZ", dir.z);
        ListTag goods = new ListTag();
        for (ItemStack st : cargo) {
            goods.add(st.save(sl.registryAccess()));
        }
        f.put("Cargo", goods);
        ListTag ids = new ListTag();
        for (Villager v : crew) {
            ids.add(VillageProgress.uuid(v.getUUID()));
            VillagerLife.data(v).putUUID("Flight", s.village.id);
            VillagerLife.data(v).putString("Task", label(kind) + "に搭乗");
        }
        f.put("Crew", ids);
        r.flight = f;
        FLYING.put(craft, s.village.id);
        VillageProgress.get(sl).setDirty();
        VillageProgress.announce(sl, s.village, label(kind) + "が「" + VillageProgress.get(sl).of(dest).name() + "」への交易飛行の準備をしています", false);
    }

    /** The village airfield: a level open patch near the centre, chosen once. */
    private static BlockPos airfield(ServerLevel sl, VillageWork.Survey s, VillageProgress.Record r) {
        if (r.airfield != null && sl.hasChunkAt(r.airfield) && clear(sl, r.airfield)) {
            return r.airfield;
        }
        BlockPos c = s.village.center;
        for (int i = 0; i < 16; i++) {
            double a = sl.random.nextDouble() * Math.PI * 2.0;
            double d = 10.0 + sl.random.nextDouble() * 12.0;
            BlockPos p = VillageExpeditions.top(sl, c.offset((int)Math.round(Math.cos(a) * d), 0, (int)Math.round(Math.sin(a) * d)));
            if (p != null && Math.abs(p.getY() - c.getY()) <= 4 && clear(sl, p)) {
                r.airfield = p;
                VillageProgress.get(sl).setDirty();
                return p;
            }
        }
        return null;
    }

    /** Five by five of open air, five high, over solid ground within a block of level. */
    static boolean clear(ServerLevel sl, BlockPos p) {
        for (int x = -2; x <= 2; x++) {
            for (int z = -2; z <= 2; z++) {
                int top = sl.getHeight(Types.MOTION_BLOCKING_NO_LEAVES, p.getX() + x, p.getZ() + z);
                if (Math.abs(top - p.getY()) > 1 || !sl.getFluidState(new BlockPos(p.getX() + x, top - 1, p.getZ() + z)).isEmpty()) {
                    return false;
                }
                for (int y = 0; y < 5; y++) {
                    if (!sl.getBlockState(p.offset(x, y, z)).canBeReplaced()) {
                        return false;
                    }
                }
            }
        }
        return true;
    }

    /** What the village can spare: of each kind beyond a stack, up to so many stacks (not gear, not expedition goods). */
    private static List<ItemStack> cargo(ServerLevel sl, VillageWork.Survey s, int stacks) {
        List<ItemStack> out = new ArrayList<>();
        for (Map.Entry<Item, Integer> e : new ArrayList<>(s.stock.entrySet())) {
            if (out.size() >= stacks) {
                break;
            }
            ItemStack one = e.getKey().getDefaultInstance();
            if (e.getValue() <= 64 || one.getMaxStackSize() < 16 || one.isDamageableItem() || keep(one)) {
                continue;
            }
            int n = Math.min(e.getValue() - 64, one.getMaxStackSize());
            int got = VillageExpeditions.take(sl, s, x -> x.is(e.getKey()), n);
            if (got > 0) {
                out.add(one.copyWithCount(got));
            }
        }
        return out;
    }

    /** What a village keeps for itself whatever the amount. */
    private static boolean keep(ItemStack st) {
        String id = BuiltInRegistries.ITEM.getKey(st.getItem()).getPath();
        return st.is(Items.EMERALD) || id.contains("obsidian") || id.contains("ender") || id.contains("blaze") || id.contains("netherite")
            || id.equals("ancient_debris") || id.equals("gunpowder") || id.equals("diamond") || id.equals("iron_ingot") || id.equals("redstone");
    }

    // ------------------------------------------------------------------------------------- under way
    private static void advance(ServerLevel sl, VillageWork.Survey s, VillageProgress.Record r, long now) {
        CompoundTag f = r.flight;
        String phase = f.getString("Phase");
        Entity craft = f.hasUUID("Craft") ? sl.getEntity(f.getUUID("Craft")) : null;
        if (craft != null) {
            FLYING.put(craft, s.village.id);
            f.remove("Missing");
        } else if ((phase.equals("board") || phase.equals("climb") || phase.equals("landing")) && !gone(f)) {
            return;
        }
        switch (phase) {
            case "board" -> {
                if (craft == null || !craft.isAlive()) {
                    cancel(sl, s, r, null);
                    return;
                }
                long aboard = craft.getPassengers().stream().filter(p -> p instanceof Villager).count();
                if (aboard >= f.getList("Crew", 10).size()) {
                    f.putString("Phase", "climb");
                    f.putLong("Until", now + 1200L);
                    VillageProgress.announce(sl, s.village, label(f.getString("Type")) + "が「" + VillageProgress.get(sl).of(VillageLedger.get(sl).villages.get(f.getUUID("Dest"))).name()
                        + "」へ飛び立ちました（積荷：" + VillageExpeditions.summary(goods(sl, f.getList("Cargo", 10))) + "）", false);
                } else if (now >= f.getLong("Until")) {
                    cancel(sl, s, r, craft);
                }
            }
            case "climb" -> {
                if (craft == null || !craft.isAlive()) {
                    // shot down or lost before it was out of sight: the cargo comes back to the chests
                    cancel(sl, s, r, null);
                } else if (now >= f.getLong("Until") + 200L) {
                    // v0.17.17: out past the distance where entities still tick, the craft never put itself away
                    stow(sl, craft, r);
                }
            }
            case "away" -> {
                if (now >= f.getLong("Back")) {
                    arrive(sl, s, r);
                }
            }
            case "landing" -> {
                if (craft == null || !craft.isAlive()) {
                    land(sl, r, null);
                }
            }
            default -> {
                // parked: put away after a while
                if (now >= f.getLong("Until")) {
                    if (craft != null) {
                        sl.sendParticles(ParticleTypes.CLOUD, craft.getX(), craft.getY() + 1.0, craft.getZ(), 20, 1.0, 0.6, 1.0, 0.02);
                        craft.ejectPassengers();
                        craft.discard();
                    }
                    r.flight = null;
                    r.flights++;
                    r.nextFlight = now + 24000L;
                    VillageProgress.get(sl).setDirty();
                }
            }
        }
    }

    private static List<ItemStack> goods(ServerLevel sl, ListTag list) {
        List<ItemStack> out = new ArrayList<>();
        for (Tag t : list) {
            ItemStack st = ItemStack.parseOptional(sl.registryAccess(), (CompoundTag)t);
            if (!st.isEmpty()) {
                out.add(st);
            }
        }
        return out;
    }

    private static void cancel(ServerLevel sl, VillageWork.Survey s, VillageProgress.Record r, Entity craft) {
        if (craft != null) {
            craft.ejectPassengers();
            craft.discard();
        }
        VillageProgress.get(sl).deliver(r, goods(sl, r.flight.getList("Cargo", 10)), sl.registryAccess());
        for (Tag t : r.flight.getList("Crew", 10)) {
            if (sl.getEntity(((CompoundTag)t).getUUID("Id")) instanceof Villager v) {
                VillagerLife.data(v).remove("Flight");
            }
        }
        r.flight = null;
        r.nextFlight = sl.getGameTime() + 12000L;
        VillageProgress.get(sl).setDirty();
    }

    /** Every tick for an aircraft on a village flight (VillagerLife.tick hands non-villagers here). */
    static void tick(Entity e) {
        if (e.tickCount % 40 == 7 && !FLYING.containsKey(e) && e.level() instanceof ServerLevel sl && present()
            && BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).getNamespace().equals("immersive_aircraft")) {
            UUID owner = owner(e);
            if (owner != null) {
                VillageProgress.Record r = VillageProgress.get(sl).villages.get(owner);
                if (r != null && r.flight != null && r.flight.hasUUID("Craft") && r.flight.getUUID("Craft").equals(e.getUUID())) {
                    FLYING.put(e, owner);
                } else {
                    abandon(sl, e);
                }
            }
        }
        if (FLYING.isEmpty()) {
            return;
        }
        UUID village = FLYING.get(e);
        if (village == null || !(e.level() instanceof ServerLevel sl)) {
            return;
        }
        VillageProgress.Record r = VillageProgress.get(sl).villages.get(village);
        if (r == null || r.flight == null || !e.isAlive() || !r.flight.hasUUID("Craft") || !r.flight.getUUID("Craft").equals(e.getUUID())) {
            FLYING.remove(e);
            return;
        }
        for (Entity p : List.copyOf(e.getPassengers())) {
            if (p instanceof Player) {
                // a player would take the controls
                p.stopRiding();
            }
        }
        String phase = r.flight.getString("Phase");
        if (!phase.equals("climb") && !phase.equals("landing")) {
            e.setNoGravity(false);
            return;
        }
        String kind = r.flight.getString("Type");
        fuel(e, kind);
        engine(e, 1.0F);
        e.setNoGravity(true);
        BlockPos field = r.airfield != null ? r.airfield : e.blockPosition();
        Vec3 pos = e.position();
        Vec3 dir = new Vec3(r.flight.getDouble("DirX"), 0.0, r.flight.getDouble("DirZ"));
        double ground = sl.getHeight(Types.MOTION_BLOCKING, (int)Math.floor(pos.x), (int)Math.floor(pos.z));
        if (phase.equals("climb")) {
            double cruise = Math.max(field.getY() + 32.0, ground + 12.0);
            double speed = Math.min(0.7, 0.15 + Math.max(0.0, pos.y - field.getY()) * 0.03);
            move(e, new Vec3(dir.x * speed, pos.y < cruise ? 0.22 : 0.0, dir.z * speed));
            double out = Math.sqrt(Math.pow(pos.x - field.getX(), 2.0) + Math.pow(pos.z - field.getZ(), 2.0));
            if (out > 160.0 || out > 48.0 && sl.getNearestPlayer(e, 128.0) == null || sl.getGameTime() >= r.flight.getLong("Until")) {
                stow(sl, e, r);
            }
        } else {
            Vec3 to = new Vec3(field.getX() + 0.5, field.getY(), field.getZ() + 0.5);
            Vec3 flat = to.subtract(pos).multiply(1.0, 0.0, 1.0);
            double dist = flat.length();
            double want = Math.max(field.getY() + Math.min(30.0, dist * 0.35), dist > 3.0 ? ground + 4.0 : field.getY());
            double speed = Math.min(0.6, Math.max(0.08, dist * 0.05));
            Vec3 h = dist > 1.0E-3 ? flat.scale(Math.min(speed, dist) / dist) : Vec3.ZERO;
            move(e, new Vec3(h.x, Math.max(-0.3, Math.min(0.25, want - pos.y)), h.z));
            if (dist < 1.0 && pos.y - field.getY() < 0.6) {
                land(sl, r, e);
            }
        }
    }

    private static float yaw(Vec3 dir) {
        return (float)(Math.atan2(dir.z, dir.x) * 180.0 / Math.PI) - 90.0F;
    }

    private static void move(Entity e, Vec3 vel) {
        e.setDeltaMovement(vel);
        e.setPos(e.getX() + vel.x, e.getY() + vel.y, e.getZ() + vel.z);
        if (vel.x * vel.x + vel.z * vel.z > 1.0E-4) {
            e.setYRot(yaw(vel));
        }
        e.setXRot(0.0F);
    }

    /** A little coal in the boiler, so the engine (and the propellers) can run. */
    private static void fuel(Entity craft, String kind) {
        if (craft instanceof Container c) {
            int boiler = kind.equals("biplane") ? 7 : 6;
            if (boiler < c.getContainerSize() && c.getItem(boiler).isEmpty()) {
                c.setItem(boiler, new ItemStack(Items.COAL, 4));
            }
        }
    }

    private static void engine(Entity craft, float target) {
        if (broken) {
            return;
        }
        try {
            if (engine == null) {
                engine = craft.getClass().getMethod("setEngineTarget", float.class);
            }
            if (engine.getDeclaringClass().isInstance(craft)) {
                engine.invoke(craft, target);
            }
        } catch (ReflectiveOperationException | LinkageError | RuntimeException ex) {
            broken = true;
            System.out.println("[OROR_VILLAGE_FLIGHTS] engine control disabled: " + ex);
        }
    }

    /** Out of sight: the aircraft and its crew go on as saved data; the goods are delivered, the payment computed. */
    private static void stow(ServerLevel sl, Entity craft, VillageProgress.Record r) {
        CompoundTag f = r.flight;
        ListTag saved = new ListTag();
        for (Entity p : List.copyOf(craft.getPassengers())) {
            if (p instanceof Villager v) {
                v.stopRiding();
                VillagerLife.data(v).remove("Flight");
                CompoundTag t = new CompoundTag();
                v.saveWithoutId(t);
                saved.add(t);
                v.discard();
            }
        }
        f.put("CrewSaved", saved);
        FLYING.remove(craft);
        craft.ejectPassengers();
        craft.discard();
        VillageProgress db = VillageProgress.get(sl);
        VillageLedger.Village dest = VillageLedger.get(sl).villages.get(f.getUUID("Dest"));
        List<ItemStack> cargo = goods(sl, f.getList("Cargo", 10));
        int value = 0;
        for (ItemStack st : cargo) {
            value += worth(st);
        }
        List<ItemStack> pay = new ArrayList<>();
        int emeralds = Math.max(1, value);
        while (emeralds > 0) {
            int part = Math.min(64, emeralds);
            pay.add(new ItemStack(Items.EMERALD, part));
            emeralds -= part;
        }
        int theirs = dest == null ? 0 : db.of(dest).stage;
        pay.addAll(wares(sl, theirs));
        if (dest != null) {
            db.deliver(db.of(dest), cargo, sl.registryAccess());
        }
        ListTag p = new ListTag();
        for (ItemStack st : pay) {
            p.add(st.save(sl.registryAccess()));
        }
        f.put("Pay", p);
        double dist = dest == null ? 500.0 : Math.sqrt(dest.center.distSqr(BlockPos.containing(craft.position())));
        f.putString("Phase", "away");
        f.putLong("Back", sl.getGameTime() + (long)(dist / 1.5) * 2L + 2400L);
        db.setDirty();
    }

    /** What a load fetches in emeralds: about one a stack of common things, more for metal and gems. */
    private static int worth(ItemStack st) {
        String id = BuiltInRegistries.ITEM.getKey(st.getItem()).getPath();
        double each = id.endsWith("_ingot") ? 0.25 : (id.contains("diamond") ? 2.0 : (st.has(net.minecraft.core.component.DataComponents.FOOD) ? 0.08 : 0.0625));
        return (int)Math.ceil(st.getCount() * each);
    }

    /** What the other village sends back besides emeralds: its own wares, finer as it grows. */
    private static List<ItemStack> wares(ServerLevel sl, int stage) {
        List<ItemStack> out = new ArrayList<>();
        String[] common = {"bread", "iron_ingot", "coal", "white_wool", "string", "copper_ingot", "redstone", "paper"};
        String[] fine = {"gold_ingot", "ender_pearl", "blaze_rod", "gunpowder", "diamond", "obsidian"};
        for (int i = 0; i < 2; i++) {
            out.add(stack(common[sl.random.nextInt(common.length)], 4 + sl.random.nextInt(9)));
        }
        if (stage >= 3) {
            out.add(stack(fine[sl.random.nextInt(fine.length)], 1 + sl.random.nextInt(4)));
        }
        return out;
    }

    private static ItemStack stack(String id, int n) {
        return ((Item)BuiltInRegistries.ITEM.get(ResourceLocation.withDefaultNamespace(id))).getDefaultInstance().copyWithCount(n);
    }

    /** Coming home: the aircraft appears out on its line at cruising height with its crew aboard and comes in to land. */
    private static void arrive(ServerLevel sl, VillageWork.Survey s, VillageProgress.Record r) {
        CompoundTag f = r.flight;
        String kind = f.getString("Type");
        EntityType<?> type = type(kind);
        BlockPos field = airfield(sl, s, r);
        Entity craft = type == null || field == null ? null : type.create(sl);
        Vec3 dir = new Vec3(f.getDouble("DirX"), 0.0, f.getDouble("DirZ"));
        if (craft != null) {
            Vec3 from = Vec3.atCenterOf(field).add(dir.scale(64.0));
            double y = Math.max(field.getY() + 30.0, sl.getHeight(Types.MOTION_BLOCKING, (int)from.x, (int)from.z) + 10.0);
            craft.moveTo(from.x, y, from.z, yaw(dir.scale(-1.0)), 0.0F);
            if (!sl.addFreshEntity(craft)) {
                craft = null;
            } else {
                mark(craft, s.village.id);
            }
        }
        List<Villager> crew = new ArrayList<>();
        for (Tag t : f.getList("CrewSaved", 10)) {
            Villager v = (Villager)EntityType.VILLAGER.create(sl);
            if (v == null) {
                continue;
            }
            v.load((CompoundTag)t);
            BlockPos at = craft != null ? craft.blockPosition() : (field != null ? field : s.village.center);
            v.moveTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5, 0.0F, 0.0F);
            if (sl.addFreshEntity(v)) {
                crew.add(v);
                if (craft != null) {
                    v.startRiding(craft, true);
                }
            }
        }
        if (craft == null) {
            f.putString("Phase", "landing");
            land(sl, r, null);
            return;
        }
        fuel(craft, kind);
        f.putUUID("Craft", craft.getUUID());
        f.putString("Phase", "landing");
        FLYING.put(craft, s.village.id);
        VillageProgress.get(sl).setDirty();
    }

    /** Down on the airfield: the crew gets out and the payment goes to the chests. */
    private static void land(ServerLevel sl, VillageProgress.Record r, Entity craft) {
        CompoundTag f = r.flight;
        if (craft != null) {
            engine(craft, 0.0F);
            craft.setNoGravity(false);
            craft.setDeltaMovement(Vec3.ZERO);
            craft.ejectPassengers();
        }
        List<ItemStack> pay = goods(sl, f.getList("Pay", 10));
        VillageProgress db = VillageProgress.get(sl);
        db.deliver(r, pay, sl.registryAccess());
        f.putString("Phase", "parked");
        f.putLong("Until", sl.getGameTime() + 1200L);
        f.remove("CrewSaved");
        f.remove("Pay");
        db.setDirty();
        VillageLedger.Village home = VillageLedger.get(sl).villages.get(r.id);
        VillageLedger.Village dest = VillageLedger.get(sl).villages.get(f.getUUID("Dest"));
        if (home != null) {
            VillageProgress.announce(sl, home, label(f.getString("Type")) + "が" + (dest != null ? "「" + db.of(dest).name() + "」" : "") + "との交易から戻りました　受け取り："
                + VillageExpeditions.summary(pay), false);
        }
    }

    /** VillagerLife.tick: a crew member walks to the aircraft and boards it; riding, it does nothing else. */
    static boolean crew(Villager v, ServerLevel sl) {
        CompoundTag n = VillagerLife.data(v);
        if (!n.hasUUID("Flight")) {
            return v.isPassenger() && v.getVehicle() != null && FLYING.containsKey(v.getVehicle());
        }
        VillageProgress.Record r = VillageProgress.get(sl).villages.get(n.getUUID("Flight"));
        if (r == null || r.flight == null || !r.flight.getString("Phase").equals("board")) {
            n.remove("Flight");
            return v.isPassenger();
        }
        Entity craft = sl.getEntity(r.flight.getUUID("Craft"));
        if (craft == null) {
            n.remove("Flight");
            return false;
        }
        if (v.getVehicle() == craft) {
            return true;
        }
        if (craft.getBoundingBox().inflate(2.0, 1.5, 2.0).contains(v.position())) {
            v.startRiding(craft, true);
        } else if ((v.tickCount + v.getId()) % 20 == 0) {
            VillageAI.walk(v, craft.blockPosition(), VillageAI.pace(v, VillageAI.WORK), 1);
        }
        return true;
    }

    // ------------------------------------------------------------------------------------- crafts the world kept
    /** A village aircraft or vehicle carries its village's id, so one found again without its trip can be put away. */
    static void mark(Entity craft, UUID village) {
        craft.getPersistentData().putUUID("OrorVillageCraft", village);
    }

    static UUID owner(Entity craft) {
        CompoundTag n = craft.getPersistentData();
        return n.hasUUID("OrorVillageCraft") ? n.getUUID("OrorVillageCraft") : null;
    }

    /**
     * A village craft that no trip owns any more (the world was closed mid-flight and the trip gave up on it, say): its
     * crew is set down on the ground and it is put away, so no village aircraft or tank is left lying about for the taking.
     */
    static void abandon(ServerLevel sl, Entity craft) {
        for (Entity p : List.copyOf(craft.getPassengers())) {
            p.stopRiding();
            if (p instanceof Villager v) {
                VillagerLife.data(v).remove("Flight");
                VillagerLife.data(v).remove("Sortie");
                BlockPos g = VillageExpeditions.top(sl, v.blockPosition());
                if (g != null) {
                    v.moveTo(g.getX() + 0.5, g.getY(), g.getZ() + 0.5, v.getYRot(), 0.0F);
                }
            }
        }
        sl.sendParticles(ParticleTypes.CLOUD, craft.getX(), craft.getY() + 1.0, craft.getZ(), 20, 1.0, 0.6, 1.0, 0.02);
        craft.discard();
    }

    /** A craft not found may just not be loaded yet (the world has just been opened): it is lost after three reviews (90 s). */
    static boolean gone(CompoundTag trip) {
        int n = trip.getInt("Missing") + 1;
        trip.putInt("Missing", n);
        return n >= 3;
    }
}
