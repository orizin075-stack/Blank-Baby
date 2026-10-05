# TUKUYO v953 — Bounded Autonomous Research + Recursive Improver

v943の自己訂正から始め、v944〜v953の研究ルートを一つの実行系へ統合した版。

- v944: hypothesis-class gap detection
- v945: finite AST primitive proposal
- v946: external evaluator + authority promotion
- v947: frozen cross-domain transfer
- v948: self-authored research goal proposal (external authorization required)
- v949: bounded autonomous research cycle
- v950: actual improver policy comparison
- v951-v953: three strict generations of bounded meta-improvement

`python -B run_tukuyo.py science-demo` で表現不足→新候補生成を再現。
`python -B run_tukuyo.py meta-demo` でI0→I1→I2→I3の探索effort改善を再現。

重要: v951-v953 は有限policy spaceの改善であり、コード自己書換えやgeneral L6の証明ではない。
