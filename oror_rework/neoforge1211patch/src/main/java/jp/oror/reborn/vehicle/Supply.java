package jp.oror.reborn.vehicle;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.Nameable;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.energy.IEnergyStorage;

/**
 * The kingdom's logistics for its machines and its guards' electric guns. Nothing is conjured any more (every vehicle
 * used to be topped up to a full battery and a fresh load of shells every minute, wherever it was):
 * <ul>
 * <li>Power: Superb Warfare's charging stations at the posts (hangar bays, helipads, runway stands, the close-in guns'
 * batteries) burn the coal blocks a hopper feeds them from the coal chest on top and charge every vehicle within eight
 * blocks; a guard's taser is recharged from a station's store when he stands by one.</li>
 * <li>Ammunition: each post has its depot (a chest named 王国軍の弾薬庫); the crew of a vehicle standing at its post load
 * from it what the vehicle's own weapons fire (as its Superb Warfare definition names them), up to its load.</li>
 * <li>A vehicle leaves its post charged and loaded; with its battery under a third or its magazines nearly empty it
 * breaks off, goes back to its post (an aircraft lands and is towed to its stand) and waits there until charged and
 * loaded again, or until five minutes have shown that its post has nothing more to give.</li>
 * </ul>
 */
public final class Supply {
    private Supply() {
    }

    public static final String DEPOT = "王国軍の弾薬庫";
    private static final String[][] TANK = {{"large_shell_he", "32"}, {"large_shell_gs", "16"}, {"rifle_ammo", "64"}, {"heavy_ammo", "64"}};
    private static final String[][] IFV = {{"small_shell_he", "64"}, {"small_shell_gs", "64"}, {"medium_anti_ground_missile", "4"}, {"rifle_ammo", "64"}};
    private static final String[][] GUN = {{"large_shell_he", "32"}, {"large_shell_cm", "8"}};
    private static final String[][] CIWS = {{"small_shell_ap", "64"}, {"small_shell_ap", "64"}};
    private static final String[][] A10 = {{"small_shell_ap", "64"}, {"small_shell_ap", "64"}, {"small_rocket", "16"}, {"large_anti_ground_missile", "2"},
        {"large_anti_ground_missile", "2"}, {"medium_aerial_bomb", "2"}};
    private static final String[][] SCOUT = {{"small_shell_he", "64"}, {"small_shell_he", "64"}, {"small_rocket", "16"}};
    private static final String[][] GUNSHIP = {{"small_shell_he", "64"}, {"small_rocket", "16"}, {"large_anti_ground_missile", "2"}, {"medium_anti_ground_missile", "4"}};
    /** What each kind carries: its own weapons' ammunition (Superb Warfare 0.8.9.2's vehicle definitions). */
    static final Map<String, String[][]> LOAD = Map.ofEntries(
        Map.entry("m_1a_2", TANK), Map.entry("t_90a", TANK), Map.entry("ztz_99a", TANK),
        Map.entry("bmp_2", IFV), Map.entry("bradley", IFV),
        Map.entry("mk_42", GUN), Map.entry("mle_1934", GUN), Map.entry("bl_132", GUN), Map.entry("hpj_11", CIWS),
        Map.entry("a_10a", A10), Map.entry("ah_6", SCOUT), Map.entry("mi_28", GUNSHIP));
    private static final String[][] GROUND = {{"large_shell_he", "16"}, {"small_shell_he", "64"}, {"rifle_ammo", "64"}, {"heavy_ammo", "64"}};
    private static final String[][] AIR = {{"small_shell_ap", "64"}, {"small_shell_he", "64"}, {"small_rocket", "16"}, {"large_anti_ground_missile", "2"}};

    static String kind(Entity v) {
        return BuiltInRegistries.ENTITY_TYPE.getKey(v.getType()).getPath();
    }

    static String[][] load(Entity v) {
        String[][] l = LOAD.get(kind(v));
        if (l != null) {
            return l;
        }
        String engine = Sbw.engine(v);
        return engine.equals("AIRCRAFT") || engine.equals("HELICOPTER") ? AIR : GROUND;
    }

    private static Item item(String path) {
        ResourceLocation id = Sbw.id(path);
        return BuiltInRegistries.ITEM.containsKey(id) ? BuiltInRegistries.ITEM.get(id) : null;
    }

    private static Container hold(Entity v) {
        return v instanceof Container c && c.getContainerSize() > 0 ? c : null;
    }

    /** A new vehicle from the kingdom's works: charged, and loaded with what its weapons fire. */
    public static void stock(Entity v) {
        Sbw.charge(v);
        Container c = hold(v);
        if (c == null) {
            return;
        }
        int slot = 0;
        for (String[] l : load(v)) {
            Item item = item(l[0]);
            if (item != null && slot < c.getContainerSize()) {
                c.setItem(slot++, new ItemStack(item, Math.min(item.getDefaultMaxStackSize(), Integer.parseInt(l[1]))));
            }
        }
    }

    /** How many rounds of its own ammunition the vehicle has aboard, and how many a full load is (bounded by its hold). */
    static int[] rounds(Entity v) {
        Container c = hold(v);
        if (c == null) {
            return new int[]{0, 0};
        }
        int have = 0, full = 0, slots = 0;
        List<Item> kinds = new ArrayList<>();
        for (String[] l : load(v)) {
            Item item = item(l[0]);
            if (item == null || slots >= c.getContainerSize()) {
                continue;
            }
            slots++;
            full += Math.min(item.getDefaultMaxStackSize(), Integer.parseInt(l[1]));
            if (!kinds.contains(item)) {
                kinds.add(item);
            }
        }
        for (int i = 0; i < c.getContainerSize(); i++) {
            ItemStack s = c.getItem(i);
            if (!s.isEmpty() && kinds.contains(s.getItem())) {
                have += s.getCount();
            }
        }
        return new int[]{have, full};
    }

    /** The battery's charge, 0 to 1 (1 for a machine without one). */
    static double charge(Entity v) {
        Object e = Sbw.call(v, "getEnergy"), m = Sbw.call(v, "getMaxEnergy");
        return e instanceof Number en && m instanceof Number max && max.intValue() > 0 ? en.doubleValue() / max.doubleValue() : 1.0;
    }

    static boolean low(Entity v) {
        int[] r = rounds(v);
        return charge(v) < 0.33 || r[1] > 0 && r[0] < Math.max(1, r[1] / 10);
    }

    static boolean full(Entity v) {
        int[] r = rounds(v);
        return charge(v) >= 0.95 && (r[1] == 0 || r[0] >= r[1] * 4 / 5);
    }

    /** The block entities of the given kind within reach of a point (a box: reach across, four up and down). */
    static List<BlockEntity> near(ServerLevel level, Vec3 at, double reach, java.util.function.Predicate<BlockEntity> what) {
        List<BlockEntity> out = new ArrayList<>();
        int x0 = (int) Math.floor(at.x - reach) >> 4, x1 = (int) Math.floor(at.x + reach) >> 4;
        int z0 = (int) Math.floor(at.z - reach) >> 4, z1 = (int) Math.floor(at.z + reach) >> 4;
        for (int cx = x0; cx <= x1; cx++) {
            for (int cz = z0; cz <= z1; cz++) {
                LevelChunk chunk = level.getChunkSource().getChunkNow(cx, cz);
                if (chunk == null) {
                    continue;
                }
                for (BlockEntity be : chunk.getBlockEntities().values()) {
                    BlockPos p = be.getBlockPos();
                    if (Math.abs(p.getX() + 0.5 - at.x) <= reach && Math.abs(p.getZ() + 0.5 - at.z) <= reach && Math.abs(p.getY() - at.y) <= 5
                        && what.test(be)) {
                        out.add(be);
                    }
                }
            }
        }
        return out;
    }

    static boolean depot(BlockEntity be) {
        return be instanceof Container && be instanceof Nameable n && n.hasCustomName() && n.getCustomName().getString().contains("弾薬庫");
    }

    static boolean station(BlockEntity be) {
        return "superbwarfare".equals(BuiltInRegistries.BLOCK_ENTITY_TYPE.getKey(be.getType()).getNamespace())
            && BuiltInRegistries.BLOCK_ENTITY_TYPE.getKey(be.getType()).getPath().contains("charging_station");
    }

    /**
     * The crew load the vehicle from the depots beside it: of each line of its load, what is missing (in the hold's free
     * room or on a part-used stack of the same shells). Returns the rounds moved.
     */
    static int reload(ServerLevel level, Entity v) {
        Container hold = hold(v);
        if (hold == null) {
            return 0;
        }
        List<BlockEntity> depots = near(level, v.position(), 10, Supply::depot);
        if (depots.isEmpty()) {
            return 0;
        }
        int moved = 0;
        java.util.Map<Item, Integer> want = new java.util.LinkedHashMap<>();
        int slots = 0;
        for (String[] l : load(v)) {
            Item item = item(l[0]);
            if (item != null && slots++ < hold.getContainerSize()) {
                want.merge(item, Math.min(item.getDefaultMaxStackSize(), Integer.parseInt(l[1])), Integer::sum);
            }
        }
        for (Map.Entry<Item, Integer> w : want.entrySet()) {
            Item item = w.getKey();
            int have = 0;
            for (int i = 0; i < hold.getContainerSize(); i++) {
                if (hold.getItem(i).is(item)) {
                    have += hold.getItem(i).getCount();
                }
            }
            int need = w.getValue() - have;
            for (BlockEntity be : depots) {
                Container from = (Container) be;
                for (int i = 0; i < from.getContainerSize() && need > 0; i++) {
                    ItemStack s = from.getItem(i);
                    if (!s.is(item)) {
                        continue;
                    }
                    int put = Math.min(need, s.getCount());
                    int left = insert(hold, new ItemStack(item, put));
                    int done = put - left;
                    if (done > 0) {
                        s.shrink(done);
                        from.setItem(i, s.isEmpty() ? ItemStack.EMPTY : s);
                        be.setChanged();
                        need -= done;
                        moved += done;
                    }
                    if (left > 0) {
                        need = 0;           // the hold is full
                    }
                }
            }
        }
        return moved;
    }

    private static int insert(Container c, ItemStack stack) {
        for (int i = 0; i < c.getContainerSize() && !stack.isEmpty(); i++) {
            ItemStack s = c.getItem(i);
            if (!s.isEmpty() && ItemStack.isSameItemSameComponents(s, stack) && s.getCount() < s.getMaxStackSize()) {
                int n = Math.min(stack.getCount(), s.getMaxStackSize() - s.getCount());
                s.grow(n);
                c.setItem(i, s);
                stack.shrink(n);
            }
        }
        for (int i = 0; i < c.getContainerSize() && !stack.isEmpty(); i++) {
            if (c.getItem(i).isEmpty()) {
                int n = Math.min(stack.getCount(), stack.getMaxStackSize());
                c.setItem(i, stack.copyWithCount(n));
                stack.shrink(n);
            }
        }
        return stack.getCount();
    }

    /**
     * A TOW launcher has no hold: Superb Warfare loads it only from a player's hand. Its gunner here takes a missile
     * from the post's depot, puts it in the tube (the launcher's round count set to one) and marks it loaded, once the
     * last shot's reload time is over. Returns 1 for a missile loaded.
     */
    static int loadLauncher(ServerLevel level, Entity v) {
        if (!(Sbw.call(v, "getLoaded") instanceof Boolean loaded) || loaded
            || Sbw.call(v, "getReloadCooldown") instanceof Number n && n.intValue() > 0) {
            return 0;
        }
        Item missile = item("medium_anti_ground_missile");
        if (missile == null) {
            return 0;
        }
        for (BlockEntity be : near(level, v.position(), 10, Supply::depot)) {
            Container from = (Container) be;
            for (int i = 0; i < from.getContainerSize(); i++) {
                ItemStack st = from.getItem(i);
                if (st.is(missile) && roundsInTube(v, 1)) {
                    st.shrink(1);
                    from.setItem(i, st.isEmpty() ? ItemStack.EMPTY : st);
                    be.setChanged();
                    Sbw.call(v, "setLoaded", true);
                    return 1;
                }
            }
        }
        return 0;
    }

    private static boolean roundsInTube(Entity v, int n) {
        try {
            java.lang.reflect.Method m = v.getClass().getMethod("modifyGunData", int.class, java.util.function.Consumer.class);
            boolean[] ok = {false};
            java.util.function.Consumer<Object> set = data -> {
                try {
                    Object value;
                    try {
                        value = data.getClass().getField("ammo").get(data);
                    } catch (NoSuchFieldException e) {
                        value = data.getClass().getMethod("getAmmo").invoke(data);
                    }
                    value.getClass().getMethod("set", int.class).invoke(value, n);
                    ok[0] = true;
                } catch (ReflectiveOperationException | RuntimeException e) {
                    ok[0] = false;
                }
            };
            m.invoke(v, 0, set);
            return ok[0];
        } catch (ReflectiveOperationException | RuntimeException | LinkageError e) {
            return false;
        }
    }

    /** A charging station within its eight blocks' reach of the vehicle (only for the log: the station does the charging). */
    static boolean charger(ServerLevel level, Entity v) {
        return !near(level, v.position(), 8.5 + v.getBbWidth() / 2, Supply::station).isEmpty();
    }

    /**
     * Every two seconds for a crewed vehicle: at its post the crew load it from the depot; it is sent back for supply when
     * low, and released when full again (or when its post has had nothing more for it for five minutes).
     */
    static void tick(ServerLevel level, Entity v, CompoundTag p, boolean atPost) {
        long now = level.getGameTime();
        if (atPost) {
            int moved = reload(level, v) + (kind(v).equals("tow") ? loadLauncher(level, v) : 0);
            if (moved > 0) {
                p.putInt("Reloaded", p.getInt("Reloaded") + moved);
                p.putLong("SupplyGot", now);
                VehicleWatch.event(v, String.format(java.util.Locale.ROOT, "SUPPLY-LOAD {\"vehicle\":\"%s\",\"rounds\":%d,\"aboard\":%d,\"charge\":%.2f}",
                    kind(v), moved, rounds(v)[0], charge(v)));
            }
            if (charge(v) < 0.999 && p.getDouble("LastCharge") < charge(v) - 1e-4) {
                p.putLong("SupplyGot", now);
            }
        }
        p.putDouble("LastCharge", charge(v));
        if (!p.getBoolean("Resupply")) {
            if (low(v)) {
                p.putBoolean("Resupply", true);
                p.putLong("ResupplySince", now);
                p.putLong("SupplyGot", now);
                p.putInt("Resupplies", p.getInt("Resupplies") + 1);
                VehicleWatch.event(v, String.format(java.util.Locale.ROOT, "SUPPLY-RETURN {\"vehicle\":\"%s\",\"charge\":%.2f,\"rounds\":%d,\"full\":%d}",
                    kind(v), charge(v), rounds(v)[0], rounds(v)[1]));
            }
        } else if (full(v) || atPost && now - p.getLong("SupplyGot") > 6000) {
            p.remove("Resupply");
            VehicleWatch.event(v, String.format(java.util.Locale.ROOT, "SUPPLY-DONE {\"vehicle\":\"%s\",\"charge\":%.2f,\"rounds\":%d,\"full\":%d,\"charger\":%b,\"seconds\":%d}",
                kind(v), charge(v), rounds(v)[0], rounds(v)[1], charger(level, v), (now - p.getLong("ResupplySince")) / 20));
        }
    }

    /**
     * A guard's electric gun recharged from a charging station's store within six blocks: the energy the gun takes is the
     * energy the station gives. Returns what the gun received.
     */
    public static int recharge(Entity holder, IEnergyStorage gun, int amount) {
        if (!(holder.level() instanceof ServerLevel level) || amount <= 0) {
            return 0;
        }
        for (BlockEntity be : near(level, holder.position(), 6, Supply::station)) {
            IEnergyStorage store = level.getCapability(Capabilities.EnergyStorage.BLOCK, be.getBlockPos(), null);
            if (store == null || store.getEnergyStored() <= 0) {
                continue;
            }
            int can = gun.receiveEnergy(Math.min(amount, store.getEnergyStored()), true);
            int got = store.extractEnergy(can, false);
            return gun.receiveEnergy(got, false);
        }
        return 0;
    }

    /** The nearest charging station within reach of a guard, for him to walk to (null for none). */
    public static BlockPos stationNear(Entity holder, double reach) {
        if (!(holder.level() instanceof ServerLevel level)) {
            return null;
        }
        BlockPos best = null;
        double bd = Double.MAX_VALUE;
        for (BlockEntity be : near(level, holder.position(), reach, Supply::station)) {
            double d = be.getBlockPos().distToCenterSqr(holder.position());
            if (d < bd) {
                bd = d;
                best = be.getBlockPos();
            }
        }
        return best;
    }

    /**
     * A post's power plant, as the citadel's are built: a charging station (facing north) with a store of energy, the
     * coal blocks of its fuel slot, a hopper on top and a chest of coal blocks over the hopper. Returns false without
     * Superb Warfare.
     */
    public static boolean placeStation(ServerLevel level, BlockPos at, int stored, int coal) {
        ResourceLocation id = Sbw.id("charging_station");
        if (!BuiltInRegistries.BLOCK.containsKey(id)) {
            return false;
        }
        level.setBlock(at, BuiltInRegistries.BLOCK.get(id).defaultBlockState(), 3);
        if (level.getBlockEntity(at) instanceof Container c) {
            c.setItem(0, new ItemStack(net.minecraft.world.item.Items.COAL_BLOCK, Math.min(64, coal)));
        }
        IEnergyStorage store = level.getCapability(Capabilities.EnergyStorage.BLOCK, at, null);
        if (store != null) {
            store.receiveEnergy(stored, false);
        }
        level.setBlock(at.above(), net.minecraft.world.level.block.Blocks.HOPPER.defaultBlockState(), 3);
        level.setBlock(at.above(2), net.minecraft.world.level.block.Blocks.CHEST.defaultBlockState(), 3);
        if (level.getBlockEntity(at.above(2)) instanceof net.minecraft.world.level.block.entity.ChestBlockEntity chest) {
            for (int i = 0; i < 4; i++) {
                chest.setItem(i, new ItemStack(net.minecraft.world.item.Items.COAL_BLOCK, 64));
            }
            name(chest, "発電所の石炭庫");
        }
        return true;
    }

    private static void name(BlockEntity be, String text) {
        be.applyComponents(net.minecraft.core.component.DataComponentMap.builder()
            .set(net.minecraft.core.component.DataComponents.CUSTOM_NAME, net.minecraft.network.chat.Component.literal(text)).build(),
            net.minecraft.core.component.DataComponentPatch.EMPTY);
        be.setChanged();
    }

    /** A depot chest (王国軍の弾薬庫) holding twice the load of each of the given kinds of vehicle. */
    public static void placeDepot(ServerLevel level, BlockPos at, String... kinds) {
        level.setBlock(at, net.minecraft.world.level.block.Blocks.CHEST.defaultBlockState(), 3);
        if (!(level.getBlockEntity(at) instanceof net.minecraft.world.level.block.entity.ChestBlockEntity chest)) {
            return;
        }
        name(chest, DEPOT);
        int slot = 0;
        for (String kind : kinds) {
            for (String[] l : LOAD.getOrDefault(kind, GROUND)) {
                Item item = item(l[0]);
                for (int k = 0; k < 2 && item != null && slot < chest.getContainerSize(); k++) {
                    chest.setItem(slot++, new ItemStack(item, Math.min(item.getDefaultMaxStackSize(), Integer.parseInt(l[1]))));
                }
            }
        }
    }

    /** Empties a vehicle's battery to the given share and its hold of ammunition (the supply test). */
    static void drain(Entity v, double share) {
        if (Sbw.call(v, "getMaxEnergy") instanceof Number max && max.intValue() > 0) {
            Sbw.call(v, "setEnergy", (int) (max.intValue() * share));
        }
        Container c = hold(v);
        if (c != null) {
            for (int i = 0; i < c.getContainerSize(); i++) {
                c.setItem(i, ItemStack.EMPTY);
            }
        }
    }

    /** The JSON of a vehicle's supply for the reports. */
    public static String report(ServerLevel level, Entity v) {
        int[] r = rounds(v);
        Object tube = Sbw.call(v, "getLoaded");
        return String.format(java.util.Locale.ROOT, "{\"vehicle\":\"%s\",\"charge\":%.3f,\"rounds\":%d,\"full\":%d,\"charger\":%b,\"depots\":%d%s}", kind(v),
            charge(v), r[0], r[1], charger(level, v), near(level, v.position(), 10, Supply::depot).size(),
            tube instanceof Boolean b ? ",\"loaded\":" + b : "");
    }
}
