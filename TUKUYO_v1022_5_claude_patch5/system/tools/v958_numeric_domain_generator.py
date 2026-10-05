#!/usr/bin/env python3
from pathlib import Path
import argparse,json,random

def main():
 p=argparse.ArgumentParser();p.add_argument('--seed',type=int,required=True);p.add_argument('--n',type=int,default=48);p.add_argument('--out',type=Path,required=True);a=p.parse_args();rng=random.Random(a.seed);seen=set();recs=[]
 while len(recs)<a.n:
  x=rng.randint(-200,200);y=rng.randint(-30,30)
  if (x,y) in seen:continue
  seen.add((x,y));recs.append({'a':x,'b':y,'expected':x//3+y})
 obj={'schema':'tukuyo.v958.numeric_holdout/1','generator_id':'numeric_holdout_v958','seed':a.seed,'records':recs};a.out.write_text(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n')
if __name__=='__main__':main()
