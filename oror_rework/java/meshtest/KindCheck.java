import com.google.gson.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Parses weapon_kinds.json exactly as CharacterRelics' static initializer does and checks every reference resolves. */
public class KindCheck {
    public static void main(String[] a) throws Exception {
        JsonObject top = JsonParser.parseReader(new InputStreamReader(new FileInputStream(a[0]), StandardCharsets.UTF_8)).getAsJsonObject();
        JsonObject kinds = top.getAsJsonObject("kinds");
        Set<String> modes = Set.of("melee", "bolt", "gatling", "shell", "bow", "guard");
        for (String id : kinds.keySet()) {
            JsonObject o = kinds.getAsJsonObject(id);
            float speed = o.get("speed").getAsFloat(), mul = o.get("mul").getAsFloat();
            o.get("reach").getAsFloat(); o.get("knock").getAsFloat(); float shot = o.get("shot").getAsFloat();
            o.get("sweep").getAsBoolean(); String mode = o.get("mode").getAsString(); int gap = o.get("gap").getAsInt();
            if (!modes.contains(mode)) throw new IllegalStateException(id + " mode " + mode);
            if (!mode.equals("melee") && !mode.equals("guard") && shot <= 0) throw new IllegalStateException(id + " shot");
            if (speed + 4.0F <= 0 || mul <= 0) throw new IllegalStateException(id + " stats");
        }
        int n = 0;
        for (String g : new String[]{"characters", "fusion"}) {
            JsonObject m = top.getAsJsonObject(g);
            for (String k : m.keySet()) { n++; if (!kinds.has(m.get(k).getAsString())) throw new IllegalStateException(k + " -> " + m.get(k)); }
        }
        System.out.println("KINDS OK " + kinds.size() + " kinds, " + n + " assignments");
    }
}
