package jp.oror.reborn.citadel;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.royal.RoyalRole;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingDeathEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (059) The court is in its hall (the user: no king on the throne, no general, no sage).
 *
 * <p>The garrison brings each post's people once, when its chunk first loads; a court that never came (a capital
 * made by an earlier version, whose chunks the garrison had already counted as done), or one that fell or wandered
 * off, was gone for good. Every minute, while a player is near the palace and the hall about the throne is loaded,
 * the court is counted: the king, the generals, the sage, the archmage, the bodyguards and the imperial guard of the
 * throne's posts. Those missing come back to their posts, at most every five minutes. The king does not come back once
 * he has truly died (the last of his forms): that is recorded with the world.</p>
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class CourtKeeper {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Citadel");
    private static List<CitadelData.Post> throne;
    private static final List<UUID> DYING = new ArrayList<>();
    public static int restored, checks;

    private CourtKeeper() {
    }

    static List<CitadelData.Post> posts() {
        if (throne == null) {
            List<CitadelData.Post> l = new ArrayList<>();
            for (List<CitadelData.Post> ps : CitadelData.posts().values()) {
                for (CitadelData.Post p : ps) {
                    if ("throne".equals(p.post()) && !p.villager() && p.vehicle().isEmpty()) {
                        l.add(p);
                    }
                }
            }
            throne = l;
        }
        return throne;
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        ServerLevel level = e.getServer().overworld();
        long now = level.getGameTime();
        if (!DYING.isEmpty()) {
            // a king whose death was not turned back (a revival cancels it): he is gone
            for (UUID id : new ArrayList<>(DYING)) {
                net.minecraft.world.entity.Entity k = level.getEntity(id);
                if (k == null || !k.isAlive()) {
                    Ledger l = Ledger.of(level);
                    l.kingFallen = true;
                    l.setDirty();
                    LOG.info("COURT the king of the capital has fallen: he is not brought back");
                }
            }
            DYING.clear();
        }
        if (now % 1200 != 600) {
            return;
        }
        CitadelSites.Site site = CitadelSites.capital();
        if (site == null) {
            return;
        }
        keep(level, site, now, false);
    }

    /** Counts the court and brings back who is missing; the number brought. */
    public static int keep(ServerLevel level, CitadelSites.Site site, long now, boolean force) {
        BlockPos t = site.throne();
        if (!level.isLoaded(t) || !level.isLoaded(t.offset(48, 0, 48)) || !level.isLoaded(t.offset(-48, 0, -48))
            || !level.isPositionEntityTicking(t) || !level.areEntitiesLoaded(ChunkPos.asLong(t))) {
            // (059) not till the world holds and ticks the hall's entities (those put in before are in no one's sight)
            return 0;
        }
        if (!force && level.getNearestPlayer(t.getX(), t.getY(), t.getZ(), 160, false) == null) {
            return 0;
        }
        Ledger ledger = Ledger.of(level);
        if (!force && now - ledger.lastRestore < 6000) {
            return 0;
        }
        checks++;
        Map<RoyalRole, Integer> present = new EnumMap<>(RoyalRole.class);
        for (RoyalMob m : level.getEntitiesOfClass(RoyalMob.class, new AABB(t).inflate(160, 80, 160), Mob::isAlive)) {
            if ("throne".equals(m.getPersistentData().getString("OrorCitadelPost")) || m.role() == RoyalRole.KING) {
                present.merge(m.role(), 1, Integer::sum);
            }
        }
        Map<RoyalRole, Integer> seen = new EnumMap<>(RoyalRole.class);
        int brought = 0;
        StringBuilder who = new StringBuilder();
        for (CitadelData.Post post : posts()) {
            RoyalRole r;
            try {
                r = RoyalRole.valueOf(post.role());
            } catch (IllegalArgumentException ex) {
                continue;
            }
            int k = seen.merge(r, 1, Integer::sum);
            if (k <= present.getOrDefault(r, 0)) {
                continue;
            }
            if (r == RoyalRole.KING && ledger.kingFallen) {
                continue;
            }
            if (CitadelGarrison.spawn(level, site, post) != null) {
                brought++;
                who.append(r.name()).append(' ');
            }
        }
        if (brought > 0) {
            ledger.lastRestore = now;
            ledger.setDirty();
            restored += brought;
            LOG.info("COURT {} of the throne's court brought back to their posts: {}", brought, who.toString().trim());
        }
        return brought;
    }

    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void died(LivingDeathEvent e) {
        if (e.getEntity() instanceof RoyalMob m && m.role() == RoyalRole.KING && !m.level().isClientSide
            && "throne".equals(m.getPersistentData().getString("OrorCitadelPost"))) {
            DYING.add(m.getUUID());
        }
    }

    static final class Ledger extends SavedData {
        static final Factory<Ledger> FACTORY = new Factory<>(Ledger::new, Ledger::load, null);
        boolean kingFallen;
        long lastRestore = -100000;

        static Ledger of(ServerLevel level) {
            return level.getDataStorage().computeIfAbsent(FACTORY, "oror_court");
        }

        static Ledger load(CompoundTag tag, HolderLookup.Provider registries) {
            Ledger l = new Ledger();
            l.kingFallen = tag.getBoolean("KingFallen");
            l.lastRestore = tag.getLong("LastRestore");
            return l;
        }

        @Override
        public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
            tag.putBoolean("KingFallen", kingFallen);
            tag.putLong("LastRestore", lastRestore);
            return tag;
        }
    }
}
