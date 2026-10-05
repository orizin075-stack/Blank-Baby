#!/usr/bin/env python3
import json,sys
from pathlib import Path
r=Path(__file__).parents[1];sys.path.insert(0,str(r));from tukuyo_v896.experiment import generate
a,b,c=generate(json.load(open(r/'evidence/SUITE_SPECS.json')))
for n,o in [('V896_RAW_EPISODES.json',a),('V896_SUITE_RESULTS.json',b),('V896_SUMMARY.json',c)]:json.dump(o,open(r/'evidence'/n,'w'),indent=2,sort_keys=True);open(r/'evidence'/n,'a').write('\n')
