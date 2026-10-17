import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Parses rigs.json with Gson into the same classes RigModel.load uses, so a schema mismatch (e.g. a non-numeric
 *  bone param) fails here instead of at resource reload in the game. Also checks the referenced files exist. */
public class RigsCheck {
    static final class Rig { String texture; String mesh; int[] size; float height; boolean translucent; List<Bone> bones; }
    static final class Bone { String name; String parent; float[] at; float[] rot; String anim; Map<String, Float> p; List<Cube> cubes; }
    static final class Cube { int[] uv; float[] o; float[] s; }

    public static void main(String[] a) throws Exception {
        File root = new File(a[0]);
        Map<String, Rig> rigs;
        try (Reader r = new InputStreamReader(new FileInputStream(new File(root, "rigs.json")), StandardCharsets.UTF_8)) {
            rigs = new Gson().fromJson(r, new TypeToken<Map<String, Rig>>() {}.getType());
        }
        int bad = 0;
        for (Map.Entry<String, Rig> e : rigs.entrySet()) {
            Rig rig = e.getValue();
            Set<String> names = new HashSet<>();
            for (Bone b : rig.bones) {
                if (b.name == null || !names.add(b.name)) { System.out.println(e.getKey() + ": bad/duplicate bone " + b.name); bad++; }
                if (b.parent != null && !names.contains(b.parent)) { System.out.println(e.getKey() + ": parent after child " + b.name); bad++; }
                if (b.at == null || b.at.length != 3 || b.rot == null || b.rot.length != 3) { System.out.println(e.getKey() + ": bone transform " + b.name); bad++; }
            }
            if (!new File(root, "textures/entity/" + rig.texture + ".png").exists()) { System.out.println(e.getKey() + ": missing texture"); bad++; }
            if (rig.mesh != null && !new File(root, "meshes/" + rig.mesh + ".bin").exists()) { System.out.println(e.getKey() + ": missing mesh"); bad++; }
        }
        System.out.println(rigs.size() + " rigs parsed like RigModel, problems: " + bad);
        if (bad > 0) System.exit(1);
    }
}
