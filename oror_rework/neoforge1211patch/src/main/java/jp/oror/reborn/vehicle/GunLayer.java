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
        if (!RoyalPilots.lineOfFire(v, target)) {
            p.putString("LayWhy", "noLine");
            return;
        }
        Object can = Sbw.call(v, "canShoot", gunner);
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
        } catch (ReflectiveOperationException | RuntimeException ex) {
            if (failures++ < 5) {
                LOG.warn("GUN-LAYER {} could not fire: {}", Supply.kind(v), ex.toString());
            }
        }
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
