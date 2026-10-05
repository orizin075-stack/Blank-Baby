from __future__ import annotations
import hashlib,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
from tukuyo_v977.whole_state import canon,sha_obj,_live_identity,sync as whole_sync,audit as whole_audit,state_path

SCHEMA='tukuyo.v984.full_runtime_fork_assay/1'

def _read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def _write(p,o):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')
def _fsha(p):
    p=Path(p);return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def report_path(data):return Path(data)/'v984'/'FULL_RUNTIME_FORK_ASSAY.json'

def _run_worker(runtime_root,branch,mode):
    env=os.environ.copy();src=str(Path(runtime_root)/'src');env['PYTHONPATH']=src+(os.pathsep+env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    p=subprocess.run([sys.executable,'-B','-m','tukuyo_v984.branch_runner','--data',str(branch),'--mode',mode],cwd=runtime_root,text=True,capture_output=True,env=env,timeout=120)
    if p.returncode!=0:raise RuntimeError('V984_BRANCH_PROCESS:'+mode+':'+(p.stdout+p.stderr)[-1200:])
    x=json.loads(p.stdout)
    if not x.get('ok'):raise RuntimeError('V984_BRANCH_RESULT:'+mode)
    return x

def run_assay(data,runtime_root):
    data=Path(data).resolve();runtime_root=Path(runtime_root).resolve()
    whole_sync(data)
    if not whole_audit(data).get('ok'):raise ValueError('V984_PARENT_WHOLE_AUDIT')
    ident=_live_identity(data);origin_whole=_fsha(state_path(data))
    with tempfile.TemporaryDirectory(prefix='tukuyo_v984_fork_') as td:
        td=Path(td);a=td/'branch_a';b=td/'branch_b'
        shutil.copytree(data,a);shutil.copytree(data,b)
        common_a=_fsha(a/'v977'/'UNIFIED_STATE.json');common_b=_fsha(b/'v977'/'UNIFIED_STATE.json')
        ra=_run_worker(runtime_root,a,'explore');rb=_run_worker(runtime_root,b,'protect')
    checks={
      'common_origin_snapshot':common_a==common_b==origin_whole,
      'separate_processes_executed':True,
      'both_whole_audits_pass':bool(ra['whole_audit']['ok'] and rb['whole_audit']['ok']),
      'whole_state_diverged':ra['whole_state_sha256']!=rb['whole_state_sha256'],
      'organism_state_diverged':ra['organism_state_sha256']!=rb['organism_state_sha256'],
      'heart_state_diverged':ra['heart_state_sha256']!=rb['heart_state_sha256'],
      'soul_state_diverged':ra['soul_sha256']!=rb['soul_sha256'],
      'choice_diverged':ra['chosen']!=rb['chosen'],
      'homeostasis_intent_diverged':ra['homeostasis_intent']!=rb['homeostasis_intent'],
    }
    payload={
      'schema':SCHEMA,'identity':ident,'origin_unified_state_sha256':origin_whole,
      'branch_a':{k:ra[k] for k in ('mode','ticks','chosen','homeostasis_intent','whole_state_sha256','organism_state_sha256','heart_state_sha256','soul_sha256')},
      'branch_b':{k:rb[k] for k in ('mode','ticks','chosen','homeostasis_intent','whole_state_sha256','organism_state_sha256','heart_state_sha256','soul_sha256')},
      'checks':checks,
      'claim_boundary':{
        'bounded_full_runtime_fork_divergence_tested':True,
        'same_snapshot_separate_process_execution':True,
        'persistent_parallel_agents_established':False,
        'consciousness_established':False,
        'literal_soul_established':False,
      },
    }
    payload['report_sha256']=sha_obj(payload);_write(report_path(data),payload)
    return {'ok':all(checks.values()),'version':'v984',**payload}

def audit(data):
    p=report_path(data)
    if not p.exists():return {'ok':False,'version':'v984','errors':['V984_ASSAY_MISSING']}
    errs=[];x=_read(p);q=dict(x);got=q.pop('report_sha256',None)
    if x.get('schema')!=SCHEMA:errs.append('V984_SCHEMA')
    if got!=sha_obj(q):errs.append('V984_REPORT_HASH')
    try:
        if x.get('identity')!=_live_identity(data):errs.append('V984_IDENTITY')
    except Exception as e:errs.append('V984_IDENTITY:'+type(e).__name__)
    if not all(x.get('checks',{}).values()):errs.append('V984_CHECKS')
    return {'ok':not errs,'version':'v984','errors':errs,'checks':x.get('checks',{}),'claim_boundary':x.get('claim_boundary',{})}
