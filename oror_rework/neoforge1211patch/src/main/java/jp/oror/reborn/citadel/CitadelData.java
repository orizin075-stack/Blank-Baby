package jp.oror.reborn.citadel;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.serialization.Codec;
import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.zip.InflaterInputStream;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.NbtIo;
import net.minecraft.nbt.NbtOps;
import net.minecraft.nbt.Tag;
import net.minecraft.util.datafix.DataFixTypes;
import net.minecraft.util.datafix.DataFixers;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.PalettedContainer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * The Grand Citadel v12 save as shipped in the jar (data/oror_supreme_bosses/citadel/v12): one file per region of the
 * save with its chunks (only the parts the generator places: block sections, block entities and entities; sections of
 * nothing but the save's dirt and bedrock are left out, the natural ground stays there), and garrison.json, where the
 * court, the garrison and the townsfolk stand. Coordinates are the save's: the castle stands at x 0, z 0, its grass at
 * y 64, chunks -40..39 on both axes. A chunk is upgraded from the save's Minecraft 1.20.1 data when first used.
 */
public final class CitadelData {
    public static final int CHUNKS = 80;
    public static final int HALF = 40;
    public static final int GROUND = 64;
    public static final int SECTIONS = 12;
    /** Minecraft 1.20.1, the version the save was written by. */
    public static final int DATA_VERSION = 3465;
    /** The king's seat on the gold dais of the throne room, in save coordinates. */
    public static final int THRONE_X = 0, THRONE_Y = 137, THRONE_Z = -32;
    private static final String ROOT = "/data/oror_supreme_bosses/citadel/v12/";
    private static final Logger LOG = LoggerFactory.getLogger("OROR Citadel");
    private static final Codec<PalettedContainer<BlockState>> SECTION = PalettedContainer.codecRW(
        Block.BLOCK_STATE_REGISTRY, BlockState.CODEC, PalettedContainer.Strategy.SECTION_STATES, Blocks.AIR.defaultBlockState());

    /** One upgraded chunk of the save: its sections by section y (null where the save had only ground), block entities and entities. */
    public record Chunk(PalettedContainer<BlockState>[] sections, List<CompoundTag> blockEntities, List<CompoundTag> entities) {
    }

    /** Someone who stands at a post: a royal role (RoyalRole name) or VILLAGER, with the trade for townsfolk. */
    public record Post(String role, int x, int y, int z, float yaw, String post, String profession) {
        public boolean villager() {
            return role.equals("VILLAGER");
        }
    }

    private record Region(byte[] data, Map<Integer, int[]> index, int base) {
    }

    private static final Map<Long, Region> REGIONS = new ConcurrentHashMap<>();
    private static final Map<Long, Chunk> CACHE = Collections.synchronizedMap(new LinkedHashMap<>(128, 0.75F, true) {
        @Override
        protected boolean removeEldestEntry(Map.Entry<Long, Chunk> eldest) {
            return size() > 160;
        }
    });
    private static volatile Map<Long, List<Post>> posts;

    private CitadelData() {
    }

    public static boolean inSave(int sx, int sz) {
        return sx >= -HALF && sx < HALF && sz >= -HALF && sz < HALF;
    }

    /** The save's chunk sx, sz (-40..39), upgraded to this version; null outside the save. */
    public static Chunk chunk(int sx, int sz) {
        if (!inSave(sx, sz)) {
            return null;
        }
        long key = ChunkPos.asLong(sx, sz);
        Chunk c = CACHE.get(key);
        if (c == null) {
            c = load(sx, sz);
            CACHE.put(key, c);
        }
        return c;
    }

    @SuppressWarnings("unchecked")
    private static Chunk load(int sx, int sz) {
        PalettedContainer<BlockState>[] sections = new PalettedContainer[SECTIONS];
        Region region = region(Math.floorDiv(sx, 32), Math.floorDiv(sz, 32));
        int[] at = region == null ? null : region.index.get(Math.floorMod(sx, 32) * 32 + Math.floorMod(sz, 32));
        if (at == null) {
            return new Chunk(sections, List.of(), List.of());
        }
        try (DataInputStream in = new DataInputStream(new InflaterInputStream(new ByteArrayInputStream(region.data, region.base + at[0], at[1])))) {
            CompoundTag tag = NbtIo.read(in);
            CompoundTag entityChunk = tag.getCompound("Entities");
            tag.remove("Entities");
            tag = DataFixTypes.CHUNK.updateToCurrentVersion(DataFixers.getDataFixer(), tag, DATA_VERSION);
            ListTag list = tag.getList("sections", Tag.TAG_COMPOUND);
            for (int i = 0; i < list.size(); i++) {
                CompoundTag s = list.getCompound(i);
                int y = s.getByte("Y");
                if (y >= 0 && y < SECTIONS && s.contains("block_states", Tag.TAG_COMPOUND)) {
                    sections[y] = SECTION.parse(NbtOps.INSTANCE, s.getCompound("block_states"))
                        .resultOrPartial(e -> LOG.error("Citadel chunk {} {} section {}: {}", sx, sz, y, e)).orElse(null);
                }
            }
            List<CompoundTag> blockEntities = new ArrayList<>();
            ListTag bes = tag.getList("block_entities", Tag.TAG_COMPOUND);
            for (int i = 0; i < bes.size(); i++) {
                blockEntities.add(bes.getCompound(i));
            }
            List<CompoundTag> entities = new ArrayList<>();
            if (!entityChunk.isEmpty()) {
                entityChunk = DataFixTypes.ENTITY_CHUNK.updateToCurrentVersion(DataFixers.getDataFixer(), entityChunk, DATA_VERSION);
                ListTag es = entityChunk.getList("Entities", Tag.TAG_COMPOUND);
                for (int i = 0; i < es.size(); i++) {
                    entities.add(es.getCompound(i));
                }
            }
            return new Chunk(sections, blockEntities, entities);
        } catch (IOException | RuntimeException e) {
            LOG.error("Citadel chunk {} {} could not be read", sx, sz, e);
            return new Chunk(sections, List.of(), List.of());
        }
    }

    private static Region region(int rx, int rz) {
        return REGIONS.computeIfAbsent(ChunkPos.asLong(rx, rz), k -> {
            try (InputStream in = CitadelData.class.getResourceAsStream(ROOT + "r." + rx + "." + rz + ".bin")) {
                if (in == null) {
                    return null;
                }
                byte[] data = in.readAllBytes();
                ByteBuffer b = ByteBuffer.wrap(data);
                if (data.length < 10 || !new String(data, 0, 5, StandardCharsets.US_ASCII).equals("OCV12") || data[5] != 1) {
                    LOG.error("Citadel region {} {} has an unknown format", rx, rz);
                    return null;
                }
                int count = b.getInt(6);
                Map<Integer, int[]> index = new HashMap<>();
                for (int i = 0; i < count; i++) {
                    int p = 10 + i * 10;
                    index.put(data[p] * 32 + data[p + 1], new int[]{b.getInt(p + 2), b.getInt(p + 6)});
                }
                return new Region(data, index, 10 + count * 10);
            } catch (IOException e) {
                LOG.error("Citadel region {} {} could not be read", rx, rz, e);
                return null;
            }
        });
    }

    /** The posts in the save's chunk sx, sz. */
    public static List<Post> posts(int sx, int sz) {
        return posts().getOrDefault(ChunkPos.asLong(sx, sz), List.of());
    }

    public static Map<Long, List<Post>> posts() {
        Map<Long, List<Post>> p = posts;
        if (p == null) {
            p = new HashMap<>();
            try (InputStream in = CitadelData.class.getResourceAsStream(ROOT + "garrison.json")) {
                JsonObject root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
                for (JsonElement el : root.getAsJsonArray("entries")) {
                    JsonObject o = el.getAsJsonObject();
                    Post post = new Post(o.get("role").getAsString(), o.get("x").getAsInt(), o.get("y").getAsInt(), o.get("z").getAsInt(),
                        o.get("yaw").getAsFloat(), o.has("post") ? o.get("post").getAsString() : "",
                        o.has("profession") ? o.get("profession").getAsString() : "");
                    p.computeIfAbsent(ChunkPos.asLong(post.x() >> 4, post.z() >> 4), k -> new ArrayList<>()).add(post);
                }
            } catch (IOException | RuntimeException e) {
                LOG.error("Citadel garrison table could not be read", e);
            }
            posts = p;
        }
        return p;
    }
}
