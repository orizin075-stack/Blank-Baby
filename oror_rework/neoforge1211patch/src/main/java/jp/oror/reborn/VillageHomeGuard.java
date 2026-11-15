package jp.oror.reborn;

import java.util.ArrayList;
import java.util.List;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.phys.AABB;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (059g) A village with a tank or a jet keeps two of its strong at home (ExpeditionHomeGuardMixin). The CI check of the
 * village's arms (CI 44 to 46) found the castle town's tank built and never brought out: every one of its strong
 * villagers (its weaponsmith, armourer and mason) had gone on a dungeon expedition, and a vehicle is crewed only by the
 * strong. An expedition's party now leaves two of them behind where the village has a vehicle (its weakest go no more;
 * with fewer than two left to go it does not set out).
 */
public final class VillageHomeGuard {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Village");
    static int trimmed;

    private VillageHomeGuard() {
    }

    /** The expedition's party with as many taken off its end as keep two strong at home, or null to leave it as it is. */
    public static List<Villager> trim(List<Villager> party) {
        if (party == null || party.isEmpty() || !(party.get(0).level() instanceof ServerLevel sl)) {
            return null;
        }
        VillageLedger.Village v = VillageLedger.of(party.get(0));
        if (v == null) {
            return null;
        }
        VillageProgress.Record r = VillageProgress.get(sl).villages.get(v.id);
        if (r == null || r.vehicles == null || r.vehicles.isEmpty()) {
            return null;
        }
        List<Villager> home = sl.getEntitiesOfClass(Villager.class, new AABB(v.center).inflate(64, 24, 64),
            x -> x.isAlive() && VillageAI.strong(x) && VillageLedger.of(x) == v && !party.contains(x) && !x.isPassenger());
        int need = 2 - home.size();
        if (need <= 0) {
            return null;
        }
        List<Villager> out = new ArrayList<>(party);
        while (need-- > 0 && !out.isEmpty()) {
            out.remove(out.size() - 1);
        }
        if (trimmed++ < 20) {
            LOG.info("EXPEDITION-HOME-GUARD {\"village\":\"{}\",\"party\":{},\"goes\":{},\"home\":{}}", r.name(), party.size(), out.size(),
                home.size() + party.size() - out.size());
        }
        return out;
    }
}
