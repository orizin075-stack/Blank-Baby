package jp.oror.reborn.ci;

import jp.oror.efprobe.EfProbeCore;
import net.minecraft.commands.Commands;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/** (r64) /oror efprobe test: the Epic Fight check shared with the NightfallCraft run (jp.oror.efprobe.EfProbeCore), in OROR. */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class EfProbeTest {
    private EfProbeTest() {
    }

    static final EfProbeCore.Hooks HOOKS = new EfProbeCore.Hooks() {
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
