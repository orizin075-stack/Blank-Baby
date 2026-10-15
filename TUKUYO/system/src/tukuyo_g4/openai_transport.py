"""Bounded Responses decoding and secret-free recovery advice, no auto resend."""
import math,re

KNOWN_CODES={
 'subscription_sharing_user_not_eligible','subscription_sharing_usage_limit_exceeded',
 'subscription_sharing_usage_unavailable','subscription_sharing_unsupported_capability',
 'subscription_sharing_route_not_supported','subscription_sharing_invalid_user',
 'subscription_sharing_user_unavailable','chatpass_v2_scope_not_authorized',
 'chatpass_v2_invalid_authorization_context','rate_limit_exceeded','insufficient_quota',
 'invalid_api_key','server_error','invalid_request_error',
}

def failure(reason,code=None,status=None,headers=None,param=None):
    code=code if code in KNOWN_CODES else None
    action='inspect_configuration';retry=False;outcome='rejected' if status and 400<=status<500 else 'unknown';reauth=False
    if reason in ('CONNECTION','TIMEOUT','STREAM_INTERRUPTED','STREAM_EVENT_BOUND'):
        action='resolve_unknown_outcome';outcome='unknown'
    elif code in ('subscription_sharing_usage_limit_exceeded','insufficient_quota'):
        action='pause_usage'
    elif code in ('subscription_sharing_usage_unavailable','subscription_sharing_user_unavailable') or status in (429,503,500,502,504):
        action='wait_then_retry_manually';retry=True
        if status and status>=500 and not code:outcome='unknown'
    elif reason in ('AUTHENTICATION','CHATGPT_LOGIN_REQUIRED') or code in ('invalid_api_key','subscription_sharing_invalid_user'):
        action='reauthenticate_or_replace_key';reauth=True
    elif reason=='CHATGPT_REFRESH_UNAVAILABLE':action='wait_then_retry_manually';retry=True
    elif reason.startswith('STREAM_'):
        action='inspect_stream_failure';outcome='unknown'
    advice={'action':action,'retryable':retry,'automatic_retry':False,'remote_outcome':outcome,'requires_reauthentication':reauth}
    if headers:
        try:
            delay=float(headers.get('retry-after',''))
            if math.isfinite(delay) and 0<=delay<=3600:advice['retry_after_seconds']=delay
        except (TypeError,ValueError):pass
    allowed={'model','input','instructions','tools','max_output_tokens','previous_response_id','temperature','stream','store','text','reasoning','service_tier'}
    safe_param=param if isinstance(param,str) and len(param)<=100 and re.fullmatch(r'[A-Za-z_]+(?:\[\d+\]|\.[A-Za-z_]+)*',param) and re.split(r'[.\[]',param)[0] in allowed else None
    return {'ok':False,'reason':reason,'provider_code':code,'provider_param':safe_param,'http_status':status,'recovery':advice}

def stream_result(events):
    completed=None;parts=[];size=0
    for count,event in enumerate(events,1):
        if count>4096:return None,failure('STREAM_EVENT_BOUND')
        kind=getattr(event,'type',None)
        if kind in ('response.failed','response.incomplete','error'):
            err=getattr(getattr(event,'response',None),'error',None)
            code=getattr(err,'code',None) or getattr(event,'code',None)
            reason='STREAM_FAILED:'+str(code if code in KNOWN_CODES else kind)
            return None,failure(reason,code)
        if kind=='response.output_text.delta':
            if completed is not None:return None,failure('STREAM_PROTOCOL_AFTER_COMPLETION')
            delta=getattr(event,'delta',None)
            if not isinstance(delta,str):return None,failure('STREAM_INVALID_DELTA')
            size+=len(delta)
            if size>65536:return None,failure('RESPONSE_TOO_LARGE')
            parts.append(delta)
        if kind=='response.completed':
            if completed is not None:return None,failure('STREAM_DUPLICATE_COMPLETION')
            completed=getattr(event,'response',None)
            if completed is None:return None,failure('STREAM_INVALID_COMPLETION')
    if completed is None:return None,failure('STREAM_INTERRUPTED')
    if parts and ''.join(parts)!=getattr(completed,'output_text',None):return None,failure('STREAM_TEXT_MISMATCH')
    return completed,None

def completed_result(response):
    if getattr(response,'status',None)!='completed':
        detail=getattr(getattr(response,'incomplete_details',None),'reason',None)
        reason='INCOMPLETE:'+detail if detail in ('max_output_tokens','content_filter') else 'INCOMPLETE'
        return failure(reason)
    text=getattr(response,'output_text',None)
    if not isinstance(text,str):return failure('INVALID_RESPONSE_TEXT')
    if len(text)>65536:return failure('RESPONSE_TOO_LARGE')
    output=getattr(response,'output',None) or []
    if any(getattr(x,'type',None) not in ('message','reasoning') for x in output):return failure('UNSUPPORTED_RESPONSE_ITEM')
    if any(getattr(c,'type',None)=='refusal' for x in output if getattr(x,'type',None)=='message' for c in (getattr(x,'content',None) or [])):
        return failure('REFUSAL')
    if not text.strip():return failure('EMPTY_RESPONSE')
    usage=getattr(response,'usage',None)
    values={k:getattr(usage,k,None) for k in ('input_tokens','output_tokens')} if usage else {}
    if any(v is not None and (type(v) is not int or v<0) for v in values.values()):return failure('INVALID_RESPONSE_USAGE')
    return {'ok':True,'text':text,'model':getattr(response,'model',None),'request_id':getattr(response,'id',None),'usage':values}
