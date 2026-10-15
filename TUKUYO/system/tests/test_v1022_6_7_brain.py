"""Clarification, method equivalence and rejected transfer; teachers are fixtures."""
import copy,json,re
from pathlib import Path
import pytest
from test_v1022_5_fusion import run
from test_v1022_6_6_chatgpt import clean,fixture_transport
from test_g4_learn import T,READING
from tukuyo_g4 import learn,llm,api,chatgpt_study as study,methods
from tukuyo_v1022 import clarification as clarify
from tukuyo_v1022 import constraints
from tukuyo_v1022.constraints_verify import verify_nonunique

def spec(text=T,alternate=False):
    r=copy.deepcopy(READING);number=re.search(r'result is (\d+)',text)[1]
    for f in r['facts']:f['eq']=f['eq'].replace('30',number);f['span']=f['span'].replace('30',number)
    if alternate:
        renames={'twelve':'offset','factor':'scale','result':'total','number':'unknown'}
        r['facts'][3]['eq']='result + twelve = number * factor'
        for f in r['facts']:
            f['eq']=re.sub(r'\b(twelve|factor|result|number)\b',lambda m:renames[m[0]],f['eq'])
        r['facts'][2]['eq']=number+' = total'
        for q in r['quantities']:q['name']=renames[q['name']]
        r['ask']='unknown';r['facts'].reverse();r['quantities'].reverse()
    return llm.read_reply(text,{'ok':True,'text':json.dumps(r)})['spec']

def fingerprint(d):
    return {p.relative_to(d).as_posix():p.read_bytes() for p in d.rglob('*') if p.is_file() and '.v1019_txn' not in p.parts}

def test_equivalent_teaching_forms_consolidate_and_transfer(tmp_path):
    a=spec();b=spec(T.replace('30','45'),True)
    assert methods.equivalent(learn.template(a),learn.template(b))
    st=learn.Store(tmp_path/'d/g4');tid=st.add(a,{'fixture':True})
    assert st.add(b,{'fixture':True})==tid and st.audit()['templates']==1
    assert api.solve(T.replace('30','60'),llm='off',data=tmp_path/'d')['answer']=='24'

@pytest.mark.parametrize('value',['9','21','54','72','105','1.5'])
def test_equivalent_method_checked_on_distinct_new_numbers(tmp_path,value):
    st=learn.Store(tmp_path/'d/g4');st.add(spec(),{'fixture':True});st.add(spec(T.replace('30','45'),True),{'fixture':True})
    from fractions import Fraction
    r=api.solve(T.replace('30',value),llm='off',data=tmp_path/'d')
    assert Fraction(r['answer'])==(Fraction(value)+12)/3 and r['reason'] is None

@pytest.mark.parametrize('change',['sign','unit','type','goal','span'])
def test_different_meaning_is_not_consolidated(change):
    a=learn.template(spec());b=copy.deepcopy(a)
    if change=='sign':b['reading']['facts'][3]['eq']='factor * number + twelve = result'
    if change=='unit':b['reading']['quantities'][0]['unit']='km'
    if change=='type':b['reading']['quantities'][0]['integer']=True
    if change=='goal':b['reading']['ask']='result'
    if change=='span':b['reading']['facts'][3]['span']='the result is {#2}'
    assert not methods.equivalent(a,b)

def test_unsupported_symbolic_method_keeps_exact_comparison():
    a=learn.template(spec());a['reading']['facts'][3]['eq']='number = max(result,twelve)'
    b=copy.deepcopy(a);b['reading']['facts'][3]['eq']='number = max(twelve,result)'
    assert '"scope": "exact"' in methods.signature(a) and not methods.equivalent(a,b)

def test_unused_number_change_requires_new_reading(tmp_path):
    text='In 2025, '+T;r=spec(text);r['unused']=[{'raw':'2025','why':'year context, not a bound quantity'}]
    st=learn.Store(tmp_path/'d/g4');st.add(r,{'fixture':True})
    assert api.solve(text.replace('30','60'),llm='off',data=tmp_path/'d')['answer']=='24'
    assert api.solve(text.replace('2025','2026'),llm='off',data=tmp_path/'d')['answer'] is None

def test_legacy_template_gets_transfer_guards_from_its_own_example():
    text='In 2025, '+T;r=spec(text);r['unused']=[{'raw':'2025','why':'year context'}]
    old=learn.template(r);old.pop('numeric_roles');old.pop('unused_guards');old['example']=text
    assert learn.instantiate(old,text.replace('30','60'))
    assert learn.instantiate(old,text.replace('2025','2026')) is None

def test_numeric_role_change_is_not_an_amount_transfer():
    text='In 2025, '+T;r=spec(text);r['unused']=[{'raw':'2025','why':'year context'}]
    tpl=learn.template(r)
    # Percent tokens are one token too; their role must survive skeleton matching.
    assert learn.instantiate(tpl,text.replace('2025','2025%')) is None

def test_two_example_study_accepts_equivalent_teacher_forms(tmp_path,clean):
    d=tmp_path/'individual';run(d,'init');clean.setattr(llm,'parents',lambda:['chatgpt'])
    def transport(kind,system,user,**kw):
        q=user.removeprefix('Text: ');r=spec(q,alternate='45.' in q)
        return {'ok':True,'text':json.dumps({'readable':True,**r}),'model':'fixture','replayed':True}
    clean.setattr(llm,'call',transport)
    r=study.study(d,[T,T.replace('30','45')])
    assert len(r['adopted_templates'])==1
    assert api.solve(T.replace('30','60'),llm='off',data=d)['answer']=='24'
    assert run(d,'whole-audit')['ok']

def test_clarification_cli_resumes_same_goal(tmp_path):
    d=tmp_path/'individual';run(d,'init')
    r=run(d,'clarify-start','制約: A+B=18。Aは何？')
    assert r['uncertain'] and r['information_requests'] and r['conditions_invented'] is False
    r=run(d,'clarify-add','B=2*A')
    assert r['answer']=='6' and r['verified'] and r['conditional_on_supplied_premises']
    assert run(d,'clarify-status')['answer']=='6' and run(d,'clarify-audit')['answered']==1
    assert run(d,'whole-audit')['ok']

@pytest.mark.parametrize('query,conditions,answer',[
    ('制約: A+B+C=27。Aは何？',['A=B','C=9'],'9'),
    ('constraints: x+y=11; goal: x',['x-y=3'],'7'),
    ('AとBの合計は18個です。Aは何個？',['BはAの2倍です'],'6'),
    ('AとBの平均は10人です。Aは何人？',['AはBより4人多いです'],'12'),
])
def test_clarification_does_not_guess_missing_conditions(tmp_path,query,conditions,answer):
    d=tmp_path/'individual';run(d,'init');r=clarify.start(d,query)
    assert r['answer'] is None
    for c in conditions:r=clarify.add(d,c)
    assert r['answer']==answer and clarify.audit(d)['ok']

@pytest.mark.parametrize('condition',['A=99','C=1;goal: C','__import__("os")=1','A=B*B'])
def test_bad_condition_cannot_change_accepted_conversation(tmp_path,condition):
    d=tmp_path/'individual';run(d,'init');clarify.start(d,'制約: A+B=18。B=12。Aは何？')
    before=fingerprint(d)
    with pytest.raises(ValueError):clarify.add(d,condition)
    assert fingerprint(d)==before and clarify.status(d)['answer']=='6'

def test_clarification_round_bound_preserves_goal(tmp_path):
    d=tmp_path/'individual';run(d,'init');clarify.start(d,'制約: A+B=18。Aは何？')
    for _ in range(8):clarify.add(d,'A+B=18')
    with pytest.raises(ValueError,match='ROUND_BOUND'):clarify.add(d,'B=12')
    assert clarify.status(d)['answer'] is None

def test_clarification_partial_rollback_is_rejected(tmp_path):
    d=tmp_path/'individual';run(d,'init');clarify.start(d,'制約: A+B=18。Aは何？')
    old={p.relative_to(d/clarify.NS):p.read_bytes() for p in (d/clarify.NS).rglob('*') if p.is_file()}
    clarify.add(d,'B=12')
    for p in (d/clarify.NS).rglob('*'):
        if p.is_file():p.unlink()
    for n,b in old.items():p=d/clarify.NS/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    with pytest.raises(ValueError,match='RECOVERY_HEAD'):clarify.load(d)
    assert not run(d,'whole-audit',ok=False)['ok']

def test_clarification_tamper_and_missing_cache(tmp_path):
    d=tmp_path/'individual';run(d,'init');clarify.start(d,'制約: A+B=18。Aは何？');clarify.add(d,'B=12')
    p=d/clarify.NS/'STATE.json';original=p.read_bytes();p.unlink()
    assert clarify.status(d)['answer']=='6' and p.read_bytes()==original
    o=json.loads(original);o['state']['sessions']['main']['result']['answer']='7';p.write_text(json.dumps(o))
    assert not clarify.audit(d)['ok'] and not run(d,'whole-audit',ok=False)['ok']

def test_clarification_checkpoint_restores_original_question(tmp_path):
    d=tmp_path/'individual';run(d,'init');run(d,'realtime-start')
    clarify.start(d,'制約: A+B=18。Aは何？');baseline=clarify.load(d)
    cp=run(d,'recovery-checkpoint','--note','clarification baseline')['path']
    for _ in range(3):
        clarify.add(d,'B=12');assert clarify.status(d)['answer']=='6'
        run(d,'recovery-restore',cp,'--trust-file',d/'v1014/recovery.pub')
        assert clarify.load(d)==baseline and clarify.status(d)['answer'] is None
        assert run(d,'whole-audit')['ok']

def test_uncertainty_is_checked_without_producer_parser(monkeypatch):
    q='制約: A+B=18。Aは何？';r=clarify._checked(q);p=r['ambiguity_proof']
    assert r['ambiguity_check']['target_values']==['18','17']
    def forbidden(*args,**kwargs):raise AssertionError('producer used by ambiguity checker')
    monkeypatch.setattr(constraints,'parse',forbidden);monkeypatch.setattr(constraints,'solve',forbidden)
    assert verify_nonunique(q,p)['supported']

@pytest.mark.parametrize('damage',['target','assignment','graph','identical'])
def test_ambiguity_certificate_rejects_false_examples(damage):
    q='制約: A+B=18。Aは何？';p=copy.deepcopy(clarify._checked(q)['ambiguity_proof'])
    if damage=='target':p['witnesses'][1]['target_value']='999'
    if damage=='assignment':p['witnesses'][1]['assignment']['A']='999'
    if damage=='graph':p['graph']['equations'][0]['rhs']='999'
    if damage=='identical':p['witnesses'][1]=copy.deepcopy(p['witnesses'][0])
    assert not verify_nonunique(q,p)['supported']

def test_impossible_count_is_not_explained_as_missing_condition(tmp_path):
    d=tmp_path/'individual';run(d,'init');before=fingerprint(d)
    with pytest.raises(ValueError,match='NEGATIVE_QUANTITY'):clarify.start(d,'AとBの合計は-18個です。Aは何個？')
    assert fingerprint(d)==before
