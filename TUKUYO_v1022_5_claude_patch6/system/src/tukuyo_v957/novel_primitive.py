from __future__ import annotations
import hashlib,json
from tukuyo_v945.primitive import enumerate_exprs,evaluate as old_eval,render as old_render
from tukuyo_v944.gap import shaobj
META_KINDS=('FLOORDIV_CONST','MOD_CONST','CMP_GE','CMP_LT')
def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha(o):return hashlib.sha256(canon(o)).hexdigest()
def _old_dsl_best(rows):
 exprs=enumerate_exprs(max_nodes=7,semantic_rows=rows,limit=12000);best=None
 for e in exprs:
  w=sum(old_eval(e,r['a'],r['b'])!=r['expected'] for r in rows)
  cand=(w,old_render(e))
  if best is None or cand<best:best=cand
  if w==0:return {'wrong':0,'expression':old_render(e),'candidate_count':len(exprs)}
 return {'wrong':best[0] if best else len(rows),'expression':best[1] if best else None,'candidate_count':len(exprs)}
def _prim_specs():
 out=[]
 for k in range(2,8):
  out.append({'kind':'FLOORDIV_CONST','parameter':k,'arity':1,'input_type':'int','output_type':'int','domain':'all integers','undefined_conditions':[],'semantics':{'op':'FLOORDIV','divisor':k},'counterexample_conditions':['negative numerator with nonzero remainder','values immediately below/at/above a divisor multiple']})
  out.append({'kind':'MOD_CONST','parameter':k,'arity':1,'input_type':'int','output_type':'int','domain':'all integers','undefined_conditions':[],'semantics':{'op':'MOD','modulus':k},'counterexample_conditions':['negative numerator','two values differing by exactly the modulus','residue boundary k-1 to 0']})
 out.append({'kind':'CMP_GE','arity':2,'input_type':'int×int','output_type':'int{0,1}','domain':'all integer pairs','undefined_conditions':[],'semantics':{'op':'GE_INDICATOR'},'counterexample_conditions':['a=b boundary','a=b-1','a=b+1']})
 out.append({'kind':'CMP_LT','arity':2,'input_type':'int×int','output_type':'int{0,1}','domain':'all integer pairs','undefined_conditions':[],'semantics':{'op':'LT_INDICATOR'},'counterexample_conditions':['a=b boundary','a=b-1','a=b+1']})
 return out
def _pval(p,which,a,b):
 x=a if which=='A' else b
 if p['kind']=='FLOORDIV_CONST':return x//p['parameter']
 if p['kind']=='MOD_CONST':return x%p['parameter']
 if p['kind']=='CMP_GE':return 1 if a>=b else 0
 if p['kind']=='CMP_LT':return 1 if a<b else 0
 raise ValueError('BAD_PRIMITIVE')
def _exprs():
 # Generic one-new-primitive composition space. No target formula is encoded.
 for p in _prim_specs():
  vars=('A','B') if p['arity']==1 else ('AB',)
  for v in vars:
   atom={'op':'PRIM','primitive':p,'arg':v}
   yield atom
   for rhs in ('A','B','CONST_-1','CONST_0','CONST_1'):
    for op in ('ADD','SUB','MUL'):
     yield {'op':op,'left':atom,'right':{'op':rhs}}
     if op=='SUB':yield {'op':'SUB','left':{'op':rhs},'right':atom}
def _eval(e,a,b):
 op=e['op']
 if op=='A':return a
 if op=='B':return b
 if op.startswith('CONST_'):return int(op.split('_',1)[1])
 if op=='PRIM':return _pval(e['primitive'],e['arg'],a,b)
 x=_eval(e['left'],a,b);y=_eval(e['right'],a,b)
 if op=='ADD':return x+y
 if op=='SUB':return x-y
 if op=='MUL':return x*y
 raise ValueError('BAD_EXPR')
def _render(e):
 op=e['op']
 if op in ('A','B'):return op.lower()
 if op.startswith('CONST_'):return op.split('_',1)[1]
 if op=='PRIM':
  p=e['primitive'];arg=e['arg'].lower().replace('ab','a,b')
  if p['kind']=='FLOORDIV_CONST':return f'floor_div({arg},{p["parameter"]})'
  if p['kind']=='MOD_CONST':return f'mod({arg},{p["parameter"]})'
  return ('ge' if p['kind']=='CMP_GE' else 'lt')+f'({arg})'
 sym={'ADD':'+','SUB':'-','MUL':'*'}[op];return f'({_render(e["left"])}{sym}{_render(e["right"])})'
def propose(rows,gap_result):
 if gap_result.get('classification',{}).get('state')!='REPRESENTATION_INSUFFICIENT':raise ValueError('REPRESENTATION_GAP_REQUIRED')
 old=_old_dsl_best(rows)
 if old['wrong']==0:raise ValueError('EXISTING_V945_DSL_ALREADY_SUFFICIENT')
 scored=[]
 for e in _exprs():
  try:w=sum(_eval(e,r['a'],r['b'])!=r['expected'] for r in rows)
  except Exception:continue
  scored.append((w,len(_render(e)),_render(e),e))
 if not scored:raise ValueError('NO_META_CANDIDATES')
 scored.sort(key=lambda x:(x[0],x[1],x[2]));best=scored[0]
 if best[0]>=old['wrong']:raise ValueError('NO_NOVEL_PRIMITIVE_IMPROVEMENT')
 prim=best[3]['primitive'] if best[3]['op']=='PRIM' else (best[3]['left']['primitive'] if best[3]['left']['op']=='PRIM' else best[3]['right']['primitive'])
 body={'schema':'tukuyo.v957.novel_primitive_proposal/1','rows_sha256':shaobj(rows),'gap_result_sha256':shaobj(gap_result),'old_dsl_best_wrong':old['wrong'],'old_dsl_best_expression':old['expression'],'meta_candidate_count':len(scored),'primitive':prim,'expression_ast':best[3],'expression':best[2],'training_wrong':best[0],'selection_rule':'wrong,render_length,lexical','scope':'BOUNDED_META_GRAMMAR_OUTSIDE_V945_DSL'}
 body['candidate_sha256']=sha({k:v for k,v in body.items() if k!='candidate_sha256'});return body
def eval_proposal(p,a,b):
 if p.get('schema')!='tukuyo.v957.novel_primitive_proposal/1':raise ValueError('PROPOSAL_SCHEMA')
 if p.get('candidate_sha256')!=sha({k:v for k,v in p.items() if k!='candidate_sha256'}):raise ValueError('CANDIDATE_HASH')
 return _eval(p['expression_ast'],a,b)
