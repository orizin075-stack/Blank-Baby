package jp.oror.reborn.combat;

import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.Brain;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.ai.memory.MemoryStatus;
import net.minecraft.world.entity.ai.memory.WalkTarget;
import net.minecraft.world.entity.monster.hoglin.Hoglin;
import net.minecraft.world.entity.monster.piglin.AbstractPiglin;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingChangeTargetEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;

/**
 * (r65) A target set on a mob its brain leads (piglins, piglin brutes, hoglins) holds. Their getTarget() reads the brain's
 * attack target, and their brain lets go of any target that is not the one it would have picked itself (for a brute: a
 * player or a wither skeleton; StopAttackingIfTargetInvalid), the next tick. So the siege's Nether army never fought the
 * kingdom (a brute beside a guard or a golem stood by), nor a rebels' piglin the king's people, nor did a brute ever strike
 * the CI's golem (MOBS-TRACE: 0 hits in every run since 11/15). Their own anger is what their brain honours first
 * (findNearestValidAttackTarget reads ANGRY_AT before anything else), as when a player strikes one: an order to fight
 * (Mob.setTarget, by OROR or any mod) is given as that anger, and as the attack target, the same moment.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class BrainTargets {
    /** As long as a piglin stays angry at one who struck it (PiglinAi). */
    static final long ANGER = 600L;

    private BrainTargets() {
    }

    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void ordered(LivingChangeTargetEvent e) {
        if (e.getTargetType() != LivingChangeTargetEvent.LivingTargetType.MOB_TARGET) {
            return;
        }
        LivingEntity t = e.getNewAboutToBeSetTarget();
        if (t == null || !(e.getEntity() instanceof Mob m) || m.level().isClientSide || t == m || !t.isAlive()
            || !(m instanceof AbstractPiglin || m instanceof Hoglin)) {
            return;
        }
        Brain<?> b = m.getBrain();
        if (b.checkMemory(MemoryModuleType.ANGRY_AT, MemoryStatus.REGISTERED)) {
            b.setMemoryWithExpiry(MemoryModuleType.ANGRY_AT, t.getUUID(), ANGER);
        }
        if (b.checkMemory(MemoryModuleType.ATTACK_TARGET, MemoryStatus.REGISTERED)) {
            b.setMemory(MemoryModuleType.ATTACK_TARGET, t);
        }
    }

    /**
     * (r65) And it goes to it. Under Epic Fight's patch (the pack as played: NightfallCraft's AdvancedCustomHumanoidMobPatch)
     * a brute's brain fights by the patch's combat goal, but nothing walks it to its foe: the CI's brute stood 154 of 200
     * ticks four blocks from the golem and struck it twice, where every goal-led mob closed to arm's reach (the pack as
     * played, MOBS-TRACE). A brain mob with a foe out of reach and nowhere to walk is walked to it, as its brain's own
     * SetWalkTargetFromAttackTargetIfTargetOutOfReach would.
     */
    @SubscribeEvent
    public static void close(EntityTickEvent.Post e) {
        if (!(e.getEntity() instanceof Mob m) || !(m instanceof AbstractPiglin || m instanceof Hoglin) || m.level().isClientSide
            || (m.tickCount + m.getId()) % 10 != 0 || m.isNoAi() || m.isPassenger()) {
            return;
        }
        LivingEntity t = m.getTarget();
        if (t == null || !t.isAlive() || t.level() != m.level()) {
            why(m, "no target");
            return;
        }
        double d = m.distanceToSqr(t);
        if (d < 2.5 * 2.5 || d > 32 * 32) {
            why(m, d < 6.25 ? "near" : "far");
            return;
        }
        if (!m.getNavigation().isDone()) {
            why(m, "walking");
            return;
        }
        Brain<?> b = m.getBrain();
        if (!b.checkMemory(MemoryModuleType.WALK_TARGET, MemoryStatus.REGISTERED)) {
            why(m, "no walk memory");
            return;
        }
        java.util.Optional<WalkTarget> w = b.getMemory(MemoryModuleType.WALK_TARGET);
        // walking elsewhere (a hoglin backing off from warped fungus, a piglin to its gold): its brain's choice stands
        if (w.isPresent() && !(w.get().getTarget() instanceof net.minecraft.world.entity.ai.behavior.EntityTracker et && et.getEntity() == t)) {
            why(m, "walk elsewhere " + w.get().getTarget().currentBlockPosition().toShortString());
            return;
        }
        if (w.isEmpty()) {
            b.setMemory(MemoryModuleType.WALK_TARGET, new WalkTarget(t, 1.0F, 1));
        }
        boolean went = m.getNavigation().moveTo(t, 1.0);
        why(m, went ? "sent" : "no path");
        m.getPersistentData().putInt("OrorBrainClose", m.getPersistentData().getInt("OrorBrainClose") + 1);
    }

    /** (r65) for the checks: why the last look found nothing to do */
    static void why(Mob m, String s) {
        m.getPersistentData().putString("OrorBrainCloseWhy", s);
    }

    /** (r65) for the checks: the brain mob's walking, as close() saw it */
    public static String trace(Mob m) {
        net.minecraft.nbt.CompoundTag d = m.getPersistentData();
        String act = m.getBrain().getActiveNonCoreActivity().map(Object::toString).orElse("-");
        String walk = m.getBrain().checkMemory(MemoryModuleType.WALK_TARGET, MemoryStatus.REGISTERED)
            ? m.getBrain().getMemory(MemoryModuleType.WALK_TARGET).map(w -> w.getTarget().currentBlockPosition().toShortString()).orElse("none") : "-";
        return "close " + d.getInt("OrorBrainClose") + " why " + d.getString("OrorBrainCloseWhy") + " navDone " + m.getNavigation().isDone()
            + " activity " + act + " walk " + walk + " speed " + String.format(java.util.Locale.ROOT, "%.2f", m.getSpeed());
    }
}
