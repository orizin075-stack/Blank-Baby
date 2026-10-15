import json,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tukuyo_v915.patcher import *
variants={'base':BASE_SOURCE,'threshold':apply(BASE_SOURCE,'threshold'),'precedence':apply(BASE_SOURCE,'precedence'),'audit':apply(BASE_SOURCE,'audit')}
full=apply(apply(apply(BASE_SOURCE,'threshold'),'precedence'),'audit');variants['full']=full
out={}
for name,src in variants.items():
 vals=[evaluate(src,s,500)['correct'] for s in (91511,91522,91533,91544,91555)]
 out[name]={'correct_total':sum(vals),'mean':sum(vals)/len(vals),'source_sha256':source_sha(src)}
out['full_strictly_beats_each_single']=all(out['full']['correct_total']>out[k]['correct_total'] for k in ('base','threshold','precedence','audit'))
print(json.dumps(out,sort_keys=True))
