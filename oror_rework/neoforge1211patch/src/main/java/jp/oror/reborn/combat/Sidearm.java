package jp.oror.reborn.combat;

import jp.oror.reborn.AdaptiveCombat;
import jp.oror.reborn.MobEquipmentUse;
import jp.oror.reborn.SupremeEntity;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.item.ItemStack;

/**
 * (052) A village guard (or an armed villager) with a gun used to keep it in his hand whatever the fight: the village's
 * weapon choice (AdaptiveCombat.select) takes a gun as his for good. Now an enemy within three and a half blocks makes
 * him holster it and take up a blade (the choice then gives him his sword, or an axe against a shield), and he draws
 * the gun again once the enemy is six blocks off; bows and crossbows he takes up for himself at range as before.
 */
public final class Sidearm {
    private static final String HOLSTER = "OrorHolsteredGun";

    private Sidearm() {
    }

    public static void choose(Mob m, LivingEntity t, double distance) {
        if (t == null || m instanceof SupremeEntity || m.level().isClientSide || !AdaptiveCombat.guardian(m)) {
            return;
        }
        CompoundTag d = m.getPersistentData();
        ItemStack main = m.getMainHandItem();
        boolean gun = !main.isEmpty() && MobEquipmentUse.kind(main).equals("gun");
        if (gun && distance < 3.5 && Math.abs(t.getY() - m.getY()) < 3) {
            d.put(HOLSTER, main.save(m.registryAccess()));
            m.setItemSlot(EquipmentSlot.MAINHAND, ItemStack.EMPTY);
            m.level().playSound(null, m.blockPosition(), SoundEvents.ARMOR_EQUIP_IRON.value(), SoundSource.NEUTRAL, 0.6F, 1.1F);
        } else if (!gun && distance > 6.0 && d.contains(HOLSTER)) {
            ItemStack holstered = ItemStack.parseOptional(m.registryAccess(), d.getCompound(HOLSTER));
            d.remove(HOLSTER);
            if (!holstered.isEmpty()) {
                m.setItemSlot(EquipmentSlot.MAINHAND, holstered);
                m.level().playSound(null, m.blockPosition(), SoundEvents.ARMOR_EQUIP_IRON.value(), SoundSource.NEUTRAL, 0.6F, 0.9F);
            }
        }
    }
}
