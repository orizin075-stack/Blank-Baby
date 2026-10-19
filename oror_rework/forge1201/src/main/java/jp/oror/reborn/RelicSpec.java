package jp.oror.reborn;

import com.google.gson.Gson;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;

public final class RelicSpec {
    public String id;
    public String character;
    public String name;
    public String slot;
    public String description;
    public int rank;
    public int color;
    public int cooldown;
    public float damage;
    public static final Map<String, RelicSpec> ALL = load();

    private static Map<String, RelicSpec> load() {
        try {
            Map var10;
            try (InputStream in = RelicSpec.class.getResourceAsStream("/assets/oror_supreme_bosses/relics.json")) {
                if (in == null) {
                    throw new IllegalStateException("Missing relics");
                }

                RelicSpec[] rows = (RelicSpec[])new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), RelicSpec[].class);
                LinkedHashMap<String, RelicSpec> out = new LinkedHashMap<>();

                for (RelicSpec s : rows) {
                    if (!CharacterSpec.ALL.containsKey(s.character) || out.putIfAbsent(s.id, s) != null || s.rank < 1 || s.rank > 3) {
                        throw new IllegalStateException("Invalid relic " + s.id);
                    }
                }

                if (out.size() != 164) {
                    throw new IllegalStateException("Expected 164 relics");
                }

                var10 = Collections.unmodifiableMap(out);
            }

            return var10;
        } catch (IOException var9) {
            throw new ExceptionInInitializerError(var9);
        }
    }
}
