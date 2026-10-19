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
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.common.util.BlockSnapshot;
import net.minecraftforge.common.util.FakePlayer;
import net.minecraftforge.common.util.FakePlayerFactory;
import net.minecraftforge.event.level.BlockEvent.BreakEvent;
import net.minecraftforge.event.level.BlockEvent.EntityPlaceEvent;
import net.minecraftforge.event.entity.living.LivingEvent.LivingTickEvent;

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

    public static void tick(LivingTickEvent e) {
        if (!(e.getEntity() instanceof Villager)) {
            // v0.17.15: the village's aircraft and vehicles on the move (the non-living ones: WorldEvents.levelTick)
            VillageFlights.tick(e.getEntity());
            VillageVehicles.tick(e.getEntity());
            // v0.17.16: wandering traders and their llamas, raid messengers and horde soldiers
            WanderingTraders.tick(e.getEntity());
            VillageRaids.tick(e.getEntity());
            return;
        }
        if (e.getEntity() instanceof Villager v
            && v.level() instanceof ServerLevel sl
            && (Boolean)RebornConfig.VILLAGE_LIFE.get()
            && !v.isBaby()
            && v.isAlive()
            && !v.isNoAi()) {
            // v0.17.15: wandering expedition parties live on the road; expedition members and flight crews follow their trip
            if (v.getPersistentData().getBoolean("OrorWanderer")) {
                if (v.tickCount % 20 == Math.floorMod(v.getId(), 20)) {
                    VillageExpeditions.wander(v, sl);
                }
                return;
            }
            if (VillageExpeditions.member(v, sl) || VillageFlights.crew(v, sl) || VillageVehicles.crew(v, sl)) {
                return;
            }
            if (v.tickCount % 20 != Math.floorMod(v.getId(), 20)) {
                return;
            }
            VillageLedger.of(v);
            // v0.17.17: kingdom and fortress villagers bring their village up to what the place already is
            VillageExpeditions.settle(v, sl);
            if (!take(sl)) {
                return;
            }

            consume(v);
            if (VillageAI.fleeing(v)) {
                data(v).putString("Task", "避難中");
                return;
            }

            if (AdaptiveCombat.enemy(v, v.getTarget())) {
                data(v).putString("Task", "村を防衛");
                return;
            }

            // v0.17.13: at night every villager, strong ones and miners too, goes home to bed (the guards are Guard Villagers')
            if (!sl.isDay()) {
                data(v).putString("Task", VillageAI.bedtime(v, sl));
                return;
            }

            if (VillagerIndustry.miner(v)) {
                return;
            }

            pickup(v, sl);
            equip(v);
            VillageExpeditions.stow(v, sl);
            // stay with a job for a while instead of picking a new one (and a new destination) every second
            CompoundTag n = data(v);
            long now = sl.getGameTime();
            int phase = n.getLong("JobUntil") > now ? n.getInt("JobPhase") : Math.floorMod((int)(now / 20L) + v.getId(), 8);
            if (n.getLong("JobUntil") <= now && n.contains("BuildOrigin") && sl.random.nextInt(2) == 0) {
                // a house going up comes before the other chores
                phase = 3;
            }
            goal = null;
            goalDistance = Double.MAX_VALUE;

            // v0.17.14: crafting, storing and tidying follow what the village lacks (VillageWork)
            boolean changed = switch (phase) {
                case 0 -> farm(v, sl);
                case 1 -> VillageWork.wantsWood(v, sl) && lumber(v, sl);
                case 2 -> VillageWork.chores(v, sl);
                case 3 -> build(v, sl);
                case 4 -> VillageWork.store(v, sl);
                case 5 -> trade(v, sl);
                case 6 -> pray(v, sl);
                default -> VillageWork.tidy(v, sl);
            };
            if (changed) {
                n.putInt("JobPhase", phase);
                n.putLong("JobUntil", now + 60L);
                n.putBoolean("JobWalk", false);
            } else if (goal != null) {
                // walk once to the nearest place this job needs, and keep at the job until there or 12 s pass
                // (v0.17.17: also when the walk follows a step of the job, which only held the job for 3 s)
                VillageAI.walk(v, goal, VillageAI.pace(v, VillageAI.WORK), 2);
                if (n.getLong("JobUntil") <= now || n.getInt("JobPhase") != phase || !n.getBoolean("JobWalk")) {
                    n.putInt("JobPhase", phase);
                    n.putLong("JobUntil", now + 240L);
                    n.putBoolean("JobWalk", true);
                }
                n.putString("Task", "仕事場へ向かっています");
            } else {
                n.remove("JobUntil");
                n.putString("Task", "素材や仕事を探しています");
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
                || s.is(Items.BONE_MEAL)
                || VillageWork.material(s);
        }
    }

    private static void equip(Villager v) {
        // v0.17.17: weapons from the pack only while the villager is armed for danger (VillageAI.gear puts them away)
        if (!MobMind.data(v).getBoolean("VillageGeared")) {
            return;
        }
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

    static boolean editable(Villager v, ServerLevel sl, BlockPos p) {
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
            } else if (((EntityPlaceEvent)MinecraftForge.EVENT_BUS.post(new EntityPlaceEvent(before, sl.getBlockState(p.below()), actor(v, sl, v.getMainHandItem()))))
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

    // v0.17.9: the work searches used to send the villager toward every far candidate in turn at 1.1x speed (the last one
    // won, so a farmer drifted toward the far corner of its search box every second); now the nearest candidate is kept
    // and tick() walks there once, at a working pace.
    private static BlockPos goal;
    private static double goalDistance = Double.MAX_VALUE;

    static boolean nearby(Villager v, BlockPos p) {
        double d = v.distanceToSqr(Vec3.atCenterOf(p));
        if (d <= 16.0) {
            return true;
        } else {
            if (d < goalDistance) {
                goalDistance = d;
                goal = p.immutable();
            }

            return false;
        }
    }

    public static boolean harvest(Villager v, ServerLevel sl, BlockPos p) {
        BlockState state = sl.getBlockState(p);
        if (editable(v, sl, p) && state.getBlock() instanceof CropBlock crop && crop.isMaxAge(state) && nearby(v, p)) {
            FakePlayer fake = actor(v, sl, Items.IRON_HOE.getDefaultInstance());
            if (((BreakEvent)MinecraftForge.EVENT_BUS.post(new BreakEvent(sl, p, state, fake))).isCanceled()) {
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
        // v0.17.17: short grass or a flower on the ground is no obstacle (the crop takes its place)
        if (editable(v, sl, ground)
            && sl.getBlockState(ground.above()).canBeReplaced() && sl.getFluidState(ground.above()).isEmpty()
            && (sl.getBlockState(ground).is(Blocks.DIRT) || sl.getBlockState(ground).is(Blocks.GRASS_BLOCK))) {
            boolean water = false;

            for (BlockPos p : BlockPos.betweenClosed(ground.offset(-4, 0, -4), ground.offset(4, 1, 4))) {
                if (sl.getFluidState(p).is(FluidTags.WATER)) {
                    water = true;
                    break;
                }
            }

            if (!water || !nearby(v, ground)) {
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
                    if (((BreakEvent)MinecraftForge.EVENT_BUS.post(new BreakEvent(sl, ground, state, actor(v, sl, Items.IRON_HOE.getDefaultInstance()))))
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
        }
        // v0.17.14: fields grow from their edges (dirt or grass beside farmland, near water), up to 16 plots a day; a
        // farmer had to be standing by water with seeds before, so it hardly ever happened
        CompoundTag n = data(v);
        long day = Math.floorDiv(sl.getGameTime(), 24000L);
        if (n.getLong("FarmDay") != day) {
            n.putLong("FarmDay", day);
            n.putInt("FarmToday", 0);
        }
        if (n.getInt("FarmToday") >= 16) {
            return false;
        }
        if (VillageWork.count(v, i -> i.is(Items.WHEAT_SEEDS) || i.is(Items.CARROT) || i.is(Items.POTATO)) == 0) {
            return VillageWork.seeds(v, sl) == VillageWork.ACTED;
        }
        boolean fields = false;
        for (BlockPos px : BlockPos.betweenClosed(v.blockPosition().offset(-8, -2, -8), v.blockPosition().offset(8, 1, 8))) {
            if (sl.getBlockState(px).is(Blocks.FARMLAND)) {
                fields = true;
            } else if (edge(sl, px) && expandFarm(v, sl, px.immutable())) {
                n.putInt("FarmToday", n.getInt("FarmToday") + 1);
                return true;
            }
        }
        if (!fields) {
            // no field nearby yet: break ground by water
            for (BlockPos px : BlockPos.betweenClosed(v.blockPosition().offset(-4, -1, -4), v.blockPosition().offset(4, -1, 4))) {
                if (expandFarm(v, sl, px.immutable())) {
                    n.putInt("FarmToday", n.getInt("FarmToday") + 1);
                    return true;
                }
            }
        }
        return false;
    }

    /** Dirt or grass right beside farmland. */
    private static boolean edge(ServerLevel sl, BlockPos ground) {
        BlockState st = sl.getBlockState(ground);
        if (!st.is(Blocks.DIRT) && !st.is(Blocks.GRASS_BLOCK)) {
            return false;
        }
        for (Direction d : Direction.Plane.HORIZONTAL) {
            if (sl.getBlockState(ground.relative(d)).is(Blocks.FARMLAND)) {
                return true;
            }
        }
        return false;
    }

    public static boolean fell(Villager v, ServerLevel sl, BlockPos p) {
        BlockState state = sl.getBlockState(p);
        if (state.is(BlockTags.LOGS)
            && editable(v, sl, p)
            && !VillageReputation.villageOwned(sl, p)
            && naturalTree(sl, p)
            && nearby(v, p)
            && sl.getBlockEntity(p) == null) {
            // v0.17.14: the whole trunk comes down (felling one log left the rest floating, and a floating trunk is no
            // longer a natural tree, so it stayed), then a sapling goes back in
            ItemStack tool = MobLevels.weapon(v, "axe");
            BlockPos base = p;
            for (int i = 0; i < 32 && sl.getBlockState(base.below()).is(BlockTags.LOGS); i++) {
                base = base.below();
            }
            List<BlockPos> trunk = new ArrayList<>();
            List<BlockPos> open = new ArrayList<>(List.of(base));
            while (!open.isEmpty() && trunk.size() < 48) {
                BlockPos q = open.remove(open.size() - 1);
                if (trunk.contains(q) || !sl.getBlockState(q).is(BlockTags.LOGS) || Math.abs(q.getX() - base.getX()) > 4 || Math.abs(q.getZ() - base.getZ()) > 4
                    || q.getY() < base.getY() || !editable(v, sl, q) || VillageReputation.villageOwned(sl, q)) {
                    continue;
                }
                trunk.add(q);
                for (BlockPos r : BlockPos.betweenClosed(q.offset(-1, 0, -1), q.offset(1, 1, 1))) {
                    open.add(r.immutable());
                }
            }
            int felled = 0;
            for (BlockPos q : trunk) {
                BlockState log = sl.getBlockState(q);
                if (((BreakEvent)MinecraftForge.EVENT_BUS.post(new BreakEvent(sl, q, log, actor(v, sl, tool)))).isCanceled()) {
                    continue;
                }
                List<ItemStack> drops = Block.getDrops(log, sl, q, null, v, tool);
                if (!sl.setBlock(q, Blocks.AIR.defaultBlockState(), 3)) {
                    continue;
                }
                felled++;
                for (ItemStack stack : drops) {
                    ItemStack rest = v.getInventory().addItem(stack);
                    if (!rest.isEmpty()) {
                        sl.addFreshEntity(new ItemEntity(sl, (double)q.getX() + 0.5, (double)q.getY() + 0.5, (double)q.getZ() + 0.5, rest));
                    }
                }
            }
            if (felled == 0) {
                return false;
            }
            for (int i = 0; i < v.getInventory().getContainerSize(); i++) {
                ItemStack sapling = v.getInventory().getItem(i);
                if (sapling.is(ItemTags.SAPLINGS) && sapling.getItem() instanceof BlockItem b && sl.getBlockState(base.below()).is(BlockTags.DIRT)
                    && b.getBlock().defaultBlockState().canSurvive(sl, base) && place(v, sl, base, b.getBlock().defaultBlockState())) {
                    sapling.shrink(1);
                    count(v, "Planted");
                    break;
                }
            }
            v.swing(InteractionHand.MAIN_HAND);
            for (int i = 0; i < felled; i++) {
                count(v, "Logs");
            }
            data(v).putString("Task", "木を伐採しました（" + felled + "本）");
            return true;
        } else {
            return false;
        }
    }

    static boolean naturalTree(ServerLevel sl, BlockPos p) {
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

    static boolean lumber(Villager v, ServerLevel sl) {
        for (BlockPos p : BlockPos.betweenClosed(v.blockPosition().offset(-5, -1, -5), v.blockPosition().offset(5, 5, 5))) {
            if (fell(v, sl, p.immutable())) {
                return true;
            }
        }

        return false;
    }

    static SimpleContainer copy(Container c) {
        SimpleContainer result = new SimpleContainer(c.getContainerSize());

        for (int i = 0; i < c.getContainerSize(); i++) {
            result.setItem(i, c.getItem(i).copy());
        }

        return result;
    }

    /**
     * Craft one batch of a recipe from the villager's inventory. v0.17.14: by id only (VillageWork decides what is needed;
     * the random recipes are gone), and a shaped recipe is laid on a grid of its own size: the crafting table trims the
     * grid to the pattern before matching, and a 3x3 grid never matched a smaller pattern (planks, sticks, torches,
     * doors...), so most of what villagers tried to make failed.
     */
    public static boolean craft(Villager v, ServerLevel sl, ResourceLocation wanted) {
        RecipeHolder<CraftingRecipe> holder = wanted == null ? null : VillageWork.recipe(sl, wanted);
        if (holder == null) {
            return false;
        }
        CraftingRecipe recipe = (CraftingRecipe)holder.value();
        NonNullList<Ingredient> ingredients = recipe.getIngredients();
        if (ingredients.isEmpty() || ingredients.size() > 9) {
            return false;
        }
        int w = recipe instanceof ShapedRecipe shaped ? shaped.getWidth() : 3;
        int h = recipe instanceof ShapedRecipe shaped ? shaped.getHeight() : 3;
        if (w * h < ingredients.size()) {
            return false;
        }
        SimpleContainer inv = v.getInventory();
        ArrayList<ItemStack> grid = new ArrayList<>(Collections.nCopies(w * h, ItemStack.EMPTY));
        SimpleContainer remaining = copy(inv);
        for (int k = 0; k < ingredients.size(); k++) {
            Ingredient ingredient = (Ingredient)ingredients.get(k);
            if (ingredient.isEmpty()) {
                continue;
            }
            int slot = -1;
            for (int i = 0; i < remaining.getContainerSize(); i++) {
                if (!remaining.getItem(i).isEmpty() && ingredient.test(remaining.getItem(i))) {
                    slot = i;
                    break;
                }
            }
            if (slot < 0) {
                return false;
            }
            grid.set(k, remaining.removeItem(slot, 1));
        }
        CraftingInput input = CraftingInput.of(w, h, grid);
        if (!recipe.matches(input, sl)) {
            return false;
        }
        ItemStack result = recipe.assemble(input, sl.registryAccess());
        if (result.isEmpty() || !remaining.addItem(result.copy()).isEmpty()) {
            return false;
        }
        for (ItemStack remainder : recipe.getRemainingItems(input)) {
            if (!remainder.isEmpty() && !remaining.addItem(remainder.copy()).isEmpty()) {
                return false;
            }
        }
        for (int i = 0; i < inv.getContainerSize(); i++) {
            inv.setItem(i, remaining.getItem(i));
        }
        count(v, "Crafts");
        data(v).putString("LastRecipe", holder.id().toString());
        data(v).putString("Task", "製作：" + result.getHoverName().getString());
        v.swing(InteractionHand.MAIN_HAND);
        return true;
    }

    /**
     * The house: a 5x5 plot with a floor (F), walls three high (W) with a door (D), a roof (R), a chest (C), a bed (B) and a
     * torch (T, when one is to hand). The second half of a door or a bed (charge false) is set with the first.
     */
    private static List<VillagerLife.BuildPart> plan() {
        ArrayList<VillagerLife.BuildPart> result = new ArrayList<>();

        for (int x = 0; x < 5; x++) {
            for (int z = 0; z < 5; z++) {
                result.add(new VillagerLife.BuildPart(new BlockPos(x, -1, z), 'F'));
            }
        }

        for (int y = 0; y < 3; y++) {
            for (int x = 0; x < 5; x++) {
                for (int z = 0; z < 5; z++) {
                    if ((x == 0 || x == 4 || z == 0 || z == 4) && (x != 2 || z != 0 || y >= 2)) {
                        result.add(new VillagerLife.BuildPart(new BlockPos(x, y, z), 'W'));
                    }
                }
            }
        }

        for (int x = 0; x < 5; x++) {
            for (int zx = 0; zx < 5; zx++) {
                result.add(new VillagerLife.BuildPart(new BlockPos(x, 3, zx), 'R'));
            }
        }

        result.add(new VillagerLife.BuildPart(new BlockPos(1, 0, 2), 'C'));
        result.add(new VillagerLife.BuildPart(new BlockPos(2, 0, 0), 'D'));
        result.add(new VillagerLife.BuildPart(new BlockPos(2, 1, 0), 'D', false));
        result.add(new VillagerLife.BuildPart(new BlockPos(3, 0, 2), 'B'));
        result.add(new VillagerLife.BuildPart(new BlockPos(3, 0, 3), 'B', false));
        result.add(new VillagerLife.BuildPart(new BlockPos(1, 0, 3), 'T'));
        return List.copyOf(result);
    }

    /**
     * A plot for a house at 'at' (its floor level). v0.17.14: the plot and a strip around it must be open air four high (so
     * a house is not built into another), on natural ground or one block over it, and not on a path, a field or water.
     */
    public static boolean startBuild(Villager v, ServerLevel sl, BlockPos at) {
        VillageLedger.Village village = VillageLedger.of(v);
        if (village == null || village.houses >= 12 || !village.contains(at.offset(5, 0, 5))) {
            return false;
        }
        for (int x = -1; x <= 5; x++) {
            for (int z = -1; z <= 5; z++) {
                for (int y = 0; y < 4; y++) {
                    BlockPos p = at.offset(x, y, z);
                    boolean inside = x >= 0 && x <= 4 && z >= 0 && z <= 4;
                    if (!sl.hasChunkAt(p) || inside && !editable(v, sl, p) || !sl.getBlockState(p).canBeReplaced() || !sl.getFluidState(p).isEmpty()) {
                        return false;
                    }
                }
            }
        }

        for (int x = 0; x < 5; x++) {
            for (int z = 0; z < 5; z++) {
                BlockPos ground = at.offset(x, -1, z);
                BlockState soil = sl.getBlockState(ground);
                if (!editable(v, sl, ground) || !sl.getFluidState(ground).isEmpty()) {
                    return false;
                }
                if (soil.canBeReplaced() ? sl.getBlockState(ground.below()).canBeReplaced() : !VillageWork.natural(soil)) {
                    return false;
                }
            }
        }

        data(v).putLong("BuildOrigin", at.asLong());
        data(v).putInt("BuildStep", 0);
        return true;
    }

    /** v0.17.14: house plots on rings 10-28 blocks around the village centre, a few tried each time. */
    private static boolean site(Villager v, ServerLevel sl) {
        VillageLedger.Village village = VillageLedger.of(v);
        CompoundTag n = data(v);
        int cursor = n.getInt("SiteCursor");
        for (int i = 0; i < 4; i++) {
            int k = cursor + i;
            int ring = 10 + Math.floorMod(k / 8, 4) * 6;
            double a = Math.floorMod(k, 8) * Math.PI / 4.0 + Math.floorMod(k / 32, 4) * 0.4;
            BlockPos c = village.center.offset((int)Math.round(Math.cos(a) * ring) - 2, 0, (int)Math.round(Math.sin(a) * ring) - 2);
            if (!sl.hasChunkAt(c)) {
                continue;
            }
            BlockPos at = new BlockPos(c.getX(), sl.getHeight(Types.MOTION_BLOCKING_NO_LEAVES, c.getX() + 2, c.getZ() + 2), c.getZ());
            if (Math.abs(at.getY() - village.center.getY()) <= 6 && startBuild(v, sl, at)) {
                n.putInt("SiteCursor", k + 1);
                return true;
            }
        }
        n.putInt("SiteCursor", cursor + 4);
        return false;
    }

    static boolean placePair(Villager v, ServerLevel sl, BlockPos p, BlockState first, BlockPos q, BlockState second) {
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
                && !((EntityPlaceEvent)MinecraftForge.EVENT_BUS.post(new EntityPlaceEvent(a, sl.getBlockState(p.below()), actor(v, sl, v.getMainHandItem()))))
                    .isCanceled()
                && !((EntityPlaceEvent)MinecraftForge.EVENT_BUS.post(new EntityPlaceEvent(b, sl.getBlockState(q.below()), actor(v, sl, v.getMainHandItem()))))
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

    /** What a house part is made of: any planks for walls and roof, cobblestone (or planks over a gap) for the floor. */
    private static java.util.function.Predicate<ItemStack> material(VillagerLife.BuildPart part) {
        return switch (part.kind) {
            case 'C' -> VillageWork.is("chest");
            case 'D' -> VillageWork.is("door");
            case 'B' -> VillageWork.is("bed");
            case 'T' -> VillageWork.is("torch");
            case 'F' -> VillageWork.is("cobblestone");
            default -> VillageWork.is("planks");
        };
    }

    /**
     * One step of the house. v0.17.14: any wood's planks, door and bed will do (only oak planks, an oak door and a white bed
     * did, and nobody made them); what the builder lacks it makes, takes from the chests or fells (VillageWork.supply);
     * natural ground stays the floor unless the builder has cobblestone for it; a spot something solid already fills is
     * passed over instead of holding the house up for ever. The builder starts only when someone in the village is
     * homeless (VillageWork.wantsHouse), on a plot it finds itself.
     */
    public static boolean build(Villager v, ServerLevel sl) {
        CompoundTag n = data(v);
        if (!n.contains("BuildOrigin")) {
            if (!VillageWork.wantsHouse(v, sl)) {
                return false;
            }
            if (!site(v, sl)) {
                VillageWork.noSite(v, sl);
                return false;
            }
        }

        BlockPos origin = BlockPos.of(n.getLong("BuildOrigin"));
        int step = n.getInt("BuildStep");
        boolean planks = VillageWork.count(v, VillageWork.is("planks")) > 0;
        while (step < HOUSE.size()) {
            VillagerLife.BuildPart part = HOUSE.get(step);
            BlockState here = sl.getBlockState(origin.offset(part.offset));
            boolean floor = part.kind == 'F';
            boolean pass = !part.charge
                || !floor && !here.canBeReplaced()
                || floor && !here.canBeReplaced() && planks && VillageWork.count(v, material(part)) == 0
                || part.kind == 'T' && VillageWork.count(v, material(part)) == 0;
            if (!pass) {
                break;
            }
            step++;
        }
        n.putInt("BuildStep", step);
        if (step >= HOUSE.size()) {
            n.remove("BuildOrigin");
            VillageLedger.of(v).houses++;
            VillageLedger.get(sl).setDirty();
            VillageWork.building(v, sl, false);
            count(v, "Houses");
            n.putString("Task", "住居が完成しました");
            return true;
        }
        VillageWork.building(v, sl, true);

        VillagerLife.BuildPart part = HOUSE.get(step);
        BlockPos p = origin.offset(part.offset);
        int slot = -1;
        for (int i = 0; i < v.getInventory().getContainerSize(); i++) {
            ItemStack item = v.getInventory().getItem(i);
            if (!item.isEmpty() && (material(part).test(item) || part.kind == 'F' && item.is(ItemTags.PLANKS)) && item.getItem() instanceof BlockItem) {
                slot = i;
                break;
            }
        }

        if (slot < 0) {
            String what = switch (part.kind) {
                case 'C' -> "chest";
                case 'D' -> "door";
                case 'B' -> "bed";
                default -> "planks";
            };
            int left = 0;
            for (int i = step; i < HOUSE.size(); i++) {
                left += "FWR".indexOf(HOUSE.get(i).kind) >= 0 ? 1 : 0;
            }
            int r = VillageWork.supply(v, sl, what, what.equals("planks") ? Math.max(1, Math.min(16, left)) : 1);
            if (r == VillageWork.CANNOT) {
                n.putString("Task", "建築資材待ち：" + what);
            }
            return r == VillageWork.ACTED;
        }

        if (!nearby(v, p)) {
            return false;
        }

        ItemStack stack = v.getInventory().getItem(slot);
        Block block = ((BlockItem)stack.getItem()).getBlock();
        BlockState original = sl.getBlockState(p);
        if (part.kind == 'F' && !original.canBeReplaced()) {
            // natural ground under the floor gives way to the builder's cobblestone
            if (!editable(v, sl, p) || !VillageWork.natural(original)
                || ((BreakEvent)MinecraftForge.EVENT_BUS.post(new BreakEvent(sl, p, original, actor(v, sl, v.getMainHandItem())))).isCanceled()) {
                n.putInt("BuildStep", step + 1);
                return false;
            }

            sl.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
        }

        BlockState state = block.defaultBlockState();
        int placed = 1;
        if (part.kind == 'D' || part.kind == 'B') {
            BlockState first = part.kind == 'D'
                ? (BlockState)state.setValue(DoorBlock.HALF, DoubleBlockHalf.LOWER)
                : (BlockState)((BlockState)state.setValue(BedBlock.FACING, Direction.SOUTH)).setValue(BedBlock.PART, BedPart.FOOT);
            BlockState second = part.kind == 'D'
                ? (BlockState)first.setValue(DoorBlock.HALF, DoubleBlockHalf.UPPER)
                : (BlockState)first.setValue(BedBlock.PART, BedPart.HEAD);
            BlockPos partner = origin.offset(HOUSE.get(step + 1).offset);
            if (!placePair(v, sl, p, first, partner, second)) {
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

        stack.shrink(1);
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

    /**
     * Sort a chest: v0.17.14 groups wood, stone, fuel and ores, crops, food, wool, gear and the rest (each by id) and merges
     * part stacks, instead of plain id order.
     */
    public static boolean sort(Container c) {
        List<ItemStack> sorted = arrangement(c);
        if (sorted == null) {
            return false;
        }

        for (int i = 0; i < c.getContainerSize(); i++) {
            c.setItem(i, sorted.get(i));
        }

        c.setChanged();
        return true;
    }

    /** True when the chest is already in the order sort() would leave it. */
    public static boolean sorted(Container c) {
        List<ItemStack> sorted = arrangement(c);
        if (sorted == null) {
            return true;
        }
        for (int i = 0; i < c.getContainerSize(); i++) {
            ItemStack a = c.getItem(i);
            ItemStack b = sorted.get(i);
            if (a.isEmpty() != b.isEmpty() || !a.isEmpty() && (!ItemStack.isSameItemSameTags(a, b) || a.getCount() != b.getCount())) {
                return false;
            }
        }
        return true;
    }

    private static List<ItemStack> arrangement(Container c) {
        List<ItemStack> all = VillageReputation.snapshot(c).stream()
            .filter(s -> !s.isEmpty())
            .sorted(Comparator.<ItemStack>comparingInt(VillagerLife::shelf).thenComparing(s -> BuiltInRegistries.ITEM.getKey(s.getItem()).toString()))
            .toList();
        SimpleContainer sorted = new SimpleContainer(c.getContainerSize());

        for (ItemStack item : all) {
            if (!sorted.addItem(item.copy()).isEmpty()) {
                return null;
            }
        }

        List<ItemStack> out = new ArrayList<>();
        for (int i = 0; i < sorted.getContainerSize(); i++) {
            out.add(sorted.getItem(i));
        }
        return out;
    }

    private static int shelf(ItemStack s) {
        String id = BuiltInRegistries.ITEM.getKey(s.getItem()).getPath();
        if (s.is(ItemTags.LOGS) || s.is(ItemTags.PLANKS) || s.is(ItemTags.WOODEN_SLABS) || s.is(Items.STICK) || s.is(ItemTags.SAPLINGS)) {
            return 0;
        } else if (id.contains("cobble") || id.contains("stone") || id.contains("deepslate") || id.equals("dirt") || id.equals("gravel") || id.contains("sand")) {
            return 1;
        } else if (s.is(Items.COAL) || s.is(Items.CHARCOAL) || id.endsWith("_ingot") || id.startsWith("raw_") || id.endsWith("_nugget") || id.contains("diamond")
            || id.contains("emerald")) {
            return 2;
        } else if (id.endsWith("_seeds") || s.is(Items.WHEAT) || s.is(Items.BONE_MEAL)) {
            return 3;
        } else if (s.has(DataComponents.FOOD)) {
            return 4;
        } else if (s.is(ItemTags.WOOL)) {
            return 5;
        } else if (s.isDamageableItem()) {
            return 6;
        }
        return 7;
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

    private static record BuildPart(BlockPos offset, char kind, boolean charge) {
        BuildPart(BlockPos offset, char kind) {
            this(offset, kind, true);
        }
    }
}
