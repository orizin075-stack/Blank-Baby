import os,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_v1022 import deliberation,proofs

def chk(q,a):
    r=deliberation.solve(q);assert r and r['recognized'] and r['answer']==a,(q,r)
    assert proofs.check(r['proof'],a),(q,r)

def test_v1022_1_multistep_quantitative_reasoning():
    chk('時速5kmで4時間進むと何kmですか？','20')
    chk('120kmを時速60kmで進むと何時間ですか？','2')
    chk('150kmを3時間で進む速度は時速何kmですか？','50')
    chk('時速60kmで30分、その後時速40kmで1時間進む。合計何km？','70')
    chk('1個120円のりんごを5個買うと合計いくら？','600')
    chk('1個120円のりんごを5個買い、1000円払った。おつりは何円？','400')
    chk('800円の商品を25%値引きした価格は何円？','600')
    chk('赤と青の比は2:3。合計25個。赤は何個？','10')
    chk('10, 20, 30, 40 の平均は何？','25')
    chk('3*x+5=20 を解いて','5')

def test_v1022_1_abstains_on_ambiguous_and_bad_discrete_ratio():
    for q in ['時速およそ5kmで4時間進むと何km？','800円の商品をだいたい25%値引きすると何円？']:
        r=deliberation.solve(q);assert r and r['answer'] is None,(q,r)
    r=deliberation.solve('赤と青の比は2:3。合計26個。赤は何個？');assert r and r['answer'] is None

def test_v1022_1_proof_tamper_rejected():
    r=deliberation.solve('時速5kmで4時間進むと何kmですか？');p=dict(r['proof']);p['steps']=[dict(x) for x in p['steps']];p['steps'][-1]['value']='21'
    assert not proofs.check(p,'21')

def test_v1022_1_planner_cycle_does_not_reexpand_by_depth():
    t={'initial':{'x':0},'goal':{'x':2},'actions':[{'id':'up','pre':{},'delta':{'x':1},'cost':1},{'id':'down','pre':{},'delta':{'x':-1},'cost':1}]}
    p=proofs.plan(t,max_nodes=8);assert p['route']==['up','up'] and p['cost']==2 and p['expanded']<=3 and proofs.check_plan(t,p)

def test_v1022_1_independent_semantic_checker():
    from tukuyo_v1022.deliberation_verify import verify
    for q,a in [('時速5kmで4時間進むと何kmですか？','20'),('1個120円のりんごを5個買い、1000円払った。おつりは何円？','400'),('3*x+5=20 を解いて','5')]:
        r=verify(q,a);assert r['recognized'] and r['decidable'] and r['supported'],(q,r)
        assert not verify(q,str(int(float(a))+1))['supported']

def test_v1022_1_occurrence_grounds_full_conditional_antecedent():
    # Regression in claude-patch1: antecedent was "雨が降る" while occurrence grounding tried to add only "雨".
    from tukuyo_v1022.cognition import logic
    r=logic('もし雨が降るなら地面が濡れる。雨が降っている。地面は濡れる？')
    assert r['answer'] is not None and not r['uncertain'] and '濡れる' in r['answer'],r
    for q in ['雨なら地面が濡れる。雨が降った夢を見た。地面は濡れる？','雨なら地面が濡れる。雨が降ると聞いた。地面は濡れる？']:
        assert logic(q)['answer'] is None
