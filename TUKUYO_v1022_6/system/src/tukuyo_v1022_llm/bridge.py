"""claude-patch1: an LLM as TUKUYO's reasoning engine, kept honest by TUKUYO's own checks.

Order of work for every question:
 1. The local core answers first. A locally proven answer is returned unchanged.
 2. Otherwise the LLM receives a bounded context: identity, heart state, effective values,
    retrieved memories with ids, learned facts and (optionally) recent conversation.
    Private keys, private notes and anything under */private/ are never read.
 3. The LLM must return JSON with the answer and the CLAIMS the answer depends on.
 4. TUKUYO checks every checkable claim itself:
      calc   -> recomputed with the safe local calculator
      memory -> the cited id must be in the supplied context and the quote must occur in it
      local  -> the sub-question must be proven by the local core with the same value
      external (general knowledge) -> cannot be checked here; marked as such
    One repair round is allowed: failed checks are sent back once.
 5. Status: verified / partially_verified / unverified / rejected. Only a verified answer
    can be "certain". A rejected answer is withheld.
 6. Every exchange is appended to a hash-chained log (v1022_llm/ANSWERS.jsonl).
The LLM never writes code, files, memories, Soul or Heart state. Nothing it says is
stored as a fact.
"""
from __future__ import annotations
import hashlib,json,os,re,time
from pathlib import Path
from tukuyo_v977 import whole_state as whole
from . import providers

NS='v1022_llm';SCHEMA='tukuyo.v1022_llm.answer/1';HEAD_SCHEMA='tukuyo.v1022_llm.answer_head/1'
CLAIM_BOUNDARY={'llm_is_reasoning_engine':True,'llm_output_stored_as_fact':False,'llm_modifies_code_or_state':False,
                'unverified_claims_marked':True,'general_intelligence_established':False,'consciousness_established':False}

def log_path(data):return Path(data)/NS/'ANSWERS.jsonl'
def head_path(data):return Path(data)/NS/'ANSWER_HEAD.json'

SYSTEM='''あなたは電子個体「TUKUYO」の思考エンジンです。TUKUYO本人として、日本語で自然に答えてください。
渡された「個体の状態」と「記憶」を使ってよいですが、無いものを記憶として作ってはいけません。
答えが分からない、または前提が足りないときは unknown を true にして、その理由を answer に書きます。

必ず次の形のJSONだけを出力してください（前後に文章を付けない）。
{"answer": "最終的な返答",
 "unknown": false,
 "confidence": 0.0〜1.0,
 "claims": [
   {"type": "calc", "expression": "12*(5+4)", "value": "108"},
   {"type": "memory", "id": "記憶のid", "quote": "その記憶本文からそのまま抜き出した一部"},
   {"type": "local", "question": "TUKUYOの内蔵コアで確かめられる小問", "value": "その答え"},
   {"type": "external", "statement": "一般知識として使った主張"}
 ]}
規則:
- 計算を使ったら、その式と値を必ず calc に入れる（式は数字と + - * / ( ) だけ）。
- 記憶を使ったら、その id と本文の抜き出しを memory に入れる。
- 一般知識に頼った主張は external に入れる。
- claims に無い根拠を answer の中で使わない。'''

def _read(p):
    try:return json.loads(Path(p).read_text(encoding='utf-8'))
    except Exception:return None

def context(data,query,share_history=None):
    """Bounded, explicitly enumerated context. Never walks the data tree, never reads */private/*."""
    d=Path(data);ctx={'identity':whole._live_identity(d)['individual_id']}
    # Read-only: loaders that create default files would change audited state as a side effect.
    h=_read(d/'v978/HEART_STATE.json')
    if h:ctx['heart']={'emotion':h.get('emotion'),'active_goal':h.get('active_goal')}
    try:
        from tukuyo_v1018.succession import DEFAULT_VALUES
        native=(_read(d/'v977/SOUL_CORE.json') or {}).get('core_values') or {};st=_read(d/'v1018/SUCCESSION_STATE.json') or {}
        inh=st.get('inherited_value_profile') if st.get('role')=='SUCCESSOR' else None
        ctx['values']={k:round(max(0.,min(1.,(float(inh.get(k,b))+float(native.get(k,b))-b) if isinstance(inh,dict) else float(native.get(k,b)))),6) for k,b in DEFAULT_VALUES.items()}
    except Exception:pass
    life=_read(d/'v1007/ORGANISM2_STATE.json')
    if life:ctx['life']={'lifecycle':life.get('lifecycle'),'energy':life.get('energy')}
    mem=[]
    try:
        from tukuyo_v1001.knowledge import search
        for r in search(d,query,5):mem.append({'id':'k:'+str(r['id']),'text':r['text']})
    except Exception:pass
    try:
        from tukuyo_v1022 import cognition
        st=cognition.state(d);q=cognition.normalize(query)
        for i,f in enumerate(st.get('facts',[])):
            if f.get('entity') and f['entity'] in q:mem.append({'id':f'f:{i}','text':f"{f['entity']}の{f['relation']}は{f['value']}"})
    except Exception:pass
    ctx['memories']=mem[:12]
    share=os.environ.get('TUKUYO_LLM_SHARE_HISTORY','1')!='0' if share_history is None else share_history
    if share:
        try:
            from tukuyo_common.journal import load_events
            ev=load_events(d/'v996/CONVERSATION_GROUNDING_EVENTS.jsonl')[-6:]
            ctx['recent_conversation']=[e.get('text','')[:300] for e in ev]
        except Exception:pass
    return ctx

def _check(data,claims,mem_index):
    from tukuyo_v1022 import proofs,cognition
    rows=[];checkable=0;failed=0;external=0
    for c in claims if isinstance(claims,list) else []:
        if not isinstance(c,dict):rows.append({'claim':c,'result':'MALFORMED'});failed+=1;continue
        t=c.get('type')
        if t=='calc':
            checkable+=1
            try:
                expr=str(c.get('expression',''))
                if not re.fullmatch(r'[\d\s.+\-*/()]{1,200}',expr):raise ValueError('EXPRESSION_CHARSET')
                v=proofs.number(proofs.calculate(expr));ok=str(c.get('value','')).strip()==v
                rows.append({'claim':c,'result':'OK' if ok else 'CALC_MISMATCH','recomputed':v});failed+=not ok
            except Exception as e:rows.append({'claim':c,'result':'CALC_UNCHECKABLE:'+type(e).__name__});failed+=1
        elif t=='memory':
            checkable+=1;m=mem_index.get(str(c.get('id','')));quote=str(c.get('quote','')).strip()
            ok=bool(m) and len(quote)>=2 and quote in m
            rows.append({'claim':c,'result':'OK' if ok else ('MEMORY_ID_UNKNOWN' if not m else 'MEMORY_QUOTE_NOT_FOUND')});failed+=not ok
        elif t=='local':
            checkable+=1
            try:
                r=cognition.solve(data,str(c.get('question','')));ok=(not r['uncertain']) and str(r['answer'])==str(c.get('value','')).strip()
                rows.append({'claim':c,'result':'OK' if ok else 'LOCAL_NOT_CONFIRMED','local_answer':r.get('answer'),'local_reason':r.get('reason')});failed+=not ok
            except Exception as e:rows.append({'claim':c,'result':'LOCAL_ERROR:'+type(e).__name__});failed+=1
        elif t=='external':external+=1;rows.append({'claim':c,'result':'EXTERNAL_UNCHECKED'})
        else:rows.append({'claim':c,'result':'UNKNOWN_CLAIM_TYPE'});failed+=1
    return rows,checkable,failed,external

def _numbers_unbacked(answer,claims,query=''):
    """Numbers in the answer that no calc/local claim, cited memory or the question itself supplies
    -> arithmetic done 'in the head', which keeps the answer from counting as verified."""
    num=r'(?<![\w.])\d+(?:\.\d+)?(?![\w.])';backed=set(re.findall(num,str(query)))
    for c in claims if isinstance(claims,list) else []:
        if isinstance(c,dict) and c.get('type') in ('calc','local'):backed.add(str(c.get('value','')).strip())
        if isinstance(c,dict) and c.get('type')=='memory':backed|=set(re.findall(num,str(c.get('quote',''))))
    nums=set(re.findall(r'(?<![\w.])\d+(?:\.\d+)?(?![\w.])',str(answer)))
    return sorted(n for n in nums if n not in backed and len(n)>=3)

FRAMING={'記憶','計算','結果','答','答え','合計','確認','検算','根拠','内蔵','質問','場合','前提','以上','全部','残','約','今','私','本当','可能','情報','説明','理由'}
EN_FRAMING={'the','and','that','this','with','from','have','has','are','was','were','for','not','you','your','answer','memory','according','based','result','total','which','what','there','their','about','into','will','would','can'}
def _content_tokens(text):
    s=__import__('unicodedata').normalize('NFKC',str(text))
    toks={t.lower() for t in re.findall(r'[\u4e00-\u9fff々]+|[\u30a0-\u30ffー]{2,}|[A-Za-z]{3,}|\d+(?:\.\d+)?',s)}
    return {t for t in toks if t not in FRAMING and t not in EN_FRAMING}

def _support_text(query,claims,checks):
    """text that a checked claim or the question actually provides"""
    parts=[str(query)]
    for c,ck in zip(claims if isinstance(claims,list) else [],checks):
        if isinstance(c,dict) and ck.get('result')=='OK':
            parts+= [str(c.get(k,'')) for k in ('expression','value','quote','question')]
    return ' '.join(parts)

def _relevant(c,answer):
    """claude-patch4: a checked claim only counts if the answer actually uses it"""
    a=__import__('unicodedata').normalize('NFKC',str(answer))
    if not isinstance(c,dict):return False
    if c.get('type') in ('calc','local'):return str(c.get('value','')).strip()!='' and str(c.get('value','')).strip() in a
    if c.get('type')=='memory':return bool(_content_tokens(c.get('quote',''))&_content_tokens(a))
    return False

def _status(checkable,failed,external,unknown,unbacked,content_unbacked=(),relevant=None):
    if unknown:return 'abstained'
    if failed:return 'rejected'
    # claude-patch4: 'verified' needs a relevant checked claim AND no content word of the answer left unsupported
    # (an unrelated correct calculation can no longer certify an invented statement)
    useful=checkable if relevant is None else relevant
    if useful and not external and not unbacked and not content_unbacked:return 'verified'
    if useful:return 'partially_verified'
    return 'unverified'

def _append_log(data,rec):
    from tukuyo_common.journal import last_event,append_event
    p=log_path(data);last=last_event(p);rec={**rec,'seq':int(last.get('seq',0))+1 if last else 1,'prev_sha256':last.get('event_sha256',whole.ZERO) if last else whole.ZERO}
    rec['event_sha256']=whole.sha_obj(rec);append_event(p,head_path(data),rec,HEAD_SCHEMA,whole.sha_obj,whole._live_identity(data)['individual_id']);return rec

TOOLS_NOTE='''
道具（任意）: 答える前に、TUKUYOの内蔵の道具を最大3つまで使えます。その場合は answer を書かずに次だけを返します:
{"tool_requests":[{"tool":"search","query":"記憶を探す語"},{"tool":"solve","question":"内蔵コアで厳密に解ける小問（計算・文章題・論理）"},{"tool":"calc","expression":"12*(5+4)"}]}
結果が返ってきたら、それを使って最終JSONを書いてください。道具の結果は claims（memory / local / calc）として引用できます。'''

def _run_tools(data,reqs,mem_index):
    from tukuyo_v1022 import proofs,cognition
    out=[]
    for r in (reqs if isinstance(reqs,list) else [])[:3]:
        if not isinstance(r,dict):continue
        t=r.get('tool')
        try:
            if t=='search':
                from tukuyo_v1001.knowledge import search
                hits=[{'id':'k:'+str(x['id']),'text':x['text']} for x in search(Path(data),str(r.get('query',''))[:200],5)]
                for h in hits:mem_index[h['id']]=h['text']
                out.append({'tool':'search','query':r.get('query'),'results':hits})
            elif t=='solve':
                x=cognition.solve(data,str(r.get('question',''))[:1000])
                out.append({'tool':'solve','question':r.get('question'),'answer':x.get('answer'),'certain':not x.get('uncertain'),'reason':x.get('reason'),'explanation':x.get('explanation')})
            elif t=='calc':
                e=str(r.get('expression',''))
                if not re.fullmatch(r'[\d\s.+\-*/()]{1,200}',e):raise ValueError('EXPRESSION_CHARSET')
                out.append({'tool':'calc','expression':e,'value':proofs.number(proofs.calculate(e))})
            else:out.append({'tool':t,'error':'UNKNOWN_TOOL'})
        except Exception as ex:out.append({'tool':t,'error':type(ex).__name__})
    return out

def _determinate_meta(local):
    """claude-patch2: 'cannot be determined' / 'premises contradict' proven by complete model checking."""
    if local.get('reason') not in ('UNDETERMINED_BY_PREMISES','PREMISES_CONTRADICT') or local.get('orphans') or not local.get('proof'):return None
    from tukuyo_v1022 import logic2
    p=local['proof']
    try:
        if p['kind']=='logic_models':
            excl=[[tuple(x) for x in cl] for cl in p['excl_clauses']] if p.get('excl_clauses') else None
            v=logic2.eval_props(len(p['atoms']),[[tuple(x) for x in cl] for cl in p['clauses']],excl,p['query'])
        else:v=logic2.order_verdict(p['nodes'],[tuple(e) for e in p['edges']],p['query'])[0]
    except Exception:return None
    return local.get('explanation') if v==p['verdict'] and v in ('undetermined','contradiction') else None

def ask(data,query,local_first=True,mode='qa'):
    from tukuyo_v1019.lifecycle import require_alive
    require_alive(data)
    local_reason=None
    if local_first:
        from tukuyo_v1022 import cognition
        local=cognition.solve(data,query)
        # generation 4: problems with numbers are also read and checked by generation 4 (see tukuyo_g4.api.think)
        try:
            from tukuyo_g4 import api as g4_api
            local=g4_api.think(data,query,local)
        except Exception as e:  # noqa: BLE001 - generation 4 must never break llm-ask; the error is shown
            local={**local,'gen4_error':type(e).__name__+':'+str(e)[:200]}
        if local.get('recognized') and not local.get('uncertain'):
            out={'ok':True,'version':'v1022.5+claude-patch4','source':'local-proof','status':'verified','answer':local['answer'],'confidence':local['confidence'],'uncertain':False,'proof':local.get('proof'),'explanation':local.get('explanation')}
            if local.get('gen4'):out['gen4']=local['gen4']
            _append_log(data,{'schema':SCHEMA,'utc_ns':time.time_ns(),'query':query,'source':'local-proof','status':'verified','answer':str(local['answer'])})
            return out
        meta=_determinate_meta(local)
        if meta:
            _append_log(data,{'schema':SCHEMA,'utc_ns':time.time_ns(),'query':query,'source':'local-proof','status':'verified','answer':meta,'determinate':False})
            return {'ok':True,'version':'v1022.5+claude-patch4','source':'local-proof','status':'verified','answer':meta,'determinate':False,'confidence':.9,'uncertain':False,'proof':local.get('proof'),'explanation':meta}
        local_reason=local.get('reason');local_note=local.get('explanation')
    else:local_note=None
    cfg=providers.config()
    if cfg.get('provider') is None:
        _append_log(data,{'schema':SCHEMA,'utc_ns':time.time_ns(),'query':query,'source':'none','status':'abstained','answer':'','local_reason':local_reason})
        # claude-patch3: say what the core DID find (e.g. which attributes of that entity it remembers)
        msg='外部の思考エンジン（LLM）が未設定で、内蔵コアだけでは答えを確定できません。'+(local_note or '')
        return {'ok':True,'version':'v1022.5+claude-patch4','source':'none','status':'abstained','answer':msg,'confidence':0.,'uncertain':True,'local_reason':local_reason,'llm':providers.public_config()}
    ctx=context(data,query);mem_index={m['id']:m['text'] for m in ctx.get('memories',[])}
    user=json.dumps({'mode':mode,'question':query,'tukuyo_state':ctx},ensure_ascii=False)
    attempts=[];reply=None;o=None;tool_log=[];tool_rounds=0;repaired=False
    for step in range(4):
        prompt=user
        if tool_log:prompt+='\n\n道具の結果: '+json.dumps(tool_log,ensure_ascii=False)
        if repaired:prompt+='\n\n前回の回答の検査結果: '+json.dumps(attempts[-1]['checks'],ensure_ascii=False)+'\n失敗した主張を直して、同じJSON形式で答え直してください。'
        try:
            reply=providers.complete(SYSTEM+TOOLS_NOTE,prompt);o=providers.extract_json(reply.text)
        except providers.LLMError as e:
            attempts.append({'round':step,'error':str(e)});o=None;break
        if 'answer' not in o and o.get('tool_requests') and tool_rounds<2:
            tool_log+=_run_tools(data,o['tool_requests'],mem_index);tool_rounds+=1;attempts.append({'round':step,'tools':[t.get('tool') for t in tool_log]});continue
        claims=o.get('claims',[]);checks,checkable,failed,external=_check(data,claims,mem_index);unbacked=_numbers_unbacked(o.get('answer',''),claims,query)
        relevant=sum(1 for c,ck in zip(claims if isinstance(claims,list) else [],checks) if ck.get('result')=='OK' and _relevant(c,o.get('answer','')))
        support=_support_text(query,claims,checks)
        content_unbacked=sorted(t for t in _content_tokens(o.get('answer','')) if t not in support.lower() and t not in _content_tokens(support))
        st=_status(checkable,failed,external,bool(o.get('unknown')),unbacked,content_unbacked,relevant)
        attempts.append({'round':step,'status':st,'checks':checks,'unbacked_numbers':unbacked,'unsupported_content':content_unbacked[:20],'relevant_checked_claims':relevant})
        if st!='rejected' or repaired:break
        repaired=True
    graded=[a for a in attempts if 'status' in a]
    if o is None or not graded:
        res={'source':'llm','status':'error','answer':'思考エンジンに接続できませんでした。' if o is None else '思考エンジンが答えを出しませんでした。','confidence':0.,'uncertain':True}
    else:
        st=graded[-1]['status'];llm_conf=float(o.get('confidence',0.5) or 0.5);llm_conf=max(0.,min(1.,llm_conf))
        cap={'verified':.95,'partially_verified':.8,'unverified':.6,'abstained':0.,'rejected':0.}[st]
        conf=round(min(llm_conf,cap),6)
        answer=o.get('answer','') if st!='rejected' else '思考エンジンの答えが内部の検算と合わなかったため、答えを保留します。'
        res={'source':'llm','status':st,'answer':str(answer),'confidence':conf,'uncertain':st!='verified' or conf<.7}
    rec={'schema':SCHEMA,'utc_ns':time.time_ns(),'query':query,'source':'llm','status':res['status'],'answer':res['answer'],'local_reason':local_reason,
         'provider':reply.provider if reply else cfg.get('provider'),'model':reply.model if reply else cfg.get('model'),'latency_ms':reply.latency_ms if reply else None,
         'context_sha256':hashlib.sha256(user.encode()).hexdigest(),'attempts':attempts,'tools':tool_log}
    _append_log(data,rec)
    return {'ok':True,'version':'v1022.5+claude-patch4',**res,'attempts':attempts,'tools':tool_log,'provider':rec['provider'],'model':rec['model'],'claim_boundary':CLAIM_BOUNDARY}

def _audit_answers(data):
    from tukuyo_common.journal import load_events
    p=log_path(data)
    if not p.exists():return {'ok':True,'version':'v1022+claude-patch1','answers':0}
    prev=whole.ZERO;errs=[];n=0
    for i,e in enumerate(load_events(p),1):
        q=dict(e);h=q.pop('event_sha256',None);n=i
        if e.get('seq')!=i or e.get('prev_sha256')!=prev or h!=whole.sha_obj(q):errs.append(f'LLM_LOG_CHAIN:{i}');break
        prev=h
    hd=_read(head_path(data)) or {}
    if not errs and (hd.get('count')!=n or hd.get('head_sha256')!=prev):errs.append('LLM_LOG_HEAD')
    return {'ok':not errs,'version':'v1022+claude-patch1','answers':n,'errors':errs}

def audit(data):
    from .study import audit as audit_study
    try:answers=_audit_answers(data)
    except (ValueError,TypeError,KeyError,OSError) as exc:
        answers={'ok':False,'answers':0,'errors':['LLM_LOG_PARSE:'+type(exc).__name__]}
    studies=audit_study(data)
    return {**answers,'ok':answers['ok'] and studies['ok'],'version':'v1022.5-fusion',
            'studies':studies['studies'],'errors':answers.get('errors',[])+studies['errors']}
