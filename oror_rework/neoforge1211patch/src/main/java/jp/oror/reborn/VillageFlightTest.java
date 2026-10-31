package jp.oror.reborn;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.level.levelgen.Heightmap;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.server.ServerStoppedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * The CI check of the villagers' own aircraft (Immersive Aircraft, VillageFlights): /oror villageflight test makes two
 * villages 300 blocks apart on open ground away from the capital, gives the first one the stage of a grown village,
 * a store of the materials an airship and a biplane are built from and goods to trade, and four villagers of its own;
 * then runs the village's flight review every two seconds as the village survey would. The villagers should build the
 * airship, walk to it, board it and fly off with the cargo. VILLAGE-FLIGHT sums up what happened.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class VillageFlightTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Village");
    public static volatile boolean resultLogged;
    private static Run run;

    private static final class Run {
        ServerLevel level;
        long started;
        VillageLedger.Village home, dest;
        VillageProgress.Record rec;
        final List<Villager> folk = new ArrayList<>();
        final List<ChunkPos> forced = new ArrayList<>();
        final List<String> phases = new ArrayList<>();
        String lastPhase = "";
        int maxAboard;
        double maxClimb, maxOut;
        BlockPos center;
        String craftType = "";
    }

    private VillageFlightTest() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("villageflight").requires(s -> s.hasPermission(2))
            .then(Commands.literal("test").executes(c -> start(c.getSource())))));
    }

    private static int start(CommandSourceStack src) {
        if (run != null) {
            src.sendFailure(Component.literal("試験中です。"));
            return 0;
        }
        if (!VillageFlights.present()) {
            LOG.info("VILLAGE-FLIGHT {\"present\":false}");
            resultLogged = true;
            return 0;
        }
        ServerLevel level = src.getServer().overworld();
        Run r = new Run();
        r.level = level;
        BlockPos from = BlockPos.containing(src.getPosition());
        BlockPos a = dry(level, from);
        BlockPos b = a.offset(300, 0, 0);
        for (BlockPos c : new BlockPos[]{a, b}) {
            for (int dx = -3; dx <= 3; dx++) {
                for (int dz = -3; dz <= 3; dz++) {
                    ChunkPos p = new ChunkPos((c.getX() >> 4) + dx, (c.getZ() >> 4) + dz);
                    if (level.setChunkForced(p.x, p.z, true)) {
                        r.forced.add(p);
                    }
                }
            }
        }
        int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, a.getX(), a.getZ());
        a = new BlockPos(a.getX(), y, a.getZ());
        b = new BlockPos(b.getX(), level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, b.getX(), b.getZ()), b.getZ());
        // a level green of 50 x 50, open to the sky, for the village and its airfield
        for (int x = -25; x <= 25; x++) {
            for (int z = -25; z <= 25; z++) {
                level.setBlock(a.offset(x, -1, z), Blocks.GRASS_BLOCK.defaultBlockState(), 2);
                level.setBlock(a.offset(x, -2, z), Blocks.DIRT.defaultBlockState(), 2);
                for (int h = 0; h < 24; h++) {
                    level.setBlock(a.offset(x, h, z), Blocks.AIR.defaultBlockState(), 2);
                }
            }
        }
        r.center = a;
        level.setBlock(a, Blocks.BELL.defaultBlockState(), 3);
        chest(level, a.offset(-2, 0, -3), new Object[][]{{Items.IRON_INGOT, 64}, {Items.COPPER_INGOT, 16}, {Items.WHITE_WOOL, 16},
            {Items.STRING, 32}, {Items.OAK_LOG, 64}, {Items.COBBLESTONE, 64}, {Items.REDSTONE, 16}});
        chest(level, a.offset(2, 0, -3), new Object[][]{{Items.WHEAT, 64}, {Items.WHEAT, 64}, {Items.WHEAT, 64}, {Items.BREAD, 64},
            {Items.BREAD, 64}, {Items.PAPER, 64}, {Items.PAPER, 64}});
        r.home = VillageLedger.get(level).register(a);
        r.dest = VillageLedger.get(level).register(b);
        r.rec = VillageProgress.get(level).of(r.home);
        r.rec.stage = Math.max(r.rec.stage, 3);
        r.rec.nextFlight = 0;
        VillageProgress.get(level).setDirty();
        for (int i = 0; i < 4; i++) {
            Villager v = EntityType.VILLAGER.create(level);
            if (v == null) {
                continue;
            }
            v.moveTo(a.getX() + 0.5 + (i - 1.5) * 2, a.getY(), a.getZ() + 4.5, 0F, 0F);
            v.setPersistenceRequired();
            v.getPersistentData().putUUID("OrorVillage", r.home.id);
            level.addFreshEntity(v);
            r.folk.add(v);
        }
        level.setDayTime(1000);
        r.started = level.getGameTime();
        run = r;
        LOG.info("VILLAGE-FLIGHT-START {\"home\":[{},{},{}],\"dest\":[{},{},{}],\"villagers\":{}}", a.getX(), a.getY(), a.getZ(), b.getX(), b.getY(),
            b.getZ(), r.folk.size());
        src.sendSuccess(() -> Component.literal("村の飛行便の試験を開始しました"), true);
        return 1;
    }

    private static void chest(ServerLevel level, BlockPos at, Object[][] goods) {
        level.setBlock(at, Blocks.CHEST.defaultBlockState(), 3);
        if (level.getBlockEntity(at) instanceof ChestBlockEntity c) {
            for (int i = 0; i < goods.length; i++) {
                c.setItem(i, new ItemStack((Item) goods[i][0], (Integer) goods[i][1]));
            }
        }
    }

    /** Open dry ground 1200 to 1800 blocks off, away from the capital (as the pilot test chooses its field). */
    private static BlockPos dry(ServerLevel level, BlockPos from) {
        int[][] offsets = {{-1200, 1200}, {1200, -1200}, {-1500, 0}, {0, 1500}, {1500, 0}, {0, -1500}, {-1800, -900}, {900, 1800}};
        jp.oror.reborn.citadel.CitadelSites.Site capital = jp.oror.reborn.citadel.CitadelSites.capital();
        BlockPos best = from.offset(offsets[0][0], 0, offsets[0][1]);
        int bestScore = Integer.MAX_VALUE;
        for (int[] o : offsets) {
            BlockPos c = from.offset(o[0], 0, o[1]);
            if (capital != null && capital.center().distSqr(new BlockPos(c.getX() + 150, capital.center().getY(), c.getZ())) < 1200 * 1200) {
                continue;
            }
            int lo = Integer.MAX_VALUE, hi = Integer.MIN_VALUE;
            boolean wet = false;
            for (int dx : new int[]{-25, 0, 25, 300}) {
                for (int dz : new int[]{-25, 0, 25}) {
                    int h = level.getChunkSource().getGenerator().getBaseHeight(c.getX() + dx, c.getZ() + dz, Heightmap.Types.OCEAN_FLOOR_WG, level,
                        level.getChunkSource().randomState());
                    lo = Math.min(lo, h);
                    hi = Math.max(hi, h);
                    wet |= h <= level.getSeaLevel();
                }
            }
            int score = hi - lo + (wet ? 400 : 0);
            if (score < bestScore) {
                bestScore = score;
                best = c;
            }
        }
        return best;
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        Run r = run;
        if (r == null) {
            return;
        }
        long t = r.level.getGameTime() - r.started;
        if (t % 40 == 5) {
            // the village's own review, as its survey runs it
            VillageWork.Survey s = VillageWork.survey(r.level, r.home);
            if (s != null) {
                VillageFlights.review(r.level, s, r.rec);
            }
            if (r.rec.aircraftType != null && !r.rec.aircraftType.isEmpty() && r.craftType.isEmpty()) {
                r.craftType = r.rec.aircraftType;
                r.phases.add("[" + t + ",\"built:" + r.rec.aircraftType + "\"]");
            }
        }
        String phase = r.rec.flight == null ? (r.rec.flights > 0 ? "done" : "none") : r.rec.flight.getString("Phase");
        if (!phase.equals(r.lastPhase)) {
            r.phases.add("[" + t + ",\"" + phase + "\"]");
            r.lastPhase = phase;
        }
        if (r.rec.flight != null && r.rec.flight.hasUUID("Craft") && r.level.getEntity(r.rec.flight.getUUID("Craft")) instanceof Entity craft) {
            int aboard = (int) craft.getPassengers().stream().filter(p -> p instanceof Villager).count();
            r.maxAboard = Math.max(r.maxAboard, aboard);
            r.maxClimb = Math.max(r.maxClimb, craft.getY() - r.center.getY());
            r.maxOut = Math.max(r.maxOut, Math.sqrt(craft.blockPosition().distSqr(r.center)));
            if (t % 100 == 0) {
                LOG.info(String.format(Locale.ROOT, "VILLAGE-FLIGHT-TRACK {\"t\":%d,\"phase\":\"%s\",\"craft\":\"%s\",\"aboard\":%d,\"y\":%.1f,\"out\":%.1f}", t,
                    phase, BuiltInRegistries.ENTITY_TYPE.getKey(craft.getType()), aboard, craft.getY(), Math.sqrt(craft.blockPosition().distSqr(r.center))));
            }
        }
        boolean away = phase.equals("away");
        if (away && t > 200 || t > 3600) {
            int walking = (int) r.folk.stream().filter(v -> v.isAlive() && VillagerLife.data(v).hasUUID("Flight")).count();
            LOG.info(String.format(Locale.ROOT, "VILLAGE-FLIGHT {\"present\":true,\"seconds\":%.1f,\"built\":\"%s\",\"phases\":[%s],\"maxAboard\":%d,"
                    + "\"maxClimb\":%.1f,\"maxOut\":%.1f,\"flights\":%d,\"crewStillAssigned\":%d,\"flewOff\":%b}",
                t / 20.0, r.rec.aircraftType, String.join(",", r.phases), r.maxAboard, r.maxClimb, r.maxOut, r.rec.flights, walking, away));
            resultLogged = true;
            for (ChunkPos p : r.forced) {
                r.level.setChunkForced(p.x, p.z, false);
            }
            run = null;
        }
    }

    @SubscribeEvent
    public static void stopped(ServerStoppedEvent e) {
        run = null;
    }
}
