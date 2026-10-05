import argparse,json,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tukuyo_v911.admit import admit
p=argparse.ArgumentParser();p.add_argument('path');p.add_argument('--track',required=True);a=p.parse_args();r=admit(a.path,a.track);print(json.dumps(r,sort_keys=True));raise SystemExit(0 if r['ok'] else 1)
