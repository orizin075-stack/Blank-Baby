package jp.oror.reborn;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.WeakHashMap;
import java.util.function.Predicate;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.ItemTags;
import net.minecraft.world.Container;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.animal.Sheep;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.CraftingRecipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeManager;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.LightLayer;
import net.minecraft.world.level.block.BedBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.ChestBlock;
import net.minecraft.world.level.block.DoorBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BedPart;
import net.minecraft.world.level.levelgen.Heightmap.Types;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * Village work that gets done (v0.17.14). Before, the craft phase tried 24 random recipes a second and made whatever
 * happened to match (and shaped recipes smaller than 3x3 never matched at all), building waited for 32 oak planks nobody
 * made, villagers took random stacks out of chests, and nobody made or set down torches, campfires, job blocks or beds.
 * Now villagers work toward what their village lacks:
 * - every 30 seconds a look around the village (Survey): its communal chests and what wood they hold, a campfire and a
 *   furnace near the centre, dark ground where monsters could spawn, unemployed and homeless villagers, trees to fell;
 * - chores in order of need, each taken by one villager at a time: a communal chest, a campfire, a job block for an
 *   unemployed villager (composter, barrel, or a fletching, smithing or cartography table or loom as the materials allow),
 *   a bed when there is nowhere to build, torches on dark ground, bread from wheat; a house with a bed, a door and a chest
 *   for the homeless (VillagerLife.build);
 * - each thing is made from real recipes (logs into planks, sticks, slabs, doors, beds...) step by step, with what the
 *   villager lacks taken from the communal chests, logs from the trees around the village, charcoal burnt from logs at a
 *   furnace, smoker, blast furnace or the campfire, and wool shorn from the village's sheep;
 * - surplus goes back to the communal chests, which are kept sorted.
 * A step is one action a second (VillagerLife.tick); walking somewhere goes through VillagerLife's goal.
 */
public final class VillageWork {
    /** Results of a step: done something, already had it, walking there, not possible now. */
    static final int ACTED = 2;
    static final int HAVE = 1;
    static final int WALK = 0;
    static final int CANNOT = -1;
    private static final Map<UUID, Survey> SURVEYS = new HashMap<>();
    private static final Map<RecipeManager, Map<ResourceLocation, RecipeHolder<CraftingRecipe>>> BOOK = new WeakHashMap<>();
    /** Natural ground a villager sets things on (not floors, roofs, paths or fields). */
    private static final Set<String> GROUND = Set.of(
        "grass_block", "dirt", "coarse_dirt", "podzol", "rooted_dirt", "mycelium", "mud", "packed_mud", "moss_block", "sand", "red_sand",
        "gravel", "clay", "stone", "cobblestone", "mossy_cobblestone", "andesite", "diorite", "granite", "tuff", "deepslate", "cobbled_deepslate",
        "sandstone", "red_sandstone", "terracotta", "snow_block"
    );
    private static final List<String> JOBS = List.of("composter", "barrel", "fletching_table", "smithing_table", "cartography_table", "loom");

    private VillageWork() {
    }

    /** What a village has and lacks, shared by its villagers. */
    static final class Survey {
        final VillageLedger.Village village;
        final List<BlockPos> chests = new ArrayList<>();
        final List<BlockPos> dark = new ArrayList<>();
        final List<BlockPos> trees = new ArrayList<>();
        final Map<String, Long> claims = new HashMap<>();
        final Map<String, UUID> takers = new HashMap<>();
        BlockPos campfire;
        BlockPos furnace;
        int wood;
        int unemployed;
        int homeless;
        int jobs;
        long at = Long.MIN_VALUE;
        long jobAt;
        long bedAt;
        long siteless;
        int misses;

        Survey(VillageLedger.Village village) {
            this.village = village;
        }
    }

    // ------------------------------------------------------------------------------------- the survey
    static Survey survey(ServerLevel sl, VillageLedger.Village village) {
        Survey s = SURVEYS.computeIfAbsent(village.id, k -> new Survey(village));
        long now = sl.getGameTime();
        if (now >= s.at && now - s.at < 600L) {
            return s;
        }
        s.at = now;
        s.chests.clear();
        s.dark.clear();
        s.trees.clear();
        s.campfire = null;
        s.furnace = null;
        s.wood = 0;
        BlockPos c = village.center;
        // chests, a campfire and a furnace in the square around the centre
        for (int dx = -16; dx <= 16; dx++) {
            for (int dz = -16; dz <= 16; dz++) {
                BlockPos col = c.offset(dx, 0, dz);
                if (!sl.hasChunkAt(col)) {
                    continue;
                }
                for (int dy = -4; dy <= 4; dy++) {
                    BlockPos p = col.offset(0, dy, 0);
                    BlockState st = sl.getBlockState(p);
                    if (st.isAir()) {
                        continue;
                    }
                    if (st.getBlock() instanceof ChestBlock) {
                        if (s.chests.size() < 16 && VillageReputation.communalChest(sl, village, p) != null) {
                            s.chests.add(p.immutable());
                        }
                    } else if (fire(st)) {
                        if (s.campfire == null || c.distSqr(p) < c.distSqr(s.campfire)) {
                            s.campfire = p.immutable();
                        }
                    } else if (furnace(st) && (s.furnace == null || c.distSqr(p) < c.distSqr(s.furnace))) {
                        s.furnace = p.immutable();
                    }
                }
            }
        }
        // chests farther out that the village built (in its houses)
        for (long l : new ArrayList<>(village.communal)) {
            if (s.chests.size() >= 16) {
                break;
            }
            BlockPos p = BlockPos.of(l);
            if (!s.chests.contains(p) && sl.hasChunkAt(p) && sl.getBlockState(p).getBlock() instanceof ChestBlock && VillageReputation.communalChest(sl, village, p) != null) {
                s.chests.add(p);
            }
        }
        for (BlockPos p : s.chests) {
            Container box = VillageReputation.communalChest(sl, village, p);
            for (int i = 0; box != null && i < box.getContainerSize(); i++) {
                ItemStack st = box.getItem(i);
                s.wood += st.is(ItemTags.LOGS) ? st.getCount() * 4 : (st.is(ItemTags.PLANKS) ? st.getCount() : 0);
            }
        }
        // dark ground (block light under 4) within 24 blocks, where a torch can stand
        for (int dx = -24; dx <= 24; dx += 3) {
            for (int dz = -24; dz <= 24; dz += 3) {
                if (dx * dx + dz * dz > 576 || s.dark.size() >= 24) {
                    continue;
                }
                BlockPos p = top(sl, c.offset(dx, 0, dz));
                if (p != null && Math.abs(p.getY() - c.getY()) <= 6 && free(sl, p, false) && sl.getBrightness(LightLayer.BLOCK, p) < 4) {
                    s.dark.add(p);
                }
            }
        }
        // trees 10-32 blocks out: the base log of each trunk on natural ground
        for (int dx = -32; dx <= 32; dx++) {
            for (int dz = -32; dz <= 32; dz++) {
                if (Math.abs(dx) < 10 && Math.abs(dz) < 10) {
                    continue;
                }
                BlockPos col = c.offset(dx, 0, dz);
                if (!sl.hasChunkAt(col)) {
                    continue;
                }
                BlockPos p = new BlockPos(col.getX(), sl.getHeight(Types.MOTION_BLOCKING_NO_LEAVES, col.getX(), col.getZ()) - 1, col.getZ());
                if (!sl.getBlockState(p).is(BlockTags.LOGS)) {
                    continue;
                }
                for (int i = 0; i < 24 && sl.getBlockState(p.below()).is(BlockTags.LOGS); i++) {
                    p = p.below();
                }
                if (VillagerLife.naturalTree(sl, p) && !VillageReputation.villageOwned(sl, p)) {
                    s.trees.add(p.immutable());
                }
            }
        }
        s.trees.sort(Comparator.comparingDouble(c::distSqr));
        if (s.trees.size() > 12) {
            s.trees.subList(12, s.trees.size()).clear();
        }
        s.unemployed = 0;
        s.homeless = 0;
        for (Villager x : sl.getEntitiesOfClass(Villager.class, new AABB(c).inflate(64.0, 16.0, 64.0), x -> x.isAlive() && !x.isBaby() && x.tickCount > 1200)) {
            if (VillageLedger.of(x) != village) {
                continue;
            }
            if (VillagerRoles.profession(x).equals("none")) {
                s.unemployed++;
            }
            if (x.getBrain().getMemory(MemoryModuleType.HOME).isEmpty()) {
                s.homeless++;
            }
            java.util.Optional<?> job = x.getBrain().getMemory(MemoryModuleType.JOB_SITE);
            if (s.furnace == null && job.isPresent() && job.get() instanceof net.minecraft.core.GlobalPos g && g.dimension().equals(sl.dimension())
                && sl.hasChunkAt(g.pos()) && furnace(sl.getBlockState(g.pos()))) {
                s.furnace = g.pos();
            }
        }
        return s;
    }

    /** Blocks looked up by id once the registries are filled (first use is in a running world). */
    private static final class B {
        static final Block CAMPFIRE = block("campfire");
        static final Block SOUL_CAMPFIRE = block("soul_campfire");
        static final Block SMOKER = block("smoker");
        static final Block BLAST_FURNACE = block("blast_furnace");
        static final Block TORCH = block("torch");
    }

    private static boolean fire(BlockState st) {
        return st.is(B.CAMPFIRE) || st.is(B.SOUL_CAMPFIRE);
    }

    private static boolean furnace(BlockState st) {
        return st.is(Blocks.FURNACE) || st.is(B.SMOKER) || st.is(B.BLAST_FURNACE);
    }

    /** The first open block over the ground at p's column, if loaded. */
    private static BlockPos top(ServerLevel sl, BlockPos p) {
        if (!sl.hasChunkAt(p)) {
            return null;
        }
        return new BlockPos(p.getX(), sl.getHeight(Types.MOTION_BLOCKING_NO_LEAVES, p.getX(), p.getZ()), p.getZ());
    }

    /**
     * Open ground: room for a block and a head over natural ground where a torch could stand (so not a roof, floor, path or
     * field), not by a door; with roomy, nothing solid beside it either.
     */
    private static boolean free(ServerLevel sl, BlockPos p, boolean roomy) {
        if (!sl.getBlockState(p).canBeReplaced() || !sl.getBlockState(p.above()).canBeReplaced() || !sl.getFluidState(p).isEmpty()) {
            return false;
        }
        if (!natural(sl.getBlockState(p.below())) || !B.TORCH.defaultBlockState().canSurvive(sl, p)) {
            return false;
        }
        for (BlockPos q : BlockPos.betweenClosed(p.offset(-1, 0, -1), p.offset(1, 1, 1))) {
            BlockState st = sl.getBlockState(q);
            if (st.getBlock() instanceof DoorBlock || st.getBlock() instanceof BedBlock || roomy && !st.canBeReplaced()) {
                return false;
            }
        }
        return true;
    }

    /** Natural ground: soil, sand, gravel or stone (not a floor, a roof, a path or a field). */
    static boolean natural(BlockState st) {
        return GROUND.contains(BuiltInRegistries.ITEM.getKey(st.getBlock().asItem()).getPath());
    }

    // ------------------------------------------------------------------------------------- chores
    /** The chores phase: the first thing the village lacks that this villager can work toward. True when it did a step. */
    static boolean chores(Villager v, ServerLevel sl) {
        VillageLedger.Village village = VillageLedger.of(v);
        if (village == null) {
            return false;
        }
        Survey s = survey(sl, village);
        long now = sl.getGameTime();
        if (!roomy(v)) {
            // hands full: put the surplus away first
            return store(v, sl);
        }
        List<String> todo = new ArrayList<>();
        if (s.chests.isEmpty()) {
            todo.add("chest");
        }
        if (s.campfire == null) {
            todo.add("campfire");
        }
        if (s.unemployed > 0 && now >= s.jobAt) {
            todo.add("job");
        }
        if (s.homeless > 0 && now >= s.bedAt && (s.village.houses >= 12 || now < s.siteless)) {
            todo.add("bed");
        }
        if (!s.dark.isEmpty()) {
            todo.add("torch");
        }
        if (count(v, i -> i.is(Items.WHEAT)) >= 3 && count(v, i -> i.has(DataComponents.FOOD)) < 8) {
            todo.add("bread");
        }
        for (String chore : todo) {
            // baking is the baker's own business; the rest go to one villager at a time
            if (!chore.equals("bread") && !claim(s, chore, v, now)) {
                continue;
            }
            int r = chore(v, sl, s, chore, now);
            if (r == ACTED) {
                return true;
            }
            if (r == WALK) {
                return false;
            }
            release(s, chore, v);
        }
        return false;
    }

    private static int chore(Villager v, ServerLevel sl, Survey s, String chore, long now) {
        return switch (chore) {
            case "chest" -> set(v, sl, s, chore, "chest", 2, 7, true);
            case "campfire" -> set(v, sl, s, chore, "campfire", 3, 8, true);
            case "job" -> {
                String job = job(v, sl, s);
                yield job == null ? CANNOT : set(v, sl, s, chore, job, 5, 14, true);
            }
            case "bed" -> bed(v, sl, s);
            case "torch" -> set(v, sl, s, chore, "torch", 0, 0, false);
            case "bread" -> craft(v, sl, "bread");
            default -> CANNOT;
        };
    }

    /** One villager at a time on a chore (for a minute after its last step). */
    private static boolean claim(Survey s, String chore, Villager v, long now) {
        UUID taker = s.takers.get(chore);
        if (taker != null && !taker.equals(v.getUUID()) && s.claims.getOrDefault(chore, 0L) > now) {
            return false;
        }
        s.takers.put(chore, v.getUUID());
        s.claims.put(chore, now + 1200L);
        return true;
    }

    private static void release(Survey s, String chore, Villager v) {
        if (v.getUUID().equals(s.takers.get(chore))) {
            s.takers.remove(chore);
            s.claims.remove(chore);
        }
    }

    /** Which job block to make: one the materials allow (those that need more than wood first), in turn. */
    private static String job(Villager v, ServerLevel sl, Survey s) {
        CompoundTag n = VillagerLife.data(v);
        if (n.getString("Chore").equals("job") && JOBS.contains(n.getString("ChoreItem"))) {
            return n.getString("ChoreItem");
        }
        List<String> can = new ArrayList<>();
        for (String job : JOBS) {
            String raw = switch (job) {
                case "fletching_table" -> "flint";
                case "smithing_table" -> "iron";
                case "cartography_table" -> "paper";
                case "loom" -> "string";
                default -> null;
            };
            if (raw == null || count(v, is(raw)) >= 2 || stocked(sl, s, is(raw), 2)) {
                can.add(job);
            }
        }
        String job = can.get(Math.floorMod(s.jobs, can.size()));
        n.putString("ChoreItem", job);
        return job;
    }

    /** Make (or fetch) one of what, then set it down on open ground min-max blocks from the centre (a dark spot for torches). */
    private static int set(Villager v, ServerLevel sl, Survey s, String chore, String what, int min, int max, boolean roomy) {
        int r = obtain(v, sl, s, what, 1);
        if (r != HAVE) {
            return r;
        }
        CompoundTag n = VillagerLife.data(v);
        BlockPos p = n.getString("Chore").equals(chore) && n.contains("ChoreSpot") ? BlockPos.of(n.getLong("ChoreSpot")) : null;
        if (p == null || !free(sl, p, roomy)) {
            p = chore.equals("torch") ? dark(v, sl, s) : spot(v, sl, s, min, max, roomy);
            if (p == null) {
                return CANNOT;
            }
            n.putString("Chore", chore);
            n.putLong("ChoreSpot", p.asLong());
        }
        if (!VillagerLife.nearby(v, p)) {
            return WALK;
        }
        int slot = slot(v, is(what));
        if (slot < 0 || !(v.getInventory().getItem(slot).getItem() instanceof BlockItem item)) {
            return CANNOT;
        }
        if (!VillagerLife.place(v, sl, p, item.getBlock().defaultBlockState())) {
            n.remove("ChoreSpot");
            return CANNOT;
        }
        v.getInventory().getItem(slot).shrink(1);
        n.remove("Chore");
        n.remove("ChoreSpot");
        n.remove("ChoreItem");
        s.village.communal.add(p.asLong());
        VillageLedger.get(sl).setDirty();
        BlockPos at = p;
        switch (chore) {
            case "chest" -> s.chests.add(p);
            case "campfire" -> s.campfire = p;
            case "job" -> {
                s.jobs++;
                s.jobAt = sl.getGameTime() + 2400L;
                s.unemployed = Math.max(0, s.unemployed - 1);
            }
            case "torch" -> s.dark.removeIf(q -> q.distSqr(at) < 49.0);
            default -> {
            }
        }
        release(s, chore, v);
        done(v, sl, p, "設置：" + item.getDefaultInstance().getHoverName().getString());
        VillagerLife.count(v, "Placed");
        return ACTED;
    }

    /** A bed on open ground when the village has stopped building houses (both halves need room). */
    private static int bed(Villager v, ServerLevel sl, Survey s) {
        int r = obtain(v, sl, s, "bed", 1);
        if (r != HAVE) {
            return r;
        }
        CompoundTag n = VillagerLife.data(v);
        BlockPos p = n.getString("Chore").equals("bed") && n.contains("ChoreSpot") ? BlockPos.of(n.getLong("ChoreSpot")) : null;
        if (p == null || !free(sl, p, true)) {
            p = spot(v, sl, s, 4, 12, true);
            if (p == null) {
                return CANNOT;
            }
            n.putString("Chore", "bed");
            n.putLong("ChoreSpot", p.asLong());
        }
        for (Direction d : Direction.Plane.HORIZONTAL) {
            BlockPos head = p.relative(d);
            if (!free(sl, head, false)) {
                continue;
            }
            if (!VillagerLife.nearby(v, p)) {
                return WALK;
            }
            int slot = slot(v, is("bed"));
            if (slot < 0 || !(v.getInventory().getItem(slot).getItem() instanceof BlockItem item)) {
                return CANNOT;
            }
            BlockState foot = (BlockState) ((BlockState) item.getBlock().defaultBlockState().setValue(BedBlock.FACING, d)).setValue(BedBlock.PART, BedPart.FOOT);
            if (!VillagerLife.placePair(v, sl, p, foot, head, (BlockState) foot.setValue(BedBlock.PART, BedPart.HEAD))) {
                return CANNOT;
            }
            v.getInventory().getItem(slot).shrink(1);
            n.remove("Chore");
            n.remove("ChoreSpot");
            s.village.communal.add(p.asLong());
            s.village.communal.add(head.asLong());
            VillageLedger.get(sl).setDirty();
            s.bedAt = sl.getGameTime() + 2400L;
            s.homeless = Math.max(0, s.homeless - 1);
            release(s, "bed", v);
            done(v, sl, p, "ベッドを設置");
            VillagerLife.count(v, "Placed");
            return ACTED;
        }
        n.remove("ChoreSpot");
        return CANNOT;
    }

    /** Open ground min-max blocks from the centre, near its height. */
    private static BlockPos spot(Villager v, ServerLevel sl, Survey s, int min, int max, boolean roomy) {
        BlockPos c = s.village.center;
        for (int i = 0; i < 12; i++) {
            double a = sl.random.nextDouble() * Math.PI * 2.0;
            double r = min + sl.random.nextDouble() * (max - min);
            BlockPos p = top(sl, c.offset((int) Math.round(Math.cos(a) * r), 0, (int) Math.round(Math.sin(a) * r)));
            if (p != null && Math.abs(p.getY() - c.getY()) <= 3 && free(sl, p, roomy) && VillagerLife.editable(v, sl, p)) {
                return p;
            }
        }
        return null;
    }

    /** The dark spot nearest the villager that is still dark. */
    private static BlockPos dark(Villager v, ServerLevel sl, Survey s) {
        s.dark.removeIf(p -> !sl.hasChunkAt(p) || sl.getBrightness(LightLayer.BLOCK, p) >= 4 || !free(sl, p, false));
        return s.dark.stream()
            .filter(p -> VillagerLife.editable(v, sl, p))
            .min(Comparator.comparingDouble(p -> v.distanceToSqr(Vec3.atCenterOf(p))))
            .orElse(null);
    }

    // ------------------------------------------------------------------------------------- getting things
    /**
     * One step toward having n of something: HAVE when the villager holds them, ACTED after a step (a craft, a fetch, a
     * fell, a shearing, a burn), WALK while walking to where the step happens, CANNOT for now.
     */
    static int obtain(Villager v, ServerLevel sl, Survey s, String what, int n) {
        int have = count(v, is(what));
        if (have >= n) {
            return HAVE;
        }
        switch (what) {
            case "logs": {
                int r = fetch(v, sl, s, is(what), n - have);
                return r != CANNOT ? r : fell(v, sl, s);
            }
            case "planks": {
                if (saw(v, sl)) {
                    return ACTED;
                }
                int r = fetch(v, sl, s, i -> i.is(ItemTags.PLANKS) || i.is(ItemTags.LOGS), Math.max(4, n - have));
                return r != CANNOT ? r : fell(v, sl, s);
            }
            case "sticks": {
                int r = obtain(v, sl, s, "planks", 2);
                return r == HAVE ? craft(v, sl, "stick") : r;
            }
            case "slabs": {
                int r = obtain(v, sl, s, "planks", 3);
                return r == HAVE ? wooden(v, sl, s, "_slab", 3) : r;
            }
            case "door": {
                int r = obtain(v, sl, s, "planks", 6);
                return r == HAVE ? wooden(v, sl, s, "_door", 6) : r;
            }
            case "bed": {
                int r = obtain(v, sl, s, "wool", 3);
                if (r != HAVE) {
                    return r;
                }
                r = obtain(v, sl, s, "planks", 3);
                if (r != HAVE) {
                    return r;
                }
                for (ItemStack st : v.getInventory().getItems()) {
                    if (st.is(ItemTags.WOOL) && count(v, i -> i.is(st.getItem())) >= 3) {
                        String colour = BuiltInRegistries.ITEM.getKey(st.getItem()).getPath().replace("_wool", "");
                        return craft(v, sl, colour + "_bed");
                    }
                }
                // three of one colour
                return obtain(v, sl, s, "wool", count(v, is("wool")) + 1);
            }
            case "fuel": {
                int r = fetch(v, sl, s, is(what), 4);
                if (r != CANNOT) {
                    return r;
                }
                BlockPos kiln = s.furnace != null ? s.furnace : s.campfire;
                r = obtain(v, sl, s, "logs", kiln == null ? 2 : 1);
                return r == HAVE ? burn(v, sl, kiln) : r;
            }
            case "wool": {
                int r = fetch(v, sl, s, is(what), n - have);
                return r != CANNOT ? r : shear(v, sl);
            }
            case "cobblestone", "flint", "iron", "paper", "string", "wheat":
                return fetch(v, sl, s, is(what), n - have);
            default: {
                // made at the crafting table from what it takes, gathered in this order
                String[] needs = switch (what) {
                    case "chest" -> new String[]{"planks:8"};
                    case "torch" -> new String[]{"sticks:1", "fuel:1"};
                    case "campfire" -> new String[]{"sticks:3", "logs:3", "fuel:1"};
                    case "composter" -> new String[]{"slabs:7"};
                    case "barrel" -> new String[]{"planks:6", "slabs:2"};
                    case "fletching_table" -> new String[]{"flint:2", "planks:4"};
                    case "smithing_table" -> new String[]{"iron:2", "planks:4"};
                    case "cartography_table" -> new String[]{"paper:2", "planks:4"};
                    case "loom" -> new String[]{"string:2", "planks:2"};
                    default -> null;
                };
                if (needs == null) {
                    return CANNOT;
                }
                for (String need : needs) {
                    String[] part = need.split(":");
                    int r = obtain(v, sl, s, part[0], Integer.parseInt(part[1]));
                    if (r != HAVE) {
                        return r;
                    }
                }
                return craft(v, sl, what);
            }
        }
    }

    /** What a material or a made thing looks like in the inventory. */
    static Predicate<ItemStack> is(String what) {
        return switch (what) {
            case "logs" -> i -> i.is(ItemTags.LOGS);
            case "planks" -> i -> i.is(ItemTags.PLANKS);
            case "slabs" -> i -> i.is(ItemTags.WOODEN_SLABS);
            case "sticks" -> i -> i.is(Items.STICK);
            case "fuel" -> i -> i.is(Items.COAL) || i.is(Items.CHARCOAL);
            case "wool" -> i -> i.is(ItemTags.WOOL);
            case "door" -> i -> i.is(ItemTags.WOODEN_DOORS);
            case "bed" -> i -> i.is(ItemTags.BEDS);
            case "cobblestone" -> i -> i.is(Items.COBBLESTONE) || i.is(item("cobbled_deepslate"));
            case "iron" -> i -> i.is(item("iron_ingot"));
            default -> {
                Item item = item(what);
                yield i -> !i.isEmpty() && i.is(item);
            }
        };
    }

    private static Item item(String id) {
        return (Item) BuiltInRegistries.ITEM.get(ResourceLocation.withDefaultNamespace(id));
    }

    private static Block block(String id) {
        return item(id) instanceof BlockItem b ? b.getBlock() : Blocks.AIR;
    }

    static int count(Villager v, Predicate<ItemStack> is) {
        int n = 0;
        for (ItemStack st : v.getInventory().getItems()) {
            if (!st.isEmpty() && is.test(st)) {
                n += st.getCount();
            }
        }
        return n;
    }

    private static int slot(Villager v, Predicate<ItemStack> is) {
        SimpleContainer inv = v.getInventory();
        for (int i = 0; i < inv.getContainerSize(); i++) {
            if (!inv.getItem(i).isEmpty() && is.test(inv.getItem(i))) {
                return i;
            }
        }
        return -1;
    }

    /** At least one free slot in the villager's eight. */
    private static boolean roomy(Villager v) {
        for (ItemStack st : v.getInventory().getItems()) {
            if (st.isEmpty()) {
                return true;
            }
        }
        return false;
    }

    /** A crafting step by vanilla recipe id. */
    private static int craft(Villager v, ServerLevel sl, String id) {
        return VillagerLife.craft(v, sl, ResourceLocation.withDefaultNamespace(id)) ? ACTED : CANNOT;
    }

    /** The crafting recipes by id, read once per recipe manager (a reload makes a new one). */
    static RecipeHolder<CraftingRecipe> recipe(ServerLevel sl, ResourceLocation id) {
        Map<ResourceLocation, RecipeHolder<CraftingRecipe>> book = BOOK.computeIfAbsent(sl.getRecipeManager(), m -> {
            Map<ResourceLocation, RecipeHolder<CraftingRecipe>> all = new HashMap<>();
            for (RecipeHolder<CraftingRecipe> r : m.getAllRecipesFor(RecipeType.CRAFTING)) {
                all.put(r.id(), r);
            }
            return all;
        });
        return book.get(id);
    }

    /** The id of the same wood's item with another ending: oak_log, stripped_oak_wood or oak_planks to oak_planks / oak_door. */
    private static ResourceLocation wood(ItemStack st, String ending) {
        ResourceLocation id = BuiltInRegistries.ITEM.getKey(st.getItem());
        String path = id.getPath();
        if (path.startsWith("stripped_")) {
            path = path.substring(9);
        }
        for (String end : List.of("_planks", "_log", "_wood", "_stem", "_hyphae", "_block")) {
            if (path.endsWith(end)) {
                path = path.substring(0, path.length() - end.length());
                break;
            }
        }
        return ResourceLocation.fromNamespaceAndPath(id.getNamespace(), path + ending);
    }

    /** Saw a log into planks of its own wood. */
    private static boolean saw(Villager v, ServerLevel sl) {
        for (ItemStack st : List.copyOf(v.getInventory().getItems())) {
            if (st.is(ItemTags.LOGS) && VillagerLife.craft(v, sl, wood(st, "_planks"))) {
                return true;
            }
        }
        return false;
    }

    /** Slabs or a door from planks of one wood (a door takes six of the same kind). */
    private static int wooden(Villager v, ServerLevel sl, Survey s, String ending, int per) {
        for (ItemStack st : List.copyOf(v.getInventory().getItems())) {
            if (st.is(ItemTags.PLANKS) && count(v, i -> i.is(st.getItem())) >= per && VillagerLife.craft(v, sl, wood(st, ending))) {
                return ACTED;
            }
        }
        // planks of mixed woods: saw some more
        return obtain(v, sl, s, "planks", count(v, is("planks")) + 4);
    }

    /** Take up to want of something from the nearest communal chest that holds it, walking there first. */
    static int fetch(Villager v, ServerLevel sl, Survey s, Predicate<ItemStack> is, int want) {
        BlockPos best = null;
        double far = Double.MAX_VALUE;
        for (BlockPos p : s.chests) {
            Container box = VillageReputation.communalChest(sl, s.village, p);
            if (box != null && holds(box, is) && v.distanceToSqr(Vec3.atCenterOf(p)) < far) {
                far = v.distanceToSqr(Vec3.atCenterOf(p));
                best = p;
            }
        }
        if (best == null) {
            return CANNOT;
        }
        if (!VillagerLife.nearby(v, best)) {
            return WALK;
        }
        Container box = VillageReputation.communalChest(sl, s.village, best);
        SimpleContainer inv = v.getInventory();
        int moved = 0;
        String name = null;
        for (int i = 0; box != null && i < box.getContainerSize() && moved < Math.max(1, want); i++) {
            ItemStack st = box.getItem(i);
            if (st.isEmpty() || !is.test(st) || !inv.canAddItem(st)) {
                continue;
            }
            ItemStack taken = box.removeItem(i, Math.min(Math.max(1, want) - moved, st.getCount()));
            name = taken.getHoverName().getString();
            ItemStack rest = inv.addItem(taken);
            moved += taken.getCount() - rest.getCount();
            if (!rest.isEmpty()) {
                // what did not fit goes back
                ItemStack left = box.getItem(i);
                if (left.isEmpty()) {
                    box.setItem(i, rest);
                } else {
                    left.grow(rest.getCount());
                }
            }
        }
        if (moved == 0) {
            return CANNOT;
        }
        box.setChanged();
        VillagerLife.count(v, "Supplies");
        VillagerLife.data(v).putString("Task", "共有チェストから取り出し：" + name);
        v.swing(InteractionHand.MAIN_HAND);
        return ACTED;
    }

    private static boolean holds(Container box, Predicate<ItemStack> is) {
        for (int i = 0; i < box.getContainerSize(); i++) {
            if (!box.getItem(i).isEmpty() && is.test(box.getItem(i))) {
                return true;
            }
        }
        return false;
    }

    /** Some communal chest holds at least n of it. */
    private static boolean stocked(ServerLevel sl, Survey s, Predicate<ItemStack> is, int n) {
        int got = 0;
        for (BlockPos p : s.chests) {
            Container box = VillageReputation.communalChest(sl, s.village, p);
            for (int i = 0; box != null && i < box.getContainerSize(); i++) {
                if (!box.getItem(i).isEmpty() && is.test(box.getItem(i))) {
                    got += box.getItem(i).getCount();
                }
            }
        }
        return got >= n;
    }

    /** Fell a tree close by, else walk to the nearest one around the village. */
    private static int fell(Villager v, ServerLevel sl, Survey s) {
        if (VillagerLife.lumber(v, sl)) {
            return ACTED;
        }
        s.trees.removeIf(p -> !sl.hasChunkAt(p) || !sl.getBlockState(p).is(BlockTags.LOGS));
        BlockPos tree = s.trees.stream().min(Comparator.comparingDouble(p -> v.distanceToSqr(Vec3.atCenterOf(p)))).orElse(null);
        if (tree == null) {
            return CANNOT;
        }
        if (VillagerLife.nearby(v, tree)) {
            // there, yet nothing came down (not a natural tree after all, or protected): strike it off
            s.trees.remove(tree);
            return CANNOT;
        }
        VillagerLife.data(v).putString("Task", "木を切りに行く");
        return WALK;
    }

    /**
     * Burn a log into charcoal at the village's furnace, smoker, blast furnace or campfire; a village with none burns two
     * logs in a pit where the villager stands.
     */
    private static int burn(Villager v, ServerLevel sl, BlockPos kiln) {
        if (kiln != null && !furnace(sl.getBlockState(kiln)) && !fire(sl.getBlockState(kiln))) {
            kiln = null;
        }
        if (kiln != null && !VillagerLife.nearby(v, kiln)) {
            return WALK;
        }
        int logs = kiln == null ? 2 : 1;
        if (count(v, is("logs")) < logs) {
            return CANNOT;
        }
        for (int i = 0; i < logs; i++) {
            v.getInventory().getItem(slot(v, is("logs"))).shrink(1);
        }
        if (kiln == null) {
            kiln = v.blockPosition();
        }
        ItemStack rest = v.getInventory().addItem(Items.CHARCOAL.getDefaultInstance());
        if (!rest.isEmpty()) {
            sl.addFreshEntity(new ItemEntity(sl, v.getX(), v.getY() + 0.5, v.getZ(), rest));
        }
        sl.sendParticles(ParticleTypes.LARGE_SMOKE, kiln.getX() + 0.5, kiln.getY() + 1.1, kiln.getZ() + 0.5, 6, 0.2, 0.2, 0.2, 0.01);
        sl.sendParticles(ParticleTypes.FLAME, kiln.getX() + 0.5, kiln.getY() + 0.8, kiln.getZ() + 0.5, 4, 0.15, 0.1, 0.15, 0.01);
        RelicEffects.sound(sl, kiln, SoundEvents.CAMPFIRE_CRACKLE, 1.0F, 1.0F);
        v.swing(InteractionHand.MAIN_HAND);
        VillagerLife.count(v, "Charcoal");
        VillagerLife.data(v).putString("Task", "炭焼き");
        return ACTED;
    }

    /** Shear the nearest sheep that has wool. */
    private static int shear(Villager v, ServerLevel sl) {
        Sheep sheep = sl.getEntitiesOfClass(Sheep.class, v.getBoundingBox().inflate(24.0, 6.0, 24.0), Sheep::readyForShearing)
            .stream()
            .min(Comparator.comparingDouble(v::distanceToSqr))
            .orElse(null);
        if (sheep == null) {
            return CANNOT;
        }
        if (!VillagerLife.nearby(v, sheep.blockPosition())) {
            VillagerLife.data(v).putString("Task", "羊の毛を刈りに行く");
            return WALK;
        }
        sheep.setSheared(true);
        ItemStack wool = item(sheep.getColor().getName() + "_wool").getDefaultInstance().copyWithCount(1 + sl.random.nextInt(3));
        ItemStack rest = v.getInventory().addItem(wool);
        if (!rest.isEmpty()) {
            sl.addFreshEntity(new ItemEntity(sl, v.getX(), v.getY() + 0.5, v.getZ(), rest));
        }
        RelicEffects.sound(sl, sheep.blockPosition(), SoundEvents.SHEEP_SHEAR, 1.0F, 1.0F);
        v.swing(InteractionHand.MAIN_HAND);
        VillagerLife.count(v, "Shorn");
        VillagerLife.data(v).putString("Task", "羊の毛を刈りました");
        return ACTED;
    }

    private static void done(Villager v, ServerLevel sl, BlockPos p, String task) {
        v.swing(InteractionHand.MAIN_HAND);
        RelicEffects.sound(sl, p, SoundEvents.WOOD_PLACE, 1.0F, 1.0F);
        sl.sendParticles(ParticleTypes.HAPPY_VILLAGER, p.getX() + 0.5, p.getY() + 0.8, p.getZ() + 0.5, 4, 0.3, 0.3, 0.3, 0.0);
        VillagerLife.data(v).putString("Task", task);
    }

    // ------------------------------------------------------------------------------------- the house builder's needs
    /** A homeless villager in the village and room for another house (VillagerLife.build), with wood to hand or trees near. */
    static boolean wantsHouse(Villager v, ServerLevel sl) {
        VillageLedger.Village village = VillageLedger.of(v);
        if (village == null || village.houses >= 12) {
            return false;
        }
        Survey s = survey(sl, village);
        int wood = count(v, is("planks")) + count(v, is("logs")) * 4 + s.wood;
        return s.homeless > 0 && (wood >= 40 || !s.trees.isEmpty()) && claim(s, "house", v, sl.getGameTime());
    }

    /** Keep the house claim while building, let it go when done. */
    static void building(Villager v, ServerLevel sl, boolean still) {
        VillageLedger.Village village = VillageLedger.of(v);
        if (village == null) {
            return;
        }
        Survey s = survey(sl, village);
        if (still) {
            claim(s, "house", v, sl.getGameTime());
        } else {
            release(s, "house", v);
            s.homeless = Math.max(0, s.homeless - 1);
        }
    }

    /** No plot found: let the claim go; after 32 failed plots the village sets beds on open ground for ten minutes. */
    static void noSite(Villager v, ServerLevel sl) {
        VillageLedger.Village village = VillageLedger.of(v);
        if (village == null) {
            return;
        }
        Survey s = survey(sl, village);
        release(s, "house", v);
        if (++s.misses >= 8) {
            s.misses = 0;
            s.siteless = sl.getGameTime() + 12000L;
        }
    }

    /** One step toward n of a building material (planks, door, bed, chest). */
    static int supply(Villager v, ServerLevel sl, String what, int n) {
        VillageLedger.Village village = VillageLedger.of(v);
        return village == null ? CANNOT : obtain(v, sl, survey(sl, village), what, n);
    }

    /** Wood is wanted while the village's chests and the villager's hands hold little, or a house is going up. */
    static boolean wantsWood(Villager v, ServerLevel sl) {
        VillageLedger.Village village = VillageLedger.of(v);
        if (village == null) {
            return false;
        }
        Survey s = survey(sl, village);
        return VillagerLife.data(v).contains("BuildOrigin") || s.wood + count(v, is("planks")) + count(v, is("logs")) * 4 < 256;
    }

    /** A farmer without seeds takes some from the chests. */
    static int seeds(Villager v, ServerLevel sl) {
        VillageLedger.Village village = VillageLedger.of(v);
        if (village == null) {
            return CANNOT;
        }
        return fetch(v, sl, survey(sl, village), i -> i.is(Items.WHEAT_SEEDS) || i.is(Items.CARROT) || i.is(Items.POTATO) || i.is(Items.BEETROOT_SEEDS), 16);
    }

    // ------------------------------------------------------------------------------------- storage
    /** How many of a thing a villager keeps on hand; -1 for things that are not the village's to store. */
    private static int keep(Villager v, ItemStack st) {
        boolean farmer = VillagerRoles.profession(v).equals("farmer");
        if (st.is(ItemTags.LOGS)) {
            return 16;
        } else if (st.is(ItemTags.PLANKS)) {
            return 32;
        } else if (st.is(ItemTags.WOODEN_SLABS) || st.is(Items.STICK) || st.is(Items.COAL) || st.is(Items.CHARCOAL) || st.is(item("torch"))) {
            return 8;
        } else if (st.is(ItemTags.WOOL)) {
            return 6;
        } else if (st.is(ItemTags.SAPLINGS)) {
            return 4;
        } else if (st.is(Items.COBBLESTONE)) {
            return 16;
        } else if (st.is(Items.WHEAT_SEEDS) || st.is(Items.BEETROOT_SEEDS) || st.is(Items.BONE_MEAL)) {
            return farmer ? 32 : 0;
        } else if (st.is(Items.WHEAT)) {
            return 16;
        } else if (st.has(DataComponents.FOOD)) {
            return 16;
        } else if (st.is(item("flint")) || st.is(item("iron_ingot")) || st.is(item("paper")) || st.is(item("string"))) {
            return 0;
        }
        return -1;
    }

    /** The storage phase: carry what is over the villager's keep to the nearest communal chest with room. */
    static boolean store(Villager v, ServerLevel sl) {
        VillageLedger.Village village = VillageLedger.of(v);
        if (village == null) {
            return false;
        }
        Survey s = survey(sl, village);
        SimpleContainer inv = v.getInventory();
        for (int i = 0; i < inv.getContainerSize(); i++) {
            ItemStack st = inv.getItem(i);
            int keep = st.isEmpty() ? -1 : keep(v, st);
            if (keep < 0) {
                continue;
            }
            int over = Math.min(st.getCount(), count(v, x -> x.is(st.getItem())) - keep);
            if (over <= 0) {
                continue;
            }
            BlockPos best = null;
            double far = Double.MAX_VALUE;
            for (BlockPos p : s.chests) {
                Container box = VillageReputation.communalChest(sl, village, p);
                if (box != null && fits(box, st) && v.distanceToSqr(Vec3.atCenterOf(p)) < far) {
                    far = v.distanceToSqr(Vec3.atCenterOf(p));
                    best = p;
                }
            }
            if (best == null) {
                return false;
            }
            if (!VillagerLife.nearby(v, best)) {
                return false;
            }
            Container box = VillageReputation.communalChest(sl, village, best);
            SimpleContainer after = VillagerLife.copy(box);
            ItemStack rest = after.addItem(st.copyWithCount(over));
            int stored = over - rest.getCount();
            if (stored <= 0) {
                return false;
            }
            for (int j = 0; j < box.getContainerSize(); j++) {
                box.setItem(j, after.getItem(j));
            }
            st.shrink(stored);
            box.setChanged();
            VillagerLife.count(v, "Stored");
            VillagerLife.data(v).putString("Task", "共有チェストに収納");
            v.swing(InteractionHand.MAIN_HAND);
            return true;
        }
        return false;
    }

    private static boolean fits(Container box, ItemStack st) {
        for (int i = 0; i < box.getContainerSize(); i++) {
            ItemStack in = box.getItem(i);
            if (in.isEmpty() || ItemStack.isSameItemSameComponents(in, st) && in.getCount() < in.getMaxStackSize()) {
                return true;
            }
        }
        return false;
    }

    /** The tidy phase: sort the nearest communal chest that is out of order. */
    static boolean tidy(Villager v, ServerLevel sl) {
        VillageLedger.Village village = VillageLedger.of(v);
        if (village == null) {
            return false;
        }
        Survey s = survey(sl, village);
        BlockPos best = null;
        double far = Double.MAX_VALUE;
        for (BlockPos p : s.chests) {
            Container box = VillageReputation.communalChest(sl, village, p);
            if (box != null && !VillagerLife.sorted(box) && v.distanceToSqr(Vec3.atCenterOf(p)) < far) {
                far = v.distanceToSqr(Vec3.atCenterOf(p));
                best = p;
            }
        }
        if (best == null || !VillagerLife.nearby(v, best)) {
            return false;
        }
        Container box = VillageReputation.communalChest(sl, village, best);
        if (box == null || !VillagerLife.sort(box)) {
            return false;
        }
        VillagerLife.count(v, "Sorted");
        VillagerLife.data(v).putString("Task", "共有チェストを整理");
        v.swing(InteractionHand.MAIN_HAND);
        return true;
    }

    /** Raw materials a villager picks up off the ground for the village's work. */
    static boolean material(ItemStack st) {
        return st.is(ItemTags.WOOL) || st.is(item("flint")) || st.is(item("string")) || st.is(item("iron_ingot")) || st.is(item("paper"))
            || st.is(item("torch"));
    }
}
