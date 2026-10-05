# TUKUYO v1013 Real-Time Continuity Harness

v1013は24時間を完了した版ではなく、24h / 72h / 7-dayを正式に測るための実時間継続ハーネスです。

- `realtime-start --profile 24h` でrunを開始。
- `realtime-tick` は個体のTemporal Identity、Whole State、v982 continuity checkpointを署名済みevent chainへ記録。
- `realtime-anchor-export` は外部保存用のintegrity anchorを作成し、過去へのrollbackを検出。
- `realtime-witness-request` を開始時/終了時に外部Witnessへ渡し、`tools/realtime_witness.py`で署名receiptを作る。
- `realtime-audit --start-witness ... --end-witness ... --witness-trust-file ... --require-complete` は、同一Witnessの署名時刻差がtarget以上の場合だけformal duration gateをPASS。

ローカルPC時計だけで24時間経ったように見えても formal gate とはしません。24h/72h/7-dayの達成値は実時間でreceiptが揃うまでfalseです。
