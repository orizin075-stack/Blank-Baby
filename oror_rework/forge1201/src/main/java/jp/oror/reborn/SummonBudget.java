package jp.oror.reborn;

import java.util.UUID;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Mob;

public final class SummonBudget {
    private SummonBudget() {
    }

    public static int remaining(ServerLevel level, UUID creator, int creatorLimit, int requested) {
        int total = 0;
        int owned = 0;

        for (Entity entity : level.getAllEntities()) {
            if (entity instanceof Mob) {
                Mob mob = (Mob)entity;
                if (mob.isAlive()) {
                    UUID owner;
                    if (entity instanceof FamiliarEntity familiar) {
                        owner = familiar.creator;
                    } else {
                        if (!entity.getPersistentData().hasUUID("ororRelicOwner")) {
                            continue;
                        }

                        owner = entity.getPersistentData().getUUID("ororRelicOwner");
                    }

                    total++;
                    if (creator.equals(owner)) {
                        owned++;
                    }
                }
            }
        }

        return Math.max(0, Math.min(requested, Math.min(creatorLimit - owned, (Integer)RebornConfig.LEVEL_SUMMONS.get() - total)));
    }
}
