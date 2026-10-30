package jp.oror.reborn.compat;

import java.awt.image.BufferedImage;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.Optional;
import javax.imageio.ImageIO;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.GenericMessageScreen;
import net.minecraft.client.gui.screens.LevelLoadingScreen;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.packs.PackLocationInfo;
import net.minecraft.server.packs.PackSelectionConfig;
import net.minecraft.server.packs.PackType;
import net.minecraft.server.packs.PathPackResources;
import net.minecraft.server.packs.repository.Pack;
import net.minecraft.server.packs.repository.PackSource;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.loading.FMLPaths;
import net.neoforged.neoforge.client.event.ScreenEvent;
import net.neoforged.neoforge.event.AddPackFindersEvent;

/**
 * 0.17.25: NightfallCraft's menus. NightfallCraft's TCR Core (1.20.1 only) replaced the widget sheet (buttons), the
 * screen tabs and header/footer separators, and drew its blurred cover image where menus had the dirt background.
 * SETUP_NIGHTFALL.cmd copies those images from the TCR Core jar to config/fancymenu/assets/nightfallcraft; from them
 * this builds an always-on resource pack in the 1.21.1 sprite layout, and draws the cover behind menus opened outside
 * a world. Without the images (setup not run) nothing changes.
 */
public final class NightfallCraftGui {
    private static final String PACK_ID = "oror_nightfall_gui";
    private static final ResourceLocation COVER = ResourceLocation.fromNamespaceAndPath(PACK_ID, "textures/menu/background_blurred.png");
    private static final String BUTTON_SCALING = "{\"gui\":{\"scaling\":{\"type\":\"nine_slice\",\"width\":200,\"height\":20,"
        + "\"border\":{\"left\":20,\"top\":4,\"right\":20,\"bottom\":4}}}}";
    private static final String TAB_SCALING = "{\"gui\":{\"scaling\":{\"type\":\"nine_slice\",\"width\":130,\"height\":24,"
        + "\"border\":{\"left\":2,\"top\":2,\"right\":2,\"bottom\":0}}}}";
    /** 1.21.1 sprite -> rectangle of the 1.20.1 widget sheet (256x256: disabled, normal and hovered buttons). */
    private static final Map<String, int[]> BUTTONS = Map.of(
        "widget/button_disabled", new int[]{0, 46, 200, 20},
        "widget/button", new int[]{0, 66, 200, 20},
        "widget/button_highlighted", new int[]{0, 86, 200, 20});
    private static final Map<String, String> TABS = Map.of(
        "widget/tab", "gui/tab/tab.png",
        "widget/tab_highlighted", "gui/tab/tab_highlighted.png",
        "widget/tab_selected", "gui/tab/tab_selected.png",
        "widget/tab_selected_highlighted", "gui/tab/tab_selected_highlighted.png");
    private static volatile boolean cover;

    @EventBusSubscriber(modid = "oror_supreme_bosses", value = Dist.CLIENT, bus = EventBusSubscriber.Bus.MOD)
    public static final class Packs {
        @SubscribeEvent
        public static void addPack(AddPackFindersEvent event) {
            if (event.getPackType() != PackType.CLIENT_RESOURCES) {
                return;
            }
            cover = false;
            if (!NightfallMenuAssets.reload()) return;
            Path source = FMLPaths.CONFIGDIR.get().resolve("fancymenu/assets/nightfallcraft");
            if (!Files.isRegularFile(source.resolve("minecraft/gui/widgets.png"))) {
                return;
            }
            Path pack = FMLPaths.GAMEDIR.get().resolve("oror-generated/" + PACK_ID);
            try {
                build(source, pack);
            } catch (IOException | RuntimeException error) {
                System.err.println("[OROR] NightfallCraft GUI pack not built: " + error);
                return;
            }
            PackLocationInfo info = new PackLocationInfo(PACK_ID, Component.literal("NightfallCraft GUI (TCR Core)"),
                PackSource.BUILT_IN, Optional.empty());
            Pack built = Pack.readMetaAndCreate(info, new PathPackResources.PathResourcesSupplier(pack), PackType.CLIENT_RESOURCES,
                new PackSelectionConfig(true, Pack.Position.TOP, false));
            if (built != null) {
                event.addRepositorySource(consumer -> consumer.accept(built));
                cover = Files.isRegularFile(pack.resolve("assets/" + PACK_ID + "/textures/menu/background_blurred.png"));
            }
        }

        private Packs() {
        }
    }

    @EventBusSubscriber(modid = "oror_supreme_bosses", value = Dist.CLIENT)
    public static final class Background {
        /**
         * TCR Core drew its cover where 1.20.1 menus had dirt, i.e. outside a world; in a world 1.21.1 is unchanged.
         * The title, loading and message screens keep NightfallCraft's FancyMenu layouts' own backgrounds.
         */
        @SubscribeEvent
        public static void background(ScreenEvent.BackgroundRendered event) {
            Screen screen = event.getScreen();
            if (!NightfallMenuAssets.ready() || !cover || Minecraft.getInstance().level != null || screen instanceof TitleScreen || screen instanceof LevelLoadingScreen
                    || screen instanceof GenericMessageScreen) {
                return;
            }
            GuiGraphics graphics = event.getGuiGraphics();
            int width = screen.width, height = screen.height;
            float scale = Math.max(width / 480.0F, height / 270.0F);
            int drawnWidth = (int)Math.ceil(480 * scale), drawnHeight = (int)Math.ceil(270 * scale);
            graphics.blit(COVER, (width - drawnWidth) / 2, (height - drawnHeight) / 2, drawnWidth, drawnHeight, 0, 0, 480, 270, 480, 270);
        }

        private Background() {
        }
    }

    private static void build(Path source, Path pack) throws IOException {
        Path sprites = pack.resolve("assets/minecraft/textures/gui/sprites");
        Files.createDirectories(sprites.resolve("widget"));
        Files.writeString(pack.resolve("pack.mcmeta"),
            "{\"pack\":{\"pack_format\":34,\"description\":\"NightfallCraft's menus from TCR Core (made by OROR from SETUP_NIGHTFALL.cmd's copy)\"}}",
            StandardCharsets.UTF_8);
        BufferedImage sheet = ImageIO.read(source.resolve("minecraft/gui/widgets.png").toFile());
        int unit = sheet.getWidth() / 256;
        for (Map.Entry<String, int[]> button : BUTTONS.entrySet()) {
            int[] r = button.getValue();
            BufferedImage part = sheet.getSubimage(r[0] * unit, r[1] * unit, r[2] * unit, r[3] * unit);
            ImageIO.write(part, "png", sprites.resolve(button.getKey() + ".png").toFile());
            Files.writeString(sprites.resolve(button.getKey() + ".png.mcmeta"), BUTTON_SCALING, StandardCharsets.UTF_8);
        }
        for (Map.Entry<String, String> tab : TABS.entrySet()) {
            Path from = source.resolve(tab.getValue());
            if (Files.isRegularFile(from)) {
                Files.copy(from, sprites.resolve(tab.getKey() + ".png"), java.nio.file.StandardCopyOption.REPLACE_EXISTING);
                Files.writeString(sprites.resolve(tab.getKey() + ".png.mcmeta"), TAB_SCALING, StandardCharsets.UTF_8);
            }
        }
        Path gui = pack.resolve("assets/minecraft/textures/gui");
        for (String side : new String[]{"header", "footer"}) {
            Path from = source.resolve("gui/" + side + "_separator.png");
            if (Files.isRegularFile(from)) {
                Files.copy(from, gui.resolve(side + "_separator.png"), java.nio.file.StandardCopyOption.REPLACE_EXISTING);
                Files.copy(from, gui.resolve("inworld_" + side + "_separator.png"), java.nio.file.StandardCopyOption.REPLACE_EXISTING);
            }
        }
        Path coverFrom = source.resolve("menu/background_blurred.png");
        if (Files.isRegularFile(coverFrom)) {
            Path menu = pack.resolve("assets/" + PACK_ID + "/textures/menu");
            Files.createDirectories(menu);
            Files.copy(coverFrom, menu.resolve("background_blurred.png"), java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        }
    }

    private NightfallCraftGui() {
    }
}
