# TUKUYO v1016 — Multi-Agent Society

v1015.5 の独立challenge再現基盤を保持したまま、複数個体の署名付き相互作用を現在の Living Episode / Soul / Relation / Peer Model / Whole State に統合する層。

## 新規公開面
- `society-send` — 公開packetを署名生成し、v1016送信台帳へ記録
- `society-receive` — 署名packetを検証・受理し、相手固有のLiving Episodeへ接続
- `society-ack` — ACKを検証し、送信側の相手固有履歴へ接続
- `society-status` / `society-audit` / `society-sync`
- `society-gate-assay <peerB_data> <peerC_data>` — 3個体統合ゲート

## v1016 gate
3個体を別identityとして初期化し、A↔B の協力履歴、A↔C の対立履歴、B↔C の第三者検証履歴を形成する。AはB/Cを別peerとして保持し、履歴差によりpeer-scoped choiceが分岐する。private relation noteが公開packetへ漏れないこと、packet replayが拒否されることもnegative controlとして検査する。

## Claim boundary
これは bounded Multi-Agent Society の機能ゲートであり、Theory of Mind、社会的意識、長期社会生態、24h multi-agent continuity、General L5、literal society/life/soul/consciousness を確立しない。cross-root distributed transaction の完全原子性も未証明。
