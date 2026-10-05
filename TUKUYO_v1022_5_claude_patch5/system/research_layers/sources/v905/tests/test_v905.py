import json,pathlib
from tukuyo_v905.adapter import load_track
def test_missing_fails(tmp_path): assert load_track(tmp_path/'none.json')['reason']=='TRACK_MISSING'
def test_valid(tmp_path):
 p=tmp_path/'x.json';p.write_text(json.dumps([{'id':'1','prompt':'p','expected':'e','must_abstain':False}]));assert load_track(p)['ok']
def test_duplicate_fails(tmp_path):
 p=tmp_path/'x.json';p.write_text(json.dumps([{'id':'1','prompt':'p','expected':'e','must_abstain':False},{'id':'1','prompt':'q','expected':'f','must_abstain':False}]));assert load_track(p)['reason']=='DUPLICATE_ID'
