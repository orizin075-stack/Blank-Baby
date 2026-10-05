import ast,subprocess,sys,json,tempfile,pathlib
ACTIONS={'probe','propose','hold','audit'};METRICS={'ambiguous_failure','representation_failure','consistency_failure'}
_ALLOWED=(ast.Module,ast.FunctionDef,ast.arguments,ast.arg,ast.Assign,ast.Name,ast.Store,ast.Load,ast.Subscript,ast.Constant,ast.If,ast.Compare,ast.Gt,ast.Return,ast.BoolOp,ast.And,ast.BinOp,ast.Add)
def safe_source(src):
 if not isinstance(src,str) or len(src)>8192:return False
 try:t=ast.parse(src)
 except SyntaxError:return False
 if any(not isinstance(n,_ALLOWED) for n in ast.walk(t)):return False
 fns=[n for n in t.body if isinstance(n,ast.FunctionDef)]
 if len(fns)!=1 or len(t.body)!=1 or fns[0].name!='choose' or [a.arg for a in fns[0].args.args]!=['m']:return False
 if sum(isinstance(n,ast.FunctionDef) for n in ast.walk(t))!=1:return False
 for n in ast.walk(t):
  if isinstance(n,ast.Name) and n.id not in {'m','a','b','c'}:return False
  if isinstance(n,ast.Subscript):
   if not isinstance(n.value,ast.Name) or n.value.id!='m' or not isinstance(n.slice,ast.Constant) or n.slice.value not in METRICS:return False
  if isinstance(n,ast.Constant):
   if isinstance(n.value,str) and n.value not in ACTIONS|METRICS:return False
   if isinstance(n.value,(int,float)) and abs(n.value)>10:return False
  if isinstance(n,ast.Return):
   if not isinstance(n.value,ast.Constant) or n.value.value not in ACTIONS:return False
 return True

def run_inproc(src,m):
 if not safe_source(src):raise ValueError('unsafe')
 ns={'__builtins__':{}};exec(compile(src,'<candidate>','exec'),ns);return ns['choose'](m)

def run_candidate(src,m,worker,timeout_s=.5):
 if not safe_source(src):return {'ok':False,'reason':'AST_REJECT'}
 with tempfile.NamedTemporaryFile('w',suffix='.py',delete=False) as f:f.write(src);p=f.name
 try:
  q=subprocess.run([sys.executable,str(worker),p,json.dumps(m)],capture_output=True,text=True,timeout=timeout_s)
  if q.returncode!=0:return {'ok':False,'reason':'PROCESS_FAIL'}
  d=json.loads(q.stdout);return {'ok':True,**d}
 except subprocess.TimeoutExpired:return {'ok':False,'reason':'TIMEOUT'}
 finally:pathlib.Path(p).unlink(missing_ok=True)
