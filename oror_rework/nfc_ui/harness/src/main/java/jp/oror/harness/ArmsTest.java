package jp.oror.harness;

import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import java.util.function.Consumer;
import net.minecraft.client.CameraType;
import net.minecraft.client.Minecraft;
import net.minecraft.client.server.IntegratedServer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.energy.IEnergyStorage;

/**
 * CI only: OROR 0.17.27's arms in a survival world. The railgun and the laser gun are held, refused while not fully
 * charged, charged, loaded and fired through Superb Warfare's own shoot path (reflection: the harness does not compile
 * against Superb Warfare) at zombies in a line, one behind a stone wall; the Blueprinter scans a small house and
 * prints it, turned, through its real use(). Every check is written to the harness log; screenshots 11-18.
 */
final class ArmsTest {
    private static BlockPos base;
    private static String name;

    static void step(Minecraft mc, int t) {
        switch (t) {
            case 1100 -> server(mc, ArmsTest::arena);
            case 1140 -> server(mc, p -> gun(p, "railgun", "rail_slug"));
            case 1240 -> Harness.shotNow(mc, "11_railgun_held");
            case 1250 -> server(mc, p -> fire(p, "railgun"));
            case 1252 -> Harness.shotNow(mc, "12_railgun_fired");
            case 1290 -> server(mc, p -> after(p, "railgun"));
            case 1300 -> server(mc, ArmsTest::arena);
            case 1340 -> server(mc, p -> gun(p, "laser_gun", "focus_cell"));
            case 1440 -> Harness.shotNow(mc, "13_laser_held");
            case 1450 -> server(mc, p -> fire(p, "laser_gun"));
            case 1452 -> Harness.shotNow(mc, "14_laser_fired");
            case 1490 -> server(mc, p -> after(p, "laser_gun"));
            case 1500 -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT);
            case 1540 -> Harness.shotNow(mc, "15_laser_third_person");
            case 1550 -> {
                mc.options.setCameraType(CameraType.FIRST_PERSON);
                server(mc, ArmsTest::house);
            }
            case 1600 -> server(mc, p -> scan(p, true));
            case 1620 -> server(mc, p -> scan(p, false));
            case 1660 -> server(mc, p -> print(p, false));
            case 1700 -> Harness.shotNow(mc, "16_blueprint_preview");
            case 1710 -> server(mc, p -> print(p, true));
            case 1820 -> server(mc, ArmsTest::look);
            case 1860 -> {
                Harness.shotNow(mc, "17_blueprint_printed");
                server(mc, ArmsTest::compare);
            }
            case 1870 -> server(mc, ArmsTest::inventory);
            case 1880 -> Harness.openInventory(mc);
            case 1940 -> Harness.shotNow(mc, "18_arms_inventory");
            case 1950 -> Harness.closeScreen(mc);
            case 1960 -> server(mc, p -> creatures(p, new String[] {"demiurgos", "eomaia", "enkou", "chaos"}));
            case 2060 -> Harness.shotNow(mc, "19_creatures_a");
            case 2070 -> server(mc, p -> creatures(p, new String[] {"teia", "kurma", "bahamut", "hephaistos"}));
            case 2170 -> Harness.shotNow(mc, "20_creatures_b");
            case 2180 -> server(mc, p -> creatures(p, new String[] {"yggdrasil", "mels"}));
            case 2280 -> Harness.shotNow(mc, "21_creatures_c");
            default -> { }
        }
    }

    static boolean active(int t) {
        return t >= 1100 && t <= 2280;
    }

    /** The rebuilt non-human characters, frozen in a row facing the camera. */
    private static void creatures(ServerPlayer player, String[] ids) {
        int x = base.getX(), y = base.getY(), z = base.getZ();
        run(player, "kill @e[type=!minecraft:player]");
        run(player, String.format(Locale.ROOT, "fill %d %d %d %d %d %d minecraft:air", x - 14, y, z + 6, x + 14, y + 12, z + 24));
        for (int k = 0; k < ids.length; k++) {
            int cx = x + (ids.length == 1 ? 0 : -12 + k * 24 / (ids.length - 1));
            String id = "oror_supreme_bosses:" + ids[k];
            boolean known = BuiltInRegistries.ENTITY_TYPE.containsKey(ResourceLocation.parse(id));
            Harness.noteNow("arms: creature " + id + (known ? "" : " is not registered"));
            run(player, String.format(Locale.ROOT, "summon %s %d %d %d {NoAI:1b,PersistenceRequired:1b,Rotation:[180f,0f]}", id, cx, y, z + 20));
        }
        run(player, String.format(Locale.ROOT, "tp %s %d %d %d facing %d %d %d", name, x, y + 4, z + 2, x, y + 3, z + 20));
    }

    private static void server(Minecraft mc, Consumer<ServerPlayer> work) {
        IntegratedServer server = mc.getSingleplayerServer();
        if (server == null || mc.player == null) return;
        UUID id = mc.player.getUUID();
        name = mc.player.getGameProfile().getName();
        server.execute(() -> {
            ServerPlayer player = server.getPlayerList().getPlayer(id);
            if (player == null) return;
            try {
                work.accept(player);
            } catch (Throwable error) {
                Harness.noteNow("arms: " + error);
                for (StackTraceElement e : error.getStackTrace()) {
                    if (e.getClassName().startsWith("jp.oror")) Harness.noteNow("  at " + e);
                }
            }
        });
    }

    private static void run(ServerPlayer player, String command) {
        player.getServer().getCommands().performPrefixedCommand(player.getServer().createCommandSourceStack(), command);
    }

    private static Item item(String id) {
        return BuiltInRegistries.ITEM.getOptional(ResourceLocation.parse(id)).orElse(null);
    }

    /** A flat stone floor around the player, three still zombies down the line of sight and a stone wall before the last. */
    private static void arena(ServerPlayer player) {
        if (base == null) base = player.blockPosition();
        int x = base.getX(), y = base.getY(), z = base.getZ();
        run(player, "execute as " + name + " at @s run kill @e[type=!minecraft:player,distance=..96]");
        run(player, "effect give " + name + " minecraft:resistance infinite 4 true");
        run(player, "effect give " + name + " minecraft:saturation infinite 0 true");
        run(player, String.format(Locale.ROOT, "fill %d %d %d %d %d %d minecraft:smooth_stone", x - 14, y - 1, z - 12, x + 14, y - 1, z + 24));
        run(player, String.format(Locale.ROOT, "fill %d %d %d %d %d %d minecraft:air", x - 14, y, z - 12, x + 14, y + 12, z + 24));
        run(player, String.format(Locale.ROOT, "fill %d %d %d %d %d %d minecraft:stone", x - 1, y, z + 12, x + 1, y + 3, z + 13));
        run(player, String.format(Locale.ROOT, "fill %d %d %d %d %d %d minecraft:glass", x - 1, y, z + 6, x + 1, y + 3, z + 6));
        for (int dz : new int[] {8, 10, 16}) {
            run(player, String.format(Locale.ROOT, "summon minecraft:zombie %d %d %d {NoAI:1b,PersistenceRequired:1b,Rotation:[180f,0f]}", x, y, z + dz));
        }
        run(player, String.format(Locale.ROOT, "tp %s %d %d %d facing %d %d %d", name, x, y, z, x, y + 1, z + 16));
        run(player, "gamemode survival " + name);
        Harness.noteNow("arms: arena at " + base);
    }

    /** Puts the gun in hand with its ammunition; checks it is refused empty, then charges and loads it. */
    private static void gun(ServerPlayer player, String gun, String ammo) {
        Item item = item("oror_supreme_bosses:" + gun);
        Item slug = item("oror_supreme_bosses:" + ammo);
        if (item == null || slug == null) {
            Harness.noteNow("arms: " + gun + " or " + ammo + " is not registered");
            return;
        }
        ItemStack stack = new ItemStack(item);
        player.getInventory().setItem(player.getInventory().selected, stack);
        player.getInventory().setItem(20, new ItemStack(slug, 3));
        try {
            Object data = gunData(stack);
            data.getClass().getMethod("reloadAmmo", Entity.class).invoke(data, player);
            data.getClass().getMethod("save").invoke(data);
            Harness.noteNow("arms: " + gun + " loaded, ammo item left " + count(player, slug) + " (expect 2)");
            Harness.noteNow("arms: " + gun + " can shoot empty: " + canShoot(stack, player) + " (expect false)");
            IEnergyStorage energy = stack.getCapability(Capabilities.EnergyStorage.ITEM);
            if (energy == null) {
                Harness.noteNow("arms: " + gun + " has no energy capability");
                return;
            }
            energy.receiveEnergy(energy.getMaxEnergyStored() - 1, false);
            Harness.noteNow("arms: " + gun + " can shoot at " + energy.getEnergyStored() + "/" + energy.getMaxEnergyStored() + ": "
                + canShoot(stack, player) + " (expect false)");
            energy.receiveEnergy(energy.getMaxEnergyStored(), false);
            Harness.noteNow("arms: " + gun + " can shoot full " + energy.getEnergyStored() + "/" + energy.getMaxEnergyStored() + ": "
                + canShoot(stack, player) + " (expect true)");
        } catch (ReflectiveOperationException error) {
            Harness.noteNow("arms: " + gun + " reflection " + error);
        }
    }

    private static void fire(ServerPlayer player, String gun) {
        ItemStack stack = player.getMainHandItem();
        try {
            Object data = gunData(stack);
            Method shoot = data.getClass().getMethod("shoot", Entity.class, double.class, boolean.class, UUID.class);
            shoot.invoke(data, player, 0.0, false, null);
            data.getClass().getMethod("save").invoke(data);
        } catch (ReflectiveOperationException error) {
            Harness.noteNow("arms: " + gun + " shoot " + error);
        }
        Harness.noteNow("arms: " + gun + " fired");
    }

    /** What the shot did: the zombies left, the energy, and whether a second shot is allowed. */
    private static void after(ServerPlayer player, String gun) {
        ServerLevel level = player.serverLevel();
        List<String> left = new ArrayList<>();
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(base).inflate(30), e -> !(e instanceof ServerPlayer))) {
            left.add(BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).getPath() + "@" + e.blockPosition().getZ() + " hp " + (int) e.getHealth());
        }
        ItemStack stack = player.getMainHandItem();
        IEnergyStorage energy = stack.getCapability(Capabilities.EnergyStorage.ITEM);
        Harness.noteNow("arms: after " + gun + ": living " + left + " (expect none), energy "
            + (energy == null ? "?" : energy.getEnergyStored()) + " (expect 0), can shoot again: " + canShoot(stack, player) + " (expect false)");
    }

    private static Object gunData(ItemStack stack) throws ReflectiveOperationException {
        Class<?> type = Class.forName("com.atsuishio.superbwarfare.data.gun.GunData");
        return type.getMethod("from", ItemStack.class).invoke(null, stack);
    }

    private static boolean canShoot(ItemStack stack, ServerPlayer player) {
        try {
            Object data = gunData(stack);
            return (Boolean) data.getClass().getMethod("canShoot", Entity.class).invoke(data, player);
        } catch (ReflectiveOperationException error) {
            Harness.noteNow("arms: canShoot " + error);
            return false;
        }
    }

    private static int count(ServerPlayer player, Item item) {
        int n = 0;
        for (ItemStack s : player.getInventory().items) if (s.is(item)) n += s.getCount();
        return n;
    }

    // -- Blueprinter

    private static BlockPos houseLo() {
        return base.offset(5, 0, -6);
    }

    /** A 5x5x5 house to the east: plank walls with a door and windows, a stone-brick roof, a lamp and a chest inside. */
    private static void house(ServerPlayer player) {
        run(player, "kill @e[type=minecraft:zombie]");
        BlockPos lo = houseLo();
        int x = lo.getX(), y = lo.getY(), z = lo.getZ();
        run(player, String.format(Locale.ROOT, "fill %d %d %d %d %d %d minecraft:air", base.getX() - 14, y, base.getZ() - 12, base.getX() + 14, y + 12, base.getZ() + 24));
        run(player, String.format(Locale.ROOT, "fill %d %d %d %d %d %d minecraft:oak_planks hollow", x, y, z, x + 4, y + 3, z + 4));
        run(player, String.format(Locale.ROOT, "fill %d %d %d %d %d %d minecraft:stone_bricks", x, y + 4, z, x + 4, y + 4, z + 4));
        run(player, String.format(Locale.ROOT, "setblock %d %d %d minecraft:oak_door[facing=west,half=lower]", x, y, z + 2));
        run(player, String.format(Locale.ROOT, "setblock %d %d %d minecraft:oak_door[facing=west,half=upper]", x, y + 1, z + 2));
        run(player, String.format(Locale.ROOT, "setblock %d %d %d minecraft:glass_pane", x + 2, y + 1, z));
        run(player, String.format(Locale.ROOT, "setblock %d %d %d minecraft:glass_pane", x + 2, y + 1, z + 4));
        run(player, String.format(Locale.ROOT, "setblock %d %d %d minecraft:chest[facing=west]", x + 3, y, z + 3));
        run(player, String.format(Locale.ROOT, "setblock %d %d %d minecraft:lantern[hanging=true]", x + 2, y + 3, z + 2));
        run(player, String.format(Locale.ROOT, "setblock %d %d %d minecraft:diamond_block", x + 3, y, z + 1));
        Item bp = item("oror_supreme_bosses:blueprinter");
        Item cart = item("oror_supreme_bosses:matter_cartridge");
        if (bp == null || cart == null) {
            Harness.noteNow("arms: blueprinter or matter_cartridge is not registered");
            return;
        }
        player.getInventory().setItem(player.getInventory().selected, new ItemStack(bp));
        player.getInventory().setItem(21, new ItemStack(cart, 2));
        Harness.noteNow("arms: house at " + lo + " (has a diamond block, which must not be copied)");
    }

    /** Looks at a corner from a place it can be seen from and uses the Blueprinter, as a player would. */
    private static void scan(ServerPlayer player, boolean first) {
        BlockPos lo = houseLo();
        BlockPos corner = first ? lo : lo.offset(4, 4, 4);
        BlockPos eye = first ? lo.offset(-2, 0, -3) : lo.offset(4, 8, 8);
        run(player, String.format(Locale.ROOT, "tp %s %d %d %d facing %.1f %.1f %.1f", name, eye.getX(), eye.getY(), eye.getZ(),
            corner.getX() + 0.5, corner.getY() + 0.5, corner.getZ() + 0.5));
        use(player, "scan corner " + corner);
    }

    private static BlockPos printTarget() {
        return base.offset(0, 0, 12);
    }

    private static void print(ServerPlayer player, boolean confirm) {
        BlockPos target = printTarget();
        run(player, String.format(Locale.ROOT, "tp %s %d %d %d facing %.1f %.1f %.1f", name, base.getX(), base.getY(), base.getZ(),
            target.getX() + 0.5, target.getY() - 0.5, target.getZ() + 0.5));
        use(player, confirm ? "print (confirm)" : "print (preview)");
        if (confirm) {
            Harness.noteNow("arms: cartridges left " + count(player, item("oror_supreme_bosses:matter_cartridge")) + " (house: 2 given)");
        }
    }

    private static void use(ServerPlayer player, String what) {
        ItemStack stack = player.getMainHandItem();
        var result = stack.use(player.level(), player, InteractionHand.MAIN_HAND);
        Harness.noteNow("arms: blueprinter " + what + " -> " + result.getResult() + ", item data " + stack.getComponents());
    }

    private static void look(ServerPlayer player) {
        BlockPos t = printTarget();
        run(player, String.format(Locale.ROOT, "tp %s %d %d %d facing %d %d %d", name, base.getX() - 8, base.getY() + 9, base.getZ() - 10, base.getX() + 3, base.getY() + 1, base.getZ() + 6));
    }

    /** The print against the house turned 180 degrees: same blocks, no diamond block, an empty chest. */
    private static void compare(ServerPlayer player) {
        ServerLevel level = player.serverLevel();
        BlockPos lo = houseLo();
        BlockPos t = printTarget();
        BlockPos origin = t.offset(-2, 0, -2);
        int same = 0, differ = 0, diamonds = 0;
        List<String> samples = new ArrayList<>();
        for (int dx = 0; dx < 5; dx++) {
            for (int dy = 0; dy < 5; dy++) {
                for (int dz = 0; dz < 5; dz++) {
                    BlockState src = level.getBlockState(lo.offset(dx, dy, dz));
                    BlockState dst = level.getBlockState(origin.offset(4 - dx, dy, 4 - dz));
                    if (dst.getBlock().getDescriptionId().contains("diamond_block")) diamonds++;
                    if (src.getBlock() == dst.getBlock()) same++;
                    else {
                        differ++;
                        if (samples.size() < 6) samples.add(src.getBlock().getDescriptionId() + "->" + dst.getBlock().getDescriptionId());
                    }
                }
            }
        }
        Harness.noteNow("arms: print vs house (turned 180): same " + same + ", differ " + differ + " " + samples
            + " (expect 1 differing: the diamond block left out), diamond blocks in the print " + diamonds + " (expect 0)");
    }

    private static void inventory(ServerPlayer player) {
        String[] all = {"railgun", "laser_gun", "rail_slug", "focus_cell", "blueprinter", "matter_cartridge"};
        int slot = 27;
        for (String id : all) {
            Item item = item("oror_supreme_bosses:" + id);
            if (item != null) player.getInventory().setItem(slot++, new ItemStack(item));
        }
    }

    private ArmsTest() {
    }
}
