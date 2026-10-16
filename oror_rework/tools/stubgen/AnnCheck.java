import org.objectweb.asm.*;
import org.objectweb.asm.tree.*;
import java.nio.file.*;
import java.util.*;
import java.util.stream.*;
import java.util.zip.*;

/** Compare annotation visibility between the original jar and recompiled classes; list annotation types by retention. */
public class AnnCheck {
    static Map<String, ClassNode> read(Path p) throws Exception {
        Map<String, ClassNode> m = new TreeMap<>();
        if (Files.isDirectory(p)) {
            try (Stream<Path> s = Files.walk(p)) {
                for (Path f : s.filter(x -> x.toString().endsWith(".class")).toList()) {
                    ClassNode cn = new ClassNode(); new ClassReader(Files.readAllBytes(f)).accept(cn, 0); m.put(cn.name, cn);
                }
            }
        } else try (ZipFile z = new ZipFile(p.toFile())) {
            for (var e = z.entries(); e.hasMoreElements();) {
                ZipEntry en = e.nextElement(); if (!en.getName().endsWith(".class")) continue;
                ClassNode cn = new ClassNode(); new ClassReader(z.getInputStream(en).readAllBytes()).accept(cn, 0); m.put(cn.name, cn);
            }
        }
        return m;
    }
    static void add(Set<String> out, String where, List<AnnotationNode> l, String tag) { if (l != null) for (AnnotationNode a : l) out.add(where + " " + tag + " " + a.desc); }
    static Set<String> anns(ClassNode cn) {
        Set<String> s = new TreeSet<>();
        add(s, "class", cn.visibleAnnotations, "V"); add(s, "class", cn.invisibleAnnotations, "I");
        for (MethodNode m : cn.methods) { add(s, m.name + m.desc, m.visibleAnnotations, "V"); add(s, m.name + m.desc, m.invisibleAnnotations, "I"); }
        for (FieldNode f : cn.fields) { add(s, f.name, f.visibleAnnotations, "V"); add(s, f.name, f.invisibleAnnotations, "I"); }
        return s;
    }
    public static void main(String[] a) throws Exception {
        Map<String, ClassNode> orig = read(Path.of(a[0])), neu = read(Path.of(a[1]));
        Map<String, String> retention = new TreeMap<>();
        for (ClassNode cn : orig.values()) for (String s : anns(cn)) { String[] p = s.split(" "); retention.merge(p[2], p[1], (x, y) -> x.equals(y) ? x : "BOTH"); }
        System.out.println("annotation types in the original jar:");
        retention.forEach((k, v) -> System.out.println("  " + v + " " + k));
        int bad = 0;
        for (ClassNode cn : neu.values()) {
            Set<String> n = anns(cn);
            ClassNode o = orig.get(cn.name);
            if (o != null) {
                Set<String> want = anns(o);
                for (String s : want) if (!n.contains(s)) { System.out.println("MISSING " + cn.name + " :: " + s); bad++; }
            }
            for (String s : n) {
                String[] p = s.split(" ");
                String r = retention.get(p[2]);
                if (r != null && !r.equals(p[1]) && !r.equals("BOTH")) { System.out.println("WRONG-RETENTION " + cn.name + " :: " + s + " (original " + r + ")"); bad++; }
            }
        }
        System.out.println(bad == 0 ? "ANNOTATIONS OK" : "ANNOTATIONS: " + bad + " problems");
    }
}
