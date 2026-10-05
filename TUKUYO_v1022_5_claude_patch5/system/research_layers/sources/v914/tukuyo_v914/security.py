import ast
BANNED=(ast.Import,ast.ImportFrom,ast.With,ast.Try,ast.Global,ast.Nonlocal,ast.ClassDef,ast.Lambda,ast.Attribute,ast.Call)
def inspect_source(src):
 try:t=ast.parse(src)
 except SyntaxError:return {'ok':False,'reason':'SYNTAX'}
 bad=[type(n).__name__ for n in ast.walk(t) if isinstance(n,BANNED)]
 return {'ok':not bad,'reason':'BANNED_AST' if bad else 'OK','bad':bad}
