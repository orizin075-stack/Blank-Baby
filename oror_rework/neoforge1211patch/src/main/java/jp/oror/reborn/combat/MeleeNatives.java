package jp.oror.reborn.combat;

import java.util.Set;
import jp.oror.reborn.MobMind;
import jp.oror.reborn.SupremeEntity;
import jp.oror.reborn.royal.RoyalMob;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.monster.RangedAttackMob;
import net.minecraft.world.entity.monster.WitherSkeleton;

/**
 * (053) The monsters that fight hand to hand by nature (zombies, husks, wither skeletons, vindicators, piglin brutes,
 * zombified piglins and the like: none of Minecraft's archers, crossbowmen, witches or trident throwers) keep to it.
 * OROR's adaptive combat (AdaptiveCombat.select) gave any mob a bow when its target was more than eight blocks off, so a
 * wither skeleton stopped, drew a bow and shot from afar instead of coming on with its sword, a piglin brute stood off
 * at eight blocks loosing arrows (the user: wither skeletons and other mobs behaving oddly; 053's CI saw both). For these
 * the weapon is now chosen as if the target were eight blocks away, and they close in. A mob that was told to prefer the
 * bow or to keep a ranged stance (MobMind), OROR's own characters and the kingdom's people choose as before.
 */
public final class MeleeNatives {
    private static final Set<String> RANGED = Set.of("bow", "crossbow");

    private MeleeNatives() {
    }

    public static boolean keepsClose(Mob m) {
        if (!(m instanceof Enemy) || m instanceof SupremeEntity || m instanceof RoyalMob) {
            return false;
        }
        if (m instanceof RangedAttackMob && !(m instanceof WitherSkeleton)) {
            return false;
        }
        return !RANGED.contains(MobMind.preferred(m)) && !"ranged".equals(MobMind.stance(m));
    }
}
