import com.sun.source.tree.*;
import com.sun.source.util.*;
import javax.tools.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Prints every @Override method: file, enclosing class, its extends/implements, name, parameter types as written. */
public class Overrides {
    public static void main(String[] a) throws Exception {
        JavaCompiler jc = ToolProvider.getSystemJavaCompiler();
        StandardJavaFileManager fm = jc.getStandardFileManager(null, null, StandardCharsets.UTF_8);
        List<Path> files = new ArrayList<>();
        try (var w = Files.walk(Paths.get(a[0]))) { w.filter(p -> p.toString().endsWith(".java")).forEach(files::add); }
        JavacTask t = (JavacTask) jc.getTask(null, fm, d -> {}, List.of("-proc:none"), null, fm.getJavaFileObjectsFromPaths(files));
        for (CompilationUnitTree cu : t.parse()) {
            new TreePathScanner<Void, String>() {
                Deque<String> sup = new ArrayDeque<>();
                @Override public Void visitClass(ClassTree c, String s) {
                    String e = c.getExtendsClause() == null ? "" : c.getExtendsClause().toString();
                    String i = String.join(",", c.getImplementsClause().stream().map(Object::toString).toList());
                    sup.push(c.getSimpleName() + " : " + e + (i.isEmpty() ? "" : " impl " + i));
                    super.visitClass(c, s); sup.pop(); return null;
                }
                @Override public Void visitNewClass(NewClassTree n, String s) {
                    if (n.getClassBody() != null) { sup.push("<anon> : " + n.getIdentifier()); scan(n.getClassBody().getMembers(), s); sup.pop(); scan(n.getArguments(), s); return null; }
                    return super.visitNewClass(n, s);
                }
                @Override public Void visitMethod(MethodTree m, String s) {
                    boolean ov = !m.getModifiers().getFlags().contains(javax.lang.model.element.Modifier.STATIC) && !m.getModifiers().getFlags().contains(javax.lang.model.element.Modifier.PRIVATE) && !m.getName().contentEquals("<init>");
                    if (ov) {
                        List<String> ps = new ArrayList<>();
                        for (VariableTree p : m.getParameters()) ps.add(p.getType().toString());
                        System.out.println(Paths.get(cu.getSourceFile().toUri()).getFileName() + "\t" + sup.peek() + "\t" + m.getName() + "(" + String.join(", ", ps) + ")");
                    }
                    return super.visitMethod(m, s);
                }
            }.scan(cu, "");
        }
    }
}
