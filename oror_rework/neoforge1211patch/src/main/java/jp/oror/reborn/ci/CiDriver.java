package jp.oror.reborn.ci;

import java.util.ArrayList;
import java.util.List;
import jp.oror.reborn.citadel.CitadelEvents;
import jp.oror.reborn.vehicle.PilotTest;
import jp.oror.reborn.war.HundredWar;
import net.minecraft.server.MinecraftServer;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Dedicated-server checks for CI, started by the JVM property oror.ci (a comma list of citadel, war, pilots): once the
 * server has started, the checks run one after another (each when the one before has logged its result, so their
 * tick times are their own), and when every check has logged its result (or after twenty minutes of ticks) the server
 * stops. Without the property this does nothing.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class CiDriver {
    private static final Logger LOG = LoggerFactory.getLogger("OROR CI");
    private static final List<String> CHECKS = new ArrayList<>();
    private static long startedAt = -1;
    private static int next;

    private CiDriver() {
    }

    @SubscribeEvent
    public static void started(ServerStartedEvent e) {
        String p = System.getProperty("oror.ci", "");
        CHECKS.clear();
        for (String c : p.split(",")) {
            if (!c.isBlank()) {
                CHECKS.add(c.trim());
            }
        }
        startedAt = CHECKS.isEmpty() ? -1 : e.getServer().getTickCount();
        next = 0;
        if (startedAt >= 0) {
            LOG.info("CI checks: {}", CHECKS);
        }
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        if (startedAt < 0) {
            return;
        }
        MinecraftServer server = e.getServer();
        long t = server.getTickCount() - startedAt;
        if (next < CHECKS.size() && t >= 100 && (next == 0 || finished(CHECKS.get(next - 1)))) {
            String command = switch (CHECKS.get(next)) {
                case "citadel" -> "oror citadel selftest";
                case "citadelupdate" -> "oror citadel update test";
                case "war" -> "oror war start 100 test";
                case "pilots" -> "oror pilots test";
                case "landings" -> "oror pilots landings";
                case "arms" -> "oror arms test";
                case "guards" -> "oror guards test";
                case "worn" -> "oror worn test";
                case "spells" -> "oror spells test";
                case "mobs" -> "oror mobs test";
                case "gunmobs" -> "oror gunmobs test";
                case "story" -> "oror story test";
                case "waza" -> "oror waza test";
                case "relics" -> "oror relics test";
                case "capitalload" -> "oror capitalload test";
                case "sweep" -> "oror sweep";
                case "gametests" -> "oror gametests";
                case "aa" -> "oror aa test";
                case "villageflight" -> "oror villageflight test";
                default -> null;
            };
            if (command != null) {
                LOG.info("CI running /{}", command);
                server.getCommands().performPrefixedCommand(server.createCommandSourceStack(), command);
            }
            next++;
            return;
        }
        boolean done = next >= CHECKS.size() && CHECKS.stream().allMatch(CiDriver::finished);
        if (done || t > 64000) {
            LOG.info("CI-DONE {\"complete\":{},\"ticks\":{}}", done, t);
            startedAt = -1;
            server.halt(false);
        }
    }

    private static boolean finished(String check) {
        return switch (check) {
            case "citadel" -> CitadelEvents.selftestDone;
            case "citadelupdate" -> jp.oror.reborn.citadel.CitadelUpdate.testDone;
            case "war" -> HundredWar.resultLogged;
            case "pilots" -> PilotTest.resultLogged;
            case "landings" -> jp.oror.reborn.vehicle.LandingTest.resultLogged;
            case "arms" -> jp.oror.reborn.royal.KingslayerArms.Remake.testLogged;
            case "guards" -> GuardTest.resultLogged;
            case "worn" -> WornTest.resultLogged;
            case "spells" -> SpellSweep.resultLogged;
            case "mobs" -> MobTraceTest.resultLogged;
            case "gunmobs" -> GunMobTest.resultLogged;
            case "story" -> jp.oror.reborn.king.KingStoryTest.resultLogged;
            case "waza" -> jp.oror.reborn.waza.WazaTest.resultLogged;
            case "relics" -> jp.oror.reborn.relic.RelicTest.resultLogged;
            case "capitalload" -> jp.oror.reborn.citadel.CapitalLoadTest.resultLogged;
            case "sweep" -> OrorSweep.resultLogged;
            case "gametests" -> OrorGameTests.resultLogged;
            case "aa" -> jp.oror.reborn.vehicle.AntiAirTest.resultLogged;
            case "villageflight" -> jp.oror.reborn.VillageFlightTest.resultLogged;
            default -> true;
        };
    }
}
