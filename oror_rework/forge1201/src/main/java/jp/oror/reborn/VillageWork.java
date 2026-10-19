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

    /** v0.17.17: every 10 s, the survey (and its review) of each village with a player within 160 blocks. */
    static void watch(ServerLevel sl) {
        if (sl.getGameTime() % 200L != 51L) {
            return;
        }
        if (sl.players().isEmpty()) {
            return;
        }
        for (VillageLedger.Village v : new ArrayList<>(VillageLedger.get(sl).villages.values())) {
            boolean near = false;
            for (net.minecraft.server.level.ServerPlayer p : sl.players()) {
                near |= !p.isSpectator() && p.blockPosition().distSqr(v.center) < 160.0 * 160.0;
            }
            if (near && sl.hasChunkAt(v.center)) {
                survey(sl, v);
            }
        }
    }

    /** v0.17.16: the latest survey of a village, if one has been made since the server started. */
    static Survey cached(UUID village) {
        return SURVEYS.get(village);
    }
    private static final Map<RecipeManager, Map<ResourceLocation, CraftingRecipe>> BOOK = new WeakHashMap<>();
    /** Natural ground a villager sets things on (not floors, roofs, paths or fields). */
    private static final Set<String> GROUND = Set.of(
        "grass_block", "dirt", "coarse_dirt", "podzol", "rooted_dirt", "mycelium", "mud", "packed_mud", "moss_block", "sand", "red_sand",
        "gravel", "clay", "stone", "cobblestone", "mossy_cobblestone", "andesite", "diorite", "granite", "tuff", "deepslate", "cobbled_deepslate",
        "sandstone", "red_sandstone", "terracotta", "snow_block"
    );
    /** v0.17.15: what a villager hands in to the communal chests whatever it holds (for expeditions, guns and aircraft). */
    private static final Set<String> VILLAGE_GOODS = Set.of(
        "ender_eye", "ender_pearl", "blaze_rod", "blaze_powder", "obsidian", "crying_obsidian", "ancient_debris", "netherite_scrap", "netherite_ingot",
        "gold_ingot", "copper_ingot", "diamond", "gunpowder", "ghast_tear", "magma_cream", "nether_wart", "quartz", "glowstone_dust", "shulker_shell",
        "chorus_fruit", "redstone", "netherite_upgrade_smithing_template", "dragon_breath"
    );
    private static final List<String> JOBS = List.of("composter", "barrel", "fletching_table", "smithing_table", "cartography_table", "loom");

    private VillageWork() {
    }

    /** What a village has and lacks, shared by its villagers. */
    static final class Survey {
        /** v0.17.17: refreshed on every call - a world opened again in the same game has new village objects. */
        VillageLedger.Village village;
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
        /** v0.17.15: what the village has, for its development, expeditions, guns and aircraft. */
        final Map<Item, Integer> stock = new HashMap<>();
        final List<BlockPos> lava = new ArrayList<>();
        final List<BlockPos> spawners = new ArrayList<>();
        int population;
        int strong;
        int miners;
        int raw;
        boolean night;
        long spawnersAt;
        long nextGun;
        BlockPos gateSpot;
        BlockPos pool;

        Survey(VillageLedger.Village village) {
            this.village = village;
        }

        /** How many of a vanilla item the communal chests hold. */
        int stock(String id) {
            return this.stock.getOrDefault(item(id), 0);
        }

        /** How many of a kind of item the communal chests hold. */
        int count(Predicate<ItemStack> is) {
            int n = 0;
            for (Map.Entry<Item, Integer> e : this.stock.entrySet()) {
                if (is.test(e.getKey().getDefaultInstance())) {
                    n += e.getValue();
                }
            }
            return n;
        }
    }

    // ------------------------------------------------------------------------------------- the survey
    static Survey survey(ServerLevel sl, VillageLedger.Village village) {
        Survey s = SURVEYS.computeIfAbsent(village.id, k -> new Survey(village));
        s.village = village;
        long now = sl.getGameTime();
        // v0.17.17: "never surveyed" is its own case - with at = Long.MIN_VALUE, now - at overflowed to a negative
        // number, so this returned the empty survey every time and no village ever saw its chests, dark ground,
        // jobless, homeless or trees (and never reached VillageExpeditions.review)
        if (s.at != Long.MIN_VALUE && now >= s.at && now - s.at < 600L) {
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
        s.stock.clear();
        s.raw = 0;
        for (BlockPos p : s.chests) {
            Container box = VillageReputation.communalChest(sl, village, p);
            for (int i = 0; box != null && i < box.getContainerSize(); i++) {
                ItemStack st = box.getItem(i);
                if (st.isEmpty()) {
                    continue;
                }
                s.wood += st.is(ItemTags.LOGS) ? st.getCount() * 4 : (st.is(ItemTags.PLANKS) ? st.getCount() : 0);
                s.stock.merge(st.getItem(), st.getCount(), Integer::sum);
                if (st.is(net.minecraftforge.common.Tags.Items.RAW_MATERIALS) || st.is(net.minecraftforge.common.Tags.Items.ORES)) {
                    s.raw += st.getCount();
                }
            }
        }
        // surface lava within 32 blocks (water on it makes obsidian)
        s.lava.clear();
        for (int dx = -32; dx <= 32 && s.lava.size() < 8; dx += 2) {
            for (int dz = -32; dz <= 32 && s.lava.size() < 8; dz += 2) {
                BlockPos col = c.offset(dx, 0, dz);
                if (!sl.hasChunkAt(col)) {
                    continue;
                }
                BlockPos p = new BlockPos(col.getX(), sl.getHeight(Types.MOTION_BLOCKING_NO_LEAVES, col.getX(), col.getZ()) - 1, col.getZ());
                if (sl.getFluidState(p).is(net.minecraft.tags.FluidTags.LAVA) && sl.getFluidState(p).isSource()) {
                    s.lava.add(p.immutable());
                }
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
        s.population = 0;
        s.strong = 0;
        s.miners = 0;
        s.night = !sl.isDay();
        for (Villager x : sl.getEntitiesOfClass(Villager.class, new AABB(c).inflate(64.0, 16.0, 64.0), x -> x.isAlive() && !x.isBaby())) {
            if (x.getPersistentData().getBoolean("OrorWanderer") || VillageLedger.of(x) != village) {
                continue;
            }
            s.population++;
            s.strong += VillageAI.strong(x) ? 1 : 0;
            s.miners += VillagerIndustry.miner(x) ? 1 : 0;
            if (x.tickCount <= 1200) {
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
        // v0.17.15: development, expeditions, guns and flights
        VillageExpeditions.review(sl, s);
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

    /** Open ground with nothing solid beside it (for a placed workbench). */
    static boolean open(ServerLevel sl, BlockPos p) {
        return free(sl, p, true);
    }

    static Block campfire() {
        return B.CAMPFIRE;
    }

    /** Put as much of a stack as fits into a container; what is left. */
    static ItemStack insert(Container box, ItemStack st) {
        ItemStack left = st.copy();
        for (int i = 0; i < box.getContainerSize() && !left.isEmpty(); i++) {
            ItemStack in = box.getItem(i);
            if (in.isEmpty()) {
                box.setItem(i, left.copy());
                left = ItemStack.EMPTY;
            } else if (ItemStack.isSameItemSameTags(in, left) && in.getCount() < in.getMaxStackSize()) {
                int n = Math.min(left.getCount(), in.getMaxStackSize() - in.getCount());
                in.grow(n);
                left.shrink(n);
            }
        }
        box.setChanged();
        return left;
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
            // hands full: put the surplus away first; v0.17.17: and when nothing is over what the villager keeps, the
            // biggest stack goes anyway (a pack of eight kept stacks blocked every chore for good)
            return store(v, sl, false) || store(v, sl, true);
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
        if (count(v, i -> i.is(Items.WHEAT)) >= 3 && count(v, i -> i.isEdible()) < 8) {
            todo.add("bread");
        }
        // v0.17.15: what a growing village works toward (VillageExpeditions)
        VillageProgress.Record rec = VillageProgress.get(sl).of(village);
        if (rec.stage >= 3 && rec.gate != null && sl.hasChunkAt(rec.gate) && !VillageExpeditions.gateIntact(sl, rec.gate)) {
            // v0.17.17: a broken gate is forgotten and built anew (before, no more nether trips ever happened)
            rec.gate = null;
            VillageProgress.get(sl).setDirty();
        }
        if (rec.stage >= 3 && rec.gate == null) {
            todo.add("gate");
        }
        if (rec.nethers >= 1 && s.stock("ender_eye") < 12 && (s.stock("blaze_rod") > 0 || s.stock("blaze_powder") > 0) && s.stock("ender_pearl") > 0) {
            todo.add("eyes");
        }
        if (s.stock("ancient_debris") > 0 || s.stock("netherite_scrap") >= 4 && s.stock("gold_ingot") >= 4) {
            todo.add("netherite");
        }
        if (VillageArms.low(v)) {
            todo.add("ammo");
        }
        for (String chore : todo) {
            // baking and a gunner's own ammunition are their own business; the rest go to one villager at a time
            if (!chore.equals("bread") && !chore.equals("ammo") && !claim(s, chore, v, now)) {
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
            case "gate" -> gate(v, sl, s);
            case "eyes" -> {
                int r = obtain(v, sl, s, "blaze_powder", 1);
                if (r == HAVE) {
                    r = obtain(v, sl, s, "ender_pearl", 1);
                }
                yield r == HAVE ? craft(v, sl, "ender_eye") : r;
            }
            case "netherite" -> netherite(v, sl, s);
            case "ammo" -> VillageArms.ammo(v, sl, s);
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

    // ------------------------------------------------------------------------------------- v0.17.15 projects
    /** The nether gate: ten obsidian set block by block into a frame near the centre. */
    private static int gate(Villager v, ServerLevel sl, Survey s) {
        if (s.gateSpot == null) {
            s.gateSpot = VillageExpeditions.gateSpot(v, sl, s);
            if (s.gateSpot == null) {
                return CANNOT;
            }
        }
        BlockPos next = null;
        int done = 0;
        for (BlockPos p : VillageExpeditions.frame(s.gateSpot)) {
            if (sl.getBlockState(p).is(Blocks.OBSIDIAN)) {
                done++;
            } else if (next == null) {
                next = p;
            }
        }
        VillageProgress db = VillageProgress.get(sl);
        if (next == null) {
            db.of(s.village).gate = s.gateSpot;
            db.setDirty();
            s.gateSpot = null;
            VillageProgress.announce(sl, s.village, "村の外れにネザーゲートを建設しました", false);
            return ACTED;
        }
        if (!sl.getBlockState(next).canBeReplaced() || !VillagerLife.editable(v, sl, next)) {
            s.gateSpot = null;
            return CANNOT;
        }
        int r = obtain(v, sl, s, "obsidian", 1);
        if (r != HAVE) {
            return r;
        }
        if (!VillagerLife.nearby(v, next)) {
            return WALK;
        }
        int slot = slot(v, is("obsidian"));
        if (slot < 0 || !VillagerLife.place(v, sl, next, Blocks.OBSIDIAN.defaultBlockState())) {
            return CANNOT;
        }
        v.getInventory().getItem(slot).shrink(1);
        s.village.communal.add(next.asLong());
        done(v, sl, next, "ネザーゲートを建設 " + (done + 1) + "/10");
        return ACTED;
    }

    /** Obsidian from a lava pool: water poured on a source block, the obsidian dug out and the hole filled with cobblestone. */
    private static int cast(Villager v, ServerLevel sl, Survey s) {
        s.lava.removeIf(p -> !sl.hasChunkAt(p) || !sl.getFluidState(p).is(net.minecraft.tags.FluidTags.LAVA) || !sl.getFluidState(p).isSource());
        BlockPos lava = s.lava.stream()
            .filter(p -> VillagerLife.editable(v, sl, p))
            .min(Comparator.comparingDouble(p -> v.distanceToSqr(Vec3.atCenterOf(p))))
            .orElse(null);
        if (lava == null) {
            return CANNOT;
        }
        if (!VillagerLife.nearby(v, lava)) {
            VillagerLife.data(v).putString("Task", "黒曜石を作りに溶岩へ");
            return WALK;
        }
        ItemStack rest = v.getInventory().addItem(Blocks.OBSIDIAN.asItem().getDefaultInstance());
        if (!rest.isEmpty()) {
            return CANNOT;
        }
        sl.setBlock(lava, Blocks.COBBLESTONE.defaultBlockState(), 3);
        s.lava.remove(lava);
        sl.sendParticles(ParticleTypes.LARGE_SMOKE, lava.getX() + 0.5, lava.getY() + 1.0, lava.getZ() + 0.5, 12, 0.3, 0.2, 0.3, 0.02);
        RelicEffects.sound(sl, lava, SoundEvents.FIRE_EXTINGUISH, 1.0F, 1.0F);
        v.swing(InteractionHand.MAIN_HAND);
        VillagerLife.count(v, "Obsidian");
        VillagerLife.data(v).putString("Task", "溶岩に水をかけて黒曜石を掘り出しました");
        return ACTED;
    }

    /** Ancient debris smelted into netherite scrap at a furnace, four scrap and four gold made into an ingot. */
    private static int netherite(Villager v, ServerLevel sl, Survey s) {
        if (count(v, is("netherite_scrap")) + s.stock("netherite_scrap") >= 4 && count(v, is("gold_ingot")) + s.stock("gold_ingot") >= 4) {
            int r = obtain(v, sl, s, "netherite_scrap", 4);
            if (r == HAVE) {
                r = obtain(v, sl, s, "gold_ingot", 4);
            }
            return r == HAVE ? craft(v, sl, "netherite_ingot") : r;
        }
        if (s.furnace == null) {
            return CANNOT;
        }
        int r = obtain(v, sl, s, "ancient_debris", 1);
        if (r != HAVE) {
            return r;
        }
        if (!VillagerLife.nearby(v, s.furnace)) {
            return WALK;
        }
        int slot = slot(v, is("ancient_debris"));
        if (slot < 0) {
            return CANNOT;
        }
        v.getInventory().getItem(slot).shrink(1);
        ItemStack rest = v.getInventory().addItem(item("netherite_scrap").getDefaultInstance());
        if (!rest.isEmpty()) {
            sl.addFreshEntity(new ItemEntity(sl, v.getX(), v.getY() + 0.5, v.getZ(), rest));
        }
        sl.sendParticles(ParticleTypes.LAVA, s.furnace.getX() + 0.5, s.furnace.getY() + 1.0, s.furnace.getZ() + 0.5, 6, 0.2, 0.2, 0.2, 0.0);
        RelicEffects.sound(sl, s.furnace, SoundEvents.ANVIL_USE, 0.6F, 0.8F);
        v.swing(InteractionHand.MAIN_HAND);
        VillagerLife.data(v).putString("Task", "古代の残骸を精錬してネザライトの欠片に");
        return ACTED;
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
            case "cobblestone", "flint", "iron", "paper", "string", "wheat", "ender_pearl", "blaze_rod", "gold_ingot", "netherite_scrap", "ancient_debris",
                "gunpowder":
                return fetch(v, sl, s, is(what), n - have);
            case "obsidian": {
                int r = fetch(v, sl, s, is(what), n - have);
                return r != CANNOT ? r : cast(v, sl, s);
            }
            case "blaze_powder": {
                int r = fetch(v, sl, s, is(what), n - have);
                if (r != CANNOT) {
                    return r;
                }
                r = obtain(v, sl, s, "blaze_rod", 1);
                return r == HAVE ? craft(v, sl, "blaze_powder") : r;
            }
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
        return (Item) BuiltInRegistries.ITEM.get(new ResourceLocation(id));
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

    static int slotOf(Villager v, Predicate<ItemStack> is) {
        return slot(v, is);
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
        return VillagerLife.craft(v, sl, new ResourceLocation(id)) ? ACTED : CANNOT;
    }

    /** The crafting recipes by id, read once per recipe manager (a reload makes a new one). */
    static CraftingRecipe recipe(ServerLevel sl, ResourceLocation id) {
        Map<ResourceLocation, CraftingRecipe> book = BOOK.computeIfAbsent(sl.getRecipeManager(), m -> {
            Map<ResourceLocation, CraftingRecipe> all = new HashMap<>();
            for (CraftingRecipe r : m.getAllRecipesFor(RecipeType.CRAFTING)) {
                all.put(r.getId(), r);
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
        return new ResourceLocation(id.getNamespace(), path + ending);
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
        // v0.17.17: a house already going up (its builder asleep for the night) is not started again by someone else
        UUID builder = s.takers.get("house");
        if (builder != null && !builder.equals(v.getUUID()) && sl.getEntity(builder) instanceof Villager b && b.isAlive()
            && VillagerLife.data(b).contains("BuildOrigin")) {
            return false;
        }
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

    /** No plot found: let the claim go; after 8 failed plots the village sets beds on open ground for ten minutes. */
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
        } else if (st.isEdible()) {
            return 16;
        } else if (st.is(item("flint")) || st.is(item("iron_ingot")) || st.is(item("paper")) || st.is(item("string"))) {
            return 0;
        } else if (st.is(Items.EMERALD)) {
            return 8;
        } else if (VILLAGE_GOODS.contains(BuiltInRegistries.ITEM.getKey(st.getItem()).getPath())) {
            return 0;
        }
        return -1;
    }

    /** The storage phase: carry what is over the villager's keep to the nearest communal chest with room. */
    static boolean store(Villager v, ServerLevel sl) {
        return store(v, sl, false);
    }

    private static boolean store(Villager v, ServerLevel sl, boolean force) {
        VillageLedger.Village village = VillageLedger.of(v);
        if (village == null) {
            return false;
        }
        Survey s = survey(sl, village);
        SimpleContainer inv = v.getInventory();
        // v0.17.17: what a villager fetched for the chore it has taken on stays with it until the chore is done
        boolean busy = s.takers.containsValue(v.getUUID());
        int forced = -1;
        if (force) {
            for (int i = 0; i < inv.getContainerSize(); i++) {
                ItemStack st = inv.getItem(i);
                if (!st.isEmpty() && !MobEquipmentUse.supported(st) && (forced < 0 || st.getCount() > inv.getItem(forced).getCount())) {
                    forced = i;
                }
            }
        }
        for (int i = 0; i < inv.getContainerSize(); i++) {
            ItemStack st = inv.getItem(i);
            if (force && i != forced) {
                continue;
            }
            int keep = st.isEmpty() ? -1 : keep(v, st);
            if (keep < 0 && !force || keep == 0 && busy && !force) {
                continue;
            }
            int over = force ? st.getCount() : Math.min(st.getCount(), count(v, x -> x.is(st.getItem())) - keep);
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
            if (in.isEmpty() || ItemStack.isSameItemSameTags(in, st) && in.getCount() < in.getMaxStackSize()) {
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
