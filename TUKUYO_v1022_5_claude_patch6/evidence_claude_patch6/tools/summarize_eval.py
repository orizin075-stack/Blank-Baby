"""markdown tables for README from final_eval_F_T_CDE.json"""
import json,sys,collections
d=json.load(open(sys.argv[1]))
S=d['summary'];rows=[r for r in d['rows'] if not r.get('audit_row')]
P5CDE={('C','think'):(69,0,24),('C','verified-query'):(69,0,24),('C','llm-ask'):(73,0,20),('D','think'):(42,0,8),('D','verified-query'):(42,0,8),('D','llm-ask'):(42,0,8),
       ('E','think'):(32,0,4),('E','verified-query'):(32,0,4),('E','llm-ask'):(32,0,4)}
print('seconds',d['seconds'])
print('\n### F/T (held-out, once)\n')
print('| セット | コマンド | patch5 正答 | patch5 確信を持った誤り | patch6 正答 | patch6 確信を持った誤り | patch6 答えなかった |')
print('|---|---|---|---|---|---|---|')
for s in 'FT':
    for c in ('think','verified-query','llm-ask'):
        a=S[f'{s}|patch5|{c}'];b=S[f'{s}|patch6|{c}']
        print(f"| {s}（{a['n']} 問） | `{c}` | {a['correct']} | {a['wrong_certain']} | **{b['correct']}** | **{b['wrong_certain']}** | {b['abstained']} |")
print('\n### per category (think)\n')
for s in 'FT':
    cats=sorted({r['set'] for r in rows if r['split']==s})
    print(f'| {s} の型 | 問題数 | patch5 正答 | patch6 正答 | patch6 誤り |');print('|---|---|---|---|---|')
    for cat in cats:
        p5=[r for r in rows if r['split']==s and r['set']==cat and r['version']=='patch5' and r['cmd']=='think']
        p6=[r for r in rows if r['split']==s and r['set']==cat and r['version']=='patch6' and r['cmd']=='think']
        print(f"| {cat} | {len(p6)} | {sum(r['correct'] for r in p5)} | {sum(r['correct'] for r in p6)} | {sum(r['wrong_certain'] for r in p6)} |")
    print()
print('\n### C/D/E (patch6) vs patch5 published\n')
print('| セット | コマンド | patch5 正答（誤り） | patch6 正答（誤り） |');print('|---|---|---|---|')
for s in 'CDE':
    for c in ('think','verified-query','llm-ask'):
        b=S[f'{s}|patch6|{c}'];p=P5CDE[(s,c)]
        print(f"| {s}（{b['n']} 問） | `{c}` | {p[0]}（{p[1]}） | **{b['correct']}**（{b['wrong_certain']}） |")
print('\n### Parser B AGREE among gated commits (think)\n')
print('| セット | patch5 | patch6 |');print('|---|---|---|')
for s in 'FTCDE':
    out=[]
    for v in ('patch5','patch6'):
        k=f'{s}|{v}|think'
        if k in S:out.append(f"{S[k]['parser_b_agree']}/{S[k]['gated_commits']}")
        else:out.append('–')
    print(f'| {s} | {out[0]} | {out[1]} |')
print('\n### wrong-certain rows\n')
for r in rows:
    if r['wrong_certain']:print(r['version'],r['cmd'],r['split'],r['set'],r['q'],'->',r['answer'],'expected',r['expected'])
print('\n### patch6 think abstentions on F/T\n')
for r in rows:
    if r['version']=='patch6' and r['cmd']=='think' and r['split'] in 'FT' and r['abstained']:print(r['split'],r['set'],r['q'],'expected',r['expected'])
print('\n### whole-audit after each run\n',{k:v['whole_audit_after'] for k,v in S.items()})
print('errors',{k:v['errors'] for k,v in S.items() if v['errors']})
