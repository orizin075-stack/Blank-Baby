import com.google.gson.Gson;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Loads characters.json with Gson into the same field types as CharacterSpec and applies its validation. */
public class RosterCheck {
    static class Spec { String id, name, model, ability, behavior; float width, height, health, damage, mana, regen, speed, loreHealth, loreMana; int cooldown, skin, hair, outfit, accent; List<String> features; }
    public static void main(String[] a) throws Exception {
        Spec[] all = new Gson().fromJson(new InputStreamReader(new FileInputStream(a[0]), StandardCharsets.UTF_8), Spec[].class);
        Set<String> ids = new HashSet<>();
        for (Spec s : all) {
            if (!s.id.matches("[a-z0-9_]+") || !ids.add(s.id) || s.health <= 0 || s.health > 1024 || s.cooldown < 20 || s.mana <= 0) throw new IllegalStateException("Invalid " + s.id);
        }
        if (all.length != 41) throw new IllegalStateException("Expected 41 characters");
        System.out.println("ROSTER OK " + all.length);
    }
}
