import json,hashlib,pathlib,re

def H(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def audit(root):
    r=pathlib.Path(root); st=json.loads((r/'STATUS.json').read_text()); rec=json.loads((r/'evidence/CLAIM_BINDING_RECEIPT.json').read_text())['payload']
    bad=[]; binds=rec.get('artifact_bindings',{})
    for rel,h in binds.items():
        if not (r/rel).is_file() or H(r/rel)!=h: bad.append('BINDING:'+rel)
    for claim in st.get('claims',[]):
        for rel in claim.get('artifacts',[]):
            if rel not in binds: bad.append('UNBOUND_CLAIM_ARTIFACT:'+rel)
    for rel in rec.get('named_implementation_artifacts',[]):
        if rel not in binds: bad.append('NAMED_IMPLEMENTATION_UNBOUND:'+rel)
    if not any(x.endswith('.py') for x in binds): bad.append('NO_IMPLEMENTATION_SHA')
    return bad
