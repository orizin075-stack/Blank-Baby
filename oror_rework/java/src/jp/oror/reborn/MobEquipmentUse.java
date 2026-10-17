package jp.oror.reborn;

import java.lang.ref.WeakReference;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.WeakHashMap;
import java.util.function.Supplier;
import jp.oror.reborn.mixin.MobGoalSelectorAccess;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import net.neoforged.fml.ModList;

public final class MobEquipmentUse {
    private static boolean magicBroken;
    private static final Set<String> BROKEN = new HashSet<>();
    private static final Map<Mob, WeakReference<Goal>> JEG_GOALS = new WeakHashMap<>();

    public static String kind(ItemStack item) {
        if (!item.isEmpty() && (Boolean)RebornConfig.MOD_EQUIPMENT.get()) {
            String ns = BuiltInRegistries.ITEM.getKey(item.getItem()).getNamespace();
            if (!BROKEN.contains(ns) && Set.of("tacz", "irons_spellbooks", "jeg", "superbwarfare").contains(ns)) {
                try {
                    if (ns.equals("jeg") && ModList.get().isLoaded("jeg") && Class.forName("ttv.migami.jeg.item.GunItem").isInstance(item.getItem())) {
                        return "gun";
                    } else if (ns.equals("superbwarfare")
                        && ModList.get().isLoaded("superbwarfare")
                        && Class.forName("com.atsuishio.superbwarfare.item.gun.GunItem").isInstance(item.getItem())) {
                        return "gun";
                    } else if (ModList.get().isLoaded("tacz")
                        && Class.forName("com.tacz.guns.api.item.IGun").getMethod("getIGunOrNull", ItemStack.class).invoke(null, item) != null) {
                        return "gun";
                    } else {
                        if (ModList.get().isLoaded("irons_spellbooks") && !magicBroken) {
                            Class<?> api = Class.forName("io.redspace.ironsspellbooks.api.spells.ISpellContainer");
                            if ((Boolean)api.getMethod("isSpellContainer", ItemStack.class).invoke(null, item)) {
                                Object spells = api.getMethod("get", ItemStack.class).invoke(null, item);
                                if (!(Boolean)api.getMethod("isEmpty").invoke(spells)) {
                                    return "magic";
                                }
                            }
                        }

                        return "";
                    }
                } catch (LinkageError | ReflectiveOperationException var4) {
                    return "";
                }
            } else {
                return "";
            }
        } else {
            return "";
        }
    }

    public static boolean supported(ItemStack item) {
        return !kind(item).isEmpty();
    }

    public static boolean use(Mob mob, LivingEntity target, ServerLevel sl, String kind) {
        if ((Boolean)RebornConfig.MOD_EQUIPMENT.get()
            && AdaptiveCombat.enemy(mob, target)
            && mob.getPersistentData().getLong("OrorSilencedUntil") <= sl.getGameTime()) {
            Vec3 d = target.getEyePosition().add(target.getDeltaMovement().scale(MobLevels.level(mob) >= 4 ? 4.0 : 1.0)).subtract(mob.getEyePosition());
            mob.setYRot((float)Math.toDegrees(Math.atan2(d.z, d.x)) - 90.0F);
            mob.setYHeadRot(mob.getYRot());
            mob.setXRot((float)(-Math.toDegrees(Math.atan2(d.y, d.horizontalDistance()))));
            mob.setSprinting(false);

            try {
                String provider = BuiltInRegistries.ITEM.getKey(mob.getMainHandItem().getItem()).getNamespace();
                return kind.equals("gun")
                    ? (provider.equals("superbwarfare") ? warfare(mob, target) : (provider.equals("jeg") ? nativeGoal(mob) : gun(mob)))
                    : kind.equals("magic") && magic(mob, sl);
            } catch (LinkageError | ReflectiveOperationException var6) {
                MobMind.data(mob).putString("EquipmentError", var6.getClass().getSimpleName());
                if (kind.equals("gun")) {
                    BROKEN.add(BuiltInRegistries.ITEM.getKey(mob.getMainHandItem().getItem()).getNamespace());
                } else {
                    magicBroken = true;
                }

                System.out.println("[OROR_EQUIPMENT] disabled " + kind + " after provider failure " + var6.getClass().getSimpleName());
                return false;
            }
        } else {
            return false;
        }
    }

    public static boolean nativeGoal(Mob mob) {
        String provider = BuiltInRegistries.ITEM.getKey(mob.getMainHandItem().getItem()).getNamespace();
        if (provider.equals("jeg") && supported(mob.getMainHandItem()) && mob instanceof PathfinderMob path && AdaptiveCombat.enemy(mob, mob.getTarget())) {
            WeakReference<Goal> old = JEG_GOALS.get(mob);
            if (old != null && old.get() != null) {
                return true;
            }

            try {
                Class<?> type = Class.forName("ttv.migami.jeg.entity.ai.AIType");
                Object tactic = type.getField("TACTICAL").get(null);
                Goal goal = (Goal)Class.forName("ttv.migami.jeg.entity.ai.GunAttackGoal")
                    .getConstructor(PathfinderMob.class, double.class, float.class, type, int.class)
                    .newInstance(path, 1.25, 32.0F, tactic, MobLevels.level(mob));
                ((MobGoalSelectorAccess)mob).oror$getGoals().addGoal(1, goal);
                JEG_GOALS.put(mob, new WeakReference<>(goal));
                MobMind.data(mob).putString("NativeGunGoal", "jeg:TACTICAL");
                return true;
            } catch (LinkageError | ReflectiveOperationException var7) {
                BROKEN.add(provider);
                MobMind.data(mob).putString("EquipmentError", var7.getClass().getSimpleName());
                return false;
            }
        }

        return false;
    }

    public static void clock(Mob mob) {
        if ((Boolean)RebornConfig.MOD_EQUIPMENT.get()
            && BuiltInRegistries.ITEM.getKey(mob.getMainHandItem().getItem()).getNamespace().equals("superbwarfare")
            && !BROKEN.contains("superbwarfare")) {
            try {
                Class<?> api = Class.forName("com.atsuishio.superbwarfare.data.gun.GunData");
                Object data = api.getMethod("from", ItemStack.class).invoke(null, mob.getMainHandItem());
                api.getMethod("tick", Entity.class, boolean.class).invoke(data, mob, true);
            } catch (LinkageError | ReflectiveOperationException var3) {
                BROKEN.add("superbwarfare");
                MobMind.data(mob).putString("EquipmentError", var3.getClass().getSimpleName());
            }
        }
    }

    private static boolean warfare(Mob mob, LivingEntity target) throws ReflectiveOperationException {
        Class<?> api = Class.forName("com.atsuishio.superbwarfare.data.gun.GunData");
        Object data = api.getMethod("from", ItemStack.class).invoke(null, mob.getMainHandItem());
        // v0.17.15: reload and work the bolt as Superb Warfare's own GunShootGoal does (neither ever started before, so a
        // mob's gun fell silent after its first magazine); the reload itself runs on in GunData.tick (clock)
        if ((Boolean)api.getMethod("shouldStartReloading", Entity.class).invoke(data, mob)) {
            api.getMethod("startReload").invoke(data);
        }
        if ((Boolean)api.getMethod("shouldStartBolt").invoke(data)) {
            api.getMethod("startBolt").invoke(data);
        }
        if (!(Boolean)api.getMethod("canShoot", Entity.class).invoke(data, mob)) {
            return false;
        } else {
            api.getMethod("shoot", Entity.class, double.class, boolean.class, UUID.class)
                .invoke(data, mob, (double)MobLevels.accuracy(mob, "gun"), true, target.getUUID());
            CompoundTag n = MobMind.data(mob);
            n.putInt("GunShots", n.getInt("GunShots") + 1);
            MobMind.practice(mob, "gun", 1);
            return true;
        }
    }

    private static boolean gun(Mob m) throws ReflectiveOperationException {
        Class<?> api = Class.forName("com.tacz.guns.api.entity.IGunOperator");
        Object operator = api.getMethod("fromLivingEntity", LivingEntity.class).invoke(null, m);
        CompoundTag n = MobMind.data(m);
        Class<?> gunApi = Class.forName("com.tacz.guns.api.item.IGun");
        Object gun = gunApi.getMethod("getIGunOrNull", ItemStack.class).invoke(null, m.getMainHandItem());
        String item = gunApi.getMethod("getGunId", ItemStack.class).invoke(gun, m.getMainHandItem()).toString();
        if (!item.equals(n.getString("GunDrawn"))) {
            api.getMethod("initialData").invoke(operator);
            api.getMethod("draw", Supplier.class).invoke(operator, (Supplier<ItemStack>)m::getMainHandItem);
            n.putString("GunDrawn", item);
            n.putString("GunResult", "DRAW");
            return false;
        } else {
            int before = (Integer)gunApi.getMethod("getCurrentAmmoCount", ItemStack.class).invoke(gun, m.getMainHandItem());
            boolean chamber = (Boolean)gunApi.getMethod("hasBulletInBarrel", ItemStack.class).invoke(gun, m.getMainHandItem());
            if (before <= 0 && !chamber) {
                n.putString("GunResult", "NO_AMMO");
                return false;
            } else {
                api.getMethod("aim", boolean.class).invoke(operator, true);
                Object result = api.getMethod("shoot", Supplier.class, Supplier.class).invoke(operator, (Supplier<Float>)m::getXRot, (Supplier<Float>)m::getYRot);
                String status = result.toString();
                n.putString("GunResult", status);
                if (status.equals("NEED_BOLT")) {
                    api.getMethod("bolt").invoke(operator);
                }

                if (status.equals("NO_AMMO")) {
                    api.getMethod("reload").invoke(operator);
                }

                if (!status.equals("SUCCESS")) {
                    return false;
                } else {
                    int after = (Integer)gunApi.getMethod("getCurrentAmmoCount", ItemStack.class).invoke(gun, m.getMainHandItem());
                    if (before > 0 && after >= before) {
                        gunApi.getMethod("setCurrentAmmoCount", ItemStack.class, int.class).invoke(gun, m.getMainHandItem(), before - 1);
                    } else if (before == 0 && chamber) {
                        gunApi.getMethod("setBulletInBarrel", ItemStack.class, boolean.class).invoke(gun, m.getMainHandItem(), false);
                    }

                    n.putInt("GunShots", n.getInt("GunShots") + 1);
                    MobMind.practice(m, "gun", 1);
                    return true;
                }
            }
        }
    }

    private static boolean magic(Mob m, ServerLevel sl) throws ReflectiveOperationException {
        Class<?> containers = Class.forName("io.redspace.ironsspellbooks.api.spells.ISpellContainer");
        Object container = containers.getMethod("get", ItemStack.class).invoke(null, m.getMainHandItem());
        Class<?> dataClass = Class.forName("io.redspace.ironsspellbooks.api.spells.SpellData");
        Object selected = containers.getMethod("getSpellAtIndex", int.class).invoke(container, 0);
        Object spell = dataClass.getMethod("getSpell").invoke(selected);
        int level = (Integer)dataClass.getMethod("getLevel").invoke(selected);
        Class<?> spells = Class.forName("io.redspace.ironsspellbooks.api.spells.AbstractSpell");
        Class<?> manaClass = Class.forName("io.redspace.ironsspellbooks.api.magic.MagicData");
        Class<?> sourceClass = Class.forName("io.redspace.ironsspellbooks.api.spells.CastSource");
        Object source = sourceClass.getField("MOB").get(null);
        Object mana = manaClass.getMethod("getPlayerMagicData", LivingEntity.class).invoke(null, m);
        CompoundTag n = MobMind.data(m);
        int cost = (Integer)spells.getMethod("getManaCost", int.class).invoke(spell, level);
        float energy = n.contains("SpellEnergy") ? n.getFloat("SpellEnergy") : 100.0F;
        long now = sl.getGameTime();
        energy = Math.min(200.0F, energy + (float)Math.max(0L, now - n.getLong("SpellClock")) * 0.25F);
        n.putLong("SpellClock", now);
        n.putFloat("SpellEnergy", energy);
        if (energy < (float)cost) {
            return false;
        } else if (!(Boolean)spells.getMethod("checkPreCastConditions", Level.class, int.class, LivingEntity.class, manaClass)
            .invoke(spell, sl, level, m, mana)) {
            return false;
        } else {
            spells.getMethod("onServerPreCast", Level.class, int.class, LivingEntity.class, manaClass).invoke(spell, sl, level, m, mana);
            spells.getMethod("onCast", Level.class, int.class, LivingEntity.class, sourceClass, manaClass).invoke(spell, sl, level, m, source, mana);
            spells.getMethod("onServerCastComplete", Level.class, int.class, LivingEntity.class, manaClass, boolean.class)
                .invoke(spell, sl, level, m, mana, false);
            n.putFloat("SpellEnergy", energy - (float)cost);
            n.putString("LastSpell", (String)spells.getMethod("getSpellId").invoke(spell));
            n.putInt("SpellCasts", n.getInt("SpellCasts") + 1);
            MobMind.practice(m, "magic", 1);
            return true;
        }
    }

    private MobEquipmentUse() {
    }
}
