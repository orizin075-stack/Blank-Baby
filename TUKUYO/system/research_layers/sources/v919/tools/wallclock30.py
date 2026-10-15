import json,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tukuyo_v919.wallclock import status
print(json.dumps(status(),sort_keys=True))
