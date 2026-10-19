package jp.oror.reborn;

import java.util.List;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Items;

public final class TacticalLearning {
    public static String context(Mob m, LivingEntity t) {
        return (t.isBlocking() ? "shield" : "open")
            + "_"
            + ((double)m.getHealth() < (double)m.getMaxHealth() * 0.35 ? "hurt" : "fit")
            + "_"
            + (m.distanceTo(t) > 8.0F ? "far" : "near");
    }

    public static void outcome(Mob m, LivingEntity t, String action, boolean hit) {
        outcome(m, context(m, t), action, hit);
    }

    public static void outcome(Mob m, String context, String action, boolean hit) {
        CompoundTag n = MobMind.data(m);
        CompoundTag table = n.getCompound("TacticalOutcomes");
        String key = context + ":" + action;
        CompoundTag cell = table.getCompound(key);
        cell.putInt(hit ? "Wins" : "Misses", Math.min(1000000, cell.getInt(hit ? "Wins" : "Misses") + 1));
        table.put(key, cell);
        n.put("TacticalOutcomes", table);
        n.putInt("OutcomeSamples", Math.min(2147483646, n.getInt("OutcomeSamples")) + 1);
    }

    public static double score(Mob m, LivingEntity t, String action) {
        CompoundTag cell = MobMind.data(m).getCompound("TacticalOutcomes").getCompound(context(m, t) + ":" + action);
        return ((double)cell.getInt("Wins") + 1.0) / ((double)(cell.getInt("Wins") + cell.getInt("Misses")) + 2.0);
    }

    public static void observe(Mob m, LivingEntity t) {
        if (t instanceof Player p && m.tickCount % 40 == Math.floorMod(m.getId(), 40)) {
            String skill = p.isBlocking()
                ? "shield"
                : (
                    (double)p.fallDistance > 1.5
                        ? "mace"
                        : (p.isSprinting() ? "tactics" : (p.getMainHandItem().is(Items.WATER_BUCKET) ? "terrain" : "teamwork"))
                );
            MobMind.practice(m, skill, 1);
            CompoundTag n = MobMind.data(m);
            n.putString("ObservedMovement", p.isSprinting() ? "sprint_reset" : (p.getDeltaMovement().y < 0.0 ? "descending_critical" : "spacing"));
            n.putString("MovementEvidence", "live_player_observation");
            return;
        }
    }

    public static String choose(Mob m, LivingEntity t, String proposed) {
        if (MobLevels.level(m) >= 3 && !t.isBlocking() && !MobMind.stance(m).equals("unarmed") && !(m instanceof SupremeEntity)) {
            String best = proposed;
            double value = score(m, t, proposed);

            for (String candidate : List.of("sword", "axe", "mace")) {
                if (m.distanceTo(t) > 8.0F) {
                    break;
                }

                CompoundTag cell = MobMind.data(m).getCompound("TacticalOutcomes").getCompound(context(m, t) + ":" + candidate);
                int samples = cell.getInt("Wins") + cell.getInt("Misses");
                double score = score(m, t, candidate);
                if (samples >= 4 && score > value + 0.12) {
                    best = candidate;
                    value = score;
                }
            }

            MobMind.data(m).putString("LearnedChoice", best);
            return best;
        } else {
            return proposed;
        }
    }

    private TacticalLearning() {
    }
}
