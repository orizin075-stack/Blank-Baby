"""TUKUYO generation 4: problems are read into a formal problem language (FPL), solved exactly, and checked.

  numbers  every number a problem states, with its position (Japanese and English)
  fpl      the formal problem language: quantities with units, facts tied to the text, the asked quantity
  solve    exact solver (rational arithmetic, propagation and linear elimination, unique answers only)
  check    a separately written checker: re-parses the facts, re-checks every equation, units, grounding and
           that the asked quantity has exactly one value
  reader_* TUKUYO's own readers (no LLM)
  llm      readers and answers from an external LLM; nothing an LLM says is committed without the checker
  api      one entry point that arbitrates between the readers
"""
