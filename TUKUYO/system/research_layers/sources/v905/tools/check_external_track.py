import argparse,json,pathlib,sys
R=pathlib.Path(__file__).parents[1];sys.path.insert(0,str(R));from tukuyo_v905.adapter import load_track
ap=argparse.ArgumentParser();ap.add_argument('track');ap.add_argument('--sha256');a=ap.parse_args();o=load_track(a.track,a.sha256);print(json.dumps(o,sort_keys=True));raise SystemExit(0 if o.get('ok') else 1)
