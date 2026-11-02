package jp.oror.reborn.royal;

import java.util.Map;
import java.util.WeakHashMap;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.entity.projectile.Arrow;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;

/**
 * (052) A kingdom guard's three weapons, and which one is in his hand. He used to carry nothing but his electric gun
 * (RoyalGuns), even with an enemy at his throat or out of its reach. Now he carries a sword and shield, a bow and a
 * pistol (Superb Warfare's Glock 17; the electric gun without it), and changes to the one the moment needs, taking half
 * a second over it:
 * <ul>
 * <li>an enemy within four blocks (and not far above or below): the sword and shield, and the royals' guard;</li>
 * <li>an enemy in sight within fifteen blocks: the pistol, kept at seven to fourteen blocks;</li>
 * <li>farther, out of sight, or flying high above: the bow, drawn for a second and loosed with the drop allowed for,
 * kept at eight to twenty-eight blocks.</li>
 * </ul>
 * With no enemy, the sword and shield. A guard under the war's charge order keeps closing in whatever he holds.
 */
public final class RoyalArmory {
    enum Arm {
        MELEE, GUN, BOW
    }

    static final class State {
        Arm arm;
        int swap, draw, bowDelay;
    }

    private static final Map<RoyalMob, State> STATES = new WeakHashMap<>();
    private static Item pistol;
    private static boolean looked;

    private RoyalArmory() {
    }

    /** The pistol the guards carry (null without Superb Warfare). */
    static Item pistol() {
        if (!looked) {
            looked = true;
            for (String id : new String[]{"superbwarfare:glock_17", "superbwarfare:taser"}) {
                Item item = BuiltInRegistries.ITEM.get(ResourceLocation.parse(id));
                if (item instanceof com.atsuishio.superbwarfare.item.gun.GunItem) {
                    pistol = item;
                    break;
                }
            }
        }
        return pistol;
    }

    /** The arm a guard holds now (for the checks): melee, gun or bow; "" for a royal who is not a guard. */
    public static String arm(RoyalMob mob) {
        State s = STATES.get(mob);
        return s == null || s.arm == null ? "" : s.arm.name().toLowerCase(java.util.Locale.ROOT);
    }

    /**
     * A guard's tick, before his guns'. Returns null when this royal is not one of the guards (his guns go on as ever),
     * "" when he fights with the sword or the bow this tick (his guns stand aside), and the pistol's id when he fights
     * with it (his guns shoot it).
     */
    public static String tick(RoyalMob mob, RoyalGuns guns) {
        if (mob.role() != RoyalRole.GUARD || mob.level().isClientSide) {
            return null;
        }
        State s = STATES.computeIfAbsent(mob, k -> new State());
        LivingEntity t = mob.getTarget();
        boolean fighting = t != null && t.isAlive() && mob.canAttack(t) && !(t instanceof Player p && (p.isCreative() || p.isSpectator()));
        Item gun = pistol();
        Arm want = Arm.MELEE;
        double d = 0;
        if (fighting) {
            d = mob.distanceTo(t);
            double dy = t.getY() - mob.getY();
            boolean sight = mob.getSensing().hasLineOfSight(t);
            boolean high = dy > 4 && !t.onGround();
            boolean close = d < (s.arm == Arm.MELEE ? 5.5 : 4.0) && Math.abs(dy) < 3;
            if (close) {
                want = Arm.MELEE;
            } else if (gun != null && sight && d <= (s.arm == Arm.GUN ? 18 : 15) && !(high && d > 10)) {
                want = Arm.GUN;
            } else {
                want = Arm.BOW;
            }
        }
        if (want != s.arm && s.swap <= 0) {
            equip(mob, guns, want, gun);
            if (s.arm != null) {
                mob.level().playSound(null, mob.blockPosition(), SoundEvents.ARMOR_EQUIP_IRON.value(), SoundSource.HOSTILE, 0.6F, 1.1F);
            }
            s.arm = want;
            s.swap = 10;
            s.draw = 0;
        }
        if (s.swap > 0) {
            s.swap--;
        }
        mob.setAggressive(fighting);
        if (fighting && mob.tickCount % 5 == 0 && s.arm != Arm.MELEE && !RoyalWarOrders.charging(mob)) {
            keep(mob, t, d, s.arm == Arm.GUN ? 7 : 8, s.arm == Arm.GUN ? 14 : 28);
        }
        if (s.arm == Arm.GUN) {
            // the half second of drawing the pistol, then his guns shoot it
            return s.swap > 4 || gun == null ? "" : BuiltInRegistries.ITEM.getKey(gun).toString();
        }
        if (s.arm == Arm.BOW && fighting && s.swap <= 0) {
            bow(mob, t, s);
        } else if (mob.isUsingItem() && s.arm != Arm.BOW) {
            mob.stopUsingItem();
        }
        return "";
    }

    private static void equip(RoyalMob mob, RoyalGuns guns, Arm arm, Item gun) {
        if (mob.isUsingItem()) {
            mob.stopUsingItem();
        }
        switch (arm) {
            case MELEE -> {
                mob.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(Items.DIAMOND_SWORD));
                mob.setItemSlot(EquipmentSlot.OFFHAND, new ItemStack(Items.SHIELD));
            }
            case GUN -> {
                if (gun != null) {
                    mob.setItemSlot(EquipmentSlot.MAINHAND, guns.make(gun));
                }
                mob.setItemSlot(EquipmentSlot.OFFHAND, ItemStack.EMPTY);
            }
            case BOW -> {
                mob.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(Items.BOW));
                mob.setItemSlot(EquipmentSlot.OFFHAND, ItemStack.EMPTY);
            }
        }
    }

    /** Keeps the guard between near and far of his enemy: backing off, standing to shoot, or closing in. */
    private static void keep(RoyalMob mob, LivingEntity t, double d, double near, double far) {
        if (d < near) {
            Vec3 away = mob.position().subtract(t.position()).multiply(1, 0, 1);
            away = away.lengthSqr() < 1.0E-4 ? mob.getLookAngle().scale(-1) : away.normalize();
            mob.getNavigation().moveTo(mob.getX() + away.x * 5, mob.getY(), mob.getZ() + away.z * 5, 1.0);
        } else if (d <= far) {
            mob.getNavigation().stop();
        } else {
            mob.getNavigation().moveTo(t, 1.0);
        }
    }

    /** Draws for a second and looses, allowing for the arrow's drop; needs a clear line to the enemy. */
    private static void bow(RoyalMob mob, LivingEntity t, State s) {
        mob.getLookControl().setLookAt(t, 30F, 30F);
        if (s.bowDelay > 0) {
            s.bowDelay--;
            return;
        }
        if (!mob.getSensing().hasLineOfSight(t)) {
            if (mob.isUsingItem()) {
                mob.stopUsingItem();
            }
            s.draw = 0;
            return;
        }
        if (!mob.isUsingItem()) {
            mob.startUsingItem(InteractionHand.MAIN_HAND);
            s.draw = 0;
            return;
        }
        if (++s.draw < 20) {
            return;
        }
        ItemStack bow = mob.getMainHandItem();
        mob.stopUsingItem();
        s.draw = 0;
        s.bowDelay = 14;
        Arrow arrow = new Arrow(mob.level(), mob, new ItemStack(Items.ARROW), bow.isEmpty() ? null : bow);
        arrow.pickup = AbstractArrow.Pickup.DISALLOWED;
        arrow.setBaseDamage(5.0);
        double dx = t.getX() - mob.getX(), dz = t.getZ() - mob.getZ();
        double dy = t.getY(0.3333) - arrow.getY();
        double h = Math.sqrt(dx * dx + dz * dz);
        arrow.shoot(dx, dy + h * 0.14, dz, 2.2F, 4F);
        mob.level().addFreshEntity(arrow);
        mob.getPersistentData().putInt("OrorArrows", mob.getPersistentData().getInt("OrorArrows") + 1);
        mob.level().playSound(null, mob.blockPosition(), SoundEvents.ARROW_SHOOT, SoundSource.HOSTILE, 1.0F, 1.0F / (mob.getRandom().nextFloat() * 0.4F + 0.8F));
        mob.swing(InteractionHand.MAIN_HAND);
    }
}
