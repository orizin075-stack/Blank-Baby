"""Dedicated TUKUYO SIWC credentials. No host/Codex credentials are read.

Official contract checked 2026-10-08. Credentials stay outside individual data.
No login or inference happens on import or while inspecting connection status.
"""
from __future__ import annotations
import base64,hashlib,json,os,secrets,stat,time,uuid,math,threading
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from urllib.parse import urlencode,urlparse,parse_qs

ISSUER='https://auth.openai.com'
AUTHORIZE=ISSUER+'/api/accounts/authorize'
TOKEN=ISSUER+'/api/accounts/oauth/token'
RESOURCE='https://api.openai.com/v1'
SCOPES='openid profile email offline_access resource.invoke chatgpt.tokens.use.direct'
SCHEMA='tukuyo.chatgpt.credentials/1'

def path():
    return Path(os.environ.get('TUKUYO_CHATGPT_CREDENTIAL_FILE') or Path.home()/'.config/tukuyo/chatgpt.json').expanduser()

def mode():
    value=os.environ.get('TUKUYO_CHATGPT_AUTH','api').strip()
    if value not in ('api','plan'):raise ValueError('CHATGPT_AUTH_MODE')
    return value

_held_lock=ContextVar('tukuyo_chatgpt_credential_lock',default=None)
_thread_lock=threading.RLock()
@contextmanager
def credential_lock(p):
    p=Path(p).absolute()
    if _held_lock.get()==str(p):yield;return
    with _thread_lock:
        if p.is_symlink() or p.parent.is_symlink():raise ValueError('CHATGPT_CREDENTIAL_SYMLINK')
        p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        lock=p.with_name(p.name+'.lock')
        flags=os.O_CREAT|os.O_RDWR|getattr(os,'O_NOFOLLOW',0)
        fd=os.open(lock,flags,0o600)
        try:
            if os.name=='nt':
                import msvcrt
                if os.fstat(fd).st_size==0:os.write(fd,b'0')
                os.lseek(fd,0,0);msvcrt.locking(fd,msvcrt.LK_LOCK,1)
            else:
                import fcntl
                fcntl.flock(fd,fcntl.LOCK_EX)
            token=_held_lock.set(str(p))
            try:yield
            finally:_held_lock.reset(token)
        finally:
            if os.name=='nt':
                os.lseek(fd,0,0);msvcrt.locking(fd,msvcrt.LK_UNLCK,1)
            else:
                import fcntl
                fcntl.flock(fd,fcntl.LOCK_UN)
            os.close(fd)

def require_external_to(data):
    individual=Path(data).resolve()
    if path().resolve().is_relative_to(individual):
        raise ValueError('CHATGPT_CREDENTIAL_INSIDE_INDIVIDUAL')

def write_private(p,obj):
    with credential_lock(p):_write_private(p,obj)

def _write_private(p,obj):
    p=Path(p)
    if p.is_symlink():raise ValueError('CHATGPT_CREDENTIAL_SYMLINK')
    p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    tmp=p.with_name(p.name+'.'+secrets.token_hex(8)+'.tmp')
    fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(obj,f,ensure_ascii=False);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(tmp,p)
        if os.name!='nt':p.chmod(0o600)
    finally:
        if tmp.exists():tmp.unlink()

def load():
    p=path()
    if not p.exists():return None
    if p.is_symlink():raise ValueError('CHATGPT_CREDENTIAL_SYMLINK')
    if os.name!='nt' and stat.S_IMODE(p.stat().st_mode)&0o077:raise ValueError('CHATGPT_CREDENTIAL_PERMISSIONS')
    o=json.loads(p.read_text())
    if not isinstance(o,dict):raise ValueError('CHATGPT_CREDENTIAL_IDENTITY')
    if o.get('schema')!=SCHEMA or o.get('issuer')!=ISSUER or not isinstance(o.get('subject'),str) or not o['subject'] or not isinstance(o.get('client_id'),str) or not o['client_id'].startswith('oaiapp_'):
        raise ValueError('CHATGPT_CREDENTIAL_IDENTITY')
    scopes=o.get('scopes');access=o.get('access_token')
    if not isinstance(scopes,list) or any(not isinstance(x,str) for x in scopes) or 'chatgpt.tokens.use.direct' not in scopes or (not (isinstance(access,str) and access) and o.get('reauthentication_required') is not True):
        raise ValueError('CHATGPT_PLAN_SCOPE_MISSING')
    try:expires=float(o.get('expires_at',0))
    except (TypeError,ValueError):raise ValueError('CHATGPT_CREDENTIAL_EXPIRY') from None
    if not math.isfinite(expires):raise ValueError('CHATGPT_CREDENTIAL_EXPIRY')
    return o

def status():
    try:o=load()
    except (ValueError,OSError):return {'configured':False,'reason':'CHATGPT_CREDENTIAL_INVALID'}
    if not o:return {'configured':False,'reason':'CHATGPT_LOGIN_REQUIRED'}
    if o.get('reauthentication_required'):return {'configured':False,'reason':'CHATGPT_LOGIN_REQUIRED','registration_retained':True,'model':o.get('model')}
    return {'configured':True,'model':o.get('model'),'expires_at':o.get('expires_at'),
            'expired':float(o.get('expires_at',0))<=time.time(),'plan_scope':True,
            'credentials_outside_individual_data':True}

def prepare(host_id,redirect_uri,previous=None,allow_id_token_hint=True):
    u=urlparse(redirect_uri)
    if u.scheme!='http' or u.hostname!='127.0.0.1' or u.path!='/auth/callback' or not u.port or u.query or u.fragment:
        raise ValueError('CHATGPT_LOOPBACK_CALLBACK')
    previous=previous or {};verifier=secrets.token_urlsafe(48)
    pending={'state':secrets.token_urlsafe(32),'nonce':secrets.token_urlsafe(32),'verifier':verifier,
             'redirect_uri':redirect_uri,'expires_at':time.time()+600,'ext_agent_host_id':host_id,
             'client_id':previous.get('client_id') or 'dynamic_agent_client','subject':previous.get('subject')}
    q={'client_id':pending['client_id'],'ext_agent_host_id':host_id,'response_type':'code','redirect_uri':redirect_uri,
       'scope':SCOPES,'resource':RESOURCE,'state':pending['state'],'nonce':pending['nonce'],'code_challenge_method':'S256',
       'code_challenge':base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')}
    if pending['client_id']=='dynamic_agent_client':q['agent_name_hint']='TUKUYO'
    elif allow_id_token_hint and previous.get('id_token'):q['id_token_hint']=previous['id_token']
    return pending,AUTHORIZE+'?'+urlencode(q)

def callback(pending,query):
    q=parse_qs(query,keep_blank_values=True)
    if any(len(v)!=1 for v in q.values()):raise ValueError('CHATGPT_CALLBACK_DUPLICATE')
    one=lambda k:q.get(k,[''])[0]
    if time.time()>pending['expires_at'] or not secrets.compare_digest(one('state'),pending['state']):
        raise ValueError('CHATGPT_CALLBACK_STATE')
    if one('error'):raise ValueError('CHATGPT_CONSENT_DECLINED')
    issued=one('client_id') or pending['client_id']
    if not issued.startswith('oaiapp_'):raise ValueError('CHATGPT_ISSUED_CLIENT_MISSING')
    if pending['client_id']!='dynamic_agent_client' and issued!=pending['client_id']:raise ValueError('CHATGPT_CLIENT_CHANGED')
    if not one('code'):raise ValueError('CHATGPT_CODE_MISSING')
    return {'grant_type':'authorization_code','client_id':issued,'code':one('code'),
            'code_verifier':pending['verifier'],'redirect_uri':pending['redirect_uri'],'resource':RESOURCE}

def verify_identity(id_token,client_id,nonce=None,subject=None):
    import httpx,jwt
    discovery=httpx.get(ISSUER+'/.well-known/openid-configuration',timeout=20);discovery.raise_for_status();d=discovery.json()
    jwks=urlparse(d['jwks_uri'])
    if d.get('issuer')!=ISSUER or jwks.scheme!='https' or jwks.hostname!='auth.openai.com':raise ValueError('CHATGPT_DISCOVERY')
    key=jwt.PyJWKClient(d['jwks_uri'],timeout=20).get_signing_key_from_jwt(id_token).key
    allowed=[x for x in d.get('id_token_signing_alg_values_supported',['RS256']) if x in ('RS256','ES256')]
    if not allowed:raise ValueError('CHATGPT_ID_TOKEN_ALGORITHM')
    claims=jwt.decode(id_token,key,algorithms=allowed,audience=client_id,issuer=ISSUER,
                      options={'require':['sub','iss','aud','exp']})
    if nonce is not None and not secrets.compare_digest(str(claims.get('nonce','')),nonce):raise ValueError('CHATGPT_ID_TOKEN_NONCE')
    if subject is not None and claims['sub']!=subject:raise ValueError('CHATGPT_ACCOUNT_CHANGED')
    return claims

def token_record(tokens,client_id,host_id,claims,previous=None):
    scopes=str(tokens.get('scope','')).split()
    if 'chatgpt.tokens.use.direct' not in scopes or str(tokens.get('token_type','')).lower()!='bearer' or not tokens.get('access_token'):
        raise ValueError('CHATGPT_PLAN_SCOPE_MISSING')
    try:lifetime=int(tokens.get('expires_in',3600))
    except (TypeError,ValueError):raise ValueError('CHATGPT_TOKEN_EXPIRY') from None
    if not 1<=lifetime<=86400:raise ValueError('CHATGPT_TOKEN_EXPIRY')
    return {'schema':SCHEMA,'issuer':ISSUER,'subject':claims['sub'],'client_id':client_id,'ext_agent_host_id':host_id,
            'id_token':tokens.get('id_token') or (previous or {}).get('id_token'),
            'access_token':tokens['access_token'],'refresh_token':tokens.get('refresh_token') or (previous or {}).get('refresh_token'),
            'scopes':scopes,'expires_at':time.time()+lifetime,
            'model':(previous or {}).get('model')}

def credential(selected_mode=None):
    selected_mode=selected_mode or mode()
    if selected_mode not in ('api','plan'):raise ValueError('CHATGPT_AUTH_MODE')
    if selected_mode!='plan':return os.environ.get('TUKUYO_OPENAI_API_KEY','').strip()
    with credential_lock(path()):return _plan_credential()

def _plan_credential():
    o=load()
    if not o or o.get('reauthentication_required'):raise ValueError('CHATGPT_LOGIN_REQUIRED')
    if float(o.get('expires_at',0))<time.time()+30:
        if not o.get('refresh_token'):raise ValueError('CHATGPT_LOGIN_REQUIRED')
        import httpx
        try:r=httpx.post(TOKEN,data={'grant_type':'refresh_token','client_id':o['client_id'],
                                   'refresh_token':o['refresh_token'],'resource':RESOURCE},timeout=30)
        except httpx.TransportError:raise ValueError('CHATGPT_REFRESH_UNAVAILABLE') from None
        if r.status_code!=200:
            try:error=r.json().get('error');code=error.get('code') if isinstance(error,dict) else error
            except (ValueError,AttributeError):code=None
            if code in ('invalid_grant','invalid_refresh_token','token_expired','refresh_token_expired','refresh_token_invalidated','refresh_token_reused'):
                o={k:v for k,v in o.items() if k not in ('access_token','refresh_token','id_token')};o['reauthentication_required']=True
                write_private(path(),o);raise ValueError('CHATGPT_LOGIN_REQUIRED')
            if code=='invalid_client':raise ValueError('CHATGPT_REFRESH_INVALID_CLIENT')
            raise ValueError('CHATGPT_REFRESH_UNAVAILABLE' if r.status_code>=500 or r.status_code==429 else 'CHATGPT_REFRESH_FAILED')
        t=r.json();t['scope']=t.get('scope') or ' '.join(o['scopes'])
        c=verify_identity(t['id_token'],o['client_id'],subject=o['subject']) if t.get('id_token') else {'sub':o['subject']}
        o=token_record(t,o['client_id'],o['ext_agent_host_id'],c,o);write_private(path(),o)
    return o['access_token']

def models(selected_mode=None):
    import httpx
    selected=selected_mode or mode();key=credential(selected)
    if not key:return {'ok':False,'reason':'CHATGPT_LOGIN_REQUIRED'}
    endpoint=RESOURCE if selected=='plan' else os.environ.get('TUKUYO_OPENAI_BASE_URL',RESOURCE).rstrip('/')
    r=httpx.get(endpoint+'/models',headers={'Authorization':'Bearer '+key},timeout=30)
    if r.status_code!=200:return {'ok':False,'reason':'MODEL_CATALOG_HTTP_'+str(r.status_code)}
    o=r.json()
    rows=[{'id':x['slug'],'name':x.get('display_name',x['slug'])} for x in o.get('models',[]) if x.get('visibility')=='list'] if selected=='plan' else [{'id':x['id'],'name':x['id']} for x in o.get('data',[])]
    return {'ok':True,'models':rows,'mode':selected}

def login(model=None,open_browser=True,timeout=300):
    """Run only on the user's own computer; the browser performs authentication."""
    from http.server import HTTPServer,BaseHTTPRequestHandler
    import httpx,webbrowser
    previous=load();p=path();host_path=p.parent/'chatgpt_host.json'
    if host_path.exists():host=json.loads(host_path.read_text())['ext_agent_host_id']
    else:host='urn:uuid:'+str(uuid.uuid4());write_private(host_path,{'ext_agent_host_id':host})
    result={}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            u=urlparse(self.path)
            if u.path!='/auth/callback':self.send_error(404);return
            try:result['exchange']=callback(pending,u.query);self.send_response(200)
            except ValueError as e:result['error']=str(e);self.send_response(400)
            self.send_header('Content-Type','text/plain; charset=utf-8');self.end_headers();self.wfile.write(b'Return to TUKUYO to finish connecting.')
    with HTTPServer(('127.0.0.1',0),Handler) as server:
        server.timeout=1;pending,url=prepare(host,f'http://127.0.0.1:{server.server_port}/auth/callback',previous,allow_id_token_hint=open_browser)
        print('Continue with ChatGPT',flush=True)
        if open_browser:webbrowser.open(url)
        else:print(url,flush=True)
        deadline=time.monotonic()+timeout
        while not result and time.monotonic()<deadline:server.handle_request()
    if result.get('error'):raise ValueError(result['error'])
    if not result:raise ValueError('CHATGPT_LOGIN_TIMEOUT')
    ex=result['exchange'];r=httpx.post(TOKEN,data=ex,timeout=30)
    if r.status_code!=200:raise ValueError('CHATGPT_TOKEN_EXCHANGE_FAILED')
    t=r.json();claims=verify_identity(t['id_token'],ex['client_id'],pending['nonce'],pending['subject'])
    o=token_record(t,ex['client_id'],host,claims,previous);write_private(p,o)
    if model:
        old=os.environ.get('TUKUYO_CHATGPT_AUTH');os.environ['TUKUYO_CHATGPT_AUTH']='plan'
        try:
            choices=models()
            if not choices['ok'] or model not in {x['id'] for x in choices['models']}:raise ValueError('CHATGPT_MODEL_NOT_AVAILABLE')
            o['model']=model;write_private(p,o)
        finally:
            if old is None:os.environ.pop('TUKUYO_CHATGPT_AUTH',None)
            else:os.environ['TUKUYO_CHATGPT_AUTH']=old
    return {'ok':True,'connected':True,'mode':'plan','model':o.get('model'),'account_identity_verified':True}
