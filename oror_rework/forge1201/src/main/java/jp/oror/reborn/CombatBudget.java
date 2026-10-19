package jp.oror.reborn;

import java.util.WeakHashMap;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Mob;

public final class CombatBudget {
    private static final WeakHashMap<ServerLevel, CombatBudget.Frame> FRAMES = new WeakHashMap<>();

    public static boolean take(Mob mob, ServerLevel sl) {
        if (mob instanceof SupremeEntity) {
            return true;
        } else {
            CombatBudget.Frame frame = FRAMES.computeIfAbsent(sl, l -> new CombatBudget.Frame());
            long now = sl.getGameTime();
            if (frame.time != now) {
                frame.time = now;
                frame.used = 0;
            }

            if (now - frame.counted >= 20L) {
                int count = 0;

                for (Entity e : sl.getAllEntities()) {
                    if (e instanceof Mob) {
                        Mob m = (Mob)e;
                        if (m.isAlive()) {
                            count++;
                        }
                    }
                }

                frame.groups = Math.max(1, (count + (Integer)RebornConfig.COMBAT_BUDGET.get() - 1) / (Integer)RebornConfig.COMBAT_BUDGET.get());
                frame.counted = now;
            }

            if (Math.floorMod(mob.getId(), frame.groups) != Math.floorMod(now / 4L, frame.groups)) {
                return false;
            } else if (frame.used >= (Integer)RebornConfig.COMBAT_BUDGET.get()) {
                return false;
            } else {
                frame.used++;
                return true;
            }
        }
    }

    private CombatBudget() {
    }

    private static final class Frame {
        long time = -1L;
        long counted = -100L;
        int used;
        int groups = 1;
    }
}
