package jp.oror.reborn;

import com.google.gson.Gson;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class CharacterSpec {
    public String id;
    public String name;
    public String model;
    public String ability;
    public String behavior;
    public float width;
    public float height;
    public float health;
    public float damage;
    public float mana;
    public float regen;
    public float speed;
    public float loreHealth;
    public float loreMana;
    public int cooldown;
    public int skin;
    public int hair;
    public int outfit;
    public int accent;
    public List<String> features;
    public static final Map<String, CharacterSpec> ALL = load();

    public boolean airborne() {
        return this.model.equals("dragon") || this.model.equals("machine");
    }

    public boolean aquatic() {
        return this.model.equals("sea") || this.model.equals("whale");
    }

    private static Map<String, CharacterSpec> load() {
        try {
            Map var10;
            try (InputStream in = CharacterSpec.class.getResourceAsStream("/assets/oror_supreme_bosses/characters.json")) {
                if (in == null) {
                    throw new IllegalStateException("Missing roster");
                }

                CharacterSpec[] a = (CharacterSpec[])new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), CharacterSpec[].class);
                LinkedHashMap<String, CharacterSpec> m = new LinkedHashMap<>();

                for (CharacterSpec s : a) {
                    if (!s.id.matches("[a-z0-9_]+")
                        || m.putIfAbsent(s.id, s) != null
                        || s.health <= 0.0F
                        || s.health > 1024.0F
                        || s.cooldown < 20
                        || s.mana <= 0.0F) {
                        throw new IllegalStateException("Invalid " + s.id);
                    }
                }

                if (m.size() != 41) {
                    throw new IllegalStateException("Expected 41 characters");
                }

                var10 = Collections.unmodifiableMap(m);
            }

            return var10;
        } catch (IOException var9) {
            throw new ExceptionInInitializerError(var9);
        }
    }
}
