package jp.oror.reborn.waza;

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
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * (057) One of the 984 techniques of the 41 characters (the design "41体984技・固有動作とサーバー判定 v2"), as
 * tools/t984/build_waza.py wrote it into waza/waza984.json: its timing (windup, active window, recovery, cooldown, in
 * ticks), its reach, the moments of its hits within the active window, its behaviour (the design's primary_behavior:
 * one of seventeen), the verbs its text asks for (what it does to whoever the behaviour reaches), its colours, sounds,
 * the props it grows on the body, the shape of its shots and its place in a chain.
 */
public record Waza(int index, String id, String character, int n, String name, int tier, Behaviour behaviour, int windup, int active,
                   int recovery, int cooldown, float range, int[] hits, List<String> verbs, String kind, int shape, int count, int[] colours,
                   String[] sounds, int props, int linkKind, int linkN, String[] particles, int[] arcs) {

    /** The design's primary behaviours. */
    public enum Behaviour {
        MELEE, PROJECTILE, BEAM, MOVE, GUARD, STATUS, FIELD, SUMMON, BUILD, HEAL, CONTROL, REWIND, ADAPT, CURSE, GROWTH, SONG, PACT;

        /** Attacks: their numbers are damage. Healing, guarding, contracts and the like never deal the attack value. */
        public boolean harms() {
            return switch (this) {
                case MELEE, PROJECTILE, BEAM, FIELD, SUMMON, CONTROL, CURSE, GROWTH, SONG -> true;
                default -> false;
            };
        }
    }

    public static final String[] TIER_NAMES = {"通常", "特殊", "大技", "必殺"};
    public static final String[] PROP_NAMES = {"halo", "crown", "robe", "tomes", "orb1", "orb2", "fruit1", "fruit2", "wheel", "core", "grip_r",
        "fin_r"};

    /** The active window, lengthened where a hit falls after it (v2: the window is extended rather than the hit lost). */
    public int activeLength() {
        int last = 0;
        for (int h : this.hits) {
            last = Math.max(last, h + 1);
        }
        return Math.max(Math.max(1, this.active), last);
    }

    public int length() {
        return this.windup + this.activeLength() + this.recovery;
    }

    public boolean has(String verb) {
        return this.verbs.contains(verb);
    }

    public boolean prop(String name) {
        for (int i = 0; i < PROP_NAMES.length; i++) {
            if (PROP_NAMES[i].equals(name)) {
                return (this.props & (1 << i)) != 0;
            }
        }
        return false;
    }

    // ------------------------------------------------------------------------------------------------------- the book

    public static final List<Waza> ALL;
    public static final Map<String, List<Waza>> BY_CHARACTER;
    public static final Map<String, Waza> BY_ID;
    /** The characters' direction, sound and shape lines (the design's 演出方針・音・色・造形), by id. */
    public static final Map<String, String[]> STYLE;
    private static final Set<String> SUPPORT = Set.of("HEAL_ALLY", "WARD", "HASTE", "MIGHT", "CLEANSE", "DEATHWARD", "INVIS");

    static {
        List<Waza> all = new ArrayList<>();
        Map<String, List<Waza>> by = new HashMap<>();
        Map<String, Waza> ids = new HashMap<>();
        Map<String, String[]> style = new HashMap<>();
        load("waza984.json", all, by, ids, style, true);
        if (all.size() != 984 || by.size() != 41 || by.values().stream().anyMatch(l -> l.size() != 24)) {
            throw new IllegalStateException("Expected 41 characters with 24 techniques each, got " + all.size() + " in " + by.size());
        }
        // (059c) the Villager King's four forms' and Azazel's V20 actions (tools/t984/v20_royal.py), after the 984
        load("waza_royal.json", all, by, ids, style, false);
        ALL = Collections.unmodifiableList(all);
        BY_CHARACTER = Collections.unmodifiableMap(by);
        BY_ID = Collections.unmodifiableMap(ids);
        STYLE = Collections.unmodifiableMap(style);
    }

    private static void load(String file, List<Waza> all, Map<String, List<Waza>> by, Map<String, Waza> ids, Map<String, String[]> style,
                             boolean required) {
        try (InputStream in = Waza.class.getResourceAsStream("/assets/oror_supreme_bosses/waza/" + file)) {
            if (in == null) {
                if (!required) {
                    return;
                }
                throw new IllegalStateException("Missing " + file);
            }
            JsonObject root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
            for (JsonElement c : root.getAsJsonArray("characters")) {
                JsonObject o = c.getAsJsonObject();
                style.put(o.get("id").getAsString(), new String[]{o.get("name").getAsString(), o.get("direction").getAsString(),
                    o.get("sound").getAsString(), o.get("shape").getAsString()});
            }
            int i = all.size();
            for (JsonElement e : root.getAsJsonArray("techniques")) {
                JsonArray a = e.getAsJsonArray();
                int[] hits = ints(a.get(11).getAsJsonArray());
                List<String> verbs = new ArrayList<>();
                for (JsonElement v : a.get(12).getAsJsonArray()) {
                    verbs.add(v.getAsString());
                }
                Behaviour b = Behaviour.valueOf(a.get(5).getAsString());
                if (b == Behaviour.HEAL) {
                    // healing reaches only its own side: it never carries a harmful verb
                    verbs.removeIf(v -> !SUPPORT.contains(v));
                }
                JsonArray cols = a.get(16).getAsJsonArray();
                int[] colours = new int[cols.size()];
                for (int k = 0; k < colours.length; k++) {
                    colours[k] = Integer.parseInt(cols.get(k).getAsString(), 16);
                }
                JsonArray snd = a.get(17).getAsJsonArray();
                String[] sounds = new String[snd.size()];
                for (int k = 0; k < sounds.length; k++) {
                    sounds[k] = snd.get(k).getAsString();
                }
                int props = 0;
                for (JsonElement p : a.get(18).getAsJsonArray()) {
                    props |= 1 << p.getAsInt();
                }
                int lk = -1, ln = -1;
                if (!a.get(19).isJsonNull()) {
                    lk = a.get(19).getAsJsonArray().get(0).getAsInt();
                    ln = a.get(19).getAsJsonArray().get(1).getAsInt();
                }
                JsonArray pa = a.get(20).getAsJsonArray();
                String[] particles = new String[pa.size()];
                for (int k = 0; k < particles.length; k++) {
                    particles[k] = pa.get(k).getAsString();
                }
                Waza w = new Waza(i++, a.get(0).getAsString(), a.get(1).getAsString(), a.get(2).getAsInt(), a.get(3).getAsString(),
                    a.get(4).getAsInt(), b, a.get(6).getAsInt(), a.get(7).getAsInt(), a.get(8).getAsInt(), a.get(9).getAsInt(),
                    a.get(10).getAsFloat(), hits, Collections.unmodifiableList(verbs), a.get(13).getAsString(), a.get(14).getAsInt(),
                    Math.max(1, Math.min(6, a.get(15).getAsInt())), colours, sounds, props, lk, ln, particles, ints(a.get(21).getAsJsonArray()));
                if (a.size() > 22 && !a.get(22).isJsonNull()) {
                    Casters.POWER.put(w.id(), a.get(22).getAsFloat());
                }
                all.add(w);
                by.computeIfAbsent(w.character(), k -> new ArrayList<>()).add(w);
                ids.put(w.id(), w);
            }
        } catch (Exception ex) {
            throw new IllegalStateException(file + ": " + ex, ex);
        }
    }

    private static int[] ints(JsonArray a) {
        int[] r = new int[a.size()];
        for (int i = 0; i < r.length; i++) {
            r[i] = a.get(i).getAsInt();
        }
        return r;
    }

    public static Waza of(int index) {
        return index >= 0 && index < ALL.size() ? ALL.get(index) : null;
    }

    /** The character's technique numbered n (1 to 24). */
    public static Waza of(String character, int n) {
        List<Waza> l = BY_CHARACTER.get(character);
        return l == null || n < 1 || n > l.size() ? null : l.get(n - 1);
    }
}
