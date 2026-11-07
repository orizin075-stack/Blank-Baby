package jp.oror.reborn.king;

import net.minecraft.nbt.CompoundTag;
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

    /** The trades the player made today, by shop and offer: the offers are made anew each time the screen opens, their stock lasts the day. */
    static final String STOCK = "OrorTradeStock";

    static CompoundTag stock(Player p) {
        CompoundTag s = KingCourt.kept(p).getCompound(STOCK);
        long day = p.level().getDayTime() / 24000L;
        if (!s.contains("Day") || s.getLong("Day") != day) {
            s = new CompoundTag();
            s.putLong("Day", day);
        }
        return s;
    }

    /** Opens the shop's screen for the player with what is left of today's stock; each trade is counted against it. */
    public static void open(Player player, Component title, String shop, MerchantOffers offers, BiConsumer<Player, MerchantOffer> traded) {
        CompoundTag s = stock(player);
        for (int i = 0; i < offers.size(); i++) {
            MerchantOffer of = offers.get(i);
            for (int n = s.getInt(shop + i); n > 0 && !of.isOutOfStock(); n--) {
                of.increaseUses();
            }
        }
        open(player, title, offers, (p, of) -> {
            int i = offers.indexOf(of);
            if (i >= 0) {
                CompoundTag k = KingCourt.kept(p);
                CompoundTag st = stock(p);
                st.putInt(shop + i, st.getInt(shop + i) + 1);
                k.put(STOCK, st);
                KingCourt.keep(p, k);
            }
            if (traded != null) {
                traded.accept(p, of);
            }
        });
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
