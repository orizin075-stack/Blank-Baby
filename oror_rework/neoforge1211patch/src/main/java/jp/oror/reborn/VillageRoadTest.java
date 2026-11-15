package jp.oror.reborn;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.npc.VillagerProfession;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.server.ServerStoppedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (059g) CI check "roads" (/oror roads test, ROAD-RESULT) of the roads between villages (VillageRoads). Two villages 260
 * blocks apart on open ground away from the capital; the first's trader and two of its people set out for the second
 * with wheat, iron and bread, on the road six times as fast as in play. Only the first village and the road's middle are
 * loaded: the party must walk off, be taken out of the world when its ground unloads, be met on the road where the middle
 * is loaded (and taken out again when that unloads), sell its goods to the second village out of sight (they wait in that
 * village's deliveries), come back with emeralds and wares (into its own village's deliveries), wait outside until its
 * village is loaded again and walk in as the same three villagers, travellers no more.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class VillageRoadTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Village");
    public static volatile boolean resultLogged;
    private static Run run;

    private static final class Run {
        ServerLevel level;
        long started, phaseAt;
        String phase = "walk";
        VillageLedger.Village home, dest;
        VillageProgress.Record homeRec, destRec;
        BlockPos a, b, m;
        final List<ChunkPos> forcedA = new ArrayList<>(), forcedM = new ArrayList<>();
        final List<UUID> folk = new ArrayList<>();
        UUID journey;
        double walked = -1, seenAlong = -1;
        boolean packedOnUnload, seenOnRoad, packedAgain, delivered, paid, earned;
        int destBefore, homeBefore, back, emeralds, payment;
        String wares = "";
        final List<String> phases = new ArrayList<>();
    }

    private VillageRoadTest() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("roads").requires(s -> s.hasPermission(2))
            .then(Commands.literal("test").executes(c -> start(c.getSource())))));
    }

    private static int start(CommandSourceStack src) {
        if (run != null) {
            return 0;
        }
        try {
            return begin(src);
        } catch (RuntimeException ex) {
            LOG.warn("ROAD-TEST failed to start", ex);
            LOG.info("ROAD-RESULT {\"present\":true,\"error\":\"" + ex.toString().replace('"', '\'') + "\",\"pass\":false}");
            resultLogged = true;
            return 0;
        }
    }

    private static int begin(CommandSourceStack src) {
        ServerLevel level = src.getServer().overworld();
        Run r = new Run();
        r.level = level;
        BlockPos a = dry(level, BlockPos.containing(src.getPosition()));
        force(level, a, r.forcedA);
        force(level, a.offset(130, 0, 0), r.forcedM);
        int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, a.getX(), a.getZ());
        a = new BlockPos(a.getX(), y, a.getZ());
        for (int x = -5; x <= 5; x++) {
            for (int z = -5; z <= 5; z++) {
                level.setBlock(a.offset(x, -1, z), Blocks.GRASS_BLOCK.defaultBlockState(), 2);
                for (int h = 0; h < 4; h++) {
                    level.setBlock(a.offset(x, h, z), Blocks.AIR.defaultBlockState(), 2);
                }
            }
        }
        BlockPos b = a.offset(260, 0, 0);
        r.a = a;
        r.b = b;
        r.m = a.offset(130, 0, 0);
        VillageLedger ledger = VillageLedger.get(level);
        VillageProgress progress = VillageProgress.get(level);
        r.home = ledger.register(a);
        r.dest = ledger.register(b);
        ledger.setDirty();
        r.homeRec = progress.of(r.home);
        r.destRec = progress.of(r.dest);
        progress.setDirty();
        r.homeBefore = r.homeRec.deliveries.size();
        r.destBefore = r.destRec.deliveries.size();
        List<Villager> party = new ArrayList<>();
        for (int i = 0; i < 3; i++) {
            Villager v = EntityType.VILLAGER.create(level);
            if (v == null) {
                continue;
            }
            if (i == 0) {
                v.setVillagerData(v.getVillagerData().setProfession(VillagerProfession.FARMER).setLevel(2));
            }
            v.moveTo(a.getX() + 0.5 + (i - 1) * 1.5, a.getY(), a.getZ() + 0.5, -90F, 0F);
            v.setPersistenceRequired();
            v.getPersistentData().putUUID("OrorVillage", r.home.id);
            level.addFreshEntity(v);
            party.add(v);
            r.folk.add(v.getUUID());
        }
        List<ItemStack> cargo = List.of(new ItemStack(Items.WHEAT, 48), new ItemStack(Items.IRON_INGOT, 16), new ItemStack(Items.BREAD, 32));
        VillageRoads.speedup = 6.0;
        VillageRoads.Roads roads = VillageRoads.Roads.of(level);
        roads.next.put(r.home.id, Long.MAX_VALUE);
        roads.next.put(r.dest.id, Long.MAX_VALUE);
        long now = level.getGameTime();
        VillageRoads.Journey j = VillageRoads.dispatch(level, roads, r.home.id, a, r.homeRec.name(),
            new VillageRoads.Target(r.dest.id, b, r.destRec.name(), false), party, cargo, now, "trade");
        r.journey = j.id;
        r.started = now;
        r.phaseAt = now;
        run = r;
        LOG.info("ROAD-TEST-START {\"home\":[{},{},{}],\"dest\":[{},{},{}],\"party\":{}}", a.getX(), a.getY(), a.getZ(), b.getX(), b.getY(), b.getZ(),
            party.size());
        return 1;
    }

    private static void force(ServerLevel level, BlockPos c, List<ChunkPos> into) {
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                ChunkPos p = new ChunkPos((c.getX() >> 4) + dx, (c.getZ() >> 4) + dz);
                if (level.setChunkForced(p.x, p.z, true)) {
                    into.add(p);
                }
            }
        }
    }

    private static void unforce(ServerLevel level, List<ChunkPos> chunks) {
        for (ChunkPos p : chunks) {
            level.setChunkForced(p.x, p.z, false);
        }
        chunks.clear();
    }

    /** Dry, level ground for the two villages and the road between them, well away from the capital. */
    private static BlockPos dry(ServerLevel level, BlockPos from) {
        int[][] offsets = {{2600, 2600}, {-2600, -2600}, {2600, -1600}, {-1600, -2600}, {3000, 0}, {0, 3000}};
        jp.oror.reborn.citadel.CitadelSites.Site capital = jp.oror.reborn.citadel.CitadelSites.capital();
        BlockPos best = from.offset(offsets[0][0], 0, offsets[0][1]);
        int bestScore = Integer.MAX_VALUE;
        for (int[] o : offsets) {
            BlockPos c = from.offset(o[0], 0, o[1]);
            if (capital != null && capital.center().distSqr(new BlockPos(c.getX() + 130, capital.center().getY(), c.getZ())) < 1400 * 1400) {
                continue;
            }
            int lo = Integer.MAX_VALUE, hi = Integer.MIN_VALUE, wet = 0;
            for (int dx = 0; dx <= 260; dx += 26) {
                int h = level.getChunkSource().getGenerator().getBaseHeight(c.getX() + dx, c.getZ(), Heightmap.Types.OCEAN_FLOOR_WG, level,
                    level.getChunkSource().randomState());
                lo = Math.min(lo, h);
                hi = Math.max(hi, h);
                wet += h <= level.getSeaLevel() ? 1 : 0;
            }
            int score = hi - lo + wet * 200;
            if (score < bestScore) {
                bestScore = score;
                best = c;
            }
        }
        return best;
    }

    private static void phase(Run r, String next) {
        r.phases.add("[" + (r.level.getGameTime() - r.started) + ",\"" + next + "\"]");
        r.phase = next;
        r.phaseAt = r.level.getGameTime();
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        Run r = run;
        if (r == null) {
            return;
        }
        long now = r.level.getGameTime(), t = now - r.started, in = now - r.phaseAt;
        VillageRoads.Journey j = VillageRoads.Roads.of(r.level).journeys.get(r.journey);
        switch (r.phase) {
            case "walk" -> {
                if (t >= 120) {
                    Entity lead = j != null && j.lead != null ? r.level.getEntity(j.lead) : null;
                    r.walked = lead != null && j.leg == 0 ? j.along(lead.position()) : -1;
                    unforce(r.level, r.forcedA);
                    phase(r, "unload");
                }
            }
            case "unload" -> {
                if (j != null && "road".equals(j.state)) {
                    r.packedOnUnload = j.packed.size() == r.folk.size();
                    phase(r, "road");
                } else if (in > 600) {
                    phase(r, "road");
                }
            }
            case "road" -> {
                if (j != null && "walking".equals(j.state) && j.leg == 0) {
                    r.seenOnRoad = true;
                    Entity lead = j.lead != null ? r.level.getEntity(j.lead) : null;
                    r.seenAlong = lead != null ? j.along(lead.position()) : -1;
                    unforce(r.level, r.forcedM);
                    phase(r, "leave");
                } else if (j == null || j.leg == 1 || in > 900) {
                    unforce(r.level, r.forcedM);
                    phase(r, "out");
                }
            }
            case "leave" -> {
                if (j != null && "road".equals(j.state)) {
                    r.packedAgain = j.packed.size() == r.folk.size();
                    phase(r, "out");
                } else if (j == null || in > 600) {
                    phase(r, "out");
                }
            }
            case "out" -> {
                if (j == null || j.leg == 1) {
                    r.delivered = r.destRec.deliveries.size() > r.destBefore;
                    if (j != null) {
                        r.emeralds = j.emeralds;
                        r.payment = j.payment;
                        r.paid = j.emeralds > 0 || !j.wares.isEmpty();
                        r.wares = VillageRoads.describe(VillageRoads.stacks(r.level, j.wares));
                    }
                    phase(r, "back");
                } else if (in > 1200) {
                    finish(r, t);
                    return;
                }
            }
            case "back" -> {
                if (j == null || "home".equals(j.state)) {
                    force(r.level, r.a, r.forcedA);
                    phase(r, "homecoming");
                } else if (in > 1200) {
                    finish(r, t);
                    return;
                }
            }
            case "homecoming" -> {
                if (j == null) {
                    for (UUID u : r.folk) {
                        Entity m = r.level.getEntity(u);
                        if (m != null && m.isAlive() && !m.getPersistentData().hasUUID(VillageRoads.KEY) && m.distanceToSqr(r.a.getX(), r.a.getY(), r.a.getZ()) < 32 * 32) {
                            r.back++;
                        }
                    }
                    r.earned = r.homeRec.deliveries.size() > r.homeBefore;
                    finish(r, t);
                    return;
                } else if (in > 600) {
                    finish(r, t);
                    return;
                }
            }
            default -> {
            }
        }
        if (t > 4000) {
            finish(r, t);
        }
    }

    private static void finish(Run r, long t) {
        boolean pass = r.walked > 2 && r.packedOnUnload && r.seenOnRoad && r.packedAgain && r.delivered && r.paid && r.back == r.folk.size() && r.earned;
        LOG.info(String.format(Locale.ROOT, "ROAD-RESULT {\"present\":true,\"seconds\":%.1f,\"phases\":[%s],\"walked\":%.1f,\"packedOnUnload\":%b,"
                + "\"seenOnRoad\":%b,\"seenAlong\":%.0f,\"packedAgain\":%b,\"delivered\":%b,\"payment\":%d,\"emeralds\":%d,\"wares\":\"%s\",\"paid\":%b,"
                + "\"cameBack\":%d,\"of\":%d,\"earned\":%b,\"roads\":%s,\"pass\":%b}",
            t / 20.0, String.join(",", r.phases), r.walked, r.packedOnUnload, r.seenOnRoad, r.seenAlong, r.packedAgain, r.delivered, r.payment,
            r.emeralds, r.wares.replace('"', '\''), r.paid, r.back, r.folk.size(), r.earned, VillageRoads.report(r.level), pass));
        VillageRoads.speedup = 1.0;
        VillageRoads.Roads roads = VillageRoads.Roads.of(r.level);
        roads.journeys.remove(r.journey);
        roads.next.remove(r.home.id);
        roads.next.remove(r.dest.id);
        roads.setDirty();
        for (UUID u : r.folk) {
            Entity m = r.level.getEntity(u);
            if (m != null) {
                m.discard();
            }
        }
        VillageLedger.get(r.level).villages.remove(r.home.id);
        VillageLedger.get(r.level).villages.remove(r.dest.id);
        VillageLedger.get(r.level).setDirty();
        VillageProgress.get(r.level).villages.remove(r.home.id);
        VillageProgress.get(r.level).villages.remove(r.dest.id);
        VillageProgress.get(r.level).setDirty();
        unforce(r.level, r.forcedA);
        unforce(r.level, r.forcedM);
        run = null;
        resultLogged = true;
    }

    @SubscribeEvent
    public static void stopped(ServerStoppedEvent e) {
        run = null;
        VillageRoads.speedup = 1.0;
    }
}
