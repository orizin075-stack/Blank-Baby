package jp.oror.reborn.combat;

import jp.oror.reborn.AdaptiveCombat;
import jp.oror.reborn.MobEquipmentUse;
import jp.oror.reborn.MobLevels;
import jp.oror.reborn.SupremeEntity;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.EntityTickEvent;

/**
 * (052) A village guard (Guard Villagers' guard, or an armed villager) with a gun used to keep it in his hand whatever
 * the fight. Now an enemy within three and a half blocks makes him holster it and take up a blade (his sword, an axe
 * against a shield), and he draws the gun again once the enemy is six blocks off or gone; bows and crossbows he takes up
 * for himself at range as before. The gun is kept on him while it is holstered (a villager's own gun goes back to his
 * pack afterwards, as the village's gear does).
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class Sidearm {
    private static final String HOLSTER = "OrorHolsteredGun", ISSUED = "OrorIssuedBlade";

    private Sidearm() {
    }

    @SubscribeEvent
    public static void tick(EntityTickEvent.Post e) {
        if (!(e.getEntity() instanceof Mob m) || m.level().isClientSide || (m.tickCount + m.getId()) % 5 != 0 || m instanceof SupremeEntity) {
            return;
        }
        CompoundTag d = m.getPersistentData();
        boolean holstered = d.contains(HOLSTER);
        ItemStack main = m.getMainHandItem();
        boolean gun = !main.isEmpty() && MobEquipmentUse.kind(main).equals("gun");
        if (!gun && !holstered || !AdaptiveCombat.guardian(m)) {
            return;
        }
        LivingEntity t = m.getTarget();
        boolean fighting = t != null && t.isAlive();
        double dist = fighting ? m.distanceTo(t) : 99;
        if (gun && !holstered && dist < 3.5 && Math.abs(t.getY() - m.getY()) < 3) {
            d.put(HOLSTER, main.save(m.registryAccess()));
            ItemStack blade = MobLevels.weapon(m, t.isBlocking() ? "axe" : "sword");
            if (blade.isEmpty()) {
                blade = new ItemStack(Items.IRON_SWORD);
            }
            d.putString(ISSUED, net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(blade.getItem()).toString());
            m.setItemSlot(EquipmentSlot.MAINHAND, blade);
            m.level().playSound(null, m.blockPosition(), SoundEvents.ARMOR_EQUIP_IRON.value(), SoundSource.NEUTRAL, 0.6F, 1.1F);
        } else if (holstered && !gun && dist > 6.0) {
            ItemStack holster = ItemStack.parseOptional(m.registryAccess(), d.getCompound(HOLSTER));
            String issued = d.getString(ISSUED);
            d.remove(HOLSTER);
            d.remove(ISSUED);
            if (holster.isEmpty()) {
                return;
            }
            boolean ours = !main.isEmpty() && net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(main.getItem()).toString().equals(issued);
            if (!main.isEmpty() && !ours && m instanceof Villager v && v.getInventory().canAddItem(main)) {
                v.getInventory().addItem(main.copy());
            }
            m.setItemSlot(EquipmentSlot.MAINHAND, holster);
            m.level().playSound(null, m.blockPosition(), SoundEvents.ARMOR_EQUIP_IRON.value(), SoundSource.NEUTRAL, 0.6F, 0.9F);
        }
    }
}
