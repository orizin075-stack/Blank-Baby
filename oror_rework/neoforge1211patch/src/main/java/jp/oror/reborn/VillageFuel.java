package jp.oror.reborn;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import jp.oror.reborn.vehicle.Sbw;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (059g, the user: "エネルギーが切れそうになったら村にある木炭や石炭を持ってきて補充するように") The village's machines run on the
 * village's own fuel. Until now a village tank or jet was charged full from nothing at its motor pool (when it went out and
 * when it came home), and a trade aircraft's engine was given four coal from nothing.
 * <ul>
 * <li>A village vehicle is charged from the coal, charcoal and coal blocks in the village's communal chests
 * (VillageVehicleChargeMixin): a coal or a charcoal is a tenth of a tank's battery (a million), a coal block nine; what the
 * chests do not hold is not charged, and the village is told.</li>
 * <li>A trade aircraft's engine takes its four coal (or charcoal) from the chests (VillageFlightFuelMixin).</li>
 * <li>A village without fuel does not send them out: with under eight coal's worth no sortie (its tank would stand at its
 * pool with an empty battery), with under four no trade flight; it is put off for a while, and the village is told.</li>
 * </ul>
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class VillageFuel {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Village");
    /** A coal's or a charcoal's worth of charge; a coal block nine of it. */
    static final int COAL_FE = 1_000_000;
    static int charges, short_charges, burnt, flightsFuelled, deferred;
    private static final Map<UUID, Long> TOLD = new HashMap<>();

    private VillageFuel() {
    }

    /** Coal's worth (coal and charcoal 1, a coal block 9) in a village's communal chests. */
    static int stock(ServerLevel sl, UUID village) {
        VillageWork.Survey s = VillageWork.cached(village);
        if (s == null) {
            return 0;
        }
        int n = 0;
        for (BlockPos p : s.chests) {
            if (sl.isLoaded(p) && sl.getBlockEntity(p) instanceof Container c) {
                for (int i = 0; i < c.getContainerSize(); i++) {
                    ItemStack st = c.getItem(i);
                    n += st.is(Items.COAL) || st.is(Items.CHARCOAL) ? st.getCount() : st.is(Items.COAL_BLOCK) ? st.getCount() * 9 : 0;
                }
            }
        }
        return n;
    }

    /** Up to so many coal's worth out of the chests (coal and charcoal first, then blocks): what was taken. */
    static int take(ServerLevel sl, UUID village, int want) {
        VillageWork.Survey s = VillageWork.cached(village);
        if (s == null || want <= 0) {
            return 0;
        }
        int got = 0;
        for (int pass = 0; pass < 2 && got < want; pass++) {
            for (BlockPos p : s.chests) {
                if (got >= want || !sl.isLoaded(p) || !(sl.getBlockEntity(p) instanceof Container c)) {
                    continue;
                }
                for (int i = 0; i < c.getContainerSize() && got < want; i++) {
                    ItemStack st = c.getItem(i);
                    boolean loose = st.is(Items.COAL) || st.is(Items.CHARCOAL);
                    if (pass == 0 && loose) {
                        int n = Math.min(st.getCount(), want - got);
                        st.shrink(n);
                        got += n;
                        c.setChanged();
                    } else if (pass == 1 && st.is(Items.COAL_BLOCK)) {
                        int n = Math.min(st.getCount(), (want - got + 8) / 9);
                        st.shrink(n);
                        got += n * 9;
                        c.setChanged();
                    }
                }
            }
        }
        burnt += got;
        return got;
    }

    /** The village a machine of it belongs to: as marked when brought out, else the record that names it. */
    static UUID owner(ServerLevel sl, Entity v) {
        UUID o = VillageFlights.owner(v);
        if (o != null) {
            return o;
        }
        for (Map.Entry<UUID, VillageProgress.Record> e : VillageProgress.get(sl).villages.entrySet()) {
            VillageProgress.Record r = e.getValue();
            if (v.getUUID().equals(r.aircraft) || r.sortie != null && r.sortie.hasUUID("Vehicle") && v.getUUID().equals(r.sortie.getUUID("Vehicle"))) {
                return e.getKey();
            }
        }
        return null;
    }

    /** VillageVehicles.charge: the battery filled from the village's fuel. False to leave it to the old charging (no village). */
    public static boolean charge(Entity v) {
        if (!(v.level() instanceof ServerLevel sl)) {
            return false;
        }
        UUID village = owner(sl, v);
        if (village == null || !Boolean.TRUE.equals(Sbw.call(v, "hasEnergyStorage"))) {
            return false;
        }
        int max = Sbw.call(v, "getMaxEnergy") instanceof Number m ? m.intValue() : 0;
        int now = Sbw.call(v, "getEnergy") instanceof Number e ? e.intValue() : 0;
        long missing = (long) max - now;
        if (missing <= 0) {
            return true;
        }
        int want = (int) ((missing + COAL_FE - 1) / COAL_FE);
        int got = take(sl, village, want);
        long add = Math.min(missing, (long) got * COAL_FE);
        Sbw.call(v, "setEnergy", (int) (now + add));
        charges++;
        if (got < want) {
            short_charges++;
            tell(sl, village, "燃料（石炭・木炭）が足りず、" + v.getName().getString() + "を"
                + Math.round(100.0 * (now + add) / Math.max(1, max)) + "%までしか充電できませんでした");
        }
        return true;
    }

    /** VillageFlights.fuel: the engine's four coal from the village's chests. False to leave it to the old fuelling. */
    public static boolean fuel(Entity craft, String type) {
        if (!(craft.level() instanceof ServerLevel sl) || !(craft instanceof Container c)) {
            return false;
        }
        UUID village = owner(sl, craft);
        if (village == null) {
            return false;
        }
        int slot = "biplane".equals(type) ? 7 : 6;
        if (slot < c.getContainerSize() && c.getItem(slot).isEmpty()) {
            boolean charcoal = false;
            VillageWork.Survey s = VillageWork.cached(village);
            if (s != null) {
                for (BlockPos p : s.chests) {
                    if (sl.isLoaded(p) && sl.getBlockEntity(p) instanceof Container box) {
                        for (int i = 0; i < box.getContainerSize(); i++) {
                            if (box.getItem(i).is(Items.CHARCOAL)) {
                                charcoal = true;
                            }
                        }
                    }
                }
            }
            int got = take(sl, village, 4);
            if (got > 0) {
                c.setItem(slot, new ItemStack(charcoal ? Items.CHARCOAL : Items.COAL, Math.min(4, got)));
                flightsFuelled++;
            }
        }
        return true;
    }

    /** Every twenty seconds: a loaded village without fuel puts off its sorties and its trade flight. */
    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        ServerLevel sl = e.getServer().overworld();
        long now = sl.getGameTime();
        if (now % 400 != 211) {
            return;
        }
        try {
            VillageProgress progress = VillageProgress.get(sl);
            for (VillageLedger.Village v : List.copyOf(VillageLedger.get(sl).villages.values())) {
                VillageProgress.Record r = progress.villages.get(v.id);
                if (r != null && sl.isPositionEntityTicking(v.center) && VillageWork.cached(v.id) != null) {
                    review(sl, v, r, now);
                }
            }
        } catch (RuntimeException ex) {
            LOG.warn("VILLAGE-FUEL the fuel check failed", ex);
        }
    }

    /** A village without fuel puts off its sorties (under eight coal's worth) and its trade flight (under four). */
    static void review(ServerLevel sl, VillageLedger.Village v, VillageProgress.Record r, long now) {
        boolean vehicles = r.vehicles != null && !r.vehicles.isEmpty() && r.sortie == null;
        boolean aircraft = r.aircraftType != null && !r.aircraftType.isEmpty() && r.flight == null;
        if (!vehicles && !aircraft) {
            return;
        }
        int fuel = stock(sl, v.id);
        if (vehicles && fuel < 8 && r.nextSortie < now + 400) {
            r.nextSortie = now + 400;
            deferred++;
            tell(sl, v.id, "燃料（石炭・木炭）がなく、戦車や戦闘機を出せません");
        }
        if (aircraft && fuel < 4 && r.nextFlight < now + 2400) {
            r.nextFlight = now + 2400;
            deferred++;
            tell(sl, v.id, "燃料（石炭・木炭）がなく、交易飛行を見送りました");
        }
    }

    /** A village told, at most once in five minutes. */
    private static void tell(ServerLevel sl, UUID village, String msg) {
        long now = sl.getGameTime();
        Long last = TOLD.get(village);
        if (last != null && now - last < 6000) {
            return;
        }
        TOLD.put(village, now);
        VillageLedger.Village v = VillageLedger.get(sl).villages.get(village);
        if (v != null) {
            VillageProgress.announce(sl, v, msg, false);
        }
        LOG.info("VILLAGE-FUEL {}", msg);
    }

    public static String report() {
        return String.format(java.util.Locale.ROOT, "{\"charges\":%d,\"short\":%d,\"burnt\":%d,\"flightsFuelled\":%d,\"deferred\":%d}", charges, short_charges, burnt,
            flightsFuelled, deferred);
    }
}
