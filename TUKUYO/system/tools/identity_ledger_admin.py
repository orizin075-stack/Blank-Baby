#!/usr/bin/env python3
"""Create a local external witness; no individual private keys are exported."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tukuyo_v1022.identity_ledger import create
p=argparse.ArgumentParser();p.add_argument('command',choices=['create']);p.add_argument('--ledger',type=Path,required=True);a=p.parse_args()
print(json.dumps(create(a.ledger),ensure_ascii=False,indent=2))
