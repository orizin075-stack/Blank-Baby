package jp.oror.reborn.ci;

import com.mojang.authlib.GameProfile;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import com.mojang.datafixers.util.Pair;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.pieces.PiecesContainer;
import net.minecraft.world.level.levelgen.structure.pools.StructurePoolElement;
import net.minecraft.world.level.levelgen.structure.pools.StructureTemplatePool;
import net.minecraft.world.level.levelgen.structure.templatesystem.LiquidSettings;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.PoolElementStructurePiece;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import net.minecraft.world.level.levelgen.structure.pools.SinglePoolElement;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (r63) The 41 gods' citadels, rebuilt (the user: "神々の城塞も点検し直し 多分ひどいから"), as the game builds them: none
 * was ever near enough for the structure audit to find one, so each is started here with the game's own jigsaw
 * generation (its own height rule, rotation and biome rule) at a place of one of its biomes far out in its own
 * dimension, its chunks generated in full and the structure placed in them as /place does. (Run 194 started them all
 * at one row of chunks with any biome let through, and the game gave no start for any; now the reason is logged, and
 * a stage the world would not make is still set out by hand to be looked at, but the test fails.) Then StructureAudit's audit
 * (missing blocks, ground inside, floating columns, dark places to stand) and the god's seal: a player right-clicks it
 * and the god must rise over it (the seal only gives the god up if there is room for it). The god is sent away again.
 * One STRUCT-AUDIT and one GOD-SEAL line for each, then GODS-RESULT.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class GodCitadelTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Structures");
    public static volatile boolean resultLogged;
    private static final int CHUNKS_PER_TICK = 6;
    private static final int SETTLE = 40;
    private static State state;

    private GodCitadelTest() {
    }

    private static final class State {
        final StructureAudit.Run audit = new StructureAudit.Run();
        final List<ResourceKey<Structure>> keys = new ArrayList<>();
        int index;
        int phase;
        int wait;
        List<ChunkPos> chunks = new ArrayList<>();
        int done;
        int placed, sealsRisen, sealsTried;
        final List<String> failed = new ArrayList<>();
        final List<String> notMade = new ArrayList<>();
        int made;
        MinecraftServer server;
        long startedAt;
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("structures").then(Commands.literal("gods")
            .requires(s -> s.hasPermission(2)).executes(c -> start(c.getSource().getServer().overworld())))));
    }

    private static int start(ServerLevel level) {
        if (state != null) {
            return 0;
        }
        State s = new State();
        s.audit.level = level;
        s.server = level.getServer();
        Registry<Structure> reg = level.registryAccess().registryOrThrow(Registries.STRUCTURE);
        for (ResourceKey<Structure> k : reg.registryKeySet()) {
            if (k.location().getNamespace().equals("oror_supreme_bosses") && k.location().getPath().endsWith("_citadel")) {
                s.keys.add(k);
            }
        }
        s.keys.sort((a, b) -> a.location().toString().compareTo(b.location().toString()));
        s.startedAt = level.getGameTime();
        resultLogged = false;
        state = s;
        LOG.info("GODS-START {\"citadels\":{}}", s.keys.size());
        return 1;
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        State s = state;
        if (s == null) {
            return;
        }
        try {
            step(s);
        } catch (Throwable t) {
            LOG.error("GODS failed at {}", s.audit.current, t);
            s.failed.add(String.valueOf(s.audit.current) + " (error " + t + ")");
            release(s);
            s.phase = 0;
            s.index++;
        }
        if (s.index >= s.keys.size() && s.phase == 0) {
            StructureAudit.Run a = s.audit;
            boolean pass = s.made == s.keys.size() && s.placed == s.keys.size() && s.sealsRisen == s.keys.size() && a.floatingTotal == 0
                && s.failed.isEmpty();
            LOG.info("GODS-RESULT {\"citadels\":{},\"made\":{},\"notMade\":\"{}\",\"placed\":{},\"sealsTried\":{},\"godsRisen\":{},\"missing\":{},\"intruding\":{},\"floatingColumns\":{},"
                    + "\"indoor\":{},\"dark\":{},\"failed\":\"{}\",\"ticks\":{},\"pass\":{}}",
                s.keys.size(), s.made, String.join("; ", s.notMade).replace('"', '\''), s.placed, s.sealsTried, s.sealsRisen, a.missingTotal, a.intrudingTotal, a.floatingTotal, a.indoorTotal, a.darkTotal,
                String.join("; ", s.failed).replace('"', '\''), a.level.getGameTime() - s.startedAt, pass);
            resultLogged = true;
            state = null;
        }
    }

    private static void step(State s) {
        ServerLevel level = s.audit.level;
        switch (s.phase) {
            case 0 -> {
                if (s.index >= s.keys.size()) {
                    return;
                }
                ResourceKey<Structure> key = s.keys.get(s.index);
                s.audit.current = key;
                begin(s, key);
                if (s.audit.start == null) {
                    s.index++;
                    return;
                }
                StructureStart start = s.audit.start;
                BoundingBox bb = start.getBoundingBox();
                s.chunks.clear();
                for (int x = (bb.minX() >> 4) - 1; x <= (bb.maxX() >> 4) + 1; x++) {
                    for (int z = (bb.minZ() >> 4) - 1; z <= (bb.maxZ() >> 4) + 1; z++) {
                        s.chunks.add(new ChunkPos(x, z));
                    }
                }
                s.done = 0;
                s.phase = 1;
            }
            case 1 -> {
                for (int i = 0; i < CHUNKS_PER_TICK && s.done < s.chunks.size(); i++, s.done++) {
                    ChunkPos p = s.chunks.get(s.done);
                    level.setChunkForced(p.x, p.z, true);
                    level.getChunk(p.x, p.z);
                }
                if (s.done >= s.chunks.size()) {
                    s.phase = 2;
                }
            }
            case 2 -> {
                StructureStart start = s.audit.start;
                ChunkGenerator gen = level.getChunkSource().getGenerator();
                BoundingBox bb = start.getBoundingBox();
                for (int x = bb.minX() >> 4; x <= bb.maxX() >> 4; x++) {
                    for (int z = bb.minZ() >> 4; z <= bb.maxZ() >> 4; z++) {
                        ChunkPos cp = new ChunkPos(x, z);
                        start.placeInChunk(level, level.structureManager(), gen, level.getRandom(),
                            new BoundingBox(cp.getMinBlockX(), level.getMinBuildHeight(), cp.getMinBlockZ(), cp.getMaxBlockX(), level.getMaxBuildHeight(), cp.getMaxBlockZ()), cp);
                    }
                }
                s.placed++;
                s.wait = SETTLE;
                s.phase = 3;
            }
            case 3 -> {
                // the light engine catches up with the new blocks
                if (--s.wait > 0) {
                    return;
                }
                StructureAudit.audit(s.audit);
                seal(s);
                release(s);
                s.phase = 0;
                s.index++;
            }
            default -> s.phase = 0;
        }
    }

    /**
     * The citadel's start as the world makes it: in the dimension its biomes are of, at a place of one of its biomes
     * (each god its own stretch of land, three thousand blocks apart), with the biome rule the world uses. If the game
     * gives no start there, the reason is looked for and the stage is set out by hand from its pool (so it is still
     * looked at), and the god is counted among those the world would not make.
     */
    private static void begin(State s, ResourceKey<Structure> key) {
        MinecraftServer server = s.server;
        Holder<Structure> holder = server.registryAccess().registryOrThrow(Registries.STRUCTURE).getHolderOrThrow(key);
        Structure structure = holder.value();
        ServerLevel level = server.overworld();
        for (ServerLevel l : server.getAllLevels()) {
            if (l.getChunkSource().getGenerator().getBiomeSource().possibleBiomes().stream().anyMatch(structure.biomes()::contains)) {
                level = l;
                break;
            }
        }
        s.audit.level = level;
        ChunkGenerator gen = level.getChunkSource().getGenerator();
        var randomState = level.getChunkSource().randomState();
        int cx = 20000 + 3000 * (s.index % 7), cz = 20000 + 3000 * (s.index / 7);
        int y = level.dimension() == Level.NETHER ? 34 : 64;
        Pair<BlockPos, Holder<Biome>> found = gen.getBiomeSource().findBiomeHorizontal(cx, y, cz, 1400, 32, structure.biomes()::contains,
            level.getRandom(), true, randomState.sampler());
        String biome = found == null ? "none" : found.getSecond().unwrapKey().map(k -> k.location().toString()).orElse("?");
        ChunkPos at = found == null ? new ChunkPos(cx >> 4, cz >> 4) : new ChunkPos(found.getFirst());
        String path = key.location().getPath();
        StructureStart start = structure.generate(level.registryAccess(), gen, gen.getBiomeSource(), randomState, level.getStructureManager(),
            level.getSeed(), at, 0, level, structure.biomes()::contains);
        String why = "";
        if (start == null || !start.isValid()) {
            StructureStart any = structure.generate(level.registryAccess(), gen, gen.getBiomeSource(), randomState, level.getStructureManager(),
                level.getSeed(), at, 0, level, b -> true);
            why = any != null && any.isValid() ? "biome refused" : "jigsaw gave nothing";
            start = any != null && any.isValid() ? any : byHand(level, structure, path, at);
            if (start == null) {
                why += ", by hand nothing";
            }
            s.notMade.add(path + " (" + why + ", " + biome + ")");
        } else {
            s.made++;
        }
        LOG.info("GOD-START {\"id\":\"{}\",\"dim\":\"{}\",\"biome\":\"{}\",\"chunk\":[{},{}],\"made\":{},\"why\":\"{}\",\"pool\":\"{}\"}", path,
            level.dimension().location(), biome, at.x, at.z, why.isEmpty(), why, why.isEmpty() ? "" : poolInfo(level, path));
        if (start == null) {
            s.failed.add(path + " (no start)");
            LOG.info("STRUCT-AUDIT {\"id\":\"{}\",\"found\":false,\"start\":false}", key.location());
        }
        s.audit.start = start;
    }

    private static String poolInfo(ServerLevel level, String path) {
        try {
            StructureTemplatePool pool = level.registryAccess().registryOrThrow(Registries.TEMPLATE_POOL)
                .get(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", path + "/start_pool"));
            var t = level.getStructureManager().get(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", path));
            return "elements=" + (pool == null ? "no pool" : String.valueOf(pool.size())) + " template="
                + t.map(x -> x.getSize().toShortString()).orElse("none");
        } catch (RuntimeException ex) {
            return String.valueOf(ex).replace('"', '\'');
        }
    }

    /** The stage set out from its pool's element at the ground, as the jigsaw would with no turn. */
    private static StructureStart byHand(ServerLevel level, Structure structure, String path, ChunkPos at) {
        StructureTemplatePool pool = level.registryAccess().registryOrThrow(Registries.TEMPLATE_POOL)
            .get(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", path + "/start_pool"));
        if (pool == null || pool.size() == 0) {
            return null;
        }
        StructurePoolElement el = pool.getRandomTemplate(RandomSource.create(level.getSeed()));
        int x = at.getMinBlockX(), z = at.getMinBlockZ();
        int y = level.dimension() == Level.NETHER ? 34 : level.getChunkSource().getGenerator().getFirstFreeHeight(x + 27, z + 27,
            Heightmap.Types.WORLD_SURFACE_WG, level, level.getChunkSource().randomState());
        BlockPos pos = new BlockPos(x, y, z);
        PoolElementStructurePiece piece = new PoolElementStructurePiece(level.getStructureManager(), el, pos, el.getGroundLevelDelta(), Rotation.NONE,
            el.getBoundingBox(level.getStructureManager(), pos, Rotation.NONE), LiquidSettings.APPLY_WATERLOGGING);
        StructureStart start = new StructureStart(structure, at, 0, new PiecesContainer(List.<StructurePiece>of(piece)));
        return start.isValid() ? start : null;
    }

    private static void release(State s) {
        for (ChunkPos p : s.chunks) {
            s.audit.level.setChunkForced(p.x, p.z, false);
        }
        s.chunks.clear();
        s.audit.start = null;
    }

    /** The seal of the citadel, right-clicked by a player: the god must rise over it. */
    private static void seal(State s) {
        ServerLevel level = s.audit.level;
        String god = s.audit.current.location().getPath().replace("_citadel", "");
        BlockPos at = null;
        BlockState sealState = null;
        for (StructurePiece piece : s.audit.start.getPieces()) {
            if (!(piece instanceof PoolElementStructurePiece pe) || !(pe.getElement() instanceof SinglePoolElement el)) {
                continue;
            }
            try {
                StructureTemplate t = StructureAudit.template(el, level.getStructureManager());
                StructurePlaceSettings settings = new StructurePlaceSettings().setRotation(pe.getRotation());
                for (StructureTemplate.StructureBlockInfo info : StructureAudit.blocks(t)) {
                    if (BuiltInRegistries.BLOCK.getKey(info.state().getBlock()).getPath().endsWith("_boss_seal")) {
                        at = StructureTemplate.calculateRelativePosition(settings, info.pos()).offset(pe.getPosition());
                        sealState = info.state();
                    }
                }
            } catch (ReflectiveOperationException ex) {
                LOG.warn("GODS reflection", ex);
            }
        }
        if (at == null) {
            s.failed.add(god + " (no seal in the template)");
            LOG.info("GOD-SEAL {\"god\":\"{}\",\"seal\":false}", god);
            return;
        }
        s.sealsTried++;
        boolean inWorld = level.getBlockState(at).is(sealState.getBlock());
        FakePlayer p = FakePlayerFactory.get(level, new GameProfile(UUID.nameUUIDFromBytes("oror-gods-test".getBytes()), "[OROR Gods]"));
        p.moveTo(at.getX() + 0.5, at.getY() + 1, at.getZ() + 3.5);
        PlayerInteractEvent.RightClickBlock ev = new PlayerInteractEvent.RightClickBlock(p, InteractionHand.MAIN_HAND, at,
            new BlockHitResult(Vec3.atCenterOf(at), Direction.UP, at, false));
        NeoForge.EVENT_BUS.post(ev);
        boolean gone = !level.getBlockState(at).is(sealState.getBlock());
        List<Entity> risen = level.getEntities((Entity) null, new AABB(at).inflate(8), x -> {
            var k = BuiltInRegistries.ENTITY_TYPE.getKey(x.getType());
            return k.getNamespace().equals("oror_supreme_bosses") && k.getPath().equals(god);
        });
        boolean ok = inWorld && gone && !risen.isEmpty();
        if (ok) {
            s.sealsRisen++;
        } else {
            s.failed.add(god + " (seal " + (inWorld ? "" : "not in world, ") + (gone ? "" : "kept, ") + risen.size() + " risen)");
        }
        LOG.info(String.format(Locale.ROOT, "GOD-SEAL {\"god\":\"%s\",\"at\":\"%d %d %d\",\"sealInWorld\":%s,\"sealTaken\":%s,\"risen\":%d,\"bossAt\":\"%s\",\"ok\":%s}",
            god, at.getX(), at.getY(), at.getZ(), inWorld, gone, risen.size(),
            risen.isEmpty() ? "" : String.format(Locale.ROOT, "%.1f %.1f %.1f", risen.get(0).getX(), risen.get(0).getY(), risen.get(0).getZ()), ok));
        for (Entity x : risen) {
            x.discard();
        }
    }
}
