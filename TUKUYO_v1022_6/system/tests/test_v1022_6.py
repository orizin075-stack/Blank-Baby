"""v1022.6 release identity: the CLI reports the revision recorded in the signed release receipt (so a re-sign
with --revision relabels the release without code changes), the version status file keeps its claim
boundaries, and the lineage keeps every earlier seed key acceptable for existing individuals."""
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py'

def test_v1022_6_release_identity(tmp_path):
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    for k in ('TUKUYO_LLM_PROVIDER','TUKUYO_LLM_COMMAND','TUKUYO_LLM_TEACHERS'):env.pop(k,None)
    cmd=[sys.executable,'-B',str(CLI)];anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if anchor:cmd+=['--runtime-trust-file',anchor]
    p=subprocess.run(cmd+['--data',str(tmp_path/'d'),'init'],cwd=ROOT,env=env,capture_output=True,text=True,timeout=240);r=json.loads(p.stdout)
    receipt=json.loads((ROOT/'META/RELEASE_RECEIPT.json').read_text(encoding='utf-8'))
    assert r['ok'] and r['release_revision']==receipt['payload']['release_revision'],(r.get('release_revision'),receipt['payload'])
    assert r['release_revision'].startswith('v1022.6')
    st=json.loads((ROOT/'STATUS_V1022_6.json').read_text(encoding='utf-8'))
    assert st['release_revision']=='v1022.6' and st['base']=='v1022.5-fusion' and st['runtime_llm_required'] is False
    assert not any(st[k] for k in ('invents_new_kinds_of_laws','24h_completed','general_intelligence_established','self_code_modification',
                                   'consciousness_established','third_party_heldout_evaluation'))
    lin=json.loads((ROOT/'META/PATCH_LINEAGE_v1022_6.json').read_text(encoding='utf-8'))
    assert {'22jzm2l8ZiBxLF0QvN5IpCcq0NQEdPwcNodO/Ey83zA=','FZbc4ewE8BB6Br/RfDYneVhKNXt8MfRaEzocWoMlkyk='}<=set(lin['accepted_seed_public_keys'])
