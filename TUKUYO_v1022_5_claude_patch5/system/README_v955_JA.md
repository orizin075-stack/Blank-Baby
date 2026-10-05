# TUKUYO v955 — Capability Retention + Semantic Guard Migration

## 主要変更
1. D6をlive runtimeで閉鎖。旧v838の恒真式型 `_regression` はファイルを変更せず、起動時にv955 hardened guardへ置換する。
2. hardened guardはADD/SUB/MULを固定仕様ベクトルで独立検証し、OPS/BUILTINSを同じ実装同士で比較しない。
3. 既存個体の `semantic_source_sha256` は維持。旧semantic→v955 guardのtransition policyを別のSemantic Migration Authority鍵で署名。
4. `--semantic-migration-trust-file ... init` で新規個体を作るとmigrationを同時適用。既存個体は `semantic-migrate` で移行可能。
5. 3分布×10 familyのcapability retention matrixを追加。高速化のためMAX/MIN等を失う候補を昇格拒否。

## 重要な境界
- v955 guardは `run_tukuyo.py` の正式mounted runtime経路に装着される。legacy moduleを直接importして呼ぶことは正式runtime surfaceではない。
- migration trust anchorはruntime ZIP外の別配布物を信頼起点にする。ZIP内receiptの鍵だけをtrust rootにしてはいけない。
- general L6、30日wall-clock、独立第三者再現は未達。
