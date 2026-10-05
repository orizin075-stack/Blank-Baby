import argparse,hashlib,json,sys,pathlib,random
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tukuyo_research_v936.evaluator import rows
from tukuyo_research_v936.features import BASE,ALL_FEATURES
from tukuyo_research_v936.learner import train,score,model_complexity
from tukuyo_research_v936.codegen import source
TASKS=('v935_reference','coupled_product','difference_shift')
LEGACY_SOURCE=ROOT/'baselines/V935_FROZEN_CANDIDATE.py'
def legacy_score(examples):
    from tukuyo_research_v936.learner import ACTIONS
    import ast
    txt=LEGACY_SOURCE.read_text()
    if H(txt.encode())!='bc880c6a7c3023a37087150ff9a6294497a07ef8ec42904c9b772547332a5f3e': raise RuntimeError('FROZEN_V935_HASH_MISMATCH')
    t=ast.parse(txt)
    if not (len(t.body)==1 and isinstance(t.body[0],ast.FunctionDef)): raise RuntimeError('FROZEN_V935_AST_SHAPE')
    ns={'__builtins__':{}};exec(compile(txt,'<frozen v935>','exec'),ns)
    fn=ns['choose'];correct=0
    for m,label in examples:
        old={'ambiguous_failure':m['a'],'representation_failure':m['b'],'consistency_failure':m['c']}
        correct+=fn(old)==label
    return {'n':len(examples),'correct':correct,'wrong':len(examples)-correct}

def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def H(x):return hashlib.sha256(x).hexdigest()
def one(task,train_seed=93601):
    # Training labels given to the learner, not access to the oracle source.
    data=list(rows(task,train_seed,2200,'uniform'))+list(rows(task,train_seed+1,1400,'edges'))
    val=list(rows(task,train_seed+7,950,'anti_corr'))
    # Full grammar and atomic baseline have equal search depth and training examples.
    atomic=train(data,BASE,6,35)
    expanded=train(data,ALL_FEATURES,6,35)
    baseline_val=score(atomic,val);exp_val=score(expanded,val)
    # A failed derived grammar is not silently promoted.
    chosen=expanded if exp_val['correct']>baseline_val['correct'] else atomic
    chosen_name='expanded' if chosen is expanded else 'atomic_fallback'
    test={dist:{'atomic':score(atomic,list(rows(task,train_seed+100+i,1500,dist))),
                'chosen':score(chosen,list(rows(task,train_seed+100+i,1500,dist))), 'frozen_v935':legacy_score(list(rows(task,train_seed+100+i,1500,dist)))}
          for i,dist in enumerate(('uniform','edges','anti_corr','boundary'))}
    return {'task':task,'train_n':len(data),'validation_n':len(val), 'baseline_validation':baseline_val,
            'expanded_validation':exp_val,'chosen_grammar':chosen_name,'atomic_complexity':model_complexity(atomic),
            'chosen_complexity':model_complexity(chosen), 'test':test,'models':{'atomic':atomic,'expanded':expanded,'chosen':chosen},
            'generated_source':source(chosen)}
def run(out):
    all_results=[one(task) for task in TASKS]
    out.mkdir(parents=True,exist_ok=True)
    summary=[]
    for result in all_results:
        task=result['task'];model=result.pop('models');src=result.pop('generated_source')
        (out/f'{task}_model.json').write_bytes(canon(model['chosen'])+b'\n')
        (out/f'{task}_source.py').write_text(src)
        result['model_sha256']=H(canon(model['chosen'])+b'\n')
        result['source_sha256']=H(src.encode())
        summary.append(result)
    (out/'REPORT.json').write_bytes(canon(summary)+b'\n')
    return summary
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);args=p.parse_args()
    print(json.dumps(run(pathlib.Path(args.out)),ensure_ascii=False))
