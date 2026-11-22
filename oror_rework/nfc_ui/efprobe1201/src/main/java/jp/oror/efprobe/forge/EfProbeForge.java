package jp.oror.efprobe.forge;

import jp.oror.efprobe.EfProbeCore;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/** Starts the Epic Fight check 30 seconds after the server is up (as OROR's CI waits for its world), stops the server after it. */
@Mod("oror_efprobe")
public final class EfProbeForge {
    private static final Logger LOG = LoggerFactory.getLogger("OROR EF Probe");
    private static int ticks, after = -1;

    public EfProbeForge() {
        MinecraftForge.EVENT_BUS.register(this);
    }

    static final EfProbeCore.Hooks HOOKS = new EfProbeCore.Hooks() {
        @Override
        public void equip(ServerLevel level, Mob m) {
            m.finalizeSpawn(level, level.getCurrentDifficultyAt(m.blockPosition()), MobSpawnType.COMMAND, null, null);
        }
    };

    @SubscribeEvent
    public void tick(TickEvent.ServerTickEvent e) {
        if (e.phase != TickEvent.Phase.END) {
            return;
        }
        MinecraftServer server = e.getServer();
        ticks++;
        if (ticks == 600) {
            LOG.info("EFP-FORGE {\"start\":true}");
            EfProbeCore.start(server.overworld(), "nightfallcraft", HOOKS);
        }
        EfProbeCore.tick();
        if (EfProbeCore.done && after < 0) {
            after = ticks;
        }
        if ((after >= 0 && ticks - after > 60) || ticks > 600 + EfProbeCore.TICKS + 2400) {
            LOG.info("EFP-FORGE {\"halt\":true,\"done\":{}}", EfProbeCore.done);
            server.halt(false);
        }
    }
}
