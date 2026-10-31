package jp.oror.look;

import com.mojang.logging.LogUtils;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.components.AbstractButton;
import net.minecraft.client.gui.components.events.GuiEventListener;
import net.minecraft.client.gui.screens.GenericMessageScreen;
import net.minecraft.client.gui.screens.LevelLoadingScreen;
import net.minecraft.client.gui.screens.ProgressScreen;
import net.minecraft.client.gui.screens.ReceivingLevelScreen;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.client.gui.screens.worldselection.CreateWorldScreen;
import net.minecraft.client.server.IntegratedServer;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.contents.TranslatableContents;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.AABB;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.common.NeoForge;
import org.slf4j.Logger;

/**
 * CI only, never shipped: in a fresh world, a stage in the sky with the eight royals in a row and armed villagers and a
 * wandering trader in another, photographed standing and mid-swing, close up and from behind; then the throne room of
 * the capital with the Villager King on his throne. Screenshots go to screenshots/, notes to look/result.txt.
 */
@Mod(value = "oror_look", dist = Dist.CLIENT)
public final class Look {
    private static final Logger LOG = LogUtils.getLogger();
    private static final Set<String> PROCEED = Set.of("gui.proceed", "gui.continue", "gui.done", "gui.ok", "gui.yes", "gui.acknowledge",
        "selectWorld.backupJoinSkipButton");
    private static final String[] ROYALS = {"villager_king", "villager_general", "imperial_guard", "royal_bodyguard", "kingdom_guard",
        "royal_mage", "royal_archmage", "royal_sage"};
    private static final int LIMIT = 48000;

    private enum Phase { TITLE, CREATE, LOADING, PLAY, DONE }

    private static Phase phase = Phase.TITLE;
    private static Screen seen;
    private static int onScreen, total, play;
    private static double sx, sy, sz;
    private static final List<String> log = Collections.synchronizedList(new ArrayList<>());

    public Look() {
        NeoForge.EVENT_BUS.addListener((ClientTickEvent.Post event) -> {
            try {
                tick(Minecraft.getInstance());
            } catch (Throwable error) {
                note("tick failed: " + error);
                LOG.error("[look] tick failed", error);
            }
        });
    }

    private static void tick(Minecraft mc) {
        if (phase == Phase.DONE) {
            return;
        }
        if (++total == LIMIT) {
            shot(mc, "99_timeout_" + phase);
            finish(mc, "timeout in " + phase);
            return;
        }
        if (mc.getOverlay() != null) {
            return;
        }
        Screen screen = mc.screen;
        if (screen != seen) {
            seen = screen;
            onScreen = 0;
            note("screen " + (screen == null ? "none" : screen.getClass().getName()) + " in " + phase);
        } else {
            onScreen++;
        }
        switch (phase) {
            case TITLE -> {
                if (screen instanceof TitleScreen && onScreen == 100) {
                    phase = Phase.CREATE;
                    CreateWorldScreen.openFresh(mc, screen);
                } else if (screen != null && !(screen instanceof TitleScreen)) {
                    popup(mc, screen);
                }
            }
            case CREATE -> {
                if (screen instanceof CreateWorldScreen) {
                    if (onScreen == 60 && !press(screen, Set.of("selectWorld.create"))) {
                        note("no create button");
                    }
                } else if (loading(screen)) {
                    phase = Phase.LOADING;
                } else if (screen == null && mc.level != null) {
                    phase = Phase.PLAY;
                } else if (screen != null) {
                    popup(mc, screen);
                }
            }
            case LOADING -> {
                if (mc.level != null && mc.player != null && screen == null) {
                    phase = Phase.PLAY;
                } else if (screen != null && !loading(screen)) {
                    popup(mc, screen);
                }
            }
            case PLAY -> {
                if (screen != null) {
                    popup(mc, screen);
                    return;
                }
                if (mc.player != null && mc.level != null) {
                    play(mc, ++play);
                }
            }
            default -> {
            }
        }
    }

    private static void play(Minecraft mc, int t) {
        switch (t) {
            case 2 -> {
                IntegratedServer server = mc.getSingleplayerServer();
                String name = mc.player.getGameProfile().getName();
                if (server != null) {
                    server.execute(() -> {
                        command(server, "gamemode creative " + name);
                        command(server, "effect give " + name + " minecraft:resistance infinite 4 true");
                    });
                }
            }
            case 40 -> stage(mc);
            case 200 -> {
                mc.options.hideGui = true;
                renderers(mc);
                view(mc, 0, 0, 0, 0F, 8F);
            }
            case 260 -> shot(mc, "10_royals");
            case 270 -> swing(mc, 0);
            case 273 -> shot(mc, "11_royals_swing");
            case 300 -> view(mc, 0, 0, 10, 0F, 8F);
            case 360 -> shot(mc, "12_villagers");
            case 370 -> swing(mc, 10);
            case 373 -> shot(mc, "13_villagers_swing");
            case 380 -> swing(mc, 10);
            case 382 -> shot(mc, "13b_villagers_swing_early");
            case 400 -> view(mc, -7, 0, 3, 0F, 4F);
            case 460 -> shot(mc, "14_king_close");
            case 470 -> view(mc, -5, 0, 3, 0F, 4F);
            case 530 -> shot(mc, "15_general_close");
            case 540 -> view(mc, -3, 0, 3, 0F, 4F);
            case 600 -> shot(mc, "16_imperial_close");
            case 610 -> view(mc, -5, 0, 10, 180F, 4F);
            case 670 -> shot(mc, "17_royals_back");
            case 680 -> view(mc, 3, 0, 13, 0F, 4F);
            case 740 -> shot(mc, "18_trader_close");
            case 760 -> throne(mc);
            case 2560 -> shot(mc, "20_throne_room");
            case 2600 -> king(mc);
            case 4400 -> shot(mc, "21_throne_room_later");
            case 4420 -> {
                king(mc);
                overCapital(mc, 0, 0, 150);
            }
            case 6200 -> shot(mc, "22_capital_aerial");
            case 6210 -> overCapital(mc, -265, -239, 40);
            case 7800 -> shot(mc, "23_helipad");
            case 7810 -> overCapital(mc, -250, -377, 45);
            case 9400 -> shot(mc, "24_airbase");
            // 048: the posts' supply, a helipad's power plant and depot, and a hangar's bays with theirs
            case 9410 -> atCapital(mc, -265, 10, -250, 0F, 48F);
            case 11000 -> shot(mc, "25_helipad_supply");
            case 11010 -> atCapital(mc, -389, 3, -160, 90F, 10F);
            case 12600 -> shot(mc, "26_hangar_supply");
            // the palace's roofs from the south-east, high up (the two light wells roofed over in 048)
            case 12610 -> atCapital(mc, 70, 115, 110, 150F, 32F);
            case 14200 -> shot(mc, "27_palace_roofs");
            case 14210 -> finish(mc, "complete");
            default -> {
            }
        }
    }

    private static void command(IntegratedServer server, String command) {
        server.getCommands().performPrefixedCommand(server.createCommandSourceStack().withSuppressedOutput(), command);
    }

    /** A white stage 40 blocks up, the royals on its back row and the villagers and trader on the front row. */
    private static void stage(Minecraft mc) {
        IntegratedServer server = mc.getSingleplayerServer();
        if (server == null) {
            return;
        }
        String name = mc.player.getGameProfile().getName();
        sx = Math.floor(mc.player.getX()) + 0.5;
        sy = Math.floor(mc.player.getY()) + 40;
        sz = Math.floor(mc.player.getZ()) + 0.5;
        server.execute(() -> {
            for (String c : new String[]{"gamemode creative " + name, "time set 6000", "weather clear 100000", "gamerule doDaylightCycle false",
                "gamerule doWeatherCycle false", "gamerule doMobSpawning false", "effect give " + name + " minecraft:night_vision infinite 0 true"}) {
                command(server, c);
            }
            int x = (int) Math.floor(sx), y = (int) sy - 1, z = (int) Math.floor(sz);
            command(server, String.format("fill %d %d %d %d %d %d minecraft:white_concrete", x - 14, y, z - 4, x + 14, y, z + 22));
            command(server, String.format("fill %d %d %d %d %d %d minecraft:air", x - 14, y + 1, z - 4, x + 14, y + 8, z + 22));
            // the royals, z + 6, facing north toward the camera
            for (int i = 0; i < ROYALS.length; i++) {
                command(server, String.format(java.util.Locale.ROOT,
                    "summon oror_supreme_bosses:%s %.1f %d %.1f {NoAI:1b,PersistenceRequired:1b,Rotation:[180f,0f],Tags:[\"oror_look\"]}",
                    ROYALS[i], sx - 7 + i * 2, y + 1, sz + 6));
            }
            // the villagers and the trader, z + 16
            String[] people = {"villager", "villager", "villager", "villager", "wandering_trader", "wandering_trader"};
            String[] hands = {"minecraft:iron_sword", "minecraft:iron_axe", "minecraft:bow", "", "minecraft:iron_sword", ""};
            String[] professions = {"weaponsmith", "farmer", "fletcher", "librarian", "", ""};
            for (int i = 0; i < people.length; i++) {
                String data = "NoAI:1b,PersistenceRequired:1b,Rotation:[180f,0f],Tags:[\"oror_look\"]"
                    + (hands[i].isEmpty() ? "" : ",HandItems:[{id:\"" + hands[i] + "\",count:1},{}]")
                    + (professions[i].isEmpty() ? "" : ",VillagerData:{profession:\"minecraft:" + professions[i] + "\",level:2,type:\"minecraft:plains\"}");
                command(server, String.format(java.util.Locale.ROOT, "summon minecraft:%s %.1f %d %.1f {%s}", people[i], sx - 5 + i * 2, y + 1, sz + 16, data));
            }
            note("stage at " + x + " " + y + " " + z);
        });
    }

    /** The camera (the player, flying) at the stage's origin plus dx, dy, dz, turned to yaw, a little above the floor. */
    private static void view(Minecraft mc, double dx, double dy, double dz, float yaw, float pitch) {
        IntegratedServer server = mc.getSingleplayerServer();
        String name = mc.player.getGameProfile().getName();
        mc.player.getAbilities().flying = true;
        server.execute(() -> command(server, String.format(java.util.Locale.ROOT, "tp %s %.2f %.2f %.2f %.1f %.1f", name, sx + dx, sy + 0.2 + dy, sz + dz, yaw, pitch)));
    }

    /** Every entity of the row (the royals' row at z + 6 when row is 0, the villagers' at z + 16) swings its main hand. */
    private static void swing(Minecraft mc, int row) {
        IntegratedServer server = mc.getSingleplayerServer();
        server.execute(() -> {
            ServerLevel level = server.overworld();
            double z = sz + (row == 0 ? 6 : 16);
            int n = 0;
            for (Entity e : level.getEntities((Entity) null, new AABB(sx - 15, sy - 2, z - 1.5, sx + 15, sy + 4, z + 1.5),
                x -> x.getTags().contains("oror_look"))) {
                if (e instanceof LivingEntity l) {
                    l.swing(InteractionHand.MAIN_HAND, true);
                    n++;
                }
            }
            note("swing row " + row + ": " + n);
        });
    }

    private static void renderers(Minecraft mc) {
        List<String> lines = new ArrayList<>();
        for (Entity e : mc.level.entitiesForRendering()) {
            if (e.getTags().contains("oror_look") || e instanceof LivingEntity && e.distanceToSqr(mc.player) < 900) {
                lines.add(net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()) + " -> "
                    + mc.getEntityRenderDispatcher().getRenderer(e).getClass().getName()
                    + (e instanceof LivingEntity l ? " holding " + l.getMainHandItem() : ""));
            }
        }
        note("renderers: " + lines);
    }

    /** To the capital's throne room (CitadelSites.capital() by reflection): the camera seven blocks in front of the throne. */
    private static void throne(Minecraft mc) {
        IntegratedServer server = mc.getSingleplayerServer();
        String name = mc.player.getGameProfile().getName();
        server.execute(() -> {
            try {
                Class<?> sites = Class.forName("jp.oror.reborn.citadel.CitadelSites");
                Object site = sites.getMethod("capital").invoke(null);
                if (site == null) {
                    note("no capital");
                    return;
                }
                Method throne = site.getClass().getMethod("throne");
                throne.setAccessible(true);
                BlockPos t = (BlockPos) throne.invoke(site);
                note("throne " + t.toShortString());
                command(server, String.format("tp %s %d %d %d 180 10", name, t.getX(), t.getY() + 1, t.getZ() + 8));
                command(server, "gamemode spectator " + name);
            } catch (Throwable error) {
                note("throne lookup failed: " + error);
            }
        });
    }

    /**
     * Above the natural capital: dx, dz from its centre (the save's origin), height blocks over its ground, looking down
     * at 60 degrees toward the south. Shows whether the outer belt (runways, helipads) is open sky.
     */
    private static void overCapital(Minecraft mc, int dx, int dz, int height) {
        IntegratedServer server = mc.getSingleplayerServer();
        String name = mc.player.getGameProfile().getName();
        server.execute(() -> {
            try {
                Class<?> sites = Class.forName("jp.oror.reborn.citadel.CitadelSites");
                Object site = sites.getMethod("capital").invoke(null);
                Method center = site.getClass().getMethod("center");
                center.setAccessible(true);
                BlockPos c = (BlockPos) center.invoke(site);
                command(server, String.format("tp %s %d %d %d 0 60", name, c.getX() + dx, c.getY() + height, c.getZ() + dz - height / 2));
                note("over the capital at " + (c.getX() + dx) + " " + (c.getZ() + dz));
            } catch (Throwable error) {
                note("capital lookup failed: " + error);
            }
        });
    }

    /** At dx, dy, dz from the natural capital's centre (the save's origin, at its ground level), facing yaw, pitch. */
    private static void atCapital(Minecraft mc, int dx, int dy, int dz, float yaw, float pitch) {
        IntegratedServer server = mc.getSingleplayerServer();
        String name = mc.player.getGameProfile().getName();
        server.execute(() -> {
            try {
                Class<?> sites = Class.forName("jp.oror.reborn.citadel.CitadelSites");
                Object site = sites.getMethod("capital").invoke(null);
                Method center = site.getClass().getMethod("center");
                center.setAccessible(true);
                BlockPos c = (BlockPos) center.invoke(site);
                command(server, String.format(java.util.Locale.ROOT, "tp %s %d %d %d %.1f %.1f", name, c.getX() + dx, c.getY() + dy, c.getZ() + dz, yaw, pitch));
                note("at the capital " + (c.getX() + dx) + " " + (c.getY() + dy) + " " + (c.getZ() + dz));
            } catch (Throwable error) {
                note("capital lookup failed: " + error);
            }
        });
    }

    /** Where the king is against his throne, from the server. */
    private static void king(Minecraft mc) {
        IntegratedServer server = mc.getSingleplayerServer();
        server.execute(() -> {
            try {
                Class<?> sites = Class.forName("jp.oror.reborn.citadel.CitadelSites");
                Object site = sites.getMethod("capital").invoke(null);
                Method throne = site.getClass().getMethod("throne");
                throne.setAccessible(true);
                BlockPos t = (BlockPos) throne.invoke(site);
                ServerLevel level = server.overworld();
                List<String> found = new ArrayList<>();
                for (Entity e : level.getEntities((Entity) null, new AABB(t).inflate(30), x -> x.getType().toString().contains("villager_king"))) {
                    found.add(String.format(java.util.Locale.ROOT, "king at %.1f %.1f %.1f (throne %s, %.2f blocks)", e.getX(), e.getY(), e.getZ(),
                        t.toShortString(), Math.sqrt(e.distanceToSqr(t.getX() + 0.5, t.getY(), t.getZ() + 0.5))));
                }
                note(found.isEmpty() ? "no king within 30 blocks of the throne" : String.join("; ", found));
            } catch (Throwable error) {
                note("king lookup failed: " + error);
            }
        });
    }

    private static boolean loading(Screen screen) {
        return screen instanceof LevelLoadingScreen || screen instanceof ReceivingLevelScreen || screen instanceof GenericMessageScreen
            || screen instanceof ProgressScreen;
    }

    private static void popup(Minecraft mc, Screen screen) {
        if (screen instanceof net.minecraft.client.gui.screens.DeathScreen && onScreen == 20) {
            // why: the death message is one of the screen's components
            for (java.lang.reflect.Field f : screen.getClass().getDeclaredFields()) {
                if (net.minecraft.network.chat.Component.class.isAssignableFrom(f.getType())) {
                    try {
                        f.setAccessible(true);
                        Object c = f.get(screen);
                        note("death: " + (c instanceof net.minecraft.network.chat.Component comp ? comp.getString() : c));
                    } catch (Exception e) {
                        note("death message unreadable: " + e);
                    }
                }
            }
            shot(mc, "death_" + total);
            if (mc.player != null) {
                mc.player.respawn();
            }
            mc.setScreen(null);
            return;
        }
        if (onScreen == 100) {
            shot(mc, "popup_" + screen.getClass().getSimpleName());
            if (!press(screen, PROCEED)) {
                screen.onClose();
            }
        } else if (onScreen == 160) {
            mc.setScreen(null);
        }
    }

    private static boolean press(Screen screen, Set<String> keys) {
        for (GuiEventListener child : screen.children()) {
            if (child instanceof AbstractButton button && button.active && button.getMessage().getContents() instanceof TranslatableContents text
                && keys.contains(text.getKey())) {
                note("press " + text.getKey());
                button.onPress();
                return true;
            }
        }
        return false;
    }

    private static void shot(Minecraft mc, String name) {
        note("screenshot " + name);
        Screenshot.grab(mc.gameDirectory, name + ".png", mc.getMainRenderTarget(), message -> {
        });
    }

    private static void finish(Minecraft mc, String result) {
        phase = Phase.DONE;
        note("finished: " + result);
        try {
            Path dir = mc.gameDirectory.toPath().resolve("look");
            Files.createDirectories(dir);
            synchronized (log) {
                Files.write(dir.resolve("result.txt"), new ArrayList<>(log), StandardCharsets.UTF_8);
            }
        } catch (Exception error) {
            LOG.error("[look] cannot write the result", error);
        }
        mc.stop();
    }

    private static void note(String line) {
        log.add(total + " " + line);
        LOG.info("[look] {}", line);
    }
}
