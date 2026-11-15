package jp.oror.reborn;

import java.util.Locale;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.npc.Villager;

/**
 * (059g) What a villager is about, in one line for the CI's logs (VillageRoadTest, VillageArmsTest): the hour, his brain's
 * activity, where his brain and his feet are going, his target, whether he flees or sleeps, the village's task for him.
 * (CI 59: a trader that had walked 13 blocks of his road in 8 seconds the run before stood still; a tank's second crewman never
 * came within 12 blocks of it. Neither said why.)
 */
final class VillagerState {
    private VillagerState() {
    }

    static String of(Villager v, Entity near) {
        StringBuilder s = new StringBuilder();
        s.append(String.format(Locale.ROOT, "hour %d", v.level().getDayTime() % 24000L));
        s.append(" activity ").append(v.getBrain().getActiveNonCoreActivity().map(a -> a.getName()).orElse("-"));
        s.append(" brainTo ").append(v.getBrain().getMemory(MemoryModuleType.WALK_TARGET)
            .map(w -> pos(w.getTarget().currentBlockPosition())).orElse("-"));
        BlockPos nav = v.getNavigation().getTargetPos();
        s.append(" navTo ").append(nav == null ? "-" : pos(nav)).append(v.getNavigation().isDone() ? " (done)" : "");
        s.append(" at ").append(pos(v.blockPosition()));
        if (near != null) {
            s.append(String.format(Locale.ROOT, " off %.1f", v.distanceTo(near)));
        }
        if (v.getTarget() != null) {
            s.append(" target ").append(BuiltInRegistries.ENTITY_TYPE.getKey(v.getTarget().getType()).getPath());
        }
        if (v.isSleeping()) {
            s.append(" sleeping");
        }
        if (v.isPassenger()) {
            s.append(" riding");
        }
        if (VillageAI.fleeing(v)) {
            s.append(" fleeing");
        }
        CompoundTag d = VillagerLife.data(v);
        s.append(" task ").append(d.getString("Task").isEmpty() ? "-" : d.getString("Task"));
        for (String k : new String[]{"Trip", "Flight", "Sortie"}) {
            if (d.contains(k)) {
                s.append(' ').append(k);
            }
        }
        return s.toString();
    }

    private static String pos(BlockPos p) {
        return p.getX() + "," + p.getY() + "," + p.getZ();
    }
}
