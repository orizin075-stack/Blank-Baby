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

    /** (055) What is to be done at a tick of the play (the King's moves' scenes, planned when they begin). */
    private static final java.util.TreeMap<Integer, Runnable> PLAN = new java.util.TreeMap<>();

    /** (058) One part only, from the workflow's input: "relics" goes from the stage straight to the relics' scenes. */
    private static final String ONLY = String.valueOf(System.getenv("OROR_LOOK_ONLY")).trim();

    private static void play(Minecraft mc, int t) {
        Runnable planned = PLAN.remove(t);
        if (planned != null) {
            planned.run();
        }
        if (ONLY.equals("palace") && t >= 240) {
            // (059) the rebuilt palace: its stairs from the town, the audience hall and the throne with the court, the
            // rooms and floors over it (template coordinates less the ground: the capital's centre is at y 65)
            if (t == 240) {
                PLAN.put(250, () -> throne(mc));
                int at = 2050;
                Object[][] tour = {
                    {"80_palace_hall", 0, 80, 38, 180F, 6F}, {"81_palace_throne", 0, 81, -15, 180F, 8F},
                    {"82_palace_throne_close", 0, 80, -21, 180F, 4F}, {"83_palace_south_stair", 0, 70, 114, 180F, -4F},
                    {"84_palace_front", 0, 78, 70, 180F, -2F}, {"85_palace_corner_stair", -33, 82, 32, 225F, 20F},
                    {"86_palace_library", -24, 77, -12, 135F, 10F}, {"87_palace_war_room", 24, 77, -12, 225F, 10F},
                    {"88_palace_treasury", -2, 77, -33, 120F, 12F}, {"89_palace_chapel", 0, 102, -18, 180F, 6F},
                    {"90_palace_bedchamber", 0, 112, -20, 180F, 10F}, {"91_palace_ballroom", 0, 124, 34, 180F, 8F},
                    {"92_palace_north_stair", 0, 70, -112, 0F, -4F}, {"93_palace_gallery", 17, 77, 30, 180F, 4F}};
                for (Object[] v : tour) {
                    int dx = (Integer) v[1], y = (Integer) v[2], dz = (Integer) v[3];
                    float yaw = (Float) v[4], pitch = (Float) v[5];
                    String name = (String) v[0];
                    PLAN.put(at, () -> atCapital(mc, dx, y - 65, dz, yaw, pitch));
                    PLAN.put(at + 60, () -> shot(mc, name));
                    at += 70;
                }
                PLAN.put(at, () -> king(mc));
                PLAN.put(at + 10, () -> finish(mc, "complete (palace only)"));
                note("palace only: planned to tick " + (at + 10));
            }
            return;
        }
        if (ONLY.equals("relics") && t >= 240) {
            // the stage stands and the player has joined (ticks 2 to 200): the capital's tour and the rest are left out
            if (t == 240) {
                int end = relicScenes(mc, 260);
                PLAN.put(end, () -> finish(mc, "complete (relics only)"));
                note("relics only: planned to tick " + end);
            }
            return;
        }
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
            // (055) close up, how he holds each arm; then each of his seventy moves caught at its windup and at its
            // blow, one form and stance at a time; then the veil of flies over the field
            case 22800 -> kingMoves(mc, 22810);
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

    /**
     * (055) The King's moves, form by form: the hero's sword, the broken one's, then Baal Zebul's five arms. For each,
     * one king alone on the stage (z + 10, facing the camera's side), close up from his right front and from his side
     * as he holds it, then every move of that arm sent to him as the server sends it (TechniqueShow "move:king_<id>")
     * and caught twice: in its windup and as its blow lands. Last the veil of flies, from above and from the ground.
     */
    private static void kingMoves(Minecraft mc, int from) {
        List<Object> moves;
        try {
            moves = new ArrayList<>((List<?>) Class.forName("jp.oror.reborn.king.KingArsenal").getField("MOVES").get(null));
        } catch (ReflectiveOperationException | RuntimeException ex) {
            note("king moves: " + ex);
            PLAN.put(from + 10, () -> finish(mc, "complete"));
            return;
        }
        String[] names = {"sword", "broken", "clubs", "scythe", "twin", "spear", "bow"};
        int at = from;
        for (int w = 0; w < names.length; w++) {
            final int weapon = w;
            final String nm = names[w];
            int phase = w == 0 ? 1 : w == 1 ? 2 : 3;
            int stance = w >= 2 ? w - 1 : 0;
            float life = w == 1 ? 0.6F : 1F;
            double k = w == 0 ? 0.75 : w == 1 ? 0.9 : 1.1;
            double dy = w == 0 ? 2.0 : w == 1 ? 2.4 : 3.0;
            PLAN.put(at, () -> soloKing(mc, phase, stance, life));
            PLAN.put(at + 40, () -> view(mc, 3.5 * k, dy, 10 - 6 * k, 30.3F, 6F));
            PLAN.put(at + 50, () -> shot(mc, String.format(java.util.Locale.ROOT, "56_%d_%s_hold", weapon, nm)));
            PLAN.put(at + 52, () -> view(mc, 8 * k, dy, 10, 90F, 4F));
            PLAN.put(at + 62, () -> shot(mc, String.format(java.util.Locale.ROOT, "56_%d_%s_hold_side", weapon, nm)));
            PLAN.put(at + 64, () -> view(mc, 4.6 * k, dy, 10 - 7 * k, 33.3F, 6F));
            int j = 0;
            for (Object m : moves) {
                try {
                    if (((Number) m.getClass().getMethod("weapon").invoke(m)).intValue() != w) {
                        continue;
                    }
                    String id = (String) m.getClass().getMethod("id").invoke(m);
                    int windup = ((Number) m.getClass().getMethod("windup").invoke(m)).intValue();
                    int length = ((Number) m.getClass().getMethod("length").invoke(m)).intValue();
                    int t0 = at + 80 + j * 32;
                    int jj = j;
                    PLAN.put(t0, () -> kingMove(mc, id, windup, length));
                    PLAN.put(t0 + Math.max(1, windup - 2), () -> shot(mc, String.format(java.util.Locale.ROOT, "57_%d_%02d_%s_w", weapon, jj, id)));
                    PLAN.put(t0 + windup + 2, () -> shot(mc, String.format(java.util.Locale.ROOT, "57_%d_%02d_%s_s", weapon, jj, id)));
                    j++;
                } catch (ReflectiveOperationException | RuntimeException ex) {
                    note("king move: " + ex);
                }
            }
            at += 80 + j * 32 + 20;
        }
        PLAN.put(at, () -> soloKing(mc, 3, 3, 1F));
        PLAN.put(at + 30, () -> kingVeil(mc));
        PLAN.put(at + 32, () -> view(mc, 0, 14, -10, 0F, 38F));
        PLAN.put(at + 90, () -> shot(mc, "58_veil_above"));
        PLAN.put(at + 92, () -> view(mc, 7, 1.2, 4, 20F, -4F));
        PLAN.put(at + 140, () -> shot(mc, "58_veil_ground"));
        // (056) Azazel remade: alone on the stage, close up, then each of his ten arts at its windup and its blow
        int az = at + 160;
        PLAN.put(az, () -> soloAzazel(mc));
        PLAN.put(az + 40, () -> view(mc, 2.6, 2.4, 10 - 5.2, 26.6F, 4F));
        PLAN.put(az + 46, () -> azazelSeen(mc));
        PLAN.put(az + 50, () -> shot(mc, "59_azazel_front"));
        PLAN.put(az + 52, () -> view(mc, 6.5, 2.4, 10, 90F, 4F));
        PLAN.put(az + 62, () -> shot(mc, "59_azazel_side"));
        PLAN.put(az + 64, () -> view(mc, 0, 2.6, 16, 180F, 4F));
        PLAN.put(az + 74, () -> shot(mc, "59_azazel_back"));
        PLAN.put(az + 76, () -> view(mc, 4.0, 2.4, 10 - 6.0, 33.7F, 6F));
        int k = 0;
        try {
            for (Object a : (List<?>) Class.forName("jp.oror.reborn.king.AzazelArts").getField("ARTS").get(null)) {
                String id = (String) a.getClass().getMethod("id").invoke(a);
                int windup = ((Number) a.getClass().getMethod("windup").invoke(a)).intValue();
                int length = ((Number) a.getClass().getMethod("length").invoke(a)).intValue();
                int t0 = az + 90 + k * 34;
                int kk = k;
                PLAN.put(t0, () -> azazelArt(mc, id, windup, length));
                PLAN.put(t0 + Math.max(1, windup - 2), () -> shot(mc, String.format(java.util.Locale.ROOT, "60_%02d_azazel_%s_w", kk, id)));
                PLAN.put(t0 + windup + 2, () -> shot(mc, String.format(java.util.Locale.ROOT, "60_%02d_azazel_%s_s", kk, id)));
                k++;
            }
        } catch (ReflectiveOperationException | RuntimeException ex) {
            note("azazel arts: " + ex);
        }
        int end = relicScenes(mc, wazaScenes(mc, az + 90 + k * 34 + 30));
        PLAN.put(end, () -> finish(mc, "complete"));
        note("king moves planned to tick " + end);
    }

    /**
     * (057) Of the 984 techniques, one of each of the seventeen behaviours (each on another character) and seven
     * finishing ones of the great creatures: the character alone on the stage with a dummy before it, the technique
     * started as the server starts it (WazaEngine.start), and caught at the end of its windup, at its first blow (or
     * its release), and late in its active window.
     */
    private static final String[] WAZA = {"kokuhaku_01", "riha_01", "tenki_19", "nortia_02", "berit_05", "elseria_12", "huang_linghua_17",
        "valeria_10", "ferdinand_01", "savior_01", "lucifara_13", "taika_23", "mary_sue_03", "gokuka_01", "merlinus_12", "cursed_love_12",
        "elseria_11", "kurma_24", "teia_24", "bahamut_24", "demiurgos_24", "yggdrasil_24", "mels_24", "chaos_24"};

    private static int wazaScenes(Minecraft mc, int from) {
        int at = from;
        java.util.Map<?, ?> book;
        try {
            book = (java.util.Map<?, ?>) Class.forName("jp.oror.reborn.waza.Waza").getField("BY_ID").get(null);
        } catch (ReflectiveOperationException | RuntimeException ex) {
            note("waza: " + ex);
            return at;
        }
        int k = 0;
        for (String id : WAZA) {
            Object w = book.get(id);
            if (w == null) {
                note("waza: no " + id);
                continue;
            }
            int windup, active, first;
            String character;
            try {
                windup = ((Number) w.getClass().getMethod("windup").invoke(w)).intValue();
                active = ((Number) w.getClass().getMethod("activeLength").invoke(w)).intValue();
                int[] hits = (int[]) w.getClass().getMethod("hits").invoke(w);
                first = hits.length > 0 ? hits[0] : Math.max(1, Math.round(active * 0.3F));
                character = (String) w.getClass().getMethod("character").invoke(w);
            } catch (ReflectiveOperationException | RuntimeException ex) {
                note("waza " + id + ": " + ex);
                continue;
            }
            int kk = k++;
            int t0 = at;
            PLAN.put(t0, () -> wazaStage(mc, character));
            PLAN.put(t0 + 30, () -> wazaView(mc));
            PLAN.put(t0 + 40, () -> wazaStart(mc, id));
            PLAN.put(t0 + 40 + Math.max(1, windup - 1), () -> shot(mc, String.format(java.util.Locale.ROOT, "62_%02d_%s_w", kk, id)));
            PLAN.put(t0 + 40 + windup + first + 1, () -> shot(mc, String.format(java.util.Locale.ROOT, "62_%02d_%s_s", kk, id)));
            PLAN.put(t0 + 40 + windup + Math.max(first + 3, active - 2), () -> shot(mc, String.format(java.util.Locale.ROOT, "62_%02d_%s_a", kk, id)));
            at = t0 + 40 + windup + active + 30;
        }
        note("waza scenes planned to tick " + at);
        return at + 10;
    }

    private static net.minecraft.world.entity.Mob wazaCaster, wazaDummy;

    /**
     * (058) Of the 123 relic techniques, sixteen of many kinds (blade lines and waves, beams, words, thunder, the colour
     * tag, wings and domes, spikes, rains of arrows, rings and clocks, trees, fists, units), each used by the player
     * itself with the weapon in hand (seen from behind it), caught while readied (the warning and the gathering light),
     * at its release, and later; then two tooltips of the rewritten relics, and the gauge over the hotbar.
     */
    private static final String[][] RELIC = {{"kokuhaku_weapon", "0"}, {"kokuhaku_weapon", "2"}, {"riha_weapon", "0"}, {"elseria_weapon", "1"},
        {"valeria_weapon", "0"}, {"nortia_weapon", "0"}, {"savior_weapon", "2"}, {"kurma_weapon", "0"}, {"teia_weapon", "2"}, {"bahamut_weapon", "0"},
        {"ouroboros_weapon", "2"}, {"yggdrasil_weapon", "2"}, {"demiurgos_weapon", "2"}, {"brutality_weapon", "2"}, {"lucifara_weapon", "1"},
        {"chaos_weapon", "1"}};

    private static int relicScenes(Minecraft mc, int from) {
        int at = from;
        Class<?> v9;
        try {
            v9 = Class.forName("jp.oror.reborn.relic.RelicV9");
        } catch (ReflectiveOperationException | RuntimeException ex) {
            note("relic: " + ex);
            return at;
        }
        int k = 0;
        for (String[] r : RELIC) {
            int slot = Integer.parseInt(r[1]);
            int windup, forming;
            try {
                Object[] ts = (Object[]) v9.getMethod("of", String.class).invoke(null, r[0]);
                Object t = ts[slot];
                windup = ((Number) t.getClass().getMethod("windup").invoke(t)).intValue();
                forming = ((Number) t.getClass().getMethod("forming").invoke(t)).intValue();
            } catch (ReflectiveOperationException | RuntimeException ex) {
                note("relic " + r[0] + "#" + slot + ": " + ex);
                continue;
            }
            int kk = k++;
            int t0 = at;
            String name = String.format(java.util.Locale.ROOT, "70_%02d_%s_%d", kk, r[0].replace("_weapon", ""), slot);
            PLAN.put(t0, () -> relicStage(mc, r[0]));
            PLAN.put(t0 + 25, () -> relicStart(mc, slot));
            PLAN.put(t0 + 25 + Math.max(2, windup - 3), () -> shot(mc, name + "_ready"));
            PLAN.put(t0 + 25 + windup + 4, () -> shot(mc, name + "_release"));
            PLAN.put(t0 + 25 + windup + 14, () -> shot(mc, name + "_later"));
            if (slot == 2) {
                PLAN.put(t0 + 25 + windup + Math.max(24, forming), () -> shot(mc, name + "_finish"));
            }
            at = t0 + 25 + windup + Math.max(30, forming + 20) + 20;
        }
        // the gauge over the hotbar, then two rewritten tooltips (a weapon's, a legend's)
        int g = at;
        PLAN.put(g, () -> {
            relicStage(mc, "kokuhaku_weapon");
            mc.options.hideGui = false;
        });
        PLAN.put(g + 20, () -> shot(mc, "71_relic_gauge"));
        // the play stands still while a screen is up: each tooltip screen takes its own picture and closes itself
        PLAN.put(g + 30, () -> mc.setScreen(new RelicTip(r("kokuhaku_weapon"), "72_tooltip_weapon")));
        PLAN.put(g + 32, () -> mc.setScreen(new RelicTip(r("kokuhaku_legend"), "73_tooltip_legend")));
        PLAN.put(g + 34, () -> mc.setScreen(new RelicTip(r("savior_charm"), "74_tooltip_charm")));
        PLAN.put(g + 36, () -> mc.setScreen(new RelicTip(r("riha_focus"), "75_tooltip_focus")));
        PLAN.put(g + 75, () -> {
            mc.setScreen(null);
            mc.options.setCameraType(net.minecraft.client.CameraType.FIRST_PERSON);
            mc.options.hideGui = true;
        });
        note("relic scenes planned to tick " + (g + 80));
        return g + 85;
    }

    private static net.minecraft.world.item.ItemStack r(String id) {
        try {
            Object items = Class.forName("jp.oror.reborn.CharacterRelics").getField("ITEMS").get(null);
            Object holder = ((java.util.Map<?, ?>) items).get(id);
            return new net.minecraft.world.item.ItemStack((net.minecraft.world.item.Item) holder.getClass().getMethod("get").invoke(holder));
        } catch (ReflectiveOperationException | RuntimeException ex) {
            note("relic item " + id + ": " + ex);
            return net.minecraft.world.item.ItemStack.EMPTY;
        }
    }

    /** A screen that shows only a relic's tooltip, as the inventory shows it (the tooltip event's lines too). */
    private static final class RelicTip extends Screen {
        private final net.minecraft.world.item.ItemStack stack;
        private final String name;
        private int frames;

        RelicTip(net.minecraft.world.item.ItemStack stack, String name) {
            super(net.minecraft.network.chat.Component.literal("relic"));
            this.stack = stack;
            this.name = name;
        }

        @Override
        public void render(net.minecraft.client.gui.GuiGraphics g, int mx, int my, float partial) {
            g.fill(0, 0, this.width, this.height, 0xFF202028);
            g.renderTooltip(this.font, this.stack, 6, 14);
            // the CI client draws only a few frames a second: the popup watcher closes a screen after 100 ticks
            if (++this.frames == 6) {
                shot(Minecraft.getInstance(), this.name);
            } else if (this.frames == 10) {
                Minecraft.getInstance().setScreen(null);
            }
        }

        @Override
        public boolean isPauseScreen() {
            return false;
        }
    }

    /** (058) The player on the stage with the relic weapon, a husk ten blocks before it, seen from behind. */
    private static void relicStage(Minecraft mc, String weapon) {
        IntegratedServer server = mc.getSingleplayerServer();
        mc.options.hideGui = true;
        mc.options.setCameraType(net.minecraft.client.CameraType.THIRD_PERSON_BACK);
        mc.player.getAbilities().flying = false;
        net.minecraft.world.item.ItemStack stack = r(weapon);
        String name = mc.player.getGameProfile().getName();
        server.execute(() -> {
            ServerLevel level = server.overworld();
            clearStage(level);
            // the throne scene left the player a spectator: a technique is never readied by one
            command(server, "gamemode creative " + name);
            command(server, "weather clear 1000000");
            command(server, "time set noon");
            command(server, String.format(java.util.Locale.ROOT, "tp %s %.2f %.2f %.2f 0 8", name, sx, sy + 0.1, sz + 2));
            ServerPlayer sp = server.getPlayerList().getPlayerByName(name);
            if (sp != null) {
                sp.getAbilities().flying = false;
                sp.onUpdateAbilities();
                sp.setItemInHand(InteractionHand.MAIN_HAND, stack.copy());
                sp.setHealth(sp.getMaxHealth());
            }
            net.minecraft.world.entity.Mob d = net.minecraft.world.entity.EntityType.HUSK.create(level);
            if (d != null) {
                d.moveTo(sx, (int) sy, sz + 9, 180F, 0F);
                d.setNoAi(true);
                d.setPersistenceRequired();
                d.addTag("oror_look");
                level.addFreshEntity(d);
            }
        });
    }

    private static void relicStart(Minecraft mc, int slot) {
        IntegratedServer server = mc.getSingleplayerServer();
        String name = mc.player.getGameProfile().getName();
        server.execute(() -> {
            try {
                ServerPlayer sp = server.getPlayerList().getPlayerByName(name);
                Object ok = Class.forName("jp.oror.reborn.relic.RelicTech").getMethod("start", ServerPlayer.class, int.class, boolean.class)
                    .invoke(null, sp, slot, true);
                note("relic technique " + slot + " started: " + ok);
            } catch (ReflectiveOperationException | RuntimeException ex) {
                note("relic start: " + ex);
            }
        });
    }

    /** (057) The character alone on the stage (z + 10, facing the camera's side), a husk before it. */
    private static void wazaStage(Minecraft mc, String character) {
        IntegratedServer server = mc.getSingleplayerServer();
        mc.options.hideGui = true;
        server.execute(() -> {
            ServerLevel level = server.overworld();
            clearStage(level);
            for (Entity e : level.getEntities((Entity) null, new AABB(sx - 48, sy - 12, sz - 24, sx + 48, sy + 40, sz + 48),
                x -> x.getTags().contains("oror_look") || x.getTags().contains("oror_azazel"))) {
                e.discard();
            }
            command(server, "weather clear 1000000");
            command(server, "time set noon");
            try {
                java.util.Map<?, ?> types = (java.util.Map<?, ?>) Class.forName("jp.oror.reborn.OrorReborn").getField("TYPES").get(null);
                Object holder = types.get(character);
                net.minecraft.world.entity.EntityType<?> type = (net.minecraft.world.entity.EntityType<?>) holder.getClass().getMethod("get").invoke(holder);
                Entity e = type.create(level);
                if (e instanceof net.minecraft.world.entity.Mob m) {
                    m.moveTo(sx, (int) sy, sz + 10, 180F, 0F);
                    m.setYHeadRot(180F);
                    m.setYBodyRot(180F);
                    m.setPersistenceRequired();
                    m.addTag("oror_look");
                    level.addFreshEntity(m);
                    Class.forName("jp.oror.reborn.waza.WazaEngine").getMethod("testMode", Class.forName("jp.oror.reborn.SupremeEntity"), boolean.class)
                        .invoke(null, m, true);
                    wazaCaster = m;
                }
                net.minecraft.world.entity.Mob d = net.minecraft.world.entity.EntityType.HUSK.create(level);
                if (d != null) {
                    d.moveTo(sx, (int) sy, sz + 10 - 4.5 - (wazaCaster == null ? 0 : wazaCaster.getBbWidth() * 0.5), 0F, 0F);
                    d.setNoAi(true);
                    d.setPersistenceRequired();
                    d.addTag("oror_look");
                    d.addTag("oror_waza_dummy");
                    level.addFreshEntity(d);
                    wazaDummy = d;
                }
            } catch (ReflectiveOperationException | RuntimeException ex) {
                note("waza stage " + character + ": " + ex);
            }
        });
    }

    /** (057) The camera at the character's right front, back far enough for its size. */
    private static void wazaView(Minecraft mc) {
        float h = wazaCaster == null ? 2F : wazaCaster.getBbHeight();
        double back = 5 + h * 1.6;
        view(mc, back * 0.55, 1.2 + h * 0.55, 10 - back * 0.85, 33F, 8F);
    }

    private static void wazaStart(Minecraft mc, String id) {
        IntegratedServer server = mc.getSingleplayerServer();
        server.execute(() -> {
            try {
                Class<?> book = Class.forName("jp.oror.reborn.waza.Waza");
                Object w = ((java.util.Map<?, ?>) book.getField("BY_ID").get(null)).get(id);
                Class.forName("jp.oror.reborn.waza.WazaEngine").getMethod("start", Class.forName("jp.oror.reborn.SupremeEntity"), book,
                    net.minecraft.world.entity.LivingEntity.class, boolean.class).invoke(null, wazaCaster, w, wazaDummy, true);
                note("waza " + id + " started on " + (wazaCaster == null ? "-" : wazaCaster.getName().getString()));
            } catch (ReflectiveOperationException | RuntimeException ex) {
                note("waza start " + id + ": " + ex);
            }
        });
    }

    /** (056) Azazel (an evoker made the rebel lord) alone on the stage, facing the camera's side. */
    private static void soloAzazel(Minecraft mc) {
        IntegratedServer server = mc.getSingleplayerServer();
        mc.options.hideGui = true;
        server.execute(() -> {
            ServerLevel level = server.overworld();
            clearStage(level);
            command(server, "weather clear 1000000");
            command(server, "time set noon");
            net.minecraft.world.entity.monster.Evoker ev = net.minecraft.world.entity.EntityType.EVOKER.create(level);
            if (ev == null) {
                return;
            }
            ev.moveTo(sx, (int) sy, sz + 10, 180F, 0F);
            ev.setYHeadRot(180F);
            ev.setYBodyRot(180F);
            ev.setNoAi(true);
            ev.setInvulnerable(true);
            ev.setPersistenceRequired();
            ev.addTag("oror_look");
            ev.addTag("oror_azazel");
            try {
                Class.forName("jp.oror.reborn.king.RebelLord").getMethod("makeLord", net.minecraft.world.entity.Mob.class, boolean.class).invoke(null, ev, false);
            } catch (ReflectiveOperationException | RuntimeException ex) {
                note("azazel: " + ex);
            }
            level.addFreshEntity(ev);
            note(String.format(java.util.Locale.ROOT, "azazel on the stage: scale %.2f, name %s", ev.getScale(), ev.getCustomName() == null ? "-" : ev.getCustomName().getString()));
        });
    }

    /**
     * (056) Everything but the player taken off the stage: the soldiers, mages and creatures of the earlier scenes
     * (in the first look at the new Azazel they were still there, and set on him the moment he stood: he was not seen).
     */
    private static void clearStage(ServerLevel level) {
        for (Entity e : level.getEntities((Entity) null, new AABB(sx - 80, sy - 16, sz - 48, sx + 80, sy + 48, sz + 80),
            x -> !(x instanceof net.minecraft.world.entity.player.Player) && !x.getTags().contains("oror_azazel")
                && (x instanceof net.minecraft.world.entity.LivingEntity || x instanceof net.minecraft.world.entity.projectile.Projectile
                    || x instanceof net.minecraft.world.entity.item.ItemEntity || x instanceof net.minecraft.world.entity.LightningBolt
                    || x instanceof net.minecraft.world.entity.ExperienceOrb || x instanceof net.minecraft.world.entity.projectile.EvokerFangs))) {
            e.discard();
        }
    }

    /** (056) What the client draws Azazel with (his name is seen by the client; his tags are not), and where he stands. */
    private static void azazelSeen(Minecraft mc) {
        List<String> lines = new ArrayList<>();
        for (Entity e : mc.level.entitiesForRendering()) {
            if (e.getCustomName() != null && e.getCustomName().getString().contains("アザゼル")) {
                lines.add(String.format(java.util.Locale.ROOT, "%s at %.1f %.1f %.1f alive %s -> %s", e.getCustomName().getString(), e.getX() - sx,
                    e.getY() - sy, e.getZ() - sz, e.isAlive(), mc.getEntityRenderDispatcher().getRenderer(e).getClass().getName()));
            }
        }
        note("azazel seen: " + lines);
    }

    /** (056) One of Azazel's arts sent to him as the server sends it (its motion only: no one is struck). */
    private static void azazelArt(Minecraft mc, String id, int windup, int length) {
        IntegratedServer server = mc.getSingleplayerServer();
        server.execute(() -> {
            ServerLevel level = server.overworld();
            clearStage(level);
            for (Entity e : level.getEntities((Entity) null, new AABB(sx - 5, sy - 3, sz + 5, sx + 5, sy + 12, sz + 15),
                x -> x.getTags().contains("oror_azazel"))) {
                try {
                    Class.forName("jp.oror.reborn.show.TechniqueShow").getMethod("send", Entity.class, String.class, int.class, int.class, int.class, int.class)
                        .invoke(null, e, "move:azazel_" + id, 0, windup, length, -1);
                } catch (ReflectiveOperationException | RuntimeException ex) {
                    note("azazel art " + id + ": " + ex);
                }
            }
        });
    }

    /** (055) One villager king alone on the stage in a form and stance. */
    private static void soloKing(Minecraft mc, int phase, int stance, float life) {
        IntegratedServer server = mc.getSingleplayerServer();
        mc.options.hideGui = true;
        server.execute(() -> {
            // the kings of the earlier scenes taken away outright: /kill only sends them back from death (they
            // return), and the divine one's storm stopped, so that one king alone stands in clear daylight
            ServerLevel level = server.overworld();
            for (Entity e : level.getEntities((Entity) null, new AABB(sx - 48, sy - 12, sz - 24, sx + 48, sy + 40, sz + 48),
                x -> x.getTags().contains("oror_look") || x.getType().toString().contains("villager_king")
                    || x instanceof net.minecraft.world.entity.monster.Vex || x instanceof net.minecraft.world.entity.LightningBolt)) {
                e.discard();
            }
            command(server, "weather clear 1000000");
            command(server, "time set noon");
            command(server, String.format(java.util.Locale.ROOT,
                "summon oror_supreme_bosses:villager_king %.1f %d %.1f {NoAI:1b,PersistenceRequired:1b,Rotation:[180f,0f],Tags:[\"oror_look\",\"oror_king_solo\"]}",
                sx, (int) sy, sz + 10));
            for (Entity e : level.getEntities((Entity) null, new AABB(sx - 5, sy - 3, sz + 5, sx + 5, sy + 12, sz + 15),
                x -> x.getTags().contains("oror_king_solo"))) {
                setForm(level, e, phase, stance, life, false);
            }
        });
    }

    /** (055) A move sent to the king on the stage, as the server sends it when he does it. */
    private static void kingMove(Minecraft mc, String id, int windup, int length) {
        IntegratedServer server = mc.getSingleplayerServer();
        server.execute(() -> {
            ServerLevel level = server.overworld();
            for (Entity e : level.getEntities((Entity) null, new AABB(sx - 5, sy - 3, sz + 5, sx + 5, sy + 12, sz + 15),
                x -> x.getTags().contains("oror_king_solo"))) {
                try {
                    Class.forName("jp.oror.reborn.show.TechniqueShow").getMethod("send", Entity.class, String.class, int.class, int.class, int.class, int.class)
                        .invoke(null, e, "move:king_" + id, 0, windup, length, -1);
                } catch (ReflectiveOperationException | RuntimeException ex) {
                    note("king move " + id + ": " + ex);
                }
            }
        });
    }

    /** (055) Baal Zebul's veil of flies about the king on the stage. */
    private static void kingVeil(Minecraft mc) {
        IntegratedServer server = mc.getSingleplayerServer();
        server.execute(() -> {
            ServerLevel level = server.overworld();
            for (Entity e : level.getEntities((Entity) null, new AABB(sx - 5, sy - 3, sz + 5, sx + 5, sy + 12, sz + 15),
                x -> x.getTags().contains("oror_king_solo"))) {
                try {
                    Class<?> mobC = Class.forName("jp.oror.reborn.royal.RoyalMob");
                    Class.forName("jp.oror.reborn.king.KingSouls").getMethod("veil", mobC, ServerLevel.class, int.class).invoke(null, e, level, 240);
                    note("veil of flies cast");
                } catch (ReflectiveOperationException | RuntimeException ex) {
                    note("king veil: " + ex);
                }
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
        if (screen.getClass().getSimpleName().equals("PactScreen") && onScreen == 20) {
            // (057) a contract offered: photographed, then refused by closing it (nothing is owed)
            shot(mc, "62_pact_screen");
            screen.onClose();
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
