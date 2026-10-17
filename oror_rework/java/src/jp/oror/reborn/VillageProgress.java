package jp.oror.reborn;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup.Provider;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Container;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedData.Factory;

/**
 * How far each village has come (v0.17.15), kept beside VillageLedger: its name, the expeditions it has made, its nether
 * gate, the guns it has unlocked, its aircraft and trade flight, and goods on their way to its chests. Villagers away on
 * an expedition or a flight are kept here as saved entity data until they come back.
 */
public final class VillageProgress extends SavedData {
    public static final String ID = "oror_village_progress";
    private static final String[] HEAD = {"東", "西", "北", "南", "麦", "石", "杉", "樺", "鈴", "霧", "月", "楓", "柊", "灯", "朝", "風", "苔", "岩", "柳", "桜"};
    private static final String[] TAIL = {"の村", "ヶ原", "谷", "台", "の里", "沢", "野", "崎"};
    public final Map<UUID, Record> villages = new HashMap<>();

    public static VillageProgress get(ServerLevel level) {
        return (VillageProgress)level.getDataStorage().computeIfAbsent(new Factory(VillageProgress::new, (tag, registries) -> load((CompoundTag)tag, (Provider)registries)), ID);
    }

    public Record of(VillageLedger.Village village) {
        return this.villages.computeIfAbsent(village.id, k -> new Record(k));
    }

    /** One village's progress. */
    public static final class Record {
        public final UUID id;
        public int stage;
        public int dungeons;
        public int nethers;
        public int ends;
        public long nextTrip;
        public BlockPos gate;
        public boolean guns;
        public BlockPos gunTable;
        public int gunsMade;
        public BlockPos airfield;
        public UUID aircraft;
        public String aircraftType = "";
        public long nextFlight;
        public int flights;
        /** The expedition under way, or null. */
        public CompoundTag trip;
        /** The trade flight under way, or null. */
        public CompoundTag flight;
        /** Superb Warfare vehicles the village has built ("tank,jet,"), and the sortie under way. */
        public String vehicles = "";
        public CompoundTag sortie;
        public long nextSortie;
        public final ListTag deliveries = new ListTag();

        Record(UUID id) {
            this.id = id;
        }

        public String name() {
            int h = this.id.hashCode();
            return HEAD[Math.floorMod(h, HEAD.length)] + TAIL[Math.floorMod(h / 31, TAIL.length)];
        }
    }

    /** A UUID in a list entry. */
    public static CompoundTag uuid(UUID id) {
        CompoundTag t = new CompoundTag();
        t.putUUID("Id", id);
        return t;
    }

    // ------------------------------------------------------------------------------------- goods on their way
    /** Goods for the village's chests, put there when its villagers next look at their chests. */
    public void deliver(Record r, List<ItemStack> goods, Provider registries) {
        for (ItemStack st : goods) {
            if (!st.isEmpty()) {
                r.deliveries.add(st.save(registries));
            }
        }
        this.setDirty();
    }

    /** Put what is waiting into the chests, as far as they have room. */
    public void unload(Record r, List<Container> chests, Provider registries) {
        if (r.deliveries.isEmpty() || chests.isEmpty()) {
            return;
        }
        ListTag left = new ListTag();
        for (Tag t : r.deliveries) {
            ItemStack st = ItemStack.parseOptional(registries, (CompoundTag)t);
            for (Container box : chests) {
                if (st.isEmpty()) {
                    break;
                }
                st = VillageWork.insert(box, st);
            }
            if (!st.isEmpty()) {
                left.add(st.save(registries));
            }
        }
        r.deliveries.clear();
        r.deliveries.addAll(left);
        this.setDirty();
    }

    /** Tell the players near the village (within 256 blocks); far-reaching news goes to everyone in the level. */
    public static void announce(ServerLevel sl, VillageLedger.Village village, String text, boolean everyone) {
        Component line = Component.literal("【" + get(sl).of(village).name() + "】" + text);
        for (ServerPlayer p : sl.players()) {
            if (everyone || p.blockPosition().distSqr(village.center) < 65536.0) {
                p.sendSystemMessage(line);
            }
        }
    }

    // ------------------------------------------------------------------------------------- saving
    public static VillageProgress load(CompoundTag tag, Provider registries) {
        VillageProgress db = new VillageProgress();
        for (Tag raw : tag.getList("Villages", 10)) {
            CompoundTag n = (CompoundTag)raw;
            if (!n.hasUUID("Id")) {
                continue;
            }
            Record r = new Record(n.getUUID("Id"));
            r.stage = n.getInt("Stage");
            r.dungeons = n.getInt("Dungeons");
            r.nethers = n.getInt("Nethers");
            r.ends = n.getInt("Ends");
            r.nextTrip = n.getLong("NextTrip");
            r.gate = n.contains("Gate") ? BlockPos.of(n.getLong("Gate")) : null;
            r.guns = n.getBoolean("Guns");
            r.gunTable = n.contains("GunTable") ? BlockPos.of(n.getLong("GunTable")) : null;
            r.gunsMade = n.getInt("GunsMade");
            r.airfield = n.contains("Airfield") ? BlockPos.of(n.getLong("Airfield")) : null;
            r.aircraft = n.hasUUID("Aircraft") ? n.getUUID("Aircraft") : null;
            r.aircraftType = n.getString("AircraftType");
            r.nextFlight = n.getLong("NextFlight");
            r.flights = n.getInt("Flights");
            r.trip = n.contains("Trip", 10) ? n.getCompound("Trip") : null;
            r.flight = n.contains("Flight", 10) ? n.getCompound("Flight") : null;
            r.vehicles = n.getString("Vehicles");
            r.sortie = n.contains("Sortie", 10) ? n.getCompound("Sortie") : null;
            r.nextSortie = n.getLong("NextSortie");
            r.deliveries.addAll(n.getList("Deliveries", 10));
            db.villages.put(r.id, r);
        }
        return db;
    }

    public CompoundTag save(CompoundTag tag, Provider registries) {
        ListTag list = new ListTag();
        for (Record r : new ArrayList<>(this.villages.values())) {
            CompoundTag n = new CompoundTag();
            n.putUUID("Id", r.id);
            n.putInt("Stage", r.stage);
            n.putInt("Dungeons", r.dungeons);
            n.putInt("Nethers", r.nethers);
            n.putInt("Ends", r.ends);
            n.putLong("NextTrip", r.nextTrip);
            if (r.gate != null) {
                n.putLong("Gate", r.gate.asLong());
            }
            n.putBoolean("Guns", r.guns);
            if (r.gunTable != null) {
                n.putLong("GunTable", r.gunTable.asLong());
            }
            n.putInt("GunsMade", r.gunsMade);
            if (r.airfield != null) {
                n.putLong("Airfield", r.airfield.asLong());
            }
            if (r.aircraft != null) {
                n.putUUID("Aircraft", r.aircraft);
            }
            n.putString("AircraftType", r.aircraftType);
            n.putLong("NextFlight", r.nextFlight);
            n.putInt("Flights", r.flights);
            if (r.trip != null) {
                n.put("Trip", r.trip);
            }
            if (r.flight != null) {
                n.put("Flight", r.flight);
            }
            n.putString("Vehicles", r.vehicles);
            if (r.sortie != null) {
                n.put("Sortie", r.sortie);
            }
            n.putLong("NextSortie", r.nextSortie);
            ListTag goods = new ListTag();
            goods.addAll(r.deliveries);
            n.put("Deliveries", goods);
            list.add(n);
        }
        tag.put("Villages", list);
        return tag;
    }
}
