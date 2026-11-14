package jp.oror.reborn.perf;

import java.lang.reflect.Field;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (053) An entity whose tick throws is taken out of the world, with the error in the log, rather than the server
 * stopping with it (NeoForge's own server setting removeErroringEntities, turned on when the server starts). With over
 * a hundred mods, one mod's mob, projectile or spell meeting another's can throw; a guard casting a spell crashed the
 * game this way (the user). The cause is still fixed where it is found (RoyalSpellSafety); this keeps the world running
 * meanwhile.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class CrashNet {
    private static final Logger LOG = LoggerFactory.getLogger("OROR CrashNet");

    private CrashNet() {
    }

    @SubscribeEvent
    public static void started(ServerStartedEvent e) {
        // (059f) a block entity's tick too (a machine, a turret's station, a spawner of some mod's): one that throws is
        // taken out (its block stays) rather than stopping the server (the user: "クラッシュする原因も見直して")
        Boolean entities = set("removeErroringEntities"), blockEntities = set("removeErroringBlockEntities");
        LOG.info("CRASHNET {\"removeErroringEntities\":true,\"was\":{},\"removeErroringBlockEntities\":true,\"wasBlockEntities\":{}}",
            entities, blockEntities);
    }

    /** NeoForge's server setting turned on; what it was (null if it could not be read). */
    private static Boolean set(String name) {
        try {
            Class<?> cfg = Class.forName("net.neoforged.neoforge.common.NeoForgeConfig");
            Object server = cfg.getField("SERVER").get(null);
            Field f = server.getClass().getField(name);
            Object value = f.get(server);
            Object before = value.getClass().getMethod("get").invoke(value);
            if (!Boolean.TRUE.equals(before)) {
                value.getClass().getMethod("set", Object.class).invoke(value, Boolean.TRUE);
            }
            return Boolean.TRUE.equals(before);
        } catch (ReflectiveOperationException | RuntimeException ex) {
            LOG.warn("CRASHNET {\"{}\":\"unavailable\",\"why\":\"{}\"}", name, ex.toString());
            return null;
        }
    }
}
