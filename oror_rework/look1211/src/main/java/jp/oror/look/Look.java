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

    /** The duels (052): who fights, from tick 1240, two hundred ticks apart. */
    private static final String[] DUELISTS = {"valeria", "kokuhaku", "elseria", "kingdom_guard"};

    private static void play(Minecraft mc, int t) {
        // (052) each duel: the character and an armed vindicator set on each other (and healed) every half second, the
        // camera five blocks off, twenty-four frames six ticks apart from the fortieth tick
        for (int d = 0; d < DUELISTS.length; d++) {
            int k = t - (1240 + d * 200);
            if (k == 0) {
                duel(mc, DUELISTS[d]);
            } else if (k == 2) {
                view(mc, 0, 1.4, 1.2, 0F, 14F);
            }
            if (k >= 6 && k <= 190 && k % 10 == 6) {
                engage(mc);
            }
            if (k >= 40 && (k - 40) % 6 == 0 && (k - 40) / 6 < 24) {
                shot(mc, String.format(java.util.Locale.ROOT, "19c_%s_%02d", DUELISTS[d], (k - 40) / 6));
            }
        }
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
            case 30 -> {
                // (051) the starter kit given on first joining: what the player holds and wears
                StringBuilder inv = new StringBuilder();
                for (int i = 0; i < mc.player.getInventory().getContainerSize(); i++) {
                    net.minecraft.world.item.ItemStack st = mc.player.getInventory().getItem(i);
                    if (!st.isEmpty()) {
                        inv.append(' ').append(net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(st.getItem())).append('x').append(st.getCount());
                    }
                }
                note("inventory after joining:" + inv);
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
            case 742 -> arms(mc);
            case 744 -> view(mc, 0, 0, 0, 0F, 8F);
            case 860 -> shot(mc, "19_arms");
            case 862 -> creatures(mc);
            case 864 -> view(mc, 0, 0, -3, 0F, 4F);
            case 980 -> shot(mc, "19b_creatures");
            // (052) the redrawn gear: in a row, worn and held by an armour stand, then at work and recharging
            case 990 -> gear(mc);
            case 992 -> view(mc, 0, 1.6, -1.5, 0F, 2F);
            case 1100 -> shot(mc, "32_gear");
            case 1102 -> view(mc, 3.6, 0.9, 0.6, 0F, 6F);
            case 1140 -> shot(mc, "33_gear_worn");
            case 1142 -> gearAtWork(mc);
            case 1144 -> view(mc, 0, 1.6, -1.5, 0F, 2F);
            case 1152 -> shot(mc, "34_gear_at_work");
            case 1202 -> shot(mc, "35_gear_recharging");
            // (052) the gear worn (Curios): from in front and behind (third person), and the talon on the bare hand;
            // between the gear's row and the duels (from 1240), the camera back in first person before they start
            case 1204 -> wornGear(mc, true);
            case 1206 -> {
                view(mc, 0, 0, 2, 180F, 6F);
                mc.options.setCameraType(net.minecraft.client.CameraType.THIRD_PERSON_FRONT);
            }
            case 1216 -> shot(mc, "36_gear_worn_front");
            case 1218 -> mc.options.setCameraType(net.minecraft.client.CameraType.THIRD_PERSON_BACK);
            case 1226 -> shot(mc, "37_gear_worn_back");
            case 1228 -> {
                // the hand is drawn in first person only with the GUI shown (F1 hides it too)
                mc.options.setCameraType(net.minecraft.client.CameraType.FIRST_PERSON);
                mc.options.hideGui = false;
                view(mc, 0, 0, 2, 180F, 20F);
            }
            case 1234 -> shot(mc, "38_gear_worn_hand");
            case 1236 -> {
                wornGear(mc, false);
                mc.options.setCameraType(net.minecraft.client.CameraType.FIRST_PERSON);
                mc.options.hideGui = true;
            }
            case 2050 -> throne(mc);
            case 3850 -> shot(mc, "20_throne_room");
            case 3890 -> king(mc);
            case 5690 -> shot(mc, "21_throne_room_later");
            case 5710 -> {
                king(mc);
                overCapital(mc, 0, 0, 150);
            }
            case 7490 -> shot(mc, "22_capital_aerial");
            case 7500 -> overCapital(mc, -265, -239, 40);
            case 9090 -> shot(mc, "23_helipad");
            case 9100 -> overCapital(mc, -250, -377, 45);
            case 10690 -> shot(mc, "24_airbase");
            // 048: the posts' supply, a helipad's power plant and depot, and a hangar's bays with theirs
            case 10700 -> atCapital(mc, -265, 10, -250, 0F, 48F);
            case 12290 -> shot(mc, "25_helipad_supply");
            // 049: the west road's hangar, from the road in front of its apron
            case 12300 -> atCapital(mc, -405, 5, -4, 180F, 14F);
            case 13890 -> shot(mc, "26_hangar_supply");
            // the palace's roofs from the south-east, high up (the two light wells roofed over in 048)
            case 13900 -> atCapital(mc, 70, 115, 110, 150F, 32F);
            case 15490 -> shot(mc, "27_palace_roofs");
            // 049: the second runway along the east band of the farm belt, from above
            case 15500 -> overCapital(mc, 361, -278, 70);
            case 17090 -> shot(mc, "28_airbase_east");
            // a high road's fountain with its new rim (its water ran out over the street), looking north from the road
            case 17100 -> atCapital(mc, 0, 7, -204, 180F, 28F);
            case 18690 -> shot(mc, "29_road_fountain");
            // the sheep ranch's barn (its gables were open) and the east fortress's hall (its roof hung over its walls)
            case 18700 -> atCapital(mc, 383, 22, -213, -135F, 30F);
            case 20290 -> shot(mc, "30_ranch_barn");
            case 20300 -> atCapital(mc, 505, 40, 55, -135F, 30F);
            case 21890 -> shot(mc, "31_fortress_east");
            // (054) the villager king's four forms on the stage: the regal king, the hero, the broken one near death
            // (every stage of his ruin), Baal Zebul with his divine clubs and with the fly lord's scythe; close up, and
            // the god from behind; then his three returns from death as films, with the screen's part shown
            case 21900 -> view(mc, 0, 3, -12, 0F, 8F);
            case 21960 -> kingForms(mc);
            case 22060 -> shot(mc, "40_king_forms");
            case 22070 -> view(mc, -15, 1.2, 3.5, 0F, 4F);
            case 22110 -> shot(mc, "41_king_regal");
            case 22120 -> view(mc, -9, 1.8, 2.5, 0F, 6F);
            case 22160 -> shot(mc, "42_king_hero");
            case 22170 -> view(mc, -3, 2.0, 2.0, 0F, 6F);
            case 22210 -> shot(mc, "43_king_broken_55");
            case 22215 -> view(mc, 3, 2.0, 2.0, 0F, 6F);
            case 22240 -> shot(mc, "43b_king_broken_15");
            case 22245 -> view(mc, 9, 3.0, 0.5, 0F, 8F);
            case 22275 -> shot(mc, "44_king_divine_spear");
            case 22280 -> view(mc, 15, 3.0, 0.5, 0F, 8F);
            case 22310 -> shot(mc, "45_king_divine_bow");
            case 22320 -> view(mc, 9, 3.0, 19.5, 180F, 8F);
            case 22360 -> shot(mc, "46_king_divine_back");
            case 22370 -> kingFilm(mc, 1);
            case 22400 -> shot(mc, "47_film_hero_kneel");
            case 22420 -> shot(mc, "48_film_hero_pillar");
            case 22457 -> shot(mc, "49_film_hero_flash");
            case 22480 -> kingFilm(mc, 2);
            case 22510 -> shot(mc, "50_film_glitch_a");
            case 22550 -> shot(mc, "51_film_glitch_b");
            case 22610 -> kingFilm(mc, 3);
            case 22650 -> shot(mc, "52_film_divine_peel");
            case 22690 -> shot(mc, "53_film_divine_rise");
            case 22725 -> shot(mc, "54_film_divine_name");
            case 22745 -> shot(mc, "55_film_divine_climax");
            case 22800 -> finish(mc, "complete");
            default -> {
            }
        }
    }

    /** (054) Five villager kings in a row on the stage, z + 10, each set to a form through OROR's own code. */
    private static void kingForms(Minecraft mc) {
        IntegratedServer server = mc.getSingleplayerServer();
        mc.options.hideGui = true;
        server.execute(() -> {
            command(server, "kill @e[tag=oror_look]");
            // the throne king, the hero, the broken one at 55% and at 15% of his life (falling apart), Baal Zebul with
            // the spear and with the bow (the holding poses)
            double[] xs = {-15, -9, -3, 3, 9, 15};
            for (int i = 0; i < xs.length; i++) {
                command(server, String.format(java.util.Locale.ROOT,
                    "summon oror_supreme_bosses:villager_king %.1f %d %.1f {NoAI:1b,PersistenceRequired:1b,Rotation:[180f,0f],Tags:[\"oror_look\",\"oror_king_%d\"]}",
                    sx + xs[i], (int) sy, sz + 10, i));
            }
            ServerLevel level = server.overworld();
            for (Entity e : level.getEntities((Entity) null, new AABB(sx - 20, sy - 3, sz, sx + 20, sy + 12, sz + 20),
                x -> x.getTags().stream().anyMatch(t -> t.startsWith("oror_king_")))) {
                int i = e.getTags().stream().filter(t -> t.startsWith("oror_king_")).mapToInt(t -> Integer.parseInt(t.substring(10))).findFirst().orElse(0);
                int[] phase = {0, 1, 2, 2, 3, 3}, stance = {0, 0, 0, 0, 4, 5};
                float[] life = {1F, 1F, 0.55F, 0.15F, 1F, 1F};
                setForm(level, e, phase[Math.min(5, i)], stance[Math.min(5, i)], life[Math.min(5, i)], false);
            }
        });
    }

    /** (054) One villager king on the stage, returning from death into the form: his film under way. */
    private static void kingFilm(Minecraft mc, int phase) {
        IntegratedServer server = mc.getSingleplayerServer();
        mc.options.hideGui = false;
        view(mc, 0, 2.2, 1.0, 0F, 6F);
        server.execute(() -> {
            command(server, "kill @e[tag=oror_look]");
            command(server, String.format(java.util.Locale.ROOT,
                "summon oror_supreme_bosses:villager_king %.1f %d %.1f {NoAI:1b,PersistenceRequired:1b,Rotation:[180f,0f],Tags:[\"oror_look\",\"oror_king_film\"]}",
                sx, (int) sy, sz + 10));
            ServerLevel level = server.overworld();
            for (Entity e : level.getEntities((Entity) null, new AABB(sx - 5, sy - 3, sz + 5, sx + 5, sy + 12, sz + 15),
                x -> x.getTags().contains("oror_king_film"))) {
                setForm(level, e, phase, 0, 1F, true);
            }
        });
    }

    private static void setForm(ServerLevel level, Entity e, int phase, int stance, float life, boolean film) {
        boolean scythe = stance != 0;
        try {
            Class<?> mobC = Class.forName("jp.oror.reborn.royal.RoyalMob");
            Class<?> forms = Class.forName("jp.oror.reborn.king.KingForms");
            Object sov = mobC.getMethod("sovereign").invoke(e);
            net.minecraft.nbt.CompoundTag t = new net.minecraft.nbt.CompoundTag();
            t.putInt("Phase", phase);
            sov.getClass().getMethod("load", net.minecraft.nbt.CompoundTag.class).invoke(sov, t);
            float field = ((Number) sov.getClass().getMethod("field").invoke(sov)).floatValue();
            mobC.getMethod("syncSovereign", float.class, int.class, boolean.class).invoke(e, field, phase, false);
            if (film) {
                forms.getMethod("reborn", mobC, int.class).invoke(null, e, phase);
            } else {
                forms.getMethod("strengthen", mobC, int.class).invoke(null, e, phase);
                forms.getMethod("arm", mobC, int.class).invoke(null, e, phase);
            }
            if (scythe) {
                Class.forName("jp.oror.reborn.king.KingDeeds").getMethod("switchStance", mobC, ServerLevel.class, int.class).invoke(null, e, level, stance);
            }
            if (life < 1F && !film) {
                java.lang.reflect.Field w = sov.getClass().getField("internalWrite");
                w.setBoolean(sov, true);
                ((LivingEntity) e).setHealth(((LivingEntity) e).getMaxHealth() * life);
                w.setBoolean(sov, false);
            }
            note(String.format(java.util.Locale.ROOT, "king form %d%s%s: scale %.2f, health %.0f/%.0f, holding %s", phase, scythe ? " (scythe)" : "",
                film ? " (film)" : "", ((LivingEntity) e).getScale(), ((LivingEntity) e).getHealth(), ((LivingEntity) e).getMaxHealth(),
                ((LivingEntity) e).getMainHandItem()));
        } catch (ReflectiveOperationException | RuntimeException ex) {
            note("king form " + phase + ": " + ex);
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

    /**
     * (051) The forbidden vault's arms on a row in front of the camera, shown as in an inventory slot: the five king-slayers,
     * the vault's three blades, the railgun and the laser gun (the stage's people cleared away first).
     */
    private static void arms(Minecraft mc) {
        IntegratedServer server = mc.getSingleplayerServer();
        if (server == null) {
            return;
        }
        String[] ids = {"kingslayer_sword", "kingslayer_axe", "kingslayer_bow", "kingslayer_crossbow", "kingslayer_trident", "azure_blade",
            "star_staff", "reverie_rapier", "railgun", "laser_gun"};
        server.execute(() -> {
            command(server, "kill @e[tag=oror_look]");
            for (int i = 0; i < ids.length; i++) {
                command(server, String.format(java.util.Locale.ROOT, "summon minecraft:item_display %.2f %.2f %.2f "
                        + "{item:{id:\"oror_supreme_bosses:%s\",count:1},item_display:\"gui\",billboard:\"center\",Tags:[\"oror_look\"],"
                        + "transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[0.9f,0.9f,0.9f]}}",
                    sx - 2.0 + (i % 5) * 1.0, sy + 1.9 - (i / 5) * 1.0, sz + 4.0, ids[i]));
            }
            note("arms on show");
        });
    }

    /** (052) The items whose sprites were placeholders, redrawn: twenty in four rows as they are seen in the world (their
     * 3D models; the inventory keeps the 2D icons), and an armour stand in the dragon coat and Teia's boots holding the
     * forge's repair tool and the squad banner. */
    private static void gear(Minecraft mc) {
        IntegratedServer server = mc.getSingleplayerServer();
        if (server == null) {
            return;
        }
        String[] ids = {"star_shard", "dragon_core", "forge_core", "curse_residue", "world_thread", "rewind_talisman", "purifying_dew",
            "mana_crystal", "dungeon_key", "field_guide", "forge_tool", "dragon_coat", "teia_boots", "omniregistry_treasure", "villager_king_token",
            "focus_cell", "dodge_talon", "last_bloom", "parry_emblem", "squad_banner"};
        server.execute(() -> {
            command(server, "kill @e[tag=oror_look]");
            command(server, "kill @e[type=minecraft:item]");
            for (int i = 0; i < ids.length; i++) {
                command(server, String.format(java.util.Locale.ROOT, "summon minecraft:item_display %.2f %.2f %.2f "
                        + "{item:{id:\"oror_supreme_bosses:%s\",count:1},item_display:\"fixed\",Rotation:[200f,0f],Tags:[\"oror_look\"],"
                        + "transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[0.85f,0.85f,0.85f]}}",
                    sx - 2.0 + (i % 5) * 1.0, sy + 3.4 - (i / 5) * 1.0, sz + 5.0, ids[i]));
            }
            // the redrawn boss seals and sealed gates, on the floor either side of the row
            String[] blocks = {"bahamut_boss_seal", "elseria_boss_seal", "hephaistos_boss_seal", "teia_boss_seal", "yggdrasil_boss_seal",
                "ouroboros_boss_seal", "sword_gate", "laboratory_gate", "tragedy_gate", "lucifara_boss_seal", "kokuhaku_boss_seal", "valeria_boss_seal"};
            for (int i = 0; i < blocks.length; i++) {
                int x = (int) Math.floor(sx) + (i < 6 ? -9 + i : 4 + (i - 6));
                command(server, String.format(java.util.Locale.ROOT, "setblock %d %d %d oror_supreme_bosses:%s", x, (int) Math.floor(sy),
                    (int) Math.floor(sz) + 7, blocks[i]));
            }
            command(server, String.format(java.util.Locale.ROOT, "summon minecraft:armor_stand %.2f %d %.2f {ShowArms:1b,NoBasePlate:1b,"
                + "Rotation:[180f,0f],Tags:[\"oror_look\"],ArmorItems:[{id:\"oror_supreme_bosses:teia_boots\",count:1},{},"
                + "{id:\"oror_supreme_bosses:dragon_coat\",count:1},{}],HandItems:[{id:\"oror_supreme_bosses:forge_tool\",count:1},"
                + "{id:\"oror_supreme_bosses:squad_banner\",count:1}],Pose:{RightArm:[-60f,0f,0f],LeftArm:[-30f,10f,-10f]}}", sx + 3.6, (int) sy,
                sz + 3.2));
            note("gear on show");
        });
    }

    /** (052) The gear worn by the camera's player (through the patch's WornGear, Curios's slots): the rewind talisman
     * round the neck, the parry emblem on the left arm, the dodge talon on the right hand, the squad banner on the back,
     * the last bloom in the hair, all ready (their cooldowns cleared); or taken off again. */
    private static void wornGear(Minecraft mc, boolean on) {
        IntegratedServer server = mc.getSingleplayerServer();
        if (server == null) {
            return;
        }
        server.execute(() -> {
            ServerPlayer p = server.getPlayerList().getPlayers().isEmpty() ? null : server.getPlayerList().getPlayers().get(0);
            if (p == null) {
                return;
            }
            if (on) {
                command(server, "kill @e[tag=oror_look]");
            }
            String[][] gear = {{"necklace", "rewind_talisman"}, {"bracelet", "parry_emblem"}, {"hands", "dodge_talon"}, {"back", "squad_banner"},
                {"head", "last_bloom"}};
            int worn = 0;
            try {
                Method wear = Class.forName("jp.oror.reborn.gear.WornGear").getMethod("wear", LivingEntity.class, String.class,
                    net.minecraft.world.item.ItemStack.class);
                for (String[] g : gear) {
                    net.minecraft.world.item.Item item = net.minecraft.core.registries.BuiltInRegistries.ITEM.get(
                        net.minecraft.resources.ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", g[1]));
                    p.getCooldowns().removeCooldown(item);
                    if ((boolean) wear.invoke(null, p, g[0], on ? new net.minecraft.world.item.ItemStack(item) : net.minecraft.world.item.ItemStack.EMPTY)) {
                        worn++;
                    }
                }
            } catch (ReflectiveOperationException | RuntimeException ex) {
                note("worn gear failed: " + ex);
            }
            p.setItemInHand(InteractionHand.MAIN_HAND, net.minecraft.world.item.ItemStack.EMPTY);
            note((on ? "gear worn: " : "gear taken off: ") + worn + " of " + gear.length);
        });
    }

    /** (052) The Nightfall gear put to work for the camera's player (its cooldowns started), so that its at-work and
     * recharging looks are what the row shows next. */
    private static void gearAtWork(Minecraft mc) {
        IntegratedServer server = mc.getSingleplayerServer();
        if (server == null) {
            return;
        }
        server.execute(() -> {
            ServerPlayer p = server.getPlayerList().getPlayers().isEmpty() ? null : server.getPlayerList().getPlayers().get(0);
            if (p == null) {
                return;
            }
            String[][] gear = {{"parry_emblem", "100"}, {"dodge_talon", "60"}, {"squad_banner", "600"}, {"last_bloom", "3600"}};
            for (String[] g : gear) {
                p.getCooldowns().addCooldown(net.minecraft.core.registries.BuiltInRegistries.ITEM.get(
                    net.minecraft.resources.ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", g[0])), Integer.parseInt(g[1]));
            }
            note("gear at work");
        });
    }

    /** (051) Three of OROR's creatures and three of its people, as 0.17.27-0.17.29 drew and modelled them. */
    private static void creatures(Minecraft mc) {
        IntegratedServer server = mc.getSingleplayerServer();
        if (server == null) {
            return;
        }
        String[] ids = {"bahamut", "kurma", "demiurgos", "valeria", "arcana", "teia"};
        server.execute(() -> {
            command(server, "kill @e[tag=oror_look]");
            for (int i = 0; i < ids.length; i++) {
                command(server, String.format(java.util.Locale.ROOT,
                    "summon oror_supreme_bosses:%s %.1f %d %.1f {NoAI:1b,PersistenceRequired:1b,Rotation:[180f,0f],Tags:[\"oror_look\"]}",
                    ids[i], sx - 10 + (i % 3) * 10 + (i >= 3 ? 5 : 0), (int) sy, sz + (i >= 3 ? 4 : 14)));
            }
            note("creatures on show");
        });
    }

    /**
     * (051) One fighter facing a vindicator across the stage (left and right of the camera), both with their AI: the
     * shots that follow catch how it moves, casts and strikes.
     */
    private static void duel(Minecraft mc, String who) {
        IntegratedServer server = mc.getSingleplayerServer();
        if (server == null) {
            return;
        }
        server.execute(() -> {
            ServerLevel level = server.overworld();
            // the stage cleared: what earlier scenes set out (the royals' king survives /kill), and what they dropped
            for (Entity e : level.getEntities((Entity) null, new AABB(sx - 30, sy - 6, sz - 20, sx + 30, sy + 20, sz + 40),
                x -> x.getTags().contains("oror_look") || x instanceof net.minecraft.world.entity.item.ItemEntity
                    || x instanceof net.minecraft.world.entity.monster.Vindicator)) {
                e.discard();
            }
            command(server, String.format(java.util.Locale.ROOT,
                "summon oror_supreme_bosses:%s %.1f %d %.1f {PersistenceRequired:1b,Rotation:[-90f,0f],Tags:[\"oror_look\",\"oror_look_hero\"]}", who,
                sx - 1.8, (int) sy, sz + 6));
            command(server, String.format(java.util.Locale.ROOT, "summon minecraft:vindicator %.1f %d %.1f {PersistenceRequired:1b,Invulnerable:1b,"
                + "Rotation:[90f,0f],Tags:[\"oror_look\",\"oror_look_foe\"],HandItems:[{id:\"minecraft:iron_axe\",count:1},{}]}", sx + 1.8, (int) sy,
                sz + 6));
            note("duel: " + who);
        });
    }

    /**
     * (052) The duel's two set on each other, healed, and brought back to the stage if they have wandered off it, so that
     * the character keeps fighting (its techniques, big moves and guard) in front of the camera.
     */
    private static void engage(Minecraft mc) {
        IntegratedServer server = mc.getSingleplayerServer();
        if (server == null) {
            return;
        }
        server.execute(() -> {
            ServerLevel level = server.overworld();
            net.minecraft.world.entity.Mob hero = null, foe = null;
            for (Entity e : level.getEntities((Entity) null, new AABB(sx - 24, sy - 4, sz - 16, sx + 24, sy + 12, sz + 30),
                x -> x.getTags().contains("oror_look") && x instanceof net.minecraft.world.entity.Mob)) {
                net.minecraft.world.entity.Mob m = (net.minecraft.world.entity.Mob) e;
                if (e.getTags().contains("oror_look_foe")) {
                    foe = m;
                } else if (e.getTags().contains("oror_look_hero")) {
                    hero = m;
                }
            }
            if (hero == null || foe == null) {
                note("engage: hero " + (hero != null) + " foe " + (foe != null));
                return;
            }
            for (net.minecraft.world.entity.Mob m : List.of(hero, foe)) {
                m.setHealth(m.getMaxHealth());
                if (Math.abs(m.getX() - sx) > 7 || Math.abs(m.getZ() - (sz + 6)) > 6 || Math.abs(m.getY() - sy) > 6) {
                    m.teleportTo(sx + (m == hero ? -1.8 : 1.8), sy, sz + 6);
                }
            }
            hero.setTarget(foe);
            foe.setTarget(hero);
            net.minecraft.nbt.CompoundTag data = hero.getPersistentData();
            note("engage: " + net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.getKey(hero.getType()).getPath() + " holds "
                + net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(hero.getMainHandItem().getItem()).getPath() + " dist "
                + String.format(java.util.Locale.ROOT, "%.1f", hero.distanceTo(foe)) + " move " + data.getString("ororMove") + " parries "
                + data.getInt("OrorParries") + "/" + data.getInt("RoyalParries") + " blocks " + data.getInt("OrorBlocks") + "/"
                + data.getInt("RoyalBlocks") + " cast " + data.getInt("OrorCastSequence"));
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
