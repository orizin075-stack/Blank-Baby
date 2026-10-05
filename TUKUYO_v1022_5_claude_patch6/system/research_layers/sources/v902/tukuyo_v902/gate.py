def assay(row):
    return row['predicted']==row['truth'] and row.get('evidence_bound',False)
def run(cases):
    return [{'id':c['id'],'detected':(assay(c)==c['should_pass'])} for c in cases]
def gate(cases):
    out=run(cases); sabotage=[c for c in cases if c.get('sabotage')]
    if not sabotage:return False,out
    return all(x['detected'] for x in out),out
