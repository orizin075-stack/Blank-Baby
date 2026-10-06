# TUKUYO 第4世代（開発中）— 引き継ぎメモ

このメモは、第4世代の作業を別のセッションで続けるためのものです。特に、Claude の API キーを使う測定は、キーを入れたあとの**新しいセッション**でしかできません。

## 1. 第4世代の考え方

- 問題を「式の言葉」（FPL, `src/tukuyo_g4/fpl.py`）に書き直し、厳密に解き（`solve.py`）、別に書いた検査（`check.py`）で確かめてから答えます。
- 書き直す手段は 4 つあります。
  - 学んだ型（`learn.py`）
  - TUKUYO 自身の読み取り器（英語、`reader_en.py`）
  - v1022 の核（日本語）
  - Claude（`llm.py`）
- 答えを確定するのは、検査に通った読みが一致したときだけです（`api.py`）。Claude の読みが 1 つだけ通ったときは、答えを保留します。
- Claude の 2 つの読みが一致して答えが確定したら、その読みを型として覚えます。同じ文で数だけが違う問題は、次から Claude なしで解けます。

## 2. 今の結果（2026-10-06）

| | 正解 | 誤り | 答えない |
|---|---|---|---|
| v1022.6（ASDiv dev 1,083 問） | 24 | 9 | 1,050 |
| 第4世代の自前の読み取り器（ASDiv dev） | 284 | 1（※） | 798 |

※ 「86 人を 9 人乗りのバスで運ぶ。必要なバスは？」で、問題集の答えは 9 ですが、読み取り器は 10 と答えます。ASDiv の他の「必要な数」の問題はすべて切り上げなので、問題集の答えの誤りと見ています。採点からは外していません。

鍵のかかったテストでの v1022.6 の結果（1 回だけ回したもの。`locked_test_runs.jsonl` に記録）:

| | 正解 | 誤り | 答えない |
|---|---|---|---|
| MGSM 日本語（111 問） | 0 | 0 | 111 |
| SVAMP（1,000 問） | 19 | 19 | 962 |
| ASDiv（1,009 問） | 21 | 14 | 974 |

## 3. Claude での測定（新しいセッションで）

1. クラウド環境の設定に、環境変数 `TUKUYO_ANTHROPIC_API_KEY` を入れます。この作業環境が自分で使う `ANTHROPIC_API_KEY` とは、別の名前にしてください。
2. `pip install anthropic`（または `uv pip install anthropic`）
3. 問題集を取ってきます：`python3 -B system/tools/g4_bench.py fetch DATA`。sha256 を固定してあります。
4. まず少数で試し、費用と精度を確かめます（下の目安を参照）。

```bash
cd TUKUYO_v1022_6/system
export TUKUYO_LLM_RECORD=$HOME/g4_llm_record.jsonl   # Claude の返事をすべて記録（あとで再生できる）
python3 -B tools/g4_bench.py run DATA --system g4 --split dev --set mgsm_ja --llm on --learn --work WORK --out mgsm_dev.json --show 10
```

- `WORK/v1022_individual` は、生きた個体です。日本語の v1022 の核と、学んだ型の置き場所に使います。
- 先に `python3 -B run_tukuyo.py --runtime-trust-file ../deliverables/TUKUYO_v1022_6_TRUST_ANCHOR.txt --data WORK/v1022_individual init` を実行してください。
- 記録したファイルを `TUKUYO_LLM_REPLAY` に指定すると、キーなしで同じ測定を再現できます。

### 費用の目安（`llm.py` の既定のモデル、effort medium、指示文はキャッシュ）

- 1 回の読みで、出力は約 2,000〜5,000 トークン（考える分を含む）です。1 問あたり 0.04〜0.10 ドルです。
- TUKUYO が自分で読めない問題は、2 回読みます。1 問あたり 0.08〜0.20 ドルです。
- MGSM の dev 139 問で約 11〜28 ドル、SVAMP のテスト 1,000 問で約 80〜200 ドルです。
- **実行する前に、どこまでやるか（費用）を利用者に確認すること。**

## 4. 鍵のかかったテストの扱い

- テスト（MGSM 111、SVAMP 1,000、ASDiv 1,009）は、`--locked-test-run 理由 --log evidence_gen4/locked_test_runs.jsonl` を付けたときだけ回ります。出力は件数だけです。
- 第4世代の最終版で、**1 回だけ**回します。回す前の開発には dev だけを使います。
- 最終の測定は 3 通り、それぞれ 1 回ずつ行います。
  1. Claude なし（自前の読み取り器と v1022 の核）
  2. Claude あり（`--llm on`）
  3. dev で学んだあと、Claude なし（学習の効果）

## 5. 残っている作業

- 自前の読み取り器の範囲を広げる（英語）。日本語の FPL 読み取り器は、まだありません。日本語は v1022 の核を使っています。
- Claude での dev の測定と、学習の効果の測定（キーが必要）。
- `think` から第4世代を通す統合。今は `g4-solve` / `g4-ask` という別のコマンドです。
- 版の名前・README・署名・リリース zip（第4世代の版として）。
