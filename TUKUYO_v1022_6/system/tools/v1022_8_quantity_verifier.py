#!/usr/bin/env python3
"""Run input checker B alone. Does not import a TUKUYO package or producer.

Input JSON: {"text":str,"answer":str,"program":the optional source program}.
This checks a mathematical reading of supplied premises, not physical truth.
"""
import argparse,importlib.util,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('input',type=Path);a=p.parse_args()
module=Path(__file__).resolve().parents[1]/'src/tukuyo_g4/episodic_verify.py'
spec=importlib.util.spec_from_file_location('raw_quantity_check',module);check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check)
packet=json.loads(a.input.read_text());r=check.inspect(packet.get('text'),packet.get('answer'),packet.get('program'))
print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(0 if r.get('recognized') and r['ok'] else 1)
