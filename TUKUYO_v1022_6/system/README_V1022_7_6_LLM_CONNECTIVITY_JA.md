# V1022.7.6 LLM接続

ChatGPTの専用ログインと専用APIキーの両方に対応します。外部の実認証は利用者の端末で行います。この環境やCodexの認証を流用しません。APIキーは `TUKUYO_OPENAI_API_KEY`、選択したモデルは `TUKUYO_OPENAI_MODEL` で指定します。ホストの `OPENAI_API_KEY` を無断で読む機能は追加していません。キーやtokenを個体data root、配布ZIP、checkpoint、文化継承へ入れないでください。

```bash
python -m pip install -r requirements-chatgpt.txt
python -B tools/chatgpt_connect.py login
python -B tools/chatgpt_connect.py models
```

ログイン方式の手順・同意画面は旧 `README_V1022_6_6_CHATGPT_JA.md` も参照してください。モデルは利用者のアカウントが返す一覧から選びます。APIキーの発行や請求先は、このプログラムが勝手に変更しません。

## 両経路の診断

`../my_tukuyo` は初期化済みの専用個体rootです。`chatgpt-status --both` はネットワークへ接続せず、plan/apiを個別に表示します。`--probe` を追加すると、それぞれ設定済みの経路へ実際に一度ずつ試験要求を出します。設定の存在と接続成功を別フィールドで表示します。

```bash
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1022_7_6_TRUST_ANCHOR.txt --data ../my_tukuyo chatgpt-status --both
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1022_7_6_TRUST_ANCHOR.txt --data ../my_tukuyo chatgpt-status --both --probe
python -B run_tukuyo.py --chatgpt-auth plan --runtime-trust-file ../TUKUYO_v1022_7_6_TRUST_ANCHOR.txt --data ../my_tukuyo chatgpt-chat '前提と不足する情報を整理して' --session plan_lesson --max-calls 32
python -B run_tukuyo.py --chatgpt-auth api --runtime-trust-file ../TUKUYO_v1022_7_6_TRUST_ANCHOR.txt --data ../my_tukuyo chatgpt-chat '別の仮説と反例を検討して' --session api_lesson --max-calls 32
```

同じsessionの認証方式・接続先・モデルを途中で変える操作は拒否します。planは検証済みのアカウント識別も束縛します。APIのアカウント識別は取得していないため、APIキーそのものの持ち主の同一性は保証しません。キー変更はメモリ中の接続を作り直しますが、キーやそのhashを個体stateへ保存しません。

API方式は非streamが標準です。`TUKUYO_OPENAI_STREAM=1` でstreamにできます。planは公式HTTP仕様に沿って常にstream、store=false、文脈をinput配列に再送し、max_output_tokensとprevious_response_idを送りません。`TUKUYO_OPENAI_TIMEOUT` は5〜300秒、標準90秒です。APIの出力上限とplanの要求回数上限は、金額の厳密な上限ではありません。

## 長い会話と中断

標準で過去16成功turnを再送し、失敗や結果不明のturnは文脈へ混ぜません。必要なら `--context-turns 32 --context-chars 65536` まで指定できます。保存した全履歴と、今回モデルに渡した文脈は別です。省略した成功turn数を返し、見えていない過去を覚えていると扱いません。

強制終了などで要求がpendingのまま残った場合:

```bash
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1022_7_6_TRUST_ANCHOR.txt --data ../my_tukuyo chatgpt-audit
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1022_7_6_TRUST_ANCHOR.txt --data ../my_tukuyo chatgpt-resolve-pending --session plan_lesson --nonce <auditが返したnonce>
```

この操作は外部へ問い合わせず、結果不明として履歴に残してpendingを解除します。使った枠は返還せず、同じ質問も自動再送しません。nonceが違う操作、同じnonceの二度目の操作は拒否します。session上限に達している場合は解除後も新規要求を送れません。checkpointへの明示的な復元は外部の支出を取り消しません。

## 障害と認証更新

利用枠不足は同じ個体内の該当認証方式への新しい教師会話・studyを停止します。新sessionを作っても回避できません。学習batchもその場で終了し、途中の候補を採用しません。利用状況を確認した利用者が `chatgpt-resume-route --auth-mode plan` または `--auth-mode api` を明示して再開できます。この操作は通信せず、使った要求枠も返しません。別個体・別アプリ・生涯の支出を制御する機能ではありません。

一時的なavailability障害は時間を置いた手動再試行、無効な権限・非対応機能は設定確認として表示します。応答にerror全文を保存せず、公開されたcodeと復旧方針だけを扱います。HTTP Retry-Afterの秒数が有効なら返します。HTTP SDKの自動再試行は0回です。

refresh tokenはファイルlockの中で再読込してから更新します。一時的な更新失敗では既存tokenを保持します。invalid_grantなどで失効が確定した場合は使用不能なtokenを除き、発行済みclient IDとアカウント登録を残して再ログインを求めます。Windowsのlock分岐は実装しましたが、この環境での実測はLinuxです。

## 検証の境界と公式資料

実OpenAI SDKをloopbackの模擬HTTP/SSEサーバーに接続した試験は、実アカウントでのログイン・モデル推論・請求の成功を証明しません。教師対話も自然言語全体の意味を証明せず、既存の二例・形式・意味ゲートを通った有限学習だけが採用されます。実アカウントでの長時間AI教師会話は未実施です。

2026-10-12に公式OpenAI documentationを確認:

- https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations
- https://developers.openai.com/siwc/token-sharing-open-source/errors-and-recovery
- https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference
- https://developers.openai.com/siwc/token-sharing-open-source/sign-in
- https://developers.openai.com/api/docs/guides/streaming-responses
