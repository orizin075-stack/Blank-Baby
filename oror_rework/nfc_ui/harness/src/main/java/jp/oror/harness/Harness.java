package jp.oror.harness;

import com.mojang.blaze3d.platform.GlUtil;
import com.mojang.logging.LogUtils;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import net.minecraft.client.CameraType;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.components.AbstractButton;
import net.minecraft.client.gui.components.AbstractWidget;
import net.minecraft.client.gui.components.events.GuiEventListener;
import net.minecraft.client.gui.screens.GenericMessageScreen;
import net.minecraft.client.gui.screens.LevelLoadingScreen;
import net.minecraft.client.gui.screens.PauseScreen;
import net.minecraft.client.gui.screens.ProgressScreen;
import net.minecraft.client.gui.screens.ReceivingLevelScreen;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.client.gui.screens.options.OptionsScreen;
import net.minecraft.client.gui.screens.worldselection.CreateWorldScreen;
import net.minecraft.client.server.IntegratedServer;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.contents.TranslatableContents;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.fml.ModList;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.common.NeoForge;
import org.slf4j.Logger;

/**
 * CI only, never shipped: drives a fresh client through the title screen, world creation and a short stay in game,
 * saving screenshots to screenshots/ and what it saw to harness/, then quits. Any other screen that stays up is
 * photographed as a popup and closed.
 */
@Mod(value = "oror_harness", dist = Dist.CLIENT)
public final class Harness {
    private static final Logger LOG = LogUtils.getLogger();
    private static final Set<String> PROCEED = Set.of("gui.proceed", "gui.continue", "gui.done", "gui.ok", "gui.yes",
            "gui.acknowledge", "selectWorld.backupJoinSkipButton");
    private static final String[] WEAPONS = {"efn:hf_murasama", "efn:yamato_dmc", "efn:excalibur", "epicfight:iron_longsword",
            "epicfight:iron_tachi", "minecraft:iron_sword"};
    private static final int LIMIT = 36000;

    private enum Phase { TITLE, CREATE, LOADING, PLAY, DONE }

    private static Phase phase = Phase.TITLE;
    private static Screen seen;
    private static int onScreen, overlayTicks, total, play, popups;
    private static boolean optionsShown;
    private static Class<? extends Screen> expected;
    private static final List<String> log = Collections.synchronizedList(new ArrayList<>());

    public Harness() {
        NeoForge.EVENT_BUS.addListener((ClientTickEvent.Post event) -> {
            try {
                tick(Minecraft.getInstance());
            } catch (Throwable error) {
                note("tick failed: " + error);
                LOG.error("[harness] tick failed", error);
            }
        });
    }

    private static void tick(Minecraft mc) {
        if (phase == Phase.DONE) return;
        if (++total == LIMIT) {
            shot(mc, "99_timeout_" + phase);
            finish(mc, "timeout in " + phase);
            return;
        }
        if (mc.getOverlay() != null) {
            if (++overlayTicks == 300) shot(mc, "00_loading_overlay");
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
            case TITLE -> title(mc, screen);
            case CREATE -> create(mc, screen);
            case LOADING -> loading(mc, screen);
            case PLAY -> play(mc, screen);
            default -> { }
        }
    }

    private static void title(Minecraft mc, Screen screen) {
        if (screen instanceof TitleScreen) {
            if (onScreen == 200) {
                shot(mc, "01_title");
                info(mc);
                widgets(mc, screen, "title-widgets.txt");
            } else if (onScreen == 220 && !optionsShown) {
                optionsShown = true;
                mc.setScreen(new OptionsScreen(screen, mc.options));
            } else if (onScreen == 220) {
                phase = Phase.CREATE;
                CreateWorldScreen.openFresh(mc, screen);
            }
        } else if (screen instanceof OptionsScreen) {
            if (onScreen == 60) shot(mc, "01b_options");
            else if (onScreen == 70) screen.onClose();
        } else if (screen != null) {
            popup(mc, screen);
        }
    }

    private static void create(Minecraft mc, Screen screen) {
        if (screen instanceof CreateWorldScreen) {
            if (onScreen == 60) shot(mc, "02_create_world");
            else if (onScreen == 70 && !press(screen, Set.of("selectWorld.create"))) note("no create button");
        } else if (loadingScreen(screen)) {
            phase = Phase.LOADING;
        } else if (screen == null && mc.level != null) {
            phase = Phase.PLAY;
        } else if (screen instanceof TitleScreen && onScreen == 100) {
            shot(mc, "02_back_to_title");
            finish(mc, "world creation did not start");
        } else if (screen != null) {
            popup(mc, screen);
        }
    }

    private static void loading(Minecraft mc, Screen screen) {
        if (screen instanceof LevelLoadingScreen && onScreen == 40) shot(mc, "03_level_loading");
        if (mc.level != null && mc.player != null && screen == null) phase = Phase.PLAY;
        else if (screen != null && !loadingScreen(screen)) popup(mc, screen);
    }

    private static boolean loadingScreen(Screen screen) {
        return screen instanceof LevelLoadingScreen || screen instanceof ReceivingLevelScreen
                || screen instanceof GenericMessageScreen || screen instanceof ProgressScreen;
    }

    private static void play(Minecraft mc, Screen screen) {
        if (mc.player == null || mc.level == null) return;
        if (screen != null && (expected == null || !expected.isInstance(screen))) {
            popup(mc, screen);
            return;
        }
        switch (++play) {
            case 20 -> equip(mc);
            case 400 -> shot(mc, "04_hud_weapon");
            case 410 -> mc.player.getInventory().selected = 8;
            case 500 -> shot(mc, "05_hud_tool");
            case 510 -> {
                mc.player.getInventory().selected = 0;
                expected = InventoryScreen.class;
                mc.setScreen(new InventoryScreen(mc.player));
            }
            case 580 -> shot(mc, "06_inventory");
            case 590 -> {
                expected = PauseScreen.class;
                mc.setScreen(null);
                mc.pauseGame(false);
            }
            case 650 -> shot(mc, "07_pause");
            case 660 -> {
                expected = null;
                mc.setScreen(null);
            }
            case 760 -> shot(mc, "08_hud_weapon_again");
            case 770 -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK);
            case 860 -> shot(mc, "09_third_person");
            case 880 -> finish(mc, "complete");
            default -> { }
        }
    }

    /** Gives the player a NightfallCraft-like loadout and a still target in front, on the integrated server. */
    private static void equip(Minecraft mc) {
        IntegratedServer server = mc.getSingleplayerServer();
        if (server == null) return;
        UUID id = mc.player.getUUID();
        String name = mc.player.getGameProfile().getName();
        server.execute(() -> {
            ServerPlayer player = server.getPlayerList().getPlayer(id);
            if (player == null) return;
            String weapon = "minecraft:iron_sword";
            for (String candidate : WEAPONS) {
                if (item(candidate).isPresent()) { weapon = candidate; break; }
            }
            note("weapon " + weapon);
            String[] hotbar = {weapon, "minecraft:bow", "minecraft:crossbow", "minecraft:golden_apple", "minecraft:torch",
                    "minecraft:cooked_beef", "minecraft:oak_planks", "minecraft:water_bucket", "minecraft:iron_pickaxe"};
            int[] counts = {1, 1, 1, 3, 32, 16, 64, 1, 1};
            for (int slot = 0; slot < hotbar.length; slot++) {
                final int s = slot;
                item(hotbar[slot]).ifPresent(i -> player.getInventory().setItem(s, new ItemStack(i, counts[s])));
            }
            item("minecraft:shield").ifPresent(i -> player.setItemSlot(EquipmentSlot.OFFHAND, new ItemStack(i)));
            item("minecraft:iron_helmet").ifPresent(i -> player.setItemSlot(EquipmentSlot.HEAD, new ItemStack(i)));
            item("minecraft:iron_chestplate").ifPresent(i -> player.setItemSlot(EquipmentSlot.CHEST, new ItemStack(i)));
            item("minecraft:iron_leggings").ifPresent(i -> player.setItemSlot(EquipmentSlot.LEGS, new ItemStack(i)));
            item("minecraft:iron_boots").ifPresent(i -> player.setItemSlot(EquipmentSlot.FEET, new ItemStack(i)));
            player.giveExperienceLevels(12);
            player.setHealth(player.getMaxHealth() * 0.7F);
            player.getFoodData().setFoodLevel(15);
            for (String command : new String[]{"time set 6000", "weather clear 100000", "gamerule doDaylightCycle false",
                    "gamerule doWeatherCycle false", "gamerule doMobSpawning false",
                    "execute as " + name + " at @s run summon minecraft:zombie ^ ^ ^5 {NoAI:1b,PersistenceRequired:1b}"}) {
                server.getCommands().performPrefixedCommand(server.createCommandSourceStack(), command);
            }
        });
        mc.player.getInventory().selected = 0;
    }

    private static Optional<Item> item(String id) {
        ResourceLocation key = ResourceLocation.tryParse(id);
        return key == null ? Optional.empty() : BuiltInRegistries.ITEM.getOptional(key);
    }

    private static void popup(Minecraft mc, Screen screen) {
        if (onScreen == 100) {
            shot(mc, "popup_" + (++popups) + "_" + screen.getClass().getSimpleName());
            if (!press(screen, PROCEED)) screen.onClose();
        } else if (onScreen == 160) {
            note("popup still open, replacing it: " + screen.getClass().getName());
            mc.setScreen(null);
        }
    }

    private static boolean press(Screen screen, Set<String> keys) {
        for (GuiEventListener child : screen.children()) {
            if (child instanceof AbstractButton button && button.active
                    && button.getMessage().getContents() instanceof TranslatableContents text && keys.contains(text.getKey())) {
                note("press " + text.getKey() + " on " + screen.getClass().getSimpleName());
                button.onPress();
                return true;
            }
        }
        return false;
    }

    private static void shot(Minecraft mc, String name) {
        note("screenshot " + name);
        Screenshot.grab(mc.gameDirectory, name + ".png", mc.getMainRenderTarget(), message -> { });
    }

    private static void info(Minecraft mc) {
        List<String> lines = new ArrayList<>();
        lines.add("gl " + GlUtil.getVendor() + " | " + GlUtil.getRenderer() + " | " + GlUtil.getOpenGLVersion());
        lines.add("window " + mc.getWindow().getWidth() + "x" + mc.getWindow().getHeight() + " gui scale " + mc.getWindow().getGuiScale());
        lines.add("selected packs " + mc.getResourcePackRepository().getSelectedIds());
        lines.add("available packs " + mc.getResourcePackRepository().getAvailableIds());
        for (KeyMapping key : mc.options.keyMappings) {
            lines.add("key " + key.getName() + " default=" + key.getDefaultKey().getName() + " now=" + key.saveString()
                    + " category=" + key.getCategory());
        }
        ModList.get().getMods().forEach(mod -> lines.add("mod " + mod.getModId() + " " + mod.getVersion()));
        write(mc, "info.txt", lines);
    }

    private static void finish(Minecraft mc, String result) {
        phase = Phase.DONE;
        note("finished: " + result);
        synchronized (log) {
            write(mc, "result.txt", new ArrayList<>(log));
        }
        mc.stop();
    }

    /** Every widget of a screen: class, label (translation key when it has one), position and size, for layout ids. */
    private static void widgets(Minecraft mc, Screen screen, String name) {
        List<String> lines = new ArrayList<>();
        lines.add("screen " + screen.width + "x" + screen.height);
        for (GuiEventListener child : screen.children()) {
            if (child instanceof AbstractWidget widget) {
                Object label = widget.getMessage().getContents() instanceof TranslatableContents text ? text.getKey() : widget.getMessage().getString();
                lines.add(widget.getClass().getName() + " '" + label + "' at " + widget.getX() + "," + widget.getY() + " size "
                        + widget.getWidth() + "x" + widget.getHeight() + (widget.visible ? "" : " hidden"));
            } else {
                lines.add(child.getClass().getName());
            }
        }
        // The identifiers FancyMenu's layouts address these widgets by (it computes them on a 1000x1000 pass).
        try {
            Class<?> discoverer = Class.forName("de.keksuccino.fancymenu.customization.widget.ScreenWidgetDiscoverer");
            for (Object meta : (List<?>) discoverer.getMethod("getWidgetsOfScreen", Screen.class).invoke(null, screen)) {
                Class<?> type = meta.getClass();
                AbstractWidget widget = (AbstractWidget) type.getMethod("getWidget").invoke(meta);
                Object label = widget.getMessage().getContents() instanceof TranslatableContents text ? text.getKey() : widget.getMessage().getString();
                lines.add("fancymenu id " + type.getMethod("getLongIdentifier").invoke(meta) + " universal "
                        + type.getMethod("getUniversalIdentifier").invoke(meta) + " " + widget.getClass().getSimpleName() + " '" + label + "'");
            }
        } catch (Throwable error) {
            lines.add("fancymenu ids unavailable: " + error);
        }
        write(mc, name, lines);
    }

    private static void note(String line) {
        log.add(total + " " + line);
        LOG.info("[harness] {}", line);
    }

    private static void write(Minecraft mc, String name, List<String> lines) {
        try {
            Path dir = mc.gameDirectory.toPath().resolve("harness");
            Files.createDirectories(dir);
            Files.write(dir.resolve(name), lines, StandardCharsets.UTF_8);
        } catch (Exception error) {
            LOG.error("[harness] cannot write {}", name, error);
        }
    }
}
