from __future__ import annotations
import ast,json,math,operator,re,time
from pathlib import Path
from tukuyo_v1000.provider import call_external,provider_name,ProviderError
from tukuyo_v1001.knowledge import search,search_diagnostics
from tukuyo_v1012.core_reasoning import reason as core_reason

import unicodedata
OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.FloorDiv:operator.floordiv,ast.Mod:operator.mod,ast.Pow:operator.pow,ast.USub:operator.neg,ast.UAdd:operator.pos}
def _calc(expr):
    def ev(n):
        if isinstance(n,ast.Expression):return ev(n.body)
        if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)):return n.value
        if isinstance(n,ast.UnaryOp) and type(n.op) in OPS:return OPS[type(n.op)](ev(n.operand))
        if isinstance(n,ast.BinOp) and type(n.op) in OPS:
            a,b=ev(n.left),ev(n.right)
            if isinstance(n.op,ast.Pow) and abs(b)>10:raise ValueError('POWER_LIMIT')
            v=OPS[type(n.op)](a,b)
            if not math.isfinite(float(v)) or abs(float(v))>1e18:raise ValueError('MAG_LIMIT')
            return v
        raise ValueError('UNSAFE_EXPRESSION')
    return ev(ast.parse(expr,mode='eval'))

def _math_expression(query):
    s=unicodedata.normalize('NFKC',str(query)).lower().strip()
    reps=[('かける','*'),('掛ける','*'),('×','*'),('たす','+'),('足す','+'),('プラス','+'),('ひく','-'),('引く','-'),('マイナス','-'),('わる','/'),('割る','/'),('÷','/'),('^','**')]
    for a,b in reps:s=s.replace(a,b)
    s=re.sub(r'(はいくつ|はいくら|は何|の答え|を計算して|計算して|ですか|でしょうか)','',s)
    s=re.sub(r'[?？。]+$','',s).strip()
    s=re.sub(r'は$','',s).strip()
    if re.fullmatch(r'[-+*/%().0-9\s]{1,160}',s) and re.search(r'\d',s):return s
    return None

def _state_context(data):
    root=Path(data); out={}
    for name,rel in [('purpose','v985/NARRATIVE_PURPOSE_STATE.json'),('peer','v995/OTHER_AGENT_MODELS.json'),('identity','v989/TEMPORAL_IDENTITY.json'),('working_memory','v1012/WORKING_MEMORY.json')]:
        p=root/rel
        if p.exists():
            try: out[name]=json.loads(p.read_text(encoding='utf-8'))
            except Exception: pass
    return out

def _builtin(query,retrieved,diag=None):
    expr=_math_expression(query)
    if expr:
        try:return str(_calc(expr))
        except ZeroDivisionError:return '計算できません（0で割ることはできません）。'
        except Exception:return 'その式は安全な内蔵計算器の範囲外です。'
    rr=core_reason(query)
    if rr.get('ok'):
        return rr['answer']
    if retrieved and (diag or {}).get('answerable'):
        return f"関連記憶: {retrieved[0]['text']}"
    if retrieved:
        return '記憶内に十分に対応する根拠を特定できません。'
    return 'この軽量コアだけでは十分な一般言語推論ができません。高性能providerを接続すると、TUKUYOの記憶・目的・関係状態を保ったまま回答できます。'

def answer(data,query,max_context=5):
    diag=search_diagnostics(data,query,max_context);retrieved=diag['results'];state=_state_context(data);prov=provider_name();t=time.monotonic()
    if prov=='command':
        sysmsg=('You are the reasoning backend for TUKUYO. Use the supplied TUKUYO state and retrieved evidence. '
                'Do not claim evidence that is absent. Give the final answer concisely and preserve uncertainty.')
        user={'query':query,'tukuyo_state':state,'retrieved_evidence':retrieved}
        r=call_external([{'role':'system','content':sysmsg},{'role':'user','content':json.dumps(user,ensure_ascii=False)}],
                        tools=[{'name':'calculator','description':'safe arithmetic calculator'},{'name':'memory_search','description':'search TUKUYO local knowledge'}])
        text=r.text;lat=r.latency_ms;meta=r.metadata
    else:
        text=_builtin(query,retrieved,diag);lat=int((time.monotonic()-t)*1000);meta={'retrieval_diagnostics':diag}
    rec={'schema':'tukuyo.v1002.cognitive_answer/1','query':query,'answer':text,'provider':prov,'retrieved_ids':[x['id'] for x in retrieved],'latency_ms':lat,'provider_metadata':meta,'retrieval_answerable':diag.get('answerable'),'retrieval_coverage':diag.get('coverage'),'retrieval_margin':diag.get('margin')}
    p=Path(data)/'v1002'/'cognitive_log.jsonl';p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('a',encoding='utf-8') as f:f.write(json.dumps(rec,ensure_ascii=False,sort_keys=True)+'\n')
    return {'ok':True,**rec,'retrieved':retrieved}
