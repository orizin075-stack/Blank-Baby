import org.objectweb.asm.*;
import org.objectweb.asm.tree.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.stream.*;
import java.util.zip.*;

/** Verify recompiled classes: report external member refs never used by the original jar, and declaration diffs. */
public class Verify {
    static Map<String, ClassNode> read(Path jarOrDir) throws IOException {
        Map<String, ClassNode> m = new TreeMap<>();
        if (Files.isDirectory(jarOrDir)) {
            try (Stream<Path> s = Files.walk(jarOrDir)) {
                for (Path p : s.filter(x -> x.toString().endsWith(".class")).toList()) {
                    ClassNode cn = new ClassNode(); new ClassReader(Files.readAllBytes(p)).accept(cn, 0); m.put(cn.name, cn);
                }
            }
        } else try (ZipFile z = new ZipFile(jarOrDir.toFile())) {
            for (Enumeration<? extends ZipEntry> e = z.entries(); e.hasMoreElements();) {
                ZipEntry en = e.nextElement(); if (!en.getName().endsWith(".class")) continue;
                ClassNode cn = new ClassNode(); new ClassReader(z.getInputStream(en).readAllBytes()).accept(cn, 0); m.put(cn.name, cn);
            }
        }
        return m;
    }
    static Set<String> refs(ClassNode cn, Set<String> own) {
        Set<String> out = new TreeSet<>();
        for (MethodNode m : cn.methods) for (AbstractInsnNode in : m.instructions) {
            if (in instanceof MethodInsnNode mi && !own.contains(mi.owner) && !mi.owner.startsWith("java/")) out.add(mi.owner + "." + mi.name + mi.desc);
            else if (in instanceof FieldInsnNode fi && !own.contains(fi.owner) && !fi.owner.startsWith("java/")) out.add(fi.owner + "." + fi.name + ":" + fi.desc);
            else if (in instanceof InvokeDynamicInsnNode id) for (Object o : id.bsmArgs) if (o instanceof Handle h && !own.contains(h.getOwner()) && !h.getOwner().startsWith("java/")) out.add(h.getOwner() + "." + h.getName() + h.getDesc());
        }
        return out;
    }
    public static void main(String[] a) throws Exception {
        Map<String, ClassNode> orig = read(Path.of(a[0]));
        Map<String, ClassNode> neu = read(Path.of(a[1]));
        Set<String> own = new HashSet<>(orig.keySet()); own.addAll(neu.keySet());
        Set<String> known = new HashSet<>();
        for (ClassNode cn : orig.values()) known.addAll(refs(cn, own));
        Set<String> allow = new HashSet<>();
        if (a.length > 2) for (String l : Files.readAllLines(Path.of(a[2]))) if (!l.isBlank() && !l.startsWith("#")) allow.add(l.trim());
        Map<String, ClassNode> stubs = a.length > 3 ? read(Path.of(a[3])) : Map.of();
        Map<String, Set<String>> knownByMember = new HashMap<>();
        for (String k : known) { int i = k.indexOf('.'); knownByMember.computeIfAbsent(k.substring(i + 1), z -> new HashSet<>()).add(k.substring(0, i)); }
        int bad = 0;
        for (ClassNode cn : neu.values()) {
            for (String r : refs(cn, own)) {
                if (known.contains(r) || allow.contains(r)) continue;
                int i = r.indexOf('.'); String owner = r.substring(0, i), mem = r.substring(i + 1);
                boolean inherited = false;
                for (String cur = owner; cur != null && stubs.containsKey(cur) && !inherited; cur = stubs.get(cur).superName)
                    if (knownByMember.getOrDefault(mem, Set.of()).contains(cur)) inherited = true;
                if (inherited) { System.out.println("ok-inherited " + r); continue; }
                System.out.println("NEW-REF " + cn.name + " -> " + r); bad++;
            }
            if (cn.superName != null && !own.contains(cn.superName) && !cn.superName.startsWith("java/")) {
                ClassNode o = orig.get(cn.name);
                if (o == null || !cn.superName.equals(o.superName)) {
                    boolean seen = orig.values().stream().anyMatch(x -> cn.superName.equals(x.superName));
                    if (!seen && !allow.contains("SUPER " + cn.superName)) { System.out.println("NEW-SUPER " + cn.name + " extends " + cn.superName); bad++; }
                }
            }
            ClassNode o = orig.get(cn.name);
            if (o != null) {
                Set<String> om = o.methods.stream().map(x -> x.name + x.desc).collect(Collectors.toCollection(TreeSet::new));
                Set<String> nm = cn.methods.stream().map(x -> x.name + x.desc).collect(Collectors.toCollection(TreeSet::new));
                for (String s : om) if (!nm.contains(s) && !s.startsWith("lambda$")) System.out.println("REMOVED-METHOD " + cn.name + "." + s);
                for (MethodNode m : cn.methods) if ((m.access & Opcodes.ACC_BRIDGE) != 0 && !om.contains(m.name + m.desc)) System.out.println("NEW-BRIDGE " + cn.name + "." + m.name + m.desc);
            }
        }
        System.out.println(bad == 0 ? "VERIFY OK" : ("VERIFY: " + bad + " unknown refs"));
    }
}
