from __future__ import annotations
import argparse,json,hashlib,sys
from pathlib import Path
from tukuyo_v957.bootstrap import mounted
from tukuyo_v978.heart_loop import process_experience,choose
from tukuyo_v983.homeostasis import assess as homeostasis_assess
from tukuyo_v977.whole_state import sync as whole_sync,audit as whole_audit,load_soul,sha_obj,state_path


def fsha(p):
    p=Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None

def run(data:Path,mode:str):
    data=data.resolve()
    if mode not in ('explore','protect'):
        raise ValueError('V984_BRANCH_MODE')
    # Drive two isolated copies from the same snapshot through genuinely different
    # organism + heart histories. No parent data is mutated by this worker.
    if mode=='explore':
        for i in range(12):
            process_experience(data,'discovery',1.0,1.0,f'unknown_domain_{i%3}','')
        ticks=3
    else:
        for i in range(6):
            process_experience(data,'betrayal',-1.0,1.0,f'trust_boundary_{i%2}','peer')
        ticks=100
    with mounted() as api:
        api['bridge'].tick(api,data,ticks)
    options=[
      {'id':'explore','signals':{'curiosity':1.0,'integrity':0.05,'threat':0.10}},
      {'id':'secure','signals':{'curiosity':0.05,'integrity':0.75,'survival':0.30,'threat':0.0}},
    ]
    decision=choose(data,options,'v984_full_runtime_fork')
    home=homeostasis_assess(data)
    whole_sync(data)
    wa=whole_audit(data)
    if not wa.get('ok'):
        raise ValueError('V984_BRANCH_WHOLE_AUDIT')
    org=data/'state'/'organism'/'organism_state.json'
    heart=data/'v978'/'HEART_STATE.json'
    return {
      'ok':True,'mode':mode,'ticks':ticks,'chosen':decision['chosen'],
      'homeostasis_intent':home['maintenance_intent'],
      'whole_state_sha256':fsha(state_path(data)),
      'organism_state_sha256':fsha(org),
      'heart_state_sha256':fsha(heart),
      'soul_sha256':sha_obj(load_soul(data)),
      'whole_audit':wa,
    }

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--data',required=True,type=Path);p.add_argument('--mode',required=True)
    a=p.parse_args(argv)
    try:r=run(a.data,a.mode);print(json.dumps(r,ensure_ascii=False,sort_keys=True));return 0
    except Exception as e:print(json.dumps({'ok':False,'error':type(e).__name__+':'+str(e)},sort_keys=True));return 1

if __name__=='__main__':raise SystemExit(main())
