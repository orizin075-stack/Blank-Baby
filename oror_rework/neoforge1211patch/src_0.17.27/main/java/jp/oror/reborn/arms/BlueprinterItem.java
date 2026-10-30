package jp.oror.reborn.arms;

import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * ブループリンター. Sneak + use switches between SCAN and PRINT. In SCAN, use on a block (up to 64 blocks away) marks
 * one corner, then the other, and the box between them is scanned (64 x 64 x 64 at most). In PRINT, use on a block
 * (up to 256 blocks away) shows where the copy will stand, centred there and turned the way you face; use the same
 * spot again within ten seconds to print it. Printing costs Matter Cartridges (see {@link Blueprints}).
 */
public class BlueprinterItem extends Item {
    static final String TAG = "OrorBlueprinter";
    static final double SCAN_REACH = 64;
    static final double PRINT_REACH = 256;

    public BlueprinterItem(Properties properties) {
        super(properties);
    }

    static CompoundTag data(ItemStack stack) {
        return stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag().getCompound(TAG);
    }

    static void save(ItemStack stack, CompoundTag tag) {
        CustomData.update(DataComponents.CUSTOM_DATA, stack, root -> root.put(TAG, tag));
    }

    static boolean printing(CompoundTag tag) {
        return tag.getBoolean("Print");
    }

    // useOn is left to pass: use() casts its own ray, which picks the same block within reach and also reaches past it

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide || !(player instanceof ServerPlayer sp) || !(level instanceof ServerLevel server)) {
            return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
        }
        CompoundTag tag = data(stack);
        if (player.isShiftKeyDown()) {
            boolean print = !printing(tag);
            tag.putBoolean("Print", print);
            tag.remove("A");
            tag.remove("Pending");
            save(stack, tag);
            sp.displayClientMessage(Component.translatable(print ? "oror.blueprinter.mode_print" : "oror.blueprinter.mode_scan")
                .withStyle(print ? ChatFormatting.AQUA : ChatFormatting.GOLD), true);
            return InteractionResultHolder.success(stack);
        }
        BlockHitResult hit = pick(player, printing(tag) ? PRINT_REACH : SCAN_REACH);
        if (hit == null) {
            sp.displayClientMessage(Component.translatable("oror.blueprinter.no_target").withStyle(ChatFormatting.RED), true);
            return InteractionResultHolder.fail(stack);
        }
        if (printing(tag)) {
            Blueprints.printClick(server, sp, stack, tag, hit.getBlockPos().relative(hit.getDirection()));
        } else {
            Blueprints.scanClick(server, sp, stack, tag, hit.getBlockPos());
        }
        return InteractionResultHolder.success(stack);
    }

    static BlockHitResult pick(Player player, double reach) {
        Vec3 eye = player.getEyePosition();
        Vec3 end = eye.add(player.getLookAngle().scale(reach));
        BlockHitResult hit = player.level().clip(new ClipContext(eye, end, ClipContext.Block.OUTLINE, ClipContext.Fluid.NONE, player));
        return hit.getType() == HitResult.Type.BLOCK ? hit : null;
    }

    @Override
    public boolean isFoil(ItemStack stack) {
        return printing(data(stack));
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> tooltip, TooltipFlag flag) {
        CompoundTag tag = data(stack);
        tooltip.add(Component.translatable(printing(tag) ? "oror.blueprinter.mode_print" : "oror.blueprinter.mode_scan")
            .withStyle(printing(tag) ? ChatFormatting.AQUA : ChatFormatting.GOLD));
        if (tag.hasUUID("Blueprint")) {
            int[] size = tag.getIntArray("Size");
            if (size.length == 3) {
                tooltip.add(Component.translatable("oror.blueprinter.stored", size[0], size[1], size[2], tag.getInt("Blocks"),
                    Blueprints.cartridges(tag.getInt("Cost"))).withStyle(ChatFormatting.WHITE));
            }
        } else {
            tooltip.add(Component.translatable("oror.blueprinter.empty").withStyle(ChatFormatting.DARK_GRAY));
        }
        ArmsItem.tooltip(getDescriptionId(), 4, tooltip);
    }
}
