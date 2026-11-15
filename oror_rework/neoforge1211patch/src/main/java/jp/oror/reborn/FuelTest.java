package jp.oror.reborn;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import jp.oror.reborn.vehicle.RoyalPilots;
import jp.oror.reborn.vehicle.Sbw;
import jp.oror.reborn.vehicle.Supply;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (059g) CI check "fuel" (/oror fuel test, FUEL-RESULT) of the fuel the machines run on (VillageFuel, Supply.restock). On a
 * cleared green away from the capital:
 * <ul>
 * <li>a village whose chest holds six coal and a coal block: a tank of it, its battery empty, is charged from them (full,
 * the chest emptied); emptied again and charged again it gets nothing and the village is told; with no fuel left the
 * village puts off its sorties;</li>
 * <li>a kingdom's post: a charging station whose coal store is empty, a chest of coal, charcoal and coal blocks six blocks
 * off, a close-in gun standing at the station: its crew carry the fuel to the store.</li>
 * </ul>
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class FuelTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Village");
    public static volatile boolean resultLogged;

    private FuelTest() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("fuel").requires(s -> s.hasPermission(2))
            .then(Commands.literal("test").executes(c -> run(c.getSource())))));
    }

    private static int run(CommandSourceStack src) {
        ServerLevel level = src.getServer().overworld();
        List<ChunkPos> forced = new ArrayList<>();
        List<Entity> made = new ArrayList<>();
        StringBuilder out = new StringBuilder("FUEL-RESULT {\"present\":true");
        boolean pass = true;
        VillageLedger.Village village = null;
        try {
            BlockPos a = BlockPos.containing(src.getPosition()).offset(3200, 0, -3200);
            for (int dx = -2; dx <= 2; dx++) {
                for (int dz = -2; dz <= 2; dz++) {
                    ChunkPos p = new ChunkPos((a.getX() >> 4) + dx, (a.getZ() >> 4) + dz);
                    if (level.setChunkForced(p.x, p.z, true)) {
                        forced.add(p);
                    }
                }
            }
            a = new BlockPos(a.getX(), level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, a.getX(), a.getZ()), a.getZ());
            for (int x = -12; x <= 12; x++) {
                for (int z = -12; z <= 12; z++) {
                    level.setBlock(a.offset(x, -1, z), Blocks.GRASS_BLOCK.defaultBlockState(), 2);
                    for (int h = 0; h < 6; h++) {
                        level.setBlock(a.offset(x, h, z), Blocks.AIR.defaultBlockState(), 2);
                    }
                }
            }
            // --- the village's tank on the village's fuel
            boolean tankPresent = Sbw.present() && Sbw.has("m_1a_2");
            out.append(",\"tank\":").append(tankPresent);
            if (tankPresent) {
                level.setBlock(a, Blocks.BELL.defaultBlockState(), 3);
                BlockPos chestAt = a.offset(2, 0, -2);
                level.setBlock(chestAt, Blocks.CHEST.defaultBlockState(), 3);
                if (level.getBlockEntity(chestAt) instanceof ChestBlockEntity c) {
                    c.setItem(0, new ItemStack(Items.COAL, 6));
                    c.setItem(1, new ItemStack(Items.COAL_BLOCK, 1));
                    c.setItem(2, new ItemStack(Items.BREAD, 16));
                }
                village = VillageLedger.get(level).register(a);
                VillageProgress.Record rec = VillageProgress.get(level).of(village);
                VillageWork.survey(level, village);
                int before = VillageFuel.stock(level, village.id);
                Entity tank = BuiltInRegistries.ENTITY_TYPE.get(Sbw.id("m_1a_2")).create(level);
                if (tank != null) {
                    tank.moveTo(a.getX() + 6.5, a.getY(), a.getZ() + 6.5, 0F, 0F);
                    level.addFreshEntity(tank);
                    made.add(tank);
                    VillageFlights.mark(tank, village.id);
                    Sbw.call(tank, "setEnergy", 0);
                    int max = Sbw.call(tank, "getMaxEnergy") instanceof Number m ? m.intValue() : 0;
                    int shortBefore = VillageFuel.short_charges;
                    boolean handled = VillageFuel.charge(tank);
                    int e1 = Sbw.call(tank, "getEnergy") instanceof Number n ? n.intValue() : -1;
                    int after = VillageFuel.stock(level, village.id);
                    Sbw.call(tank, "setEnergy", 0);
                    VillageFuel.charge(tank);
                    int e2 = Sbw.call(tank, "getEnergy") instanceof Number n ? n.intValue() : -1;
                    boolean told = VillageFuel.short_charges > shortBefore;
                    rec.vehicles = "tank,";
                    rec.sortie = null;
                    rec.nextSortie = 0;
                    long now = level.getGameTime();
                    VillageFuel.review(level, village, rec, now);
                    boolean deferred = rec.nextSortie >= now + 400;
                    boolean ok = handled && max > 0 && e1 >= Math.min(max, before * VillageFuel.COAL_FE) - 1 && after < before && e2 == 0 && told && deferred;
                    pass &= ok;
                    out.append(String.format(Locale.ROOT, ",\"village\":{\"fuelBefore\":%d,\"handled\":%b,\"max\":%d,\"charged\":%d,\"fuelAfter\":%d,"
                        + "\"chargedEmpty\":%d,\"toldShort\":%b,\"sortieDeferred\":%b,\"ok\":%b}", before, handled, max, e1, after, e2, told, deferred, ok));
                }
            }
            // --- the kingdom's post: the crew fill the power plant's coal store
            BlockPos st = a.offset(-6, 0, 6);
            boolean station = Supply.placeStation(level, st, 0, 0);
            out.append(",\"station\":").append(station);
            if (station) {
                if (level.getBlockEntity(st.above(2)) instanceof Container store) {
                    store.clearContent();
                }
                BlockPos src2 = st.offset(6, 0, 0);
                level.setBlock(src2, Blocks.CHEST.defaultBlockState(), 3);
                int sourceBefore = 0;
                if (level.getBlockEntity(src2) instanceof ChestBlockEntity c) {
                    c.setItem(0, new ItemStack(Items.COAL, 64));
                    c.setItem(1, new ItemStack(Items.CHARCOAL, 16));
                    c.setItem(2, new ItemStack(Items.COAL_BLOCK, 8));
                    sourceBefore = 64 + 16 + 8 * 9;
                }
                Entity gun = RoyalPilots.deploy(level, Vec3.atBottomCenterOf(st.offset(2, 0, 0)), 0F, "hpj_11", 1, null);
                if (gun != null) {
                    made.add(gun);
                    made.addAll(gun.getPassengers());
                    int moved = Supply.restock(level, gun);
                    int stored = 0;
                    if (level.getBlockEntity(st.above(2)) instanceof Container store) {
                        for (int i = 0; i < store.getContainerSize(); i++) {
                            ItemStack s = store.getItem(i);
                            stored += s.is(Items.COAL) || s.is(Items.CHARCOAL) ? s.getCount() : s.is(Items.COAL_BLOCK) ? s.getCount() * 9 : 0;
                        }
                    }
                    boolean ok = moved > 0 && stored == moved && moved <= sourceBefore;
                    pass &= ok;
                    out.append(String.format(Locale.ROOT, ",\"post\":{\"sourceBefore\":%d,\"carried\":%d,\"inStore\":%d,\"ok\":%b}", sourceBefore, moved, stored, ok));
                } else {
                    out.append(",\"post\":\"no gun\"");
                }
            }
        } catch (RuntimeException ex) {
            LOG.warn("FUEL-TEST failed", ex);
            out.append(",\"error\":\"").append(ex.toString().replace('"', '\'')).append('"');
            pass = false;
        }
        out.append(",\"fuel\":").append(VillageFuel.report()).append(",\"pass\":").append(pass).append('}');
        LOG.info(out.toString());
        for (Entity e : made) {
            if (!e.isRemoved()) {
                e.discard();
            }
        }
        if (village != null) {
            VillageLedger.get(level).villages.remove(village.id);
            VillageProgress.get(level).villages.remove(village.id);
        }
        for (ChunkPos p : forced) {
            level.setChunkForced(p.x, p.z, false);
        }
        resultLogged = true;
        return 1;
    }
}
