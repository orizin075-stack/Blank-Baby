package jp.oror.reborn.ci;

import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.DoorBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.DoubleBlockHalf;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.energy.IEnergyStorage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * The part of /oror sweep for the arms that a right-click alone does not show (051, after 0.17.27's client harness):
 * the railgun and the laser gun held by the stand-in, refused empty and one short of a full charge, allowed full, loaded
 * and fired through Superb Warfare's own shoot path (by reflection, as the harness did) at three zombies in a line, the
 * last behind a stone wall; and the Blueprinter scanning a small house corner to corner and printing it, turned.
 * SWEEP-ARMS lines say how each went against what is expected.
 */
final class SweepArms {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Sweep");

    private SweepArms() {
    }

    private static String steps = "";
    private static int cartsLeft = -1;

    /** The guns, and the Blueprinter's scan and print begun; check() looks at the print once it has had time to rise. */
    static void run(ServerLevel level, Player p, BlockPos base) {
        for (String[] g : new String[][]{{"railgun", "rail_slug"}, {"laser_gun", "focus_cell"}}) {
            try {
                gun(level, p, base, g[0], g[1]);
            } catch (Throwable ex) {
                log("{\"gun\":\"%s\",\"error\":\"%s\"}", g[0], esc(ex.toString()));
            }
        }
        try {
            blueprint(level, p, base);
        } catch (Throwable ex) {
            log("{\"blueprinter\":true,\"error\":\"%s\"}", esc(ex.toString()));
        }
    }

    /** The print against the house (the Blueprinter lays its blocks over some seconds, not at once). */
    static void check(ServerLevel level, BlockPos base) {
        try {
            compare(level, base);
        } catch (Throwable ex) {
            log("{\"blueprinter\":true,\"error\":\"%s\"}", esc(ex.toString()));
        }
    }

    private static void log(String fmt, Object... args) {
        LOG.info("SWEEP-ARMS " + String.format(Locale.ROOT, fmt, args));
    }

    private static Item item(String id) {
        return BuiltInRegistries.ITEM.getOptional(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", id)).orElse(null);
    }

    /** Stands the stand-in at feet, facing a point. */
    private static void face(Player p, Vec3 feet, Vec3 at) {
        p.moveTo(feet.x, feet.y, feet.z, 0F, 0F);
        Vec3 eye = feet.add(0, p.getEyeHeight(), 0);
        Vec3 d = at.subtract(eye);
        float yaw = (float) (Mth.atan2(d.z, d.x) * Mth.RAD_TO_DEG) - 90F;
        float pitch = (float) -(Mth.atan2(d.y, Math.sqrt(d.x * d.x + d.z * d.z)) * Mth.RAD_TO_DEG);
        p.moveTo(feet.x, feet.y, feet.z, yaw, pitch);
        p.setYHeadRot(yaw);
    }

    private static void fill(ServerLevel level, BlockPos a, BlockPos b, BlockState s) {
        for (BlockPos q : BlockPos.betweenClosed(a, b)) {
            level.setBlock(q, s, 2);
        }
    }

    private static void arena(ServerLevel level, BlockPos base) {
        for (Entity e : level.getEntities((Entity) null, new AABB(base).inflate(40), e -> !(e instanceof Player))) {
            e.discard();
        }
        fill(level, base.offset(-14, -1, -12), base.offset(14, -1, 24), Blocks.SMOOTH_STONE.defaultBlockState());
        fill(level, base.offset(-14, 0, -12), base.offset(14, 12, 24), Blocks.AIR.defaultBlockState());
        fill(level, base.offset(-1, 0, 12), base.offset(1, 3, 13), Blocks.STONE.defaultBlockState());
        fill(level, base.offset(-1, 0, 6), base.offset(1, 3, 6), Blocks.GLASS.defaultBlockState());
        for (int dz : new int[]{8, 10, 16}) {
            Zombie z = EntityType.ZOMBIE.create(level);
            if (z != null) {
                z.moveTo(base.getX() + 0.5, base.getY(), base.getZ() + dz + 0.5, 180F, 0F);
                z.setNoAi(true);
                z.setPersistenceRequired();
                z.addTag("oror_sweep");
                level.addFreshEntity(z);
            }
        }
    }

    private static Object gunData(ItemStack stack) throws ReflectiveOperationException {
        Class<?> type = Class.forName("com.atsuishio.superbwarfare.data.gun.GunData");
        return type.getMethod("from", ItemStack.class).invoke(null, stack);
    }

    private static boolean canShoot(ItemStack stack, Player p) throws ReflectiveOperationException {
        Object data = gunData(stack);
        return (Boolean) data.getClass().getMethod("canShoot", Entity.class).invoke(data, p);
    }

    private static int count(Player p, Item item) {
        int n = 0;
        for (ItemStack s : p.getInventory().items) {
            if (s.is(item)) {
                n += s.getCount();
            }
        }
        return n;
    }

    private static void gun(ServerLevel level, Player p, BlockPos base, String gun, String ammo) throws ReflectiveOperationException {
        Item item = item(gun), round = item(ammo);
        if (item == null || round == null) {
            log("{\"gun\":\"%s\",\"registered\":false}", gun);
            return;
        }
        arena(level, base);
        p.getInventory().clearContent();
        face(p, Vec3.atBottomCenterOf(base), new Vec3(base.getX() + 0.5, base.getY() + 1, base.getZ() + 16.5));
        ItemStack stack = new ItemStack(item);
        p.getInventory().setItem(p.getInventory().selected, stack);
        p.getInventory().setItem(20, new ItemStack(round, 3));
        Object data = gunData(stack);
        data.getClass().getMethod("reloadAmmo", Entity.class).invoke(data, p);
        data.getClass().getMethod("save").invoke(data);
        int left = count(p, round);
        boolean empty = canShoot(stack, p);
        IEnergyStorage energy = stack.getCapability(Capabilities.EnergyStorage.ITEM);
        boolean shortOne = false, full = false;
        int max = -1;
        if (energy != null) {
            max = energy.getMaxEnergyStored();
            energy.receiveEnergy(max - 1, false);
            shortOne = canShoot(stack, p);
            energy.receiveEnergy(max, false);
            full = canShoot(stack, p);
        }
        Object fire = gunData(stack);
        Method shoot = fire.getClass().getMethod("shoot", Entity.class, double.class, boolean.class, UUID.class);
        shoot.invoke(fire, p, 0.0, false, null);
        fire.getClass().getMethod("save").invoke(fire);
        List<String> living = new ArrayList<>();
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(base).inflate(30), e -> e instanceof Zombie && e.isAlive())) {
            living.add("z" + (e.blockPosition().getZ() - base.getZ()) + "hp" + (int) e.getHealth());
        }
        IEnergyStorage after = stack.getCapability(Capabilities.EnergyStorage.ITEM);
        log("{\"gun\":\"%s\",\"roundsLeftAfterLoad\":%d,\"expect\":2,\"canShootEmpty\":%b,\"canShootOneShort\":%b,\"canShootFull\":%b,"
                + "\"maxEnergy\":%d,\"zombiesLeft\":\"%s\",\"energyAfter\":%d,\"canShootAgain\":%b,\"ok\":%b}", gun, left, empty, shortOne, full, max,
            living, after == null ? -1 : after.getEnergyStored(), canShoot(stack, p),
            left == 2 && !empty && !shortOne && full && living.isEmpty() && (after == null || after.getEnergyStored() == 0));
    }

    // ---------------------------------------------------------------------------------------------- the Blueprinter

    private static void blueprint(ServerLevel level, Player p, BlockPos base) {
        Item bp = item("blueprinter"), cart = item("matter_cartridge");
        if (bp == null || cart == null) {
            log("{\"blueprinter\":true,\"registered\":false}");
            return;
        }
        arena(level, base);
        for (Entity e : level.getEntities((Entity) null, new AABB(base).inflate(40), e -> e instanceof Zombie)) {
            e.discard();
        }
        fill(level, base.offset(-14, 0, -12), base.offset(14, 12, 24), Blocks.AIR.defaultBlockState());
        BlockPos lo = base.offset(5, 0, -6);
        int x = lo.getX(), y = lo.getY(), z = lo.getZ();
        for (BlockPos q : BlockPos.betweenClosed(lo, lo.offset(4, 3, 4))) {
            boolean shell = q.getX() == x || q.getX() == x + 4 || q.getY() == y || q.getY() == y + 3 || q.getZ() == z || q.getZ() == z + 4;
            level.setBlock(q, shell ? Blocks.OAK_PLANKS.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
        }
        fill(level, lo.offset(0, 4, 0), lo.offset(4, 4, 4), Blocks.STONE_BRICKS.defaultBlockState());
        level.setBlock(lo.offset(0, 0, 2), Blocks.OAK_DOOR.defaultBlockState().setValue(DoorBlock.HALF, DoubleBlockHalf.LOWER), 2);
        level.setBlock(lo.offset(0, 1, 2), Blocks.OAK_DOOR.defaultBlockState().setValue(DoorBlock.HALF, DoubleBlockHalf.UPPER), 2);
        level.setBlock(lo.offset(2, 1, 0), Blocks.GLASS_PANE.defaultBlockState(), 2);
        level.setBlock(lo.offset(2, 1, 4), Blocks.GLASS_PANE.defaultBlockState(), 2);
        level.setBlock(lo.offset(3, 0, 3), Blocks.CHEST.defaultBlockState(), 2);
        level.setBlock(lo.offset(2, 3, 2), Blocks.LANTERN.defaultBlockState(), 2);
        level.setBlock(lo.offset(3, 0, 1), Blocks.DIAMOND_BLOCK.defaultBlockState(), 2);
        p.getInventory().clearContent();
        p.getInventory().setItem(p.getInventory().selected, new ItemStack(bp));
        p.getInventory().setItem(21, new ItemStack(cart, 2));
        List<String> steps = new ArrayList<>();
        int x0 = lo.getX();
        // the two corners, each looked at from where it can be seen
        face(p, Vec3.atBottomCenterOf(lo.offset(-2, 0, -3)), Vec3.atCenterOf(lo));
        steps.add("scan1:" + p.getMainHandItem().use(level, p, InteractionHand.MAIN_HAND).getResult());
        BlockPos far = lo.offset(4, 4, 4);
        face(p, Vec3.atBottomCenterOf(lo.offset(4, 8, 8)), Vec3.atCenterOf(far));
        steps.add("scan2:" + p.getMainHandItem().use(level, p, InteractionHand.MAIN_HAND).getResult());
        BlockPos target = base.offset(0, 0, 12);
        face(p, Vec3.atBottomCenterOf(base), new Vec3(target.getX() + 0.5, target.getY() - 0.5, target.getZ() + 0.5));
        steps.add("preview:" + p.getMainHandItem().use(level, p, InteractionHand.MAIN_HAND).getResult());
        steps.add("print:" + p.getMainHandItem().use(level, p, InteractionHand.MAIN_HAND).getResult());
        SweepArms.steps = steps.toString();
        SweepArms.cartsLeft = count(p, cart);
    }

    private static void compare(ServerLevel level, BlockPos base) {
        BlockPos lo = base.offset(5, 0, -6);
        BlockPos target = base.offset(0, 0, 12);
        BlockPos origin = target.offset(-2, 0, -2);
        int same = 0, differ = 0, diamonds = 0, built = 0;
        for (int dx = 0; dx < 5; dx++) {
            for (int dy = 0; dy < 5; dy++) {
                for (int dz = 0; dz < 5; dz++) {
                    BlockState src = level.getBlockState(lo.offset(dx, dy, dz));
                    BlockState dst = level.getBlockState(origin.offset(4 - dx, dy, 4 - dz));
                    if (dst.is(Blocks.DIAMOND_BLOCK)) {
                        diamonds++;
                    }
                    if (!dst.isAir()) {
                        built++;
                    }
                    if (src.getBlock() == dst.getBlock()) {
                        same++;
                    } else {
                        differ++;
                    }
                }
            }
        }
        log("{\"blueprinter\":true,\"steps\":\"%s\",\"cartridgesLeft\":%d,\"printedBlocks\":%d,\"same\":%d,\"differ\":%d,\"expectDiffer\":1,"
            + "\"diamondsPrinted\":%d,\"ok\":%b}", steps, cartsLeft, built, same, differ, diamonds, differ <= 1 && diamonds == 0 && built > 50);
    }

    private static String esc(String s) {
        return s == null ? "" : s.replace("\\", "/").replace("\"", "'").replace("\n", " ");
    }
}
