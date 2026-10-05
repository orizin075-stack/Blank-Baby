from __future__ import annotations
import json, os, shlex, subprocess, time
from dataclasses import dataclass

@dataclass
class ProviderResult:
    text: str
    provider: str
    latency_ms: int
    metadata: dict

class ProviderError(RuntimeError): pass

def provider_name() -> str:
    return 'command' if os.environ.get('TUKUYO_LLM_COMMAND','').strip() else 'builtin'

def call_external(messages, tools=None, timeout=120) -> ProviderResult:
    cmd=os.environ.get('TUKUYO_LLM_COMMAND','').strip()
    if not cmd: raise ProviderError('EXTERNAL_PROVIDER_NOT_CONFIGURED')
    argv=shlex.split(cmd)
    if not argv: raise ProviderError('EMPTY_PROVIDER_COMMAND')
    payload={'schema':'tukuyo.llm.command/1','messages':messages,'tools':tools or []}
    t=time.monotonic()
    p=subprocess.run(argv,input=json.dumps(payload,ensure_ascii=False).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout,check=False)
    ms=int((time.monotonic()-t)*1000)
    if p.returncode!=0: raise ProviderError('PROVIDER_RC_%d:%s'%(p.returncode,p.stderr.decode(errors='replace')[:500]))
    try:o=json.loads(p.stdout.decode())
    except Exception as e: raise ProviderError('PROVIDER_BAD_JSON') from e
    text=o.get('text') if isinstance(o,dict) else None
    if not isinstance(text,str): raise ProviderError('PROVIDER_TEXT_MISSING')
    return ProviderResult(text=text,provider='command',latency_ms=ms,metadata={k:v for k,v in o.items() if k!='text'})
