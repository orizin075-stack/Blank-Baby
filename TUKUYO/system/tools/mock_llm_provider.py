#!/usr/bin/env python3
"""Deterministic STAND-IN for an LLM, for testing claude-patch1 plumbing only.

It is NOT intelligent: it knows a few verbs, a few paraphrases and a few facts, so that the
bridge, the claim checks and the teacher pipeline can be exercised offline. Any capability
number obtained with this mock says nothing about a real model.

Use as a command provider:
  TUKUYO_LLM_COMMAND="python3 -B tools/mock_llm_provider.py"
  MOCK_LLM_MODE = honest | wrong_calc | fake_memory | inconsistent | liar | fail | tools
"""
import json,os,re,sys,tempfile
from pathlib import Path

MODE=os.environ.get('MOCK_LLM_MODE','honest')
for _a in sys.argv[1:]:
    if _a.startswith('--mode='):MODE=_a.split('=',1)[1]
DOWN=['販売','出荷','譲り','寄付','売り払','なくして','失くし','紛失','盗まれ','返品','手放']
UP=['仕入','入荷','補充','借りてきて','受け取','もらって']
SYN={'住んでいる街','暮らしている町','住まいのある都市','今住んでいるところ','住所のある都市'}
UNITS='個|枚|本|冊|台|人';BOX='箱|袋|パック|ケース|束'

def counter():
    p=Path(os.environ.get('MOCK_LLM_STATE',Path(tempfile.gettempdir())/'mock_llm_counter'));n=int(p.read_text()) if p.exists() else 0
    p.write_text(str(n+1));return n

def event_reply(q):
    m=re.search(rf'1\s*({BOX})に?(\d+)\s*({UNITS})入りが(\d+)\s*\1',q)
    if not m:return {'events':[],'answer':None}
    per=int(m[2]);n=per*int(m[4]);events=[]
    flip=-1 if MODE=='liar' or (MODE=='inconsistent' and counter()%2==1) else 1
    for c in re.split(r'[。]',q[m.end():]):
        qm=re.search(rf'(\d+)\s*({UNITS}|{BOX})',c)
        if not qm:continue
        d=-1 if any(v in c for v in DOWN) else (1 if any(v in c for v in UP) else 0)
        d*=flip;events.append({'surface':c.strip(),'direction':d,'occurred':True,'scope':'current_inventory'})
        n+=d*int(qm[1])*(per if qm[2]==m[1] else 1)
    return {'events':events,'answer':str(n)}

def alias_reply(q,cands):
    out=[{'surface':s,'canonical':'現在の居住地'} for s in SYN if s in q and '現在の居住地' in cands]
    return {'aliases':out}

def bridge_reply(u,tool_results=None):
    q=u.get('question','');mem=u.get('tukuyo_state',{}).get('memories',[])
    if MODE=='fabricate':        # claude-patch4 regression: an invented claim dressed up with an unrelated correct calc
        return {'answer':'光の速さは秒速30万kmです。','unknown':False,'confidence':.95,'claims':[{'type':'calc','expression':'1+1','value':'2'}]}
    if MODE=='fabricate2':       # the calc is used, but the rest of the sentence is invented
        return {'answer':'星野村の人口は2人で、村長は山田です。','unknown':False,'confidence':.95,'claims':[{'type':'calc','expression':'1+1','value':'2'}]}
    if MODE=='tools':
        if tool_results is None:return {'tool_requests':[{'tool':'solve','question':q},{'tool':'search','query':q}]}
        for t in tool_results:
            if t.get('tool')=='solve' and t.get('certain'):
                return {'answer':f"{t['answer']}です。",'unknown':False,'confidence':.9,'claims':[{'type':'local','question':q,'value':str(t['answer'])}]}
        return {'answer':'わかりません。','unknown':True,'confidence':.1,'claims':[]}
    m=re.search(r'(\d+)かける(\d+)足す(\d+)',q)
    if m:
        v=int(m[1])*int(m[2])+int(m[3]);v=v+1 if MODE=='wrong_calc' else v
        return {'answer':f'{v}です。','unknown':False,'confidence':.9,'claims':[{'type':'calc','expression':f'{m[1]}*{m[2]}+{m[3]}','value':str(v)}]}
    for mm in mem:
        ent=re.match(r'(.+?)の',mm['text'])
        key=ent.group(1) if ent else mm['text'][:4]
        if key and key in q:
            mid='k:does-not-exist' if MODE=='fake_memory' else mm['id']
            return {'answer':f"記憶では、{mm['text']}",'unknown':False,'confidence':.85,'claims':[{'type':'memory','id':mid,'quote':mm['text']}]}
    if '光の速さ' in q:
        return {'answer':'光の速さはおよそ秒速30万キロメートルです。','unknown':False,'confidence':.9,'claims':[{'type':'external','statement':'真空中の光速は約299,792 km/s'}]}
    return {'answer':'その質問には、今わかる根拠がありません。','unknown':True,'confidence':.1,'claims':[]}

def main():
    if MODE=='fail':sys.stderr.write('mock failure');sys.exit(1)
    p=json.loads(sys.stdin.read());system=p['messages'][0]['content'];user=p['messages'][1]['content']
    body=user.split('\n\n')[0];u=json.loads(body)
    tr=None
    if '\n\n道具の結果: ' in user:tr=json.loads(user.split('\n\n道具の結果: ')[1].split('\n\n')[0])
    if '在庫の文章題を分解' in system:o=event_reply(u['question'])
    elif '言い換えを判定' in system:o=alias_reply(u['question'],u.get('candidates',[]))
    else:o=bridge_reply(u,tr)
    print(json.dumps({'text':json.dumps(o,ensure_ascii=False),'model':'mock-'+MODE},ensure_ascii=False))
main()
