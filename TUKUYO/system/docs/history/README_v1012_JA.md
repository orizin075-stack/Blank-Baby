# TUKUYO v1012 — Memory Compaction + Core Reasoning Repair

v1012は24時間連続試験の前段として、長期記憶の安全なcheckpoint化と内蔵推論の強化を行う。

- canonical Soul/Heart/Conversation/Knowledge履歴は削除せず、検証可能checkpointを生成する。
- checkpoint後の追記を許し、過去prefixの改ざんは検出する。
- 軽量内蔵推論で数量文章問題、単純条件推論、比較推移、限定的カテゴリ推論を扱う。
- 導出できない問題を推測で埋めない。

Claim boundary: memory compaction is non-destructive working-memory compaction, not proof that arbitrary old memories can be deleted without semantic loss. Core reasoning is bounded and is not general reasoning or GPT-class standalone intelligence.
