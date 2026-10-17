package jp.oror.reborn;

import com.mojang.authlib.GameProfile;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.fml.ModList;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;

/**
 * Guns for grown villages (v0.17.15), Superb Warfare's own guns, through its API by reflection (0.8.9.x).
 * - The unlock: 10 villagers, a miner, 64 metal (ingots and raw ore in the communal chests) and 64 emeralds. The village
 *   then sets up a gunsmithy near its centre: Superb Warfare's reforging table (six iron ingots).
 * - There it makes guns from the chests' iron, gunpowder and emeralds, one every two minutes, for its strong villagers,
 *   strongest first: pistols and SMGs at first, assault rifles in a 城下町, marksman rifles and machine guns after the
 *   Nether. A gun goes into the villager's hands and is fired, reloaded and worked (bolt action) through Superb
 *   Warfare's own gun data (MobEquipmentUse).
 * - Ammunition: each gun carries spare rounds in Superb Warfare's backup ammo pool ("virtual ammo"), which its reload
 *   draws on; a gunner whose spare rounds run low takes a gunpowder from the chests for three more magazines.
 */
public final class VillageArms {
    private static final String[][] TIERS = {
        {"glock_17", "m_1911", "mp_443"},
        {"mp_5", "vector"},
        {"ak_47", "m_4", "hk_416", "sks", "qbz_95"},
        {"svd", "mk_14", "k_98", "mosin_nagant"},
        {"rpk", "m_60", "aa_12"}
    };
    private static boolean broken;

    private VillageArms() {
    }

    static boolean present() {
        return !broken && ModList.get().isLoaded("superbwarfare");
    }

    private static Item item(String ns, String id) {
        ResourceLocation rl = ResourceLocation.fromNamespaceAndPath(ns, id);
        return BuiltInRegistries.ITEM.containsKey(rl) ? (Item)BuiltInRegistries.ITEM.get(rl) : null;
    }

    static void review(ServerLevel sl, VillageWork.Survey s, VillageProgress.Record r) {
        if (!present()) {
            return;
        }
        long now = sl.getGameTime();
        if (!r.guns) {
            int metal = s.stock("iron_ingot") + s.stock("gold_ingot") + s.stock("copper_ingot") + s.raw;
            if (s.population >= 10 && s.miners >= 1 && metal >= 64 && s.stock("emerald") >= 64) {
                r.guns = true;
                VillageProgress.get(sl).setDirty();
                VillageProgress.announce(sl, s.village, "鉱夫の資源とエメラルドが十分に集まり、銃の製造が解禁されました（Superb Warfare）", true);
            }
            return;
        }
        if (r.gunTable == null || !table(sl, r.gunTable)) {
            r.gunTable = null;
            if (s.stock("iron_ingot") >= 6) {
                BlockPos at = placeTable(sl, s);
                if (at != null) {
                    VillageExpeditions.take(sl, s, "iron_ingot", 6);
                    r.gunTable = at;
                    VillageProgress.get(sl).setDirty();
                    VillageProgress.announce(sl, s.village, "村の中心近くに銃工房（改造台）を設けました", false);
                }
            }
            return;
        }
        if (now < s.nextGun) {
            return;
        }
        s.nextGun = now + 2400L;
        if (s.stock("iron_ingot") < 8 || s.stock("gunpowder") < 4 || s.stock("emerald") < 6) {
            return;
        }
        Villager who = sl.getEntitiesOfClass(Villager.class, new AABB(s.village.center).inflate(64.0, 24.0, 64.0),
                v -> v.isAlive() && VillageAI.strong(v) && VillageLedger.of(v) == s.village && !armed(v) && !v.getPersistentData().getBoolean("OrorWanderer"))
            .stream()
            .max(java.util.Comparator.comparingInt(VillageExpeditions::power))
            .orElse(null);
        if (who == null) {
            return;
        }
        int tier = Math.min(TIERS.length - 1, Math.max(0, r.stage - 2) + (r.gunsMade % 2));
        ItemStack gun = gun(sl, tier);
        if (gun.isEmpty()) {
            return;
        }
        VillageExpeditions.take(sl, s, "iron_ingot", 8);
        VillageExpeditions.take(sl, s, "gunpowder", 4);
        VillageExpeditions.take(sl, s, "emerald", 6);
        ItemStack rest = who.getInventory().addItem(gun);
        if (!rest.isEmpty()) {
            VillageProgress.get(sl).deliver(r, List.of(rest), sl.registryAccess());
        }
        r.gunsMade++;
        VillageProgress.get(sl).setDirty();
        sl.sendParticles(ParticleTypes.CRIT, r.gunTable.getX() + 0.5, r.gunTable.getY() + 1.2, r.gunTable.getZ() + 0.5, 12, 0.4, 0.2, 0.4, 0.1);
        RelicEffects.sound(sl, r.gunTable, SoundEvents.ANVIL_USE, 0.8F, 1.3F);
        VillageProgress.announce(sl, s.village, "銃工房で「" + gun.getHoverName().getString() + "」を製作し、" + who.getName().getString() + "に持たせました", false);
    }

    /** A villager already holding or carrying a gun. */
    static boolean armed(Villager v) {
        if (MobEquipmentUse.kind(v.getMainHandItem()).equals("gun")) {
            return true;
        }
        for (ItemStack st : v.getInventory().getItems()) {
            if (!st.isEmpty() && MobEquipmentUse.kind(st).equals("gun")) {
                return true;
            }
        }
        return false;
    }

    /** The gunsmithy: Superb Warfare's reforging table, or a smithing table where it is missing. */
    private static Item tableItem() {
        Item reforging = item("superbwarfare", "reforging_table");
        return reforging != null ? reforging : item("minecraft", "smithing_table");
    }

    private static boolean table(ServerLevel sl, BlockPos p) {
        Item item = tableItem();
        return item instanceof BlockItem b && sl.hasChunkAt(p) && sl.getBlockState(p).is(b.getBlock());
    }

    /** Set the table down as a player would (its item handles facing and any second half). */
    private static BlockPos placeTable(ServerLevel sl, VillageWork.Survey s) {
        if (!(tableItem() instanceof BlockItem block) || !sl.getGameRules().getBoolean(net.minecraft.world.level.GameRules.RULE_MOBGRIEFING)) {
            return null;
        }
        BlockPos c = s.village.center;
        FakePlayer actor = FakePlayerFactory.get(sl, new GameProfile(UUID.nameUUIDFromBytes("oror_gunsmith".getBytes()), "[Village Gunsmith]"));
        for (int i = 0; i < 16; i++) {
            double a = sl.random.nextDouble() * Math.PI * 2.0;
            double d = 4.0 + sl.random.nextDouble() * 6.0;
            BlockPos p = VillageExpeditions.top(sl, c.offset((int)Math.round(Math.cos(a) * d), 0, (int)Math.round(Math.sin(a) * d)));
            if (p == null || Math.abs(p.getY() - c.getY()) > 3 || !VillageWork.open(sl, p)) {
                continue;
            }
            ItemStack stack = block.getDefaultInstance();
            actor.setItemInHand(InteractionHand.MAIN_HAND, stack);
            BlockPlaceContext context = new BlockPlaceContext(actor, InteractionHand.MAIN_HAND, stack,
                new BlockHitResult(Vec3.atCenterOf(p.below()).add(0.0, 0.5, 0.0), Direction.UP, p.below(), false));
            if (block.place(context).consumesAction() && table(sl, p)) {
                s.village.communal.add(p.asLong());
                return p;
            }
        }
        return null;
    }

    // ------------------------------------------------------------------------------------- Superb Warfare by reflection
    /** A Superb Warfare gun of the tier (or a lower one) with three magazines of spare rounds; empty if none. */
    static ItemStack gun(ServerLevel sl, int tier) {
        if (!present()) {
            return ItemStack.EMPTY;
        }
        try {
            for (int t = Math.min(tier, TIERS.length - 1); t >= 0; t--) {
                List<String> ids = new ArrayList<>(List.of(TIERS[t]));
                java.util.Collections.shuffle(ids, new java.util.Random(sl.random.nextLong()));
                for (String id : ids) {
                    Item item = item("superbwarfare", id);
                    if (item == null) {
                        continue;
                    }
                    ItemStack gun = item.getDefaultInstance();
                    if (!MobEquipmentUse.kind(gun).equals("gun")) {
                        continue;
                    }
                    spare(gun, magazine(gun) * 3);
                    return gun;
                }
            }
        } catch (LinkageError | ReflectiveOperationException | RuntimeException e) {
            broken = true;
            System.out.println("[OROR_VILLAGE_ARMS] Superb Warfare guns disabled: " + e);
        }
        return ItemStack.EMPTY;
    }

    private static Object data(ItemStack gun) throws ReflectiveOperationException {
        return Class.forName("com.atsuishio.superbwarfare.data.gun.GunData").getMethod("from", ItemStack.class).invoke(null, gun);
    }

    private static Object value(Object data, String field) throws ReflectiveOperationException {
        Field f = data.getClass().getField(field);
        return f.get(data);
    }

    private static int magazine(ItemStack gun) throws ReflectiveOperationException {
        Object data = data(gun);
        Object prop = Class.forName("com.atsuishio.superbwarfare.data.gun.GunProp").getField("MAGAZINE").get(null);
        Method get = null;
        for (Method m : data.getClass().getMethods()) {
            if (m.getName().equals("get") && m.getParameterCount() == 1 && m.getParameterTypes()[0].isInstance(prop)) {
                get = m;
                break;
            }
        }
        Object n = get == null ? null : get.invoke(data, prop);
        return n instanceof Number num ? Math.max(1, num.intValue()) : 10;
    }

    private static int spareLeft(ItemStack gun) throws ReflectiveOperationException {
        Object virtual = value(data(gun), "virtualAmmo");
        return ((Number)virtual.getClass().getMethod("get").invoke(virtual)).intValue();
    }

    /** Set the gun's spare rounds (Superb Warfare's backup ammo pool, which reloading draws on) and write it to the item. */
    private static void spare(ItemStack gun, int rounds) throws ReflectiveOperationException {
        Object data = data(gun);
        Object virtual = value(data, "virtualAmmo");
        virtual.getClass().getMethod("set", int.class).invoke(virtual, rounds);
        Object version = value(data, "nbtVersion");
        version.getClass().getMethod("invalidateState").invoke(version);
        data.getClass().getMethod("save").invoke(data);
    }

    private static boolean warfare(ItemStack gun) {
        return !gun.isEmpty() && BuiltInRegistries.ITEM.getKey(gun.getItem()).getNamespace().equals("superbwarfare")
            && MobEquipmentUse.kind(gun).equals("gun");
    }

    /** The ammunition chore: a gunner low on spare rounds takes a gunpowder from the chests for three more magazines. */
    static int ammo(Villager v, ServerLevel sl, VillageWork.Survey s) {
        if (!present() || !warfare(v.getMainHandItem())) {
            return VillageWork.CANNOT;
        }
        try {
            ItemStack gun = v.getMainHandItem();
            int mag = magazine(gun);
            int left = spareLeft(gun);
            if (left >= mag * 2) {
                return VillageWork.CANNOT;
            }
            if (VillageWork.count(v, VillageWork.is("gunpowder")) == 0) {
                return VillageWork.fetch(v, sl, s, VillageWork.is("gunpowder"), 2);
            }
            v.getInventory().getItem(VillageWork.slotOf(v, VillageWork.is("gunpowder"))).shrink(1);
            spare(gun, left + mag * 3);
            VillagerLife.data(v).putString("Task", "弾薬を補充");
            return VillageWork.ACTED;
        } catch (LinkageError | ReflectiveOperationException | RuntimeException e) {
            broken = true;
            return VillageWork.CANNOT;
        }
    }

    /** Whether this villager's gun wants ammunition (for the chores list). */
    static boolean low(Villager v) {
        if (!present() || !warfare(v.getMainHandItem())) {
            return false;
        }
        try {
            return spareLeft(v.getMainHandItem()) < magazine(v.getMainHandItem()) * 2;
        } catch (LinkageError | ReflectiveOperationException | RuntimeException e) {
            broken = true;
            return false;
        }
    }
}
