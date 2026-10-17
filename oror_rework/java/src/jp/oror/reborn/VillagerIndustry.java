package jp.oror.reborn;

import com.google.common.collect.ImmutableSet;
import com.mojang.authlib.GameProfile;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.GlobalPos;
import net.minecraft.core.Direction.Plane;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.TagKey;
import net.minecraft.world.Container;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.ai.memory.WalkTarget;
import net.minecraft.world.entity.ai.village.poi.PoiType;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.npc.VillagerProfession;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.item.crafting.SingleRecipeInput;
import net.minecraft.world.item.trading.ItemCost;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.ClipContext.Fluid;
import net.minecraft.world.level.block.AbstractFurnaceBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.AbstractFurnaceBlockEntity;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.FurnaceBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.HitResult.Type;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.event.entity.living.LivingDeathEvent;
import net.neoforged.neoforge.event.entity.living.LivingDropsEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent.EntityInteract;
import net.neoforged.neoforge.event.level.BlockEvent.BreakEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent.Post;
import net.neoforged.neoforge.event.village.VillagerTradesEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class VillagerIndustry {
    public static final String TAG = "OrorIndustry";
    public static final DeferredRegister<PoiType> POIS = DeferredRegister.create(Registries.POINT_OF_INTEREST_TYPE, "oror_supreme_bosses");
    public static final DeferredRegister<VillagerProfession> PROFESSIONS = DeferredRegister.create(Registries.VILLAGER_PROFESSION, "oror_supreme_bosses");
    public static final DeferredHolder<PoiType, PoiType> FURNACE_POI = POIS.register(
        "mining_furnace", () -> new PoiType(ImmutableSet.copyOf(Blocks.FURNACE.getStateDefinition().getPossibleStates()), 1, 1)
    );
    public static final DeferredHolder<VillagerProfession, VillagerProfession> MINER = PROFESSIONS.register(
        "miner",
        () -> new VillagerProfession(
                "oror_supreme_bosses:miner",
                p -> p.is(FURNACE_POI.getKey()),
                p -> p.is(FURNACE_POI.getKey()),
                ImmutableSet.of(),
                ImmutableSet.of(),
                SoundEvents.VILLAGER_WORK_TOOLSMITH
            )
    );
    private static final TagKey<Block> TUNNEL = TagKey.create(Registries.BLOCK, ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "miner_tunnel"));

    private VillagerIndustry() {
    }

    public static CompoundTag data(Villager v) {
        CompoundTag root = v.getPersistentData();
        if (!root.contains("OrorIndustry", 10)) {
            root.put("OrorIndustry", new CompoundTag());
        }

        return root.getCompound("OrorIndustry");
    }

    public static SimpleContainer cargo(Villager v) {
        SimpleContainer c = new SimpleContainer(9);
        c.fromTag(data(v).getList("Cargo", 10), v.registryAccess());
        return c;
    }

    private static void saveCargo(Villager v, SimpleContainer cargo) {
        data(v).put("Cargo", cargo.createTag(v.registryAccess()));
    }

    public static boolean miner(Villager v) {
        return v.getVillagerData().getProfession() == MINER.get();
    }

    public static BlockPos station(Villager v) {
        CompoundTag n = data(v);
        return n.contains("Station") ? BlockPos.of(n.getLong("Station")) : null;
    }

    public static boolean hire(Villager v, BlockPos at, Player player) {
        if (v.level() instanceof ServerLevel sl
            && !v.isBaby()
            && sl.hasChunkAt(at)
            && sl.getBlockState(at).is(Blocks.FURNACE)
            && sl.getBlockEntity(at) instanceof FurnaceBlockEntity furnace) {
            CompoundTag owner = furnace.getPersistentData();
            if (owner.hasUUID("OrorMiner") && !owner.getUUID("OrorMiner").equals(v.getUUID())) {
                return false;
            }

            BlockPos old = station(v);
            if (old != null
                && !old.equals(at)
                && sl.hasChunkAt(old)
                && sl.getBlockEntity(old) instanceof FurnaceBlockEntity previous
                && previous.getPersistentData().hasUUID("OrorMiner")
                && previous.getPersistentData().getUUID("OrorMiner").equals(v.getUUID())) {
                previous.getPersistentData().remove("OrorMiner");
                previous.setChanged();
            }

            owner.putUUID("OrorMiner", v.getUUID());
            furnace.setChanged();
            CompoundTag n = data(v);
            n.putLong("Station", at.asLong());
            n.putString("Dimension", sl.dimension().location().toString());
            if (player != null) {
                n.putUUID("Owner", player.getUUID());
            }

            n.putString("State", "鉱脈を探しています");
            n.remove("Target");
            n.putLong("NextWork", 0L);
            if (!miner(v)) {
                v.releasePoi(MemoryModuleType.JOB_SITE);
                v.setVillagerData(v.getVillagerData().setProfession((VillagerProfession)MINER.get()));
                v.setOffers(null);
                v.refreshBrain(sl);
            }

            v.getBrain().setMemory(MemoryModuleType.JOB_SITE, GlobalPos.of(sl.dimension(), at));
            v.setPersistenceRequired();
            return true;
        }

        return false;
    }

    public static void interact(EntityInteract e) {
        if (e.getHand() == InteractionHand.MAIN_HAND
            && e.getTarget() instanceof Villager v
            && v.level() instanceof ServerLevel sl
            && (Boolean)RebornConfig.MINERS.get()) {
            Player p = e.getEntity();
            ItemStack stack = p.getItemInHand(e.getHand());
            if (stack.is(Items.FURNACE) && !v.isBaby() && v.getVillagerData().getProfession() != VillagerProfession.NITWIT) {
                BlockPos at = null;

                for (BlockPos pos : BlockPos.betweenClosed(v.blockPosition().offset(-4, -2, -4), v.blockPosition().offset(4, 2, 4))) {
                    if (sl.hasChunkAt(pos) && sl.getBlockState(pos).is(Blocks.FURNACE)) {
                        BlockEntity posx = sl.getBlockEntity(pos);
                        if (posx instanceof FurnaceBlockEntity) {
                            FurnaceBlockEntity f = (FurnaceBlockEntity)posx;
                            if ((!f.getPersistentData().hasUUID("OrorMiner") || f.getPersistentData().getUUID("OrorMiner").equals(v.getUUID()))
                                && (at == null || pos.distSqr(v.blockPosition()) < at.distSqr(v.blockPosition()))) {
                                at = pos.immutable();
                            }
                        }
                    }
                }

                boolean placed = false;
                if (at == null) {
                    for (Direction direction : Plane.HORIZONTAL) {
                        BlockPos posx = v.blockPosition().relative(direction, 2);
                        if (sl.hasChunkAt(posx)
                            && sl.getBlockState(posx).canBeReplaced()
                            && !sl.getBlockState(posx.below()).isAir()
                            && sl.noCollision(new AABB(posx))) {
                            BlockPlaceContext context = new BlockPlaceContext(
                                p, e.getHand(), stack, new BlockHitResult(Vec3.atCenterOf(posx.below()).add(0.0, 0.5, 0.0), Direction.UP, posx.below(), false)
                            );
                            if (((BlockItem)Items.FURNACE).place(context).consumesAction()) {
                                at = posx;
                                placed = true;
                                break;
                            }
                        }
                    }
                }

                if (at != null && hire(v, at, p)) {
                    if (!placed && !p.isCreative()) {
                        stack.shrink(1);
                    }

                    p.sendSystemMessage(Component.literal("採掘精錬師になりました。竈の隣にチェストと燃料を用意してください。"));
                } else {
                    p.sendSystemMessage(Component.literal("空いている竈か、竈を置ける場所が必要です。"));
                }

                e.setCancellationResult(InteractionResult.SUCCESS);
                e.setCanceled(true);
            } else if (miner(v) && p.isShiftKeyDown() && stack.isEmpty()) {
                SimpleContainer c = cargo(v);

                for (int i = 0; i < c.getContainerSize(); i++) {
                    ItemStack item = c.getItem(i);
                    if (!item.isEmpty()) {
                        p.getInventory().add(item);
                        c.setItem(i, item);
                    }
                }

                saveCargo(v, c);
                p.sendSystemMessage(Component.literal(status(v)));
                e.setCancellationResult(InteractionResult.SUCCESS);
                e.setCanceled(true);
            }
        }
    }

    public static void trades(VillagerTradesEvent e) {
        if (e.getType() == MINER.get()) {
            Item[] sell = new Item[]{Items.TORCH, Items.IRON_PICKAXE, Items.DIAMOND_PICKAXE, Items.NETHERITE_PICKAXE, Items.NETHERITE_INGOT};
            Item[] buy = new Item[]{Items.COAL, Items.RAW_IRON, Items.RAW_COPPER, Items.RAW_GOLD, Items.DIAMOND};

            for (int rank = 1; rank <= 5; rank++) {
                int r = rank;
                e.getTrades().get(rank)
                    .add((entity, random) -> new MerchantOffer(new ItemCost(buy[r - 1], r == 5 ? 2 : 8), Items.EMERALD.getDefaultInstance(), 16, r * 5, 0.05F));
                e.getTrades().get(rank)
                    .add(
                        (entity, random) -> new MerchantOffer(
                                new ItemCost(Items.EMERALD, r == 1 ? 1 : r * 4), new ItemStack(sell[r - 1], r == 1 ? 16 : 1), 12, r * 8, 0.05F
                            )
                    );
            }
        }
    }

    public static void tick(Post e) {
        if (e.getEntity() instanceof Villager v
            && v.level() instanceof ServerLevel sl
            && (Boolean)RebornConfig.MINERS.get()
            && !v.isNoAi()
            && !v.isBaby()
            && v.isAlive()
            && miner(v)) {
            CompoundTag n = data(v);
            long now = sl.getGameTime();
            if (now < n.getLong("NextWork")) {
                return;
            }

            n.putLong("NextWork", now + 5L);
            if (station(v) == null) {
                Optional<GlobalPos> memory = v.getBrain().getMemory(MemoryModuleType.JOB_SITE);
                if (memory.isPresent() && memory.get().dimension().equals(sl.dimension())) {
                    hire(v, memory.get().pos(), null);
                }
            }

            BlockPos at = station(v);
            if (at != null && n.getString("Dimension").equals(sl.dimension().location().toString())) {
                if (!sl.hasChunkAt(at)) {
                    n.putString("State", "職場の読み込み待ち");
                    return;
                }

                if (sl.getBlockEntity(at) instanceof FurnaceBlockEntity furnace && sl.getBlockState(at).is(Blocks.FURNACE)) {
                    if (furnace.getPersistentData().hasUUID("OrorMiner") && !furnace.getPersistentData().getUUID("OrorMiner").equals(v.getUUID())) {
                        n.putString("State", "この竈は別の職人が使用中");
                        return;
                    }

                    furnace.getPersistentData().putUUID("OrorMiner", v.getUUID());
                    if (AdaptiveCombat.enemy(v, v.getTarget())) {
                        n.putString("State", "村を防衛しています");
                        return;
                    }

                    if (v.distanceToSqr(Vec3.atCenterOf(at)) > Math.pow((double)((Integer)RebornConfig.MINER_RANGE.get() + 4), 2.0)) {
                        walk(v, at, 1.1F, 2);
                        n.putString("State", "職場へ戻っています");
                        return;
                    }

                    SimpleContainer c = cargo(v);
                    if (v.distanceToSqr(Vec3.atCenterOf(at)) <= 16.0 || hasCargo(c) || !furnace.getItem(2).isEmpty() || !furnace.getItem(0).isEmpty()) {
                        if (v.distanceToSqr(Vec3.atCenterOf(at)) > 16.0) {
                            returnTo(v, at, sl);
                            n.putString("State", "鉱石を竈へ運んでいます");
                            return;
                        }

                        service(v, furnace, c, at, sl);
                        blast(v, furnace, at, sl);
                        saveCargo(v, c);
                        if (n.getString("State").equals("保管場所が満杯") || n.getString("State").equals("燃料待ち")) {
                            return;
                        }
                    }

                    if (!sl.getGameRules().getBoolean(GameRules.RULE_MOBGRIEFING)) {
                        n.putString("State", "採掘停止：mobGriefing=false");
                        return;
                    }

                    if (!c.canAddItem(Items.COBBLESTONE.getDefaultInstance())) {
                        n.putString("State", "保管場所が満杯");
                        return;
                    }

                    BlockPos target = n.contains("Target") ? BlockPos.of(n.getLong("Target")) : null;
                    if (target == null || !sl.hasChunkAt(target) || !ore(sl.getBlockState(target)) || !within(v, target)) {
                        target = scan(v, sl);
                        if (target == null) {
                            n.putString("State", "鉱脈を探しています");
                            return;
                        }

                        n.putLong("Target", target.asLong());
                    }

                    v.getLookControl().setLookAt((double)target.getX() + 0.5, (double)target.getY() + 0.5, (double)target.getZ() + 0.5, 40.0F, 40.0F);
                    ItemStack tool = MobLevels.weapon(v, "pickaxe");
                    v.setItemSlot(EquipmentSlot.MAINHAND, tool);
                    MobMind.data(v).remove("Selected");
                    BlockHitResult hit = sl.clip(
                        new ClipContext(v.getEyePosition(), Vec3.atCenterOf(target), net.minecraft.world.level.ClipContext.Block.COLLIDER, Fluid.NONE, v)
                    );
                    BlockPos nearest = hit.getType() == Type.BLOCK ? hit.getBlockPos() : target;
                    if (v.distanceToSqr(Vec3.atCenterOf(nearest)) <= 12.25 && !sl.getBlockState(nearest).isAir()) {
                        v.getNavigation().stop();
                        v.getBrain().eraseMemory(MemoryModuleType.WALK_TARGET);
                        if (now < n.getLong("NextDig")) {
                            n.putString("State", "ドリルで掘削しています");
                            return;
                        }

                        n.putLong("NextDig", now + (long)Math.max(8, 72 - MobLevels.level(v) * 10));
                        boolean excavated = excavate(v, nearest, c, sl, tool);
                        saveCargo(v, c);
                        n.putString("State", excavated ? "採掘しています" : "掘削できない障害物");
                        if (!excavated) {
                            n.remove("Target");
                            n.putLong("NextWork", now + 40L);
                        }

                        return;
                    }

                    int dx = Integer.signum(target.getX() - v.blockPosition().getX());
                    int dz = Integer.signum(target.getZ() - v.blockPosition().getZ());
                    if (Math.abs((double)target.getX() - v.getX()) >= Math.abs((double)target.getZ() - v.getZ())) {
                        dz = 0;
                    } else {
                        dx = 0;
                    }

                    BlockPos step = v.blockPosition().offset(dx, 0, dz);
                    if (target.getY() < v.blockPosition().getY() - 1) {
                        step = step.below();
                    }

                    if (target.getY() > v.blockPosition().getY() + 1) {
                        step = step.above();
                    }

                    boolean blocked = false;

                    for (BlockPos part : List.of(step.above(), step)) {
                        if (!sl.getBlockState(part).getCollisionShape(sl, part).isEmpty()) {
                            blocked = true;
                            if (now >= n.getLong("NextDig")) {
                                n.putLong("NextDig", now + (long)Math.max(8, 72 - MobLevels.level(v) * 10));
                                excavate(v, part, c, sl, tool);
                                saveCargo(v, c);
                            }
                            break;
                        }
                    }

                    if (!blocked && sl.getFluidState(step).isEmpty() && !sl.getBlockState(step.below()).isAir()) {
                        walk(v, step, 1.15F, 0);
                    }

                    n.putString("State", blocked ? "通路を掘削しています" : "鉱脈へ移動しています");
                    return;
                }

                n.putString("State", "職場の竈がありません");
                return;
            }

            n.putString("State", "竈の登録待ち");
            return;
        }
    }

    private static boolean hasCargo(Container c) {
        for (int i = 0; i < c.getContainerSize(); i++) {
            if (!c.getItem(i).isEmpty()) {
                return true;
            }
        }

        return false;
    }

    public static boolean ore(BlockState s) {
        return s.is(net.neoforged.neoforge.common.Tags.Blocks.ORES);
    }

    private static boolean within(Villager v, BlockPos p) {
        BlockPos at = station(v);
        int r = (Integer)RebornConfig.MINER_RANGE.get();
        int d = (Integer)RebornConfig.MINER_DEPTH.get();
        return at != null
            && Math.abs(p.getX() - at.getX()) <= r
            && Math.abs(p.getZ() - at.getZ()) <= r
            && p.getY() >= at.getY() - d
            && p.getY() <= at.getY() + 2;
    }

    private static BlockPos scan(Villager v, ServerLevel sl) {
        CompoundTag n = data(v);
        BlockPos at = station(v);
        int radius = Math.min((Integer)RebornConfig.MINER_RANGE.get(), 6 + MobLevels.level(v) * 2);
        int side = radius * 2 + 1;
        int depth = (Integer)RebornConfig.MINER_DEPTH.get() + 3;
        int total = side * side * depth;
        int cursor = Math.floorMod(n.getInt("Scan"), total);
        BlockPos best = null;
        double cost = Double.MAX_VALUE;

        for (int i = 0; i < 64; i++) {
            int index = (cursor + i) % total;
            BlockPos p = at.offset(index % side - radius, 2 - index / (side * side), index / side % side - radius);
            if (p.getY() >= sl.getMinBuildHeight() && sl.hasChunkAt(p) && sl.getWorldBorder().isWithinBounds(p) && ore(sl.getBlockState(p))) {
                double score = p.distSqr(v.blockPosition());
                if (score < cost) {
                    best = p;
                    cost = score;
                }
            }
        }

        n.putInt("Scan", (cursor + 64) % total);
        n.putInt("Scanned", Math.min(2147483583, n.getInt("Scanned")) + 64);
        return best;
    }

    public static boolean excavate(Villager v, BlockPos p, SimpleContainer c, ServerLevel sl, ItemStack tool) {
        if (sl.getGameRules().getBoolean(GameRules.RULE_MOBGRIEFING)
            && within(v, p)
            && sl.hasChunkAt(p)
            && sl.getWorldBorder().isWithinBounds(p)
            && !(v.distanceToSqr(Vec3.atCenterOf(p)) > 12.25)) {
            BlockState s = sl.getBlockState(p);
            if (!s.isAir()
                && sl.getBlockEntity(p) == null
                && !(s.getDestroySpeed(sl, p) < 0.0F)
                && !(s.getDestroySpeed(sl, p) > 50.0F)
                && s.getFluidState().isEmpty()
                && (ore(s) || s.is(TUNNEL))
                && !VillageReputation.villageOwned(sl, p)
                && tool.isCorrectToolForDrops(s)) {
                for (Direction d : Direction.values()) {
                    if (!sl.getFluidState(p.relative(d)).isEmpty()) {
                        return false;
                    }
                }

                CompoundTag n = data(v);
                FakePlayer fake = FakePlayerFactory.get(sl, new GameProfile(n.hasUUID("Owner") ? n.getUUID("Owner") : v.getUUID(), "[OROR Miner]"));
                fake.setItemInHand(InteractionHand.MAIN_HAND, tool);
                if (((BreakEvent)NeoForge.EVENT_BUS.post(new BreakEvent(sl, p, s, fake))).isCanceled()) {
                    return false;
                } else {
                    List<ItemStack> drops = Block.getDrops(s, sl, p, null, fake, tool);
                    SimpleContainer simulated = new SimpleContainer(c.getContainerSize());

                    for (int i = 0; i < c.getContainerSize(); i++) {
                        simulated.setItem(i, c.getItem(i).copy());
                    }

                    for (ItemStack drop : drops) {
                        if (!simulated.addItem(drop.copy()).isEmpty()) {
                            return false;
                        }
                    }

                    if (!sl.destroyBlock(p, false, v)) {
                        return false;
                    } else {
                        for (ItemStack dropx : drops) {
                            ItemStack remaining = c.addItem(dropx);
                            if (!remaining.isEmpty()) {
                                throw new IllegalStateException("Mining capacity changed on server thread");
                            }
                        }

                        n.putInt("BlocksMined", n.getInt("BlocksMined") + 1);
                        if (ore(s)) {
                            n.putInt("OresMined", n.getInt("OresMined") + 1);
                        }

                        MobMind.practice(v, "terrain", 2);
                        v.swing(InteractionHand.MAIN_HAND);
                        sl.sendParticles(ParticleTypes.CRIT, (double)p.getX() + 0.5, (double)p.getY() + 0.5, (double)p.getZ() + 0.5, 4, 0.2, 0.2, 0.2, 0.02);
                        sl.playSound(null, p, SoundEvents.STONE_BREAK, SoundSource.BLOCKS, 0.6F, 1.2F);
                        return true;
                    }
                }
            } else {
                return false;
            }
        } else {
            return false;
        }
    }

    private static void walk(Villager v, BlockPos at, float speed, int distance) {
        // v0.17.9: a working pace whatever the miner's speed bonuses (1.1x on a boosted villager was a sprint)
        float pace = VillageAI.pace(v, VillageAI.WORK * speed / 1.1F);
        v.getBrain().setMemory(MemoryModuleType.WALK_TARGET, new WalkTarget(at, pace, distance));
        v.getNavigation().moveTo((double)at.getX() + 0.5, (double)at.getY(), (double)at.getZ() + 0.5, (double)pace);
    }

    private static void returnTo(Villager v, BlockPos at, ServerLevel sl) {
        walk(v, at, 1.15F, 2);
    }

    private static List<Container> boxes(ServerLevel sl, BlockPos at) {
        ArrayList<Container> out = new ArrayList<>();

        for (Direction direction : Direction.values()) {
            BlockPos p = at.relative(direction);
            if (sl.hasChunkAt(p)) {
                BlockEntity var9 = sl.getBlockEntity(p);
                if (var9 instanceof Container) {
                    Container c = (Container)var9;
                    if (!(c instanceof AbstractFurnaceBlockEntity)) {
                        out.add(c);
                    }
                }
            }
        }

        return out;
    }

    public static boolean smeltable(ItemStack item, ServerLevel sl) {
        return !item.isEmpty()
            && (
                item.is(net.neoforged.neoforge.common.Tags.Items.RAW_MATERIALS)
                    || item.is(net.neoforged.neoforge.common.Tags.Items.ORES)
                    || item.is(net.neoforged.neoforge.common.Tags.Items.DUSTS)
            )
            && sl.getRecipeManager().getRecipeFor(RecipeType.SMELTING, new SingleRecipeInput(item), sl).isPresent();
    }

    private static ItemStack insert(Container container, ItemStack input) {
        ItemStack remaining = input.copy();

        for (int i = 0; i < container.getContainerSize() && !remaining.isEmpty(); i++) {
            if (container.canPlaceItem(i, remaining)) {
                ItemStack old = container.getItem(i);
                int room = Math.min(remaining.getMaxStackSize(), container.getMaxStackSize()) - old.getCount();
                if (old.isEmpty() || ItemStack.isSameItemSameComponents(old, remaining)) {
                    int count = Math.min(room, remaining.getCount());
                    if (count > 0) {
                        if (old.isEmpty()) {
                            container.setItem(i, remaining.copyWithCount(count));
                        } else {
                            old.grow(count);
                        }

                        remaining.shrink(count);
                        container.setChanged();
                    }
                }
            }
        }

        return remaining;
    }

    private static int movedToBoxes(List<Container> boxes, ItemStack stack) {
        int count = stack.getCount();
        ItemStack left = stack.copy();

        for (Container box : boxes) {
            left = insert(box, left);
        }

        int moved = count - left.getCount();
        stack.shrink(moved);
        return moved;
    }

    public static void service(Villager v, FurnaceBlockEntity furnace, SimpleContainer c, BlockPos at, ServerLevel sl) {
        CompoundTag n = data(v);
        List<Container> boxes = boxes(sl, at);
        ItemStack output = furnace.getItem(2);
        if (!output.isEmpty()) {
            int before = output.getCount();
            if (!boxes.isEmpty()) {
                movedToBoxes(boxes, output);
            } else if (c.canAddItem(output)) {
                ItemStack left = c.addItem(output.copy());
                output.setCount(left.getCount());
            }

            int moved = before - output.getCount();
            n.putInt("ProductsCollected", n.getInt("ProductsCollected") + moved);
            if (moved > 0) {
                MobMind.practice(v, "tactics", 1);
            }

            if (!output.isEmpty()) {
                n.putString("State", "保管場所が満杯");
                furnace.setChanged();
                return;
            }

            furnace.setItem(2, ItemStack.EMPTY);
        }

        for (int i = 0; i < c.getContainerSize(); i++) {
            ItemStack stack = c.getItem(i);
            if (!stack.isEmpty()) {
                if (AbstractFurnaceBlockEntity.isFuel(stack) && furnace.getItem(1).isEmpty()) {
                    furnace.setItem(1, stack.split(1));
                } else {
                    if (smeltable(stack, sl)) {
                        ItemStack input = furnace.getItem(0);
                        if (input.isEmpty()) {
                            furnace.setItem(0, stack.split(Math.min(64, stack.getCount())));
                            continue;
                        }

                        if (ItemStack.isSameItemSameComponents(input, stack)) {
                            int amount = Math.min(input.getMaxStackSize() - input.getCount(), stack.getCount());
                            input.grow(amount);
                            stack.shrink(amount);
                            continue;
                        }
                    }

                    if (!stack.isEmpty() && !smeltable(stack, sl)) {
                        movedToBoxes(boxes, stack);
                    }
                }
            }
        }

        if (furnace.getItem(0).isEmpty()) {
            for (Container box : boxes) {
                boolean found = false;

                for (int ix = 0; ix < box.getContainerSize(); ix++) {
                    if (smeltable(box.getItem(ix), sl)) {
                        furnace.setItem(0, box.removeItem(ix, 64));
                        found = true;
                        break;
                    }
                }

                if (found) {
                    break;
                }
            }
        }

        if (furnace.getItem(1).isEmpty() && !furnace.getItem(0).isEmpty()) {
            for (Container box : boxes) {
                boolean found = false;

                for (int ixx = 0; ixx < box.getContainerSize(); ixx++) {
                    if (AbstractFurnaceBlockEntity.isFuel(box.getItem(ixx))) {
                        furnace.setItem(1, box.removeItem(ixx, 1));
                        found = true;
                        break;
                    }
                }

                if (found) {
                    break;
                }
            }
        }

        furnace.setChanged();
        boolean needsFuel = !furnace.getItem(0).isEmpty() && furnace.getItem(1).isEmpty() && !(Boolean)sl.getBlockState(at).getValue(AbstractFurnaceBlock.LIT);
        n.putString("State", needsFuel ? "燃料待ち" : "採掘・精錬しています");
    }

    // ------------------------------------------------------------------------------------- the blast furnace (v0.17.15)
    /** An ore, raw metal or dust the furnace has no recipe for but a blast furnace has. */
    public static boolean blastOnly(ItemStack item, ServerLevel sl) {
        return ore(item) && !sl.getRecipeManager().getRecipeFor(RecipeType.SMELTING, new SingleRecipeInput(item), sl).isPresent() && blastable(item, sl);
    }

    private static boolean blastable(ItemStack item, ServerLevel sl) {
        return ore(item) && sl.getRecipeManager().getRecipeFor(RecipeType.BLASTING, new SingleRecipeInput(item), sl).isPresent();
    }

    private static boolean ore(ItemStack item) {
        return !item.isEmpty()
            && (
                item.is(net.neoforged.neoforge.common.Tags.Items.RAW_MATERIALS)
                    || item.is(net.neoforged.neoforge.common.Tags.Items.ORES)
                    || item.is(net.neoforged.neoforge.common.Tags.Items.DUSTS)
            );
    }

    private static Item item(String id) {
        return (Item)net.minecraft.core.registries.BuiltInRegistries.ITEM.get(ResourceLocation.withDefaultNamespace(id));
    }

    /**
     * v0.17.15: what the furnace cannot smelt goes to a blast furnace. Ores, raw metal and dusts that only have a blasting
     * recipe wait in the station's chests until a blast furnace stands within four blocks of the furnace; then the miner
     * keeps it loaded, fuelled and emptied like the furnace, and lets it take ores the furnace is too busy for (a blast
     * furnace smelts them twice as fast). A miner without one builds it the crafting way: five iron ingots, a furnace
     * (eight cobblestone) and three smooth stone, the smooth stone smelted in its own furnace from stone and cobblestone.
     */
    private static void blast(Villager v, FurnaceBlockEntity furnace, BlockPos at, ServerLevel sl) {
        CompoundTag n = data(v);
        List<Container> boxes = boxes(sl, at);
        Block block = item("blast_furnace") instanceof BlockItem b ? b.getBlock() : null;
        if (block == null || boxes.isEmpty()) {
            return;
        }
        BlockPos found = null;
        for (BlockPos p : BlockPos.betweenClosed(at.offset(-4, -2, -4), at.offset(4, 2, 4))) {
            if (sl.getBlockState(p).is(block) && sl.getBlockEntity(p) instanceof AbstractFurnaceBlockEntity) {
                found = p.immutable();
                break;
            }
        }
        if (found != null) {
            AbstractFurnaceBlockEntity kiln = (AbstractFurnaceBlockEntity)sl.getBlockEntity(found);
            ItemStack output = kiln.getItem(2);
            if (!output.isEmpty()) {
                int moved = movedToBoxes(boxes, output);
                n.putInt("ProductsCollected", n.getInt("ProductsCollected") + moved);
                if (output.isEmpty()) {
                    kiln.setItem(2, ItemStack.EMPTY);
                }
            }
            if (kiln.getItem(0).isEmpty()) {
                // what only it can smelt first, then ores the furnace has queued behind its own load
                boolean busy = !furnace.getItem(0).isEmpty();
                ItemStack input = take(boxes, s -> blastOnly(s, sl), 64);
                if (input.isEmpty() && busy) {
                    input = take(boxes, s -> blastable(s, sl), 64);
                }
                if (!input.isEmpty()) {
                    kiln.setItem(0, input);
                }
            }
            if (kiln.getItem(1).isEmpty() && !kiln.getItem(0).isEmpty()) {
                ItemStack fuel = take(boxes, AbstractFurnaceBlockEntity::isFuel, 1);
                if (!fuel.isEmpty()) {
                    kiln.setItem(1, fuel);
                }
            }
            kiln.setChanged();
            if (!kiln.getItem(0).isEmpty()) {
                n.putString("State", "竈と溶鉱炉で精錬しています");
            }
            return;
        }
        if (count(boxes, s -> blastOnly(s, sl)) == 0) {
            return;
        }
        // build one: 5 iron ingots, a furnace (8 cobblestone) and 3 smooth stone
        Item iron = item("iron_ingot");
        Item smooth = item("smooth_stone");
        Item stone = item("stone");
        int needSmooth = Math.max(0, 3 - count(boxes, s -> s.is(smooth)));
        int cobble = count(boxes, s -> s.is(Items.COBBLESTONE));
        if (needSmooth > 0 && furnace.getItem(0).isEmpty()) {
            // smooth stone is stone smelted again; stone is cobblestone smelted
            ItemStack feed = take(boxes, s -> s.is(stone), needSmooth);
            if (feed.isEmpty() && cobble > 8) {
                feed = take(boxes, s -> s.is(Items.COBBLESTONE), Math.min(needSmooth, cobble - 8));
            }
            if (!feed.isEmpty()) {
                furnace.setItem(0, feed);
                furnace.setChanged();
            }
        }
        if (needSmooth > 0 || count(boxes, s -> s.is(iron)) < 5 || cobble < 8) {
            n.putString("State", "溶鉱炉の材料集め（鉄インゴット" + Math.min(5, count(boxes, s -> s.is(iron))) + "/5・丸石" + Math.min(8, cobble)
                + "/8・滑らかな石" + (3 - needSmooth) + "/3）");
            return;
        }
        if (!sl.getGameRules().getBoolean(GameRules.RULE_MOBGRIEFING)) {
            return;
        }
        for (Direction d : Plane.HORIZONTAL) {
            BlockPos p = at.relative(d);
            if (sl.getBlockState(p).canBeReplaced() && sl.getFluidState(p).isEmpty() && !sl.getBlockState(p.below()).canBeReplaced()
                && sl.noCollision(new AABB(p))) {
                take(boxes, s -> s.is(iron), 5);
                take(boxes, s -> s.is(Items.COBBLESTONE), 8);
                take(boxes, s -> s.is(smooth), 3);
                sl.setBlock(p, block.defaultBlockState(), 3);
                sl.sendParticles(ParticleTypes.CLOUD, p.getX() + 0.5, p.getY() + 1.0, p.getZ() + 0.5, 8, 0.3, 0.2, 0.3, 0.02);
                RelicEffects.sound(sl, p, SoundEvents.ANVIL_LAND, 0.6F, 1.2F);
                v.swing(InteractionHand.MAIN_HAND);
                n.putString("State", "溶鉱炉を組み立てました");
                return;
            }
        }
        n.putString("State", "溶鉱炉を置く場所がありません");
    }

    private static int count(List<Container> boxes, java.util.function.Predicate<ItemStack> is) {
        int n = 0;
        for (Container box : boxes) {
            for (int i = 0; i < box.getContainerSize(); i++) {
                if (!box.getItem(i).isEmpty() && is.test(box.getItem(i))) {
                    n += box.getItem(i).getCount();
                }
            }
        }
        return n;
    }

    /** Take up to n of one kind (the first matching stack's item) out of the chests. */
    private static ItemStack take(List<Container> boxes, java.util.function.Predicate<ItemStack> is, int n) {
        ItemStack got = ItemStack.EMPTY;
        for (Container box : boxes) {
            for (int i = 0; i < box.getContainerSize() && got.getCount() < n; i++) {
                ItemStack st = box.getItem(i);
                if (st.isEmpty() || !is.test(st) || !got.isEmpty() && !ItemStack.isSameItemSameComponents(got, st)) {
                    continue;
                }
                ItemStack part = box.removeItem(i, Math.min(n - got.getCount(), st.getCount()));
                if (got.isEmpty()) {
                    got = part;
                } else {
                    got.grow(part.getCount());
                }
                box.setChanged();
            }
        }
        return got;
    }

    public static String status(Villager v) {
        CompoundTag n = data(v);
        int carried = 0;
        SimpleContainer c = cargo(v);

        for (int i = 0; i < c.getContainerSize(); i++) {
            carried += c.getItem(i).getCount();
        }

        return "採掘精錬師 / 取引Lv."
            + v.getVillagerData().getLevel()
            + " / "
            + n.getString("State")
            + " / 採掘="
            + n.getInt("OresMined")
            + "鉱石 / 回収="
            + n.getInt("ProductsCollected")
            + " / 運搬="
            + carried;
    }

    public static void death(LivingDeathEvent e) {
        if (e.getEntity() instanceof Villager v && v.level() instanceof ServerLevel sl && miner(v)) {
            BlockPos at = station(v);
            if (at != null
                && sl.hasChunkAt(at)
                && sl.getBlockEntity(at) instanceof FurnaceBlockEntity f
                && f.getPersistentData().hasUUID("OrorMiner")
                && f.getPersistentData().getUUID("OrorMiner").equals(v.getUUID())) {
                f.getPersistentData().remove("OrorMiner");
                f.setChanged();
            }

            return;
        }
    }

    public static void drops(LivingDropsEvent e) {
        if (e.getEntity() instanceof Villager v && miner(v)) {
            SimpleContainer c = cargo(v);

            for (int i = 0; i < c.getContainerSize(); i++) {
                ItemStack stack = c.removeItemNoUpdate(i);
                if (!stack.isEmpty()) {
                    e.getDrops().add(new ItemEntity(v.level(), v.getX(), v.getY(), v.getZ(), stack));
                }
            }

            saveCargo(v, c);
            return;
        }
    }
}
