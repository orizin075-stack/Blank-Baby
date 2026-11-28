package jp.oror.reborn.combat;

import java.util.UUID;
import jp.oror.reborn.king.RebelPact;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.OwnableEntity;
import net.minecraft.world.entity.ai.Brain;
import net.minecraft.world.entity.ai.behavior.EntityTracker;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.ai.memory.MemoryStatus;
import net.minecraft.world.entity.player.Player;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingChangeTargetEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;

/**
 * (r79, the r78 audit: "全AIで共通の敵対判定を使用する", "敵対記憶・移動目標・攻撃対象を同期する") One answer to "are these
 * two on the same side", for every AI of OROR's and any other mod's that sets a mob's target: a team (vanilla's and any mod's
 * isAlliedTo, both ways), an owner and what it owns (a tamed beast, a summon, a contracted ally), the village's folk among
 * themselves, the kingdom's people and the village's, a caster and its summons (Casters.summoner), and the rebels' allies with
 * one another and with the friend they serve. The rebels' allies are one band: two players' hired allies stand together, as
 * both stand against the king.
 * <p>
 * With it: no mob is given one of its own side for a target (whatever gave it), unless a player of its own side has just
 * struck it; and twice a second a mob whose target has come to be on its side (a pact made in the fight, an owner changed)
 * lets it go, with its brain's anger, attack and walk memories of it (a piglin's ANGRY_AT stayed ten minutes before).
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class Sides {
    private Sides() {
    }

    public static boolean friends(LivingEntity a, LivingEntity b) {
        if (a == null || b == null) {
            return false;
        }
        if (a == b) {
            return true;
        }
        if (a.isAlliedTo(b) || b.isAlliedTo(a)) {
            return true;
        }
        if (owns(a, b) || owns(b, a)) {
            return true;
        }
        if (b instanceof Mob mb && MobDodge.friendly(a, mb) || a instanceof Mob ma && MobDodge.friendly(b, ma)) {
            return true;
        }
        // a caster and what it summoned (Casters.ally's own wider answer, "not his foe" for Azazel and the gods, is no
        // friendship: it would take from Azazel the target he was set on, and the rebels' lord the king)
        if (jp.oror.reborn.waza.Casters.summoner(b) == a.getId() || jp.oror.reborn.waza.Casters.summoner(a) == b.getId()) {
            return true;
        }
        if (a instanceof jp.oror.reborn.royal.RoyalMob && village(b) || b instanceof jp.oror.reborn.royal.RoyalMob && village(a)) {
            return true;
        }
        boolean ra = a.getPersistentData().getBoolean(RebelPact.ALLY), rb = b.getPersistentData().getBoolean(RebelPact.ALLY);
        if (ra && rb) {
            return true;
        }
        return ra && serves(a, b) || rb && serves(b, a);
    }

    private static boolean village(LivingEntity e) {
        return e instanceof net.minecraft.world.entity.npc.AbstractVillager || e instanceof net.minecraft.world.entity.animal.IronGolem;
    }

    private static boolean owns(LivingEntity owner, LivingEntity owned) {
        if (owned instanceof OwnableEntity o && o.getOwnerUUID() != null && o.getOwnerUUID().equals(owner.getUUID())) {
            return true;
        }
        UUID rebelOwner = RebelPact.ownerOf(owned);
        return rebelOwner != null && rebelOwner.equals(owner.getUUID());
    }

    private static boolean serves(LivingEntity ally, LivingEntity other) {
        return other instanceof Player p && (other.getUUID().equals(RebelPact.ownerOf(ally)) || RebelPact.friend(p));
    }

    /** A player of the mob's own side who has just struck it may be answered. */
    private static boolean provoked(Mob m, LivingEntity t) {
        return t instanceof Player && m.getLastHurtByMob() == t && m.tickCount - m.getLastHurtByMobTimestamp() < 100;
    }

    @SubscribeEvent(priority = EventPriority.LOW)
    public static void target(LivingChangeTargetEvent e) {
        if (Boolean.getBoolean("oror.bisect") || EXPERIMENT) {
            return;
        }
        LivingEntity t = e.getNewAboutToBeSetTarget();
        if (t == null || e.isCanceled() || !(e.getEntity() instanceof Mob m) || m.level().isClientSide) {
            return;
        }
        if (friends(m, t) && !provoked(m, t)) {
            e.setCanceled(true);
            COUNT[0]++;
        }
    }

    @SubscribeEvent
    public static void tick(EntityTickEvent.Post e) {
        if (EXPERIMENT || !(e.getEntity() instanceof Mob m) || m.level().isClientSide || (m.tickCount + m.getId()) % 10 != 0) {
            return;
        }
        LivingEntity t = m.getTarget();
        if (t != null && friends(m, t) && !provoked(m, t)) {
            forget(m, t);
            COUNT[1]++;
        }
    }

    /** The mob lets go of t: its target, and its brain's anger at, attack on and walk to it; it stops where it was going. */
    public static void forget(Mob m, LivingEntity t) {
        if (m.getTarget() == t) {
            m.setTarget(null);
        }
        Brain<?> b = m.getBrain();
        if (b.checkMemory(MemoryModuleType.ANGRY_AT, MemoryStatus.REGISTERED)
            && b.getMemory(MemoryModuleType.ANGRY_AT).map(u -> u.equals(t.getUUID())).orElse(false)) {
            b.eraseMemory(MemoryModuleType.ANGRY_AT);
        }
        if (b.checkMemory(MemoryModuleType.ATTACK_TARGET, MemoryStatus.REGISTERED)
            && b.getMemory(MemoryModuleType.ATTACK_TARGET).map(x -> x == t).orElse(false)) {
            b.eraseMemory(MemoryModuleType.ATTACK_TARGET);
        }
        if (b.checkMemory(MemoryModuleType.WALK_TARGET, MemoryStatus.REGISTERED)
            && b.getMemory(MemoryModuleType.WALK_TARGET).map(w -> w.getTarget() instanceof EntityTracker et && et.getEntity() == t).orElse(false)) {
            b.eraseMemory(MemoryModuleType.WALK_TARGET);
            m.getNavigation().stop();
        }
    }

    /** For the checks: targets turned away, targets let go. */
    public static final int[] COUNT = new int[2];

    /** BISECT EXPERIMENT (to be removed): Sides' handlers off. */
    public static final boolean EXPERIMENT = true;
}
