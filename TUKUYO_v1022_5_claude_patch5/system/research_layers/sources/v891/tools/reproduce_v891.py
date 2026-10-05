#!/usr/bin/env python3
import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(root)); from tukuyo_v891.experiment import generate
s=json.load(open(root/'evidence/SUITE_SPECS.json')); a,b,c=generate(s)
for n,o in [('V891_RAW_EPISODES.json',a),('V891_SUITE_RESULTS.json',b),('V891_SUMMARY.json',c)]: json.dump(o,open(root/'evidence'/n,'w'),indent=2,sort_keys=True); open(root/'evidence'/n,'a').write('\n')
