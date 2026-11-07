package jp.oror.reborn.ci;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.gametest.framework.GameTestInfo;
import net.minecraft.gametest.framework.GameTestRegistry;
import net.minecraft.gametest.framework.GlobalTestReporter;
import net.minecraft.gametest.framework.TestFunction;
import net.minecraft.gametest.framework.TestReporter;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Rotation;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * /oror gametests (051, CI): the mod's own game tests, all of them (the other line wrote 119 in thirteen holders:
 * adventure, arsenal, civilization, compatibility, equipment, extension, fusion, mind, power, progression, reborn,
 * regression, relic), run on the dedicated server as /test runall would, 3000 blocks from spawn. Each result is logged as
 * GAMETEST with its error, and GAMETEST-RESULT sums them up once every test has reported (or nothing has come for five
 * minutes).
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class OrorGameTests {
    private static final Logger LOG = LoggerFactory.getLogger("OROR GameTest");
    public static volatile boolean resultLogged;
    private static final Map<String, String> RESULTS = new LinkedHashMap<>();
    private static int total = -1;
    private static long startedAt, lastAt;

    private OrorGameTests() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("gametests").requires(s -> s.hasPermission(2))
            .executes(c -> start(c.getSource()))));
    }

    private static int start(CommandSourceStack src) {
        if (total >= 0) {
            return 0;
        }
        // NeoForge registers game tests and ticks them only outside production (GameTestHooks), so on a release server
        // the holders are registered here, the runner built and started here, and the ticker ticked from tick() below
        StringBuilder notes = new StringBuilder();
        if (ValidationSupport.functions().isEmpty()) {
            for (String holder : HOLDERS) {
                try {
                    Class<?> c = Class.forName("jp.oror.reborn." + holder + "GameTests");
                    GameTestRegistry.class.getMethod("register", Class.class).invoke(null, c);
                } catch (Throwable ex) {
                    notes.append(holder).append(": ").append(ex).append("; ");
                }
            }
        }
        total = ValidationSupport.functions().size();
        startedAt = lastAt = src.getServer().getTickCount();
        LOG.info("GAMETEST-START {\"tests\":{},\"notes\":\"{}\"}", total, esc(notes.toString()));
        if (total == 0) {
            finish("no tests registered: " + notes);
            return 0;
        }
        GlobalTestReporter.replaceWith(new TestReporter() {
            @Override
            public void onTestFailed(GameTestInfo info) {
                record(info, false);
            }

            @Override
            public void onTestSuccess(GameTestInfo info) {
                record(info, true);
            }
        });
        try {
            startRunner(src.getServer().overworld(), BlockPos.containing(src.getPosition()).offset(0, 0, 3000));
            ticking = true;
        } catch (Throwable ex) {
            LOG.error("game test runner", ex);
            finish("the runner could not start: " + ex);
            return 0;
        }
        return 1;
    }

    private static final String[] HOLDERS = {"Adventure", "Arsenal", "Civilization", "Compatibility", "Equipment", "Extension", "Fusion",
        "Mind", "Power", "Progression", "Reborn", "Regression", "Relic"};
    private static boolean ticking;

    /** As /test runall does: every test laid out in a grid from at, and the runner started (by reflection: its API moves). */
    /** (053) The other line's runner (ValidationSupport, in the base jar): the same grid of tests, without the ones that
     * need TUKUYO running beside the server or a client (their names logged as GAMETEST-SKIP), its chunks let go after. */
    private static void startRunner(ServerLevel level, BlockPos at) throws ReflectiveOperationException {
        ValidationSupport.startRunner(level, at);
    }

    private static synchronized void record(GameTestInfo info, boolean ok) {
        String error = ok || info.getError() == null ? "" : info.getError().toString();
        RESULTS.put(info.getTestName(), ok ? "" : error);
        lastAt = net.neoforged.neoforge.server.ServerLifecycleHooks.getCurrentServer() == null ? lastAt
            : net.neoforged.neoforge.server.ServerLifecycleHooks.getCurrentServer().getTickCount();
        LOG.info(String.format(Locale.ROOT, "GAMETEST {\"test\":\"%s\",\"ok\":%b,\"required\":%b,\"error\":\"%s\"}", info.getTestName(), ok,
            info.isRequired(), esc(error)));
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        if (total <= 0 || resultLogged) {
            return;
        }
        int now = e.getServer().getTickCount();
        if (ticking) {
            try {
                net.minecraft.gametest.framework.GameTestTicker.SINGLETON.tick();
            } catch (Throwable ex) {
                LOG.error("game test tick", ex);
                ticking = false;
                finish("the ticker failed: " + ex);
                return;
            }
        }
        synchronized (OrorGameTests.class) {
            if (RESULTS.size() >= total) {
                finish("");
            } else if (now - lastAt > 6000) {
                finish("stalled: no result for five minutes");
            }
        }
    }

    private static void finish(String note) {
        int passed = (int) RESULTS.values().stream().filter(String::isEmpty).count();
        StringBuilder failed = new StringBuilder();
        RESULTS.forEach((name, error) -> {
            if (!error.isEmpty()) {
                failed.append(failed.length() > 0 ? "," : "").append("\"").append(name).append("\"");
            }
        });
        LOG.info(String.format(Locale.ROOT, "GAMETEST-RESULT {\"tests\":%d,\"reported\":%d,\"passed\":%d,\"failed\":%d,\"failedTests\":[%s],"
            + "\"note\":\"%s\"}", Math.max(total, 0), RESULTS.size(), passed, RESULTS.size() - passed, failed, esc(note)));
        resultLogged = true;
    }

    private static String esc(String s) {
        return s == null ? "" : s.replace("\\", "/").replace("\"", "'").replace("\n", " ");
    }
}
