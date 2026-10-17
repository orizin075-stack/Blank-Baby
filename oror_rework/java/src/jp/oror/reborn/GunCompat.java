package jp.oror.reborn;

import java.lang.reflect.Method;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.neoforged.fml.ModList;

/**
 * Guns and Epic Fight (v0.17.12). The pack starts every player in Epic Fight's battle mode, where a left click that is
 * not aimed at a block always plays a melee attack, whatever is in hand. TaCZ, Just Enough Guns and Superb Warfare fire
 * on the same left click, so every shot also swung the gun as a club. While a gun from another mod is in the main hand
 * the player is put in vanilla mode, and back in battle mode when it leaves the hand (only if this switched it, so a
 * mode the player picked themselves stays). Epic Fight is reached by reflection and left alone if its API differs.
 * Called every 5 ticks for each player from WorldEvents.
 */
public final class GunCompat {
    private static boolean broken;
    private static Method patchOf;
    private static Class<?> patchClass;
    private static Method isBattle;
    private static Method toVanilla;
    private static Method toBattle;

    private GunCompat() {
    }

    static void tick(Player p) {
        if (broken || !ModList.get().isLoaded("epicfight")) {
            return;
        }
        CompoundTag d = p.getPersistentData();
        boolean gun = AdaptiveCombat.gunClass(p.getMainHandItem());
        if (gun == d.getBoolean("ororGunHeld")) {
            return;
        }
        d.putBoolean("ororGunHeld", gun);
        try {
            Object patch = patch(p);
            if (patch == null) {
                return;
            }
            if (gun && (Boolean) isBattle.invoke(patch)) {
                toVanilla.invoke(patch, true);
                d.putBoolean("ororGunVanilla", true);
                p.displayClientMessage(Component.translatable("weapon_kind.oror_supreme_bosses.gun_mode"), true);
            } else if (!gun && d.getBoolean("ororGunVanilla")) {
                d.remove("ororGunVanilla");
                if (!(Boolean) isBattle.invoke(patch)) {
                    toBattle.invoke(patch, true);
                }
            }
        } catch (LinkageError | ReflectiveOperationException | ClassCastException e) {
            broken = true;
            System.out.println("[OROR_GUNS] Epic Fight mode switching disabled: " + e.getClass().getSimpleName());
        }
    }

    private static Object patch(Player p) throws ReflectiveOperationException {
        if (patchOf == null) {
            Class<?> caps = Class.forName("yesman.epicfight.world.capabilities.EpicFightCapabilities");
            patchClass = Class.forName("yesman.epicfight.world.capabilities.entitypatch.player.PlayerPatch");
            patchOf = caps.getMethod("getEntityPatch", Entity.class, Class.class);
            isBattle = patchClass.getMethod("isEpicFightMode");
            toVanilla = patchClass.getMethod("toVanillaMode", boolean.class);
            toBattle = patchClass.getMethod("toEpicFightMode", boolean.class);
        }
        return patchOf.invoke(null, p, patchClass);
    }
}
