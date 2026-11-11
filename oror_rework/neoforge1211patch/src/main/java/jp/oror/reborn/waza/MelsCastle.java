package jp.oror.reborn.waza;

import java.util.List;
import java.util.Optional;
import jp.oror.reborn.SupremeEntity;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Vec3i;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;
import net.neoforged.neoforge.event.entity.living.LivingDropsEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;
import net.neoforged.neoforge.registries.RegisterEvent;

/**
 * (057) 至高武王 メルス, as asked: he fights with his own liquid body and holds no weapon (whatever is put in his hands
 * is let go), and when he is beaten he leaves a castle: 「武王の城」, which, used on the ground, raises a fortress in
 * front of its holder (the villager fortress: walls, towers, halls, its villagers and its guards), on a stone
 * foundation down to the ground so that it does not float.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class MelsCastle {
    public static Item CASTLE;
    static final ResourceLocation FORTRESS = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "villager_fortress");

    private MelsCastle() {
    }

    static boolean isMels(Object e) {
        return e instanceof SupremeEntity b && b.spec != null && b.spec.id.equals("mels");
    }

    /** No weapon in his hands (the liquid martial artist fights with his body): let go as each tick begins and ends,
     * whatever (the mob mind's weapon choice, a mod's equipment) put it there. */
    @SubscribeEvent(priority = net.neoforged.bus.api.EventPriority.HIGHEST)
    public static void unarmedBefore(EntityTickEvent.Pre e) {
        letGo(e.getEntity());
    }

    @SubscribeEvent(priority = net.neoforged.bus.api.EventPriority.LOWEST)
    public static void unarmed(EntityTickEvent.Post e) {
        letGo(e.getEntity());
    }

    private static void letGo(net.minecraft.world.entity.Entity e) {
        if (isMels(e) && !e.level().isClientSide) {
            SupremeEntity b = (SupremeEntity) e;
            for (EquipmentSlot slot : new EquipmentSlot[]{EquipmentSlot.MAINHAND, EquipmentSlot.OFFHAND}) {
                if (!b.getItemBySlot(slot).isEmpty()) {
                    b.setItemSlot(slot, ItemStack.EMPTY);
                    b.setDropChance(slot, 0F);
                }
            }
        }
    }

    /** Beaten, he leaves the castle. */
    @SubscribeEvent
    public static void drops(LivingDropsEvent e) {
        if (isMels(e.getEntity()) && CASTLE != null && e.getEntity().level() instanceof ServerLevel sl) {
            var m = e.getEntity();
            ItemEntity it = new ItemEntity(sl, m.getX(), m.getY() + 0.5, m.getZ(), new ItemStack(CASTLE));
            it.setGlowingTag(true);
            it.setUnlimitedLifetime();
            e.getDrops().add(it);
        }
    }

    /**
     * Raises the fortress before the holder: its near wall's middle a couple of blocks ahead of the block used, its floor
     * on that block's level, a stone foundation under any part over air. Refused (false) when the ground it needs is
     * not loaded or there is no room under the sky.
     */
    public static boolean place(ServerLevel sl, BlockPos used, Direction facing, Player p) {
        Optional<StructureTemplate> t = sl.getStructureManager().get(FORTRESS);
        if (t.isEmpty()) {
            return false;
        }
        StructureTemplate template = t.get();
        Vec3i size = template.getSize();
        Direction f = facing.getAxis().isHorizontal() ? facing : Direction.NORTH;
        BlockPos floor = used.above();
        BlockPos centre = floor.relative(f, size.getZ() / 2 + 2);
        BlockPos origin = centre.offset(-size.getX() / 2, 0, -size.getZ() / 2);
        BlockPos far = origin.offset(size.getX(), 0, size.getZ());
        if (!sl.hasChunksAt(origin, far) || origin.getY() + size.getY() >= sl.getMaxBuildHeight() || origin.getY() <= sl.getMinBuildHeight() + 2) {
            if (p != null) {
                p.displayClientMessage(Component.literal("ここには城を建てられない（土地が読み込まれていないか、空が足りない）"), true);
            }
            return false;
        }
        // (058) not over what someone built: no castle in the capital or a village, none over a chest or any other block
        // with something in it, none over a house (worked wood and stone, doors, beds, glass)
        String taken = taken(sl, origin, size);
        if (taken != null) {
            if (p != null) {
                p.displayClientMessage(Component.literal("ここには城を建てられない（" + taken + "）。何も建っていない土地で使ってください"), true);
            }
            return false;
        }
        // the foundation: under every column of the footprint, stone bricks down to the ground (at most sixteen)
        BlockState stone = Blocks.STONE_BRICKS.defaultBlockState();
        for (int x = 0; x < size.getX(); x++) {
            for (int z = 0; z < size.getZ(); z++) {
                BlockPos at = origin.offset(x, -1, z);
                for (int d = 0; d < 16 && sl.getBlockState(at).canBeReplaced(); d++, at = at.below()) {
                    sl.setBlock(at, stone, Block.UPDATE_CLIENTS);
                }
            }
        }
        template.placeInWorld(sl, origin, origin, new StructurePlaceSettings().setIgnoreEntities(false), sl.random, Block.UPDATE_ALL);
        sl.playSound(null, centre, SoundEvents.BELL_RESONATE, SoundSource.BLOCKS, 2F, 0.8F);
        sl.playSound(null, centre, SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.PLAYERS, 1F, 1F);
        return true;
    }

    /** What already stands where the fortress would (null if the ground is free). */
    static String taken(ServerLevel sl, BlockPos origin, Vec3i size) {
        BlockPos far = origin.offset(size.getX() - 1, size.getY() - 1, size.getZ() - 1);
        for (BlockPos corner : new BlockPos[]{origin, far, new BlockPos(origin.getX(), origin.getY(), far.getZ()),
            new BlockPos(far.getX(), origin.getY(), origin.getZ()), origin.offset(size.getX() / 2, 0, size.getZ() / 2)}) {
            if (jp.oror.reborn.village.BuildingGuard.inCapital(corner, 64)) {
                return "王都の中";
            }
            if (jp.oror.reborn.village.BuildingGuard.inVillage(sl, corner)) {
                return "村の中";
            }
        }
        int built = 0;
        for (BlockPos q : BlockPos.betweenClosed(origin, far)) {
            BlockState st = sl.getBlockState(q);
            if (st.isAir()) {
                continue;
            }
            if (st.hasBlockEntity()) {
                return "箱などの中身のあるブロックがある";
            }
            if (st.is(net.minecraft.tags.BlockTags.PLANKS) || st.is(net.minecraft.tags.BlockTags.DOORS) || st.is(net.minecraft.tags.BlockTags.BEDS)
                || st.is(net.minecraft.tags.BlockTags.WOOL) || st.is(net.minecraft.tags.BlockTags.STONE_BRICKS)
                || st.is(net.minecraft.tags.BlockTags.STAIRS) || st.is(net.minecraft.tags.BlockTags.SLABS) || st.is(net.minecraft.tags.BlockTags.WALLS)
                || st.is(net.minecraft.tags.BlockTags.FENCES) || st.is(net.minecraft.tags.BlockTags.TRAPDOORS)
                || st.is(net.minecraft.tags.BlockTags.IMPERMEABLE)) {
                if (++built >= 12) {
                    return "建物がある";
                }
            }
        }
        return null;
    }

    static final class Castle extends Item {
        Castle(Properties p) {
            super(p);
        }

        @Override
        public InteractionResult useOn(UseOnContext ctx) {
            if (!(ctx.getLevel() instanceof ServerLevel sl)) {
                return InteractionResult.SUCCESS;
            }
            Player p = ctx.getPlayer();
            Direction facing = p != null ? p.getDirection() : ctx.getHorizontalDirection();
            if (place(sl, ctx.getClickedPos(), facing, p)) {
                if (p != null) {
                    p.displayClientMessage(Component.literal("武王の城が建った").withStyle(ChatFormatting.GOLD), false);
                    if (!p.getAbilities().instabuild) {
                        ctx.getItemInHand().shrink(1);
                    }
                }
                return InteractionResult.CONSUME;
            }
            return InteractionResult.FAIL;
        }

        @Override
        public void appendHoverText(ItemStack stack, TooltipContext ctx, List<Component> lines, TooltipFlag flag) {
            for (int i = 1; i <= 3; i++) {
                lines.add(Component.translatable("item.oror_supreme_bosses.mels_castle.desc" + i).withStyle(i == 3 ? ChatFormatting.GOLD
                    : ChatFormatting.GRAY));
            }
        }
    }

    @EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD)
    public static final class Registry {
        private Registry() {
        }

        @SubscribeEvent
        public static void register(RegisterEvent event) {
            event.register(Registries.ITEM, helper -> {
                CASTLE = new Castle(new Item.Properties().stacksTo(1).rarity(Rarity.EPIC).fireResistant()
                    .component(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, true));
                helper.register(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "mels_castle"), CASTLE);
            });
        }

        @SubscribeEvent
        public static void tab(BuildCreativeModeTabContentsEvent event) {
            if (event.getTabKey().location().equals(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "supreme_entities"))) {
                event.accept(CASTLE);
            }
        }
    }
}
