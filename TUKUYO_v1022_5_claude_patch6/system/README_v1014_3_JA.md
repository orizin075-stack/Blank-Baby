# TUKUYO v1014.3 — Long-Run Continuity Campaign Harness

v1014.2 の atomic crash recovery を、24時間・72時間・7日間の実時間継続試験として運用するための再開可能な campaign 層。

- `continuity-campaign-start`: realtime run、初期 recovery checkpoint、start witness request、start external anchor を一括作成。
- `continuity-campaign-step`: 別Pythonプロセスから heartbeat を追加し、必要なら recovery checkpoint を作成。起動時に v1014.2 が修復した crash action も campaign evidence に記録する。
- `continuity-campaign-end-request`: 外部witness用の終了requestを作成。
- `continuity-campaign-audit`: realtime署名chain、Whole State、recovery checkpoint、campaign event hash chain、外部witness pairを統合監査。
- `continuity-campaign-evidence`: 監査・resource sample・主要state hashを単一JSONへ束縛。

24h/72h/7d の正式完走は、対応する実時間が経過し、同一外部witness鍵によるstart/end receiptが検証された場合にのみ成立する。短縮gateのPASSを24時間完走と呼ばない。
