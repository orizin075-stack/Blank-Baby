package jp.oror.reborn;

import jp.oror.reborn.royal.RoyalMob;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.FlyingMob;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.animal.AbstractGolem;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.animal.WaterAnimal;
import net.minecraft.world.entity.monster.AbstractIllager;
import net.minecraft.world.entity.monster.AbstractSkeleton;
import net.minecraft.world.entity.monster.Vex;
import net.minecraft.world.entity.monster.Witch;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.entity.monster.piglin.AbstractPiglin;
import net.minecraft.world.entity.npc.AbstractVillager;
import net.minecraft.world.phys.Vec3;

/**
 * Smart-mob combat for creatures without hands. AdaptiveCombat used to hand any mob it drove a bow, a crossbow or a
 * sword (a cow or a spider "shooting" arrows out of nowhere); a mob that cannot hold a weapon now fights with what it
 * has, and gets one move of its own: from a few blocks away it springs at its enemy.
 */
public final class HandlessCombat {
    private HandlessCombat() {
    }

    /** True for mobs that hold and use weapons: people, illagers, the undead soldiers, piglins, witches, the royals. */
    public static boolean handed(Mob m) {
        if (m instanceof SupremeEntity || m instanceof RoyalMob || m instanceof AbstractVillager || m instanceof AbstractIllager
            || m instanceof AbstractSkeleton || m instanceof Zombie || m instanceof AbstractPiglin || m instanceof Witch || m instanceof Vex) {
            return true;
        }
        if (m instanceof Animal || m instanceof WaterAnimal || m instanceof AbstractGolem || m instanceof FlyingMob || m instanceof FamiliarEntity) {
            return false;
        }
        String ns = BuiltInRegistries.ENTITY_TYPE.getKey(m.getType()).getNamespace();
        if (ns.equals("guardvillagers")) {
            return true;
        }
        if (ns.equals("minecraft")) {
            return false;
        }
        // another mod's monster: a person-sized one has hands (most of them are drawn as people), a beast does not
        return m.getType().getCategory() == MobCategory.MONSTER && m.getBbHeight() >= 1.4F && m.getBbWidth() <= 0.9F;
    }

    /**
     * The handless mob's choice: no weapon; from three to ten blocks off, on the ground, it may spring at its enemy
     * (every two to three seconds), landing beside it ready to bite or butt.
     */
    public static String select(Mob m, LivingEntity t, double distance) {
        net.minecraft.nbt.CompoundTag n = MobMind.data(m);
        // what the old code handed it (a bow, a sword, armour and a shield) is taken back
        for (net.minecraft.world.entity.EquipmentSlot slot : net.minecraft.world.entity.EquipmentSlot.values()) {
            String key = "Managed_" + slot.getName();
            if (n.contains(key) || slot == net.minecraft.world.entity.EquipmentSlot.MAINHAND && n.contains("Selected")) {
                m.setItemSlot(slot, net.minecraft.world.item.ItemStack.EMPTY);
                n.remove(key);
            }
        }
        n.remove("Selected");
        long now = m.level().getGameTime();
        if (distance > 3.0 && distance < 10.0 && m.onGround() && n.getLong("NextPounce") <= now && m.getSensing().hasLineOfSight(t)) {
            Vec3 d = t.position().subtract(m.position());
            Vec3 flat = new Vec3(d.x, 0, d.z).normalize();
            double reach = Math.min(1.3, 0.35 + distance * 0.11);
            m.setDeltaMovement(flat.x * reach, 0.42 + Math.max(0, d.y) * 0.08, flat.z * reach);
            m.hasImpulse = true;
            n.putLong("NextPounce", now + 40 + m.getRandom().nextInt(20));
            n.putLong("NextAttack", Math.min(n.getLong("NextAttack"), now + 6));
            m.level().playSound(null, m.getX(), m.getY(), m.getZ(), SoundEvents.RAVAGER_STEP, SoundSource.HOSTILE, 0.6F, 1.4F);
            MobMind.practice(m, "tactics", 1);
        }
        return "unarmed";
    }
}
