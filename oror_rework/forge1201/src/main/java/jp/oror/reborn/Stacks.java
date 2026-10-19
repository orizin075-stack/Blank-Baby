package jp.oror.reborn;

import java.util.function.Consumer;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.item.ItemStack;

/**
 * Forge 1.20.1 port: what 1.21.1 kept in an item's custom_data component lives in the stack's NBT tag. The mod's own
 * keys (OrorTemper, ...) are read and written there.
 */
public final class Stacks {
    /** A copy of the stack's tag (empty when it has none), like CustomData.copyTag(). */
    public static CompoundTag custom(ItemStack stack) {
        CompoundTag tag = stack.getTag();
        return tag == null ? new CompoundTag() : tag.copy();
    }

    /** Changes the stack's tag in place, like CustomData.update(CUSTOM_DATA, stack, f). */
    public static void update(ItemStack stack, Consumer<CompoundTag> f) {
        f.accept(stack.getOrCreateTag());
    }

    private Stacks() {
    }
}
