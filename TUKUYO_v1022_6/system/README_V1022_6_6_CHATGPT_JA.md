# TUKUYO V1022.6.6 ChatGPT Teaching Experimental

V1022.6.5 Gen4 Fusionの頭脳・実個体・署名・復元基盤を保持し、ChatGPTの正式な認証、継続対話、異なる2例からの教師学習を追加しました。認証前に「接続済み」とは表示しません。workspaceの反復復元問題は未解決です。

## 接続する

本体ZIPと公開アンカーを同じフォルダに置いて、本体を展開してください。`system` に移動し、Pythonで次を実行します。秘密鍵・APIキーをこのチャットへ貼る必要はありません。

```sh
python -m pip install -r requirements-chatgpt.txt
python -B tools/chatgpt_connect.py login
```

自分のPCのブラウザで **Continue with ChatGPT** を完了します。対象プラン・アカウント・workspaceの許可によって利用可否が変わります。ChatGPTの過去の会話を読む権限は要求しません。登録したTUKUYOの資格情報だけを `~/.config/tukuyo/` の保護されたファイルへ保存します。既存のCodexの資格情報や、ホストのOPENAI_API_KEYを流用しません。

モデル一覧と選択は、ログインしたアカウントのものを使います。PowerShellでは次のようにします。

```powershell
$env:TUKUYO_CHATGPT_AUTH = "plan"
python -B tools/chatgpt_connect.py models
$env:TUKUYO_OPENAI_MODEL = "一覧から選んだモデルID"
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1022_6_6_TRUST_ANCHOR.txt --data ../my_tukuyo init
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1022_6_6_TRUST_ANCHOR.txt --data ../my_tukuyo chatgpt-status --probe
```

macOS/Linuxでは環境変数を `export TUKUYO_CHATGPT_AUTH=plan` と `export TUKUYO_OPENAI_MODEL=...` で設定します。上のモデルIDは置換用です。使用できるモデルを推測して自動固定しません。既存個体にはinitを繰り返さず、新アンカーで `runtime-trust-rebind --previous-trust-file 旧公開アンカー` を使います。

APIキー方式も使えます。専用の `TUKUYO_OPENAI_API_KEY` と `TUKUYO_OPENAI_MODEL` を環境変数に設定し、`TUKUYO_CHATGPT_AUTH=api` を選択します。APIキー方式の料金はAPIアカウントの設定に依存します。

`chatgpt-status` は設定を見るだけです。`--probe` を付けた場合だけ短い実リクエストを送り、完了した正しい応答を得たときだけ `live_connection_verified=true` になります。record/replayを実接続の証拠には使いません。

## 対話と学習

次の例はsystemフォルダで実行します。両方式とも、明示的に設定したモデルへリクエストします。

```sh
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1022_6_6_TRUST_ANCHOR.txt --data ../my_tukuyo chatgpt-chat "未解決問題の条件を整理する方法を教えて" --session lesson1 --max-calls 16
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1022_6_6_TRUST_ANCHOR.txt --data ../my_tukuyo chatgpt-chat "では、条件が足りない場合の次の観測は？" --session lesson1
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1022_6_6_TRUST_ANCHOR.txt --data ../my_tukuyo chatgpt-study chatgpt_study_examples.json --dry-run
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1022_6_6_TRUST_ANCHOR.txt --data ../my_tukuyo chatgpt-study chatgpt_study_examples.json --session arithmetic1 --max-calls 8
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1022_6_6_TRUST_ANCHOR.txt --data ../my_tukuyo think --llm off "When three times a number is decreased by twelve, the result is 60. What is the number?"
```

会話は過去8成功turnを文脈として使い、署名付き状態に保存します。返答は常にunverifiedです。会話を保存することと、その内容を知識として採用することは別です。自伝や鍵を自動で教師へ送る機能はありません。

新しいstudyは、自力で解けない問いを選び、同一教師にstory/goalの2読みを依頼します。読みを厳密に解き、別実装の形式検査、原文span、対応範囲内の意味検査、値と単位の一致を確認します。さらに同じ型の異なる数値例2件が揃うまで、新しい型を採用しません。同一例の繰り返しでは条件を満たしません。採用後は同じ文型の新しい数値を、教師なしで解けるようになります。例の教材は既知の開発用問題で、未知holdoutではありません。

同じ教師の2読みは独立した教師ではなく、形式的な整合性が自然言語の意味全体を証明するわけでもありません。studyは重みを更新せず、数値スロットを持つ有限の型を保存します。G4の既存の一般経路は親版の合議規則を保持し、新しい2例ゲートはchatgpt-studyに適用します。

## 接続・復旧の境界

ChatGPTプランのHTTP経路は公式Responses APIを使い、store=false・stream=true、完了event確認、inputでの文脈再送を守ります。previewで禁止されるmax_output_tokensやprevious_response_idは送りません。APIキー経路は従来の非streamも対応します。plan経路は出力token上限を指定できないため、sessionのリクエスト数を制限しても金額や総tokenの厳密な上限にはなりません。

リクエスト枠を通信の前に署名して予約します。途中停止で結果不明になった枠は自動再送せず、当該sessionを停止します。必要なら別名のsessionで再開します。通信結果はローカルtransactionで保存しますが、外部の請求・生成をrollbackできるという意味ではありません。

学習型と会話はWhole State・transaction・checkpointの監査対象です。認証tokenは個体data rootへ入れず、子孫・公開技能・checkpointに含めません。資格情報の保存先を個体内に指定した対話は拒否します。資格情報はUnixで0600の専用ファイルです。WindowsのACL・実環境でのブラウザログインは別途確認が必要です。logoutはローカル資格情報を削除し、遠隔の権限撤回はChatGPT設定から行います。

sessionの回数上限は、その時点の署名付き状態に適用します。過去のcheckpointへ明示的に復元してから新たに通信する場合、復元前に使った外部リクエストも請求や利用枠の消費に残ります。生涯の支出上限を保証する機能ではありません。

今回の実測は外部の検証報告・evidenceを参照してください。本物のChatGPTへの接続、長時間対話、汎用知能、意識、24h、workspaceの復旧根治を、offline試験の成功だけで主張しません。

## 公式仕様

- [Registration and sign-in](https://developers.openai.com/siwc/token-sharing-open-source/sign-in)
- [Models and inference](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference)
- [Preview limitations](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations)
- [Accounts and sessions](https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions)
- [Responses API conversation state](https://developers.openai.com/api/docs/guides/conversation-state)

2026-10-08に確認。サービスの仕様・対象アカウントの条件は変更される可能性があります。
