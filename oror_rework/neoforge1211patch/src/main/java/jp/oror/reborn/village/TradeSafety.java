package jp.oror.reborn.village;

import java.util.Optional;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.npc.AbstractVillager;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.trading.ItemCost;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.item.trading.MerchantOffers;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (053) A trade that cannot be written down taken out of a villager's or a wandering trader's offers before it is: one
 * whose goods are nothing (an empty stack: a mod's trade naming an item the pack does not have, or none), or more than a
 * stack can hold, or that asks for nothing. Minecraft writes the offers out whole when the merchant is saved, and stops
 * the server on such a trade ("Saving entity NBT ... Value must be within range [1;99]: 0; Item must not be
 * minecraft:air": 053's CI, a wandering trader that a structure set down as the world was made, its trades drawn for the
 * first time as it was saved); shown to a player it would cut the connection instead. Each trade taken out is logged
 * (OROR-TRADE-DROPPED) with what it offered and asked for, so the mod that made it can be found.
 */
public final class TradeSafety {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Trades");

    private TradeSafety() {
    }

    public static void clean(AbstractVillager merchant, MerchantOffers offers) {
        if (offers == null || offers.isEmpty()) {
            return;
        }
        offers.removeIf(o -> {
            if (o != null && writable(o)) {
                return false;
            }
            try {
                LOG.warn("OROR-TRADE-DROPPED {\"merchant\":\"{}\",\"sells\":\"{}\",\"asks\":\"{}\",\"alsoAsks\":\"{}\"}",
                    BuiltInRegistries.ENTITY_TYPE.getKey(merchant.getType()), o == null ? "null" : name(o.getResult()),
                    o == null ? "" : cost(o.getItemCostA()), o == null ? "" : o.getItemCostB().map(TradeSafety::cost).orElse(""));
            } catch (RuntimeException ignored) {
                // the log is only a help
            }
            return true;
        });
    }

    private static boolean writable(MerchantOffer o) {
        ItemStack r = o.getResult();
        if (r == null || r.isEmpty() || r.getCount() > 99) {
            return false;
        }
        if (!payable(o.getItemCostA())) {
            return false;
        }
        Optional<ItemCost> b = o.getItemCostB();
        return b == null || b.isEmpty() || payable(b.get());
    }

    private static boolean payable(ItemCost c) {
        return c != null && c.count() > 0 && c.item() != null && c.item().value() != Items.AIR;
    }

    private static String name(ItemStack s) {
        return s == null ? "null" : s.getCount() + " " + BuiltInRegistries.ITEM.getKey(s.getItem());
    }

    private static String cost(ItemCost c) {
        return c == null ? "null" : c.count() + " " + (c.item() == null ? "null" : BuiltInRegistries.ITEM.getKey(c.item().value()));
    }
}
