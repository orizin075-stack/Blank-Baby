package jp.oror.reborn.ci;

import com.mojang.authlib.GameProfile;
import java.util.UUID;
import jp.oror.efprobe.EfProbeCore;
import net.minecraft.commands.Commands;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.player.Player;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/** (r64) /oror efprobe test: the Epic Fight check shared with the NightfallCraft run (jp.oror.efprobe.EfProbeCore), in OROR. */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class EfProbeTest {
    private EfProbeTest() {
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
            this.actuallyHurt(source, amount);
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
        @SuppressWarnings("deprecation")
        public void equip(ServerLevel level, Mob m) {
            m.finalizeSpawn(level, level.getCurrentDifficultyAt(m.blockPosition()), MobSpawnType.COMMAND, null);
        }
    };

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("efprobe").then(Commands.literal("test")
            .requires(s -> s.hasPermission(2)).executes(c -> {
                EfProbeCore.start(c.getSource().getServer().overworld(), "oror", HOOKS);
                return 1;
            }))));
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        EfProbeCore.tick();
    }
}
