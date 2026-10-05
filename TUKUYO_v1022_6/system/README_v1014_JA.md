# TUKUYO v1014 — Restart / Recovery Continuity

v1014はv1013の実時間continuity harnessを、クラッシュ・state破損・rollback試行を含む復旧へ拡張する。

- `recovery-checkpoint`: data rootの非秘密状態を署名付きcheckpointへ保存。
- `recovery-audit`: checkpoint署名・各ファイルhash・件数/総量を検査。
- `recovery-restore --dry-run`: 一時領域へ復元し、Temporal Identity / Whole State / v1013 realtime ledger / 任意の外部anchorを検査する。
- `recovery-restore`: staged audit合格後だけ本体へcommitする。
- 秘密鍵とcheckpoint保管領域はsnapshotへ含めない。

## Claim boundary

この版は72時間運転を完了した版ではない。72hのprocess kill、checkpoint restart、resource pressure、rollback attemptを正しく測るための復旧基盤である。文字通りの生命・魂・意識は主張しない。
