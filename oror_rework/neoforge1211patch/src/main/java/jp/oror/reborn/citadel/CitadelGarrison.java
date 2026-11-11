package jp.oror.reborn.citadel;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashSet;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
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
import net.minecraft.world.entity.Entity;
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
import net.neoforged.neoforge.event.entity.EntityLeaveLevelEvent;
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
    private static int parked;
    /** (059) the garrison's people the world would not take, and those that left it, by why (for the CI check: since the
     * fourth 058 run the capital's royals were spawned and none were there a moment later) */
    private static int refused;
    /** (059) people's chunks waited for (announced before they were whole) and given up on (gone for a minute) */
    private static int waited, dropped, limbo, retried;
    /** (059) the first people spawned and every one of the throne's, held to see where they are later (CI) */
    private static final java.util.List<Object[]> TRACE = new java.util.ArrayList<>();
    private static final Map<String, Integer> LEFT = new TreeMap<>();
    private static int traced;
    private static final org.slf4j.Logger LOG = org.slf4j.LoggerFactory.getLogger("OROR Citadel");

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
                QUEUE.add(new long[]{k, pos.x, pos.z, site.chunkX(), site.chunkZ(), site.ground(), -1L, 0L, 0L});
            }
        }
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        ServerLevel level = e.getServer().overworld();
        long now = level.getGameTime();
        int waits = 0;
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
            if (ledger.done.contains(q[0])) {
                continue;
            }
            if (q[8] > now) {
                requeue(q);
                if (++waits >= 8) {
                    return;
                }
                n--;
                continue;
            }
            // (059) a chunk's load is announced before the chunk is whole: its people wait their turn again (a chunk
            // that went away comes back with its own load)
            int cx = (int) q[1], cz = (int) q[2];
            if (level.getChunkSource().getChunkNow(cx, cz) == null) {
                if (q[6] < 0) {
                    q[6] = now;
                }
                if (now - q[6] < 1200) {
                    requeue(q);
                    waited++;
                    if (++waits >= 8) {
                        return;
                    }
                    n--;
                } else {
                    dropped++;
                }
                continue;
            }
            CitadelSites.Site site = new CitadelSites.Site((int) q[3], (int) q[4], (int) q[5], false);
            int sx = (int) q[1] - site.chunkX() - CitadelData.HALF, sz = (int) q[2] - site.chunkZ() - CitadelData.HALF;
            // (059) and they must be in the world's lists once put in it: in most CI runs since 8 November the capital's
            // people were alive at their posts and in no list of the world's (the entities of a chunk not yet held and
            // ticked by the world: the king on his throne unseen, unmoving). Who is not is taken out again and the
            // chunk's people try again later (twenty times at most, a few seconds apart); the chunk is done when they
            // are all in the world.
            List<Mob> put = new ArrayList<>();
            boolean lost = false;
            for (CitadelData.Post post : CitadelData.posts(sx, sz)) {
                if (q[7] > 0 && post.role().equals("PARKED")) {
                    continue;   // the machines stood ready the first time
                }
                Mob mob = spawn(level, site, post);
                if (mob != null) {
                    put.add(mob);
                    if (level.getEntity(mob.getUUID()) != mob) {
                        lost = true;
                    }
                }
            }
            if (lost && q[7] < 20) {
                for (Mob m : put) {
                    m.discard();
                }
                retried++;
                q[7]++;
                q[8] = now + 60;
                requeue(q);
                continue;
            }
            spawned += put.size();
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

    /** Vehicles stood ready with no crew so far. */
    public static int parked() {
        return parked;
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
        if (post.role().equals("PARKED")) {
            Entity v = jp.oror.reborn.vehicle.RoyalPilots.deploy(level, net.minecraft.world.phys.Vec3.atBottomCenterOf(at), post.yaw(),
                post.vehicle(), 0, null);
            if (v != null) {
                v.addTag(TAG);
                parked++;
            }
            return null;
        }
        Mob mob = post.villager() ? villager(level, at, post) : royal(level, post.role().equals("TANK") ? "GUARD" : post.role());
        if (mob == null) {
            return null;
        }
        if (!post.vehicle().isEmpty()) {
            mob.getPersistentData().putString("OrorMotor", post.vehicle());
            mob.getPersistentData().putInt("OrorMotorSeats", post.seats());
            mob.getPersistentData().putFloat("OrorMotorYaw", post.yaw());
            mob.getPersistentData().putBoolean("OrorMotorStill", post.still());
            // (058) where the machine belongs, whatever the soldier does before he brings it out
            mob.getPersistentData().putLong("OrorMotorAt", at.asLong());
        }
        mob.moveTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5, post.yaw(), 0.0F);
        mob.setYHeadRot(post.yaw());
        mob.setYBodyRot(post.yaw());
        mob.setPersistenceRequired();
        mob.addTag(TAG);
        mob.getPersistentData().putString("OrorCitadelPost", post.post());
        if (!level.addFreshEntity(mob)) {
            refused++;
            if (refused <= 5) {
                LOG.info("GARRISON-REFUSED {} at {} (post {})", post.role(), at.toShortString(), post.post());
            }
            return null;
        }
        if (level.getEntity(mob.getUUID()) != mob) {
            limbo++;
        }
        synchronized (TRACE) {
            if (TRACE.size() < 12 || "throne".equals(post.post()) && TRACE.size() < 60) {
                TRACE.add(new Object[]{mob, at, level.getGameTime()});
            }
        }
        return mob;
    }

    /** (059) Where the traced people are now: alive, tracked by the world, how far from their posts. */
    public static String traced(ServerLevel level) {
        StringBuilder b = new StringBuilder("[");
        synchronized (TRACE) {
            for (Object[] t : TRACE) {
                Mob m = (Mob) t[0];
                BlockPos at = (BlockPos) t[1];
                Entity live = level.getEntity(m.getUUID());
                b.append(b.length() > 1 ? "," : "").append(String.format(java.util.Locale.ROOT,
                    "{\"type\":\"%s\",\"post\":\"%s\",\"at\":\"%s\",\"age\":%d,\"alive\":%b,\"removed\":\"%s\",\"tracked\":%b,\"same\":%b,"
                        + "\"now\":\"%d %d %d\",\"off\":%.1f,\"hp\":%.1f,\"last\":\"%s\"}",
                    EntityType.getKey(m.getType()).getPath(), m.getPersistentData().getString("OrorCitadelPost"), at.toShortString(),
                    level.getGameTime() - (long) t[2], m.isAlive(), m.getRemovalReason(), live != null, live == m,
                    m.getBlockX(), m.getBlockY(), m.getBlockZ(), Math.sqrt(m.blockPosition().distSqr(at)), m.getHealth(),
                    m.getLastDamageSource() == null ? "-" : m.getLastDamageSource().getMsgId()));
            }
        }
        return b.append(']').toString();
    }

    /** (059) The citadel's people in the box, counted over every entity of the level (not the box query). */
    public static int allTagged(ServerLevel level, net.minecraft.world.phys.AABB box) {
        int n = 0;
        for (Entity e : level.getAllEntities()) {
            if (e != null && e.getTags().contains(TAG) && box.contains(e.position())) {
                n++;
            }
        }
        return n;
    }

    /** (059) Why the garrison's people leave the world (killed, discarded, changed, unloaded), and who did it, the first few. */
    @SubscribeEvent
    public static void left(EntityLeaveLevelEvent e) {
        Entity en = e.getEntity();
        if (e.getLevel().isClientSide() || !en.getTags().contains(TAG)) {
            return;
        }
        Entity.RemovalReason r = en.getRemovalReason();
        String k = (r == null ? "NONE" : r.name()) + (en instanceof Villager ? "/villager" : en instanceof RoyalMob ? "/royal" : "/other");
        synchronized (LEFT) {
            LEFT.merge(k, 1, Integer::sum);
        }
        if (traced < 6 && r != Entity.RemovalReason.UNLOADED_TO_CHUNK && r != Entity.RemovalReason.UNLOADED_WITH_PLAYER) {
            traced++;
            StringBuilder b = new StringBuilder();
            for (StackTraceElement st : Thread.currentThread().getStackTrace()) {
                if (b.length() > 1800) {
                    break;
                }
                String c = st.getClassName();
                if (c.startsWith("java.") || c.startsWith("jdk.") || c.contains("EventBus") || c.contains("eventbus")) {
                    continue;
                }
                b.append(c.substring(c.lastIndexOf('.') + 1)).append('.').append(st.getMethodName()).append(':').append(st.getLineNumber()).append(" < ");
            }
            String hurt = en instanceof net.minecraft.world.entity.LivingEntity le && le.getLastDamageSource() != null
                ? le.getLastDamageSource().getMsgId() + " hp=" + le.getHealth() : "-";
            LOG.info("GARRISON-LEFT {} {} at {} post={} hurt={} by {}", k, net.minecraft.world.entity.EntityType.getKey(en.getType()),
                en.blockPosition().toShortString(), en.getPersistentData().getString("OrorCitadelPost"), hurt, b);
        }
    }

    private static void requeue(long[] q) {
        synchronized (QUEUE) {
            if (QUEUED.add(q[0])) {
                QUEUE.add(q);
            }
        }
    }

    public static int refused() {
        return refused;
    }

    public static String waits() {
        return "{\"waited\":" + waited + ",\"dropped\":" + dropped + ",\"untracked\":" + limbo + ",\"retried\":" + retried + "}";
    }

    public static String left() {
        synchronized (LEFT) {
            StringBuilder b = new StringBuilder("{");
            LEFT.forEach((k, v) -> b.append(b.length() > 1 ? "," : "").append('"').append(k).append("\":").append(v));
            return b.append('}').toString();
        }
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
