package jp.oror.reborn;

import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.MethodType;
import net.minecraft.world.entity.Entity;
import net.neoforged.fml.ModList;

/**
 * Epic Fight's entity patches, reached by name (AdaptiveCombat: whether Epic Fight animates a mob, which then fights by
 * its own animated attacks; GunCompat: a player's battle mode while a gun is held).
 * <p>
 * (059e) The user: "モブのモーションが機能してなかった". The patch was looked up with Class.getMethod, which makes Java
 * load every type EpicFightCapabilities names, the client's LocalPlayer among them; a dedicated server refuses that
 * class ("Attempted to load class net/minecraft/client/player/LocalPlayer for invalid dist DEDICATED_SERVER", in every
 * server log), so the lookup was given up for good at the first mob: every vanilla mob Epic Fight animates passed for
 * one it does not, and AdaptiveCombat fought for it with its own strikes, the mob sliding into its foe with no motion
 * of Epic Fight's attacks. It is now found one method at a time (MethodHandles), as MobGuard and OwnerlessSwords do, and
 * a gun's mode switch failing no longer gives up the patch lookup with it.
 */
final class EpicFightBridge {
    private static boolean broken, looked, gunBroken, warned;
    private static MethodHandle patchOf;
    private static Class<?> mobPatch;
    private static Class<?> playerPatch;

    private EpicFightBridge() {
    }

    private static void look() {
        if (looked) {
            return;
        }
        looked = true;
        MethodHandles.Lookup lk = MethodHandles.publicLookup();
        try {
            Class<?> caps = Class.forName("yesman.epicfight.world.capabilities.EpicFightCapabilities");
            mobPatch = Class.forName("yesman.epicfight.world.capabilities.entitypatch.MobPatch");
            playerPatch = Class.forName("yesman.epicfight.world.capabilities.entitypatch.player.PlayerPatch");
            Class<?> entityPatch = Class.forName("yesman.epicfight.world.capabilities.entitypatch.EntityPatch");
            for (Class<?> ret : new Class<?>[]{entityPatch, Object.class}) {
                try {
                    patchOf = lk.findStatic(caps, "getEntityPatch", MethodType.methodType(ret, Entity.class, Class.class));
                    break;
                } catch (ReflectiveOperationException | LinkageError | RuntimeException ex) {
                    // the other erasure of its return
                }
            }
            if (patchOf == null) {
                giveUp("no getEntityPatch(Entity, Class)");
            }
        } catch (ReflectiveOperationException | LinkageError | RuntimeException ex) {
            giveUp(ex.getClass().getSimpleName());
        }
    }

    private static void giveUp(String why) {
        broken = true;
        System.out.println("[OROR_EPICFIGHT] entity patch lookup disabled: " + why);
    }

    static Object patch(Entity e, boolean player) {
        if (broken || player && gunBroken || e == null || !ModList.get().isLoaded("epicfight")) {
            return null;
        }
        look();
        if (broken) {
            return null;
        }
        Class<?> type = player ? playerPatch : mobPatch;
        try {
            Object p = patchOf.invoke(e, type);
            return type.isInstance(p) ? p : null;
        } catch (Throwable ex) {
            // this entity's patch could not be had: it passes for one without (the next is asked afresh)
            if (!warned) {
                warned = true;
                System.out.println("[OROR_EPICFIGHT] entity patch lookup failed once: " + ex.getClass().getSimpleName());
            }
            return null;
        }
    }

    static boolean animates(Entity e) {
        return patch(e, false) != null;
    }

    /** GunCompat's use of a player's patch (its battle mode) failed: that use is given up, not the patch lookup. */
    static void broken(Throwable x) {
        gunBroken = true;
        System.out.println("[OROR_EPICFIGHT] battle-mode switch disabled: " + (x == null ? "?" : x.getClass().getSimpleName()));
    }
}
