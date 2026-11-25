package jp.oror.reborn.combat;

import java.util.ArrayList;
import java.util.Map;
import java.util.WeakHashMap;
import jp.oror.reborn.EpicFightBridge;
import jp.oror.reborn.show.TechniqueShow;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.common.Tags;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * (r76, the user: "ダウン状態とそこに攻撃入れると特殊モーションと一緒に超ダメージはいってその後スタミナ一気に回復するシステムを　放置したら
 * 立ち直ってスタミナ全回復するけど　ナイトフォールクラフトにもあったよ") The down, as NightfallCraft has it: a mob whose stamina breaks
 * (MobStamina: winded) goes down for five seconds (three for a boss): it kneels, dazed (Epic Fight's NEUTRALIZE stun on a
 * mob Epic Fight moves, which is what opens it to Combat Evolution's execution and its own motion, as in NightfallCraft),
 * stars about its head; it neither moves nor strikes, dodges nor guards.
 * <ul>
 * <li>Struck while down: a critical blow (致命の一撃), three times the blow and a tenth of its health (a boss: twice and a
 * twenty-fifth), thrown down by it (Epic Fight's KNOCKDOWN), with a burst of sparks, a sweep and a crash; then it is up
 * at once with all its stamina back. Combat Evolution's execution, when that is what struck, deals its own blow (not
 * multiplied again) and the mob is up with all its stamina when the execution is done.</li>
 * <li>Left alone: up again when the time is out, its stamina full.</li>
 * </ul>
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class MobDown {
    public static final int TICKS = 100, BOSS_TICKS = 60;

    static final class Down {
        long until;
        boolean executed;
        long upAt = -1;
    }

    private static final Map<Mob, Down> DOWN = new WeakHashMap<>();
    public static int downs, criticals, executions, rose;
    private static boolean ceHooked;

    private MobDown() {
    }

    static boolean boss(Mob m) {
        return m.getType().is(Tags.EntityTypes.BOSSES) || m instanceof jp.oror.reborn.SupremeEntity;
    }

    public static boolean isDown(LivingEntity e) {
        return e instanceof Mob m && DOWN.containsKey(m);
    }

    /** Its stamina broken: down, for five seconds (three for a boss). */
    public static void down(Mob m) {
        if (m.level().isClientSide || DOWN.containsKey(m) || !m.isAlive()) {
            return;
        }
        hookCombatEvolution();
        Down d = new Down();
        int ticks = boss(m) ? BOSS_TICKS : TICKS;
        d.until = m.level().getGameTime() + ticks;
        DOWN.put(m, d);
        downs++;
        m.getPersistentData().putInt("OrorDowns", m.getPersistentData().getInt("OrorDowns") + 1);
        m.getNavigation().stop();
        EpicFightBridge.stun(m, "NEUTRALIZE", ticks / 20F);
        TechniqueShow.send(m, "winded", 0, 1, ticks, -1);
        if (m.level() instanceof ServerLevel sl) {
            sl.playSound(null, m.blockPosition(), SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 0.35F, 0.6F);
            sl.playSound(null, m.blockPosition(), SoundEvents.PLAYER_ATTACK_KNOCKBACK, SoundSource.HOSTILE, 0.9F, 0.7F);
            sl.sendParticles(ParticleTypes.CRIT, m.getX(), m.getY() + m.getBbHeight() * 0.6, m.getZ(), 20, 0.3, 0.3, 0.3, 0.3);
        }
    }

    /** Up again, its stamina full. */
    static void up(Mob m, boolean struck) {
        if (DOWN.remove(m) == null) {
            return;
        }
        rose++;
        MobStamina.restore(m);
        if (!struck && m.level() instanceof ServerLevel sl) {
            sl.playSound(null, m.blockPosition(), SoundEvents.ARMOR_EQUIP_GENERIC.value(), SoundSource.HOSTILE, 0.8F, 0.8F);
            sl.sendParticles(ParticleTypes.CLOUD, m.getX(), m.getY() + 0.2, m.getZ(), 8, 0.3, 0.05, 0.3, 0.02);
        }
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        if (DOWN.isEmpty()) {
            return;
        }
        for (Map.Entry<Mob, Down> en : new ArrayList<>(DOWN.entrySet())) {
            Mob m = en.getKey();
            Down d = en.getValue();
            if (m == null || !m.isAlive()) {
                DOWN.remove(m);
                continue;
            }
            long now = m.level().getGameTime();
            if (d.upAt >= 0 && now >= d.upAt || d.upAt < 0 && now >= d.until) {
                up(m, d.upAt >= 0);
                continue;
            }
            // held where it fell: no steps, no lunge
            m.getNavigation().stop();
            Vec3 v = m.getDeltaMovement();
            m.setDeltaMovement(0, Math.min(v.y, 0), 0);
            if (m.level() instanceof ServerLevel sl && (now + m.getId()) % 5 == 0) {
                // stars about its head
                double a = now * 0.35;
                for (int i = 0; i < 3; i++) {
                    double b = a + i * Math.PI * 2 / 3;
                    sl.sendParticles(ParticleTypes.ENCHANTED_HIT, m.getX() + Math.cos(b) * 0.45, m.getY() + m.getBbHeight() + 0.25,
                        m.getZ() + Math.sin(b) * 0.45, 1, 0, 0, 0, 0);
                }
            }
        }
    }

    /** A downed mob strikes no one. */
    @SubscribeEvent(priority = EventPriority.HIGHEST)
    public static void noBlows(LivingIncomingDamageEvent e) {
        if (e.getSource().getEntity() instanceof Mob m && e.getSource().getDirectEntity() == m && DOWN.containsKey(m)) {
            e.setCanceled(true);
        }
    }

    /** Struck down: the critical blow (or Combat Evolution's execution), then up with all its stamina. */
    @SubscribeEvent(priority = EventPriority.HIGH)
    public static void struck(LivingIncomingDamageEvent e) {
        if (!(e.getEntity() instanceof Mob m) || m.level().isClientSide || !(e.getSource().getEntity() instanceof LivingEntity attacker) || attacker == m) {
            return;
        }
        Down d = DOWN.get(m);
        if (d == null || d.upAt >= 0) {
            return;
        }
        if (d.executed) {
            // Combat Evolution's execution deals its own blow: up when it is done
            d.upAt = m.level().getGameTime() + 25;
            return;
        }
        boolean boss = boss(m);
        float extra = m.getMaxHealth() * (boss ? 0.04F : 0.10F);
        e.setAmount(e.getAmount() * (boss ? 2F : 3F) + extra);
        criticals++;
        m.getPersistentData().putInt("OrorCriticals", m.getPersistentData().getInt("OrorCriticals") + 1);
        // thrown down by it, and up again a moment later with all its stamina
        d.upAt = m.level().getGameTime() + 20;
        EpicFightBridge.stun(m, "KNOCKDOWN", 1.0F);
        if (m.level() instanceof ServerLevel sl) {
            Vec3 at = m.position().add(0, m.getBbHeight() * 0.55, 0);
            sl.sendParticles(ParticleTypes.SWEEP_ATTACK, at.x, at.y, at.z, 3, 0.4, 0.2, 0.4, 0);
            sl.sendParticles(ParticleTypes.CRIT, at.x, at.y, at.z, 40, 0.4, 0.5, 0.4, 0.6);
            sl.sendParticles(ParticleTypes.ENCHANTED_HIT, at.x, at.y, at.z, 30, 0.4, 0.5, 0.4, 0.5);
            sl.sendParticles(ParticleTypes.EXPLOSION, at.x, at.y, at.z, 1, 0, 0, 0, 0);
            sl.playSound(null, m.blockPosition(), SoundEvents.PLAYER_ATTACK_CRIT, SoundSource.PLAYERS, 1.0F, 0.7F);
            sl.playSound(null, m.blockPosition(), SoundEvents.ANVIL_LAND, SoundSource.PLAYERS, 0.6F, 0.5F);
            sl.playSound(null, m.blockPosition(), SoundEvents.TRIDENT_THUNDER.value(), SoundSource.PLAYERS, 0.35F, 1.6F);
            Vec3 push = m.position().subtract(attacker.position()).multiply(1, 0, 1).normalize().scale(0.6);
            m.push(push.x, 0.35, push.z);
            m.hurtMarked = true;
        }
    }

    /** Combat Evolution's execution of a downed mob (read by name: Combat Evolution is the pack's, not OROR's). */
    @SuppressWarnings({"unchecked", "rawtypes"})
    private static void hookCombatEvolution() {
        if (ceHooked) {
            return;
        }
        ceHooked = true;
        try {
            Class ev = Class.forName("net.shelmarow.combat_evolution.api.event.OnExecutionStartEvent");
            java.lang.reflect.Method target = ev.getMethod("getTarget");
            NeoForge.EVENT_BUS.addListener(EventPriority.LOWEST, false, ev, (java.util.function.Consumer) event -> {
                try {
                    Object patch = target.invoke(event);
                    Object original = patch.getClass().getMethod("getOriginal").invoke(patch);
                    if (original instanceof Mob m && DOWN.get(m) instanceof Down d) {
                        d.executed = true;
                        executions++;
                        // up when the execution's motion is through, whatever its blow did
                        d.upAt = m.level().getGameTime() + 60;
                    }
                } catch (ReflectiveOperationException | RuntimeException ex) {
                    // another version of it
                }
            });
        } catch (ClassNotFoundException | LinkageError ex) {
            // Combat Evolution is not here
        } catch (ReflectiveOperationException ex) {
            System.out.println("[OROR] Combat Evolution's execution not hooked: " + ex);
        } catch (RuntimeException ex) {
            System.out.println("[OROR] Combat Evolution's execution not hooked: " + ex);
        }
    }
}
