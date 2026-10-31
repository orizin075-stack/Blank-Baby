package jp.oror.reborn.citadel;

import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.vehicle.RoyalPilots;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.level.Explosion;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.level.ExplosionEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * The capital is not wrecked by its own defence (048): the turrets on its walls, its tanks and helicopters fire heavy
 * shells and rockets at whatever comes near, and every miss blew holes in the roofs of the castle and the town (in a
 * world with the pack's block physics, the broken blocks then hang about as debris). An explosion inside a citadel
 * that the kingdom's own forces caused (a royal, a crewed vehicle or turret, or a shell, rocket or missile one of
 * them fired) breaks no blocks; nor does any explosion inside the castle's ward, the keep and its courts. Entities are
 * hurt and thrown as before: only the blocks are spared.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class CapitalGuard {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Citadel");
    /** Half the side of the castle's ward (keep, courts, inner moat), from the citadel's centre. */
    private static final int WARD = 140;
    public static int spared;

    private CapitalGuard() {
    }

    @SubscribeEvent
    public static void detonate(ExplosionEvent.Detonate e) {
        if (!(e.getLevel() instanceof ServerLevel) || e.getAffectedBlocks().isEmpty()) {
            return;
        }
        Vec3 c = e.getExplosion().center();
        CitadelSites.Site site = CitadelSites.nearest(BlockPos.containing(c), CitadelData.HALF * 16 + 32);
        if (site == null) {
            return;
        }
        BlockPos centre = site.center();
        double dx = Math.abs(c.x - centre.getX()), dz = Math.abs(c.z - centre.getZ());
        if (dx > CitadelData.HALF * 16 || dz > CitadelData.HALF * 16) {
            return;
        }
        if (dx <= WARD && dz <= WARD || kingdoms(e.getExplosion())) {
            int n = e.getAffectedBlocks().size();
            e.getAffectedBlocks().clear();
            if (spared++ % 50 == 0) {
                LOG.info("CAPITAL-GUARD {\"spared\":{},\"blocks\":{},\"at\":[{},{},{}]}", spared, n, (int) c.x, (int) c.y, (int) c.z);
            }
        }
    }

    /** The kingdom's own fire: a royal, a crewed vehicle or turret, its rider, or what one of them shot. */
    static boolean kingdoms(Explosion x) {
        Entity direct = x.getDirectSourceEntity(), cause = x.getIndirectSourceEntity();
        Entity owner = direct instanceof Projectile p ? p.getOwner() : null;
        for (Entity en : new Entity[]{direct, cause, owner}) {
            if (en == null) {
                continue;
            }
            if (en instanceof RoyalMob || en.getTags().contains(RoyalPilots.CREWED)
                || en.getVehicle() != null && en.getVehicle().getTags().contains(RoyalPilots.CREWED)) {
                return true;
            }
        }
        return false;
    }
}
