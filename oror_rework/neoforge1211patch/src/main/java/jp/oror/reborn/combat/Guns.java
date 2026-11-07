package jp.oror.reborn.combat;

import java.util.Locale;
import java.util.Set;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SwordItem;

/**
 * (053) Whether a stack is a firearm of the pack's gun mods (TACZ, JEG, Superb Warfare, the pillagers' gun mods, TACZ
 * Bandits), or of any mod whose item class is a gun: as OROR's adaptive combat tells them (AdaptiveCombat.gun), without
 * its bows and crossbows.
 */
public final class Guns {
    public static final Set<String> MODS = Set.of("tacz", "jeg", "superbwarfare", "pillagers_gun", "pillagerguns", "tacz_bandits");

    private Guns() {
    }

    public static boolean held(ItemStack s) {
        if (s == null || s.isEmpty()) {
            return false;
        }
        String ns = BuiltInRegistries.ITEM.getKey(s.getItem()).getNamespace();
        if (ns.equals("minecraft") || ns.equals("oror_supreme_bosses")) {
            return false;
        }
        if (MODS.contains(ns) && !(s.getItem() instanceof SwordItem)) {
            return true;
        }
        for (Class<?> c = s.getItem().getClass(); c != null && c != Item.class; c = c.getSuperclass()) {
            if (c.getSimpleName().toLowerCase(Locale.ROOT).contains("gun")) {
                return true;
            }
        }
        return false;
    }
}
