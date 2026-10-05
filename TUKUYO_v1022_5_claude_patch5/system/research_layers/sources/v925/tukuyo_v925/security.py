import ast
ALLOWED=(ast.Module,ast.FunctionDef,ast.arguments,ast.arg,ast.Assign,ast.If,ast.Return,ast.Name,ast.Load,ast.Store,ast.Subscript,ast.Constant,ast.Compare,ast.Gt,ast.GtE,ast.Lt,ast.LtE,ast.And,ast.Or,ast.BoolOp,ast.BinOp,ast.Sub,ast.Add,ast.UnaryOp,ast.USub)
BANNED_NAMES={'eval','exec','open','compile','globals','locals','getattr','setattr','input','help','__import__'}
def inspect_source(src):
 try:t=ast.parse(src)
 except SyntaxError:return {'ok':False,'bad':['SYNTAX']}
 bad=[]
 for n in ast.walk(t):
  if not isinstance(n,ALLOWED):bad.append(type(n).__name__)
  if isinstance(n,ast.Name) and (n.id in BANNED_NAMES or n.id.startswith('__')):bad.append('NAME:'+n.id)
 fs=[n for n in t.body if isinstance(n,ast.FunctionDef)]
 all_fs=[n for n in ast.walk(t) if isinstance(n,ast.FunctionDef)]
 if len(fs)!=1 or fs[0].name!='choose' or len(all_fs)!=1:bad.append('FUNCTION_SHAPE')
 return {'ok':not bad,'bad':sorted(set(bad))}
