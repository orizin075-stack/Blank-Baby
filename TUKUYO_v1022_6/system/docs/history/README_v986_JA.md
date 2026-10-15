# TUKUYO v986 — Bounded Long-Horizon Purpose Planner

v985で形成された高位purposeを、複数cycleにまたがる監査可能な内部計画へ変換する層。計画は`WHOLE_AUDIT`、`HOMEOSTASIS_ASSESS`、`EVIDENCE_REFLECT`、`RELATIONSHIP_REVIEW`、`HEART_AUDIT`、`PURPOSE_REEVALUATE`の有限whitelistだけから構成される。各stepはcycle、step_id、成功条件を持ち、plan全体はpurpose state hashとidentityへ束縛される。purposeが更新された場合はstaleとして検出され、古い計画を無条件に実行しない。

これは長期計画の機能的実装であり、外部サービスへの自動操作、任意コード実行、open-ended goal inventionは含まない。
