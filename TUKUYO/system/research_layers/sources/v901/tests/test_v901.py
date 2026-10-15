import json,pathlib,tempfile,shutil
from tukuyo_v901.lint import audit

def test_clean(tmp_path):
    src=pathlib.Path(__file__).parents[1]; d=tmp_path/'x'; shutil.copytree(src,d); assert audit(d)==[]
def test_mutation_detected(tmp_path):
    src=pathlib.Path(__file__).parents[1]; d=tmp_path/'x'; shutil.copytree(src,d); (d/'tukuyo_v901/lint.py').write_text('x=1'); assert audit(d)
