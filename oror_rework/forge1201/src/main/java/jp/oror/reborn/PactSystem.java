package jp.oror.reborn;

import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraftforge.event.entity.player.PlayerEvent.Clone;
import net.minecraftforge.event.TickEvent.PlayerTickEvent;

public final class PactSystem {
    public static void interact(SupremeEntity b, Player p) {
        CompoundTag n = p.getPersistentData();
        int debt = n.getInt("ororPactDebt");
        long now = p.level().getGameTime();
        if (p.isShiftKeyDown()
            && p.getMainHandItem().is(Items.EMERALD)
            && !p.getCooldowns().isOnCooldown(Items.EMERALD)
            && debt < (b.lore() ? Integer.MAX_VALUE : 16)) {
            if (!p.isCreative()) {
                p.getMainHandItem().shrink(1);
            }

            n.putInt("ororPactDebt", ++debt);
            p.heal(p.getMaxHealth());
            p.getFoodData().setFoodLevel(20);
            p.getInventory().add(new ItemStack(Items.EMERALD, 8));
            p.getCooldowns().addCooldown(Items.EMERALD, 100);
            p.displayClientMessage(Component.literal("契約成立：全回復・満腹・エメラルド8個。未来の負債=" + debt + "。3件から弱体化、4件から鈍足。死後も負債を継承します。"), false);
        } else {
            if (now >= n.getLong("ororPactFreeAidUntil")) {
                p.heal(4.0F);
                n.putLong("ororPactFreeAidUntil", now + 1200L);
            }

            p.displayClientMessage(
                Component.literal("甘契の未怪：今は無償で助けましょう。契約はエメラルド1個を持ち、しゃがんで右クリック。全回復・満腹・8個の富と引換えに負債1件。3件から弱体化、4件から鈍足、死後も継承。現在 " + debt + "件。"), false
            );
        }
    }

    public static void tick(PlayerTickEvent e) {
        if (e.phase != net.minecraftforge.event.TickEvent.Phase.END) {
            return;
        }
        Player p = e.player;
        if (!p.level().isClientSide && p.tickCount % 40 == 0) {
            int d = p.getPersistentData().getInt("ororPactDebt");
            if (d >= 3) {
                p.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 100, Math.min(4, d / 3 - 1)));
            }

            if (d >= 4) {
                p.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 100, Math.min(3, d / 4 - 1)));
            }
        }
    }

    public static void clone(Clone e) {
        CompoundTag old = e.getOriginal().getPersistentData();
        CompoundTag n = e.getEntity().getPersistentData();
        n.putInt("ororPactDebt", old.getInt("ororPactDebt"));
        n.putLong("ororPactNextVisit", old.getLong("ororPactNextVisit"));
    }
}
