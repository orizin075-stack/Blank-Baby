"""No test reaches a real LLM: the Claude settings of the developer's environment are removed for the whole test
session (the CLI subprocesses inherit os.environ). Tests that need Claude use recorded replies (TUKUYO_LLM_REPLAY),
set with monkeypatch."""
import os
for _k in ('TUKUYO_ANTHROPIC_API_KEY','TUKUYO_ANTHROPIC_BASE_URL','TUKUYO_LLM_REPLAY','TUKUYO_LLM_RECORD'):os.environ.pop(_k,None)
