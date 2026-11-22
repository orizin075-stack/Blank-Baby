package jp.oror.efprobe.forge;

import com.mojang.authlib.GameProfile;
import java.util.UUID;
import jp.oror.efprobe.EfProbeCore;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.player.Player;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.common.util.FakePlayer;
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

    static final class Tester extends FakePlayer {
        Tester(ServerLevel level, int n) {
            super(level, new GameProfile(UUID.nameUUIDFromBytes(("oror-efprobe-" + n).getBytes()), "[EF Probe " + n + "]"));
        }

        @Override
        public boolean isInvulnerableTo(DamageSource source) {
            return false;
        }

        @Override
        public boolean isInvulnerable() {
            return false;
        }

        /**
         * (run nfc 2) a new player is spared every blow for its first three seconds, and a fake player never counts them
         * down (it does not tick): no mob ever hurt the tester. Taken straight to its health, past that.
         */
        @Override
        public boolean hurt(DamageSource source, float amount) {
            if (amount <= 0 || !this.isAlive()) {
                return false;
            }
            // (run nfc 3) never to nothing: a fake player that falls stopped the server seven seconds into the check
            float before = this.getHealth();
            this.actuallyHurt(source, amount);
            if (this.getHealth() < 1F) {
                this.setHealth(Math.min(1F, before));
            }
            return true;
        }

        void ready() {
            this.attackStrengthTicker = 200;
        }
    }

    static final EfProbeCore.Hooks HOOKS = new EfProbeCore.Hooks() {
        @Override
        public Player tester(ServerLevel level, int n) {
            return new Tester(level, n);
        }

        @Override
        public void ready(Player p) {
            if (p instanceof Tester t) {
                t.ready();
            }
        }

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
