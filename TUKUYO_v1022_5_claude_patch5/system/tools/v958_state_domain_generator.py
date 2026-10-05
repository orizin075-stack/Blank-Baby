#!/usr/bin/env python3
from pathlib import Path
import argparse,json,random

def main():
 p=argparse.ArgumentParser();p.add_argument('--seed',type=int,required=True);p.add_argument('--n',type=int,default=48);p.add_argument('--out',type=Path,required=True);a=p.parse_args();rng=random.Random(a.seed);recs=[];counter=7
 for i in range(a.n):
  # state machine process, schema is deliberately not numeric-pair rows
  counter += rng.choice([-11,-7,-4,2,5,9,13]); batch=rng.randint(-12,12)
  observed=(counter//3)+batch
  recs.append({'schema':'tukuyo.v958.state_transition/1','step':i,'before':{'counter':counter,'phase':i%4},'event':{'kind':'BATCH_APPLY','batch':batch},'observed':{'bucket_plus_batch':observed,'counter_after':counter+batch}})
 obj={'schema':'tukuyo.v958.state_transition_suite/1','generator_id':'state_machine_v958','seed':a.seed,'records':recs};a.out.write_text(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n')
if __name__=='__main__':main()
