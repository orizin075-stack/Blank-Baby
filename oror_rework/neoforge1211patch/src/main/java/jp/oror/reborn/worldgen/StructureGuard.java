package jp.oror.reborn.worldgen;

import com.mojang.datafixers.util.Either;
import java.lang.reflect.Field;
import java.util.Arrays;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.PoolElementStructurePiece;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import net.minecraft.world.level.levelgen.structure.pools.SinglePoolElement;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (r63) The walls of OROR's buildings kept whole (the user: "建物の壁とか壊れてる"). The kingdom and the other buildings
 * are placed at the last step of a chunk's decoration, but a chunk decorated later writes its own features (lava lakes
 * and their stone rims, geodes, fossils, dungeons, trees) up to a chunk into its neighbours, through the buildings
 * already standing there: holes in the walls (the structure audit: stone bricks gone to air, stone, bone block).
 * <p>
 * Each OROR piece's box is known once its structure start is made (or loaded); while a world-generation region writes a
 * block inside one of them, the write is refused unless it is an OROR piece placing itself (its template, its clearing
 * and its footing).
 */
@net.neoforged.fml.common.EventBusSubscriber(modid = "oror_supreme_bosses")
public final class StructureGuard {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Structures");
    private static final ConcurrentHashMap<Long, BoundingBox[]> BOXES = new ConcurrentHashMap<>();
    private static final ThreadLocal<int[]> PLACING = ThreadLocal.withInitial(() -> new int[1]);
    public static final AtomicLong REFUSED = new AtomicLong(), STARTS = new AtomicLong();
    private static Field templateField;
    private static volatile boolean failed, said;

    private StructureGuard() {
    }

    /** Another world opened next (single player) must not keep this one's boxes. */
    @net.neoforged.bus.api.SubscribeEvent
    public static void stopped(net.neoforged.neoforge.event.server.ServerStoppedEvent e) {
        BOXES.clear();
    }

    /** The template a pool element places, if it is one of OROR's. */
    public static boolean oror(SinglePoolElement el) {
        if (failed) {
            return false;
        }
        try {
            if (templateField == null) {
                Field f = SinglePoolElement.class.getDeclaredField("template");
                f.setAccessible(true);
                templateField = f;
            }
            @SuppressWarnings("unchecked")
            Either<ResourceLocation, ?> e = (Either<ResourceLocation, ?>) templateField.get(el);
            ResourceLocation id = e.left().orElse(null);
            return id != null && id.getNamespace().equals("oror_supreme_bosses");
        } catch (ReflectiveOperationException | RuntimeException ex) {
            failed = true;
            LOG.warn("STRUCT-GUARD off: {}", ex.toString());
            return false;
        }
    }

    public static boolean oror(StructurePiece piece) {
        return piece instanceof PoolElementStructurePiece pe && pe.getElement() instanceof SinglePoolElement el && oror(el);
    }

    /** A structure start made or loaded: its OROR pieces' boxes, by the chunks they cross. */
    public static void started(StructureStart start) {
        boolean any = false;
        for (StructurePiece piece : start.getPieces()) {
            if (!oror(piece)) {
                continue;
            }
            any = true;
            BoundingBox b = piece.getBoundingBox();
            for (int cx = b.minX() >> 4; cx <= b.maxX() >> 4; cx++) {
                for (int cz = b.minZ() >> 4; cz <= b.maxZ() >> 4; cz++) {
                    BOXES.compute(ChunkPos.asLong(cx, cz), (k, old) -> {
                        if (old == null) {
                            return new BoundingBox[] {b};
                        }
                        for (BoundingBox o : old) {
                            if (o.equals(b)) {
                                return old;
                            }
                        }
                        BoundingBox[] n = Arrays.copyOf(old, old.length + 1);
                        n[old.length] = b;
                        return n;
                    });
                }
            }
        }
        if (any) {
            STARTS.incrementAndGet();
            if (!said) {
                said = true;
                LOG.info("STRUCT-GUARD on (first start {})", start.getChunkPos());
            }
        }
    }

    public static void placing(StructurePiece piece) {
        if (oror(piece)) {
            PLACING.get()[0]++;
        }
    }

    public static void placed(StructurePiece piece) {
        int[] n = PLACING.get();
        if (n[0] > 0 && oror(piece)) {
            n[0]--;
        }
    }

    /** Whether a world-generation write at the place is to be refused. */
    public static boolean refuse(BlockPos pos) {
        if (BOXES.isEmpty() || PLACING.get()[0] > 0) {
            return false;
        }
        BoundingBox[] boxes = BOXES.get(ChunkPos.asLong(pos.getX() >> 4, pos.getZ() >> 4));
        if (boxes == null) {
            return false;
        }
        for (BoundingBox b : boxes) {
            if (b.isInside(pos)) {
                REFUSED.incrementAndGet();
                return true;
            }
        }
        return false;
    }
}
