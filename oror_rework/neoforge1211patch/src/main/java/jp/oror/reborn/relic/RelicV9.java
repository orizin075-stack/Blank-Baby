package jp.oror.reborn.relic;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * (058) The 164 relics as the V9 design describes them (assets/oror_supreme_bosses/relic_v9.json, made by
 * tools/v9/build_v9.py from the design text): each relic's tooltip, the punishment its hits may draw, the enchantments a
 * reward carries, a charm's crisis guard, a legend's crowning attack, and the 123 techniques of the weapons.
 */
public final class RelicV9 {
    private RelicV9() {
    }

    /** One tooltip line: its colour's name and its text. */
    public record Line(String style, String text) {
    }

    public static final class Info {
        public String id, slot, character, god, name;
        public List<Line> summary = List.of(), detail = List.of();
        /** The punishment a hit may draw: effect name, chance, ticks (weapons and legends). */
        public String procEffect;
        public double procChance;
        public int procTicks;
        public List<String[]> enchants = List.of();
        public JsonObject crisis, ultimate;
    }

    public static final class Tech {
        public int index, slot, damage, range, cd, color;
        public String id, relic, character, name, label, kind, motion, effect;
        public int[] wind = {10, 10};
        public JsonObject tele;
        public List<String> anim = List.of();
        public List<JsonObject> prog = List.of();

        /** Ticks from the key to the release: the stance and the aim (Ⅰ), the build (Ⅱ), the omen (the finisher). */
        public int windup() {
            return this.slot == 2 ? this.wind[0] : this.wind[0] + this.wind[1];
        }

        /** Ticks the technique's own moments may still run after its release (the finisher's forming). */
        public int forming() {
            return this.slot == 2 ? this.wind[1] : 0;
        }
    }

    public static final Map<String, Info> RELICS;
    public static final List<Tech> TECHS;
    private static final Map<String, Tech[]> BY_WEAPON = new HashMap<>();

    static {
        Map<String, Info> relics = new LinkedHashMap<>();
        List<Tech> techs = new ArrayList<>();
        try (InputStream in = RelicV9.class.getResourceAsStream("/assets/oror_supreme_bosses/relic_v9.json")) {
            if (in != null) {
                JsonObject top = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
                JsonObject rs = top.getAsJsonObject("relics");
                for (String id : rs.keySet()) {
                    JsonObject o = rs.getAsJsonObject(id);
                    Info i = new Info();
                    i.id = id;
                    i.slot = str(o, "slot");
                    i.character = str(o, "character");
                    i.god = str(o, "god");
                    i.name = str(o, "name");
                    i.summary = lines(o.getAsJsonArray("summary"));
                    i.detail = lines(o.getAsJsonArray("detail"));
                    if (o.has("proc")) {
                        JsonObject p = o.getAsJsonObject("proc");
                        i.procEffect = p.get("e").getAsString();
                        i.procChance = p.get("p").getAsDouble();
                        i.procTicks = p.get("t").getAsInt();
                    }
                    if (o.has("enchants")) {
                        List<String[]> l = new ArrayList<>();
                        for (JsonElement e : o.getAsJsonArray("enchants")) {
                            JsonArray a = e.getAsJsonArray();
                            l.add(new String[]{a.get(0).getAsString(), a.get(1).getAsString()});
                        }
                        i.enchants = l;
                    }
                    i.crisis = o.has("crisis") ? o.getAsJsonObject("crisis") : null;
                    i.ultimate = o.has("ultimate") ? o.getAsJsonObject("ultimate") : null;
                    relics.put(id, i);
                }
                for (JsonElement e : top.getAsJsonArray("techs")) {
                    JsonObject o = e.getAsJsonObject();
                    Tech t = new Tech();
                    t.index = o.get("index").getAsInt();
                    t.id = str(o, "id");
                    t.relic = str(o, "relic");
                    t.character = str(o, "character");
                    t.slot = o.get("slot").getAsInt();
                    t.name = str(o, "name");
                    t.label = str(o, "label");
                    t.damage = o.get("damage").getAsInt();
                    t.range = o.get("range").getAsInt();
                    t.cd = o.get("cd").getAsInt();
                    t.color = o.get("color").getAsInt();
                    t.kind = str(o, "kind");
                    t.motion = str(o, "motion");
                    t.effect = str(o, "effect");
                    JsonArray w = o.getAsJsonArray("wind");
                    t.wind = new int[]{w.get(0).getAsInt(), w.get(1).getAsInt()};
                    t.tele = o.getAsJsonObject("tele");
                    List<String> anim = new ArrayList<>();
                    for (JsonElement a : o.getAsJsonArray("anim")) {
                        anim.add(a.getAsString());
                    }
                    t.anim = anim;
                    List<JsonObject> prog = new ArrayList<>();
                    for (JsonElement p : o.getAsJsonArray("prog")) {
                        prog.add(p.getAsJsonObject());
                    }
                    t.prog = prog;
                    techs.add(t);
                    BY_WEAPON.computeIfAbsent(t.relic, k -> new Tech[3])[t.slot] = t;
                }
            }
        } catch (Exception ex) {
            throw new IllegalStateException("Invalid relic_v9.json", ex);
        }
        RELICS = Collections.unmodifiableMap(relics);
        TECHS = Collections.unmodifiableList(techs);
    }

    private static String str(JsonObject o, String k) {
        return o.has(k) ? o.get(k).getAsString() : "";
    }

    private static List<Line> lines(JsonArray a) {
        List<Line> l = new ArrayList<>();
        if (a != null) {
            for (JsonElement e : a) {
                JsonArray x = e.getAsJsonArray();
                l.add(new Line(x.get(0).getAsString(), x.get(1).getAsString()));
            }
        }
        return l;
    }

    public static Info info(String id) {
        return id == null ? null : RELICS.get(id);
    }

    /** The weapon's three techniques (特殊技Ⅰ, Ⅱ, 必殺技), or null for a relic that is no weapon. */
    public static Tech[] of(String weaponId) {
        return weaponId == null ? null : BY_WEAPON.get(weaponId);
    }

    public static Tech tech(int index) {
        return index >= 0 && index < TECHS.size() ? TECHS.get(index) : null;
    }
}
