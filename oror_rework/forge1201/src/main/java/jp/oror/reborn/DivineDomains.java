package jp.oror.reborn;

import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.WeakHashMap;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraftforge.event.entity.living.LivingEvent.LivingTickEvent;

public final class DivineDomains {
    private static final Map<ServerLevel, long[]> BUDGET = new WeakHashMap<>();
    private static final Set<String> ERASURE = Set.of("miyohime", "tenki", "kokuhaku", "demiurgos", "shinra", "fallen_savior", "innocence", "ain_sof_aur");

    private static int available(ServerLevel sl) {
        long[] state = BUDGET.computeIfAbsent(sl, k -> new long[]{-1L, 0L});
        if (state[0] != sl.getGameTime()) {
            state[0] = sl.getGameTime();
            state[1] = 0L;
        }

        return (int)Math.max(0L, 512L - state[1]);
    }

    private static boolean intended(SupremeEntity b, LivingEntity t) {
        if (b.arena || b.spec.behavior.equals("violent") || t == b.getTarget() || b.spec.behavior.equals("guardian") && t instanceof Enemy) {
            return true;
        } else {
            if (t instanceof Mob m && (m.getTarget() == b || m.getLastHurtByMob() == b || m.getTarget() != null && b.ally(m.getTarget()))) {
                return true;
            }

            return false;
        }
    }

    public static void begin(SupremeEntity b) {
        if (b.lore() && (Boolean)RebornConfig.DIVINE_DOMAINS.get() && AdaptiveCombat.enemy(b, b.getTarget())) {
            CompoundTag n = b.getPersistentData();
            n.putLong("OrorDomainUntil", b.level().getGameTime() + 200L);
            n.putLong("OrorDomainCasts", n.getLong("OrorDomainCasts") + 1L);
        }
    }

    public static void tick(LivingTickEvent event) {
        if (event.getEntity() instanceof SupremeEntity b
            && b.level() instanceof ServerLevel sl
            && b.lore()
            && !b.isNoAi()
            && b.isAlive()
            && (Boolean)RebornConfig.DIVINE_DOMAINS.get()) {
            if (!b.getPersistentData().contains("OrorDomainUntil") || b.getPersistentData().getLong("OrorDomainUntil") <= sl.getGameTime()) {
                if (!AdaptiveCombat.enemy(b, b.getTarget())) {
                    return;
                }

                begin(b);
            }

            int allowance = Math.min(128, available(sl));
            if (allowance == 0) {
                return;
            }

            List<LivingEntity> targets = sl.getEntitiesOfClass(
                LivingEntity.class, b.getBoundingBox().inflate(48.0), e -> e != b && b.validEnemy(e) && !(e instanceof SupremeEntity) && intended(b, e)
            );
            int count = 0;

            for (LivingEntity target : targets) {
                if (count++ >= allowance) {
                    break;
                }

                BUDGET.get(sl)[1]++;
                float before = target.getHealth();
                LorePowers.strike(b, target, 1000000.0F, ERASURE.contains(b.spec.id));
                if (before > 0.0F && !target.isAlive()) {
                    b.getPersistentData().putLong("OrorDomainDefeats", b.getPersistentData().getLong("OrorDomainDefeats") + 1L);
                }
            }

            return;
        }
    }

    private DivineDomains() {
    }
}
