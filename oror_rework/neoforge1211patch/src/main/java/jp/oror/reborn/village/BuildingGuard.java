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
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.EntityMobGriefingEvent;
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
 * <li>(059f) No hostile mob takes a block of the capital (EntityMobGriefingEvent): an enderman carrying its blocks away,
 * a ravager trampling its hedges and crops, a zombie breaking its doors, a wither tearing through it, a silverfish in
 * its stone. The villagers' own work (their farmers' harvest) is as it was. No fire burns in it either
 * (CapitalFireMixin).</li>
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

    public static int blastsStopped, blocksSpared, griefStopped, firesOut;

    @SubscribeEvent(priority = EventPriority.LOW)
    public static void grief(EntityMobGriefingEvent e) {
        Entity who = e.getEntity();
        if (!e.canGrief() || who == null || who.level().isClientSide || !(who instanceof Enemy || who instanceof net.minecraft.world.entity.boss.wither.WitherBoss)) {
            return;
        }
        if (inCapital(who.blockPosition(), 64)) {
            e.setCanGrief(false);
            griefStopped++;
        }
    }

    /**
     * (058) No explosion takes a block of the capital or of a village, whoever set it off, and none of a god's, the
     * king's or a rebel lord's takes a block anywhere (the user's broken buildings). Until now a player's or a hostile mob's explosion went
     * through (049), and one whose centre lay outside a town took the houses at its edge. Block by block now: what lies
     * in the capital or a village stays; the rest of the crater is as it was. What an explosion does to bodies is not
     * touched.
     */
    @SubscribeEvent(priority = EventPriority.LOW)
    public static void blast(ExplosionEvent.Detonate e) {
        if (!(e.getLevel() instanceof ServerLevel sl) || e.getAffectedBlocks().isEmpty()) {
            return;
        }
        Entity direct = e.getExplosion().getDirectSourceEntity(), indirect = e.getExplosion().getIndirectSourceEntity();
        int before = e.getAffectedBlocks().size();
        if (ororBeing(direct) || ororBeing(indirect)) {
            e.getAffectedBlocks().clear();
        } else {
            BlockPos at = BlockPos.containing(e.getExplosion().center());
            CitadelSites.Site site = CitadelSites.nearest(at, 0);
            VillageLedger.Village village = VillageLedger.get(sl).nearest(at);
            if (site != null || village != null) {
                e.getAffectedBlocks().removeIf(p -> inCapital(p, 64) || village != null && village.contains(p));
            }
        }
        int spared = before - e.getAffectedBlocks().size();
        if (spared > 0) {
            blastsStopped++;
            blocksSpared += spared;
        }
    }

    /** One of OROR's great beings (a god, the king, a rebel lord), or what it shot. */
    private static boolean ororBeing(Entity e) {
        if (e instanceof Projectile pr && pr.getOwner() != null) {
            e = pr.getOwner();
        }
        return e instanceof jp.oror.reborn.SupremeEntity
            || e instanceof jp.oror.reborn.royal.RoyalMob r && r.role() == jp.oror.reborn.royal.RoyalRole.KING
            || e != null && e.getPersistentData().getBoolean("OrorRebelLord");
    }

    // --------------------------------------------------------------------------------------------- the CI check

    public static volatile boolean shieldLogged;

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(net.minecraft.commands.Commands.literal("oror").then(net.minecraft.commands.Commands.literal("shield")
            .then(net.minecraft.commands.Commands.literal("test").requires(s -> s.hasPermission(2)).executes(c -> shieldTest(c.getSource())))));
    }

    /**
     * /oror shield test (059f): over the palace, a fire on a plank goes out at its first tick and the plank stays; a fire
     * on netherrack stays lit; a zombie there may not grief, a villager may as the game rule says, and a zombie far
     * outside the capital may as the rule says. Everything put back as it was. Logged as CAPITAL-SHIELD.
     */
    private static int shieldTest(net.minecraft.commands.CommandSourceStack src) {
        ServerLevel lv = src.getServer().overworld();
        CitadelSites.Site site = CitadelSites.capital();
        boolean rule = lv.getGameRules().getBoolean(net.minecraft.world.level.GameRules.RULE_MOBGRIEFING);
        String spotText = "none";
        boolean fireOut = false, plankKept = false, hearthLit = false, zombieIn = true, villagerIn = !rule, zombieOut = !rule;
        int firesBefore = firesOut, griefBefore = griefStopped;
        if (site != null) {
            BlockPos c = site.center();
            lv.getChunk(c.getX() >> 4, c.getZ() >> 4);
            BlockPos spot = null;
            for (int dy = 0; dy < 160 && spot == null; dy++) {
                BlockPos q = c.above(dy);
                if (lv.getBlockState(q).isAir() && lv.getBlockState(q.above()).isAir() && lv.getBlockState(q.above(2)).isAir()) {
                    spot = q;
                }
            }
            if (spot != null) {
                spotText = spot.toShortString();
                net.minecraft.world.level.block.state.BlockState was0 = lv.getBlockState(spot), was1 = lv.getBlockState(spot.above());
                BlockPos up = spot.above();
                lv.setBlock(spot, net.minecraft.world.level.block.Blocks.OAK_PLANKS.defaultBlockState(), 3);
                lv.setBlock(up, net.minecraft.world.level.block.Blocks.FIRE.defaultBlockState(), 3);
                lv.getBlockState(up).tick(lv, up, lv.random);
                fireOut = !lv.getBlockState(up).is(net.minecraft.world.level.block.Blocks.FIRE);
                plankKept = lv.getBlockState(spot).is(net.minecraft.world.level.block.Blocks.OAK_PLANKS);
                lv.setBlock(spot, net.minecraft.world.level.block.Blocks.NETHERRACK.defaultBlockState(), 3);
                lv.setBlock(up, net.minecraft.world.level.block.Blocks.FIRE.defaultBlockState(), 3);
                lv.getBlockState(up).tick(lv, up, lv.random);
                hearthLit = lv.getBlockState(up).is(net.minecraft.world.level.block.Blocks.FIRE);
                lv.setBlock(up, was1, 3);
                lv.setBlock(spot, was0, 3);
                net.minecraft.world.entity.monster.Zombie z = net.minecraft.world.entity.EntityType.ZOMBIE.create(lv);
                net.minecraft.world.entity.npc.Villager v = net.minecraft.world.entity.EntityType.VILLAGER.create(lv);
                if (z != null && v != null) {
                    z.moveTo(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
                    v.moveTo(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
                    zombieIn = net.neoforged.neoforge.event.EventHooks.canEntityGrief(lv, z);
                    villagerIn = net.neoforged.neoforge.event.EventHooks.canEntityGrief(lv, v);
                    z.moveTo(c.getX() + CitadelSites.SIZE * 16 + 400.5, spot.getY(), c.getZ() + 0.5);
                    zombieOut = net.neoforged.neoforge.event.EventHooks.canEntityGrief(lv, z);
                    z.discard();
                    v.discard();
                }
            }
        }
        boolean pass = site != null && fireOut && plankKept && hearthLit && !zombieIn && villagerIn == rule && zombieOut == rule;
        org.slf4j.LoggerFactory.getLogger("OROR Shield").info("CAPITAL-SHIELD {\"spot\":\"{}\",\"fireOut\":{},\"plankKept\":{},\"hearthLit\":{},"
            + "\"zombieGriefsIn\":{},\"villagerGriefsIn\":{},\"zombieGriefsOut\":{},\"rule\":{},\"firesOut\":{},\"griefStopped\":{},\"pass\":{}}",
            spotText, fireOut, plankKept, hearthLit, zombieIn, villagerIn, zombieOut, rule, firesOut - firesBefore, griefStopped - griefBefore, pass);
        shieldLogged = true;
        return 1;
    }
}
