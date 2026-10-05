from __future__ import annotations
import json,re,math
from pathlib import Path
from tukuyo_v977.whole_state import canon,sha_obj,_live_identity
from tukuyo_v1000.provider import provider_name
from tukuyo_v1004.deliberation import deliberate
from tukuyo_v1002.cognition import _math_expression,_calc
from tukuyo_v1001.knowledge import search_diagnostics,tokens
from tukuyo_v1014_1.semantic_verifier import verify_bounded_semantics
from tukuyo_common.atomic_fs import atomic_write_bytes,atomic_write_json,durable_unlink,maybe_crash
SCHEMA='tukuyo.v1010.calibrated_verified_reasoning/1'
def _write(p,o,crashpoint=None):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);atomic_write_bytes(p,canon(o)+b'\n',crashpoint=crashpoint)
def _numeric_answer(a):
 m=re.fullmatch(r'\s*(-?\d+(?:\.\d+)?)\s*',str(a));return float(m.group(1)) if m else None
def _evidence_score(data,query,row):
    answer=str(row.get('answer','')).strip();expr=_math_expression(query)
    if expr:
        try:
            expected=float(_calc(expr));got=_numeric_answer(answer)
            return (1.0 if got is not None and math.isclose(got,expected,rel_tol=1e-12,abs_tol=1e-12) else 0.02),{'mode':'CALCULATOR_RECOMPUTE','expected':expected,'independent':True}
        except Exception:return .15,{'mode':'CALCULATOR_REJECTED','independent':True}

    # v1014.1: do not ask the answer-generating core to validate itself.  The
    # bounded semantic verifier independently reconstructs requested entity,
    # query role, exactness, units and event balance.
    sv=verify_bounded_semantics(query,answer)
    if sv.get('kind') in ('EVENT_CONSUMPTION','PACK_TOTAL'):
        # Package/event surfaces unsupported by the new coverage guard cannot
        # be approved by the permissive legacy parser as a fallback.
        from tukuyo_v1022.cognition import inventory,normalize
        from tukuyo_v1022 import cognition as local_cognition
        guarded=inventory(normalize(query),local_cognition.state(data))
        if not guarded.get('recognized') or guarded.get('uncertain'):
            return .10,{'mode':'LOCAL_EVENT_COVERAGE_ABSTAIN','independent':False,'reason':guarded.get('reason')}
    if sv.get('recognized'):
        if not sv.get('decidable'):
            return .10,{'mode':'INDEPENDENT_SEMANTIC_ABSTAIN','independent':True,'reason':sv.get('reason'),'kind':sv.get('kind')}
        good=bool(sv.get('supported'))
        return (.97 if good else .02),{'mode':'INDEPENDENT_SEMANTIC_VERIFY','independent':True,'kind':sv.get('kind'),'expected':sv.get('expected'),'matched':good}

    d=search_diagnostics(data,query,5)
    if d.get('answerable'):
        top=d['results'][0]['text'] if d['results'] else ''
        direct=bool(top and top in answer);at=set(tokens(answer));et=set(tokens(top));over=(len(at&et)/max(1,len(at))) if at else 0.0
        if direct:over=1.0
        s=.16+.20*float(d.get('semantic_coverage',d.get('coverage',0)))+.10*float(d.get('margin',0))+.50*over
        return min(.97,s),{'mode':'RETRIEVAL_SUPPORT','coverage':d.get('coverage'),'semantic_coverage':d.get('semantic_coverage'),'margin':d.get('margin'),'direct_quote_match':direct,'answer_evidence_overlap':round(over,6),'independent':True,'candidate_count':d.get('candidate_count')}
    return .12,{'mode':'NO_GROUNDED_SUPPORT','reason':d.get('reason'),'coverage':d.get('coverage'),'margin':d.get('margin'),'independent':True}

def score_candidate(data,query,answer):
 score,evidence=_evidence_score(data,query,{'answer':str(answer)});return {'ok':True,'version':'v1011','query':str(query),'answer':str(answer),'confidence':round(float(score),6),'uncertain':float(score)<.70,'verification_evidence':evidence}

SECOND_OPINION_REASONS=frozenset({'NO_INVENTORY_FRAME','NO_LOGIC_FRAME','NO_LOGIC_QUERY','MEMORY_PREMISES_MISSING','QUERY_ROLE_MISSING'})
def _second_opinion(query,local):
 """claude-patch1: when the v1022 core abstains, the older bounded reasoner may propose an
 answer, but it is accepted ONLY if the independent verifier decides and agrees.
 Only for abstentions that mean "no frame for this question". A deliberate abstention
 (ambiguous range, unconfirmed event, conflicting memory ...) is never overridden: the
 legacy reasoner and the v1014.1 verifier were shown to share blind spots there
 (e.g. both read "3〜5個食べました" as 5)."""
 if local.get('reason') not in SECOND_OPINION_REASONS:return local
 try:
  from tukuyo_v1012.core_reasoning import reason
  r=reason(query)
  if not r.get('ok') or r.get('answer') in (None,''):return local
  sv=verify_bounded_semantics(query,str(r['answer']))
 except Exception:return local
 if sv.get('recognized') and sv.get('decidable') and sv.get('supported'):
  ev={'mode':'LEGACY_CANDIDATE+INDEPENDENT_SEMANTIC_VERIFY','independent':True,'kind':sv.get('kind'),'expected':sv.get('expected'),'local_abstention':local.get('reason')}
  return {**local,'answer':str(r['answer']),'confidence':.97,'uncertain':False,'proof':None,'verification_evidence':ev}
 return local

def _same_surface(a,b):
 """Same bounded proposition up to politeness/particle surface: 「地面は濡れるです。」 == 「地面が濡れる」."""
 def n(x):
  x=re.sub(r'[\s。．.!！]+','',str(x));x=re.sub(r'(?:です|だ|である)$','',x)
  return re.sub(r'^([^、。]{1,24}?)[はが](.+)$',r'\1が\2',x)
 return bool(n(a)) and n(a)==n(b)

_STOP_EN=frozenset('what which who whom whose where when why how is are was were the a an of in on at to into does do did it its and or'.split())
def _memory_covers(query,memory):
 import unicodedata
 q=unicodedata.normalize('NFKC',str(query)).lower();m=unicodedata.normalize('NFKC',str(memory)).lower()
 if re.search(r'[a-z]{3}',q) and not re.search(r'[\u3040-\u30ff\u4e00-\u9fff]',q):
  terms=[w for w in re.findall(r'[a-z0-9]+',q) if w not in _STOP_EN and len(w)>1]
  return bool(terms) and all(re.search(r'\b'+re.escape(w),m) for w in terms)
 q=re.sub(r'(?:は|って)?\s*(?:何|なに|なん|誰|だれ|どこ|いつ|いくつ|いくら|どれ|どの|どう|どんな)[^?？]*[?？]?$|[?？。]+$','',q)
 terms=[t for t in re.split(r'[のはがをにでともへや、\s]+',q) if len(t)>=2]
 return bool(terms) and all(t in m for t in terms)

def _independent_crosscheck(query,local):
 """claude-patch1: the answering core must not be its own only judge.
 An accepted local answer is re-read by the separately written v1014.1 verifier.
 Agreement adds independent evidence; a decided disagreement withholds the answer."""
 if local.get('uncertain') or local.get('answer') is None:return local
 try:
  sv=verify_bounded_semantics(query,str(local['answer']));same_family=False
  if (not sv.get('recognized') or not sv.get('decidable')) and (local.get('proof') or {}).get('kind')=='deliberation':
   from tukuyo_v1022.deliberation_verify import verify as verify_deliberation
   sv=verify_deliberation(query,str(local['answer']));same_family=True
 except Exception as e:sv={'recognized':False,'reason':'VERIFIER_ERROR:'+type(e).__name__}
 if sv.get('recognized') and sv.get('decidable') and not sv.get('supported') and sv.get('expected') is not None and _same_surface(local['answer'],sv['expected']):
  sv={**sv,'supported':True,'surface_normalized':True}
 ev=dict(local.get('verification_evidence') or {})
 if sv.get('recognized') and sv.get('decidable'):
  if sv.get('supported'):
   # claude-patch4: a re-parse by the producer's own family (deliberation_verify) is a recheck, not independence
   gate=(ev.get('semantic_gate') or {}).get('independent_parser')
   ev.update({'independent':not same_family,'independent_mode':'SAME_FAMILY_RECHECK' if same_family else 'INDEPENDENT_SEMANTIC_VERIFY','kind':sv.get('kind'),'independent_expected':sv.get('expected'),
              'independence':{'secondary_verifier':'deliberation_verify (same family)' if same_family else 'v1014.1','separate_parser_B':gate or 'NOT_APPLICABLE'}})
   return {**local,'confidence':max(float(local.get('confidence',0)),.9),'verification_evidence':ev}
  ev.update({'independent':True,'independent_mode':'INDEPENDENT_SEMANTIC_DISAGREEMENT','kind':sv.get('kind'),'independent_expected':sv.get('expected'),'withheld_answer':str(local['answer'])})
  return {**local,'answer':None,'confidence':.02,'uncertain':True,'reason':'INDEPENDENT_VERIFIER_DISAGREEMENT','verification_evidence':ev}
 ev.update({'independent':False,'independent_reason':sv.get('reason')})
 return {**local,'verification_evidence':ev}

def solve(data,query,samples=3):
 from tukuyo_v1022.cognition import solve as local_solve
 local=local_solve(data,query)
 if local.get('recognized'):local=_independent_crosscheck(query,local)
 if local.get('recognized') and local.get('uncertain'):local=_second_opinion(query,local)
 if local.get('recognized'):
  out={'schema':SCHEMA,'individual_id':_live_identity(data)['individual_id'],'query':query,
       'answer':local.get('answer') or '根拠が足りないため確定できません。','candidate_count':1,'agreement':1.,
       'confidence':local['confidence'],'uncertain':local['uncertain'],'proof':local.get('proof'),
       'verification_evidence':local.get('verification_evidence',{'mode':'LOCAL_COVERAGE_ABSTAIN','reason':local.get('reason')}),'candidate_summaries':[]}
  out['result_sha256']=sha_obj(out);marker=Path(data)/'v1014/private/PENDING_MUTATION.json'
  atomic_write_json(marker,{'schema':'tukuyo.v1014_2.pending_mutation/1','operation':'VERIFIED_QUERY_SYNC','created_for_sha256':out['result_sha256']})
  _write(Path(data)/'v1005/LAST_VERIFIED_REASONING.json',out,crashpoint='verified_result');maybe_crash('verified_query:after_result')
  from tukuyo_v977.whole_state import sync as whole_sync
  whole_sync(data);durable_unlink(marker)
  return {'ok':True,'version':'v1022','verification_revision':'v1022',**out}
 samples=max(1,min(4,int(samples)));rows=[deliberate(data,query) for _ in range(samples if provider_name()=='command' else 1)]
 for r in rows:
  r['verification_score'],r['verification_evidence']=_evidence_score(data,query,r)
 groups={}
 for r in rows:groups.setdefault(r['answer'].strip(),[]).append(r)
 best=max(groups.items(),key=lambda kv:(len(kv[1]),max(x['verification_score'] for x in kv[1]),kv[0]))
 chosen=max(best[1],key=lambda x:x['verification_score']);agreement=len(best[1])/len(rows)
 # Agreement cannot rescue an unsupported answer.
 support=float(chosen['verification_score']);confidence=round(min(support,.72*support+.28*agreement),6);uncertain=confidence<.70
 # claude-patch1: echoing a *related* memory is not an answer. If the question's own terms are not
 # all in that memory (other entity, other attribute), the echo is never presented as certain.
 if str(chosen['answer']).startswith('関連記憶:') and not _memory_covers(query,str(chosen['answer'])[5:]):
  confidence=min(confidence,.5);uncertain=True
  chosen={**chosen,'verification_evidence':{**(chosen.get('verification_evidence') or {}),'coverage_gate':'QUESTION_TERMS_NOT_IN_MEMORY'}}
 out={'schema':SCHEMA,'individual_id':_live_identity(data)['individual_id'],'query':query,'answer':chosen['answer'],'candidate_count':len(rows),
      'agreement':round(agreement,6),'confidence':confidence,'uncertain':uncertain,'verification_evidence':chosen['verification_evidence'],
      'candidate_summaries':[{'answer':r['answer'],'score':r['verification_score'],'evidence':r['verification_evidence'],'tools':[t.get('name') for t in r.get('tools_used',[])]} for r in rows]}
 out['result_sha256']=sha_obj(out)
 marker=Path(data)/'v1014'/'private'/'PENDING_MUTATION.json'
 atomic_write_json(marker,{'schema':'tukuyo.v1014_2.pending_mutation/1','operation':'VERIFIED_QUERY_SYNC','created_for_sha256':out['result_sha256']})
 _write(Path(data)/'v1005'/'LAST_VERIFIED_REASONING.json',out,crashpoint='verified_result');maybe_crash('verified_query:after_result')
 from tukuyo_v977.whole_state import sync as whole_sync
 whole_sync(data);durable_unlink(marker)
 return {'ok':True,'version':'v1010','verification_revision':'v1015.1',**out}
def audit(data):
 p=Path(data)/'v1005'/'LAST_VERIFIED_REASONING.json'
 if not p.exists():return {'ok':False,'version':'v1010','errors':['V1005_MISSING']}
 x=json.loads(p.read_text());q=dict(x);h=q.pop('result_sha256',None);errs=[]
 if h!=sha_obj(q):errs.append('V1010_VERIFIER_HASH')
 if not 0<=float(x.get('confidence',-1))<=1:errs.append('V1010_CONFIDENCE')
 if x.get('uncertain') is False and float(x.get('confidence',0))<.70:errs.append('V1010_UNCERTAINTY_CALIBRATION')
 return {'ok':not errs,'version':'v1010','errors':errs,'confidence':x.get('confidence'),'uncertain':x.get('uncertain')}
