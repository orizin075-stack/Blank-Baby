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
        try {
            Class<?> cfg = Class.forName("net.neoforged.neoforge.common.NeoForgeConfig");
            Object server = cfg.getField("SERVER").get(null);
            Field f = server.getClass().getField("removeErroringEntities");
            Object value = f.get(server);
            Object before = value.getClass().getMethod("get").invoke(value);
            if (!Boolean.TRUE.equals(before)) {
                value.getClass().getMethod("set", Object.class).invoke(value, Boolean.TRUE);
            }
            LOG.info("CRASHNET {\"removeErroringEntities\":true,\"was\":{}}", before);
        } catch (ReflectiveOperationException | RuntimeException ex) {
            LOG.warn("CRASHNET {\"removeErroringEntities\":\"unavailable\",\"why\":\"{}\"}", ex.toString());
        }
    }
}
