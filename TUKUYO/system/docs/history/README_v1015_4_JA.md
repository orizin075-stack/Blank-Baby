# TUKUYO v1015.4 — Independent Endurance Reproduction Kit

v1015.3 の成功・失敗耐久証拠を、元 data root に依存しない portable reproduction bundle として書き出す層。

- `endurance-repro-export --out ... --witness-trust-file ...` で SUCCESS / FAILURE を自動判定して portable bundle を生成する。
- `tools/v1015_4_independent_verifier.py` は TUKUYO package を import せず、別配布 publisher trust と witness trust だけを使って release receipt、release binding、resume/execution chains、realtime signatures、campaign chain、witness receipts を再検証する。
- コピー済み `audit.ok` や completion flags は権威として使わない。
- 24h / 72h / 7day の実時間完走はこの版でも未完了。第三者「人間」による外部再現も PENDING。
