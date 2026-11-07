package jp.oror.reborn.king;

import java.util.function.BiConsumer;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.trading.Merchant;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.item.trading.MerchantOffers;

/**
 * (054) A trading screen for one who is not a villager: the villager king's court, the rebels' camps. The offers are
 * made for the player who opens it; each trade made is told to whoever opened it (the king's favour, the rebels').
 */
public final class OrorMerchant implements Merchant {
    private Player customer;
    private final MerchantOffers offers;
    private final BiConsumer<Player, MerchantOffer> traded;

    public OrorMerchant(MerchantOffers offers, BiConsumer<Player, MerchantOffer> traded) {
        this.offers = offers;
        this.traded = traded;
    }

    /** Opens the screen for the player, titled as given. */
    public static void open(Player player, Component title, MerchantOffers offers, BiConsumer<Player, MerchantOffer> traded) {
        OrorMerchant m = new OrorMerchant(offers, traded);
        m.setTradingPlayer(player);
        m.openTradingScreen(player, title, 5);
    }

    @Override
    public void setTradingPlayer(Player player) {
        this.customer = player;
    }

    @Override
    public Player getTradingPlayer() {
        return this.customer;
    }

    @Override
    public MerchantOffers getOffers() {
        return this.offers;
    }

    @Override
    public void overrideOffers(MerchantOffers offers) {
    }

    @Override
    public void notifyTrade(MerchantOffer offer) {
        offer.increaseUses();
        if (this.customer != null && this.traded != null) {
            this.traded.accept(this.customer, offer);
        }
    }

    @Override
    public void notifyTradeUpdated(ItemStack stack) {
    }

    @Override
    public int getVillagerXp() {
        return 0;
    }

    @Override
    public void overrideXp(int xp) {
    }

    @Override
    public boolean showProgressBar() {
        return false;
    }

    @Override
    public SoundEvent getNotifyTradeSound() {
        return SoundEvents.VILLAGER_YES;
    }

    @Override
    public boolean isClientSide() {
        return false;
    }
}
