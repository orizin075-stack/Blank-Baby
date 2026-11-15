package jp.oror.reborn.vehicle;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.UUID;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.Projectile;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * (059g) The TOW's gunner keeps his missile on the target. Superb Warfare's wire-guided missile flies where the one who
 * fired it is aiming, as his game tells it each moment; a soldier's has nothing to tell it, and the CI check's six missiles
 * flew straight on over their target and 1,600 blocks out until they were taken away. A missile one of the kingdom's
 * gunners fires (GunLayer has him marked with his target for twenty seconds) is told its target, and that target's place
 * every tick while both are in the world (Superb Warfare's own setTargetUuid, setTargetVec and setTargetPos).
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class MissileGuide {
    /** Gunners who have just fired, with their target and until when. */
    private static final Map<UUID, Object[]> AIMING = new HashMap<>();
    /** Missiles in flight, with their target. */
    private static final Map<Entity, UUID> FLYING = new HashMap<>();
    static int guided;

    private MissileGuide() {
    }

    static void fired(Entity gunner, LivingEntity target) {
        AIMING.put(gunner.getUUID(), new Object[]{target.getUUID(), gunner.level().getGameTime() + 400});
    }

    @SubscribeEvent
    public static void joined(EntityJoinLevelEvent e) {
        if (AIMING.isEmpty() || !(e.getLevel() instanceof ServerLevel) || !(e.getEntity() instanceof Projectile p)) {
            return;
        }
        if (!BuiltInRegistries.ENTITY_TYPE.getKey(p.getType()).getPath().contains("missile") || p.getOwner() == null) {
            return;
        }
        Object[] a = AIMING.get(p.getOwner().getUUID());
        if (a != null) {
            FLYING.put(p, (UUID) a[0]);
            guided++;
        }
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        if (FLYING.isEmpty() && AIMING.isEmpty()) {
            return;
        }
        ServerLevel level = e.getServer().overworld();
        long now = level.getGameTime();
        AIMING.values().removeIf(a -> (Long) a[1] < now);
        for (Iterator<Map.Entry<Entity, UUID>> it = FLYING.entrySet().iterator(); it.hasNext(); ) {
            Map.Entry<Entity, UUID> en = it.next();
            Entity m = en.getKey();
            Entity t = m.level() instanceof ServerLevel sl ? sl.getEntity(en.getValue()) : null;
            if (m.isRemoved() || t == null || !t.isAlive()) {
                it.remove();
                continue;
            }
            net.minecraft.world.phys.Vec3 at = t.getBoundingBox().getCenter();
            Sbw.call(m, "setTargetUuid", t.getStringUUID());
            Sbw.call(m, "setTargetVec", at);
            Sbw.call(m, "setTargetPos", at);
        }
    }
}
