package jp.oror.reborn.ci;

import com.mojang.authlib.GameProfile;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
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
 * generation (its own height rule and rotation; only its biome is not asked) at a place of its own far out in the
 * overworld, its chunks generated in full and the structure placed in them as /place does. Then StructureAudit's audit
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
            boolean pass = s.placed == s.keys.size() && s.sealsRisen == s.keys.size() && a.floatingTotal == 0 && s.failed.isEmpty();
            LOG.info("GODS-RESULT {\"citadels\":{},\"placed\":{},\"sealsTried\":{},\"godsRisen\":{},\"missing\":{},\"intruding\":{},\"floatingColumns\":{},"
                    + "\"indoor\":{},\"dark\":{},\"failed\":\"{}\",\"ticks\":{},\"pass\":{}}",
                s.keys.size(), s.placed, s.sealsTried, s.sealsRisen, a.missingTotal, a.intrudingTotal, a.floatingTotal, a.indoorTotal, a.darkTotal,
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
                Holder<Structure> holder = level.registryAccess().registryOrThrow(Registries.STRUCTURE).getHolderOrThrow(key);
                ChunkGenerator gen = level.getChunkSource().getGenerator();
                // far out, a place for each, twelve chunks apart
                ChunkPos at = new ChunkPos(1250 + 12 * s.index, 1250);
                StructureStart start = holder.value().generate(level.registryAccess(), gen, gen.getBiomeSource(), level.getChunkSource().randomState(),
                    level.getStructureManager(), level.getSeed(), at, 0, level, b -> true);
                if (start == null || !start.isValid()) {
                    s.failed.add(key.location().getPath() + " (no start)");
                    LOG.info("STRUCT-AUDIT {\"id\":\"{}\",\"found\":false,\"start\":false}", key.location());
                    s.index++;
                    return;
                }
                s.audit.start = start;
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
