"""Dispatch independently implemented input checks without altering legacy ABI.

The historical semantic_coverage module remains stdlib-only and standalone.
Neither quantity checker imports the answer producer or shares its tokenizer.
"""
from .semantic_coverage import inspect as legacy_input, quantity_scope
from .quantity_verify import inspect as quantity_input

def inspect(query,answer=None,proof=None):
    scope=quantity_scope(query)
    if scope is not None:return scope
    checked=quantity_input(query,answer,proof)
    return checked if checked is not None else legacy_input(query,answer,proof)
