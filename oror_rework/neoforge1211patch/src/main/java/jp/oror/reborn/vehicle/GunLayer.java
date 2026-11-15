package jp.oror.reborn.vehicle;

import java.lang.reflect.Method;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.phys.Vec3;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (059g) The gunner who pulls the trigger. The capital's guns but the HPJ-11 (the Mle 1934 and BL-132 field guns, the Mk 42
 * and the TOW launcher: Superb Warfare's ArtilleryEntity and TowEntity) are no self-aiming turrets: Superb Warfare turns
 * their barrel to the target the crew is given (RoyalPilots, Sbw.aim), but fires them only when the one aboard presses
 * fire, which a soldier never did (CI 43 and 44: brought out, manned, turned, not one round in 45 seconds). Now, the
 * target held for a moment and a half (the barrel come round to it) and the line to it clear, whenever Superb Warfare
 * says the gunner's seat can fire (its own reload and ammunition, canShoot), the gun is fired through its own
 * vehicleShoot for him, at the target.
 */
final class GunLayer {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Vehicles");
    private static final Map<Class<?>, Method> SHOOT = new ConcurrentHashMap<>();
    private static final java.util.Set<Class<?>> NONE = ConcurrentHashMap.newKeySet();
    static int fired, failures;

    private GunLayer() {
    }

    static void lay(Entity v, CompoundTag p, Mob gunner, LivingEntity target) {
        long now = v.level().getGameTime();
        String on = target.getStringUUID();
        if (!on.equals(p.getString("LayOn"))) {
            p.putString("LayOn", on);
            p.putLong("LayFrom", now);
            return;
        }
        if (now - p.getLong("LayFrom") < 30) {
            p.putString("LayWhy", "laying");
            return;
        }
        if (now < p.getLong("LayNext")) {
            return;                                   // (CI 48: three rounds a second) the gun's own rate of fire
        }
        if (!RoyalPilots.lineOfFire(v, target)) {
            p.putString("LayWhy", "noLine");
            return;
        }
        Object can = Sbw.call(v, "canShoot", gunner);
        if (!Boolean.TRUE.equals(can) && load(v, p, gunner)) {
            // (CI 47: every one of the four had no round in its breech, its rounds in the hold) the gunner loads one
            can = Sbw.call(v, "canShoot", gunner);
        }
        if (!Boolean.TRUE.equals(can)) {
            // (CI 46: not one round) what Superb Warfare says of the gunner's seat, kept for the check
            p.putString("LayWhy", "cannot:" + can + " " + state(v, gunner));
            return;
        }
        Method m = shoot(v);
        if (m == null) {
            p.putString("LayWhy", "noMethod");
            return;
        }
        p.putString("LayWhy", "fires");
        try {
            m.invoke(v, gunner, target.getUUID(), target.getBoundingBox().getCenter());
            fired++;
            p.putInt("Fired", p.getInt("Fired") + 1);
            p.putLong("LayNext", now + interval(v, gunner));
        } catch (ReflectiveOperationException | RuntimeException ex) {
            if (failures++ < 5) {
                LOG.warn("GUN-LAYER {} could not fire: {}", Supply.kind(v), ex.toString());
            }
        }
    }

    /**
     * The gunner loads a round where his gun has none in it: by Superb Warfare's own reloading from the vehicle's ammunition
     * (GunData.reloadAmmo, from its ammunition supplier), or else by hand, one of the gun's own rounds taken out of the
     * vehicle's hold. True if the gun has a round in it after. (The TOW has no hold: its missile comes from the kingdom's
     * depot beside it, Supply.loadLauncher.)
     */
    /** Ticks between two rounds: the seat's weapon's own rate (Superb Warfare's vehicleWeaponRpm), three seconds if unknown. */
    private static long interval(Entity v, Mob gunner) {
        try {
            Object rpm = v.getClass().getMethod("vehicleWeaponRpm", LivingEntity.class).invoke(v, gunner);
            if (rpm instanceof Number n && n.intValue() > 0) {
                return Math.max(5, (long) Math.ceil(1200.0 / n.intValue()));
            }
        } catch (ReflectiveOperationException | RuntimeException ex) {
            // unknown: as below
        }
        return 60;
    }

    /** Missiles a TOW's crew carries beside the depot's (a post with no depot at hand still fires a few). */
    static final int TOW_SPARE = 6;

    static boolean load(Entity v, CompoundTag p, Mob gunner) {
        int seat = Sbw.call(v, "getSeatIndex", gunner) instanceof Number n ? n.intValue() : 0;
        Object supplier = Sbw.call(v, "getAmmoSupplier");
        boolean[] loaded = {false};
        try {
            Method modify = v.getClass().getMethod("modifyGunData", int.class, java.util.function.Consumer.class);
            java.util.function.Consumer<Object> loadIt = data -> {
                try {
                    Object ammo = data.getClass().getField("ammo").get(data);
                    Method get = ammo.getClass().getMethod("get");
                    int in = get.invoke(ammo) instanceof Number h ? h.intValue() : 0;
                    if (in <= 0 && supplier instanceof Entity from) {
                        data.getClass().getMethod("reloadAmmo", Entity.class).invoke(data, from);
                        in = get.invoke(ammo) instanceof Number after ? after.intValue() : 0;
                    }
                    if (in <= 0 && takeRound(v)) {
                        ammo.getClass().getMethod("set", int.class).invoke(ammo, 1);
                        in = 1;
                    }
                    if (in <= 0 && "tow".equals(Supply.kind(v)) && p.getInt("TowSpent") < TOW_SPARE) {
                        // the TOW has no hold: one of the missiles its crew carries (the depot beside it refills the tube
                        // too, Supply.loadLauncher)
                        ammo.getClass().getMethod("set", int.class).invoke(ammo, 1);
                        p.putInt("TowSpent", p.getInt("TowSpent") + 1);
                        in = 1;
                    }
                    loaded[0] = in > 0;
                } catch (ReflectiveOperationException | RuntimeException ex) {
                    if (failures++ < 5) {
                        LOG.warn("GUN-LAYER {} could not load: {}", Supply.kind(v), ex.toString());
                    }
                }
            };
            modify.invoke(v, seat, loadIt);
        } catch (ReflectiveOperationException | RuntimeException ex) {
            if (failures++ < 5) {
                LOG.warn("GUN-LAYER {} has no modifyGunData: {}", Supply.kind(v), ex.toString());
            }
        }
        if (loaded[0]) {
            loads++;
            if ("tow".equals(Supply.kind(v))) {
                Sbw.call(v, "setLoaded", true);
            }
        }
        return loaded[0];
    }

    static int loads;

    /** One of the gun's own rounds (its kind's load, Supply) out of the vehicle's hold. */
    private static boolean takeRound(Entity v) {
        Supply.Hold hold = Supply.hold(v);
        if (hold == null) {
            return false;
        }
        java.util.Set<String> rounds = new java.util.HashSet<>();
        for (String[] l : Supply.load(v)) {
            rounds.add(l[0]);
        }
        for (int i = 0; i < hold.size(); i++) {
            net.minecraft.world.item.ItemStack st = hold.get(i);
            if (!st.isEmpty() && rounds.contains(net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(st.getItem()).getPath())) {
                st.shrink(1);
                hold.set(i, st.isEmpty() ? net.minecraft.world.item.ItemStack.EMPTY : st);
                hold.changed();
                return true;
            }
        }
        return false;
    }

    /** The gunner's seat as Superb Warfare holds it: its index, its gun's rounds loaded and its spare, the vehicle's hold. */
    static String state(Entity v, Mob gunner) {
        StringBuilder b = new StringBuilder();
        Object seat = Sbw.call(v, "getSeatIndex", gunner);
        b.append("seat=").append(seat);
        Object data = null;
        if (seat instanceof Number n) {
            try {
                data = v.getClass().getMethod("getGunData", int.class).invoke(v, n.intValue());
            } catch (ReflectiveOperationException | RuntimeException ex) {
                b.append(" getGunData=").append(ex.getClass().getSimpleName());
            }
        }
        b.append(" gun=").append(data == null ? "none" : data.getClass().getSimpleName());
        if (data != null) {
            for (String f : new String[]{"ammo", "backupAmmoCount", "reload", "shootTimer"}) {
                try {
                    Object val = data.getClass().getField(f).get(data);
                    Object got = val == null ? null : Sbw.call(val, "get");
                    b.append(' ').append(f).append('=').append(got != null ? got : val);
                } catch (ReflectiveOperationException | RuntimeException ex) {
                    b.append(' ').append(f).append("=?");
                }
            }
            Object maxAmmo = Sbw.call(data, "magazine");
            b.append(" magazine=").append(maxAmmo);
        }
        int[] r = Supply.rounds(v);
        b.append(" hold=").append(r[0]).append('/').append(r[1]);
        return b.toString();
    }

    private static Method shoot(Entity v) {
        Class<?> c = v.getClass();
        if (NONE.contains(c)) {
            return null;
        }
        Method m = SHOOT.get(c);
        if (m == null) {
            try {
                m = c.getMethod("vehicleShoot", LivingEntity.class, UUID.class, Vec3.class);
                SHOOT.put(c, m);
            } catch (NoSuchMethodException ex) {
                NONE.add(c);
                LOG.warn("GUN-LAYER {} has no vehicleShoot(LivingEntity, UUID, Vec3)", Supply.kind(v));
                return null;
            }
        }
        return m;
    }
}
