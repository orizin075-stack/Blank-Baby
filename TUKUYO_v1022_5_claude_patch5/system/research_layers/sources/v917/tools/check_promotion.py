import argparse,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tukuyo_v917.gate import decide
p=argparse.ArgumentParser();p.add_argument('receipt');p.add_argument('--evaluator-pubkey-b64',required=True);p.add_argument('--candidate-sha256',required=True);a=p.parse_args();o=json.loads(pathlib.Path(a.receipt).read_text());r=decide(o,a.evaluator_pubkey_b64,a.candidate_sha256);print(json.dumps(r,sort_keys=True));raise SystemExit(0 if r['promote'] else 1)
