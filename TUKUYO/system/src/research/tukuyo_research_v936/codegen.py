"""Compile learned decision trees to a constrained source representation, no eval."""
import ast
from .learner import ACTIONS
from .features import ALL_FEATURES

def _expr(name):
    if name in ('a','b','c'): return name
    op,a,b=name.split(':')
    symbol={'sum':'+','diff':'-','prod':'*'}[op]
    return f'({a} {symbol} {b})'

def source(tree):
    out=['def choose(m):',"    a=float(m['a']); b=float(m['b']); c=float(m['c'])"]
    def walk(node,indent):
        pad=' '*indent
        if 'feature' not in node:
            if node['action'] not in ACTIONS:raise ValueError('invalid action')
            out.append(pad+f"return {node['action']!r}")
        else:
            if node['feature'] not in ALL_FEATURES:raise ValueError('invalid feature')
            t=float(node['threshold'])
            if not -1<=t<=2:raise ValueError('invalid threshold')
            out.append(pad+f"if {_expr(node['feature'])} <= {t:.12g}:")
            walk(node['left'],indent+4)
            out.append(pad+'else:')
            walk(node['right'],indent+4)
    walk(tree,4)
    src='\n'.join(out)+'\n'
    verify_generated_source(src,tree)
    return src

def verify_generated_source(src,tree):
    expected='\n'.join(['def choose(m):',"    a=float(m['a']); b=float(m['b']); c=float(m['c'])"])
    t=ast.parse(src)
    if not (len(t.body)==1 and isinstance(t.body[0],ast.FunctionDef)): raise ValueError('GENERATED_AST_SHAPE')
    # This is an identity check, not a general-purpose Python sandbox.
    if not (t.body[0].name=='choose' and len(t.body[0].args.args)==1): raise ValueError('GENERATED_FUNCTION_SIGNATURE')
    if not src.startswith(expected+'\n'): raise ValueError('GENERATED_PREFIX_MISMATCH')
    if 'import ' in src or '__' in src: raise ValueError('GENERATED_FORBIDDEN_TOKEN')
    return True
