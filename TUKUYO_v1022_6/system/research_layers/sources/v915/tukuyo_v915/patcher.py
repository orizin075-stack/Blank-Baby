import ast,copy,hashlib,random
BASE_SOURCE="""def choose(m):\n    a=m['ambiguous_failure']; b=m['representation_failure']\n    if a>0.30: return 'probe'\n    if b>0.30: return 'propose'\n    return 'hold'\n"""
ALLOWED_ACTIONS={'probe','propose','hold','audit'}
def source_sha(src): return hashlib.sha256(src.encode()).hexdigest()
def safe_source(src):
 try:t=ast.parse(src)
 except SyntaxError:return False
 banned=(ast.Import,ast.ImportFrom,ast.With,ast.Try,ast.Global,ast.Nonlocal,ast.ClassDef,ast.Lambda,ast.Attribute)
 if any(isinstance(n,banned) for n in ast.walk(t)):return False
 for n in ast.walk(t):
  if isinstance(n,ast.Call): return False
 return True
class Threshold(ast.NodeTransformer):
 def __init__(self,new=.20):self.new=new
 def visit_Constant(self,node):
  if isinstance(node.value,float) and abs(node.value-.30)<1e-9:return ast.copy_location(ast.Constant(self.new),node)
  return node
def patch_threshold(src):
 t=Threshold().visit(ast.parse(src));ast.fix_missing_locations(t);return ast.unparse(t)+'\n'
def patch_precedence(src):
 t=ast.parse(src);f=t.body[0];
 # locate assignments a,b then first if on a
 for n in f.body:
  if isinstance(n,ast.If) and isinstance(n.test,ast.Compare):
   left=n.test.left
   if isinstance(left,ast.Name) and left.id=='a':
    n.test=ast.BoolOp(op=ast.And(),values=[ast.Compare(left=ast.Name('a',ast.Load()),ops=[ast.GtE()],comparators=[ast.Name('b',ast.Load())]),n.test]);break
 ast.fix_missing_locations(t);return ast.unparse(t)+'\n'
def patch_audit(src):
 t=ast.parse(src);f=t.body[0]
 # add c assignment after first assignment statement, then audit before first if
 has_c=any(isinstance(n,ast.Name) and n.id=='c' for n in ast.walk(t))
 if has_c:return src
 assign=ast.Assign(targets=[ast.Name('c',ast.Store())],value=ast.Subscript(value=ast.Name('m',ast.Load()),slice=ast.Constant('consistency_failure'),ctx=ast.Load()))
 audit=ast.If(test=ast.Compare(left=ast.Name('c',ast.Load()),ops=[ast.Gt()],comparators=[ast.Constant(.22)]),body=[ast.Return(ast.Constant('audit'))],orelse=[])
 idx=0
 while idx<len(f.body) and isinstance(f.body[idx],ast.Assign):idx+=1
 f.body.insert(idx,assign);f.body.insert(idx+1,audit);ast.fix_missing_locations(t);return ast.unparse(t)+'\n'
def apply(src,kind):
 if kind=='threshold':return patch_threshold(src)
 if kind=='precedence':return patch_precedence(src)
 if kind=='audit':return patch_audit(src)
 raise ValueError(kind)
def run(src,m):
 if not safe_source(src):raise ValueError('unsafe')
 ns={'__builtins__':{}};exec(compile(src,'<candidate>','exec'),ns);return ns['choose'](m)
def truth(m):
 a=m['ambiguous_failure'];b=m['representation_failure'];c=m['consistency_failure']
 if c>.22:return 'audit'
 if a>=b and a>.20:return 'probe'
 if b>.20:return 'propose'
 return 'hold'
def rows(seed,n=400):
 r=random.Random(seed);return [{'ambiguous_failure':r.random()*.48,'representation_failure':r.random()*.48,'consistency_failure':r.random()*.35} for _ in range(n)]
def evaluate(src,seed,n=400):
 correct=wrong=0;cats={'missed_consistency':0,'wrong_priority':0,'missed_low_signal':0,'other':0}
 for m in rows(seed,n):
  try:p=run(src,m)
  except Exception:p='__INVALID__'
  t=truth(m)
  if p==t:correct+=1;continue
  if p not in ALLOWED_ACTIONS:wrong+=1
  if t=='audit':cats['missed_consistency']+=1
  elif t=='probe' and m['representation_failure']>m['ambiguous_failure']:cats['wrong_priority']+=1
  elif max(m['ambiguous_failure'],m['representation_failure'])>.20 and max(m['ambiguous_failure'],m['representation_failure'])<=.30:cats['missed_low_signal']+=1
  else:cats['other']+=1
 return {'correct':correct,'wrong':wrong,'n':n,'failures':cats}
def proposed_patch(summary,applied=()):
 # bounded mutation grammar; choice is driven by observed failure counts.
 opts=[]
 if 'audit' not in applied:opts.append(('audit',summary['failures']['missed_consistency']))
 if 'threshold' not in applied:opts.append(('threshold',summary['failures']['missed_low_signal']))
 if 'precedence' not in applied:opts.append(('precedence',summary['failures']['wrong_priority']+summary['failures']['other']))
 return max(opts,key=lambda x:(x[1],x[0]))[0] if opts else None
