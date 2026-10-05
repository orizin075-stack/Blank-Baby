from pathlib import Path
from tukuyo_v1001.knowledge import add,search
from tukuyo_v1002.cognition import answer
from tukuyo_v1003.benchmark import run

def test_v1001_retrieval(tmp_path):
    add(tmp_path,'京都の旧称には平安京がある','t')
    assert '平安京' in search(tmp_path,'京都 旧称',1)[0]['text']

def test_v1002_builtin_calc(tmp_path):
    assert answer(tmp_path,'17*(4+2)')['answer']=='102'

def test_v1002_rag(tmp_path):
    add(tmp_path,'TUKUYOの試験符号はSELENE','t')
    assert 'SELENE' in answer(tmp_path,'TUKUYO 試験符号')['answer']

def test_v1003_benchmark(tmp_path):
    assert run(tmp_path)['ok']
