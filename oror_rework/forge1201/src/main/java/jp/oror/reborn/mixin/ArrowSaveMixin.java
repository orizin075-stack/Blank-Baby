package jp.oror.reborn.mixin;

import net.minecraft.core.HolderLookup.Provider;
import net.minecraft.nbt.Tag;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.entity.projectile.AbstractArrow.Pickup;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

@Mixin(
    value = {AbstractArrow.class},
    remap = false
)
public abstract class ArrowSaveMixin {
    @Redirect(
        method = {"addAdditionalSaveData"},
        at = @At(
            value = "INVOKE",
            target = "Lnet/minecraft/world/item/ItemStack;save(Lnet/minecraft/core/HolderLookup$Provider;)Lnet/minecraft/nbt/Tag;"
        ),
        remap = false
    )
    private Tag oror$saveNonPickupArrow(ItemStack item, Provider registries) {
        AbstractArrow arrow = (AbstractArrow)this;
        if (item.isEmpty() && arrow.getType() == EntityType.ARROW && arrow.pickup == Pickup.DISALLOWED) {
            System.out.println("[OROR_ARROW_NBT] normalized invalid non-pickup arrow ammunition for save");
            return Items.ARROW.getDefaultInstance().save(registries);
        } else {
            return item.save(registries);
        }
    }
}
