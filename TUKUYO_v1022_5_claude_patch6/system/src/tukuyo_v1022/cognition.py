"""Bounded local learning from teacher dialogue, without a runtime LLM.

Numeric literals are abstracted into event templates. Polarity, actor and time
are retained. Lexical aliases and explicit facts carry supervised provenance.
The system does not store a question-to-answer lookup table.
"""
from __future__ import annotations
import copy,json,re,time,unicodedata
from pathlib import Path
from tukuyo_common.atomic_fs import atomic_write_bytes
from tukuyo_v977 import whole_state as whole
from tukuyo_v1019.transaction import transactional
from tukuyo_v1019.lifecycle import require_alive
from . import proofs,store

NS='v1022';COMPONENT='local_cognition_v1022';SCHEMA='tukuyo.v1022.cognition/1'
UNITS='個|枚|本|冊|台|人';BOXES='箱|袋|パック|ケース|束'
KANJI={'〇':0,'零':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
def _kanji(m):
    n=part=0
    for c in m.group():
        if c in KANJI:part=KANJI[c]
        else:n+=(part or 1)*{'十':10,'百':100,'千':1000}[c];part=0
    return str(n+part)
def normalize(s):
    s=unicodedata.normalize('NFKC',str(s)).strip()
    return re.sub(r'[〇零一二三四五六七八九十百千]+(?=\s*(?:'+UNITS+'|'+BOXES+'|円))',_kanji,s)
def _default(data):
    return {'schema':SCHEMA,'individual_id':whole._live_identity(data)['individual_id'],'rounds':0,'teachers':{},
            'aliases':{},'event_rules':{},'facts':[],'conflicts':0,'rejected':0,
            'dialogue_head':whole.ZERO,'inherited_public_learning':[],'seed_provenance':None}
def _validate(s):
    if s.get('schema')!=SCHEMA or type(s.get('rounds')) is not int or not 0<=s['rounds']<=10000:raise ValueError('V1022_COGNITION_STATE')
    if len(s['event_rules'])>512 or len(s['aliases'])>512 or len(s['facts'])>1024:raise ValueError('V1022_LEARNING_LIMIT')
    for r in s['event_rules'].values():
        if type(r.get('direction')) is not int or r['direction'] not in (-1,0,1) or not isinstance(r.get('support'),list):raise ValueError('V1022_RULE_SCHEMA')
    if any(not isinstance(k,str) or not isinstance(v,str) or not 0<len(k)<=100 or not 0<len(v)<=100 for k,v in s['aliases'].items()):raise ValueError('V1022_ALIAS_SCHEMA')
def state(data):
    if not (Path(data)/NS/'commits').exists():return _default(data)
    s=store.load(data,NS,COMPONENT,_validate)
    if s['individual_id']!=whole._live_identity(data)['individual_id']:raise ValueError('V1022_COGNITION_IDENTITY')
    return s
def _no(reason,recognized=True):return {'ok':True,'answer':None,'confidence':0.,'uncertain':True,'recognized':recognized,'reason':reason,'proof':None}
def _yes(a,p,confidence=.9):
    if not proofs.check(p,a):return _no('PROOF_REJECTED')
    return {'ok':True,'answer':str(a),'confidence':confidence,'uncertain':False,'recognized':True,'proof':p,
            'verification_evidence':{'mode':'LOCAL_PROOF_CHECK','proof_checked':True,'premise_grounding':'BOUNDED_PARSER_OR_SUPERVISED_MEMORY'}}
def _template(s):
    s=re.sub(r'\d+\s*(?:'+UNITS+'|'+BOXES+')','<Q>',normalize(s))
    return re.sub(r'[\s。、,!?？！]','',s).replace('<Q>を','<Q>')
def _aliases(s,learned):
    for surface,canonical in sorted(learned['aliases'].items(),key=lambda x:-len(x[0])):s=s.replace(surface,canonical)
    return s
def package(s):
    m=re.search(rf'1\s*({BOXES})\s*(?:に|あたり|には)?\s*(\d+)\s*({UNITS})(?:入り)?\s*(?:が|の|を|[、,\s])*\s*(\d+)\s*\1',s)
    if m:return {'per':int(m[2]),'count':int(m[4]),'unit':m[3],'container':m[1],'end':m.end()}
    m=re.search(rf'(\d+)\s*({UNITS})\s*入り(?:の)?\s*({BOXES})?\s*(?:を|が|で|[×xX*])?\s*(\d+)\s*({BOXES}|つ)',s)
    if m:
        if m[3] and m[5]!='つ' and m[3]!=m[5]:return None
        return {'per':int(m[1]),'count':int(m[4]),'unit':m[2],'container':m[3] or m[5],'end':m.end()}
    return None
def clauses(s):return [x.strip() for x in re.split(r'[。.!！?？、,]|(?:が|けれど|しかし)\s*(?=\d)',s) if x.strip()]
def inventory(s,learned):
    p=package(s)
    if p:
        initial=p['per']*p['count'];per=p['per'];unit=p['unit'];box=p['container'];tail=s[p['end']:]
        tail=re.sub(r'^(?:[、, ]*(?:今の在庫として|在庫として|手元に|ここに))?(?:あります|ある|です|を買いました|を持っています|を用意しました)?[。 ]*','',tail)
    else:
        frames=list(re.finditer(rf'(\d+)\s*({UNITS})(?:あります|ある|持っています|持っている|ありました|あった|あり)',s))
        m=frames[0] if frames else None
        if not m:return _no('NO_INVENTORY_FRAME',False)
        if len(frames)>1 or re.search(rf'\d+\s*({UNITS})',s[:m.start()]):return _no('MULTIPLE_INITIAL_INVENTORIES_UNSUPPORTED')
        initial=int(m[1]);per=1;unit=m[2];box='__none__';tail=s[m.end():]
    if initial>10**9 or per>10**6:return _no('QUANTITY_LIMIT')
    if re.search(r'[「」『』“”]|事実ではない|誤り|二種類|両方|合わせる',s):return _no('QUOTED_REVISED_OR_MIXED_INVENTORY_UNSUPPORTED')
    if re.search(r'\d+\s*[〜~～-]\s*\d+|少なくとも|最大|最低|以上|以下|未満|高々|せいぜい|[-−]\s*\d+|\d+\.\d+\s*(?:'+UNITS+'|'+BOXES+')',s):return _no('NON_EXACT_OR_SIGNED_COUNT')
    # claude-patch1: approximate ("5個ぐらい", "約5個") and disjunctive ("3個か4個") counts are not exact either.
    if re.search(r'\d+\s*(?:'+UNITS+'|'+BOXES+r')?\s*(?:ぐらい|くらい|ほど|程度|前後|ちょっと)|(?:約|およそ|ほぼ|だいたい|大体)\s*\d|数\s*(?:'+UNITS+'|'+BOXES+r')|(?:何(?:'+UNITS+'|'+BOXES+r')|いくつ)か(?=\s*(?:を|が|は)?\s*[^\s?？。、])|\d+\s*(?:'+UNITS+'|'+BOXES+r')?\s*(?:か|または|もしくは|or)\s*\d',s):return _no('NON_EXACT_OR_SIGNED_COUNT')
    asked=re.search(r'何('+UNITS+'|'+BOXES+'|円|kg|g|m|cm)',s)
    if not asked:
        # claude-patch1: "箱はいくつ？" / "袋の数は？" ask for the container count.
        asked=re.search(r'('+BOXES+r')(?:は|の数は|の個数は)\s*(?:いくつ|何個|どれだけ)',s)
    if asked and asked[1] not in (unit,box):return _no('QUERY_UNIT_MISMATCH')
    remaining=bool(re.search(r'残り|残数|残った|今の在庫|現在の在庫|何個にな',tail) or re.search(rf'\d+\s*({UNITS}|{BOXES})',tail))
    if not remaining:
        if not re.search(r'何|いくつ|総数|合計|全部',tail):return _no('QUERY_ROLE_MISSING')
        n=p['count'] if p and asked and asked[1]==box else initial
        return _yes(n,{'kind':'inventory','initial':n,'per':per,'events':[],**({'package_count':p['count']} if p else {})})
    events=[]
    for c in clauses(tail):
        if re.search(r'何|いくつ|残り|残数|残った',c) and not re.search(r'\d',c):continue
        qs=list(re.finditer(rf'(\d+)\s*({UNITS}|{BOXES})',c))
        if not qs:
            if c in ('足りないです','足りません','在庫としてあります','今の在庫としてあります','あります','ある'):continue
            if events and events[-1]['source']=='scope_time_polarity' and events[-1]['direction']==0 and re.fullmatch(r'(?:だが)?まだ(?:実行|実施)していない',c):continue
            return _no('UNCOVERED_INVENTORY_CLAUSE')
        if any(q[2] not in (unit,box) for q in qs):return _no('EVENT_UNIT_MISMATCH')
        if re.search(r'不明|かどうか|かもしれ|ないとは|なくは|限らない|疑い|らしい|そうです|と言った|と言われ|と報告|と聞|と嘘|嘘|誤報|訂正|夢|想像|もし|なら|たら',c):return _no('AMBIGUOUS_EVENT_MODALITY')
        other=bool(re.search(r'別の在庫|他の在庫|別の人が別の|友人の在庫|他人の在庫|隣店の在庫',c));future=bool(re.search(r'明日|来週|予定|つもり|食べたい|使いたい|売りたい|渡したい|欲しい|まだ実行していない|まだ食べていない',c))
        negative=bool(re.search(r'(?:食べ|使[わっい]|使用し|消費し|捨て|渡[さし]|返[さし]|売[らり]|返品し|借り|もら[わっ])(?:てい)?(?:ません|なかった|ない|ず|なくて|なかっ)',c))
        t=_template(_aliases(c,learned));r=learned['event_rules'].get(t)
        # claude-patch1: rules are recorded from the raw surface, but lookup used to apply aliases
        # first, so an alias such as 補充しました->補充した hid the learned rule. Try both forms.
        raw=_template(c)
        if r is None:r=learned['event_rules'].get(raw)
        if r is None:
            matches=[(k,r) for k,r in learned['event_rules'].items() if k.startswith('<Q>') and (t.endswith(k) or raw.endswith(k))]
            if matches:r=max(matches,key=lambda x:len(x[0]))[1]
        if other or future or negative:direction=0;source='scope_time_polarity'
        elif re.search(r'食べ|使っ|使い|使用|消費|捨て|渡し|あげ|返却|返し',c):direction=-1;source='bounded_builtin'
        elif re.search(r'もらっ|もらい|追加|買い足|増え',c):direction=1;source='bounded_builtin'
        elif re.search(r'開け|数え|確認',c):direction=0;source='non_consumption'
        elif r and r.get('conflict'):return _no('LEARNED_RULE_CONFLICT')
        elif r and len(r['support'])>=2:direction=r['direction'];source='learned:'+r['id']
        else:return _no('UNKNOWN_EVENT_MEANING')
        if source in ('bounded_builtin','non_consumption'):
            kinds=sum(bool(re.search(pattern,c)) for pattern in (r'食べ|使っ|使い|使用|消費|捨て|渡し|あげ|返却|返し',r'もらっ|もらい|追加|買い足|増え',r'開け|数え|確認',r'借り|返品|売っ|売り|紛失|失い|盗ま'))
            if kinds>1:return _no('MIXED_EVENT_CLAUSE_UNSUPPORTED')
        if source=='bounded_builtin' and re.search(r'(?:食べる|使う|捨てる|渡す|食べます|使います)(?:ところ|前|そう|$)',c):return _no('EVENT_NOT_ESTABLISHED_AS_COMPLETED')
        for q in qs:events.append({'quantity':int(q[1]),'direction':direction,'factor':per if q[2]==box else 1,'clause':c,'source':source})
    n=initial+sum(e['quantity']*e['direction']*e['factor'] for e in events)
    if n<0:return _no('OVERCONSUMPTION')
    if asked and asked[1]==box:
        if any(e['direction'] and e['factor']==1 for e in events):return _no('PARTIAL_CONTAINER_UNDERDETERMINED')
        initial=p['count'];events=[{**e,'factor':1} for e in events];n=initial+sum(e['quantity']*e['direction'] for e in events)
    return _yes(n,{'kind':'inventory','initial':initial,'per':per,'events':events,'coverage':'ALL_BOUNDED_CLAUSES',**({'package_count':p['count']} if p else {})})
def _prop(s):
    s=s.strip().rstrip('。?？');s=re.sub(r'(?:ですか|であるか|です|である|だ|か)$','',s)
    return re.sub(r'^([^、。 ]{1,30})は',r'\1が',s)
def logic(s):
    parts=[x.strip() for x in re.split(r'[。.!！]',s) if x.strip()];queries=[x for x in parts if re.search(r'[?？]$',x)]
    if not queries:return _no('NO_LOGIC_QUERY',False)
    qs=queries[0];rules=[];premises=[];categories=[];comparisons=[];unsupported=False
    for c in parts:
        if c in queries:continue
        m=re.fullmatch(r'すべての(.+?)は(.+?)(?:です|である|だ)',c)
        if m:categories.append((m[1],m[2]));continue
        m=re.fullmatch(r'(?:もし)?(.+?)(?:ならば|なら|であれば)(.+)',c)
        if m:rules.append((_prop(m[1]),_prop(m[2])));continue
        m=re.fullmatch(r'(.+?)は(.+?)より(大きい|高い|速い|重い)(?:です)?',c)
        if m:comparisons.append((m[1],m[2],m[3]));continue
        if re.search(r'相関|原因|必ず|かもしれ|または|だけ|否定|ない',c):unsupported=True
        premises.append(_prop(c))
    if not categories and not comparisons and not rules:return _no('NO_LOGIC_FRAME',False)
    if unsupported:return _no('LOGIC_SCOPE_UNSUPPORTED')
    if comparisons:
        dims={d for a,b,d in comparisons};edges={(a,b) for a,b,d in comparisons}
        if len(dims)!=1:return _no('COMPARISON_DIMENSION_MISMATCH')
        closure=set(edges)
        for _ in range(32):
            new={(a,d) for a,b in closure for c,d in closure if b==c};n=len(closure);closure|=new
            if len(closure)==n:break
        if any(a==b for a,b in closure):return _no('COMPARISON_CYCLE')
        m=re.fullmatch(r'(.+?)は(.+?)より(大きい|高い|速い|重い)(?:ですか|か)?[?？]',qs)
        if not m or m[3] not in dims:return _no('COMPARISON_QUERY_UNSUPPORTED')
        if (m[1],m[2]) not in closure:return _no('NO_COMPARISON_PROOF')
        premises=[a+'>'+b for a,b in edges];rules=[(a+'>'+b,a+'>'+d) for a,b in closure for c,d in edges if b==c]
        conclusion=m[1]+'>'+m[2];answer=f'{m[1]}は{m[2]}より{m[3]}関係にあります。'
    else:
        entities={p.split('が',1)[0] for p in premises if 'が' in p}
        for e in entities:rules.extend((e+'が'+a,e+'が'+b) for a,b in categories)
        conclusion=_prop(qs);answer=re.sub(r'(?:ですか|か)$','',qs.rstrip('?？'))+'です。'
    # claude-patch1: "雨が降っている" asserts that the event-noun antecedent "雨" holds. Only a closed list
    # of plain occurrence predicates counts; hearsay, dreams, plans etc. do not fullmatch and stay unproven.
    antecedents={a for a,b in rules}
    for p in list(premises):
        m=re.fullmatch(r'(.{1,20}?)が(?:降って(?:いる|います)|降った|降りました|降る|降ります|吹いて(?:いる|います)|吹いた|吹く|起きて(?:いる|います)|起きた|起こって(?:いる|います)|起こった|発生して(?:いる|います)|発生した|来て(?:いる|います)|来た|続いて(?:いる|います)|続いた)',p)
        if m:
            subject=m[1]
            # v1022.1 regression fix: a conditional antecedent is normally a full
            # proposition (e.g. 雨が降る), not just its event noun (雨).  Ground the
            # matching antecedent proposition from a plain occurrence premise.
            for a in sorted(antecedents):
                if a==subject or re.fullmatch(re.escape(subject)+r'が(?:降る|降ります|吹く|吹きます|起きる|起こる|発生する|来る|続く)',a):
                    if a not in premises:premises.append(a)
    known=set(premises);steps=[]
    for _ in range(32):
        changed=False
        for a,b in rules:
            if a in known and b not in known:known.add(b);steps.append([a,b]);changed=True
        if not changed:break
    if conclusion not in known:return _no('PREMISE_NOT_ESTABLISHED')
    return _yes(answer,{'kind':'logic','premises':premises,'rules':[list(x) for x in rules],'steps':steps,'conclusion':conclusion,'answer':answer})
def _memory(s,learned):
    q=_aliases(re.split(r'質問[:：]',s)[-1],learned);facts=learned['facts']
    prefix=re.split(r'質問[:：]',s)[0] if re.search(r'質問[:：]',s) else ''
    scoped=[f for f in facts if f.get('context')==prefix] if prefix else []
    if scoped:facts=scoped
    matches=[f for f in facts if f['entity'] in q and f['relation'] in q]
    if matches:
        longest=max(len(f['entity']) for f in matches);matches=[f for f in matches if len(f['entity'])==longest]
    if not matches:return _no('MEMORY_PREMISES_MISSING',False)
    if len({f['value'] for f in matches})!=1:return _no('MEMORY_CONFLICT_OR_TIME_AMBIGUITY')
    return _yes(matches[0]['value'],{'kind':'memory','facts':matches,'normalized_query':q},.85)
def _numbers_used(query,proof):
    """claude-patch3: numbers of the question (except a per-unit '1' as in 1個/1本/1人) must occur in the proof."""
    q=unicodedata.normalize('NFKC',str(query))
    need=[m.group() for m in re.finditer(r'\d+(?:\.\d+)?',q) if not (m.group()=='1' and re.match(r'\s*(?:'+UNITS+'|'+BOXES+r'|日|時間|分|か月|週間|年|回|杯|袋|冊|ページ)',q[m.end():]))]
    blob=json.dumps(proof,ensure_ascii=False)
    have=set(re.findall(r'\d+(?:\.\d+)?',blob))
    return all(n in have or str(proofs.number(proofs.calculate(n))) in have for n in need)
SITUATION_REASONS={'SITUATION_TARGET_NOT_DETERMINED':'聞かれている人や物のはじめの数がお話に書かれていないので、答えを決められません。',
    'SITUATION_EVENT_NOT_IN_STORY':'聞かれている出来事がお話の中にありません。','SITUATION_AMBIGUOUS_TARGET':'どの人（物）の数を聞いているのか決められません。',
    'SITUATION_AMBIGUOUS_OBJECT':'どの物が増えたり減ったりしたのか決められません。','SITUATION_UNKNOWN_TARGET':'聞かれている人や物がお話に出てきません。',
    'SITUATION_TIME_OF_QUESTION_UNCLEAR':'いつの数を聞いているのか（はじめか今か）決められません。','SITUATION_HEDGED_OR_NEGATED':'数や出来事がはっきり決まっていないので、答えを確定しません。',
    'SITUATION_HEDGED_OR_UNKNOWN_AMOUNT':'数がはっきり決まっていないので、答えを確定しません。','SITUATION_AMBIGUOUS_VERB':'見方によって増えるとも減るとも読める動詞なので、決められません。',
    'SITUATION_ACTIVITY_EFFECT_UNKNOWN':'読んだ・数えたなどの出来事で数が減るのかどうか決められません。','SITUATION_UNKNOWN_QUESTION_VERB':'質問の動詞の意味を読み取れません。'}
def _gate_ok(query,res):
    from .semantic_gate import audit as _semantic_audit
    try:return bool(_semantic_audit(query,res['answer'],res.get('proof')).get('ok'))
    except Exception:return False
def _same_number(a,b):
    try:return proofs.calculate(str(a))==proofs.calculate(str(b))
    except (ValueError,SyntaxError,ZeroDivisionError,OverflowError):return str(a)==str(b)
def _solve_core(data,query,formal_task=None):
    """claude-patch6: read what the question asks before any producer answers it.

    The situation model (situation.py) is authoritative for every question that does not ask for
    the current amount of the story's main holding: the starting amount, an event's amount, what
    another person has or received, another object. For a plain "how many now / left" question the
    older producers keep precedence (their behaviour and learned rules are unchanged); the model is a
    second, separately built reading that answers when they abstain and blocks when they disagree."""
    if formal_task is not None:return _solve_core_v5(data,query,formal_task)
    from .situation import solve as _situation
    sit=_situation(query)
    # several holders or objects: only this model keeps them apart, so it decides (patch5 answered
    # 「りんごが12個…みかんを3個もらいました。りんごは何個？」 with 10)
    if sit and (sit.get('role') not in (None,'remain','total') or sit.get('holdings',1)>1):
        if 'answer' in sit:
            y=_yes(sit['answer'],sit['proof'],.93)
            if not y['uncertain']:return {**y,'question_role':sit['role']}
            return y
        return {**_no(sit['refused']),'question_role':sit.get('role'),'explanation':SITUATION_REASONS.get(sit['refused'])}
    r=_solve_core_v5(data,query,formal_task)
    if sit and 'answer' in sit:
        if r.get('answer') is None or r.get('uncertain'):
            if r.get('reason') in ('LEARNED_RULE_CONFLICT','AMBIGUOUS_EVENT_MODALITY','WORD_PROBLEM_EVENT_NOT_CONFIRMED','HEDGED_OR_HYPOTHETICAL_QUANTITIES','NON_EXACT_OR_SIGNED_COUNT','OVERCONSUMPTION'):return r
            y=_yes(sit['answer'],sit['proof'],.92)
            if not y['uncertain']:return {**y,'question_role':sit['role'],'second_reading':'SITUATION_MODEL_ONLY'}
        elif not _same_number(r['answer'],sit['answer']) and (r.get('proof') or {}).get('kind') in ('inventory','arithmetic','deliberation'):
            old_ok,new_ok=_gate_ok(query,r),_gate_ok(query,sit)
            if new_ok and not old_ok:
                y=_yes(sit['answer'],sit['proof'],.92)
                if not y['uncertain']:return {**y,'question_role':sit['role'],'second_reading':'OLDER_READING_DID_NOT_ACCOUNT_FOR_THE_QUESTION'}
            if old_ok and not new_ok:return r
            return {**_no('PRODUCERS_DISAGREE'),'withheld_answer':str(r['answer']),'situation_answer':sit['answer'],
                    'explanation':f'二つの読み方で答えが食い違った（{r["answer"]} と {sit["answer"]}）ので、答えを確定しません。'}
        else:r={**r,'second_reading':'SITUATION_MODEL_AGREES'}
    # claude-patch6: problem families no older producer reads (mathprob.py). They answer only when the older
    # producers abstained, and a disagreement with an older answer withholds both.
    from .mathprob import solve as _mathprob
    mp=_mathprob(query)
    if mp and 'answer' in mp:
        if r.get('answer') is None or r.get('uncertain'):
            if r.get('reason') in ('HEDGED_OR_HYPOTHETICAL_QUANTITIES','NON_EXACT_OR_SIGNED_COUNT','DELIBERATION_AMBIGUOUS_QUANTITY'):return r
            if r.get('reason')=='WORD_PROBLEM_EVENT_NOT_CONFIRMED' and not mp.get('negation_ok'):return r
            y=_yes(mp['answer'],mp['proof'],.92)
            if not y['uncertain']:return y
        elif not _same_number(r['answer'],mp['answer']) and (r.get('proof') or {}).get('kind') in ('inventory','arithmetic','deliberation','meta_derivation','situation','qtime'):
            old_ok,new_ok=_gate_ok(query,r),_gate_ok(query,mp)
            if new_ok and not old_ok:
                y=_yes(mp['answer'],mp['proof'],.92)
                if not y['uncertain']:return {**y,'second_reading':'OLDER_READING_DID_NOT_ACCOUNT_FOR_THE_QUESTION'}
            if old_ok and not new_ok:return r
            return {**_no('PRODUCERS_DISAGREE'),'withheld_answer':str(r['answer']),'mathprob_answer':mp['answer'],
                    'explanation':f'二つの読み方で答えが食い違った（{r["answer"]} と {mp["answer"]}）ので、答えを確定しません。'}
    return r
def _solve_core_v5(data,query,formal_task=None):
    learned=state(data);s=normalize(query)
    if len(s)>10000:return _no('QUERY_LIMIT')
    if formal_task is not None:
        p=proofs.plan(formal_task)
        if p['route'] is None:return {**_no(p['reason']),'planning':p}
        # v1022.2: do not stop at the first optimal route. Generate bounded
        # alternatives and test one-action-loss contingencies as a self-critique.
        alternatives=proofs.alternative_plans(formal_task,limit=4)
        robustness=proofs.assess_plan_robustness(formal_task)
        route=bool(re.search(r'行動(?:名の)?列|経路|手順|順番|route|action sequence',s,re.I))
        cost=not route and bool(re.search(r'費用|cost',s,re.I));answer=str(p['cost']) if cost else json.dumps(p['route'],ensure_ascii=False)
        proof={'kind':'plan_cost' if cost else 'plan','task':formal_task,'plan':p,
               'alternatives':alternatives,'robustness':robustness}
        return _yes(answer,proof,.95)
    # claude-patch3: exact unit / clock / weekday / calendar / percent questions (whole-question forms only)
    from .qtime import solve as _qtime
    qt=_qtime(query)
    if qt:
        y=_yes(qt['answer'],{'kind':'qtime','qkind':qt['kind'],'source_query':str(query),'answer':qt['answer'],'expression':qt.get('expression')},.95)
        if not y['uncertain']:return y
    # Shared refusal takes precedence over older multi-step parsers. A known
    # inventory frame can still account for a negated event as a zero change.
    from .wordprob import solve as _wordprob
    word_candidate=_wordprob(query)
    if word_candidate and word_candidate.get('refused'):
        guarded_inventory=inventory(s,learned)
        if guarded_inventory.get('recognized'):return guarded_inventory
        return _no(word_candidate['refused'])
    m=re.fullmatch(r'(?:計算(?:して)?[:： ]*)?([\d\s.+\-*/()]+)(?:\s*(?:=|は)?\s*(?:いくつ|何|計算して)?[?？]?)',s)
    if m:
        try:return _yes(proofs.number(proofs.calculate(m[1])),{'kind':'arithmetic','expression':m[1]},.98)
        except (ValueError,SyntaxError,ZeroDivisionError,OverflowError):return _no('ARITHMETIC_UNSUPPORTED')
    # claude-patch1: worded arithmetic ("50から13を引くと？", "4の3倍は？") rewritten to a pure expression.
    from .nl_arith import expression as _nl_expression
    e=_nl_expression(query)
    if e:
        try:return _yes(proofs.number(proofs.calculate(e)),{'kind':'arithmetic','expression':e,'from_words':True},.97)
        except (ValueError,SyntaxError,ZeroDivisionError,OverflowError):return _no('ARITHMETIC_UNSUPPORTED')
    # v1022.3: dependency-graph meta reasoning.  Multiple derivations of the
    # same target are explored; failed strategies are diagnosed and successful
    # alternatives must agree before commitment.  An independent parser repeats
    # the computation before the answer is exposed.
    from .meta_reasoning import solve as _meta_local
    mr=_meta_local(query)
    if mr is not None:
        if mr.get('answer') is None:
            out=_no(mr.get('reason','META_REASONING_ABSTAIN'))
            out['meta_reasoning']={'target':mr.get('target'),'successful_strategies':mr.get('successful_strategies',[]),
                                   'failed_strategies':mr.get('failed_strategies',[]),
                                   'information_requests':mr.get('information_requests',[]),
                                   'conflict_resolution':mr.get('conflict_resolution')}
            return out
        from .meta_reasoning_verify import verify as _verify_meta
        mv=_verify_meta(query,str(mr['answer']))
        if not (mv.get('recognized') and mv.get('decidable') and mv.get('supported')):return _no('META_SECONDARY_VERIFY_REJECTED')
        out=_yes(mr['answer'],mr['proof'],mr.get('confidence',.92))
        out['meta_reasoning']={'target':mr.get('target'),'successful_strategies':mr.get('successful_strategies',[]),
                               'failed_strategies':mr.get('failed_strategies',[]),'evidence':mr.get('reasoning_evidence',{})}
        out['verification_evidence']={**out.get('verification_evidence',{}),'secondary_semantic_check':'PASS',
                                      'problem_decomposition':'DEPENDENCY_GRAPH','strategy_comparison':True}
        return out
    # v1022.2: finite hypothesis generation compares multiple candidate rules,
    # searches for a bounded counterexample, and answers only when the supported
    # hypothesis is unique inside the declared class. A separate parser repeats
    # the decision before commitment.
    from .hypothesis import solve as _hypothesis_local
    hr=_hypothesis_local(query)
    if hr is not None:
        if hr.get('answer') is None:return _no(hr.get('reason','HYPOTHESIS_ABSTAIN'))
        from .hypothesis_verify import verify as _verify_hypothesis
        hv=_verify_hypothesis(query,str(hr['answer']))
        if not (hv.get('recognized') and hv.get('decidable') and hv.get('supported')):return _no('HYPOTHESIS_SECONDARY_VERIFY_REJECTED')
        out=_yes(hr['answer'],hr['proof'],hr.get('confidence',.91))
        out['verification_evidence']={**out.get('verification_evidence',{}),'secondary_semantic_check':'PASS','candidate_generation':'FINITE_BOUNDED','counterexample_search':True}
        return out
    # v1022.1+: bounded multi-step deliberation. The parser proposes a formal
    # derivation; proofs.check replays it and an independent re-parser must agree.
    from .deliberation import solve as _deliberate_local
    dr=_deliberate_local(query)
    if dr is not None:
        if dr.get('answer') is None:return _no(dr.get('reason','DELIBERATION_ABSTAIN'))
        from .deliberation_verify import verify as _verify_deliberation
        dv=_verify_deliberation(query,str(dr['answer']))
        if not (dv.get('recognized') and dv.get('decidable') and dv.get('supported')):return _no('DELIBERATION_SECONDARY_VERIFY_REJECTED')
        if word_candidate and proofs.number(word_candidate['value'])!=str(dr['answer']):
            # The legacy unit-price parser can ignore a second purchase. The
            # new schema checks every number before proposing its expression.
            w=word_candidate
            out=_yes(proofs.number(w['value']),{'kind':'arithmetic','expression':w['expression'],'from_words':True,'schema':w['schema'],'unit':w['unit'],'source_query':str(query)},.93)
            out['fusion_resolution']={'basis':'COMPLETE_NUMBER_COVERAGE','discarded_partial_legacy_answer':str(dr['answer'])}
            return out
        # claude-patch3: every number in the question must be used by the derivation. v1022.5 answered
        # 「2000円で、1個450円のケーキを3個買いました。おつりは？」 with 1350 (the 2000 was never read).
        if not _numbers_used(query,dr['proof']):
            if word_candidate:
                w=word_candidate
                return _yes(proofs.number(w['value']),{'kind':'arithmetic','expression':w['expression'],'from_words':True,'schema':w['schema'],'unit':w['unit'],'source_query':str(query)},.93)
            return _no('DELIBERATION_IGNORED_NUMBERS')
        out=_yes(dr['answer'],dr['proof'],dr.get('confidence',.94))
        out['verification_evidence']={**out.get('verification_evidence',{}),'secondary_semantic_check':'PASS'}
        return out
    r=inventory(s,learned)
    # claude-patch3: the inventory parser declines shapes it was not built for (two separate stocks, a role or
    # unit it does not ask about); a full-coverage word-problem schema may still answer those.
    # An unknown *event* verb stays in the teacher-learned domain; a comparison clause (「より9枚多く持っています」)
    # is not an event, so a non-event schema may answer it.
    if r['recognized'] and word_candidate and not word_candidate.get('refused') and (
            r.get('reason') in ('MULTIPLE_INITIAL_INVENTORIES_UNSUPPORTED','QUERY_ROLE_MISSING','QUERY_UNIT_MISMATCH') or
            r.get('reason')=='UNKNOWN_EVENT_MEANING' and word_candidate.get('schema') not in ('change_sequence','combine')):
        r={'recognized':False}
    if r['recognized']:return r
    # claude-patch2: other arithmetic word problems (full-coverage schemas, see wordprob.py)
    w=word_candidate
    if w and w.get('refused'):return _no(w['refused'])
    if w:
        y=_yes(proofs.number(w['value']),{'kind':'arithmetic','expression':w['expression'],'from_words':True,'schema':w['schema'],'unit':w['unit'],'source_query':str(query)},.93)
        if not y['uncertain']:return y
    r=logic(s)
    # claude-patch2: complete model checking for negation / contraposition / universals / order
    from .logic2 import solve as _logic2
    l2=_logic2(query)
    if l2 and l2['verdict']=='refused' and r['recognized']:
        return _no(l2.get('reason','LOGIC2_ABSTAIN'))
    if l2 and l2['verdict']!='refused':
        if l2['answer'] is not None:
            # Keep the previously verified modus-ponens surface when complete
            # model checking confirms it; legacy crosscheck expects a proposition.
            if r['recognized'] and not r['uncertain'] and (l2['verdict']=='yes' or l2['verdict'].startswith('derive:')):
                return {**r,'model_check_confirmed':True}
            y=_yes(l2['answer'],l2['proof'],.95)
            if not y['uncertain']:return {**y,'explanation':l2['explanation']}
        else:
            reason={'undetermined':'UNDETERMINED_BY_PREMISES','contradiction':'PREMISES_CONTRADICT','ambiguous':'AMBIGUOUS_DISJUNCTION'}.get(l2['verdict'],'LOGIC2_ABSTAIN')
            return {**_no(reason),'proof':l2['proof'],'explanation':l2['explanation'],'orphans':l2['orphans']}
    if r['recognized']:return r
    m=_memory(s,learned)
    if m['recognized']:return m
    # claude-patch2: the individual's own knowledge store (read-only)
    from .kqa import solve as _kqa
    k=_kqa(data,query)
    if k:
        if k.get('conflict'):return _no('MEMORY_CONFLICT_OR_TIME_AMBIGUITY')
        if k.get('missing'):
            known='、'.join(k['known_attributes'][:8])
            msg=f"「{k['entity']}」について覚えているのは{known}です。聞かれたことは覚えていません。" if known else f"「{k['entity']}」については、ほかのことは覚えていません。"
            return {**_no('MEMORY_ATTRIBUTE_MISSING'),'explanation':msg,'information_request':{'entity':k['entity'],'known_attributes':k['known_attributes']}}
        y=_yes(k['answer'],{'kind':'knowledge','records':k['records'],'entity':k['entity'],'attribute':k['attribute'],'value':k['value'],'match':k['match'],'source_query':str(query)},.85)
        if not y['uncertain']:return {**y,'explanation':'記憶「'+'」「'.join(x['text'] for x in k['records'])+'」より。'}
    return m
def solve(data,query,formal_task=None):
    r=_solve_core(data,query,formal_task)
    # claude-patch4: final commit gate (separately written tokenizer/parser; see semantic_gate.py)
    if r.get('answer') is not None and not r.get('uncertain') and formal_task is None:
        from .semantic_gate import audit as _semantic_audit
        g=_semantic_audit(query,r['answer'],r.get('proof'))
        if not g['ok']:
            out=_no(g['reason']);out['semantic_gate']=g;out['withheld_answer']=str(r['answer'])
            out['explanation']={'UNCOVERED_NUMERIC_OR_OPERATION':'問題の数（'+'、'.join(g.get('unexplained',[]))+'）を使い切った説明になっていないので、答えを確定しません。',
                                'INDEPENDENT_PARSER_DISAGREES':'別に書かれた読み取りが違う値（'+str(g.get('independent_reading'))+'）を出したので、答えを確定しません。',
                                'CONTAINER_OR_CONTENT_AMBIGUOUS':'箱の数を聞いているのか中身の数を聞いているのか決められません。',
                                'PART_ASKED_OF_UNSPLIT_TOTAL':'合計しか分からないので、その一部の数は決められません。',
                                'AMBIGUOUS_OPERATION_TARGET':'どの品物への操作なのかが決められません。','HEDGED_QUANTITY':'数がはっきり決まっていないので、答えを確定しません。'}.get(g['reason'])
            return out
        if g.get('applied'):r={**r,'verification_evidence':{**(r.get('verification_evidence') or {}),'semantic_gate':g}}
    if r.get('answer') is not None and not r.get('explanation'):
        from .explain import explain
        e=explain(r)
        if e:r={**r,'explanation':e}
    return r
def _record_rule(s,t,d,numbers,teacher):
    r=s['event_rules'].setdefault(t,{'id':whole.sha_obj(t)[:16],'direction':d,'support':[],'teachers':[],'conflict':False})
    if r['direction']!=d:r['conflict']=True;s['conflicts']+=1
    else:
        if numbers not in r['support']:r['support'].append(numbers)
        if teacher not in r['teachers']:r['teachers'].append(teacher)
    return {'template':t,'direction':d,'support':len(r['support']),'conflict':r['conflict']}
def _canonicalize_rules(s):
    merged={}
    for key,r in s['event_rules'].items():
        key=key.replace('<Q>を','<Q>');r=copy.deepcopy(r);r['id']=whole.sha_obj(key)[:16]
        if key not in merged:merged[key]=r;continue
        old=merged[key]
        if old['direction']!=r['direction'] and not old['conflict']:s['conflicts']+=1
        old['conflict']=old['conflict'] or r['conflict'] or old['direction']!=r['direction']
        for field in ('support','teachers'):
            for value in r[field]:
                if value not in old[field]:old[field].append(value)
    s['event_rules']=merged
@transactional()
def install_seed(data):
    path=Path(__file__).resolve().parents[2]/'META/TRAINED_SKILLS.json'
    if not path.is_file():return {'installed':False}
    s=state(data)
    if (Path(data)/NS/'commits').exists():return {'installed':False,'reason':'EXISTING_LEARNING_PRESERVED'}
    seed=store.read(path);publisher=store.read(path.parent/'RELEASE_RECEIPT.json')['public_key']
    if not whole._verify(seed,publisher):raise ValueError('V1022_SEED_SIGNATURE')
    payload=seed['payload']
    if set(payload)!={'schema','event_rules','aliases','training_provenance'} or payload['schema']!='tukuyo.v1022.public_skills/1':raise ValueError('V1022_SEED_SCHEMA')
    s['event_rules']=copy.deepcopy(payload['event_rules']);s['aliases']=dict(payload['aliases']);s['seed_provenance']=seed
    _validate(s);store.save(data,NS,COMPONENT,s);whole.sync(data)
    return {'installed':True,'active_rules':sum(not r['conflict'] and len(r['support'])>=2 for r in s['event_rules'].values())}
def _induce(q,a):
    p=package(normalize(q));m=re.fullmatch(r'\s*(\d+)\s*(?:'+UNITS+'|'+BOXES+r')?\s*',str(a))
    if not p or not m:return None
    events=[c for c in clauses(normalize(q)[p['end']:]) if re.search(rf'\d+\s*({UNITS}|{BOXES})',c)]
    if len(events)!=1:return None
    c=events[0];qs=list(re.finditer(rf'(\d+)\s*({UNITS}|{BOXES})',c))
    if len(qs)!=1 or int(qs[0][1])==0 or qs[0][2] not in (p['unit'],p['container']):return None
    amount=int(qs[0][1])*(p['per'] if qs[0][2]==p['container'] else 1);delta=int(m[1])-p['per']*p['count']
    if delta not in (-amount,0,amount):return None
    return _template(c),int(delta/amount),[int(x) for x in re.findall(r'\d+',normalize(q))]
@transactional()
def learn(data,bundle,teacher=None):
    require_alive(data);s=copy.deepcopy(state(data));teacher=str(teacher or bundle.get('teacher',''));examples=bundle.get('examples',[])
    if not teacher or len(teacher)>100 or not isinstance(examples,list) or not 1<=len(examples)<=128:raise ValueError('DIALOGUE_BATCH_OR_TEACHER')
    _canonicalize_rules(s)
    records=[]
    for e in examples:
        q=str(e['question']);expected=e.get('expected_answer');before=solve(data,q,e.get('formal_task'));proposed=[]
        induced=_induce(q,expected)
        if induced:proposed.append(_record_rule(s,*induced,teacher))
        for label in e.get('event_labels',[]):
            surface=str(label.get('surface',''));d=label.get('direction');occurred=label.get('occurred');scope=label.get('scope')
            if surface not in q or type(d) is not int or d not in (-1,0,1) or type(occurred) is not bool or scope not in ('current_inventory','other_inventory','hypothetical','uncertain'):s['rejected']+=1;continue
            if scope=='uncertain':continue
            # A positive event quoted as false must not redefine that verb as
            # zero consumption. Scope and non-occurrence are checked on the
            # full input clause, not learned from its isolated surface label.
            if not occurred or scope!='current_inventory':continue
            nums=[int(x) for x in re.findall(r'\d+',normalize(q))]
            if nums:proposed.append(_record_rule(s,_template(surface),d if occurred and scope=='current_inventory' else 0,nums,teacher))
        for a in e.get('aliases',[]):
            surface=str(a['surface']);canonical=str(a['canonical'])
            if not surface or not canonical or max(len(surface),len(canonical))>100 or any(x in surface+canonical for x in ('<Q>','\n','\x00')):s['rejected']+=1;continue
            if surface in s['aliases'] and s['aliases'][surface]!=canonical:s['conflicts']+=1;continue
            s['aliases'][surface]=canonical
        for f in e.get('facts',[]):
            f={k:str(f[k]) for k in ('entity','relation','value')}
            if any(not v or len(v)>200 for v in f.values()):s['rejected']+=1;continue
            f.update(teacher=teacher,source_id=str(e.get('id','')),context=re.split(r'質問[:：]',normalize(q))[0] if re.search(r'質問[:：]',q) else '')
            if not any(all(old[k]==f[k] for k in ('entity','relation','value','context')) for old in s['facts']):s['facts'].append(f)
        s['rounds']+=1;s['teachers'][teacher]=s['teachers'].get(teacher,0)+1
        r={'seq':s['rounds'],'teacher':teacher,'question':q,'student_before':before,'expected_answer':expected,
           'explanation':str(e.get('explanation',''))[:3000],'proposed_rules':proposed,'previous':s['dialogue_head'],'utc_ns':time.time_ns()}
        r['sha256']=whole.sha_obj(r);s['dialogue_head']=r['sha256'];records.append(r)
    _validate(s)
    for r in records:atomic_write_bytes(Path(data)/NS/'dialogues'/f"{r['seq']:06d}.json",whole.canon(r)+b'\n')
    store.save(data,NS,COMPONENT,s)
    from tukuyo_v978.heart_loop import process_experience
    process_experience(data,'learning',.15,.2,'teacher-dialogue',teacher);whole.sync(data)
    responses=[{'id':e.get('id'),'question':e['question'],'result':solve(data,e['question'],e.get('formal_task'))} for e in examples]
    return {'ok':True,'version':'v1022','teacher':teacher,'rounds':s['rounds'],'new_rounds':len(records),
            'active_event_rules':sum(not r['conflict'] and len(r['support'])>=2 for r in s['event_rules'].values()),'aliases':len(s['aliases']),'facts':len(s['facts']),'responses':responses}
def audit(data):
    try:
        s=state(data);previous=whole.ZERO
        for i in range(1,s['rounds']+1):
            r=store.read(Path(data)/NS/'dialogues'/f'{i:06d}.json');h=r.pop('sha256')
            if r['seq']!=i or r['previous']!=previous or whole.sha_obj(r)!=h:raise ValueError('V1022_DIALOGUE_CHAIN')
            previous=h
        if previous!=s['dialogue_head']:raise ValueError('V1022_DIALOGUE_HEAD')
        for proof in s['inherited_public_learning']:
            if not whole._verify(proof,proof.get('public_key','')) or proof.get('payload',{}).get('target_individual_id')!=s['individual_id']:raise ValueError('V1022_CULTURAL_SIGNATURE')
        seed=s.get('seed_provenance')
        if seed:
            meta=Path(__file__).resolve().parents[2]/'META'
            publishers={store.read(meta/'RELEASE_RECEIPT.json')['public_key']}
            for name in ('PATCH_LINEAGE_v1022_4.json','PATCH_LINEAGE_v1022_5.json','PATCH_LINEAGE_v1022_6.json'):
                lineage=meta/name
                if lineage.is_file():publishers.update(store.read(lineage).get('accepted_seed_public_keys',[]))
            if seed.get('public_key') not in publishers or not whole._verify(seed,seed.get('public_key','')):raise ValueError('V1022_SEED_SIGNATURE')
        return {'ok':True,'version':'v1022','rounds':s['rounds'],'teachers':s['teachers'],'aliases':len(s['aliases']),'facts':len(s['facts']),
                'active_event_rules':sum(not r['conflict'] and len(r['support'])>=2 for r in s['event_rules'].values()),'conflicts':s['conflicts'],
                'claim_boundary':{'local_symbolic_learning':True,'qa_answer_table':False,'runtime_llm':False,'general_intelligence':False,'consciousness':False}}
    except Exception as e:return {'ok':False,'version':'v1022','errors':[str(e)]}
