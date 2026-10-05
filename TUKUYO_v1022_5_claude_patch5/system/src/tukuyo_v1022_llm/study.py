"""claude-patch2: self-study.

TUKUYO looks back over the questions it could not answer by itself (the hash-chained llm-ask log
records why the local core abstained), keeps those whose gap is something a teacher can fill
(an unknown event verb, an unknown wording of a known fact), asks the teacher(s) through the
guarded teacher pipeline, and then re-tests itself on the same questions WITHOUT any LLM.

The study log is hash-chained (v1022_llm/STUDY.jsonl) so its claims can be audited.
"""
from __future__ import annotations
import json,time
from pathlib import Path
from tukuyo_v977 import whole_state as whole
from . import bridge,providers,teacher

TEACHABLE=('UNKNOWN_EVENT_MEANING','MEMORY_PREMISES_MISSING')
SCHEMA='tukuyo.v1022_llm.study/1';HEAD_SCHEMA='tukuyo.v1022_llm.study_head/1'

def _log(data):return Path(data)/bridge.NS/'STUDY.jsonl'
def _head(data):return Path(data)/bridge.NS/'STUDY_HEAD.json'

def _validate_limit(limit):
    if type(limit) is not int or not 1<=limit<=128:raise ValueError('SELF_STUDY_LIMIT')

def candidates(data,limit=20):
    _validate_limit(limit)
    from tukuyo_common.journal import load_events
    from tukuyo_v1022 import cognition
    seen=[];out=[]
    p=bridge.log_path(data)
    for e in (load_events(p) if p.exists() else []):
        q=e.get('query')
        if not q or q in seen:continue
        seen.append(q)
        if e.get('local_reason') in TEACHABLE:
            now=cognition.solve(data,q)
            if now.get('uncertain') and now.get('reason') in TEACHABLE:out.append({'question':q,'reason':now['reason']})
    return out[:limit]

def study(data,limit=20,dry_run=False,extra=None):
    from tukuyo_v1019.lifecycle import require_alive
    from tukuyo_common.journal import last_event,append_event
    from tukuyo_v1022 import cognition
    _validate_limit(limit);require_alive(data)
    cands=candidates(data,limit)
    for q in (extra or []):
        if len(cands)>=limit:break
        r=cognition.solve(data,q)
        if r.get('uncertain') and r.get('reason') in TEACHABLE and q not in [c['question'] for c in cands]:cands.append({'question':q,'reason':r['reason']})
    if dry_run or not cands:
        return {'ok':True,'version':'v1022.5+claude-patch4','dry_run':dry_run,'candidates':cands,'summary':None}
    res=teacher.teach(data,[c['question'] for c in cands])
    after=[{'question':c['question'],'local_answer':(x:=cognition.solve(data,c['question'])).get('answer'),'solved_locally':not x.get('uncertain')} for c in cands]
    rec={'schema':SCHEMA,'utc_ns':time.time_ns(),'teachers':res.get('teachers'),'candidates':len(cands),'summary':res['summary'],
         'now_solved_locally':sum(a['solved_locally'] for a in after),'questions':[c['question'] for c in cands]}
    p=_log(data);last=last_event(p) if p.exists() else None
    rec={**rec,'seq':int(last.get('seq',0))+1 if last else 1,'prev_sha256':last.get('event_sha256',whole.ZERO) if last else whole.ZERO}
    rec['event_sha256']=whole.sha_obj(rec);append_event(p,_head(data),rec,HEAD_SCHEMA,whole.sha_obj,whole._live_identity(data)['individual_id'])
    return {'ok':True,'version':'v1022.5+claude-patch4','candidates':cands,'teach':res,'after':after,'now_solved_locally':rec['now_solved_locally'],'log_seq':rec['seq']}

def audit(data):
    from tukuyo_common.journal import load_events
    p=_log(data);head=_head(data);errors=[];prev=whole.ZERO;count=0
    if not p.exists() and not head.exists():return {'ok':True,'studies':0,'errors':[]}
    try:
        if not p.exists():raise ValueError('STUDY_LOG_MISSING')
        for i,event in enumerate(load_events(p),1):
            body=dict(event);digest=body.pop('event_sha256',None)
            if event.get('schema')!=SCHEMA or event.get('seq')!=i or event.get('prev_sha256')!=prev or digest!=whole.sha_obj(body):
                raise ValueError('STUDY_LOG_CHAIN:'+str(i))
            count=i;prev=digest
        value=json.loads(head.read_text());body=dict(value);digest=body.pop('head_record_sha256',None)
        if digest!=whole.sha_obj(body) or value.get('schema')!=HEAD_SCHEMA or value.get('count')!=count or value.get('head_sha256')!=prev or value.get('journal_size')!=p.stat().st_size or value.get('individual_id')!=whole._live_identity(data)['individual_id']:
            raise ValueError('STUDY_LOG_HEAD')
    except (ValueError,TypeError,KeyError,OSError) as exc:errors.append(str(exc))
    return {'ok':not errors,'studies':count,'errors':errors}
