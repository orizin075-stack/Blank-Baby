import json,pathlib,sys
req=json.loads(pathlib.Path('evidence/REPRODUCTION_CONTRACT.json').read_text());ok=req['release_authority_must_not_sign_external_receipt'] and len(req['canonical_track_sha256'])==2;print(json.dumps({'ok':ok,'ready_for_external_inputs':True,'external_run_completed':False},sort_keys=True));raise SystemExit(0 if ok else 1)
