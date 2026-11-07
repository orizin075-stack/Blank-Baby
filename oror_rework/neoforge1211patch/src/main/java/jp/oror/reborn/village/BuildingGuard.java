package jp.oror.reborn.village;

import jp.oror.reborn.VillageLedger;
import jp.oror.reborn.citadel.CitadelSites;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.level.ChunkPos;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.level.ExplosionEvent;

/**
 * (053) The buildings of the capital and of villages kept from their own people (the user: the palace's entrance and
 * villages broken).
 * <ul>
 * <li>The villagers' miners dig only underground: not a block open to the sky (a yard, a field, a path), nor where the
 * capital stands (above three blocks under its ground), and no longer calcite (the capital's white walls) nor grass
 * blocks (data/oror_supreme_bosses/tags/block/miner_tunnel.json); they were digging through what lay between their
 * workshop and a vein, up to two blocks above their workshop's floor (MinerGuardMixin).</li>
 * <li>Villagers build no huts in the capital (their 5 x 5 huts, begun wherever a ring round the village's middle
 * was clear: the palace's forecourt, the streets, before doors, and left half built while they waited for planks: the
 * entrances blocked and the buildings unfinished the user found), and in a village not within four blocks of a door, a
 * bell, a workstation or a path (VillagerBuildMixin); a hut begun in the capital is given up.</li>
 * <li>An explosion in the capital or in a village breaks no blocks unless a player or a monster made it: the
 * kingdom's turrets and tanks, the royals' and the villagers' guns and spells hurt what they hit, not the town they
 * defend (explosions break blocks elsewhere, as 049 asked).</li>
 * </ul>
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class BuildingGuard {
    private BuildingGuard() {
    }

    /** Within the capital's footprint (any citadel's), above dy levels under its ground. */
    public static boolean inCapital(BlockPos p, int below) {
        CitadelSites.Site s = CitadelSites.nearest(p, 0);
        if (s == null) {
            return false;
        }
        ChunkPos c = new ChunkPos(p);
        return s.contains(c.x, c.z, 1) && p.getY() > s.ground() - below;
    }

    public static boolean inVillage(ServerLevel sl, BlockPos p) {
        VillageLedger.Village v = VillageLedger.get(sl).nearest(p);
        return v != null && v.contains(p);
    }

    /** May villagers begin a 5 x 5 hut with this corner (before their own rules)? */
    public static boolean hutMay(ServerLevel sl, BlockPos corner) {
        if (inCapital(corner, 64)) {
            return false;
        }
        BlockPos.MutableBlockPos q = new BlockPos.MutableBlockPos();
        for (int x = -4; x <= 8; x++) {
            for (int z = -4; z <= 8; z++) {
                for (int y = -1; y <= 3; y++) {
                    net.minecraft.world.level.block.state.BlockState st = sl.getBlockState(q.set(corner.getX() + x, corner.getY() + y, corner.getZ() + z));
                    if (st.is(net.minecraft.tags.BlockTags.DOORS) || st.is(net.minecraft.world.level.block.Blocks.BELL)
                        || st.is(net.minecraft.world.level.block.Blocks.DIRT_PATH) || st.is(net.minecraft.tags.BlockTags.BEDS)
                        || st.is(net.minecraft.tags.BlockTags.FENCE_GATES) || workstation(st)) {
                        return false;
                    }
                }
            }
        }
        return true;
    }

    private static boolean workstation(net.minecraft.world.level.block.state.BlockState st) {
        return net.minecraft.world.entity.ai.village.poi.PoiTypes.forState(st).isPresent();
    }

    /** May a villager's miner dig here (before its own rules)? */
    public static boolean minerMay(ServerLevel sl, BlockPos p) {
        return !sl.canSeeSky(p.above()) && !inCapital(p, 3);
    }

    private static boolean hostile(Entity e) {
        if (e instanceof Projectile pr && pr.getOwner() != null) {
            e = pr.getOwner();
        }
        return e instanceof Player || e instanceof Enemy;
    }

    @SubscribeEvent(priority = EventPriority.LOW)
    public static void blast(ExplosionEvent.Detonate e) {
        if (!(e.getLevel() instanceof ServerLevel sl) || e.getAffectedBlocks().isEmpty()) {
            return;
        }
        Entity direct = e.getExplosion().getDirectSourceEntity(), indirect = e.getExplosion().getIndirectSourceEntity();
        if (hostile(indirect) || indirect == null && hostile(direct)) {
            return;
        }
        BlockPos at = BlockPos.containing(e.getExplosion().center());
        if (inCapital(at, 64) || inVillage(sl, at)) {
            e.getAffectedBlocks().clear();
        }
    }
}
