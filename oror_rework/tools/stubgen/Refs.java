import org.objectweb.asm.*;
import org.objectweb.asm.tree.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;

/** Collects every external class/member referenced by a set of class files. Output: TSV lines. */
public class Refs {
    static Set<String> own = new HashSet<>();
    static TreeMap<String, TreeSet<String>> out = new TreeMap<>();
    static Map<String, ClassNode> byName = new HashMap<>();
    static String resolveOwn(String owner, String what) {
        // member referenced through a mod class but declared in an external ancestor
        if (what == null || !own.contains(owner)) return owner;
        String[] p = what.split(" ");
        if (p.length < 3 || p[0].startsWith("SUPER") || p[0].startsWith("IFACE")) return owner;
        String cur = owner;
        while (cur != null && own.contains(cur)) {
            ClassNode cn = byName.get(cur);
            boolean field = p[0].endsWith("F");
            if (field) { for (FieldNode f : cn.fields) if (f.name.equals(p[1])) return owner; }
            else { for (MethodNode m : cn.methods) if (m.name.equals(p[1]) && m.desc.equals(p[2])) return owner; }
            cur = cn.superName;
        }
        return cur == null ? owner : cur;
    }
    static void add(String owner, String what) {
        if (owner == null) return;
        owner = resolveOwn(owner, what);
        while (owner.startsWith("[")) owner = owner.substring(1);
        if (owner.startsWith("L") && owner.endsWith(";")) owner = owner.substring(1, owner.length() - 1);
        if (owner.length() == 1) return;
        if (own.contains(owner) || owner.startsWith("java/") || owner.startsWith("javax/") || owner.startsWith("jdk/") || owner.startsWith("sun/")) return;
        out.computeIfAbsent(owner, k -> new TreeSet<>());
        if (what != null) out.get(owner).add(what);
    }
    static void desc(String d) {
        if (d == null) return;
        Type t = Type.getType(d);
        if (t.getSort() == Type.METHOD) { desc(t.getReturnType().getDescriptor()); for (Type a : t.getArgumentTypes()) desc(a.getDescriptor()); }
        else if (t.getSort() == Type.OBJECT) add(t.getInternalName(), null);
        else if (t.getSort() == Type.ARRAY) desc(t.getElementType().getDescriptor());
    }
    public static void main(String[] a) throws Exception {
        List<ClassNode> nodes = new ArrayList<>();
        try (ZipFile z = new ZipFile(a[0])) {
            for (Enumeration<? extends ZipEntry> e = z.entries(); e.hasMoreElements();) {
                ZipEntry en = e.nextElement();
                if (!en.getName().endsWith(".class")) continue;
                ClassNode cn = new ClassNode();
                new ClassReader(z.getInputStream(en).readAllBytes()).accept(cn, 0);
                nodes.add(cn); own.add(cn.name); byName.put(cn.name, cn);
            }
        }
        for (ClassNode cn : nodes) {
            // overridable instance methods: declare on the first external ancestor with the same access
            String ext = cn.superName;
            while (ext != null && own.contains(ext)) ext = byName.get(ext).superName;
            if (ext != null && !ext.equals("java/lang/Object") && !ext.startsWith("java/") && !ext.startsWith("com/google/")) {
                for (MethodNode m : cn.methods) {
                    if ((m.access & (Opcodes.ACC_PRIVATE | Opcodes.ACC_STATIC | Opcodes.ACC_SYNTHETIC)) != 0) continue;
                    if (m.name.startsWith("<") || m.name.startsWith("lambda$") || m.desc.contains("Ljp/oror/")) continue;
                    String acc = (m.access & Opcodes.ACC_PROTECTED) != 0 ? "OVRP" : ((m.access & Opcodes.ACC_PUBLIC) != 0 ? "OVR" : null);
                    if (acc == null) continue;
                    out.computeIfAbsent(ext, k -> new TreeSet<>()).add(acc + " " + m.name + " " + m.desc);
                }
            }
            add(cn.superName, "SUPER_OF " + cn.name);
            for (String i : cn.interfaces) add(i, "IFACE_OF " + cn.name);
            if (cn.visibleAnnotations != null) for (AnnotationNode an : cn.visibleAnnotations) desc(an.desc);
            if (cn.invisibleAnnotations != null) for (AnnotationNode an : cn.invisibleAnnotations) desc(an.desc);
            for (FieldNode f : cn.fields) desc(f.desc);
            for (MethodNode m : cn.methods) {
                desc(m.desc);
                if (m.visibleAnnotations != null) for (AnnotationNode an : m.visibleAnnotations) desc(an.desc);
                if (m.invisibleAnnotations != null) for (AnnotationNode an : m.invisibleAnnotations) desc(an.desc);
                for (AbstractInsnNode in : m.instructions) {
                    if (in instanceof MethodInsnNode mi) {
                        String k = switch (mi.getOpcode()) { case Opcodes.INVOKESTATIC -> "SM"; case Opcodes.INVOKEINTERFACE -> "IM"; case Opcodes.INVOKESPECIAL -> "SP"; default -> "VM"; };
                        add(mi.owner, k + (mi.itf ? "I" : "") + " " + mi.name + " " + mi.desc);
                        desc(mi.desc);
                    } else if (in instanceof FieldInsnNode fi) {
                        String k = (fi.getOpcode() == Opcodes.GETSTATIC || fi.getOpcode() == Opcodes.PUTSTATIC) ? "SF" : "VF";
                        add(fi.owner, k + " " + fi.name + " " + fi.desc);
                        desc(fi.desc);
                    } else if (in instanceof TypeInsnNode ti) {
                        add(ti.desc, null);
                    } else if (in instanceof LdcInsnNode li && li.cst instanceof Type t) {
                        desc(t.getDescriptor());
                    } else if (in instanceof InvokeDynamicInsnNode id) {
                        desc(id.desc);
                        for (Object o : id.bsmArgs) {
                            if (o instanceof Handle h) {
                                String k = switch (h.getTag()) { case Opcodes.H_INVOKESTATIC -> "SM"; case Opcodes.H_INVOKEINTERFACE -> "IM"; case Opcodes.H_INVOKESPECIAL, Opcodes.H_NEWINVOKESPECIAL -> "SP"; default -> "VM"; };
                                add(h.getOwner(), k + (h.isInterface() ? "I" : "") + " " + h.getName() + " " + h.getDesc());
                                desc(h.getDesc());
                            } else if (o instanceof Type t) desc(t.getDescriptor());
                        }
                    } else if (in instanceof MultiANewArrayInsnNode ma) desc(ma.desc);
                }
                for (TryCatchBlockNode tc : m.tryCatchBlocks) if (tc.type != null) add(tc.type, null);
            }
        }
        try (PrintWriter w = new PrintWriter(a[1])) {
            for (var e : out.entrySet()) { w.println(e.getKey()); for (String s : e.getValue()) w.println("\t" + s); }
        }
        System.out.println("external classes: " + out.size());
    }
}
