"""LLM providers for claude-patch1 (stdlib only: urllib, no SDK dependency).

Select with TUKUYO_LLM_PROVIDER:
  anthropic  Claude API Messages endpoint. Needs ANTHROPIC_API_KEY and TUKUYO_LLM_MODEL.
  openai     Any OpenAI-compatible /chat/completions server (Ollama, LM Studio, vLLM, ...).
             TUKUYO_LLM_BASE_URL (default http://localhost:11434/v1), TUKUYO_LLM_MODEL,
             optional TUKUYO_LLM_API_KEY.
  command    The existing v1000 JSON stdin/stdout command (TUKUYO_LLM_COMMAND).
Unset/none -> no LLM; callers fall back to the local core.

Only the text built by the bridge is ever sent. Keys are read from the environment,
never written to disk, and never included in logs or outputs.
"""
from __future__ import annotations
import json,os,time,urllib.error,urllib.request
from dataclasses import dataclass

class LLMError(RuntimeError):pass

@dataclass
class LLMReply:
    text:str
    provider:str
    model:str
    latency_ms:int
    usage:dict

def config():
    prov=os.environ.get('TUKUYO_LLM_PROVIDER','').strip().lower()
    if not prov and os.environ.get('TUKUYO_LLM_COMMAND','').strip():prov='command'
    if prov in ('','none','off','builtin'):return {'provider':None}
    if prov not in ('anthropic','openai','command'):raise LLMError('UNKNOWN_LLM_PROVIDER:'+prov)
    base={'anthropic':'https://api.anthropic.com','openai':'http://localhost:11434/v1','command':None}[prov]
    return {'provider':prov,'model':os.environ.get('TUKUYO_LLM_MODEL','').strip() or None,
            'base_url':(os.environ.get('TUKUYO_LLM_BASE_URL','').strip() or base),
            'max_tokens':int(os.environ.get('TUKUYO_LLM_MAX_TOKENS','1200')),'timeout':float(os.environ.get('TUKUYO_LLM_TIMEOUT','90')),
            'has_key':bool(os.environ.get('ANTHROPIC_API_KEY' if prov=='anthropic' else 'TUKUYO_LLM_API_KEY','').strip())}

def public_config():
    try:c=config()
    except LLMError as e:return {'provider':None,'error':str(e)}
    return {k:v for k,v in c.items() if k!='has_key'}|({'api_key_present':c.get('has_key')} if c.get('provider') else {})

def _post(url,headers,body,timeout):
    data=json.dumps(body,ensure_ascii=False).encode()
    last=None
    for attempt in range(2):
        req=urllib.request.Request(url,data=data,headers=headers,method='POST')
        try:
            with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            last='HTTP_%d:%s'%(e.code,e.read().decode(errors='replace')[:300])
            if e.code in (429,500,502,503,529) and attempt==0:time.sleep(2.0);continue
            raise LLMError(last) from None
        except (urllib.error.URLError,TimeoutError,OSError) as e:
            last='NETWORK:'+type(e).__name__+':'+str(e)[:200]
            if attempt==0:time.sleep(1.0);continue
            raise LLMError(last) from None
    raise LLMError(last or 'LLM_REQUEST_FAILED')

def teachers():
    """claude-patch2: TUKUYO_LLM_TEACHERS = JSON list of provider configs, e.g.
      [{"provider":"anthropic","model":"<id>"},{"provider":"openai","model":"qwen2.5:14b","base_url":"http://localhost:11434/v1"},
       {"provider":"command","command":"python3 my_teacher.py"}]
    Keys are never written here: an entry may name the env var holding its key ("api_key_env").
    Without it, the single provider from config() is the only teacher."""
    raw=os.environ.get('TUKUYO_LLM_TEACHERS','').strip()
    if not raw:
        c=config();return [c] if c.get('provider') else []
    try:items=json.loads(raw)
    except ValueError:raise LLMError('TUKUYO_LLM_TEACHERS_NOT_JSON') from None
    if not isinstance(items,list) or not 1<=len(items)<=8:raise LLMError('TUKUYO_LLM_TEACHERS_LIMIT')
    out=[]
    for it in items if isinstance(items,list) else []:
        if not isinstance(it,dict) or it.get('provider') not in ('anthropic','openai','command'):raise LLMError('TUKUYO_LLM_TEACHERS_ENTRY')
        if any(k in it for k in ('api_key','key','token')):raise LLMError('TUKUYO_LLM_TEACHERS_MUST_NOT_CONTAIN_KEYS')
        base={'anthropic':'https://api.anthropic.com','openai':'http://localhost:11434/v1','command':None}[it['provider']]
        out.append({'provider':it['provider'],'model':it.get('model'),'base_url':it.get('base_url') or base,'command':it.get('command'),
                    'api_key_env':it.get('api_key_env'),'max_tokens':int(it.get('max_tokens',1200)),'timeout':float(it.get('timeout',90))})
    unique=[];seen=set()
    for item in out:
        identity=json.dumps({k:item.get(k) for k in ('provider','model','base_url','command')},sort_keys=True)
        if identity not in seen:unique.append(item);seen.add(identity)
    return unique

def name_of(c):
    return f"llm:{c['provider']}:{c.get('model') or (c.get('command') or 'command').split()[-1]}"

def _run_command(cmd,system,user,timeout):
    import shlex,subprocess
    argv=shlex.split(cmd)
    if not argv:raise LLMError('EMPTY_PROVIDER_COMMAND')
    payload={'schema':'tukuyo.llm.command/1','messages':[{'role':'system','content':system},{'role':'user','content':user}],'tools':[]}
    t=time.monotonic()
    try:p=subprocess.run(argv,input=json.dumps(payload,ensure_ascii=False).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout,check=False)
    except (subprocess.TimeoutExpired,OSError) as e:raise LLMError('COMMAND:'+type(e).__name__) from None
    if p.returncode!=0:raise LLMError('COMMAND:PROVIDER_RC_%d'%p.returncode)
    try:o=json.loads(p.stdout.decode());text=o['text']
    except Exception:raise LLMError('COMMAND:PROVIDER_BAD_JSON') from None
    return LLMReply(str(text),'command',str(o.get('model','command')),int((time.monotonic()-t)*1000),{})

def complete(system,user,temperature=0.0,cfg=None):
    c=cfg or config();p=c['provider']
    if p is None:raise LLMError('LLM_NOT_CONFIGURED')
    t=time.monotonic()
    if p=='command':
        if c.get('command'):return _run_command(c['command'],system,user,int(c['timeout']))
        from tukuyo_v1000.provider import call_external,ProviderError
        try:r=call_external([{'role':'system','content':system},{'role':'user','content':user}],timeout=int(c['timeout']))
        except ProviderError as e:raise LLMError('COMMAND:'+str(e)) from None
        return LLMReply(r.text,'command',str(r.metadata.get('model','command')),r.latency_ms,{})
    if not c['model']:raise LLMError('TUKUYO_LLM_MODEL_REQUIRED')
    if p=='anthropic':
        key=os.environ.get(c.get('api_key_env') or 'ANTHROPIC_API_KEY','').strip()
        if not key:raise LLMError('ANTHROPIC_API_KEY_REQUIRED')
        o=_post(c['base_url'].rstrip('/')+'/v1/messages',{'x-api-key':key,'anthropic-version':'2023-06-01','content-type':'application/json'},
                {'model':c['model'],'max_tokens':c['max_tokens'],'system':system,'temperature':temperature,'messages':[{'role':'user','content':user}]},c['timeout'])
        text=''.join(b.get('text','') for b in o.get('content',[]) if b.get('type')=='text')
        return LLMReply(text,'anthropic',str(o.get('model',c['model'])),int((time.monotonic()-t)*1000),o.get('usage',{}))
    headers={'content-type':'application/json'};key=os.environ.get(c.get('api_key_env') or 'TUKUYO_LLM_API_KEY','').strip()
    if key:headers['authorization']='Bearer '+key
    o=_post(c['base_url'].rstrip('/')+'/chat/completions',headers,
            {'model':c['model'],'temperature':temperature,'max_tokens':c['max_tokens'],'messages':[{'role':'system','content':system},{'role':'user','content':user}]},c['timeout'])
    try:text=o['choices'][0]['message']['content']
    except (KeyError,IndexError,TypeError):raise LLMError('OPENAI_RESPONSE_SHAPE') from None
    return LLMReply(text or '','openai',str(o.get('model',c['model'])),int((time.monotonic()-t)*1000),o.get('usage',{}))

def extract_json(text):
    """First balanced JSON object in the reply (models sometimes wrap JSON in prose or fences)."""
    s=str(text);start=s.find('{')
    while start!=-1:
        depth=0;instr=False;esc=False
        for i in range(start,len(s)):
            ch=s[i]
            if instr:
                if esc:esc=False
                elif ch=='\\':esc=True
                elif ch=='"':instr=False
                continue
            if ch=='"':instr=True
            elif ch=='{':depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:
                    try:
                        o=json.loads(s[start:i+1])
                        if isinstance(o,dict):return o
                    except ValueError:pass
                    break
        start=s.find('{',start+1)
    raise LLMError('LLM_JSON_MISSING')
