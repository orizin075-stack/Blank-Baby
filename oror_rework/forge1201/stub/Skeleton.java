import com.sun.source.tree.*;
import com.sun.source.util.JavacTask;
import javax.lang.model.element.Modifier;
import javax.tools.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/**
 * Compile-only skeletons of real library sources: same packages, classes, generics, fields and method signatures,
 * bodies replaced by default returns. Only parses (no symbol resolution), so it runs on sources whose dependencies are
 * absent. Every class also gets a no-argument constructor so subclasses compile against it.
 *
 *   java Skeleton.java <out dir> <source files...>
 */
public class Skeleton {
    static StringBuilder out;

    public static void main(String[] args) throws Exception {
        Path outDir = Paths.get(args[0]);
        JavaCompiler jc = ToolProvider.getSystemJavaCompiler();
        StandardJavaFileManager fm = jc.getStandardFileManager(null, null, StandardCharsets.UTF_8);
        for (int i = 1; i < args.length; i++) {
            JavacTask task = (JavacTask) jc.getTask(null, fm, d -> {}, List.of("-proc:none"), null, fm.getJavaFileObjects(args[i]));
            for (CompilationUnitTree cu : task.parse()) {
                out = new StringBuilder();
                String pkg = cu.getPackageName() == null ? "" : cu.getPackageName().toString();
                out.append("package ").append(pkg).append(";\n\n");
                StringBuilder body = new StringBuilder();
                StringBuilder saved = out;
                out = body;
                for (Tree t : cu.getTypeDecls()) if (t instanceof ClassTree ct) klass(ct, "", false);
                out = saved;
                String text = body.toString();
                for (ImportTree imp : cu.getImports()) {
                    String q = imp.getQualifiedIdentifier().toString();
                    String simple = q.substring(q.lastIndexOf('.') + 1);
                    if (simple.equals("*") || text.matches("(?s).*\\b" + java.util.regex.Pattern.quote(simple) + "\\b.*"))
                        out.append("import ").append(imp.isStatic() ? "static " : "").append(q).append(";\n");
                }
                out.append("\n").append(text);
                Path f = outDir.resolve(pkg.replace('.', '/')).resolve(Paths.get(args[i]).getFileName());
                Files.createDirectories(f.getParent());
                Files.writeString(f, out.toString());
            }
        }
    }

    static String mods(ModifiersTree m, boolean dropFinal, boolean keepAnno) {
        StringBuilder s = new StringBuilder();
        if (keepAnno) for (AnnotationTree a : m.getAnnotations()) s.append(a).append(' ');
        for (Modifier x : m.getFlags()) {
            if (dropFinal && x == Modifier.FINAL) continue;
            if (x == Modifier.NATIVE || x == Modifier.SYNCHRONIZED || x == Modifier.TRANSIENT || x == Modifier.VOLATILE || x == Modifier.STRICTFP) continue;
            if (x == Modifier.SEALED || x == Modifier.NON_SEALED) continue;
            s.append(x).append(' ');
        }
        return s.toString();
    }

    static String dflt(Tree type) {
        String t = type == null ? "void" : type.toString();
        switch (t) {
            case "void": return "";
            case "boolean": return "return false;";
            case "byte": case "short": case "int": case "long": case "float": case "double": case "char": return "return 0;";
            default: return "return null;";
        }
    }

    static String init(Tree type) {
        String t = type.toString();
        switch (t) {
            case "boolean": return "false";
            case "byte": case "short": case "int": case "long": case "float": case "double": case "char": return "0";
            default: return "null";
        }
    }

    static void klass(ClassTree c, String ind, boolean nested) {
        Tree.Kind k = c.getKind();
        boolean iface = k == Tree.Kind.INTERFACE || k == Tree.Kind.ANNOTATION_TYPE;
        String kw = switch (k) {
            case INTERFACE -> "interface";
            case ENUM -> "enum";
            case ANNOTATION_TYPE -> "@interface";
            default -> "class"; // records become classes
        };
        String m = mods(c.getModifiers(), false, k == Tree.Kind.ANNOTATION_TYPE);
        if (k == Tree.Kind.RECORD) m = m.replace("static ", "") + (nested ? "static " : "");
        out.append(ind).append(m).append(kw).append(' ').append(c.getSimpleName());
        if (!c.getTypeParameters().isEmpty()) out.append("<").append(String.join(", ", c.getTypeParameters().stream().map(Object::toString).toList())).append(">");
        if (c.getExtendsClause() != null) out.append(" extends ").append(c.getExtendsClause());
        if (!c.getImplementsClause().isEmpty()) {
            out.append(iface ? " extends " : " implements ");
            out.append(String.join(", ", c.getImplementsClause().stream().map(Object::toString).toList()));
        }
        out.append(" {\n");
        String in = ind + "    ";
        if (k == Tree.Kind.ENUM) {
            List<String> consts = new ArrayList<>();
            for (Tree t : c.getMembers())
                if (t instanceof VariableTree v && v.getInitializer() instanceof NewClassTree nc && nc.getIdentifier().toString().equals(c.getSimpleName().toString()))
                    consts.add(v.getName().toString());
            out.append(in).append(String.join(", ", consts)).append(";\n");
        }
        boolean hasNoArg = false;
        if (k == Tree.Kind.RECORD) {
            // record components: accessors and a canonical constructor
            List<String> params = new ArrayList<>();
            for (Tree t : c.getMembers())
                if (t instanceof VariableTree v && !v.getModifiers().getFlags().contains(Modifier.STATIC)) {
                    out.append(in).append("public ").append(v.getType()).append(' ').append(v.getName()).append("() { ").append(dflt(v.getType())).append(" }\n");
                    params.add(v.getType() + " " + v.getName());
                }
            out.append(in).append("public ").append(c.getSimpleName()).append('(').append(String.join(", ", params)).append(") {}\n");
            hasNoArg = params.isEmpty();
        }
        for (Tree t : c.getMembers()) {
            if (t instanceof VariableTree v) {
                if (k == Tree.Kind.ENUM && v.getInitializer() instanceof NewClassTree nc && nc.getIdentifier().toString().equals(c.getSimpleName().toString())) continue;
                if (k == Tree.Kind.RECORD && !v.getModifiers().getFlags().contains(Modifier.STATIC)) continue;
                if (v.getModifiers().getFlags().contains(Modifier.PRIVATE)) continue;
                out.append(in).append(mods(v.getModifiers(), !iface, false)).append(v.getType()).append(' ').append(v.getName());
                if (iface) out.append(" = ").append(init(v.getType()));
                out.append(";\n");
            } else if (t instanceof MethodTree mt) {
                if (mt.getModifiers().getFlags().contains(Modifier.PRIVATE)) continue;
                boolean ctor = mt.getName().contentEquals("<init>");
                if (ctor && k == Tree.Kind.RECORD) continue;
                if (ctor && mt.getParameters().isEmpty()) hasNoArg = true;
                if (ctor && k == Tree.Kind.ENUM) continue;
                String mm = mods(mt.getModifiers(), false, false);
                // Forge's extension interfaces are implemented by patched Minecraft classes: their methods get bodies
                String cn = c.getSimpleName().toString();
                boolean forced = k == Tree.Kind.INTERFACE && (cn.startsWith("IForge") || cn.startsWith("ICapability") || cn.equals("INBTSerializable") || cn.equals("IConfigSpec"))
                    && mt.getBody() == null && !mt.getModifiers().getFlags().contains(Modifier.STATIC);
                if (forced) mm = mm.replace("abstract ", "") + "default ";
                // enum constants lose their bodies, so the enum's abstract methods get one
                if (k == Tree.Kind.ENUM) mm = mm.replace("abstract ", "");
                out.append(in).append(mm);
                if (!mt.getTypeParameters().isEmpty()) out.append("<").append(String.join(", ", mt.getTypeParameters().stream().map(Object::toString).toList())).append("> ");
                if (ctor) out.append(c.getSimpleName());
                else out.append(mt.getReturnType()).append(' ').append(mt.getName());
                out.append('(');
                List<String> ps = new ArrayList<>();
                for (VariableTree p : mt.getParameters()) ps.add(mods(p.getModifiers(), true, false) + p.getType() + " " + p.getName());
                out.append(String.join(", ", ps)).append(')');
                if (!mt.getThrows().isEmpty()) out.append(" throws ").append(String.join(", ", mt.getThrows().stream().map(Object::toString).toList()));
                boolean abs = k != Tree.Kind.ENUM && (mt.getModifiers().getFlags().contains(Modifier.ABSTRACT) || (iface && mt.getBody() == null));
                if (forced) abs = false;
                if (k == Tree.Kind.ANNOTATION_TYPE) {
                    out.append(mt.getDefaultValue() != null ? " default " + mt.getDefaultValue() : "").append(";\n");
                } else if (abs) out.append(";\n");
                else out.append(" { ").append(ctor ? "" : dflt(mt.getReturnType())).append(" }\n");
            } else if (t instanceof ClassTree inner) {
                if (inner.getModifiers().getFlags().contains(Modifier.PRIVATE)) continue;
                klass(inner, in, true);
            }
        }
        boolean anyCtor = c.getMembers().stream().anyMatch(t -> t instanceof MethodTree m2 && m2.getName().contentEquals("<init>"));
        // no constructor at all: the implicit one is public; otherwise a protected one lets subclasses compile
        if ((k == Tree.Kind.CLASS) && !hasNoArg) out.append(in).append(anyCtor ? "protected " : "public ").append(c.getSimpleName()).append("() {}\n");
        out.append(ind).append("}\n");
    }
}
