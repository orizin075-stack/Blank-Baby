from __future__ import annotations
import json,re,time
from pathlib import Path
from tukuyo_v977.whole_state import canon,sha_obj,_live_identity
from tukuyo_v1000.provider import provider_name,call_external,ProviderError
from tukuyo_v1001.knowledge import search,search_diagnostics
from tukuyo_v1002.cognition import _calc,_state_context,_math_expression
SCHEMA='tukuyo.v1004.deliberation/1'

def _write(p,o):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')
def _tool(data,name,args):
 if name=='calculator': return {'value':_calc(str(args.get('expression','')))}
 if name=='memory_search': return {'results':search(data,str(args.get('query','')),min(8,max(1,int(args.get('k',5)))))}
 if name=='self_state': return {'state':_state_context(data)}
 raise ValueError('TOOL_NOT_ALLOWED:'+str(name))
def deliberate(data,query,max_steps=4):
 max_steps=max(1,min(6,int(max_steps))); prov=provider_name(); diag=search_diagnostics(data,query,5);retrieved=diag['results']; tools_used=[]; t=time.monotonic(); answer=''
 if prov=='command':
  messages=[{'role':'system','content':'You are TUKUYO reasoning backend. Return a concise final answer. You may request only the declared tools via metadata.tool_calls. Never invent tool output.'},
            {'role':'user','content':json.dumps({'query':query,'tukuyo_state':_state_context(data),'retrieved_evidence':retrieved},ensure_ascii=False)}]
  specs=[{'name':'calculator','description':'safe arithmetic','args':{'expression':'string'}},{'name':'memory_search','description':'local evidence search','args':{'query':'string','k':'int'}},{'name':'self_state','description':'read bounded TUKUYO self state','args':{}}]
  for _ in range(max_steps):
   r=call_external(messages,tools=specs); answer=r.text
   calls=r.metadata.get('tool_calls',[]) if isinstance(r.metadata,dict) else []
   if not calls: break
   results=[]
   for c in calls[:3]:
    try: out=_tool(data,c.get('name'),c.get('args') or {});ok=True
    except Exception as e: out={'error':type(e).__name__+':'+str(e)};ok=False
    row={'name':c.get('name'),'args':c.get('args') or {},'ok':ok,'result':out};tools_used.append(row);results.append(row)
   messages.append({'role':'assistant','content':answer});messages.append({'role':'user','content':json.dumps({'tool_results':results,'instruction':'Use these results; request another tool only if necessary.'},ensure_ascii=False)})
 else:
  expr=_math_expression(query)
  if expr:
   try: answer=str(_calc(expr));tools_used=[{'name':'calculator','ok':True,'expression':expr}]
   except Exception: answer='計算できません。';tools_used=[{'name':'calculator','ok':False,'expression':expr}]
  else:
   from tukuyo_v1012.core_reasoning import reason as core_reason
   rr=core_reason(query)
   if rr.get('ok'):
    answer=str(rr['answer']);tools_used=[{'name':'core_reasoning','ok':True,'kind':rr.get('kind'),'confidence':rr.get('confidence')}]
   elif retrieved and diag.get('answerable'):
    answer='関連記憶: '+retrieved[0]['text'];tools_used=[{'name':'memory_search','ok':True,'diagnostics':diag}]
   elif retrieved:
    answer='記憶内に十分に対応する根拠を特定できません。';tools_used=[{'name':'memory_search','ok':False,'diagnostics':diag}]
   else: answer='内蔵コアでは十分な一般推論ができません。高性能provider接続時は、検証可能なtool loopを使用できます。'
 rec={'schema':SCHEMA,'individual_id':_live_identity(data)['individual_id'],'query':query,'answer':answer,'provider':prov,'tools_used':tools_used,'retrieved_ids':[x['id'] for x in retrieved],'latency_ms':int((time.monotonic()-t)*1000)};rec['record_sha256']=sha_obj(rec)
 p=Path(data)/'v1004'/'DELIBERATION_LOG.jsonl';p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('a',encoding='utf-8') as f:f.write(json.dumps(rec,ensure_ascii=False,sort_keys=True)+'\n')
 return {'ok':True,'version':'v1004',**rec}
def audit(data):
 p=Path(data)/'v1004'/'DELIBERATION_LOG.jsonl';errs=[];n=0
 if p.exists():
  for line in p.read_text(encoding='utf-8').splitlines():
   if not line.strip():continue
   n+=1;x=json.loads(line);q=dict(x);h=q.pop('record_sha256',None)
   if h!=sha_obj(q):errs.append('V1004_HASH');break
   for t in x.get('tools_used',[]):
    if t.get('name') not in ('calculator','memory_search','self_state'):errs.append('V1004_TOOL_SURFACE');break
 return {'ok':not errs,'version':'v1004','records':n,'errors':errs,'claim_boundary':{'bounded_tool_use':True,'unattended_external_action':False}}
