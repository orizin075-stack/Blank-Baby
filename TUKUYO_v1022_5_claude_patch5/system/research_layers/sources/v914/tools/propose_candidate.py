import json,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tukuyo_v914.patcher import BASE_SOURCE,apply,proposed_patch
summary=json.loads(pathlib.Path(sys.argv[1]).read_text());src=BASE_SOURCE;ap=[]
for _ in range(3):
 k=proposed_patch(summary,ap);ap.append(k);src=apply(src,k)
 # diagnostics are intentionally fixed public input; hidden rows are never read here.
 summary={'failures':{k:0 for k in summary['failures']}}
pathlib.Path(sys.argv[2]).write_text(src);print(json.dumps({'patches':ap}))
