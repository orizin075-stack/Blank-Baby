# TUKUYO v999 — Adaptive Policy Search

v992の「always SHIELD と同一」という弱点を解消するため、120候補の有限方策構造を訓練世界で実走し、観測された最終スコアだけで選択する。

fresh評価では選択方策は状態依存で GATHER / SHIELD を使い分け、6 holdoutすべてで always-forward / always-shield / hand-written context rule を上回ることを要求する。

これは同一の閉世界family内の bounded policy search であり、cross-domain generalizationではない。
