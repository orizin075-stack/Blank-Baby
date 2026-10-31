package jp.oror.reborn.citadel;

import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.royal.RoyalRole;
import net.minecraft.core.BlockPos;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.EntityTickEvent;

/**
 * The Villager King keeps his seat. Posted to the throne, with no enemy to fight, he sits on the throne block itself,
 * facing his hall; he used to wander a block or so off it (his idle stroll and look-around goals), and only walked back
 * when more than a block away. In a fight he leaves it as before (RoyalMob's own combat), and returns when it is over.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class ThroneSeat {
    private ThroneSeat() {
    }

    @SubscribeEvent
    public static void sit(EntityTickEvent.Post e) {
        if (!(e.getEntity() instanceof RoyalMob king) || king.level().isClientSide || king.tickCount % 4 != 0 || king.role() != RoyalRole.KING
            || !"throne".equals(king.getPersistentData().getString("OrorCitadelPost")) || king.getTarget() != null || !king.hasRestriction()) {
            return;
        }
        // the throne of his citadel (the cell above the gold dais), else where he was posted
        CitadelSites.Site site = CitadelSites.nearest(king.blockPosition(), 1);
        BlockPos seat = site != null && site.throne().closerThan(king.blockPosition(), 8) ? site.throne() : king.getRestrictCenter();
        double dx = king.getX() - (seat.getX() + 0.5), dz = king.getZ() - (seat.getZ() + 0.5), dy = king.getY() - seat.getY();
        if (dx * dx + dz * dz > 0.09 && Math.abs(dy) < 2.5) {
            king.getNavigation().stop();
            king.moveTo(seat.getX() + 0.5, seat.getY(), seat.getZ() + 0.5, 0F, 0F);
            king.setYHeadRot(0F);
            king.setYBodyRot(0F);
        }
    }
}
