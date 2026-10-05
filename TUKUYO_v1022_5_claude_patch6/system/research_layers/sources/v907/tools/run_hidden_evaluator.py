import json,pathlib,sys
R=pathlib.Path(__file__).parents[1];sys.path.insert(0,str(R));from tukuyo_v907.evaluator import evaluate
src=(R/'candidate/CANDIDATE_SOURCE.py').read_text();rows=json.loads((R/'evaluator_only/HIDDEN_ROWS.json').read_text());print(json.dumps(evaluate(src,rows),sort_keys=True))
