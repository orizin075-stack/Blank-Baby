package jp.oror.harness;

import com.mojang.logging.LogUtils;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.components.AbstractButton;
import net.minecraft.client.gui.components.events.GuiEventListener;
import net.minecraft.client.gui.screens.GenericDirtMessageScreen;
import net.minecraft.client.gui.screens.LevelLoadingScreen;
import net.minecraft.client.gui.screens.ProgressScreen;
import net.minecraft.client.gui.screens.ReceivingLevelScreen;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.client.gui.screens.worldselection.CreateWorldScreen;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.LivingEntityRenderer;
import net.minecraft.client.server.IntegratedServer;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.contents.TranslatableContents;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.loading.FMLEnvironment;
import net.minecraftforge.registries.ForgeRegistries;
import org.slf4j.Logger;

/**
 * CI only, never shipped: a mob gallery for the reference pack (L_Ender's Cataclysm, Alex's Caves, Legendary Monsters,
 * Monster Expansion, Witheria and their libraries, Forge 1.20.1). Creates a world, builds a stage high in the sky and
 * shows every living entity the mods add, one at a time, frozen (NoAI) beside an armour stand for scale; each is
 * photographed with the HUD hidden from three quarters in front and from the side. What it measured (size, renderer
 * and model classes) goes to harness/gallery.tsv.
 */
@Mod("oror_harness")
public final class Harness {
    private static final Logger LOG = LogUtils.getLogger();
    private static final Set<String> PROCEED = Set.of("gui.proceed", "gui.continue", "gui.done", "gui.ok", "gui.yes",
            "gui.acknowledge", "selectWorld.backupJoinSkipButton");
    private static final int LIMIT = 150000;
    private static final double SX = 0.5, SY = 241.0, SZ = 0.5;          // where each mob stands

    private enum Phase { TITLE, CREATE, LOADING, PLAY, DONE }

    private static Phase phase = Phase.TITLE;
    private static Screen seen;
    private static int onScreen, overlayTicks, total, play, popups, index = -1, step;
    private static final List<String> log = Collections.synchronizedList(new ArrayList<>());
    private static final List<String> rows = Collections.synchronizedList(new ArrayList<>());
    private static volatile List<String> ids;
    private static volatile double width = 1, height = 1;
    private static volatile String current;

    public Harness() {
        if (FMLEnvironment.dist != Dist.CLIENT) return;
        MinecraftForge.EVENT_BUS.addListener((TickEvent.ClientTickEvent event) -> {
            if (event.phase != TickEvent.Phase.END) return;
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
                List<String> lines = new ArrayList<>();
                ModList.get().getMods().forEach(mod -> lines.add("mod " + mod.getModId() + " " + mod.getVersion()));
                write(mc, "info.txt", lines);
            } else if (onScreen == 220) {
                phase = Phase.CREATE;
                CreateWorldScreen.openFresh(mc, screen);
            }
        } else if (screen != null) {
            popup(mc, screen);
        }
    }

    private static void create(Minecraft mc, Screen screen) {
        if (screen instanceof CreateWorldScreen) {
            if (onScreen == 70 && !press(screen, Set.of("selectWorld.create"))) note("no create button");
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
        if (mc.level != null && mc.player != null && screen == null) phase = Phase.PLAY;
        else if (screen != null && !loadingScreen(screen)) popup(mc, screen);
    }

    private static boolean loadingScreen(Screen screen) {
        return screen instanceof LevelLoadingScreen || screen instanceof ReceivingLevelScreen
                || screen instanceof GenericDirtMessageScreen || screen instanceof ProgressScreen;
    }

    private static void play(Minecraft mc, Screen screen) {
        if (mc.player == null || mc.level == null) return;
        if (screen != null) {
            popup(mc, screen);
            return;
        }
        play++;
        if (play == 40) setup(mc);
        if (play < 200) return;
        if (ids == null) {
            if (play == 600) finish(mc, "no entity list");
            return;
        }
        // one mob at a time: summon, let it settle, front three-quarter shot, side shot, clear the stage
        step++;
        if (index < 0 || current == null || step > 70) {
            index++;
            step = 0;
            if (index >= ids.size()) {
                write(mc, "done.txt", List.of(String.valueOf(ids.size())));
                finish(mc, "complete: " + ids.size() + " mobs");
                return;
            }
            current = ids.get(index);
            write(mc, "progress.txt", List.of(String.valueOf(index)));
            if (index % 10 == 0) write(mc, "gallery-" + index + ".tsv", new ArrayList<>(rows));
            summon(mc, current);
            return;
        }
        String file = String.format(Locale.ROOT, "%03d+%s", index, current.replace(':', '+').replace('/', '_'));
        switch (step) {
            case 6 -> camera(mc, 35.0, 0.62);
            case 34 -> {
                describe(mc);
                shot(mc, file + "_a");
            }
            case 36 -> camera(mc, 90.0, 0.5);
            case 52 -> shot(mc, file + "_b");
            default -> { }
        }
    }

    /** World rules, a stage high in the sky, spectator mode, the HUD hidden, and the list of mobs to show. */
    private static void setup(Minecraft mc) {
        IntegratedServer server = mc.getSingleplayerServer();
        if (server == null) return;
        mc.options.hideGui = true;
        mc.options.fov().set(55);
        UUID id = mc.player.getUUID();
        server.execute(() -> {
            for (String command : new String[]{"time set 6000", "weather clear 1000000", "gamerule doDaylightCycle false",
                    "gamerule doWeatherCycle false", "gamerule doMobSpawning false", "gamerule mobGriefing false",
                    "gamerule doFireTick false", "gamerule doTileDrops false", "difficulty easy"}) {
                server.getCommands().performPrefixedCommand(server.createCommandSourceStack(), command);
            }
            ServerLevel level = server.overworld();
            for (int x = -30; x <= 30; x++) {
                for (int z = -30; z <= 30; z++) {
                    level.setBlock(new BlockPos(x, 240, z), (x + z & 1) == 0 ? Blocks.SMOOTH_STONE.defaultBlockState()
                            : Blocks.STONE.defaultBlockState(), 2);
                }
            }
            ServerPlayer player = server.getPlayerList().getPlayer(id);
            if (player != null) {
                player.setGameMode(GameType.SPECTATOR);
                player.teleportTo(level, SX, SY + 4, SZ + 10, 180, 10);
            }
            List<String> out = new ArrayList<>();
            for (Map.Entry<ResourceKey<EntityType<?>>, EntityType<?>> e : ForgeRegistries.ENTITY_TYPES.getEntries()) {
                String key = e.getKey().location().toString();
                if (key.startsWith("minecraft:") || key.startsWith("oror_harness:")) continue;
                try {
                    Entity probe = e.getValue().create(level);
                    if (probe instanceof LivingEntity) out.add(key);
                    else note("skip " + key + " (" + (probe == null ? "null" : probe.getClass().getSimpleName()) + ")");
                    if (probe != null) probe.discard();
                } catch (Throwable error) {
                    note("skip " + key + " (" + error + ")");
                }
            }
            Collections.sort(out);
            note("mobs to show: " + out.size() + " " + out);
            // a mob that took the last client down is skipped: start after the one in progress.txt
            try {
                Path progress = mc.gameDirectory.toPath().resolve("harness/progress.txt");
                if (Files.exists(progress)) {
                    index = Integer.parseInt(Files.readString(progress).trim());
                    note("resuming after " + index + " (" + (index < out.size() ? out.get(index) : "?") + ")");
                    rows.add(index + "\t" + (index < out.size() ? out.get(index) : "?") + "\tcrashed the client");
                }
            } catch (Exception error) {
                note("cannot read progress: " + error);
            }
            ids = out;
        });
    }

    private static void summon(Minecraft mc, String key) {
        IntegratedServer server = mc.getSingleplayerServer();
        if (server == null) return;
        server.execute(() -> {
            ServerLevel level = server.overworld();
            clear(level);
            try {
                EntityType<?> type = ForgeRegistries.ENTITY_TYPES.getValue(net.minecraft.resources.ResourceLocation.tryParse(key));
                Entity entity = type == null ? null : type.create(level);
                if (entity == null) {
                    note("cannot create " + key);
                    return;
                }
                entity.moveTo(SX, SY, SZ, 0, 0);
                if (entity instanceof Mob mob) {
                    try {
                        mob.finalizeSpawn(level, level.getCurrentDifficultyAt(BlockPos.containing(SX, SY, SZ)), MobSpawnType.COMMAND, null, null);
                    } catch (Throwable error) {
                        note("finalizeSpawn " + key + ": " + error);
                    }
                    mob.setNoAi(true);
                    mob.setPersistenceRequired();
                }
                entity.moveTo(SX, SY, SZ, 0, 0);
                if (entity instanceof LivingEntity living) {
                    living.setYHeadRot(0);
                    living.setYBodyRot(0);
                }
                entity.setSilent(true);
                entity.setInvulnerable(true);
                level.addFreshEntity(entity);
                width = entity.getBbWidth();
                height = entity.getBbHeight();
                Entity stand = EntityType.ARMOR_STAND.create(level);
                if (stand != null) {
                    stand.moveTo(SX - Math.max(1.6, width / 2 + 1.4), SY, SZ, 0, 0);
                    level.addFreshEntity(stand);
                }
                note("summoned " + key + " " + String.format(Locale.ROOT, "%.2fx%.2f", width, height));
            } catch (Throwable error) {
                note("summon failed " + key + ": " + error);
                LOG.error("[harness] summon failed {}", key, error);
            }
        });
    }

    /** Everything but players near the stage goes (the last mob, its minions, projectiles, the scale stand). */
    private static void clear(ServerLevel level) {
        for (Entity e : level.getEntities((Entity) null, new AABB(SX - 96, SY - 64, SZ - 96, SX + 96, SY + 96, SZ + 96),
                e -> !(e instanceof Player))) {
            e.discard();
        }
    }

    /** Puts the camera at `angle` degrees round from the mob's front, framing its whole box, looking at `aim` of its height. */
    private static void camera(Minecraft mc, double angle, double aim) {
        IntegratedServer server = mc.getSingleplayerServer();
        if (server == null) return;
        UUID id = mc.player.getUUID();
        double w = width, h = height;
        server.execute(() -> {
            ServerPlayer player = server.getPlayerList().getPlayer(id);
            if (player == null) return;
            double size = Math.max(h, w * 1.1);
            double d = size * 1.45 + 2.2;
            double a = Math.toRadians(angle);
            double dx = Math.sin(a) * d, dz = Math.cos(a) * d;
            double ty = SY + h * aim;
            double cy = ty + size * 0.18;
            float yaw = (float) Math.toDegrees(Math.atan2(dx, -dz));
            float pitch = (float) Math.toDegrees(Math.atan2(cy - ty, d));
            player.teleportTo(server.overworld(), SX + dx, cy - player.getEyeHeight(), SZ + dz, yaw, pitch);
        });
    }

    private static void describe(Minecraft mc) {
        String renderer = "?", model = "?", cls = "?";
        if (mc.level != null) {
            for (Entity e : mc.level.entitiesForRendering()) {
                String key = String.valueOf(ForgeRegistries.ENTITY_TYPES.getKey(e.getType()));
                if (!key.equals(current)) continue;
                cls = e.getClass().getName();
                EntityRenderer<?> r = mc.getEntityRenderDispatcher().getRenderer(e);
                renderer = r.getClass().getName();
                if (r instanceof LivingEntityRenderer<?, ?> lr) model = lr.getModel().getClass().getName();
                break;
            }
        }
        rows.add(String.format(Locale.ROOT, "%d\t%s\t%.2f\t%.2f\t%s\t%s\t%s", index, current, width, height, cls, renderer, model));
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

    private static void finish(Minecraft mc, String result) {
        phase = Phase.DONE;
        note("finished: " + result);
        write(mc, "gallery-session-" + System.currentTimeMillis() + ".tsv", new ArrayList<>(rows));
        synchronized (log) {
            write(mc, "result-" + System.currentTimeMillis() + ".txt", new ArrayList<>(log));
        }
        mc.stop();
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
