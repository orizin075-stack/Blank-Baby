"""generation 4: the parents. Large language models as readers and as a voice, never as the judge.

TUKUYO generation 4 learns from three parents: Claude (Anthropic), ChatGPT (OpenAI) and Gemini (Google).

  read(text, view, parent)   a parent writes the problem in the formal problem language (structured output against a
                             JSON schema). The caller solves the reading and check.py decides. Two views with their
                             own instructions and examples: 'story' reads in the order of the text, 'goal' starts from
                             what is asked. Readings by two different parents that pass the checker and agree are two
                             independent readings (api.py).
  answer(question, parent)   for what is not a problem (knowledge, conversation): a parent's reply, always unverified.
  parents()                  the parents that can be asked now, in the order claude, chatgpt, gemini.

Configuration (environment; keys are never written anywhere, and the host's own ANTHROPIC_*, OPENAI_*, GEMINI_* and
GOOGLE_* variables are never read):
  claude    TUKUYO_ANTHROPIC_API_KEY (package `anthropic`); TUKUYO_LLM_MODEL (default MODEL_DEFAULT below);
            TUKUYO_LLM_EFFORT (default medium); TUKUYO_ANTHROPIC_BASE_URL (default https://api.anthropic.com)
  chatgpt   TUKUYO_OPENAI_API_KEY (package `openai`); TUKUYO_OPENAI_MODEL (required: there is no default, choose a
            current model); TUKUYO_OPENAI_EFFORT (optional reasoning effort); TUKUYO_OPENAI_BASE_URL
  gemini    TUKUYO_GEMINI_API_KEY (package `google-genai`); TUKUYO_GEMINI_MODEL (required, no default);
            TUKUYO_GEMINI_THINKING (optional thinking level: MINIMAL LOW MEDIUM HIGH); TUKUYO_GEMINI_BASE_URL
  TUKUYO_LLM_PARENTS   optional comma list that limits the parents used (e.g. "claude,gemini")
  TUKUYO_LLM_VOICE     the parent that answers questions that are not problems (default: the first parent)
  TUKUYO_LLM_RECORD    a JSONL file: every reply is appended (parent, request hash, model, request id, text, usage)
  TUKUYO_LLM_REPLAY    a JSONL file written by TUKUYO_LLM_RECORD: requests are answered from it, offline; the parents
                       are then the ones the file holds
A declined request (Claude: stop_reason 'refusal', retried on another model by the API; ChatGPT: a refusal; Gemini: a
block or a safety stop), a reply cut at the token limit, or a failing call comes back as {'ok': False, 'reason': ...},
never as an answer.
"""
from __future__ import annotations
import hashlib,json,os,threading,time

MODEL_DEFAULT='claude-opus-5-5'
EFFORT_DEFAULT='medium'
PROMPT_VERSION='g4-read-1'
_lock=threading.Lock()

FPL_SCHEMA={'type':'object','additionalProperties':False,'required':['readable','quantities','facts','ask','answer_unit','unused'],
 'properties':{
  'readable':{'type':'boolean'},
  'quantities':{'type':'array','items':{'type':'object','additionalProperties':False,'required':['name','unit','integer','signed','about'],
     'properties':{'name':{'type':'string'},'unit':{'type':'string'},'integer':{'type':'boolean'},'signed':{'type':'boolean'},'about':{'type':'string'}}}},
  'facts':{'type':'array','items':{'type':'object','additionalProperties':False,'required':['eq','span','known'],
     'properties':{'eq':{'type':'string'},'span':{'type':'string'},'known':{'type':'string'}}}},
  'ask':{'type':'string'},
  'answer_unit':{'type':'string'},
  'unused':{'type':'array','items':{'type':'object','additionalProperties':False,'required':['raw','why'],
     'properties':{'raw':{'type':'string'},'why':{'type':'string'}}}}}}

RULES="""You write a math word problem in TUKUYO's formal problem language. You do not solve it: TUKUYO solves your \
reading exactly and a separate checker decides whether it may be used. Write only what the text states.

Quantities
- name: ASCII snake_case. unit: what the quantity counts or measures, in words of your choice used consistently: a \
counted thing (egg, apple, person, 個, 人), money (dollar, 円), a measure (km, hour, minute, kg), a rate as a fraction \
("dollar/egg", "km/hour", "egg/day"), "1" for a pure number, "%" for a percentage.
- integer: true for counts of whole things. signed: true only if the quantity may be negative.

Facts (each fact is one equation "left = right")
1. binding: `name = number` for a number written in the text. span: an exact quote from the text that contains the \
number (copy the characters exactly; keep it short). Bind every number where it is stated. Number words count as \
numbers: "half"/"半分" is 1/2, "twice"/"2倍" is 2, "a dozen" is 12, "40%" is 40 with unit "%", "3割" is 30 with unit "%".
2. known constant: `name = number` for a fact of the world that the text does not state (60 minutes in an hour, 7 \
days in a week, 100 cents in a dollar, 1000 meters in a kilometer). Put what it is in `known` and leave span empty. \
Only these numbers: 2, 3, 4, 7, 10, 12, 16, 24, 36, 52, 60, 100, 365, 366, 1000, 1760, 5280.
3. relation: an equation over names saying how quantities are connected. span: the exact quote that states the \
connection. No numbers in a relation except 0, 1 and 100 (write a percentage as rate / 100).
- Fields not used by a fact are empty strings ("known" of bindings and relations, "span" of known constants).
- Functions you may use: floor, ceil, abs, min, max, gcd, lcm, mod.

Checks your reading must pass
- Every number written in the text is bound, or listed in `unused` with the reason it plays no role (an age that is \
never used, a year, a name like "Room 5"). The number 1 of a rate ("1個あたり", "per 1 kg") and ordinals ("2つ目", \
"the second") may be left out.
- Units agree: both sides of every equation and both operands of + and - have the same unit. Convert with known \
constants (minutes = hours * min_per_hour).
- Every quantity gets exactly one value from the facts. Counts are whole and nothing is negative unless signed.
- ask: the quantity the question asks for. answer_unit: its unit in the words of the question.
- If the text is not a math problem, or cannot be written this way, set readable to false and leave the lists empty."""

VIEWS={
 'story':"""Procedure: go through the text in order. For each sentence, bind the numbers it states and write the relations it \
states, naming each new quantity as it appears. Finish with the question.""",
 'goal':"""Procedure: start from the question. Name the asked quantity first and write the relation that defines it. Then, \
for every quantity in that relation, either bind it to a number of the text or define it by another relation, until \
every quantity is bound. Finally list the numbers of the text you did not need, with the reason.""",
}

EXAMPLES={
 'story':[
  ('パン屋さんは1日に240個のパンを焼きます。朝に3割を売り、昼に残りの半分を売りました。昼のあとに残っているパンは何個ですか？',
   {'readable':True,'quantities':[
     {'name':'baked','unit':'個','integer':True,'signed':False,'about':'breads baked in a day'},
     {'name':'morning_rate','unit':'%','integer':False,'signed':False,'about':'share sold in the morning'},
     {'name':'morning_sold','unit':'個','integer':True,'signed':False,'about':'sold in the morning'},
     {'name':'after_morning','unit':'個','integer':True,'signed':False,'about':'left after the morning'},
     {'name':'half','unit':'1','integer':False,'signed':False,'about':'half'},
     {'name':'noon_sold','unit':'個','integer':True,'signed':False,'about':'sold at noon'},
     {'name':'left','unit':'個','integer':True,'signed':False,'about':'left after noon'}],
    'facts':[
     {'eq':'baked = 240','span':'1日に240個のパンを焼きます','known':''},
     {'eq':'morning_rate = 30','span':'朝に3割を売り','known':''},
     {'eq':'morning_sold = baked * morning_rate / 100','span':'朝に3割を売り','known':''},
     {'eq':'after_morning = baked - morning_sold','span':'残り','known':''},
     {'eq':'half = 1/2','span':'残りの半分を売りました','known':''},
     {'eq':'noon_sold = after_morning * half','span':'昼に残りの半分を売りました','known':''},
     {'eq':'left = after_morning - noon_sold','span':'昼のあとに残っているパン','known':''}],
    'ask':'left','answer_unit':'個','unused':[]}),
  ('Mia is 9 years old. She had 25 stickers and gave 7 to each of her 2 brothers. How many stickers does she have now?',
   {'readable':True,'quantities':[
     {'name':'had','unit':'sticker','integer':True,'signed':False,'about':'stickers at first'},
     {'name':'per_brother','unit':'sticker/brother','integer':True,'signed':False,'about':'given to each brother'},
     {'name':'brothers','unit':'brother','integer':True,'signed':False,'about':'number of brothers'},
     {'name':'given','unit':'sticker','integer':True,'signed':False,'about':'stickers given away'},
     {'name':'now','unit':'sticker','integer':True,'signed':False,'about':'stickers now'}],
    'facts':[
     {'eq':'had = 25','span':'She had 25 stickers','known':''},
     {'eq':'per_brother = 7','span':'gave 7 to each','known':''},
     {'eq':'brothers = 2','span':'her 2 brothers','known':''},
     {'eq':'given = per_brother * brothers','span':'gave 7 to each of her 2 brothers','known':''},
     {'eq':'now = had - given','span':'How many stickers does she have now?','known':''}],
    'ask':'now','answer_unit':'stickers','unused':[{'raw':'9','why':"Mia's age plays no role"}]}),
 ],
 'goal':[
  ('A train travels at 80 kilometers per hour for 2 hours and 30 minutes. How far does it travel?',
   {'readable':True,'quantities':[
     {'name':'distance','unit':'km','integer':False,'signed':False,'about':'distance travelled'},
     {'name':'speed','unit':'km/hour','integer':False,'signed':False,'about':'speed'},
     {'name':'time','unit':'hour','integer':False,'signed':False,'about':'time travelling'},
     {'name':'hours','unit':'hour','integer':False,'signed':False,'about':'whole hours'},
     {'name':'minutes','unit':'minute','integer':False,'signed':False,'about':'extra minutes'},
     {'name':'min_per_hour','unit':'minute/hour','integer':False,'signed':False,'about':'minutes in an hour'}],
    'facts':[
     {'eq':'distance = speed * time','span':'How far does it travel?','known':''},
     {'eq':'speed = 80','span':'80 kilometers per hour','known':''},
     {'eq':'time = hours + minutes / min_per_hour','span':'for 2 hours and 30 minutes','known':''},
     {'eq':'hours = 2','span':'2 hours','known':''},
     {'eq':'minutes = 30','span':'30 minutes','known':''},
     {'eq':'min_per_hour = 60','span':'','known':'60 minutes in an hour'}],
    'ask':'distance','answer_unit':'kilometers','unused':[]}),
  ('大小2つの数があります。2つの数の和は50で、差は14です。大きい方の数はいくつですか？',
   {'readable':True,'quantities':[
     {'name':'big','unit':'1','integer':False,'signed':False,'about':'the larger number'},
     {'name':'small','unit':'1','integer':False,'signed':False,'about':'the smaller number'},
     {'name':'total','unit':'1','integer':False,'signed':False,'about':'the sum'},
     {'name':'gap','unit':'1','integer':False,'signed':False,'about':'the difference'}],
    'facts':[
     {'eq':'big + small = total','span':'2つの数の和は50','known':''},
     {'eq':'big - small = gap','span':'差は14','known':''},
     {'eq':'total = 50','span':'和は50','known':''},
     {'eq':'gap = 14','span':'差は14です','known':''}],
    'ask':'big','answer_unit':'','unused':[{'raw':'2','why':'how many numbers there are, not an amount'}]}),
 ],
}

def system_prompt(view):
    ex='\n\n'.join(f'Example {i+1}\nText: {t}\nReading: {json.dumps(r,ensure_ascii=False)}' for i,(t,r) in enumerate(EXAMPLES[view]))
    return RULES+'\n\n'+VIEWS[view]+'\n\n'+ex

ANSWER_SYSTEM="""You are one of the voices of TUKUYO, a small reasoning system, answering a question that is not a math \
problem. Answer briefly and plainly, in the language of the question. If you are not sure, say so. Your answer is shown \
as your own statement, not as something TUKUYO has checked."""

# ----------------------------------------------------------------------------- transport
PARENTS=('claude','chatgpt','gemini')
KEY_ENV={'claude':'TUKUYO_ANTHROPIC_API_KEY','chatgpt':'TUKUYO_OPENAI_API_KEY','gemini':'TUKUYO_GEMINI_API_KEY'}
PACKAGE={'claude':'anthropic','chatgpt':'openai','gemini':'google-genai'}

def _env(k):return os.environ.get(k,'').strip()

def settings(parent='claude'):
    s={'parent':parent,'key':bool(_env(KEY_ENV[parent])),'replay':_env('TUKUYO_LLM_REPLAY') or None,'record':_env('TUKUYO_LLM_RECORD') or None}
    if parent=='claude':
        s.update(model=_env('TUKUYO_LLM_MODEL') or MODEL_DEFAULT,effort=_env('TUKUYO_LLM_EFFORT') or EFFORT_DEFAULT,
                 base_url=_env('TUKUYO_ANTHROPIC_BASE_URL') or 'https://api.anthropic.com')
    elif parent=='chatgpt':
        s.update(model=_env('TUKUYO_OPENAI_MODEL') or None,effort=_env('TUKUYO_OPENAI_EFFORT') or None,
                 base_url=_env('TUKUYO_OPENAI_BASE_URL') or 'https://api.openai.com/v1')
    elif parent=='gemini':
        s.update(model=_env('TUKUYO_GEMINI_MODEL') or None,thinking=(_env('TUKUYO_GEMINI_THINKING') or None),
                 base_url=_env('TUKUYO_GEMINI_BASE_URL') or None)
    else:raise ValueError('UNKNOWN_PARENT:'+str(parent))
    return s

def _replay_parents(path):
    _replayed(path,None)
    return {r.get('parent') or 'claude' for r in _replay_cache.get(path,{}).values()}

def parents():
    """the parents that can be asked now: with TUKUYO_LLM_REPLAY the ones the file holds, otherwise the ones with a key
    (and, for chatgpt and gemini, a model); TUKUYO_LLM_PARENTS limits the list"""
    only=[x.strip() for x in _env('TUKUYO_LLM_PARENTS').split(',') if x.strip()]
    rp=_env('TUKUYO_LLM_REPLAY')
    if rp:held=_replay_parents(rp);ps=[p for p in PARENTS if p in held]
    else:ps=[p for p in PARENTS if settings(p)['key'] and settings(p)['model']]
    return [p for p in ps if not only or p in only]

def available():
    return bool(parents())

def request_hash(kind,system,user):
    return hashlib.sha256(json.dumps([kind,system,user],ensure_ascii=False).encode()).hexdigest()

def _kind(parent,kind):
    """the request kind of a parent; Claude's keeps the generation-4 form so that earlier recordings replay"""
    return kind if parent=='claude' else parent+':'+kind

_replay_cache={}
def _replayed(path,h):
    if path not in _replay_cache:
        d={}
        try:
            with open(path,encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        r=json.loads(line);d[r['hash']]=r
        except OSError:pass
        _replay_cache[path]=d
    return _replay_cache[path].get(h) if h else None

_clients={}
def _client(parent):
    if parent not in _clients:
        s=settings(parent);key=os.environ[KEY_ENV[parent]].strip()
        if parent=='claude':
            import anthropic
            _clients[parent]=anthropic.Anthropic(api_key=key,base_url=s['base_url'],max_retries=3,timeout=600.0)
        elif parent=='chatgpt':
            import openai
            _clients[parent]=openai.OpenAI(api_key=key,base_url=s['base_url'],max_retries=3,timeout=600.0)
        else:
            from google import genai
            from google.genai import types
            ho=types.HttpOptions(timeout=600000,**({'base_url':s['base_url']} if s['base_url'] else {}))
            _clients[parent]=genai.Client(api_key=key,http_options=ho)
    return _clients[parent]

def _call_claude(s,system,user,schema,max_tokens):
    import anthropic
    oc={'effort':s['effort']}
    if schema:oc['format']={'type':'json_schema','schema':schema}
    try:
        r=_client('claude').beta.messages.create(model=s['model'],max_tokens=max_tokens,betas=['server-side-fallback-2026-07-01'],fallbacks='default',
            system=[{'type':'text','text':system,'cache_control':{'type':'ephemeral'}}],messages=[{'role':'user','content':user}],output_config=oc)
    except anthropic.AuthenticationError:return {'ok':False,'reason':'AUTHENTICATION'}
    except anthropic.PermissionDeniedError:return {'ok':False,'reason':'PERMISSION_DENIED'}
    except anthropic.NotFoundError:return {'ok':False,'reason':'MODEL_OR_ENDPOINT_NOT_FOUND'}
    except anthropic.BadRequestError as e:return {'ok':False,'reason':'BAD_REQUEST:'+str(getattr(e,'message',e))[:300]}
    except anthropic.RateLimitError:return {'ok':False,'reason':'RATE_LIMITED'}
    except anthropic.APIStatusError as e:return {'ok':False,'reason':f'API_STATUS_{e.status_code}'}
    except anthropic.APIConnectionError:return {'ok':False,'reason':'CONNECTION'}
    u=r.usage
    out={'ok':True,'text':''.join(b.text for b in r.content if b.type=='text'),'model':r.model,'request_id':getattr(r,'_request_id',None),
         'usage':{k:getattr(u,k,None) for k in ('input_tokens','output_tokens','cache_read_input_tokens','cache_creation_input_tokens')}}
    if r.stop_reason=='refusal':
        cat=getattr(getattr(r,'stop_details',None),'category',None);out={**out,'ok':False,'reason':f'REFUSAL:{cat}','text':''}
    elif r.stop_reason=='max_tokens':out={**out,'ok':False,'reason':'MAX_TOKENS','text':''}
    return out

def _call_chatgpt(s,system,user,schema,max_tokens):
    import openai
    kw={'model':s['model'],'instructions':system,'input':user,'max_output_tokens':max_tokens,'store':False}
    if schema:kw['text']={'format':{'type':'json_schema','name':'tukuyo_reading','schema':schema,'strict':True}}
    if s.get('effort'):kw['reasoning']={'effort':s['effort']}
    try:r=_client('chatgpt').responses.create(**kw)
    except openai.AuthenticationError:return {'ok':False,'reason':'AUTHENTICATION'}
    except openai.PermissionDeniedError:return {'ok':False,'reason':'PERMISSION_DENIED'}
    except openai.NotFoundError:return {'ok':False,'reason':'MODEL_OR_ENDPOINT_NOT_FOUND'}
    except openai.BadRequestError as e:return {'ok':False,'reason':'BAD_REQUEST:'+str(getattr(e,'message',e))[:300]}
    except openai.RateLimitError:return {'ok':False,'reason':'RATE_LIMITED'}
    except openai.APIStatusError as e:return {'ok':False,'reason':f'API_STATUS_{e.status_code}'}
    except openai.APIConnectionError:return {'ok':False,'reason':'CONNECTION'}
    u=r.usage
    out={'ok':True,'text':r.output_text,'model':r.model,'request_id':r.id,
         'usage':{'input_tokens':getattr(u,'input_tokens',None),'output_tokens':getattr(u,'output_tokens',None)} if u is not None else {}}
    refused=[c for o in (r.output or []) if getattr(o,'type',None)=='message' for c in (o.content or []) if getattr(c,'type',None)=='refusal']
    if refused:out={**out,'ok':False,'reason':'REFUSAL','text':''}
    elif r.status!='completed':out={**out,'ok':False,'reason':'INCOMPLETE:'+str(getattr(r.incomplete_details,'reason',None) or r.status),'text':''}
    return out

def _call_gemini(s,system,user,schema,max_tokens):
    import httpx
    from google.genai import errors,types
    cfg={'system_instruction':system,'max_output_tokens':max_tokens}
    if schema:cfg.update(response_mime_type='application/json',response_json_schema=schema)
    if s.get('thinking'):cfg['thinking_config']=types.ThinkingConfig(thinking_level=s['thinking'])
    try:r=_client('gemini').models.generate_content(model=s['model'],contents=user,config=types.GenerateContentConfig(**cfg))
    except errors.ClientError as e:
        code=getattr(e,'code',None)
        return {'ok':False,'reason':{400:'BAD_REQUEST',401:'AUTHENTICATION',403:'PERMISSION_DENIED',404:'MODEL_OR_ENDPOINT_NOT_FOUND',429:'RATE_LIMITED'}.get(code,f'API_STATUS_{code}')
                +(':'+str(getattr(e,'message','') or '')[:300] if code==400 else '')}
    except errors.APIError as e:return {'ok':False,'reason':f'API_STATUS_{getattr(e,"code",None)}'}
    except httpx.TransportError:return {'ok':False,'reason':'CONNECTION'}
    um=r.usage_metadata
    out={'ok':True,'text':'','model':r.model_version or s['model'],'request_id':r.response_id,
         'usage':{'input_tokens':um.prompt_token_count,'output_tokens':(um.candidates_token_count or 0)+(um.thoughts_token_count or 0),
                  'cached_input_tokens':um.cached_content_token_count} if um is not None else {}}
    fb=r.prompt_feedback
    if fb is not None and fb.block_reason:return {**out,'ok':False,'reason':'BLOCKED:'+str(getattr(fb.block_reason,'name',fb.block_reason))}
    cand=r.candidates[0] if r.candidates else None
    fr=getattr(getattr(cand,'finish_reason',None),'name',None)
    if cand is None:return {**out,'ok':False,'reason':'NO_CANDIDATE'}
    if fr=='MAX_TOKENS':return {**out,'ok':False,'reason':'MAX_TOKENS'}
    if fr not in (None,'STOP','FINISH_REASON_UNSPECIFIED'):return {**out,'ok':False,'reason':'FINISH:'+fr}
    return {**out,'text':r.text or ''}

CALL={'claude':_call_claude,'chatgpt':_call_chatgpt,'gemini':_call_gemini}

def call(kind,system,user,schema=None,max_tokens=16000,parent='claude'):
    s=settings(parent);h=request_hash(_kind(parent,kind),system,user)
    if s['replay']:
        r=_replayed(s['replay'],h)
        if r is None:return {'ok':False,'reason':'NOT_IN_REPLAY','hash':h,'parent':parent}
        return {**{k:r.get(k) for k in ('ok','text','model','request_id','usage','reason')},'hash':h,'replayed':True,'parent':parent}
    if not s['key']:return {'ok':False,'reason':'LLM_NOT_CONFIGURED','parent':parent}
    if not s['model']:return {'ok':False,'reason':'MODEL_NOT_SET','parent':parent}
    try:__import__({'claude':'anthropic','chatgpt':'openai','gemini':'google.genai'}[parent])
    except ImportError:return {'ok':False,'reason':'PACKAGE_MISSING:'+PACKAGE[parent],'parent':parent}
    t=time.monotonic()
    out={**CALL[parent](s,system,user,schema,max_tokens),'ms':int((time.monotonic()-t)*1000),'hash':h,'parent':parent}
    if s['record']:
        with _lock,open(s['record'],'a',encoding='utf-8') as f:
            f.write(json.dumps({'parent':parent,'hash':h,'kind':_kind(parent,kind),**{k:out.get(k) for k in ('ok','reason','text','model','request_id','usage')}},ensure_ascii=False)+'\n')
    return out

# ----------------------------------------------------------------------------- uses
def read(text,view='story',lang=None,parent='claude'):
    """-> {'ok', 'spec' (FPL), 'reply': transport record} ; spec is None when the parent says the text is not readable"""
    r=call('read:'+view+':'+PROMPT_VERSION,system_prompt(view),'Text: '+text,schema=FPL_SCHEMA,parent=parent)
    if not r.get('ok'):return {'ok':False,'reason':r.get('reason'),'reply':r}
    try:o=json.loads(r['text'])
    except (ValueError,TypeError):return {'ok':False,'reason':'NOT_JSON','reply':r}
    if not isinstance(o,dict) or not o.get('readable'):return {'ok':False,'reason':'NOT_READABLE','reply':r}
    try:
        spec={'schema':'tukuyo.g4.fpl/1','lang':lang or ('ja' if any('\u3040'<=c<='\u9fff' for c in text) else 'en'),'text':text,
              'quantities':o['quantities'],'ask':o['ask'],'answer_unit':o.get('answer_unit',''),'unused':o.get('unused') or [],
              'facts':[{'eq':f['eq'],**({'span':f['span']} if f.get('span') else {}),**({'known':f['known']} if f.get('known') else {})} for f in o['facts']]}
    except (KeyError,TypeError):return {'ok':False,'reason':'NOT_A_READING','reply':r}
    return {'ok':True,'spec':spec,'reply':r}

def voice():
    v=_env('TUKUYO_LLM_VOICE');ps=parents()
    return v if v in ps else (ps[0] if ps else 'claude')

def answer(question,parent=None):
    parent=parent or voice()
    r=call('answer:2',ANSWER_SYSTEM,question,max_tokens=4000,parent=parent)
    if not r.get('ok'):return {'ok':False,'reason':r.get('reason'),'parent':parent}
    return {'ok':True,'answer':(r['text'] or '').strip(),'verified':False,'source':parent,'model':r.get('model'),'request_id':r.get('request_id'),'parent':parent}
