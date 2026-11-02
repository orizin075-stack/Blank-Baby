package jp.oror.reborn.mixin;

import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.Tag;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

/**
 * An arrow's item when it is saved: a vanilla arrow that may not be picked up and lost its item is saved as a plain
 * arrow (as before), and (051) any other arrow-like shot with no item at all is saved with an empty compound in its
 * place, which loading reads back as the shot's default item. Saved as it was, an empty stack threw ("Cannot encode
 * empty ItemStack") and the shot was dropped from the chunk: the CI server's game tests left Superb Warfare taser darts
 * in the world that could not be saved.
 */
@Mixin(AbstractArrow.class)
public abstract class ArrowSaveMixin {
    @Redirect(method = "addAdditionalSaveData", at = @At(value = "INVOKE",
        target = "Lnet/minecraft/world/item/ItemStack;save(Lnet/minecraft/core/HolderLookup$Provider;)Lnet/minecraft/nbt/Tag;"), remap = false)
    private Tag oror$saveNonPickupArrow(ItemStack stack, HolderLookup.Provider registries) {
        if (stack.isEmpty()) {
            AbstractArrow self = (AbstractArrow) (Object) this;
            if (self.getType() == EntityType.ARROW && self.pickup == AbstractArrow.Pickup.DISALLOWED) {
                return Items.ARROW.getDefaultInstance().save(registries);
            }
            return new CompoundTag();
        }
        return stack.save(registries);
    }
}
