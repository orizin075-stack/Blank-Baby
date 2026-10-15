#!/usr/bin/env python3
"""Standalone signature/prefix verifier. No TUKUYO runtime imports or writes."""
import argparse,base64,hashlib,json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
def canon(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(o):return hashlib.sha256(canon(o)).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def verify_env(env,pub):
    if set(env)!={'payload','public_key','signature'} or env['public_key']!=pub:raise ValueError('SIGNER')
    Ed25519PublicKey.from_public_bytes(base64.b64decode(pub,validate=True)).verify(base64.b64decode(env['signature'],validate=True),canon(env['payload']))
    return env['payload']
def verify(path,trust,data=None):
    try:
        p=Path(path);pub=Path(trust).read_text().strip();reg=verify_env(read(p/'REGISTRY.json'),pub)
        if reg.get('schema')!='tukuyo.identity_ledger.registry/1':raise ValueError('REGISTRY')
        raw=(p/'JOURNAL.jsonl').read_bytes()
        if raw and not raw.endswith(b'\n'):raise ValueError('TRUNCATED')
        rows=[json.loads(line) for line in raw.splitlines()];previous='0'*64;latest={};names={};keys={}
        for i,env in enumerate(rows,1):
            q=verify_env(env,pub);s=q['snapshot'];proof=verify_env(s['local_proof'],s['whole_public_key']);key=sha({'identity':s['identity'],'whole_public_key':s['whole_public_key']})
            if q.get('schema')!='tukuyo.identity_ledger.event/1' or q.get('ledger_id')!=reg['ledger_id'] or q.get('seq')!=i or q.get('previous')!=previous or q.get('identity_key')!=key:raise ValueError('CHAIN')
            if proof['identity']!=s['identity'] or sha(s['local_proof'])!=s['whole_head_sha256']:raise ValueError('WHOLE_BINDING')
            if s['global_unique_individual_proven'] is not False:raise ValueError('CLAIM_BOUNDARY')
            old=latest.get(key)
            if q['kind'] in ('ENROLL','BRANCH'):
                if old or s['identity']['individual_id'] in names or s['whole_public_key'] in keys:raise ValueError('DUPLICATE_REGISTRATION')
                names[s['identity']['individual_id']]=key;keys[s['whole_public_key']]=key
            elif q['kind'] not in ('ADVANCE','DEATH') or old is None:raise ValueError('OPERATION')
            if old:
                a=old['payload']['snapshot'];heads=a['soul_heads']
                if s['soul_heads'][:len(heads)]!=heads:raise ValueError('HISTORY_FORK')
                if a['lifecycle']=='DEAD' and s['lifecycle']!='DEAD':raise ValueError('DEATH_REVERSED')
            if q['kind']=='DEATH' and s['lifecycle']!='DEAD':raise ValueError('DEATH_MARKER')
            if q['kind']=='BRANCH':
                ds=q['branch_declarations'];c=verify_env(ds['child'],s['whole_public_key']);parent=next((e for e in rows[:i-1] if sha(e)==c['parent_receipt_sha256']),None)
                if parent is None:raise ValueError('BRANCH_PARENT')
                ps=parent['payload']['snapshot'];other=verify_env(ds['parent'],ps['whole_public_key'])
                if c.get('schema')!='tukuyo.identity_ledger.branch/1' or latest.get(parent['payload']['identity_key'])!=parent or c.get('private_autobiography_transferred_by_registration') is not False or c.get('runtime_generated_by_this_registration') is not False or c!=other or c['child_identity']!=s['identity'] or c['child_whole_public_key']!=s['whole_public_key'] or ps['identity']['individual_id']==s['identity']['individual_id'] or ps['whole_public_key']==s['whole_public_key'] or ps['lifecycle']=='DEAD':raise ValueError('BRANCH_BINDING')
            latest[key]=env;previous=sha(env)
        head=verify_env(read(p/'HEAD.json'),pub)
        if head!={'schema':'tukuyo.identity_ledger.head/1','ledger_id':reg['ledger_id'],'seq':len(rows),'head_sha256':previous}:raise ValueError('HEAD')
        if (p/'PREPARED.json').exists():raise ValueError('PENDING_RECOVERY_REQUIRED')
        if data:
            d=Path(data);b=read(d/'identity_ledger/BINDING.json');binding=verify_env(b,pub);local=read(d/'v977/UNIFIED_STATE.json');lp=verify_env(local,binding['whole_public_key']);key=sha({'identity':binding['identity'],'whole_public_key':binding['whole_public_key']});expected=latest.get(key)
            if binding['ledger_id']!=reg['ledger_id'] or lp['identity']!=binding['identity'] or not expected:raise ValueError('LOCAL_IDENTITY')
            if read(d/'identity_ledger/RECEIPT.json')!=expected or sha(local)!=expected['payload']['snapshot']['whole_head_sha256']:raise ValueError('LOCAL_STALE_OR_FORKED')
            if hashlib.sha256((d/'identity_ledger/BINDING.json').read_bytes()).hexdigest()!=lp['component_hashes']['external_identity_binding']:raise ValueError('LOCAL_BINDING_COMPONENT')
        return {'ok':True,'events':len(rows),'identities':len(latest),'pending':False,'raw_signatures_and_prefixes_checked':True,'physical_uniqueness_proven':False,'independent_real_world_witness_proven':False,'literal_soul_proven':False}
    except Exception as e:return {'ok':False,'errors':[type(e).__name__+':'+str(e)],'physical_uniqueness_proven':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--ledger',type=Path,required=True);p.add_argument('--trust-file',type=Path,required=True);p.add_argument('--data',type=Path);a=p.parse_args();r=verify(a.ledger,a.trust_file,a.data);print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(0 if r['ok'] else 1)
