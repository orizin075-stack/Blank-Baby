"""generation 4: Claude as a reader and as a voice, never as the judge.

  read(text, view)     Claude writes the problem in the formal problem language (structured output against a JSON
                       schema). The caller solves the reading and check.py decides. Two views with their own
                       instructions and their own examples: 'story' reads in the order of the text, 'goal' starts
                       from what is asked. Two readings that pass the checker and agree are two independent readings.
  answer(question)     for what is not a problem (knowledge, conversation): Claude's reply, always marked unverified.

Configuration (environment; the key is never written anywhere):
  TUKUYO_ANTHROPIC_API_KEY   the API key (needs the `anthropic` package: pip install anthropic)
  TUKUYO_ANTHROPIC_BASE_URL  default https://api.anthropic.com. The host's own ANTHROPIC_* variables are never read.
  TUKUYO_LLM_MODEL           default MODEL_DEFAULT below
  TUKUYO_LLM_EFFORT          default medium (low | medium | high | xhigh | max)
  TUKUYO_LLM_RECORD          a JSONL file: every reply is appended (request hash, model, request id, text, usage)
  TUKUYO_LLM_REPLAY          a JSONL file written by TUKUYO_LLM_RECORD: requests are answered from it, offline
A declined request (stop_reason 'refusal') is retried by the API on another model (fallbacks 'default'); a request
declined by every model, cut at max_tokens or failing comes back as {'ok': False, 'reason': ...}, never as an answer.
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

ANSWER_SYSTEM="""You are the voice of TUKUYO, a small reasoning system, answering a question that is not a math problem. \
Answer briefly and plainly, in the language of the question. If you are not sure, say so. Your answer is shown as \
Claude's statement, not as something TUKUYO has checked."""

# ----------------------------------------------------------------------------- transport
def settings():
    return {'model':os.environ.get('TUKUYO_LLM_MODEL','').strip() or MODEL_DEFAULT,
            'effort':os.environ.get('TUKUYO_LLM_EFFORT','').strip() or EFFORT_DEFAULT,
            'base_url':os.environ.get('TUKUYO_ANTHROPIC_BASE_URL','').strip() or 'https://api.anthropic.com',
            'key':bool(os.environ.get('TUKUYO_ANTHROPIC_API_KEY','').strip()),
            'replay':os.environ.get('TUKUYO_LLM_REPLAY','').strip() or None,'record':os.environ.get('TUKUYO_LLM_RECORD','').strip() or None}

def available():
    s=settings();return bool(s['key'] or s['replay'])

def request_hash(kind,system,user):
    return hashlib.sha256(json.dumps([kind,system,user],ensure_ascii=False).encode()).hexdigest()

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
    return _replay_cache[path].get(h)

_client=None
def _anthropic():
    global _client
    if _client is None:
        import anthropic
        s=settings()
        _client=anthropic.Anthropic(api_key=os.environ['TUKUYO_ANTHROPIC_API_KEY'].strip(),base_url=s['base_url'],max_retries=3,timeout=600.0)
    return _client

def call(kind,system,user,schema=None,max_tokens=16000):
    s=settings();h=request_hash(kind,system,user)
    if s['replay']:
        r=_replayed(s['replay'],h)
        if r is None:return {'ok':False,'reason':'NOT_IN_REPLAY','hash':h}
        return {**{k:r.get(k) for k in ('ok','text','model','request_id','usage','reason')},'hash':h,'replayed':True}
    if not s['key']:return {'ok':False,'reason':'LLM_NOT_CONFIGURED'}
    try:import anthropic
    except ImportError:return {'ok':False,'reason':'ANTHROPIC_PACKAGE_MISSING'}
    oc={'effort':s['effort']}
    if schema:oc['format']={'type':'json_schema','schema':schema}
    t=time.monotonic()
    try:
        r=_anthropic().beta.messages.create(model=s['model'],max_tokens=max_tokens,betas=['server-side-fallback-2026-07-01'],fallbacks='default',
            system=[{'type':'text','text':system,'cache_control':{'type':'ephemeral'}}],messages=[{'role':'user','content':user}],output_config=oc)
    except anthropic.AuthenticationError:return {'ok':False,'reason':'AUTHENTICATION','hash':h}
    except anthropic.PermissionDeniedError:return {'ok':False,'reason':'PERMISSION_DENIED','hash':h}
    except anthropic.NotFoundError:return {'ok':False,'reason':'MODEL_OR_ENDPOINT_NOT_FOUND','hash':h}
    except anthropic.BadRequestError as e:return {'ok':False,'reason':'BAD_REQUEST:'+str(getattr(e,'message',e))[:300],'hash':h}
    except anthropic.RateLimitError:return {'ok':False,'reason':'RATE_LIMITED','hash':h}
    except anthropic.APIStatusError as e:return {'ok':False,'reason':f'API_STATUS_{e.status_code}','hash':h}
    except anthropic.APIConnectionError:return {'ok':False,'reason':'CONNECTION','hash':h}
    u=r.usage
    usage={k:getattr(u,k,None) for k in ('input_tokens','output_tokens','cache_read_input_tokens','cache_creation_input_tokens')}
    out={'ok':True,'text':''.join(b.text for b in r.content if b.type=='text'),'model':r.model,'request_id':getattr(r,'_request_id',None),
         'usage':usage,'ms':int((time.monotonic()-t)*1000),'hash':h}
    if r.stop_reason=='refusal':
        cat=getattr(getattr(r,'stop_details',None),'category',None);out={**out,'ok':False,'reason':f'REFUSAL:{cat}','text':''}
    elif r.stop_reason=='max_tokens':out={**out,'ok':False,'reason':'MAX_TOKENS','text':''}
    if s['record']:
        with _lock,open(s['record'],'a',encoding='utf-8') as f:
            f.write(json.dumps({'hash':h,'kind':kind,**{k:out.get(k) for k in ('ok','reason','text','model','request_id','usage')}},ensure_ascii=False)+'\n')
    return out

# ----------------------------------------------------------------------------- uses
def read(text,view='story',lang=None):
    """-> {'ok', 'spec' (FPL), 'reply': transport record} ; spec is None when Claude says the text is not readable"""
    r=call('read:'+view+':'+PROMPT_VERSION,system_prompt(view),'Text: '+text,schema=FPL_SCHEMA)
    if not r.get('ok'):return {'ok':False,'reason':r.get('reason'),'reply':r}
    try:o=json.loads(r['text'])
    except ValueError:return {'ok':False,'reason':'NOT_JSON','reply':r}
    if not o.get('readable'):return {'ok':False,'reason':'NOT_READABLE','reply':r}
    spec={'schema':'tukuyo.g4.fpl/1','lang':lang or ('ja' if any('぀'<=c<='鿿' for c in text) else 'en'),'text':text,
          'quantities':o['quantities'],'ask':o['ask'],'answer_unit':o.get('answer_unit',''),'unused':o.get('unused') or [],
          'facts':[{'eq':f['eq'],**({'span':f['span']} if f.get('span') else {}),**({'known':f['known']} if f.get('known') else {})} for f in o['facts']]}
    return {'ok':True,'spec':spec,'reply':r}

def answer(question):
    r=call('answer:1',ANSWER_SYSTEM,question,max_tokens=4000)
    if not r.get('ok'):return {'ok':False,'reason':r.get('reason')}
    return {'ok':True,'answer':r['text'].strip(),'verified':False,'source':'claude','model':r.get('model'),'request_id':r.get('request_id')}
