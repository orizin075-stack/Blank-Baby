import java.io.*;
import java.nio.file.*;
import java.util.*;

/** Parses meshes/*.bin exactly like RigModel.loadMesh and checks counts, index ranges and uv/normal ranges. */
public class MeshCheck {
    public static void main(String[] a) throws Exception {
        int bad = 0, files = 0;
        String rigs = new String(Files.readAllBytes(Paths.get(a[0], "rigs.json")));
        for (Path p : Files.newDirectoryStream(Paths.get(a[0], "meshes"))) {
            files++;
            String key = p.getFileName().toString().replace(".bin", "");
            try (DataInputStream in = new DataInputStream(new BufferedInputStream(new FileInputStream(p.toFile())))) {
                int magic = in.readInt(), bones = in.readInt();
                if (magic != 0x4F524D33) { System.out.println(key + " bad magic"); bad++; continue; }
                long quads = 0, glow = 0;
                float minY = 1e9f, maxY = -1e9f;
                for (int b = 0; b < bones; b++) {
                    int vc = in.readInt();
                    if (vc == 0) continue;
                    for (int i = 0; i < vc; i++) {
                        float x = in.readShort() / 512f, y = in.readShort() / 512f, z = in.readShort() / 512f;
                        float u = in.readChar() / 65535f, v = in.readChar() / 65535f;
                        float nx = in.readByte() / 127f, ny = in.readByte() / 127f, nz = in.readByte() / 127f;
                        if (u < 0 || u > 1 || v < 0 || v > 1) { bad++; }
                        float nl = (float) Math.sqrt(nx * nx + ny * ny + nz * nz);
                        if (nl < 0.8f || nl > 1.2f) { bad++; }
                    }
                    int q = in.readInt() * 4;
                    for (int i = 0; i < q; i++) if (in.readChar() >= vc) { bad++; }
                    int g = in.readInt() * 4;
                    for (int i = 0; i < g; i++) if (in.readChar() >= vc) { bad++; }
                    quads += q / 4; glow += g / 4;
                }
                if (in.read() != -1) { System.out.println(key + " trailing bytes"); bad++; }
                int idx = rigs.indexOf("\"" + key + "\":");
                System.out.println(key + ": bones " + bones + ", quads " + quads + ", glow " + glow + (idx < 0 ? "  NOT IN rigs.json" : ""));
            }
        }
        System.out.println(files + " files, problems: " + bad);
    }
}
