package jp.oror.reborn.citadel;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashSet;
import java.util.Set;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.royal.RoyalRegistry;
import jp.oror.reborn.royal.RoyalRole;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.LongArrayTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.npc.VillagerData;
import net.minecraft.world.entity.npc.VillagerProfession;
import net.minecraft.world.entity.npc.VillagerType;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.saveddata.SavedData;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.level.ChunkEvent;
import net.neoforged.neoforge.event.server.ServerStoppedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * The people of a Grand Citadel take their posts the first time each chunk of it is loaded: the villager king on the
 * throne, the generals, the imperial guard and the court, the gate and casemate garrisons, the outer fortresses, the
 * tank crews and the townsfolk (garrison.json). This works for citadels generated in new worlds and for the 045 preview
 * save, whose citadel had no people. Each chunk's posts are filled once (a ledger in the world's saved data), a few
 * chunks a tick, on the server thread.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class CitadelGarrison {
    public static final String TAG = "oror_citadel";
    private static final Deque<long[]> QUEUE = new ArrayDeque<>();
    private static final Set<Long> QUEUED = new HashSet<>();
    private static int spawned;

    private CitadelGarrison() {
    }

    /** The ledger key of a save chunk of a site: 22 bits each for the site's chunk x and z, 7 each for the save chunk. */
    static long key(CitadelSites.Site site, int sx, int sz) {
        return ((long) (site.chunkX() & 0x3FFFFF) << 42) | ((long) (site.chunkZ() & 0x3FFFFF) << 20) | ((long) (sx + 64) << 7) | (sz + 64);
    }

    @SubscribeEvent
    public static void load(ChunkEvent.Load e) {
        if (!(e.getLevel() instanceof ServerLevel level) || !level.dimension().equals(Level.OVERWORLD) || !(e.getChunk() instanceof LevelChunk chunk)) {
            return;
        }
        ChunkPos pos = chunk.getPos();
        CitadelSites.Site site = CitadelSites.garrisoned(level.getChunkSource().getGenerator(), pos.x, pos.z);
        if (site == null) {
            return;
        }
        int sx = pos.x - site.chunkX() - CitadelData.HALF, sz = pos.z - site.chunkZ() - CitadelData.HALF;
        if (CitadelData.posts(sx, sz).isEmpty()) {
            return;
        }
        long k = key(site, sx, sz);
        synchronized (QUEUE) {
            if (QUEUED.add(k)) {
                QUEUE.add(new long[]{k, pos.x, pos.z, site.chunkX(), site.chunkZ(), site.ground()});
            }
        }
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        ServerLevel level = e.getServer().overworld();
        for (int n = 0; n < 4; n++) {
            long[] q;
            synchronized (QUEUE) {
                q = QUEUE.poll();
                if (q != null) {
                    QUEUED.remove(q[0]);
                }
            }
            if (q == null) {
                return;
            }
            Ledger ledger = Ledger.of(level);
            if (ledger.done.contains(q[0]) || level.getChunkSource().getChunkNow((int) q[1], (int) q[2]) == null) {
                continue;
            }
            CitadelSites.Site site = new CitadelSites.Site((int) q[3], (int) q[4], (int) q[5], false);
            int sx = (int) q[1] - site.chunkX() - CitadelData.HALF, sz = (int) q[2] - site.chunkZ() - CitadelData.HALF;
            for (CitadelData.Post post : CitadelData.posts(sx, sz)) {
                Mob mob = spawn(level, site, post);
                if (mob != null) {
                    spawned++;
                }
            }
            ledger.done.add(q[0]);
            ledger.setDirty();
        }
    }

    @SubscribeEvent
    public static void stopped(ServerStoppedEvent e) {
        synchronized (QUEUE) {
            QUEUE.clear();
            QUEUED.clear();
        }
    }

    public static int spawned() {
        return spawned;
    }

    public static int queued() {
        synchronized (QUEUE) {
            return QUEUE.size();
        }
    }

    /** One person at a post, in the world. */
    static Mob spawn(ServerLevel level, CitadelSites.Site site, CitadelData.Post post) {
        BlockPos at = site.toWorld(post.x(), post.y(), post.z());
        if (at.getY() <= level.getMinBuildHeight() || at.getY() >= level.getMaxBuildHeight() - 2) {
            return null;
        }
        Mob mob = post.villager() ? villager(level, at, post) : royal(level, post.role().equals("TANK") ? "GUARD" : post.role());
        if (mob == null) {
            return null;
        }
        if (!post.vehicle().isEmpty()) {
            mob.getPersistentData().putString("OrorMotor", post.vehicle());
            mob.getPersistentData().putInt("OrorMotorSeats", post.seats());
        }
        mob.moveTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5, post.yaw(), 0.0F);
        mob.setYHeadRot(post.yaw());
        mob.setYBodyRot(post.yaw());
        mob.setPersistenceRequired();
        mob.addTag(TAG);
        mob.getPersistentData().putString("OrorCitadelPost", post.post());
        level.addFreshEntity(mob);
        return mob;
    }

    private static Mob royal(ServerLevel level, String role) {
        RoyalRole r;
        try {
            r = RoyalRole.valueOf(role);
        } catch (IllegalArgumentException e) {
            return null;
        }
        EntityType<RoyalMob> type = RoyalRegistry.TYPES.get(r);
        return type == null ? null : type.create(level);
    }

    private static Mob villager(ServerLevel level, BlockPos at, CitadelData.Post post) {
        Villager v = EntityType.VILLAGER.create(level);
        if (v == null) {
            return null;
        }
        VillagerData d = v.getVillagerData().setType(VillagerType.byBiome(level.getBiome(at)));
        if (!post.profession().isEmpty()) {
            VillagerProfession trade = BuiltInRegistries.VILLAGER_PROFESSION.get(ResourceLocation.withDefaultNamespace(post.profession()));
            if (trade != VillagerProfession.NONE) {
                // a journeyman who has traded keeps the trade without a workstation
                d = d.setProfession(trade).setLevel(2);
                v.setVillagerXp(10);
            }
        }
        v.setVillagerData(d);
        if (post.baby()) {
            v.setAge(-24000);
        }
        // the town belongs to the villager king: the village system counts it as a kingdom
        v.getPersistentData().putString("OrorSettlement", "kingdom");
        return v;
    }

    /** Which chunks of which citadels have had their people. */
    static final class Ledger extends SavedData {
        static final Factory<Ledger> FACTORY = new Factory<>(Ledger::new, Ledger::load, null);
        final Set<Long> done = new HashSet<>();

        static Ledger of(ServerLevel level) {
            return level.getDataStorage().computeIfAbsent(FACTORY, "oror_citadel_garrison");
        }

        static Ledger load(CompoundTag tag, HolderLookup.Provider registries) {
            Ledger l = new Ledger();
            for (long k : tag.getLongArray("Done")) {
                l.done.add(k);
            }
            return l;
        }

        @Override
        public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
            tag.put("Done", new LongArrayTag(done.stream().mapToLong(Long::longValue).toArray()));
            return tag;
        }
    }
}
