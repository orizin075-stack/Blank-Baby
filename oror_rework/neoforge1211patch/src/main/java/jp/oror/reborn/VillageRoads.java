package jp.oror.reborn;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import jp.oror.reborn.citadel.CitadelSites;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.royal.RoyalRegistry;
import jp.oror.reborn.royal.RoyalRole;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Container;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.npc.VillagerProfession;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.entity.EntityLeaveLevelEvent;
import net.neoforged.neoforge.event.entity.living.LivingDeathEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (059g) The roads between the villages, the villagers' kingdoms and the royal capital (the user: "村同士の移動や王国をまたいでの
 * 移動や取引もできるように").
 *
 * <p>Until now a village's people left it only on an expedition (to a dungeon, the Nether, the End) or, from a town up,
 * in its trade airship; nobody walked from one village to another, and the capital's people never left its walls.
 * Now:</p>
 * <ul>
 * <li>Every village with three people or more sends out a trading party about twice a day while it is loaded: a trader
 * (one of its people with a trade, not one of its fighters or miners) and one or two of its strong villagers as escort
 * (six people or more, ten or more or a kingdom). It takes what its communal chests hold beyond 32 of a kind (eight stacks
 * at most; never emeralds, tools, weapons or armour) to another village or kingdom (the nearer the likelier, a kingdom
 * twice as likely) or to the royal capital.</li>
 * <li>A crowded village (twelve people or more) sends one of its people along to settle in a village five or more
 * smaller: he stays there and takes a bed and a job of the new village.</li>
 * <li>The party walks: out of the village along the straight road, its trader and escort by the village's own walking
 * (VillageAI), fighting and fleeing as any villager does. Where the ground is not loaded the journey goes on as saved
 * data at two blocks a second, and where the road comes into loaded ground again (a player near it) the party is there,
 * walking on: travellers are met on the road. They are not shown on water (they go round it out of sight) nor inside the
 * kingdom's walls (they pass through its gates).</li>
 * <li>Arrived, the goods go into the other village's chests (or are delivered there when it is next loaded, as the trade
 * flights' are); it pays in emeralds by the goods' worth and adds some of its own surplus (or what its land is known for),
 * a tenth taken as a toll where the road crossed into another realm (another kingdom, or the royal capital's).
 * The capital pays a little more and gives the kingdom's own wares. The party walks home with the emeralds and the wares,
 * which go into its own village's chests.</li>
 * <li>Crossing from one realm to another (a kingdom's land is 640 blocks round it; the royal capital's its 1,280-block
 * square) is told to the players who see it.</li>
 * <li>The royal capital sends the king's merchant (with two of its guards) out of its gates to a village about once a
 * day and a half while a player is in the kingdom: he brings the kingdom's wares and buys with them what the village can
 * pay.</li>
 * <li>A trader killed on the road drops what he carries (the goods out, or the emeralds and wares home).</li>
 * </ul>
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class VillageRoads {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Village");
    /** A traveller's journey (persistent data), and which time the party was put into the world (a copy left in saved ground is refused). */
    static final String KEY = "OrorRoad", SEQ = "OrorRoadSeq";
    /** The royal capital as a place on the roads. */
    static final UUID CAPITAL = new UUID(0x0E0E0E0E0E0E4E0EL, 0x8E0E0E0E0E0E0E01L);
    /** Blocks a tick on the road out of sight (two a second), and the CI check's speed-up. */
    static final double SPEED = 0.1;
    static double speedup = 1.0;
    static final long INTERVAL = 12000, ROYAL_INTERVAL = 18000;
    static final int KEEP = 32, STACKS = 8, REALM = 640;
    static int departed, arrivedOut, cameHome, shown, packed, crossings, settled, robbed, errors;

    private VillageRoads() {
    }

    /** A party on the road. Leg 0 goes from the start to the goal, leg 1 back. */
    static final class Journey {
        UUID id, from, to, lead, migrant;
        BlockPos fromPos, toPos;
        String fromName = "", toName = "", realm = "", kind = "trade", state = "walking";
        int leg, seq, emeralds, toll, payment, shownTimes;
        long legStart, seenAt, stuckAt;
        double done, stuckFrom;
        boolean crossed;
        final ListTag packed = new ListTag();
        final List<UUID> walking = new ArrayList<>();
        ListTag cargo = new ListTag(), wares = new ListTag();

        Vec3 a() {
            return Vec3.atBottomCenterOf(leg == 0 ? fromPos : toPos);
        }

        Vec3 b() {
            return Vec3.atBottomCenterOf(leg == 0 ? toPos : fromPos);
        }

        double length() {
            return b().subtract(a()).horizontalDistance();
        }

        Vec3 dir() {
            Vec3 d = b().subtract(a()).multiply(1, 0, 1);
            return d.lengthSqr() < 1 ? new Vec3(1, 0, 0) : d.normalize();
        }

        Vec3 at(double along) {
            return a().add(dir().scale(along));
        }

        double along(Vec3 p) {
            return p.subtract(a()).multiply(1, 0, 1).dot(dir());
        }

        double roadDone(long now) {
            return Math.min(length(), done + Math.max(0, now - legStart) * SPEED * speedup);
        }

        boolean holds(UUID u) {
            for (Tag t : packed) {
                if (t instanceof CompoundTag c && c.hasUUID("UUID") && c.getUUID("UUID").equals(u)) {
                    return true;
                }
            }
            return false;
        }

        CompoundTag save() {
            CompoundTag t = new CompoundTag();
            t.putUUID("Id", id);
            t.putUUID("From", from);
            t.putUUID("To", to);
            if (lead != null) {
                t.putUUID("Lead", lead);
            }
            if (migrant != null) {
                t.putUUID("Migrant", migrant);
            }
            t.putLong("FromPos", fromPos.asLong());
            t.putLong("ToPos", toPos.asLong());
            t.putString("FromName", fromName);
            t.putString("ToName", toName);
            t.putString("Realm", realm);
            t.putString("Kind", kind);
            t.putString("State", state);
            t.putInt("Leg", leg);
            t.putInt("Seq", seq);
            t.putInt("Emeralds", emeralds);
            t.putInt("Toll", toll);
            t.putInt("Payment", payment);
            t.putLong("LegStart", legStart);
            t.putLong("SeenAt", seenAt);
            t.putDouble("Done", done);
            t.putBoolean("Crossed", crossed);
            t.put("Packed", packed.copy());
            ListTag w = new ListTag();
            for (UUID u : walking) {
                CompoundTag c = new CompoundTag();
                c.putUUID("U", u);
                w.add(c);
            }
            t.put("Walking", w);
            t.put("Cargo", cargo.copy());
            t.put("Wares", wares.copy());
            return t;
        }

        static Journey load(CompoundTag t) {
            Journey j = new Journey();
            j.id = t.getUUID("Id");
            j.from = t.getUUID("From");
            j.to = t.getUUID("To");
            j.lead = t.hasUUID("Lead") ? t.getUUID("Lead") : null;
            j.migrant = t.hasUUID("Migrant") ? t.getUUID("Migrant") : null;
            j.fromPos = BlockPos.of(t.getLong("FromPos"));
            j.toPos = BlockPos.of(t.getLong("ToPos"));
            j.fromName = t.getString("FromName");
            j.toName = t.getString("ToName");
            j.realm = t.getString("Realm");
            j.kind = t.getString("Kind");
            j.state = t.getString("State");
            j.leg = t.getInt("Leg");
            j.seq = t.getInt("Seq");
            j.emeralds = t.getInt("Emeralds");
            j.toll = t.getInt("Toll");
            j.payment = t.getInt("Payment");
            j.legStart = t.getLong("LegStart");
            j.seenAt = t.getLong("SeenAt");
            j.done = t.getDouble("Done");
            j.crossed = t.getBoolean("Crossed");
            j.packed.addAll(t.getList("Packed", Tag.TAG_COMPOUND));
            for (Tag w : t.getList("Walking", Tag.TAG_COMPOUND)) {
                if (w instanceof CompoundTag c && c.hasUUID("U")) {
                    j.walking.add(c.getUUID("U"));
                }
            }
            j.cargo = t.getList("Cargo", Tag.TAG_COMPOUND);
            j.wares = t.getList("Wares", Tag.TAG_COMPOUND);
            return j;
        }
    }

    /** The roads of a world: the parties on them, when each village sends its next, and the settlers waiting for their new village to be loaded. */
    static final class Roads extends SavedData {
        static final Factory<Roads> FACTORY = new Factory<>(Roads::new, Roads::load, null);
        final Map<UUID, Journey> journeys = new LinkedHashMap<>();
        final Map<UUID, Long> next = new HashMap<>();
        final ListTag settlers = new ListTag();

        static Roads of(ServerLevel level) {
            return level.getDataStorage().computeIfAbsent(FACTORY, "oror_village_roads");
        }

        static Roads load(CompoundTag tag, HolderLookup.Provider registries) {
            Roads r = new Roads();
            for (Tag t : tag.getList("Journeys", Tag.TAG_COMPOUND)) {
                try {
                    Journey j = Journey.load((CompoundTag) t);
                    r.journeys.put(j.id, j);
                } catch (RuntimeException ex) {
                    LOG.warn("ROAD a journey could not be read: {}", ex.toString());
                }
            }
            for (Tag t : tag.getList("Next", Tag.TAG_COMPOUND)) {
                CompoundTag c = (CompoundTag) t;
                if (c.hasUUID("V")) {
                    r.next.put(c.getUUID("V"), c.getLong("At"));
                }
            }
            r.settlers.addAll(tag.getList("Settlers", Tag.TAG_COMPOUND));
            return r;
        }

        @Override
        public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
            ListTag js = new ListTag();
            for (Journey j : journeys.values()) {
                js.add(j.save());
            }
            tag.put("Journeys", js);
            ListTag n = new ListTag();
            for (Map.Entry<UUID, Long> e : next.entrySet()) {
                CompoundTag c = new CompoundTag();
                c.putUUID("V", e.getKey());
                c.putLong("At", e.getValue());
                n.add(c);
            }
            tag.put("Next", n);
            tag.put("Settlers", settlers.copy());
            return tag;
        }
    }

    /** Where a party goes. */
    record Target(UUID id, BlockPos pos, String name, boolean capital) {
    }

    // ------------------------------------------------------------------------------------------------------------ the tick

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        ServerLevel level = e.getServer().overworld();
        long now = level.getGameTime();
        if (!GONE.isEmpty()) {
            for (UUID u : List.copyOf(GONE)) {
                Entity m = level.getEntity(u);
                if (m != null && !m.isRemoved()) {
                    m.discard();
                }
            }
            GONE.clear();
        }
        if (now % 20 != 11) {
            return;
        }
        try {
            Roads roads = Roads.of(level);
            if (now % 400 == 11) {
                departures(level, roads, now);
            }
            for (Journey j : List.copyOf(roads.journeys.values())) {
                travel(level, roads, j, now);
            }
            if (!roads.settlers.isEmpty()) {
                settle(level, roads);
            }
        } catch (RuntimeException ex) {
            if (errors++ < 5) {
                LOG.warn("ROAD the roads' tick failed", ex);
            }
        }
    }

    private static void departures(ServerLevel level, Roads roads, long now) {
        VillageLedger ledger = VillageLedger.get(level);
        VillageProgress progress = VillageProgress.get(level);
        Set<UUID> busy = new HashSet<>();
        for (Journey j : roads.journeys.values()) {
            busy.add(j.from);
        }
        for (VillageLedger.Village v : List.copyOf(ledger.villages.values())) {
            if (busy.contains(v.id) || !ticking(level, v.center)) {
                continue;
            }
            Long at = roads.next.get(v.id);
            if (at == null) {
                // a village first seen: its first party within two to ten minutes
                roads.next.put(v.id, now + 2400 + level.random.nextInt(9600));
                roads.setDirty();
                continue;
            }
            if (now < at) {
                continue;
            }
            roads.next.put(v.id, now + (long) (INTERVAL * (0.7 + 0.6 * level.random.nextDouble())));
            roads.setDirty();
            if (plan(level, roads, ledger, progress, v, now) != null) {
                busy.add(v.id);
            }
        }
        royal(level, roads, ledger, progress, now, busy);
    }

    /** A village's party, if it has the people and something to sell (or someone to send to a new home). */
    private static Journey plan(ServerLevel level, Roads roads, VillageLedger ledger, VillageProgress progress, VillageLedger.Village v, long now) {
        VillageWork.Survey s = VillageWork.survey(level, v);
        if (s == null || s.population < 3) {
            return null;
        }
        Target dest = destination(level, ledger, progress, v);
        if (dest == null) {
            return null;
        }
        List<Villager> folk = level.getEntitiesOfClass(Villager.class, new AABB(v.center).inflate(64, 24, 64), x -> free(x) && VillageLedger.of(x) == v);
        if (folk.size() < 3) {
            return null;
        }
        List<Mob> party = new ArrayList<>();
        Villager trader = null;
        for (Villager x : folk) {
            if (!VillageAI.strong(x) && !VillagerIndustry.miner(x) && traded(x) && (trader == null || x.getVillagerXp() > trader.getVillagerXp())) {
                trader = x;
            }
        }
        if (trader == null) {
            for (Villager x : folk) {
                if (!VillageAI.strong(x)) {
                    trader = x;
                    break;
                }
            }
        }
        if (trader == null) {
            return null;
        }
        party.add(trader);
        VillageProgress.Record rec = progress.of(v);
        int escorts = s.population >= 10 || rec.kingdom ? 2 : s.population >= 6 ? 1 : 0;
        for (Villager x : folk) {
            if (escorts > 0 && x != trader && VillageAI.strong(x) && party.size() < folk.size() / 3 + 1) {
                party.add(x);
                escorts--;
            }
        }
        Villager migrant = null;
        if (s.population >= 12 && !dest.capital()) {
            VillageWork.Survey there = VillageWork.cached(dest.id());
            if (there == null || there.population + 5 <= s.population) {
                for (Villager x : folk) {
                    if (!party.contains(x) && !VillageAI.strong(x) && !VillagerIndustry.miner(x)) {
                        migrant = x;
                        break;
                    }
                }
            }
        }
        List<ItemStack> cargo = take(level, s.chests, STACKS, Double.MAX_VALUE);
        if (cargo.isEmpty() && migrant == null) {
            return null;
        }
        if (migrant != null) {
            party.add(migrant);
        }
        Journey j = dispatch(level, roads, v.id, v.center, rec.name(), dest, party, cargo, now, "trade");
        j.migrant = migrant == null ? null : migrant.getUUID();
        announce(level, v, "【" + plain(j.fromName) + "】の行商隊（" + party.size() + "人）が【" + plain(j.toName) + "】へ出発しました"
            + (cargo.isEmpty() ? "" : "　荷：" + describe(cargo)) + (j.crossed ? "　（国境を越える旅です）" : "")
            + (migrant != null ? "　" + migrant.getName().getString() + "は向こうに移り住みます" : ""));
        return j;
    }

    /**
     * A party set on its road: its members marked as travellers (and walking, while they are in the world), the goods
     * it carries, the realm it sets out from. Used by plan, by the royal merchant and by the CI check.
     */
    static Journey dispatch(ServerLevel level, Roads roads, UUID from, BlockPos fromPos, String fromName, Target dest, List<? extends Entity> party,
                            List<ItemStack> cargo, long now, String kind) {
        Journey j = new Journey();
        j.id = UUID.randomUUID();
        j.from = from;
        j.to = dest.id();
        j.fromPos = fromPos;
        j.toPos = dest.pos();
        j.fromName = fromName;
        j.toName = dest.name();
        j.kind = kind;
        j.legStart = now;
        j.seenAt = now;
        j.stuckAt = now;
        j.seq = 1;
        j.realm = realm(level, fromPos);
        j.crossed = !j.realm.equals(realm(level, dest.pos()));
        j.cargo = save(level, cargo);
        j.state = "walking";
        for (Entity m : party) {
            if (j.lead == null) {
                j.lead = m.getUUID();
            }
            m.getPersistentData().putUUID(KEY, j.id);
            m.getPersistentData().putInt(SEQ, j.seq);
            if (level.getEntity(m.getUUID()) == m) {
                j.walking.add(m.getUUID());
            } else {
                CompoundTag t = new CompoundTag();
                if (m.saveAsPassenger(t)) {
                    j.packed.add(t);
                }
            }
        }
        if (j.walking.isEmpty()) {
            j.state = "road";
        }
        roads.journeys.put(j.id, j);
        roads.setDirty();
        departed++;
        LOG.info(String.format(Locale.ROOT, "ROAD-DEPART {\"from\":\"%s\",\"to\":\"%s\",\"kind\":\"%s\",\"party\":%d,\"cargo\":%d,\"km\":%.2f,\"crossed\":%b}",
            plain(j.fromName), plain(j.toName), kind, party.size(), cargo.size(), j.length() / 1000.0, j.crossed));
        return j;
    }

    /** Another village or kingdom to go to (the nearer the likelier, a kingdom twice as likely), or the royal capital. */
    private static Target destination(ServerLevel level, VillageLedger ledger, VillageProgress progress, VillageLedger.Village from) {
        List<Target> options = new ArrayList<>();
        List<Double> weights = new ArrayList<>();
        for (VillageLedger.Village o : ledger.villages.values()) {
            if (o == from) {
                continue;
            }
            double d = Math.sqrt(o.center.distSqr(from.center));
            if (d < 64 || d > 2400) {
                continue;
            }
            VillageProgress.Record r = progress.of(o);
            options.add(new Target(o.id, o.center, r.name(), false));
            weights.add((r.kingdom ? 2.0 : 1.0) / (1.0 + d / 400.0));
        }
        CitadelSites.Site cap = CitadelSites.capital();
        if (cap != null) {
            double d = Math.sqrt(cap.center().distSqr(from.center));
            if (d < 3000) {
                options.add(new Target(CAPITAL, cap.center(), "王都", true));
                weights.add(2.0 / (1.0 + d / 600.0));
            }
        }
        double sum = 0;
        for (double w : weights) {
            sum += w;
        }
        double pick = level.random.nextDouble() * sum;
        for (int i = 0; i < options.size(); i++) {
            pick -= weights.get(i);
            if (pick <= 0) {
                return options.get(i);
            }
        }
        return options.isEmpty() ? null : options.get(options.size() - 1);
    }

    /** One of the village's people free to go: grown, about, not asleep, on no other errand. */
    private static boolean free(Villager x) {
        CompoundTag d = x.getPersistentData();
        return x.isAlive() && !x.isBaby() && !x.isNoAi() && !x.isPassenger() && !x.isSleeping() && !d.hasUUID(KEY) && !d.getBoolean("OrorWanderer")
            && !d.contains("OrorParty") && !d.contains("OrorCaravan") && !d.contains("OrorHunter") && !d.contains("OrorVillageCraft");
    }

    private static boolean traded(Villager x) {
        VillagerProfession p = x.getVillagerData().getProfession();
        return p != VillagerProfession.NONE && p != VillagerProfession.NITWIT;
    }

    // --------------------------------------------------------------------------------------------------------- on the road

    private static void travel(ServerLevel level, Roads roads, Journey j, long now) {
        switch (j.state) {
            case "walking" -> walking(level, roads, j, now);
            case "road" -> road(level, roads, j, now);
            case "home" -> home(level, roads, j);
            default -> end(roads, j);
        }
    }

    /** In the world: packed away where the ground stops ticking (or at the kingdom's walls), moved on when stuck, arrived at the end. */
    private static void walking(ServerLevel level, Roads roads, Journey j, long now) {
        List<Entity> here = new ArrayList<>();
        for (UUID u : List.copyOf(j.walking)) {
            Entity m = level.getEntity(u);
            if (m != null && m.isAlive()) {
                here.add(m);
            }
        }
        if (here.isEmpty()) {
            if (j.walking.isEmpty()) {
                if (j.packed.isEmpty()) {
                    lost(level, roads, j);
                } else {
                    toRoad(j, now, j.done);
                    roads.setDirty();
                }
            }
            return;                                // in ground not loaded just now (a restart): they wait there
        }
        j.seenAt = now;
        Entity lead = here.get(0);
        for (Entity m : here) {
            if (m.getUUID().equals(j.lead)) {
                lead = m;
            }
        }
        double along = j.along(lead.position());
        for (Entity m : here) {
            BlockPos b = m.blockPosition();
            if (!ticking(level, b) || inKingdom(b)) {
                pack(j, m);
            }
        }
        if (j.walking.isEmpty()) {
            toRoad(j, now, along);
            roads.setDirty();
            return;
        }
        if (along >= j.length() - 16) {
            arrive(level, roads, j, now, true);
            return;
        }
        if (along > j.stuckFrom + 3) {
            j.stuckFrom = along;
            j.stuckAt = now;
        } else if (now - j.stuckAt > 600) {
            // a wall, a ravine, water: the party goes round it (a dozen blocks on along the road)
            Vec3 on = j.at(Math.min(j.length(), along + 12));
            BlockPos top = surface(level, on);
            if (top != null) {
                for (Entity m : here) {
                    m.teleportTo(top.getX() + 0.5, top.getY(), top.getZ() + 0.5);
                }
            }
            j.stuckFrom = along + 12;
            j.stuckAt = now;
        }
        Vec3 goal = j.at(Math.min(j.length(), Math.max(0, along) + 16));
        BlockPos top = surface(level, goal);
        for (Entity m : here) {
            if (m instanceof Mob mob && !(m instanceof Villager) && mob.getTarget() == null && top != null) {
                mob.getNavigation().moveTo(top.getX() + 0.5, top.getY(), top.getZ() + 0.5, 1.0);
            }
        }
        realmCheck(level, j, lead.blockPosition(), true);
    }

    /** Out of sight: on along the road; in the world again where the road is in loaded ground; arrived at its end. */
    private static void road(ServerLevel level, Roads roads, Journey j, long now) {
        double along = j.roadDone(now);
        if (along >= j.length() - 1) {
            arrive(level, roads, j, now, false);
            return;
        }
        Vec3 p = j.at(along);
        BlockPos b = BlockPos.containing(p);
        realmCheck(level, j, b, false);
        if (!j.packed.isEmpty() && showable(level, b)) {
            unpack(level, roads, j, p, now, along);
        }
    }

    /** Back at a village not loaded: the party waits on the road outside until it is, then walks in. */
    private static void home(ServerLevel level, Roads roads, Journey j) {
        VillageLedger.Village v = VillageLedger.get(level).villages.get(j.from);
        BlockPos c = v != null ? v.center : j.fromPos;
        if (!ticking(level, c)) {
            return;
        }
        int i = 0;
        for (Tag t : j.packed) {
            Entity m = restore(level, (CompoundTag) t, Vec3.atBottomCenterOf(c).add((i % 3) - 1, 0, (i / 3) - 1), true);
            if (m != null) {
                release(m);
                level.addFreshEntity(m);
            }
            i++;
        }
        j.packed.clear();
        LOG.info("ROAD-HOME {\"from\":\"{}\",\"members\":{}}", plain(j.fromName), i);
        end(roads, j);
    }

    // ----------------------------------------------------------------------------------------------------- arrival, trade

    private static void arrive(ServerLevel level, Roads roads, Journey j, long now, boolean seen) {
        if (j.leg == 0) {
            if ("royal".equals(j.kind)) {
                royalTrade(level, j, seen);
            } else {
                trade(level, j, seen);
            }
            migrate(level, roads, j, seen);
            arrivedOut++;
            j.leg = 1;
            j.done = 0;
            j.legStart = now;
            j.stuckFrom = 0;
            j.stuckAt = now;
            if (!seen) {
                j.state = "road";
            }
            roads.setDirty();
            return;
        }
        // home
        if ("royal".equals(j.kind)) {
            // the king's merchant back at the gates: into the capital
            for (UUID u : List.copyOf(j.walking)) {
                Entity m = level.getEntity(u);
                if (m != null) {
                    m.discard();
                }
            }
            end(roads, j);
            return;
        }
        homecoming(level, j, seen);
        cameHome++;
        if (seen) {
            for (UUID u : List.copyOf(j.walking)) {
                Entity m = level.getEntity(u);
                if (m != null) {
                    release(m);
                }
            }
            j.walking.clear();
            if (j.packed.isEmpty()) {
                end(roads, j);
                return;
            }
        }
        j.state = "home";
        roads.setDirty();
    }

    /** The goods into the other village's stores, paid for in emeralds and its own surplus (a tenth off across a border). */
    private static void trade(ServerLevel level, Journey j, boolean seen) {
        List<ItemStack> goods = stacks(level, j.cargo);
        boolean capital = CAPITAL.equals(j.to);
        double worth = worth(goods);
        int pay = goods.isEmpty() ? 0 : (int) Math.max(1, Math.round(worth * (capital ? 1.15 : 1.0)));
        int toll = j.crossed && pay > 0 ? Math.max(1, pay / 10) : 0;
        pay = Math.min(pay - toll, 320);
        VillageLedger.Village dest = capital ? null : VillageLedger.get(level).villages.get(j.to);
        if (dest != null && !goods.isEmpty()) {
            List<ItemStack> left = seen ? store(level, dest, goods) : goods;
            if (!left.isEmpty()) {
                VillageProgress.get(level).deliver(VillageProgress.get(level).of(dest), left, level.registryAccess());
            }
        }
        List<ItemStack> back = new ArrayList<>();
        double budget = pay * 0.5;
        if (dest != null && seen) {
            VillageWork.Survey there = VillageWork.cached(dest.id);
            if (there != null) {
                back.addAll(take(level, there.chests, 3, budget));
            }
        }
        if (back.isEmpty() && budget >= 1) {
            back.addAll(known(level, j.toPos, capital, budget));
        }
        int emeralds = Math.max(0, pay - (int) Math.round(worth(back)));
        j.wares = save(level, back);
        j.emeralds = emeralds;
        j.toll = toll;
        j.payment = pay;
        j.cargo = new ListTag();
        String msg = "【" + plain(j.fromName) + "】の行商隊が到着し、取引しました　納品：" + describe(goods) + "　支払い：エメラルド×" + emeralds
            + (back.isEmpty() ? "" : "、" + describe(back)) + (toll > 0 ? "　（関税 エメラルド×" + toll + "）" : "");
        if (dest != null) {
            announce(level, dest, msg);
        } else {
            capitalSays(level, msg);
        }
        LOG.info(String.format(Locale.ROOT, "ROAD-ARRIVE {\"from\":\"%s\",\"to\":\"%s\",\"seen\":%b,\"goods\":%d,\"worth\":%.1f,\"emeralds\":%d,\"wares\":%d,\"toll\":%d}",
            plain(j.fromName), plain(j.toName), seen, goods.size(), worth, emeralds, back.size(), toll));
    }

    /** The king's merchant at a village: the kingdom's wares into its stores, and what it can pay for them, if he is seen there. */
    private static void royalTrade(ServerLevel level, Journey j, boolean seen) {
        List<ItemStack> goods = stacks(level, j.cargo);
        VillageLedger.Village dest = VillageLedger.get(level).villages.get(j.to);
        if (dest == null) {
            return;
        }
        List<ItemStack> left = seen ? store(level, dest, goods) : goods;
        if (!left.isEmpty()) {
            VillageProgress.get(level).deliver(VillageProgress.get(level).of(dest), left, level.registryAccess());
        }
        int paid = 0;
        if (seen) {
            VillageWork.Survey there = VillageWork.cached(dest.id);
            int want = (int) Math.round(worth(goods));
            if (there != null) {
                for (BlockPos p : there.chests) {
                    if (level.getBlockEntity(p) instanceof Container c) {
                        for (int i = 0; i < c.getContainerSize() && paid < want; i++) {
                            ItemStack s = c.getItem(i);
                            if (s.is(Items.EMERALD)) {
                                int n = Math.min(s.getCount(), want - paid);
                                s.shrink(n);
                                paid += n;
                                c.setChanged();
                            }
                        }
                    }
                }
            }
        }
        j.emeralds = paid;
        j.cargo = new ListTag();
        announce(level, dest, "王都の御用商人が到着し、王国の品を納めました：" + describe(goods) + (paid > 0 ? "　代金：エメラルド×" + paid : ""));
        LOG.info("ROAD-ROYAL {\"to\":\"{}\",\"seen\":{},\"goods\":{},\"paid\":{}}", plain(j.toName), seen, goods.size(), paid);
    }

    /** The settler stays: a villager of the new village, its bed and job to find. */
    private static void migrate(ServerLevel level, Roads roads, Journey j, boolean seen) {
        if (j.migrant == null) {
            return;
        }
        UUID u = j.migrant;
        j.migrant = null;
        if (seen && level.getEntity(u) instanceof Villager v) {
            j.walking.remove(u);
            newcomer(v, j.to);
            settled++;
            announceTo(level, j.to, v.getName().getString() + "が【" + plain(j.fromName) + "】から移り住みました");
            return;
        }
        for (int i = 0; i < j.packed.size(); i++) {
            if (j.packed.get(i) instanceof CompoundTag c && c.hasUUID("UUID") && c.getUUID("UUID").equals(u)) {
                CompoundTag s = new CompoundTag();
                s.putUUID("Village", j.to);
                s.putString("From", j.fromName);
                s.put("Entity", c.copy());
                roads.settlers.add(s);
                j.packed.remove(i);
                roads.setDirty();
                return;
            }
        }
    }

    /** Settlers whose new village is loaded now walk into it. */
    private static void settle(ServerLevel level, Roads roads) {
        for (int i = roads.settlers.size() - 1; i >= 0; i--) {
            CompoundTag s = roads.settlers.getCompound(i);
            VillageLedger.Village v = s.hasUUID("Village") ? VillageLedger.get(level).villages.get(s.getUUID("Village")) : null;
            if (v == null) {
                roads.settlers.remove(i);
                roads.setDirty();
                continue;
            }
            if (!ticking(level, v.center)) {
                continue;
            }
            Entity m = restore(level, s.getCompound("Entity"), Vec3.atBottomCenterOf(v.center).add(1, 0, 1), true);
            if (m instanceof Villager vi) {
                newcomer(vi, v.id);
                level.addFreshEntity(vi);
                settled++;
                announce(level, v, vi.getName().getString() + "が【" + plain(s.getString("From")) + "】から移り住みました");
            }
            roads.settlers.remove(i);
            roads.setDirty();
        }
    }

    private static void newcomer(Villager v, UUID village) {
        release(v);
        v.getPersistentData().putUUID("OrorVillage", village);
        v.getBrain().eraseMemory(MemoryModuleType.HOME);
        v.getBrain().eraseMemory(MemoryModuleType.JOB_SITE);
        v.getBrain().eraseMemory(MemoryModuleType.POTENTIAL_JOB_SITE);
        v.getBrain().eraseMemory(MemoryModuleType.MEETING_POINT);
    }

    /** The emeralds and wares into the home village's stores. */
    private static void homecoming(ServerLevel level, Journey j, boolean seen) {
        List<ItemStack> goods = stacks(level, j.wares);
        int e = j.emeralds;
        while (e > 0) {
            int n = Math.min(64, e);
            goods.add(new ItemStack(Items.EMERALD, n));
            e -= n;
        }
        j.wares = new ListTag();
        j.emeralds = 0;
        VillageLedger.Village home = VillageLedger.get(level).villages.get(j.from);
        if (home == null || goods.isEmpty()) {
            return;
        }
        List<ItemStack> left = seen ? store(level, home, goods) : goods;
        if (!left.isEmpty()) {
            VillageProgress.get(level).deliver(VillageProgress.get(level).of(home), left, level.registryAccess());
        }
        announce(level, home, "【" + plain(j.fromName) + "】の行商隊が【" + plain(j.toName) + "】から戻りました　持ち帰り：" + describe(goods));
        LOG.info("ROAD-RETURN {\"from\":\"{}\",\"to\":\"{}\",\"seen\":{},\"goods\":{}}", plain(j.fromName), plain(j.toName), seen, goods.size());
    }

    // ------------------------------------------------------------------------------------------------- the king's merchant

    private static void royal(ServerLevel level, Roads roads, VillageLedger ledger, VillageProgress progress, long now, Set<UUID> busy) {
        CitadelSites.Site cap = CitadelSites.capital();
        if (cap == null || busy.contains(CAPITAL)) {
            return;
        }
        boolean someone = false;
        for (ServerPlayer p : level.players()) {
            someone |= cap.contains(p.chunkPosition().x, p.chunkPosition().z, 4);
        }
        if (!someone) {
            return;
        }
        Long at = roads.next.get(CAPITAL);
        if (at == null || now < at) {
            if (at == null) {
                roads.next.put(CAPITAL, now + 3600 + level.random.nextInt(6000));
                roads.setDirty();
            }
            return;
        }
        roads.next.put(CAPITAL, now + (long) (ROYAL_INTERVAL * (0.7 + 0.6 * level.random.nextDouble())));
        roads.setDirty();
        BlockPos c = cap.center();
        VillageLedger.Village dest = null;
        double best = Double.MAX_VALUE;
        for (VillageLedger.Village v : ledger.villages.values()) {
            double d = Math.sqrt(v.center.distSqr(c));
            double score = d * (0.6 + 0.8 * level.random.nextDouble());
            if (d < 2600 && score < best) {
                best = score;
                dest = v;
            }
        }
        if (dest == null) {
            return;
        }
        Vec3 dir = Vec3.atBottomCenterOf(dest.center).subtract(Vec3.atBottomCenterOf(c)).multiply(1, 0, 1);
        dir = dir.lengthSqr() < 1 ? new Vec3(1, 0, 0) : dir.normalize();
        Vec3 gate = Vec3.atBottomCenterOf(c).add(dir.scale(CitadelSites.SIZE * 8 + 48));
        BlockPos gatePos = BlockPos.containing(gate);
        boolean show = showable(level, gatePos);
        BlockPos top = show ? surface(level, gate) : gatePos;
        List<Entity> party = new ArrayList<>();
        Villager merchant = EntityType.VILLAGER.create(level);
        if (merchant == null) {
            return;
        }
        merchant.setVillagerData(merchant.getVillagerData().setProfession(VillagerProfession.LIBRARIAN).setLevel(3));
        merchant.setCustomName(Component.literal("王都の御用商人"));
        merchant.setPersistenceRequired();
        party.add(merchant);
        for (int i = 0; i < 2; i++) {
            RoyalMob g = RoyalRegistry.TYPES.get(RoyalRole.GUARD).create(level);
            if (g != null) {
                g.setPersistenceRequired();
                party.add(g);
            }
        }
        for (int i = 0; i < party.size(); i++) {
            party.get(i).moveTo(top.getX() + 0.5 + i - 1, top.getY(), top.getZ() + 0.5, 0F, 0F);
        }
        List<ItemStack> wares = known(level, c, true, 28);
        Journey j = dispatch(level, roads, CAPITAL, gatePos, "王都", new Target(dest.id, dest.center, progress.of(dest).name(), false), List.of(), wares,
            now, "royal");
        if (show) {
            j.state = "walking";                  // before they join the world (a traveller of a journey not walking is refused)
        }
        for (Entity m : party) {
            m.getPersistentData().putUUID(KEY, j.id);
            m.getPersistentData().putInt(SEQ, j.seq);
            if (j.lead == null) {
                j.lead = m.getUUID();
            }
            if (show) {
                j.walking.add(m.getUUID());
                level.addFreshEntity(m);
            } else {
                CompoundTag t = new CompoundTag();
                if (m.saveAsPassenger(t)) {
                    j.packed.add(t);
                }
            }
        }
        j.state = j.walking.isEmpty() ? "road" : "walking";
        capitalSays(level, "王都の御用商人が【" + plain(j.toName) + "】へ向けて城門を出ました　荷：" + describe(wares));
    }

    // ------------------------------------------------------------------------------------------------- in and out of sight

    /** Loaded, ticking ground on dry land outside the kingdom's walls: where a party on the road can be in the world. */
    static boolean showable(ServerLevel level, BlockPos b) {
        if (!ticking(level, b) || inKingdom(b)) {
            return false;
        }
        int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, b.getX(), b.getZ());
        BlockPos top = new BlockPos(b.getX(), y, b.getZ());
        return level.getFluidState(top).isEmpty() && level.getFluidState(top.below()).isEmpty();
    }

    /** Ground that is loaded and whose entities tick (a player near it, or kept loaded). */
    static boolean ticking(ServerLevel level, BlockPos p) {
        return level.isPositionEntityTicking(p);
    }

    private static boolean inKingdom(BlockPos b) {
        CitadelSites.Site cap = CitadelSites.capital();
        return cap != null && cap.contains(b.getX() >> 4, b.getZ() >> 4, 0);
    }

    /** The ground's top at a place in loaded ground, or null. */
    private static BlockPos surface(ServerLevel level, Vec3 p) {
        BlockPos b = BlockPos.containing(p);
        if (!ticking(level, b)) {
            return null;
        }
        return new BlockPos(b.getX(), level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, b.getX(), b.getZ()), b.getZ());
    }

    private static void unpack(ServerLevel level, Roads roads, Journey j, Vec3 p, long now, double along) {
        j.seq++;
        j.state = "walking";
        Vec3 side = new Vec3(-j.dir().z, 0, j.dir().x);
        BlockPos ptop = surface(level, p);
        double baseY = ptop != null ? ptop.getY() : p.y;
        // out of the keeping first: one still listed there is refused as a stale copy when he joins the world
        ListTag pending = j.packed.copy();
        j.packed.clear();
        int i = 0;
        for (Tag t : pending) {
            Vec3 q = p.add(side.scale((i % 3 - 1) * 1.5)).add(j.dir().scale(-1.5 * (i / 3)));
            q = new Vec3(q.x, baseY, q.z);
            Entity m = restore(level, (CompoundTag) t, q, true);
            if (m == null) {
                continue;
            }
            m.getPersistentData().putUUID(KEY, j.id);
            m.getPersistentData().putInt(SEQ, j.seq);
            j.walking.add(m.getUUID());
            if (!level.addFreshEntity(m)) {
                j.walking.remove(m.getUUID());
                j.packed.add(t);
                continue;
            }
            i++;
        }
        if (j.walking.isEmpty()) {
            j.state = "road";
            return;
        }
        j.seenAt = now;
        j.stuckAt = now;
        j.stuckFrom = along;
        j.shownTimes++;
        shown++;
        roads.setDirty();
        tell(level, p, 96, "§e【" + plain(j.fromName) + "】の" + ("royal".equals(j.kind) ? "御用商人の一行" : "行商隊") + "が通りかかりました（"
            + (j.leg == 0 ? "【" + plain(j.toName) + "】へ" : "帰り道") + "）");
        LOG.info(String.format(Locale.ROOT, "ROAD-SEEN {\"from\":\"%s\",\"to\":\"%s\",\"leg\":%d,\"along\":%.0f,\"of\":%.0f,\"members\":%d}",
            plain(j.fromName), plain(j.toName), j.leg, along, j.length(), i));
    }

    /** A member out of the world into the journey's keeping. */
    private static void pack(Journey j, Entity m) {
        CompoundTag t = new CompoundTag();
        if (m.saveAsPassenger(t)) {
            j.packed.add(t);
        }
        j.walking.remove(m.getUUID());
        m.discard();
        packed++;
    }

    private static void toRoad(Journey j, long now, double along) {
        j.state = "road";
        j.done = Math.max(0, Math.min(j.length(), along));
        j.legStart = now;
        j.seq++;
    }

    /** An entity from a journey's keeping, at a place (on the ground there when asked). */
    private static Entity restore(ServerLevel level, CompoundTag tag, Vec3 at, boolean ground) {
        BlockPos top = ground ? surface(level, at) : null;
        double y = top != null ? top.getY() : at.y;
        Entity e = EntityType.loadEntityRecursive(tag.copy(), level, x -> {
            x.moveTo(at.x, y, at.z, x.getYRot(), 0F);
            return x;
        });
        if (e != null && level.getEntity(e.getUUID()) != null) {
            e.setUUID(UUID.randomUUID());          // never two of the same
        }
        return e;
    }

    /** No longer a traveller: an ordinary villager (or guard) wherever he is. */
    static void release(Entity m) {
        m.getPersistentData().remove(KEY);
        m.getPersistentData().remove(SEQ);
    }

    private static void end(Roads roads, Journey j) {
        roads.journeys.remove(j.id);
        roads.setDirty();
    }

    private static void lost(ServerLevel level, Roads roads, Journey j) {
        LOG.info("ROAD-LOST {\"from\":\"{}\",\"to\":\"{}\",\"leg\":{}}", plain(j.fromName), plain(j.toName), j.leg);
        if (!CAPITAL.equals(j.from)) {
            announceTo(level, j.from, "【" + plain(j.fromName) + "】の行商隊は【" + plain(j.toName) + "】への道で消息を絶ちました");
        }
        end(roads, j);
    }

    // ------------------------------------------------------------------------------------------------------------ realms

    /** Whose land a place is: the royal capital's, a kingdom's (640 blocks about it), or no one's (""). */
    static String realm(ServerLevel level, BlockPos p) {
        if (inKingdom(p)) {
            return "王都";
        }
        VillageProgress progress = VillageProgress.get(level);
        String best = "";
        double bestD = (double) REALM * REALM;
        for (VillageLedger.Village v : VillageLedger.get(level).villages.values()) {
            VillageProgress.Record r = progress.villages.get(v.id);
            if (r != null && r.kingdom) {
                double d = v.center.distSqr(p);
                if (d < bestD) {
                    bestD = d;
                    best = r.name();
                }
            }
        }
        return best;
    }

    private static void realmCheck(ServerLevel level, Journey j, BlockPos p, boolean seen) {
        if (level.getGameTime() % 100 != 11) {
            return;
        }
        String r = realm(level, p);
        if (r.equals(j.realm)) {
            return;
        }
        String was = j.realm;
        j.realm = r;
        crossings++;
        LOG.info("ROAD-CROSSING {\"from\":\"{}\",\"out\":\"{}\",\"into\":\"{}\",\"seen\":{}}", plain(j.fromName), plain(was), plain(r), seen);
        if (seen) {
            tell(level, Vec3.atCenterOf(p), 96, "§e【" + plain(j.fromName) + "】の行商隊が"
                + (r.isEmpty() ? "【" + plain(was) + "】の国境を出ました" : "国境を越えて【" + plain(r) + "】に入りました"));
        }
    }

    // ------------------------------------------------------------------------------------------------------------ goods

    /** What the chests hold beyond KEEP of a kind (never emeralds, nor anything that does not stack), at most so many stacks and so much worth. */
    static List<ItemStack> take(ServerLevel level, List<BlockPos> chests, int stacks, double budget) {
        List<ItemStack> out = new ArrayList<>();
        if (chests == null || chests.isEmpty()) {
            return out;
        }
        Map<Item, Integer> total = new HashMap<>();
        List<Container> boxes = new ArrayList<>();
        for (BlockPos p : chests) {
            if (level.isLoaded(p) && level.getBlockEntity(p) instanceof Container c) {
                boxes.add(c);
                for (int i = 0; i < c.getContainerSize(); i++) {
                    ItemStack s = c.getItem(i);
                    if (!s.isEmpty()) {
                        total.merge(s.getItem(), s.getCount(), Integer::sum);
                    }
                }
            }
        }
        double spent = 0;
        for (Container c : boxes) {
            for (int i = 0; i < c.getContainerSize() && out.size() < stacks; i++) {
                ItemStack s = c.getItem(i);
                if (s.isEmpty() || s.is(Items.EMERALD) || s.getMaxStackSize() < 16 || s.isDamageableItem()) {
                    continue;
                }
                int spare = total.getOrDefault(s.getItem(), 0) - KEEP;
                if (spare <= 0) {
                    continue;
                }
                int n = Math.min(spare, s.getCount());
                double each = worth(s) / s.getCount();
                if (each > 0 && spent + each * n > budget) {
                    n = (int) Math.floor((budget - spent) / each);
                }
                if (n <= 0) {
                    continue;
                }
                out.add(s.copyWithCount(n));
                s.shrink(n);
                total.merge(s.getItem(), -n, Integer::sum);
                spent += each * n;
                c.setChanged();
            }
        }
        return out;
    }

    /** Goods into a village's communal chests; what does not fit comes back. */
    private static List<ItemStack> store(ServerLevel level, VillageLedger.Village v, List<ItemStack> goods) {
        VillageWork.Survey s = VillageWork.cached(v.id);
        List<ItemStack> left = new ArrayList<>();
        for (ItemStack g : goods) {
            ItemStack rest = g.copy();
            if (s != null) {
                for (BlockPos p : s.chests) {
                    if (rest.isEmpty()) {
                        break;
                    }
                    if (level.isLoaded(p) && level.getBlockEntity(p) instanceof Container c) {
                        rest = VillageWork.insert(c, rest);
                        c.setChanged();
                    }
                }
            }
            if (!rest.isEmpty()) {
                left.add(rest);
            }
        }
        return left;
    }

    /** What a land is known for (by its biome), to so much worth: the royal capital's the kingdom's own wares. */
    private static List<ItemStack> known(ServerLevel level, BlockPos at, boolean capital, double budget) {
        String[] goods;
        if (capital) {
            goods = new String[]{"iron_ingot", "bread", "gold_ingot", "cooked_beef", "glass", "lantern", "superbwarfare:rifle_ammo_box",
                "superbwarfare:handgun_ammo_box"};
        } else {
            String biome = level.getBiome(at).unwrapKey().map(k -> k.location().getPath()).orElse("plains");
            if (biome.contains("desert") || biome.contains("badlands")) {
                goods = new String[]{"sand", "cactus", "terracotta", "rabbit_hide", "gold_nugget"};
            } else if (biome.contains("snow") || biome.contains("taiga") || biome.contains("ice") || biome.contains("grove")) {
                goods = new String[]{"spruce_log", "sweet_berries", "leather", "packed_ice", "white_wool"};
            } else if (biome.contains("savanna")) {
                goods = new String[]{"acacia_log", "cooked_beef", "leather", "hay_block"};
            } else if (biome.contains("jungle") || biome.contains("swamp") || biome.contains("mangrove")) {
                goods = new String[]{"cocoa_beans", "bamboo", "melon_slice", "slime_ball", "mangrove_log"};
            } else if (biome.contains("peak") || biome.contains("hill") || biome.contains("mountain") || biome.contains("stony")) {
                goods = new String[]{"iron_ingot", "coal", "stone_bricks", "copper_ingot", "lapis_lazuli"};
            } else if (biome.contains("ocean") || biome.contains("beach") || biome.contains("river")) {
                goods = new String[]{"cooked_cod", "cooked_salmon", "dried_kelp_block", "prismarine_shard", "ink_sac"};
            } else {
                goods = new String[]{"bread", "wheat", "hay_block", "leather", "oak_log", "pumpkin_pie"};
            }
        }
        List<ItemStack> out = new ArrayList<>();
        double spent = 0, share = budget / goods.length;
        for (String id : goods) {
            Item item = BuiltInRegistries.ITEM.getOptional(id.contains(":") ? ResourceLocation.parse(id) : ResourceLocation.withDefaultNamespace(id))
                .orElse(null);
            if (item == null || item == Items.AIR) {
                continue;
            }
            ItemStack one = new ItemStack(item);
            double each = Math.max(0.01, worth(one));
            int n = (int) Math.min(one.getMaxStackSize(), Math.floor(Math.min(share, budget - spent) / each));
            if (n <= 0) {
                continue;
            }
            out.add(one.copyWithCount(n));
            spent += each * n;
        }
        return out;
    }

    /** What goods are worth in emeralds (about the villagers' own prices). */
    static double worth(List<ItemStack> goods) {
        double w = 0;
        for (ItemStack s : goods) {
            w += worth(s);
        }
        return w;
    }

    static double worth(ItemStack s) {
        String id = BuiltInRegistries.ITEM.getKey(s.getItem()).getPath();
        double each;
        if (s.is(Items.EMERALD)) {
            each = 1;
        } else if (s.is(Items.NETHERITE_INGOT)) {
            each = 12;
        } else if (s.is(Items.DIAMOND)) {
            each = 3;
        } else if (s.is(Items.NETHERITE_SCRAP) || s.is(Items.ANCIENT_DEBRIS)) {
            each = 4;
        } else if (s.is(Items.GOLDEN_APPLE) || s.is(Items.ENCHANTED_BOOK)) {
            each = 4;
        } else if (s.is(Items.GOLD_INGOT) || s.is(Items.ENDER_PEARL) || s.is(Items.BLAZE_ROD)) {
            each = 0.5;
        } else if (s.is(Items.IRON_INGOT) || s.is(Items.LAPIS_LAZULI) || s.is(Items.OBSIDIAN)) {
            each = 0.25;
        } else if (id.endsWith("_ingot") || id.endsWith("_gem") || id.contains("ammo")) {
            each = 0.2;
        } else if (s.is(Items.LEATHER) || s.is(Items.BOOK) || s.is(Items.GLASS) || s.is(Items.LANTERN) || id.contains("wool")) {
            each = 0.12;
        } else if (s.has(net.minecraft.core.component.DataComponents.FOOD)) {
            each = 0.06;
        } else if (id.endsWith("_log") || id.endsWith("_planks") || id.equals("coal") || id.equals("redstone") || id.endsWith("_nugget")) {
            each = 0.05;
        } else if (id.contains("stone") || id.contains("dirt") || id.contains("sand") || id.contains("gravel") || id.contains("deepslate")) {
            each = 0.01;
        } else {
            each = 0.04;
        }
        return each * s.getCount();
    }

    static ListTag save(ServerLevel level, List<ItemStack> goods) {
        ListTag l = new ListTag();
        for (ItemStack s : goods) {
            if (!s.isEmpty()) {
                l.add(s.save(level.registryAccess()));
            }
        }
        return l;
    }

    static List<ItemStack> stacks(ServerLevel level, ListTag l) {
        List<ItemStack> out = new ArrayList<>();
        for (Tag t : l) {
            if (t instanceof CompoundTag c) {
                ItemStack s = ItemStack.parseOptional(level.registryAccess(), c);
                if (!s.isEmpty()) {
                    out.add(s);
                }
            }
        }
        return out;
    }

    static String describe(List<ItemStack> goods) {
        if (goods.isEmpty()) {
            return "なし";
        }
        Map<String, Integer> sum = new LinkedHashMap<>();
        for (ItemStack s : goods) {
            sum.merge(s.getHoverName().getString(), s.getCount(), Integer::sum);
        }
        StringBuilder b = new StringBuilder();
        int n = 0;
        for (Map.Entry<String, Integer> e : sum.entrySet()) {
            if (n++ == 4) {
                b.append(" ほか");
                break;
            }
            b.append(n == 1 ? "" : "、").append(e.getKey()).append("×").append(e.getValue());
        }
        return b.toString();
    }

    private static String plain(String name) {
        String s = name == null ? "" : name;
        if (s.startsWith("【") && s.endsWith("】")) {
            s = s.substring(1, s.length() - 1);
        }
        return s.replace("】", "").replace("【", "");
    }

    // ------------------------------------------------------------------------------------------------------------ telling

    private static void announce(ServerLevel level, VillageLedger.Village v, String msg) {
        if (v != null) {
            VillageProgress.announce(level, v, msg, false);
        }
    }

    private static void announceTo(ServerLevel level, UUID village, String msg) {
        if (CAPITAL.equals(village)) {
            capitalSays(level, msg);
        } else {
            announce(level, VillageLedger.get(level).villages.get(village), msg);
        }
    }

    private static void capitalSays(ServerLevel level, String msg) {
        CitadelSites.Site cap = CitadelSites.capital();
        if (cap == null) {
            return;
        }
        for (ServerPlayer p : level.players()) {
            if (cap.contains(p.chunkPosition().x, p.chunkPosition().z, 4)) {
                p.sendSystemMessage(Component.literal("§6[王都] §f" + msg));
            }
        }
    }

    private static void tell(ServerLevel level, Vec3 at, double r, String msg) {
        for (ServerPlayer p : level.players()) {
            if (p.position().distanceToSqr(at) < r * r) {
                p.sendSystemMessage(Component.literal(msg));
            }
        }
    }

    // --------------------------------------------------------------------------------------------- the travellers themselves

    /**
     * VillagerLife.tick's start (VillagerRoadMixin): a traveller walks his road instead of living his village's day (work,
     * bed, chores would turn him round for home). A fight or a flight is left to the village's own ways.
     */
    public static boolean onLife(Entity e) {
        if (!(e instanceof Villager v) || !(v.level() instanceof ServerLevel level) || !v.getPersistentData().hasUUID(KEY)) {
            return false;
        }
        if (AdaptiveCombat.enemy(v, v.getTarget()) || VillageAI.fleeing(v)) {
            return false;
        }
        if ((v.tickCount + v.getId()) % 20 != 0) {
            return true;
        }
        Journey j = Roads.of(level).journeys.get(v.getPersistentData().getUUID(KEY));
        if (j == null) {
            release(v);
            return false;
        }
        if (!"walking".equals(j.state)) {
            return true;
        }
        double along = j.along(v.position());
        Vec3 goal = j.at(Math.min(j.length(), Math.max(0, along) + 14));
        BlockPos at = surface(level, goal);
        if (at == null) {
            at = new BlockPos(BlockPos.containing(goal).getX(), v.getBlockY(), BlockPos.containing(goal).getZ());
        }
        VillageAI.walk(v, at, VillageAI.pace(v, 0.35), 2);
        VillagerLife.data(v).putString("Task", j.leg == 0 ? "行商" : "帰路");
        return true;
    }

    /** Members taken into a journey's keeping as their ground stopped ticking: discarded on the next tick if still in the world. */
    private static final Set<UUID> GONE = new HashSet<>();

    /**
     * A member's ground stopped ticking or unloaded under him: into the journey's keeping. (CI 43: the world stops tracking an
     * entity as its chunk leaves the ticking range, before the unload sets a removal reason, and the unload itself tells
     * no one; the party in the first village's unloaded ground was never taken in.) A copy stays in the saved ground and is
     * refused when it loads; one still in the world is discarded on the next tick.
     */
    @SubscribeEvent
    public static void left(EntityLeaveLevelEvent e) {
        Entity m = e.getEntity();
        if (!(e.getLevel() instanceof ServerLevel level) || !m.getPersistentData().hasUUID(KEY)) {
            return;
        }
        Entity.RemovalReason why = m.getRemovalReason();
        if (why != null && why != Entity.RemovalReason.UNLOADED_TO_CHUNK && why != Entity.RemovalReason.UNLOADED_WITH_PLAYER) {
            return;                                  // killed, discarded, gone to another dimension
        }
        Roads roads = Roads.of(level);
        Journey j = roads.journeys.get(m.getPersistentData().getUUID(KEY));
        if (j == null || !j.walking.contains(m.getUUID())) {
            return;
        }
        CompoundTag t = new CompoundTag();
        if (m.saveAsPassenger(t)) {
            j.packed.add(t);
        }
        j.walking.remove(m.getUUID());
        packed++;
        if (why == null) {
            GONE.add(m.getUUID());
        }
        if (j.walking.isEmpty()) {
            toRoad(j, level.getGameTime(), j.along(m.position()));
        }
        roads.setDirty();
    }

    /** A traveller coming into the world: his journey's own, a copy of an earlier time (refused), or one whose journey is over (released). */
    @SubscribeEvent
    public static void joined(EntityJoinLevelEvent e) {
        Entity m = e.getEntity();
        if (!(e.getLevel() instanceof ServerLevel level) || !m.getPersistentData().hasUUID(KEY)) {
            return;
        }
        Journey j = Roads.of(level).journeys.get(m.getPersistentData().getUUID(KEY));
        if (j == null) {
            release(m);
            return;
        }
        if (!"walking".equals(j.state) || m.getPersistentData().getInt(SEQ) != j.seq || j.holds(m.getUUID())) {
            e.setCanceled(true);
            return;
        }
        if (!j.walking.contains(m.getUUID())) {
            j.walking.add(m.getUUID());
        }
    }

    /** A traveller killed: the trader drops what the party carries. */
    @SubscribeEvent
    public static void died(LivingDeathEvent e) {
        LivingEntity m = e.getEntity();
        if (!(m.level() instanceof ServerLevel level) || !m.getPersistentData().hasUUID(KEY)) {
            return;
        }
        Roads roads = Roads.of(level);
        Journey j = roads.journeys.get(m.getPersistentData().getUUID(KEY));
        if (j == null) {
            return;
        }
        j.walking.remove(m.getUUID());
        if (m.getUUID().equals(j.migrant)) {
            j.migrant = null;
        }
        if (m.getUUID().equals(j.lead)) {
            List<ItemStack> goods = stacks(level, j.leg == 0 ? j.cargo : j.wares);
            int em = j.emeralds;
            while (em > 0) {
                int n = Math.min(64, em);
                goods.add(new ItemStack(Items.EMERALD, n));
                em -= n;
            }
            for (ItemStack s : goods) {
                level.addFreshEntity(new ItemEntity(level, m.getX(), m.getY() + 0.5, m.getZ(), s));
            }
            if (!goods.isEmpty()) {
                robbed++;
                tell(level, m.position(), 64, "§c【" + plain(j.fromName) + "】の行商隊が襲われ、荷が散らばった：" + describe(goods));
                LOG.info("ROAD-ROBBED {\"from\":\"{}\",\"goods\":{}}", plain(j.fromName), goods.size());
            }
            j.cargo = new ListTag();
            j.wares = new ListTag();
            j.emeralds = 0;
            j.lead = j.walking.isEmpty() ? null : j.walking.get(0);
        }
        if (j.walking.isEmpty() && j.packed.isEmpty()) {
            lost(level, roads, j);
        }
        roads.setDirty();
    }

    /** For reports: the parties on the roads and what has happened on them since the server started. */
    public static String report(ServerLevel level) {
        Roads roads = Roads.of(level);
        int walking = 0, road = 0, home = 0;
        for (Journey j : roads.journeys.values()) {
            switch (j.state) {
                case "walking" -> walking++;
                case "road" -> road++;
                default -> home++;
            }
        }
        return String.format(Locale.ROOT, "{\"onRoads\":%d,\"walking\":%d,\"outOfSight\":%d,\"waitingHome\":%d,\"departed\":%d,\"arrived\":%d,\"cameHome\":%d,"
                + "\"seen\":%d,\"packed\":%d,\"crossings\":%d,\"settled\":%d,\"robbed\":%d,\"settlersWaiting\":%d}", roads.journeys.size(), walking, road,
            home, departed, arrivedOut, cameHome, shown, packed, crossings, settled, robbed, roads.settlers.size());
    }
}
