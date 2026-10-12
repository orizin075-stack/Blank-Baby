"""Replay an FPL proof against its original input, independently of the solving parser."""
from fractions import Fraction
from .check import check

def verify(query,answer,proof):
    try:
        if proof.get('kind')!='g4_reading' or proof.get('source_query')!=query:return False
        spec=proof['spec']
        if spec.get('text')!=query:return False
        result=check(spec,proof['values'])
        return result['ok'] and result['answer'] is not None and Fraction(result['answer'])==Fraction(str(answer))
    except (ValueError,KeyError,TypeError,ZeroDivisionError):return False
