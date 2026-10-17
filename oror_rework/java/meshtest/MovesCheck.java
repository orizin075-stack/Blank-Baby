import com.google.gson.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Parses boss_moves.json the way BossMoves does; every move must be one BossMoves implements and every style known. */
public class MovesCheck {
    static final Set<String> MOVES = Set.of("dash_slash", "blink_strike", "combo_rush", "spin_slash", "blade_wave", "leap_slam", "uppercut",
        "ground_spikes", "nova", "vortex", "meteor", "beam", "homing_orbs", "arrow_rain", "bolt_barrage", "bullet_storm", "shell_barrage",
        "barrier", "chain_pull", "reap", "ricochet", "afterimage", "charge", "breath");
    static final Set<String> STYLES = Set.of("duelist", "brawler", "caster", "gunner", "juggernaut", "guardian", "flyer", "swimmer", "trickster", "rooted");
    public static void main(String[] a) throws Exception {
        JsonObject chars = JsonParser.parseReader(new InputStreamReader(new FileInputStream(a[0]), StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonObject("characters");
        JsonObject lang = JsonParser.parseReader(new InputStreamReader(new FileInputStream(a[1]), StandardCharsets.UTF_8)).getAsJsonObject();
        int n = 0;
        for (String id : chars.keySet()) {
            JsonObject o = chars.getAsJsonObject(id);
            if (!STYLES.contains(o.get("style").getAsString())) throw new IllegalStateException(id + " style");
            JsonArray m = o.getAsJsonArray("moves");
            for (int i = 0; i < m.size(); i++) {
                String mv = m.get(i).getAsString();
                if (!MOVES.contains(mv)) throw new IllegalStateException(id + " move " + mv);
                if (!lang.has("boss_move.oror_supreme_bosses." + id + "." + mv)) throw new IllegalStateException(id + " name " + mv);
                n++;
            }
        }
        if (chars.size() != 41) throw new IllegalStateException("characters " + chars.size());
        System.out.println("MOVES OK " + chars.size() + " characters, " + n + " moves");
    }
}
