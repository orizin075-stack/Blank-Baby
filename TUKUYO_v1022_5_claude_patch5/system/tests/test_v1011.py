import sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_v1001.knowledge import add,search_diagnostics
from tukuyo_v1011.calibration import assay

def test_v1011_fact_facet_paraphrase_and_entity_rejection():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)
        add(d,'アルファ共和国の首都はセレン。');add(d,'アルファ共和国の人口は20万人。')
        r=search_diagnostics(d,'アルファ共和国の首府はどこ？',3)
        assert r['answerable'] and 'セレン' in r['results'][0]['text']
        x=search_diagnostics(d,'ベータ共和国の首都は？',3)
        assert not x['answerable'] and x['reason']=='ENTITY_MISMATCH'

def test_v1011_bounded_calibration_is_directionally_correct():
    with tempfile.TemporaryDirectory() as td:
        r=assay(Path(td));assert r['ok'] and r['auroc']>=.9 and r['wrong_uncertain']>=5
