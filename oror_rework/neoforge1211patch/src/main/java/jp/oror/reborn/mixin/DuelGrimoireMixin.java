package jp.oror.reborn.mixin;

import jp.oror.reborn.duel.GrimoireBook;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * (059e) The user's Duel Dominion grimoire opens as a book ({@link GrimoireBook}): right-click raises it and opens it
 * (it stays in use, the reading pose, while the book is open), unless the other hand holds a bound hair to store, which
 * is Duel Dominion's own right-click as before. Without Duel Dominion this does nothing.
 */
@Pseudo
@Mixin(targets = "jp.oror.dueldominion.GrimoireItem", remap = false)
public abstract class DuelGrimoireMixin extends Item {
    private DuelGrimoireMixin(Item.Properties p) {
        super(p);
    }

    @Inject(method = "use(Lnet/minecraft/world/level/Level;Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/InteractionHand;)Lnet/minecraft/world/InteractionResultHolder;",
        at = @At("HEAD"), cancellable = true, require = 0)
    private void oror$openBook(Level level, Player player, InteractionHand hand, CallbackInfoReturnable<InteractionResultHolder<ItemStack>> cir) {
        ItemStack book = player.getItemInHand(hand);
        ItemStack other = player.getItemInHand(hand == InteractionHand.MAIN_HAND ? InteractionHand.OFF_HAND : InteractionHand.MAIN_HAND);
        if (GrimoireBook.isHair(other)) {
            return;
        }
        player.startUsingItem(hand);
        if (level.isClientSide) {
            GrimoireBook.openClient(hand);
        }
        cir.setReturnValue(InteractionResultHolder.consume(book));
    }

    /** Held open as long as the reader reads (the book's screen open). */
    @Override
    public int getUseDuration(ItemStack stack, LivingEntity entity) {
        return 72000;
    }
}
