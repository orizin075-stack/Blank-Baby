package jp.oror.reborn;

import com.mojang.authlib.GameProfile;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.NonNullList;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.FluidTags;
import net.minecraft.tags.ItemTags;
import net.minecraft.world.Container;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.ai.memory.WalkTarget;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.TieredItem;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.CraftingRecipe;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.item.crafting.ShapedRecipe;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.block.BedBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.DoorBlock;
import net.minecraft.world.level.block.FarmBlock;
import net.minecraft.world.level.block.LeavesBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BedPart;
import net.minecraft.world.level.block.state.properties.DoubleBlockHalf;
import net.minecraft.world.level.levelgen.Heightmap.Types;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.common.util.BlockSnapshot;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.event.level.BlockEvent.BreakEvent;
import net.neoforged.neoforge.event.level.BlockEvent.EntityPlaceEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent.Post;

public final class VillagerLife {
    private static final Map<ServerLevel, long[]> BUDGET = new WeakHashMap<>();
    private static final List<VillagerLife.BuildPart> HOUSE = plan();

    public static CompoundTag data(Villager v) {
        CompoundTag n = v.getPersistentData();
        if (!n.contains("OrorLife", 10)) {
            n.put("OrorLife", new CompoundTag());
        }

        return n.getCompound("OrorLife");
    }

    public static void count(Villager v, String key) {
        CompoundTag n = data(v);
        n.putInt(key, Math.min(2147483646, n.getInt(key)) + 1);
    }

    public static String status(Villager v) {
        CompoundTag n = data(v);
        return n.getString("Task")
            + " / 収穫 "
            + n.getInt("Harvests")
            + " 製作 "
            + n.getInt("Crafts")
            + " 伐採 "
            + n.getInt("Logs")
            + " 建築 "
            + n.getInt("Built")
            + " 交易 "
            + n.getInt("Trades")
            + " 信仰 "
            + n.getString("Faith");
    }

    private static boolean take(ServerLevel sl) {
        long[] a = BUDGET.computeIfAbsent(sl, k -> new long[]{-1L, 0L});
        if (a[0] != sl.getGameTime()) {
            a[0] = sl.getGameTime();
            a[1] = 0L;
        }

        return a[1]++ < (long)((Integer)RebornConfig.VILLAGE_BUDGET.get()).intValue();
    }

    public static void tick(Post e) {
        if (e.getEntity() instanceof Villager v
            && v.level() instanceof ServerLevel sl
            && (Boolean)RebornConfig.VILLAGE_LIFE.get()
            && !v.isBaby()
            && v.isAlive()
            && !v.isNoAi()
            && v.tickCount % 20 == Math.floorMod(v.getId(), 20)) {
            VillageLedger.of(v);
            if (!take(sl)) {
                return;
            }

            consume(v);
            if (AdaptiveCombat.enemy(v, v.getTarget())) {
                data(v).putString("Task", "村を防衛");
                return;
            }

            if (VillagerIndustry.miner(v)) {
                return;
            }

            pickup(v, sl);
            equip(v);
            int phase = Math.floorMod((int)(sl.getGameTime() / 20L) + v.getId(), 8);

            boolean changed = switch (phase) {
                case 0 -> farm(v, sl);
                case 1 -> lumber(v, sl);
                case 2 -> craft(v, sl, null);
                case 3 -> build(v, sl);
                case 4 -> storage(v, sl, false);
                case 5 -> trade(v, sl);
                case 6 -> pray(v, sl);
                default -> storage(v, sl, true);
            };
            if (!changed) {
                data(v).putString("Task", "素材や仕事を探しています");
            }

            return;
        }
    }

    private static void pickup(Villager v, ServerLevel sl) {
        for (ItemEntity item : sl.getEntitiesOfClass(ItemEntity.class, v.getBoundingBox().inflate(3.0), i -> i.isAlive() && !i.hasPickUpDelay() && wanted(i.getItem()))
            .stream()
            .limit(8L)
            .toList()) {
            ItemStack rest = v.getInventory().addItem(item.getItem().copy());
            if (rest.getCount() != item.getItem().getCount()) {
                item.setItem(rest);
                if (rest.isEmpty()) {
                    item.discard();
                }

                count(v, "Pickups");
            }
        }
    }

    /** Materials a villager uses for farming, crafting and building; tools, gear and loot stay on the ground. */
    private static boolean wanted(ItemStack s) {
        if (s.isEmpty() || s.isDamageableItem()) {
            return false;
        } else {
            return s.has(DataComponents.FOOD)
                || s.is(ItemTags.LOGS)
                || s.is(ItemTags.PLANKS)
                || s.is(ItemTags.SAPLINGS)
                || s.is(Items.WHEAT)
                || s.is(Items.WHEAT_SEEDS)
                || s.is(Items.BEETROOT_SEEDS)
                || s.is(Items.COBBLESTONE)
                || s.is(Items.STICK)
                || s.is(Items.COAL)
                || s.is(Items.CHARCOAL)
                || s.is(Items.BONE_MEAL);
        }
    }

    private static void equip(Villager v) {
        if (!MobEquipmentUse.supported(v.getMainHandItem())) {
            SimpleContainer inv = v.getInventory();

            for (int i = 0; i < inv.getContainerSize(); i++) {
                ItemStack item = inv.getItem(i);
                if (MobEquipmentUse.supported(item)) {
                    ItemStack old = v.getMainHandItem();
                    if (!old.isEmpty() && !inv.canAddItem(old)) {
                        return;
                    }

                    ItemStack next = inv.removeItem(i, 1);
                    if (!old.isEmpty()) {
                        inv.addItem(old);
                    }

                    v.setItemInHand(InteractionHand.MAIN_HAND, next);
                    CompoundTag n = MobMind.data(v);
                    n.remove("OriginalWeapon");
                    n.remove("Selected");
                    n.putBoolean("OriginalAuto", false);
                    n.putString("Weapon", MobEquipmentUse.kind(next));
                    return;
                }
            }
        }
    }

    public static boolean consume(Villager v) {
        if (v.getHealth() >= v.getMaxHealth() * 0.85F) {
            return false;
        } else {
            SimpleContainer inv = v.getInventory();

            for (int i = 0; i < inv.getContainerSize(); i++) {
                ItemStack stack = inv.getItem(i);
                if (stack.has(DataComponents.FOOD)) {
                    v.heal((float)Math.max(2, ((FoodProperties)stack.get(DataComponents.FOOD)).nutrition()));
                    stack.shrink(1);
                    v.swing(InteractionHand.MAIN_HAND);
                    count(v, "Meals");
                    return true;
                }

                if (stack.is(Items.POTION)) {
                    ItemStack used = stack.copyWithCount(1).finishUsingItem(v.level(), v);
                    stack.shrink(1);
                    if (!used.isEmpty()) {
                        inv.addItem(used);
                    }

                    count(v, "Potions");
                    return true;
                }
            }

            return false;
        }
    }

    private static boolean editable(Villager v, ServerLevel sl, BlockPos p) {
        VillageLedger.Village village = VillageLedger.of(v);
        return sl.getGameRules().getBoolean(GameRules.RULE_MOBGRIEFING)
            && sl.hasChunkAt(p)
            && sl.getWorldBorder().isWithinBounds(p)
            && village != null
            && village.contains(p)
            && !village.property.containsKey(p.asLong());
    }

    private static FakePlayer actor(Villager v, ServerLevel sl, ItemStack tool) {
        FakePlayer p = FakePlayerFactory.get(sl, new GameProfile(v.getUUID(), "[Village Worker]"));
        p.setItemInHand(InteractionHand.MAIN_HAND, tool);
        return p;
    }

    public static boolean place(Villager v, ServerLevel sl, BlockPos p, BlockState state) {
        if (editable(v, sl, p) && sl.getBlockState(p).canBeReplaced() && sl.noCollision(new AABB(p))) {
            BlockSnapshot before = BlockSnapshot.create(sl.dimension(), sl, p);
            if (!sl.setBlock(p, state, 3)) {
                return false;
            } else if (((EntityPlaceEvent)NeoForge.EVENT_BUS.post(new EntityPlaceEvent(before, sl.getBlockState(p.below()), actor(v, sl, v.getMainHandItem()))))
                .isCanceled()) {
                before.restore();
                return false;
            } else {
                return true;
            }
        } else {
            return false;
        }
    }

    private static boolean nearby(Villager v, BlockPos p) {
        if (v.distanceToSqr(Vec3.atCenterOf(p)) <= 16.0) {
            return true;
        } else {
            v.getNavigation().moveTo((double)p.getX() + 0.5, (double)p.getY(), (double)p.getZ() + 0.5, 1.1);
            v.getBrain().setMemory(MemoryModuleType.WALK_TARGET, new WalkTarget(p, 1.1F, 2));
            return false;
        }
    }

    public static boolean harvest(Villager v, ServerLevel sl, BlockPos p) {
        BlockState state = sl.getBlockState(p);
        if (editable(v, sl, p) && state.getBlock() instanceof CropBlock crop && crop.isMaxAge(state) && nearby(v, p)) {
            FakePlayer fake = actor(v, sl, Items.IRON_HOE.getDefaultInstance());
            if (((BreakEvent)NeoForge.EVENT_BUS.post(new BreakEvent(sl, p, state, fake))).isCanceled()) {
                return false;
            } else {
                List<ItemStack> drops = Block.getDrops(state, sl, p, null, v, fake.getMainHandItem());
                Item seed = crop == Blocks.CARROTS
                    ? Items.CARROT
                    : (crop == Blocks.POTATOES ? Items.POTATO : (crop == Blocks.BEETROOTS ? Items.BEETROOT_SEEDS : Items.WHEAT_SEEDS));
                boolean planted = false;

                for (ItemStack drop : drops) {
                    if (!planted && drop.is(seed)) {
                        drop.shrink(1);
                        planted = true;
                    }
                }

                if (!planted) {
                    return false;
                } else {
                    sl.setBlock(p, crop.getStateForAge(0), 3);

                    for (ItemStack dropx : drops) {
                        if (!dropx.isEmpty()) {
                            ItemStack rest = v.getInventory().addItem(dropx);
                            if (!rest.isEmpty()) {
                                sl.addFreshEntity(new ItemEntity(sl, (double)p.getX() + 0.5, (double)p.getY() + 0.3, (double)p.getZ() + 0.5, rest));
                            }
                        }
                    }

                    v.swing(InteractionHand.MAIN_HAND);
                    count(v, "Harvests");
                    data(v).putString("Task", "収穫して植え直しました");
                    return true;
                }
            }
        } else {
            return false;
        }
    }

    public static boolean expandFarm(Villager v, ServerLevel sl, BlockPos ground) {
        if (editable(v, sl, ground)
            && nearby(v, ground)
            && sl.getBlockState(ground.above()).isAir()
            && (sl.getBlockState(ground).is(Blocks.DIRT) || sl.getBlockState(ground).is(Blocks.GRASS_BLOCK))) {
            boolean water = false;

            for (BlockPos p : BlockPos.betweenClosed(ground.offset(-4, 0, -4), ground.offset(4, 1, 4))) {
                if (sl.getFluidState(p).is(FluidTags.WATER)) {
                    water = true;
                    break;
                }
            }

            if (!water) {
                return false;
            } else {
                int slot = -1;
                Block crop = null;

                for (int i = 0; i < v.getInventory().getContainerSize(); i++) {
                    ItemStack item = v.getInventory().getItem(i);
                    if (item.is(Items.WHEAT_SEEDS)) {
                        slot = i;
                        crop = Blocks.WHEAT;
                        break;
                    }

                    if (item.is(Items.CARROT)) {
                        slot = i;
                        crop = Blocks.CARROTS;
                        break;
                    }

                    if (item.is(Items.POTATO)) {
                        slot = i;
                        crop = Blocks.POTATOES;
                        break;
                    }
                }

                if (slot < 0) {
                    return false;
                } else {
                    BlockState state = sl.getBlockState(ground);
                    if (((BreakEvent)NeoForge.EVENT_BUS.post(new BreakEvent(sl, ground, state, actor(v, sl, Items.IRON_HOE.getDefaultInstance()))))
                        .isCanceled()) {
                        return false;
                    } else {
                        sl.setBlock(ground, (BlockState)Blocks.FARMLAND.defaultBlockState().setValue(FarmBlock.MOISTURE, 7), 3);
                        if (!place(v, sl, ground.above(), crop.defaultBlockState())) {
                            sl.setBlock(ground, state, 3);
                            return false;
                        } else {
                            v.getInventory().getItem(slot).shrink(1);
                            count(v, "FarmExpanded");
                            data(v).putString("Task", "畑を拡張しました");
                            return true;
                        }
                    }
                }
            }
        } else {
            return false;
        }
    }

    public static boolean farm(Villager v, ServerLevel sl) {
        for (BlockPos p : BlockPos.betweenClosed(v.blockPosition().offset(-6, -1, -6), v.blockPosition().offset(6, 1, 6))) {
            if (harvest(v, sl, p.immutable())) {
                return true;
            }
        }

        if (!VillagerRoles.profession(v).equals("farmer")) {
            return false;
        } else {
            for (BlockPos px : BlockPos.betweenClosed(v.blockPosition().offset(-4, -1, -4), v.blockPosition().offset(4, -1, 4))) {
                if (expandFarm(v, sl, px.immutable())) {
                    return true;
                }
            }

            return false;
        }
    }

    public static boolean fell(Villager v, ServerLevel sl, BlockPos p) {
        BlockState state = sl.getBlockState(p);
        if (editable(v, sl, p)
            && state.is(BlockTags.LOGS)
            && !VillageReputation.villageOwned(sl, p)
            && naturalTree(sl, p)
            && nearby(v, p)
            && sl.getBlockEntity(p) == null) {
            ItemStack tool = MobLevels.weapon(v, "axe");
            if (((BreakEvent)NeoForge.EVENT_BUS.post(new BreakEvent(sl, p, state, actor(v, sl, tool)))).isCanceled()) {
                return false;
            } else {
                List<ItemStack> drops = Block.getDrops(state, sl, p, null, v, tool);
                if (!sl.setBlock(p, Blocks.AIR.defaultBlockState(), 3)) {
                    return false;
                } else {
                    for (ItemStack stack : drops) {
                        ItemStack rest = v.getInventory().addItem(stack);
                        if (!rest.isEmpty()) {
                            sl.addFreshEntity(new ItemEntity(sl, (double)p.getX() + 0.5, (double)p.getY() + 0.5, (double)p.getZ() + 0.5, rest));
                        }
                    }

                    v.swing(InteractionHand.MAIN_HAND);
                    count(v, "Logs");
                    data(v).putString("Task", "木を伐採しました");
                    return true;
                }
            }
        } else {
            return false;
        }
    }

    private static boolean naturalTree(ServerLevel sl, BlockPos p) {
        BlockPos base = p;

        for (int i = 0; i < 32 && sl.getBlockState(base.below()).is(BlockTags.LOGS); i++) {
            base = base.below();
        }

        if (!sl.getBlockState(base.below()).is(BlockTags.DIRT)) {
            return false;
        } else {
            BlockPos top = p;

            for (int i = 0; i < 48 && sl.getBlockState(top.above()).is(BlockTags.LOGS); i++) {
                top = top.above();
            }

            for (BlockPos q : BlockPos.betweenClosed(top.offset(-2, -1, -2), top.offset(2, 2, 2))) {
                BlockState leaves = sl.getBlockState(q);
                if (leaves.is(BlockTags.LEAVES) && leaves.hasProperty(LeavesBlock.PERSISTENT) && !(Boolean)leaves.getValue(LeavesBlock.PERSISTENT)) {
                    return true;
                }
            }

            return false;
        }
    }

    private static boolean lumber(Villager v, ServerLevel sl) {
        for (BlockPos p : BlockPos.betweenClosed(v.blockPosition().offset(-5, 0, -5), v.blockPosition().offset(5, 5, 5))) {
            if (fell(v, sl, p.immutable())) {
                return true;
            }
        }

        return false;
    }

    private static SimpleContainer copy(Container c) {
        SimpleContainer result = new SimpleContainer(c.getContainerSize());

        for (int i = 0; i < c.getContainerSize(); i++) {
            result.setItem(i, c.getItem(i).copy());
        }

        return result;
    }

    public static boolean craft(Villager v, ServerLevel sl, ResourceLocation wanted) {
        SimpleContainer inv = v.getInventory();
        List<RecipeHolder<CraftingRecipe>> recipes = sl.getRecipeManager().getAllRecipesFor(RecipeType.CRAFTING);
        if (recipes.isEmpty()) {
            return false;
        } else {
            int start = data(v).getInt("RecipeCursor");

            for (int j = 0; j < Math.min(24, recipes.size()); j++) {
                RecipeHolder<CraftingRecipe> holder = wanted == null
                    ? recipes.get(Math.floorMod(start + j, recipes.size()))
                    : recipes.stream().filter(r -> r.id().equals(wanted)).findFirst().orElse(null);
                if (holder == null) {
                    return false;
                }

                CraftingRecipe recipe = (CraftingRecipe)holder.value();
                int w = recipe instanceof ShapedRecipe shaped ? shaped.getWidth() : 3;
                if (recipe instanceof ShapedRecipe shapedx) {
                    shapedx.getHeight();
                } else {
                    byte var26 = 3;
                }

                NonNullList<Ingredient> ingredients = recipe.getIngredients();
                if (!ingredients.isEmpty() && ingredients.size() <= 9) {
                    ArrayList<ItemStack> grid = new ArrayList<>(Collections.nCopies(9, ItemStack.EMPTY));
                    SimpleContainer remaining = copy(inv);
                    boolean matches = true;

                    for (int k = 0; k < ingredients.size(); k++) {
                        Ingredient ingredient = (Ingredient)ingredients.get(k);
                        if (!ingredient.isEmpty()) {
                            int slot = -1;

                            for (int i = 0; i < remaining.getContainerSize(); i++) {
                                if (!remaining.getItem(i).isEmpty() && ingredient.test(remaining.getItem(i))) {
                                    slot = i;
                                    break;
                                }
                            }

                            if (slot < 0) {
                                matches = false;
                                break;
                            }

                            grid.set(recipe instanceof ShapedRecipe ? k / w * 3 + k % w : k, remaining.removeItem(slot, 1));
                        }
                    }

                    if (matches) {
                        CraftingInput input = CraftingInput.of(3, 3, grid);
                        if (recipe.matches(input, sl)) {
                            ItemStack result = recipe.assemble(input, sl.registryAccess());
                            if (!result.isEmpty()
                                && (
                                    wanted != null
                                        || result.getItem() instanceof BlockItem
                                        || result.has(DataComponents.FOOD)
                                        || result.getItem() instanceof TieredItem
                                )
                                && remaining.addItem(result.copy()).isEmpty()) {
                                boolean fits = true;

                                for (ItemStack remainder : recipe.getRemainingItems(input)) {
                                    if (!remainder.isEmpty() && !remaining.addItem(remainder.copy()).isEmpty()) {
                                        fits = false;
                                        break;
                                    }
                                }

                                if (fits) {
                                    for (int ix = 0; ix < inv.getContainerSize(); ix++) {
                                        inv.setItem(ix, remaining.getItem(ix));
                                    }

                                    count(v, "Crafts");
                                    data(v).putString("LastRecipe", holder.id().toString());
                                    data(v).putString("Task", "製作：" + result.getHoverName().getString());
                                    data(v).putInt("RecipeCursor", start + j + 1);
                                    v.swing(InteractionHand.MAIN_HAND);
                                    return true;
                                }
                            }
                        }
                    }
                }
            }

            data(v).putInt("RecipeCursor", start + 24);
            return false;
        }
    }

    private static List<VillagerLife.BuildPart> plan() {
        ArrayList<VillagerLife.BuildPart> result = new ArrayList<>();

        for (int x = 0; x < 5; x++) {
            for (int z = 0; z < 5; z++) {
                result.add(new VillagerLife.BuildPart(new BlockPos(x, -1, z), Blocks.COBBLESTONE));
            }
        }

        for (int y = 0; y < 3; y++) {
            for (int x = 0; x < 5; x++) {
                for (int z = 0; z < 5; z++) {
                    if ((x == 0 || x == 4 || z == 0 || z == 4) && (x != 2 || z != 0 || y >= 2)) {
                        result.add(new VillagerLife.BuildPart(new BlockPos(x, y, z), Blocks.OAK_PLANKS));
                    }
                }
            }
        }

        for (int x = 0; x < 5; x++) {
            for (int zx = 0; zx < 5; zx++) {
                result.add(new VillagerLife.BuildPart(new BlockPos(x, 3, zx), Blocks.OAK_PLANKS));
            }
        }

        result.add(new VillagerLife.BuildPart(new BlockPos(1, 0, 2), Blocks.CHEST));
        result.add(new VillagerLife.BuildPart(new BlockPos(2, 0, 0), Blocks.OAK_DOOR));
        result.add(new VillagerLife.BuildPart(new BlockPos(2, 1, 0), Blocks.OAK_DOOR, false));
        result.add(new VillagerLife.BuildPart(new BlockPos(3, 0, 2), Blocks.WHITE_BED));
        result.add(new VillagerLife.BuildPart(new BlockPos(3, 0, 3), Blocks.WHITE_BED, false));
        return List.copyOf(result);
    }

    public static boolean startBuild(Villager v, ServerLevel sl, BlockPos at) {
        VillageLedger.Village village = VillageLedger.of(v);
        if (village.houses < 8 && village.contains(at.offset(5, 0, 5))) {
            for (int x = 0; x < 5; x++) {
                for (int z = 0; z < 5; z++) {
                    for (int y = 0; y < 4; y++) {
                        if (!editable(v, sl, at.offset(x, y, z)) || !sl.getBlockState(at.offset(x, y, z)).canBeReplaced()) {
                            return false;
                        }
                    }
                }
            }

            for (int x = 0; x < 5; x++) {
                for (int z = 0; z < 5; z++) {
                    BlockPos ground = at.offset(x, -1, z);
                    BlockState soil = sl.getBlockState(ground);
                    boolean clearable = soil.is(Blocks.STONE) || soil.is(Blocks.DIRT) || soil.is(Blocks.GRASS_BLOCK);
                    if (!editable(v, sl, ground) || !clearable && (!soil.canBeReplaced() || sl.getBlockState(ground.below()).canBeReplaced())) {
                        return false;
                    }
                }
            }

            data(v).putLong("BuildOrigin", at.asLong());
            data(v).putInt("BuildStep", 0);
            return true;
        } else {
            return false;
        }
    }

    private static boolean placePair(Villager v, ServerLevel sl, BlockPos p, BlockState first, BlockPos q, BlockState second) {
        if (editable(v, sl, p)
            && editable(v, sl, q)
            && sl.getBlockState(p).canBeReplaced()
            && sl.getBlockState(q).canBeReplaced()
            && sl.noCollision(new AABB(p))
            && sl.noCollision(new AABB(q))) {
            BlockSnapshot a = BlockSnapshot.create(sl.dimension(), sl, p);
            BlockSnapshot b = BlockSnapshot.create(sl.dimension(), sl, q);
            if (sl.setBlock(p, first, 2)
                && sl.setBlock(q, second, 2)
                && !((EntityPlaceEvent)NeoForge.EVENT_BUS.post(new EntityPlaceEvent(a, sl.getBlockState(p.below()), actor(v, sl, v.getMainHandItem()))))
                    .isCanceled()
                && !((EntityPlaceEvent)NeoForge.EVENT_BUS.post(new EntityPlaceEvent(b, sl.getBlockState(q.below()), actor(v, sl, v.getMainHandItem()))))
                    .isCanceled()) {
                sl.updateNeighborsAt(p, first.getBlock());
                sl.updateNeighborsAt(q, second.getBlock());
                if (sl.getBlockState(p).is(first.getBlock()) && sl.getBlockState(q).is(second.getBlock())) {
                    return true;
                } else {
                    a.restore();
                    b.restore();
                    return false;
                }
            } else {
                a.restore();
                b.restore();
                return false;
            }
        } else {
            return false;
        }
    }

    public static boolean build(Villager v, ServerLevel sl) {
        CompoundTag n = data(v);
        if (!n.contains("BuildOrigin")) {
            int planks = 0;

            for (ItemStack stack : v.getInventory().getItems()) {
                if (stack.is(Items.OAK_PLANKS)) {
                    planks += stack.getCount();
                }
            }

            BlockPos site = VillageLedger.of(v).center.offset(8 + v.getId() % 3 * 7, 0, 8);
            site = new BlockPos(site.getX(), sl.getHeight(Types.MOTION_BLOCKING_NO_LEAVES, site.getX() + 2, site.getZ() + 2), site.getZ());
            if (planks < 32 || !startBuild(v, sl, site)) {
                return false;
            }
        }

        int step = n.getInt("BuildStep");
        if (step >= HOUSE.size()) {
            n.remove("BuildOrigin");
            VillageLedger.of(v).houses++;
            VillageLedger.get(sl).setDirty();
            count(v, "Houses");
            return true;
        } else {
            VillagerLife.BuildPart part = HOUSE.get(step);
            BlockPos p = BlockPos.of(n.getLong("BuildOrigin")).offset(part.offset);
            if (sl.getBlockState(p).is(part.block)) {
                n.putInt("BuildStep", step + 1);
                return true;
            } else if (!nearby(v, p)) {
                return false;
            } else {
                int slot = -1;

                for (int i = 0; i < v.getInventory().getContainerSize(); i++) {
                    if (v.getInventory().getItem(i).is(part.block.asItem())) {
                        slot = i;
                        break;
                    }
                }

                if (slot < 0 && part.charge) {
                    n.putString("Task", "建築資材待ち：" + part.block.getName().getString());
                    return false;
                } else {
                    BlockState original = sl.getBlockState(p);
                    if (part.offset.getY() < 0 && !original.canBeReplaced()) {
                        if (!editable(v, sl, p)
                            || !original.is(Blocks.STONE) && !original.is(Blocks.DIRT) && !original.is(Blocks.GRASS_BLOCK)
                            || ((BreakEvent)NeoForge.EVENT_BUS.post(new BreakEvent(sl, p, original, actor(v, sl, v.getMainHandItem())))).isCanceled()) {
                            return false;
                        }

                        sl.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
                    }

                    BlockState state = part.block.defaultBlockState();
                    if (part.block instanceof DoorBlock) {
                        state = (BlockState)state.setValue(DoorBlock.HALF, part.charge ? DoubleBlockHalf.LOWER : DoubleBlockHalf.UPPER);
                    }

                    if (part.block instanceof BedBlock) {
                        state = (BlockState)((BlockState)state.setValue(BedBlock.FACING, Direction.SOUTH))
                            .setValue(BedBlock.PART, part.charge ? BedPart.FOOT : BedPart.HEAD);
                    }

                    int placed = 1;
                    if (part.charge && (part.block instanceof DoorBlock || part.block instanceof BedBlock)) {
                        VillagerLife.BuildPart next = HOUSE.get(step + 1);
                        BlockState second = part.block instanceof DoorBlock
                            ? (BlockState)state.setValue(DoorBlock.HALF, DoubleBlockHalf.UPPER)
                            : (BlockState)state.setValue(BedBlock.PART, BedPart.HEAD);
                        BlockPos partner = BlockPos.of(n.getLong("BuildOrigin")).offset(next.offset);
                        if (!placePair(v, sl, p, state, partner, second)) {
                            return false;
                        }

                        VillageLedger.of(v).communal.add(partner.asLong());
                        placed = 2;
                    } else if (!place(v, sl, p, state)) {
                        if (!original.canBeReplaced()) {
                            sl.setBlock(p, original, 3);
                        }

                        return false;
                    }

                    if (part.charge) {
                        v.getInventory().getItem(slot).shrink(1);
                    }

                    n.putInt("BuildStep", step + placed);
                    VillageLedger.of(v).communal.add(p.asLong());
                    VillageLedger.get(sl).setDirty();

                    for (int ix = 0; ix < placed; ix++) {
                        count(v, "Built");
                    }

                    v.swing(InteractionHand.MAIN_HAND);
                    n.putString("Task", "住居を建設 " + (step + placed) + "/" + HOUSE.size());
                    return true;
                }
            }
        }
    }

    public static boolean sort(Container c) {
        List<ItemStack> original = VillageReputation.snapshot(c);
        List<ItemStack> all = original.stream()
            .filter(s -> !s.isEmpty())
            .sorted(Comparator.comparing(s -> BuiltInRegistries.ITEM.getKey(s.getItem()).toString()))
            .toList();
        SimpleContainer sorted = new SimpleContainer(c.getContainerSize());

        for (ItemStack item : all) {
            if (!sorted.addItem(item.copy()).isEmpty()) {
                return false;
            }
        }

        for (int i = 0; i < c.getContainerSize(); i++) {
            c.setItem(i, sorted.getItem(i));
        }

        c.setChanged();
        return true;
    }

    private static boolean storage(Villager v, ServerLevel sl, boolean tidy) {
        VillageLedger.Village village = VillageLedger.of(v);

        for (BlockPos p : BlockPos.betweenClosed(v.blockPosition().offset(-5, -1, -5), v.blockPosition().offset(5, 1, 5))) {
            Container box = VillageReputation.communalChest(sl, village, p.immutable());
            if (box != null && nearby(v, p)) {
                if (tidy) {
                    if (sort(box)) {
                        count(v, "Sorted");
                        data(v).putString("Task", "共有チェストを整理");
                        return true;
                    }
                } else {
                    SimpleContainer inv = v.getInventory();
                    if (inv.isEmpty()) {
                        for (int i = 0; i < box.getContainerSize(); i++) {
                            if (!box.getItem(i).isEmpty() && inv.canAddItem(box.getItem(i))) {
                                inv.addItem(box.removeItem(i, Math.min(64, box.getItem(i).getCount())));
                                box.setChanged();
                                count(v, "Supplies");
                                return true;
                            }
                        }
                    } else {
                        for (int ix = 0; ix < inv.getContainerSize(); ix++) {
                            ItemStack stack = inv.getItem(ix);
                            if (!stack.isEmpty() && stack.getCount() >= 24 && !stack.has(DataComponents.FOOD)) {
                                SimpleContainer temp = copy(box);
                                ItemStack rest = temp.addItem(stack.copyWithCount(stack.getCount() - 8));
                                int stored = stack.getCount() - 8 - rest.getCount();
                                if (stored > 0) {
                                    for (int j = 0; j < box.getContainerSize(); j++) {
                                        box.setItem(j, temp.getItem(j));
                                    }

                                    stack.shrink(stored);
                                    box.setChanged();
                                    count(v, "Stored");
                                    return true;
                                }
                            }
                        }
                    }
                }
            }
        }

        return false;
    }

    public static boolean tradeWith(Villager buyer, Villager seller) {
        if (buyer != seller && VillageReputation.sameVillage(buyer, seller) && !(buyer.distanceToSqr(seller) > 16.0) && seller.getTradingPlayer() == null) {
            SimpleContainer inv = buyer.getInventory();

            for (MerchantOffer offer : seller.getOffers()) {
                if (!offer.isOutOfStock()) {
                    for (int a = 0; a < inv.getContainerSize(); a++) {
                        for (int b = -1; b < inv.getContainerSize(); b++) {
                            if (b != a) {
                                ItemStack ca = inv.getItem(a).copy();
                                ItemStack cb = b < 0 ? ItemStack.EMPTY : inv.getItem(b).copy();
                                if (offer.satisfiedBy(ca, cb)) {
                                    SimpleContainer buyerAfter = copy(inv);
                                    SimpleContainer sellerAfter = copy(seller.getInventory());
                                    if (sellerAfter.addItem(offer.getCostA().copy()).isEmpty()
                                        && (offer.getCostB().isEmpty() || sellerAfter.addItem(offer.getCostB().copy()).isEmpty())) {
                                        offer.take(ca, cb);
                                        buyerAfter.setItem(a, ca);
                                        if (b >= 0) {
                                            buyerAfter.setItem(b, cb);
                                        }

                                        if (!buyerAfter.addItem(offer.getResult().copy()).isEmpty()) {
                                            return false;
                                        }

                                        for (int i = 0; i < inv.getContainerSize(); i++) {
                                            inv.setItem(i, buyerAfter.getItem(i));
                                        }

                                        for (int i = 0; i < sellerAfter.getContainerSize(); i++) {
                                            seller.getInventory().setItem(i, sellerAfter.getItem(i));
                                        }

                                        seller.notifyTrade(offer);
                                        count(buyer, "Trades");
                                        count(seller, "Trades");
                                        data(buyer).putString("Task", "村人同士で取引");
                                        return true;
                                    }

                                    return false;
                                }
                            }
                        }
                    }
                }
            }

            return false;
        } else {
            return false;
        }
    }

    private static boolean trade(Villager v, ServerLevel sl) {
        for (Villager seller : sl.getEntitiesOfClass(Villager.class, v.getBoundingBox().inflate(4.0), s -> s.isAlive() && !s.isBaby())
            .stream()
            .limit(6L)
            .toList()) {
            if (tradeWith(v, seller)) {
                return true;
            }
        }

        return false;
    }

    public static boolean pray(Villager v, ServerLevel sl) {
        CompoundTag n = data(v);
        long day = Math.floorDiv(sl.getGameTime(), 24000);
        if (n.contains("PrayerDay") && n.getLong("PrayerDay") == day) {
            return false;
        } else {
            boolean shrine = false;

            for (BlockPos p : BlockPos.betweenClosed(v.blockPosition().offset(-4, -1, -4), v.blockPosition().offset(4, 2, 4))) {
                if (sl.getBlockState(p).is(Blocks.BELL)) {
                    shrine = true;
                    break;
                }
            }

            if (!shrine) {
                return false;
            } else {
                n.putLong("PrayerDay", day);
                String faith = sl.getEntitiesOfClass(SupremeEntity.class, v.getBoundingBox().inflate(24.0), b -> b.ally(v))
                    .stream()
                    .findFirst()
                    .map(b -> b.spec.name)
                    .orElse("村の守護と豊穣");
                n.putString("Faith", faith);

                for (Villager friend : sl.getEntitiesOfClass(Villager.class, v.getBoundingBox().inflate(8.0), f -> VillageReputation.sameVillage(v, f))) {
                    friend.heal(2.0F);
                }

                v.swing(InteractionHand.MAIN_HAND);
                sl.sendParticles(ParticleTypes.HAPPY_VILLAGER, v.getX(), v.getEyeY(), v.getZ(), 5, 0.3, 0.3, 0.3, 0.0);
                count(v, "Prayers");
                n.putString("Task", "集会と祈り");
                return true;
            }
        }
    }

    private VillagerLife() {
    }

    private static record BuildPart(BlockPos offset, Block block, boolean charge) {
        BuildPart(BlockPos offset, Block block) {
            this(offset, block, true);
        }
    }
}
