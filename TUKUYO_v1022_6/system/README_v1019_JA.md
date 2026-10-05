# TUKUYO v1019 — Hardened Bounded Generational Evolution

v1018のflat signed lineage certificate chain / child-key binding / replay rejection / irreversible death / live inherited-value couplingを保持したまま、有限のheritable trait layerへbounded mutation・environment-specific fitness・selection・successor inheritanceを追加する。

## 重要な分離
- Functional Soul / autobiographical memory / Soul event historyは個体固有で、進化traitへ直接コピーしない。
- v1019のheritable traitは survival / integrity / curiosity / truthfulness / relationship の有限5軸。
- trait総量は3.15の固定budget。何かを上げるには別のtraitを下げる必要があり、全trait=1への単調飽和を防ぐ。
- selection結果のexact profileは次世代の進化層へ継承し、実行時のHeartへはbaselineから0.65減衰したprofileを接続する。

## 環境
resource / research / social / volatile の4環境のみ。各環境は固定された重みでfitnessを評価する。baseline個体も候補へ必ず含めるため、その局所selectionでfitnessが下がる候補は採用しない。

## fresh確認
- 新規v1019 regression: 6/6 PASS（分割実行）。
- v1018 hardening unit: 3/3 PASS。
- Parent→Child→Grandchildで research→social のenvironment shift、bounded mutation、distinct identity、one family lineage、Whole State 3/3を確認。
- 10世代実個体: 全個体 Evolution / Succession / Whole audit PASS。package sizeは約3.38KB→14.91KBまでほぼ線形。
- 100世代trait simulation: trait budget 3.15を全世代で保存し、全trait=1への飽和を防止。

## Claim boundary
これはbounded artificial generational adaptation assayであり、自然選択、literal genetic evolution、literal reproduction、literal life/soul、consciousness、open-ended evolution、General L5の成立を主張しない。
