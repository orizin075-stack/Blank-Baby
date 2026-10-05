import json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/'run_tukuyo.py'

def run(data,*args,ok=True):
    p=subprocess.run([sys.executable,'-B',str(CLI),'--data',str(data),*map(str,args)],cwd=ROOT,text=True,capture_output=True)
    if ok and p.returncode!=0: raise AssertionError(p.stdout+p.stderr)
    return json.loads(p.stdout)

def test_heart_loop_restart_and_choice_shift():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V978-H')
        opts=Path(td)/'opts.json';opts.write_text(json.dumps([
          {'id':'explore','signals':{'curiosity':0.9,'integrity':0.1,'threat':0.2},'themes':['unknown_lab']},
          {'id':'secure','signals':{'curiosity':0.1,'integrity':0.9,'survival':0.8,'threat':-0.1},'themes':['preserve_truth']}
        ]),encoding='utf-8')
        before=run(d,'heart-choose',opts,'--context','unknown')
        run(d,'heart-experience','betrayal','-1','1','--theme','unknown_lab','--relation','peer-X')
        run(d,'heart-experience','vow','0.8','1','--theme','preserve_truth')
        after=run(d,'heart-choose',opts,'--context','unknown')
        assert before['chosen'] in ('explore','secure')
        assert after['chosen']=='secure'
        # New process is implicit in each CLI invocation; state persists.
        st=run(d,'heart-status');assert st['ok'] and st['individual_id']=='V978-H' and st['meaning_count']==2
        wa=run(d,'whole-audit');assert wa['ok']

def test_feedback_binding_and_event_chain():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V978-F')
        opts=Path(td)/'opts.json';opts.write_text(json.dumps([{'id':'a','signals':{'curiosity':1}},{'id':'b','signals':{'integrity':1}}]),encoding='utf-8')
        ch=run(d,'heart-choose',opts);bad=run(d,'heart-feedback','wrong','-1','1',ok=False);assert not bad['ok'] and 'HEART_FEEDBACK_ACTION_BINDING' in bad['error']
        good=run(d,'heart-feedback',ch['chosen'],'0.5','0.7','--theme','action_result');assert good['ok']
        assert run(d,'heart-audit')['ok']
