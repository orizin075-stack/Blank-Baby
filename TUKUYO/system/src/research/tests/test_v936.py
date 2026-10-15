import ast, hashlib, json, os, random, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tukuyo_research_v936.evaluator import rows
from tukuyo_research_v936.features import ALL_FEATURES, BASE
from tukuyo_research_v936.learner import train,score,predict,model_complexity
from tukuyo_research_v936.codegen import source
from tools.reproduce import run,legacy_score,canon,H

def test_reproduction_bit_exact():
    with tempfile.TemporaryDirectory() as p:
        summary=run(Path(p))
        assert len(summary)==3
        for file in (ROOT/'evidence').iterdir():
            assert (Path(p)/file.name).read_bytes()==file.read_bytes(),file.name

def test_truth_held_out_and_negative_labels():
    task='coupled_product';data=list(rows(task,93601,1600,'uniform'))
    hold=list(rows(task,94701,1000,'anti_corr'))
    original=train(data,ALL_FEATURES,6,35)
    rnd=random.Random(8411)
    labels=[y for _,y in data];rnd.shuffle(labels)
    poisoned=train([(m,labels[i]) for i,(m,_) in enumerate(data)],ALL_FEATURES,6,35)
    good=score(original,hold);bad=score(poisoned,hold)
    assert good['correct']>bad['correct']+200,(good,bad)

def test_derived_vs_atomic_on_novel_task():
    report=json.loads((ROOT/'evidence/REPORT.json').read_text())
    cases=[x for x in report if x['task']!='v935_reference']
    assert len(cases)==2
    for entry in cases:
        assert entry['chosen_grammar']=='expanded' and entry['chosen_complexity']['derived']
        assert all(v['chosen']['correct']>v['atomic']['correct'] for v in entry['test'].values())
        assert all(v['chosen']['correct']>v['frozen_v935']['correct'] for v in entry['test'].values())

def test_guard_prevents_overwriting_frozen_v935_on_reference():
    report=json.loads((ROOT/'evidence/REPORT.json').read_text());old=report[0]
    assert old['task']=='v935_reference'
    assert any(v['chosen']['correct']<v['frozen_v935']['correct'] for v in old['test'].values())
    status=json.loads((ROOT/'STATUS.json').read_text())
    assert status['active_policy_promotion']=='BLOCKED_NONREGRESSION'
    assert status['external_blind_evaluation']=='PENDING'

def test_interpreter_equals_compiled_generated_source():
    report=json.loads((ROOT/'evidence/REPORT.json').read_text())
    for entry in report:
        task=entry['task'];model=json.loads((ROOT/'evidence'/f'{task}_model.json').read_text())
        src=(ROOT/'evidence'/f'{task}_source.py').read_text();assert src==source(model)
        ns={'__builtins__':{'float':float}};exec(compile(src,'<generated>','exec'),ns)
        for m,y in rows(task,98421,150,'boundary'):
            assert predict(model,m)==ns['choose'](m)

def test_tree_input_rejects_nonfinite_and_missing():
    from tukuyo_research_v936.features import values
    import math
    for x in (math.inf,float('nan'),-2,2):
        try:values({'a':x,'b':0.2,'c':0.1})
        except ValueError:pass
        else:raise AssertionError('should fail')

def test_not_entire_tukuyo_agent():
    status=json.loads((ROOT/'STATUS.json').read_text())
    assert status['whole_tukuyo_core_included'] is False
    assert status['general_l6_established'] is False
