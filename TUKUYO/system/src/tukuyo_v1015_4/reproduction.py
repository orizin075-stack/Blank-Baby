from __future__ import annotations
import base64, hashlib, json, time
from pathlib import Path
from tukuyo_common.atomic_fs import atomic_write_bytes
from tukuyo_v977.whole_state import canon, sha_obj
from tukuyo_v1015_3 import endurance_resume as resume
from tukuyo_v1015_2 import endurance_execution as execution

VERSION='v1015.4'
SCHEMA='tukuyo.v1015_4.portable_reproduction_bundle/1'

def _read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def _raw_b64(p): return base64.b64encode(Path(p).read_bytes()).decode('ascii')
def _events(d):
    out=[]
    p=Path(d)
    if not p.is_dir(): return out
    for f in sorted(p.glob('*.json')):
        out.append(_read(f))
    return out

def _success_evidence(data, state):
    p=state.get('evidence_bundle')
    if p and Path(p).is_file(): return _read(p)
    cand=sorted((Path(data)/'v1015_2'/'evidence').glob('*_authenticated_endurance.json'))
    if not cand: raise ValueError('SUCCESS_EVIDENCE_MISSING')
    return _read(cand[-1])

def export_bundle(data,out,witness_trust_file):
    data=Path(data); out=Path(out); witness_trust_file=Path(witness_trust_file)
    if not witness_trust_file.is_file(): raise ValueError('WITNESS_TRUST_FILE_MISSING')
    rs=_read(resume.state_path(data)); es=_read(execution.state_path(data))
    terminal=rs.get('terminal_state')
    if terminal not in ('SUCCEEDED','FAILED'): raise ValueError('TERMINAL_STATE_REQUIRED')
    if terminal=='SUCCEEDED':
        source=_success_evidence(data,es); kind='SUCCESS'
    else:
        fp=rs.get('failure_evidence') or str(resume.failure_path(data))
        if not Path(fp).is_file(): raise ValueError('FAILURE_EVIDENCE_MISSING')
        source=_read(fp); kind='FAILURE'
    root=Path(__file__).resolve().parents[2]
    mp=root/'META'/'RELEASE_MANIFEST.json'; rp=root/'META'/'RELEASE_RECEIPT.json'
    obj={
      'schema':SCHEMA,'version':VERSION,'outcome':kind,'generated_utc_ns':time.time_ns(),
      'release_manifest_bytes_b64':_raw_b64(mp),'release_receipt_bytes_b64':_raw_b64(rp),
      'release_binding':rs.get('release_binding'),
      'resume_state':rs,'resume_events':_events(resume.events_dir(data)),
      'execution_state':es,'execution_events':_events(execution.events_dir(data)),
      'source_evidence':source,
      'witness_public_key':witness_trust_file.read_text(encoding='utf-8').strip(),
      'claim_boundary':{
        'portable_no_data_root_required':True,
        'copied_audit_flags_are_non_authoritative':True,
        'external_publisher_trust_required':True,
        'external_witness_trust_required':True,
        'third_party_human_reproduction_completed':False,
      },
    }
    obj['bundle_sha256']=sha_obj(obj)
    out.parent.mkdir(parents=True,exist_ok=True); atomic_write_bytes(out,canon(obj)+b'\n')
    return {'ok':True,'version':VERSION,'outcome':kind,'path':str(out),'bundle_sha256':obj['bundle_sha256']}
