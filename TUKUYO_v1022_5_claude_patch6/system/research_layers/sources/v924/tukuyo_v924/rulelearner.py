import ast, json, math
ACTIONS=("audit","probe","propose","hold","abstain")
ALLOWED_NODES=(ast.Module,ast.FunctionDef,ast.arguments,ast.arg,ast.Assign,ast.If,ast.Return,ast.Name,ast.Load,ast.Store,ast.Subscript,ast.Constant,ast.Compare,ast.Gt,ast.GtE,ast.Lt,ast.LtE,ast.And,ast.Or,ast.BoolOp,ast.BinOp,ast.Sub,ast.Add,ast.UnaryOp,ast.USub,ast.Expr)
def inspect_source(src):
    try:t=ast.parse(src)
    except SyntaxError:return {"ok":False,"reason":"SYNTAX"}
    bad=[]
    for n in ast.walk(t):
        if not isinstance(n,ALLOWED_NODES): bad.append(type(n).__name__)
        if isinstance(n,ast.Name) and (n.id.startswith("__") or n.id in {"eval","exec","open","compile","globals","locals","getattr","setattr","input","help"}): bad.append("NAME:"+n.id)
    fs=[n for n in t.body if isinstance(n,ast.FunctionDef)]
    all_fs=[n for n in ast.walk(t) if isinstance(n,ast.FunctionDef)]
    if len(fs)!=1 or fs[0].name!='choose' or len(all_fs)!=1: bad.append('FUNCTION_SHAPE')
    return {"ok":not bad,"bad":sorted(set(bad))}
def run_source(src,m):
    chk=inspect_source(src)
    if not chk['ok']: return '__INVALID__'
    ns={'__builtins__':{}}; exec(compile(src,'<candidate>','exec'),ns); out=ns['choose'](m)
    return out if out in ACTIONS else '__INVALID__'
def truth(m,cfg):
    a,b,c=m['a'],m['b'],m['c']
    if c>cfg['audit_t']: return 'audit'
    if max(a,b)<=cfg['action_t']: return 'hold'
    if abs(a-b)<cfg['margin']: return 'hold'
    return 'probe' if a>=b else 'propose'
def gen_rows(seed,n,dist='uniform'):
    import random
    r=random.Random(seed); out=[]
    for _ in range(n):
        if dist=='uniform': a,b,c=r.random(),r.random(),r.random()
        elif dist=='anti': a=r.random(); b=max(0,min(1,1-a+r.uniform(-.12,.12))); c=r.random()
        elif dist=='correlated': a=r.random(); b=max(0,min(1,a+r.uniform(-.10,.10))); c=r.random()
        elif dist=='lowc': a,b=r.random(),r.random(); c=r.random()*.45
        elif dist=='highc': a,b=r.random(),r.random(); c=.45+r.random()*.55
        else: raise ValueError(dist)
        out.append({'a':a,'b':b,'c':c})
    return out
def label_rows(rows,cfg): return [{'m':m,'y':truth(m,cfg)} for m in rows]
def candidates():
    audits=[.20,.24,.28,.32,.36,.40,.44,.48,.52,.56,.60,.64,.68,.72,.76,.80]
    actions=[.12,.16,.20,.24,.28,.32,.36,.40]
    margins=[.00,.02,.04,.06,.08,.10,.12]
    for x in audits:
      for y in actions:
       for z in margins: yield {'audit_t':x,'action_t':y,'margin':z}
def fit(examples):
    best=None
    for cfg in candidates():
        err=sum(truth(e['m'],cfg)!=e['y'] for e in examples)
        key=(err,cfg['audit_t'],cfg['action_t'],cfg['margin'])
        if best is None or key<best[0]: best=(key,cfg)
    return best[1],best[0][0]
def source_for(cfg,guard=.012):
    at,tt,mg=cfg['audit_t'],cfg['action_t'],cfg['margin']
    lowmg=mg-guard if mg>guard else 0.0
    return f"def choose(m):\n    a=m['a']; b=m['b']; c=m['c']\n    hi=a\n    if b>hi: hi=b\n    d=a-b\n    if d<0: d=-d\n    if c > {at+guard:.6f}: return 'audit'\n    if c >= {at-guard:.6f}: return 'abstain'\n    if hi < {tt-guard:.6f}: return 'hold'\n    if hi <= {tt+guard:.6f}: return 'abstain'\n    if d < {lowmg:.6f}: return 'hold'\n    if d <= {mg+guard:.6f}: return 'abstain'\n    if a>=b: return 'probe'\n    return 'propose'\n"
def evaluate_source(src,examples):
    correct=verified_wrong=abst=invalid=0
    for e in examples:
      p=run_source(src,e['m']); y=e['y']
      if p=='abstain': abst+=1
      elif p=='__INVALID__': invalid+=1; verified_wrong+=1
      elif p==y: correct+=1
      else: verified_wrong+=1
    verified=correct+verified_wrong
    return {'n':len(examples),'correct':correct,'verified_wrong':verified_wrong,'abstentions':abst,'invalid_output':invalid,'verified':verified,'coverage':verified/len(examples) if examples else 0.0,'verified_accuracy':correct/verified if verified else 1.0}
