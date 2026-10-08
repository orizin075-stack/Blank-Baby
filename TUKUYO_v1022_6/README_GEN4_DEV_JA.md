# TUKUYO 第4世代（開発版 v1022.6+gen4-dev）

これは、TUKUYO 第4世代の**開発版**です。まだ正式な版ではありません。v1022.6 の上に、第4世代（`system/src/tukuyo_g4/`）を足したものです。

第4世代は、**3 つの LLM（Claude・ChatGPT・Gemini）を親にして育つ子**です。

- 問題を「式の言葉」に書き直し、分数のまま正確に解き、別に書いた検査で確かめてから答えます。
- 自分で読めない問題は、親たちが読みます。**別々の親の読みが 2 つ以上一致し、TUKUYO の検査にも通ったときだけ**答えます。
- 一致した読みは、どの親が一致したかと一緒に覚えます。数だけが違う同じ形の問題は、次から親なしで解けます。
- 知識や会話の問いは、親が答えます。答えには「確かめていない」と印を付けます（3 つの親が一致しても、一致は証明ではないため）。

## 1. 今の状態

| | 結果 |
|---|---|
| 署名と manifest | 開発用の鍵で署名済み（`v1022.6+gen4-dev`）。`deliverables/TUKUYO_v1022_6_TRUST_ANCHOR.txt` で検証できます |
| 全体テスト | **452/452 合格**（v1022.6 までの 432 件と、第4世代の 20 件） |
| ASDiv の開発用 1,083 問（他の人が作った英語の文章題）、親なし | `think`：正解 290、誤り 1（問題集の答えの誤りと見ている 1 問）、答えない 792。v1022.6 の `think` は正解 24、誤り 9 |
| 自分で書いた確認用の問題（引っかけを含む） | 103 問で誤り 0 |
| 親（Claude・ChatGPT・Gemini） | **まだ本物で一度も測っていません。** 記録した返事と、各社の道具の応答の型を使った試験だけです |
| 日本語の問題集（MGSM） | 親なしでは 0 問。日本語は親が入ってから伸ばす部分です |

## 2. 使い方

Python 3.12 以降と `cryptography` が必要です。個体のデータは、配布フォルダの外に置いてください。

```sh
cd system
A=../deliverables/TUKUYO_v1022_6_TRUST_ANCHOR.txt
python3 -B tools/verify_release.py . --trusted-pubkey-file $A
python3 -B run_tukuyo.py --runtime-trust-file $A --data ~/tukuyo init
python3 -B run_tukuyo.py --runtime-trust-file $A --data ~/tukuyo think -- 'Kim saw 4 cats in the morning. Later she saw one more cat. How many cats did she see in all?'
python3 -B run_tukuyo.py --runtime-trust-file $A --data ~/tukuyo g4-ask --voices all -- 'What is the capital of France?'
```

- 親のキーがないとき、`g4-ask` は計算の問題でない問いに `NOT_A_PROBLEM_AND_NO_LLM`（親がいないので答えない）と返します。
- `think` は、数の出てくる問題を第4世代にも読ませます。`--engine v1022` で、v1022 の核だけに戻せます。
- `--llm off` を付けると、親を呼びません。既定（auto）では、親のキーがあるときだけ呼びます。**親を呼ぶと費用がかかります。**

## 3. 親の設定

キーは環境変数で渡します。ファイルにもログにも書きません。第4世代の親は、`ANTHROPIC_API_KEY` や `OPENAI_API_KEY` など、ほかの道具が使う名前を読みません（v1022 の `llm-ask` の外部 LLM の設定 `TUKUYO_LLM_PROVIDER` は、これとは別の仕組みです）。

| 親 | キー | モデル | 道具 |
|---|---|---|---|
| Claude | `TUKUYO_ANTHROPIC_API_KEY` | `TUKUYO_LLM_MODEL`（既定あり） | `pip install anthropic` |
| ChatGPT | `TUKUYO_OPENAI_API_KEY` | `TUKUYO_OPENAI_MODEL`（**必ず指定**） | `pip install openai` |
| Gemini | `TUKUYO_GEMINI_API_KEY` | `TUKUYO_GEMINI_MODEL`（**必ず指定**） | `pip install google-genai` |

- ChatGPT と Gemini のモデル名は、よく変わるので決め打ちしていません。各社の文書で今のモデルを選んでください。
- `TUKUYO_LLM_PARENTS=claude,gemini` のようにすると、使う親を絞れます。`TUKUYO_LLM_VOICE` で、会話に答える親を選べます。
- 詳しい測り方・費用の目安・本番テストの決まりは `evidence_gen4/HANDOFF_GEN4.md` にあります。

## 4. 気をつけること

- **開発版です。** 本番のテスト（鍵のかかった問題集）は、第4世代ではまだ回していません。最終版で 1 回だけ回します。
- 署名は開発用の鍵です。正式に採用するときは、ご自身の鍵で署名し直してください（`README_V1022_6_JA.md` §3 と同じ手順）。
- v1022.6 の長時間融合試験（4 時間）は、2 時間 7 分で中断したままです（`README_V1022_6_JA.md` §1）。
