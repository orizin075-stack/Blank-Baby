package jp.oror.reborn.king;

import jp.oror.reborn.mixin.RoyalMobBossAccess;
import jp.oror.reborn.royal.RoyalMob;
import net.minecraft.server.level.ServerBossEvent;

/** (054) The king's two boss bars (his life and his AT field), as RoyalMob keeps them. */
public final class KingBars {
    private KingBars() {
    }

    public static ServerBossEvent[] of(RoyalMob king) {
        if (!((Object) king instanceof RoyalMobBossAccess a)) {
            return null;
        }
        return new ServerBossEvent[]{a.oror$boss(), a.oror$atBoss()};
    }
}
