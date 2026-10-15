"""generation 4 core: number finding, the formal problem language, the exact solver, the separately written checker,
the prompt examples, and the arbitration between readings (offline, with recorded replies)."""
import copy,json,os,sys
from fractions import Fraction
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tukuyo_g4 import numbers as N,llm,api
from tukuyo_g4.solve import solve
from tukuyo_g4.check import check

DUCKS='ジャネットのアヒルは1日に16個の卵を生みます。ジャネットは毎朝朝食の一環で3個を消費し、毎日4個使って友達向けにマフィンを焼きます。残りを市場で1個あたり2ドルの価格で売ります。彼女は毎日市場でいくら手に入れていますか？'
def ducks():
    return {'schema':'tukuyo.g4.fpl/1','lang':'ja','text':DUCKS,
     'quantities':[{'name':n,'unit':u,'integer':i} for n,u,i in [('laid','egg/day',1),('eaten','egg/day',1),('baked','egg/day',1),('left','egg/day',1),('price','dollar/egg',0),('income','dollar/day',0)]],
     'facts':[{'eq':'laid = 16','span':'1日に16個の卵を生みます'},{'eq':'eaten = 3','span':'3個を消費し'},{'eq':'baked = 4','span':'毎日4個使って'},
              {'eq':'left = laid - eaten - baked','span':'残りを'},{'eq':'price = 2','span':'1個あたり2ドル'},{'eq':'income = left * price','span':'残りを市場で1個あたり2ドルの価格で売ります'}],
     'ask':'income','unused':[]}

def vals(t):return [(str(n.value),n.kind) for n in N.find(t)]

def test_numbers_japanese_and_english():
    assert vals('8万ドルで家を購入し、5万ドルかけて修繕。150%増加。')==[('80000','jbig'),('50000','jbig'),('150','percent')]
    assert vals('4分の3を食べた。6割引き。1万5千円。三十五人。二つ。一緒に。三角形。十分な時間')==[('3/4','jfrac'),('60','percent'),('15000','jbig'),('35','kanji'),('2','kanji')]
    assert vals('2時間半、その半分')==[('2','digits'),('1/2','half'),('1/2','half')]
    assert vals('one hundred and five, twenty-five, a dozen, two-thirds, one and a half, twice, the second day, 1,250 and 3/4')==[
        ('105','word'),('25','word'),('12','word'),('2/3','word'),('3/2','word'),('2','word'),('2','ordinal'),('1250','digits'),('3/4','digits')]

def test_solver_and_checker_accept_a_correct_reading():
    s=ducks();r=solve(s)
    assert r['ok'] and r['answer']==18
    c=check(s,r['values']);assert c['ok'] and c['answer']=='18',c['failures']

def test_checker_rejects_ungrounded_unbalanced_or_incomplete_readings():
    cases={'literal in a relation':(5,'income = left * 2','NUMBER_IN_RELATION'),'units':(5,'income = left + price','UNITS'),
           'number not in span':(4,'price = 3','NUMBER_NOT_IN_SPAN')}
    for name,(i,eq,fail) in cases.items():
        s=ducks();s['facts'][i]['eq']=eq;r=solve(s);assert r['ok'],name
        c=check(s,r['values']);assert not c['ok'] and any(f.startswith(fail) for f in c['failures']),(name,c['failures'])
    s=ducks();del s['facts'][2];s['facts'][2]['eq']='left = laid - eaten';s['quantities']=[q for q in s['quantities'] if q['name']!='baked']
    r=solve(s);c=check(s,r['values']);assert 'NUMBER_NOT_ACCOUNTED:4' in c['failures']
    s=ducks();s['facts'][3]['eq']='left = laid - eaten - baked - laid';assert solve(s)['reason'].startswith('NEGATIVE')
    s=ducks();del s['facts'][0];assert solve(s)['reason'].startswith('UNDERDETERMINED')

def test_systems_of_equations_and_uniqueness():
    t='兄は弟より3歳年上で、2人の年齢を合わせると21歳です。兄は何歳ですか？'
    s={'schema':'tukuyo.g4.fpl/1','lang':'ja','text':t,'quantities':[{'name':'older','unit':'歳','integer':True},{'name':'younger','unit':'歳','integer':True},{'name':'gap','unit':'歳'},{'name':'total','unit':'歳'}],
       'facts':[{'eq':'gap = 3','span':'弟より3歳年上'},{'eq':'older = younger + gap','span':'兄は弟より3歳年上'},{'eq':'total = 21','span':'合わせると21歳'},{'eq':'older + younger = total','span':'2人の年齢を合わせると'}],
       'ask':'older','unused':[{'raw':'2','why':'the two brothers'}]}
    r=solve(s);assert r['ok'] and r['answer']==12
    c=check(s,r['values']);assert c['ok'],c['failures']
    bad={**s,'facts':s['facts'][:3]};assert solve(bad)['reason'].startswith('UNDERDETERMINED')
    # the checker's own uniqueness test: values that satisfy the facts but are not forced by them are refused
    c=check(bad,{'older':12,'younger':9,'gap':3,'total':21});assert any(f.startswith('NOT_UNIQUE') for f in c['failures'])

def test_prompt_examples_pass_the_solver_and_the_checker():
    for view,exs in llm.EXAMPLES.items():
        for text,o in exs:
            s={'schema':'tukuyo.g4.fpl/1','lang':'x','text':text,'quantities':o['quantities'],'ask':o['ask'],'unused':o['unused'],
               'facts':[{'eq':f['eq'],**({'span':f['span']} if f['span'] else {}),**({'known':f['known']} if f['known'] else {})} for f in o['facts']]}
            r=solve(s);assert r['ok'],(view,text,r);c=check(s,r['values']);assert c['ok'],(view,text,c['failures'])

def test_llm_is_off_without_configuration_and_ignores_host_variables(monkeypatch):
    for k in ('TUKUYO_ANTHROPIC_API_KEY','TUKUYO_LLM_REPLAY'):monkeypatch.delenv(k,raising=False)
    monkeypatch.setenv('ANTHROPIC_API_KEY','host-key-must-not-be-used');monkeypatch.setenv('ANTHROPIC_BASE_URL','http://host-proxy.invalid')
    assert not llm.available() and llm.settings()['base_url']=='https://api.anthropic.com'
    assert llm.read('2+2は？')['reason']=='LLM_NOT_CONFIGURED'

def test_arbitration_commits_only_agreeing_verified_readings(tmp_path,monkeypatch):
    good={'readable':True,'quantities':[{'name':q['name'],'unit':q['unit'],'integer':bool(q['integer']),'signed':False,'about':''} for q in ducks()['quantities']],
          'facts':[{**f,'known':''} for f in ducks()['facts']],'ask':'income','answer_unit':'ドル','unused':[]}
    wrong=copy.deepcopy(good);wrong['facts'][3]['eq']='left = laid - eaten + baked'
    clash=copy.deepcopy(good);clash['facts'][5]['eq']='income = left + price'
    cases={'agree':(good,good),'disagree':(wrong,good),'single':(clash,good)}
    rec=tmp_path/'replay.jsonl';lines=[];texts={}
    for name,(a,b) in cases.items():
        t=DUCKS+'（'+name+'）';texts[name]=t
        for view,o in (('story',a),('goal',b)):
            h=llm.request_hash('read:'+view+':'+llm.PROMPT_VERSION,llm.system_prompt(view),'Text: '+t)
            lines.append(json.dumps({'hash':h,'ok':True,'text':json.dumps(o,ensure_ascii=False),'model':'fixture'},ensure_ascii=False))
    rec.write_text('\n'.join(lines)+'\n',encoding='utf-8');monkeypatch.setenv('TUKUYO_LLM_REPLAY',str(rec));llm._replay_cache.clear()
    monkeypatch.setattr(api,'_own',lambda text:None)
    r=api.solve(texts['agree']);assert (r['answer'],r['route'])==('18','llm+llm')
    r=api.solve(texts['disagree']);assert r['answer'] is None and r['reason']=='DISAGREE:18,34'
    r=api.solve(texts['single']);assert r['answer'] is None and r['reason']=='SINGLE_LLM_READING' and r['withheld']=='18'
    r=api.solve(DUCKS+'（not recorded）');assert r['answer'] is None and r['reason']=='NO_VERIFIED_READING'
