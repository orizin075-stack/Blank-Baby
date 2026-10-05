import json,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tukuyo_v914.patcher import evaluate,source_sha
from tukuyo_v914.security import inspect_source
src=pathlib.Path(sys.argv[1]).read_text();sec=inspect_source(src)
if not sec['ok']: print(json.dumps({'ok':False,'reason':sec['reason'],'bad':sec['bad']}));raise SystemExit(2)
r=evaluate(src,91499,700);print(json.dumps({'ok':r['wrong']==0,'correct':r['correct'],'wrong':r['wrong'],'n':r['n'],'candidate_sha256':source_sha(src)},sort_keys=True));raise SystemExit(0 if r['wrong']==0 else 1)
