# TUKUYO v1015.2 — Real-Time Endurance Execution Kit

v1015.1の認証済み耐久証拠層を変更せず、その外側に24h/72h/7day実時間campaignを運転する実行キットを追加する。runnerはwitness秘密鍵を保持せず、`v1015_2/witness_outbox`へ署名要求のみを生成する。外部witness agentはdata root外の秘密鍵で別プロセスからreceiptを作成する。

`endurance-exec-init` → 外部START witness → `endurance-exec-accept-witness` → 定期`endurance-exec-pump` → MID witness → END witness → authenticated endurance bundle、の順で動く。pumpはfresh-process runnerから呼べる。Living Episodeも指定間隔で低影響のoperational observationとして記録する。

短縮targetを使ったprotocol testは24h/72h/7day達成を意味しない。profile claimはv1015.1のraw event-chain + external witness再検証が成立した場合のみtrueになる。

## 推奨24h運転

本番用の例では `tick=300秒`, `checkpoint=3600秒`, `witness=300秒`, `living=3600秒` を推奨する。先にdata root外でwitness鍵を生成し、Terminal Aで `v1015_2_witness_agent.py watch`、Terminal Bで `v1015_2_endurance_runner.py` を動かす。runnerは公開鍵しか受け取らず、private keyは読み込まない。

24h/72h/7day claimはrunner stateではなく、最終的なv1015.1 authenticated endurance bundleの再検証結果のみを正本とする。途中でtick/witness deadlineを超えたrunは証拠を残したままinvalidになる。
