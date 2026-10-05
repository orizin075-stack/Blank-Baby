"""patch6's research_without_invention on patch5's held-out key and seeds (50000-50019, tiers 1-4) vs the
'research' episodes in patch5's published evidence file: must be identical episode by episode."""
import json,sys,hashlib
sys.path.insert(0,'/tmp/claude-0/-home-user-Blank-Baby/dd3c6b53-ae17-5414-bda7-717330a62fb9/scratchpad/run6f/system/src')
from tukuyo_v1023r.worlds import DeviceWorld
from tukuyo_v1023r.ecology import run_episode,REGIMES
from tukuyo_v1023r.evaluate import KEY
ev=json.load(open('/home/user/Blank-Baby/TUKUYO_v1022_5_claude_patch6/evidence_claude_patch5/heldout_research_ecology.json'))
keys=('alive','final_energy','law_claimed','law_correct','wrong_law_claimed','unexplained','status','method')
p5={(r['regime'],r['seed'],r['tier'],r['noise']):{k:r[k] for k in keys} for r in ev['episodes'] if r['policy']=='research'}
same=diff=0;bad=[]
for (reg,s,tier,noise),want in sorted(p5.items()):
    r=run_episode(DeviceWorld(KEY,s,tier,noise),'research',econ=REGIMES[reg],seed=s,invent=False)
    got={k:r.get(k) for k in keys}
    if got==want:same+=1
    else:diff+=1;bad.append(((reg,s,tier,noise),want,got))
print(json.dumps({'compared':len(p5),'identical':same,'different':diff,'examples':bad[:3]},ensure_ascii=False))
