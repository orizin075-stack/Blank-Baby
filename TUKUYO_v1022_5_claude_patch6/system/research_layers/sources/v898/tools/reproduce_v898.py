#!/usr/bin/env python3
import json,sys
from pathlib import Path
r=Path(__file__).parents[1];sys.path.insert(0,str(r));from tukuyo_v898.experiment import generate
a,b=generate(json.load(open(r/'evidence/SUITE_SPECS.json')));json.dump(a,open(r/'evidence/V898_RAW_EPISODES.json','w'),indent=2,sort_keys=True);open(r/'evidence/V898_RAW_EPISODES.json','a').write('\n');json.dump(b,open(r/'evidence/V898_SUMMARY.json','w'),indent=2,sort_keys=True);open(r/'evidence/V898_SUMMARY.json','a').write('\n')
