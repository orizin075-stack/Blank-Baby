package jp.oror.reborn.perf;

import jp.oror.reborn.royal.RoyalMob;
import net.minecraft.world.entity.Mob;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;

/**
 * The royals' path searches made smaller (049): a search may look at sixteen nodes for each block of the mob's follow
 * range, and the royals follow their enemies far; half that is enough for the stand-offs and charges of a battle, and
 * a search that would need more is given up sooner (the hundred-man battle spent an eighth of its tick on the royals'
 * paths, by the CI's profile).
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class PathBudget {
    private PathBudget() {
    }

    @SubscribeEvent
    public static void joined(EntityJoinLevelEvent e) {
        if (!e.getLevel().isClientSide() && e.getEntity() instanceof RoyalMob m) {
            ((Mob) m).getNavigation().setMaxVisitedNodesMultiplier(0.5F);
        }
    }
}
