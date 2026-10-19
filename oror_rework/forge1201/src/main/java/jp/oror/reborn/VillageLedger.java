package jp.oror.reborn;

import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.GlobalPos;
import net.minecraft.core.HolderLookup.Provider;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedData.Factory;

public final class VillageLedger extends SavedData {
    public static final String ID = "oror_villages";
    public final Map<UUID, VillageLedger.Village> villages = new LinkedHashMap<>();

    public static VillageLedger get(ServerLevel level) {
        return (VillageLedger)level.getDataStorage().computeIfAbsent(new Factory(VillageLedger::new, VillageLedger::load), "oror_villages");
    }

    public VillageLedger.Village nearest(BlockPos p) {
        return this.villages.values().stream().filter(v -> v.contains(p)).min(Comparator.comparingDouble(v -> v.center.distSqr(p))).orElse(null);
    }

    public VillageLedger.Village register(BlockPos p) {
        VillageLedger.Village v = this.nearest(p);
        if (v == null) {
            v = new VillageLedger.Village(UUID.randomUUID(), p);
            this.villages.put(v.id, v);
            this.setDirty();
        }

        return v;
    }

    public static VillageLedger.Village of(Mob m) {
        if (m.level() instanceof ServerLevel sl) {
            VillageLedger var7 = get(sl);
            CompoundTag n = m.getPersistentData();
            if (n.hasUUID("OrorVillage")) {
                VillageLedger.Village old = var7.villages.get(n.getUUID("OrorVillage"));
                if (old != null) {
                    return old;
                }
            }

            BlockPos home = m.blockPosition();
            if (m instanceof Villager v) {
                Optional<GlobalPos> memory = v.getBrain().getMemory(MemoryModuleType.HOME);
                if (memory.isPresent() && memory.get().dimension().equals(sl.dimension())) {
                    home = memory.get().pos();
                }
            }

            VillageLedger.Village result = m instanceof Villager ? var7.register(home) : var7.nearest(home);
            if (result != null) {
                n.putUUID("OrorVillage", result.id);
            }

            return result;
        } else {
            return null;
        }
    }

    public int change(VillageLedger.Village v, UUID player, int amount, long now, String reason) {
        if (amount > 0) {
            long day = Math.floorDiv(now, 24000);
            if (day != v.day) {
                v.day = day;
                v.dailyGains.clear();
            }

            String key = player + ":" + reason;
            int used = v.dailyGains.getOrDefault(key, 0);
            amount = Math.min(amount, Math.max(0, 100 - used));
            v.dailyGains.put(key, used + amount);
        }

        int score = Math.clamp((long)(v.score(player) + amount), -1000, 1000);
        v.scores.put(player, score);
        this.setDirty();
        return score;
    }

    public static VillageLedger load(CompoundTag tag, Provider registries) {
        VillageLedger db = new VillageLedger();

        for (Tag raw : tag.getList("Villages", 10)) {
            CompoundTag n = (CompoundTag)raw;
            if (n.hasUUID("Id")) {
                VillageLedger.Village v = new VillageLedger.Village(n.getUUID("Id"), BlockPos.of(n.getLong("Center")));
                v.houses = Math.max(0, n.getInt("Houses"));
                v.day = n.getLong("Day");

                for (Tag entry : n.getList("Scores", 10)) {
                    CompoundTag s = (CompoundTag)entry;
                    if (s.hasUUID("Player")) {
                        v.scores.put(s.getUUID("Player"), Math.clamp((long)s.getInt("Score"), -1000, 1000));
                    }
                }

                for (Tag entryx : n.getList("Property", 10)) {
                    CompoundTag s = (CompoundTag)entryx;
                    if (s.hasUUID("Owner")) {
                        v.property.put(s.getLong("Pos"), s.getUUID("Owner"));
                    }
                }

                for (long pos : n.getLongArray("Communal")) {
                    v.communal.add(pos);
                }

                CompoundTag gains = n.getCompound("DailyGains");
                gains.getAllKeys().forEach(k -> v.dailyGains.put(k, gains.getInt(k)));
                db.villages.put(v.id, v);
            }
        }

        return db;
    }

    public CompoundTag save(CompoundTag tag, Provider registries) {
        ListTag list = new ListTag();

        for (VillageLedger.Village v : this.villages.values()) {
            CompoundTag n = new CompoundTag();
            n.putUUID("Id", v.id);
            n.putLong("Center", v.center.asLong());
            n.putInt("Houses", v.houses);
            n.putLong("Day", v.day);
            ListTag scores = new ListTag();
            v.scores.forEach((p, s) -> {
                CompoundTag a = new CompoundTag();
                a.putUUID("Player", p);
                a.putInt("Score", s);
                scores.add(a);
            });
            n.put("Scores", scores);
            ListTag owners = new ListTag();
            v.property.forEach((p, o) -> {
                CompoundTag a = new CompoundTag();
                a.putLong("Pos", p);
                a.putUUID("Owner", o);
                owners.add(a);
            });
            n.put("Property", owners);
            n.putLongArray("Communal", v.communal.stream().mapToLong(Long::longValue).toArray());
            CompoundTag gains = new CompoundTag();
            v.dailyGains.forEach(gains::putInt);
            n.put("DailyGains", gains);
            list.add(n);
        }

        tag.put("Villages", list);
        return tag;
    }

    public static final class Village {
        public final UUID id;
        public final BlockPos center;
        public final Map<UUID, Integer> scores = new HashMap<>();
        public final Map<Long, UUID> property = new HashMap<>();
        public final Set<Long> communal = new HashSet<>();
        public final Map<String, Integer> dailyGains = new HashMap<>();
        public long day = -1L;
        public int houses;

        Village(UUID id, BlockPos center) {
            this.id = id;
            this.center = center.immutable();
        }

        public int score(UUID player) {
            return this.scores.getOrDefault(player, 0);
        }

        public boolean contains(BlockPos p) {
            return this.center.distSqr(p) <= 4096.0;
        }
    }
}
