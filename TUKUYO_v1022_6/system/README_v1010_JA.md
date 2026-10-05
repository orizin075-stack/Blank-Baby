# TUKUYO v1010 Long-Life Cognitive Repair

v1009の外部監査で確認された長期性能・認知校正の欠陥を修復する版。

- Temporal Soul Identityの通常syncを差分追記化。完全再演はaudit時に維持。
- knowledge storeをappend-only + SQLite派生索引化。
- retrievalにanswerable/no-answer判定、coverage、top marginを追加。
- verifierは関連性・再計算を根拠に校正し、agreementだけで高confidenceにしない。
- 日本語の文章形式算数を内蔵calculatorへ正規化。
- conversation ingest完了時にwhole stateを自動sync。
- boundedな否定scopeを追加（助けてもらえなかった／誰も傷つかなかった等）。

これは一般言語理解やGPT-4相当を主張しない。長期個体としての計算量と、内蔵コアの反証可能な校正を改善する。
