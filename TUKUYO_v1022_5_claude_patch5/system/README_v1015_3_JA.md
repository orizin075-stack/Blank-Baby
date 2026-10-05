# TUKUYO v1015.3 — Endurance Resume / Failure Evidence

v1015.2の実時間耐久runnerを維持し、その外側に再開証拠・release binding・不可逆な失敗記録を追加する。目的は24h/72h/7day本番中にrunner停止、OS再起動、witness遅延、operator abortが起きても、「どこから再開したか」「continuity条件を破ったか」「失敗campaignを後から成功へ書き換えていないか」を監査可能にすること。

`endurance-exec-resume` は現在のrelease manifest/receiptと開始時bindingを比較し、runner session IDの変化だけを再開として記録する。`v1015_3_endurance_runner.py` は起動ごとに新しいsession IDを生成し、子CLIへ共通で渡すため、CLI subprocess数とrunner再起動数を分離できる。

cadence超過、release binding変更、operator abortはterminal failureとなり、v1015.2側にもFAILを伝播する。terminal failureは成功へ戻せず、`FAILURE_EVIDENCE.json`へresume履歴、execution/campaign/realtime履歴、witness request/receipt、release bindingを束縛する。`endurance-failure-evidence-audit` は失敗bundleのhash chainと存在するwitness署名を再検証し、24h/72h/7day成功claimが混入していないことを確認する。

この版自身は24h/72h/7dayの実時間完走を主張しない。短縮試験は再開・失敗証拠プロトコルの検証に限る。
