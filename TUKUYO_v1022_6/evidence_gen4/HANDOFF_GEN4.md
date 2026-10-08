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
- 自前の読み取り器は男女を知りません。2 人以上が出てくる he/she は、直前の主語として読んだうえで、ほかの読み方（同じ人を he とも she とも呼ばないもの）もすべて試します。別の答えになる読み方が 1 つでもあれば答えません。

## 2. 今の結果（2026-10-06）

ASDiv の開発用 1,083 問（他の人が作った英語の文章題）、Claude なし：

| | 正解 | 誤り | 答えない |
|---|---|---|---|
| v1022.6 の `think` | 24 | 9 | 1,050 |
| 第4世代の読み取り器だけ（`g4-solve`） | 287 | 1（※） | 795 |
| 第4世代をつないだ `think` | 290 | 1（※） | 792 |

※ 「86 人を 9 人乗りのバスで運ぶ。必要なバスは？」で、問題集の答えは 9 ですが、読み取り器は 10 と答えます。ASDiv の他の「必要な数」の問題はすべて切り上げなので、問題集の答えの誤りと見ています。採点からは外していません。

`think` での第4世代の使い方（`api.think`）：

- 数の出てこない問い（論理・記憶）と、答えが数でない問いは、これまでどおり v1022 の核が答えます。
- 日本語の文章題：v1022 の核の読みは、読みの 1 つです。Claude が設定されていれば、Claude の読みと突き合わせます。
- 英語の文章題：第4世代が読みます。v1022 の核の英語の物語の読み（証明に `schema` があるもの）は、ASDiv で 20 回正しく 9 回誤ったので、答えにも反対にも使いません（第4世代で確かめられないときは `withheld_answer` として見せ、答えは確定しません）。式（`12*(5+4)`）と公式の問題（平均・面積・最大公約数など、`mathprob`）の答えは、読みの 1 つとして使います（ASDiv で 4 回とも正解）。
- `llm-ask` も、最初の自前の答えを同じ `think` の決まりで出します。
- `--engine v1022` で、v1022 の核だけの `think` に戻せます。`--llm off|auto|on` で Claude を使うかを決めます（既定は auto：`TUKUYO_ANTHROPIC_API_KEY` があるときだけ使う）。
- テストは Claude を呼びません（`tests/conftest.py` が Claude の設定を外します）。

鍵のかかったテストでの v1022.6 の結果（1 回だけ回したもの。`locked_test_runs.jsonl` に記録）:

| | 正解 | 誤り | 答えない |
|---|---|---|---|
| MGSM 日本語（111 問） | 0 | 0 | 111 |
| SVAMP（1,000 問） | 19 | 19 | 962 |
| ASDiv（1,009 問） | 21 | 14 | 974 |

## 3. Claude での測定（新しいセッションで）

1. クラウド環境の設定に、環境変数 `TUKUYO_ANTHROPIC_API_KEY` を入れます。この作業環境が自分で使う `ANTHROPIC_API_KEY` とは、別の名前にしてください。キーをチャットに貼ってはいけません。
2. `pip install anthropic`（または `uv pip install anthropic`）
3. 問題集を取ってきます：`python3 -B tools/g4_bench.py fetch DATA`。sha256 を固定してあります。
4. 生きた個体を作ります。日本語の v1022 の核と、学んだ型の置き場所に使います。

```bash
cd TUKUYO_v1022_6/system
python3 -B run_tukuyo.py --runtime-trust-file ../deliverables/TUKUYO_v1022_6_TRUST_ANCHOR.txt --data WORK/v1022_individual init
```

5. まず少数で試します。`--limit 10` は、各問題集の dev から決まった 10 問を取ります（毎回同じ 10 問）。結果の `llm_usage` に、実際に使ったトークン数が出ます。ここから本当の費用を計算してください。

```bash
export TUKUYO_LLM_RECORD=$HOME/g4_llm_record.jsonl   # Claude の返事をすべて記録（あとで再生できる）
python3 -B tools/g4_bench.py run DATA --system g4 --split dev --limit 10 --llm on --work WORK --out trial.json --show 10
```

6. 利用者が費用を承認したら、dev 全体を回します。`--learn` を付けると、Claude と一致した読みを型として覚えます。

```bash
python3 -B tools/g4_bench.py run DATA --system g4 --split dev --set mgsm_ja --llm on --learn --work WORK --out mgsm_dev.json --show 10
```

- 記録したファイルを `TUKUYO_LLM_REPLAY` に指定すると、キーなしで同じ測定を再現できます（費用はかかりません）。
- Claude の読みの失敗の理由（`LLM_NOT_CONFIGURED`、`AUTHENTICATION`、`ANTHROPIC_PACKAGE_MISSING` など）は、`api.solve` の `readings` に出ます。

### 費用の目安（`llm.py` の既定のモデル、effort medium、指示文はキャッシュ）

- 1 回の読みで、出力は約 2,000〜5,000 トークン（考える分を含む）です。1 問あたり 0.04〜0.10 ドルです。
- TUKUYO が自分で読めない問題は、2 回読みます。1 問あたり 0.08〜0.20 ドルです。
- 試し（`--limit 10`、20 問）で約 2〜4 ドル、MGSM の dev 139 問で約 11〜28 ドル、SVAMP のテスト 1,000 問で約 80〜200 ドルです。
- これは見積もりです。試しの `llm_usage` から計算した本当の費用で、見積もりを直してください。
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
- 版の名前・README・署名・リリース zip（第4世代の版として）。

## 6. 署名（新しいセッションで）

- これまでの署名の秘密鍵は、リポジトリに入れていません。新しいセッションにはありません。
- **測るだけなら、署名は要りません。** コミット済みの木は署名してあり、同梱のアンカーで検証できます。

```bash
cd TUKUYO_v1022_6/system
python3 -B tools/verify_release.py . --trusted-pubkey-file ../deliverables/TUKUYO_v1022_6_TRUST_ANCHOR.txt
```

- `system/` の中を直すと、署名し直すまで CLI とテストが動きません（manifest が合わないため）。そのときは、そのセッションで新しい鍵を作って署名し直し、第4世代の開発用のアンカーを置きます。v1022.6 のアンカーは書き換えません。**秘密鍵はコミットしません**（セッションの scratchpad など、リポジトリの外に置く）。

```bash
cd TUKUYO_v1022_6
K=リポジトリの外の場所/g4_key
python3 -B system/tools/claude_patch_sign.py keygen --out-dir $K
python3 -B system/tools/claude_patch_sign.py sign system --private-key $K/patch_signing.key --revision v1022.6+gen4-dev
cp $K/patch_signing.pub deliverables/TUKUYO_GEN4_DEV_TRUST_ANCHOR.txt
python3 -B system/tools/verify_release.py system --trusted-pubkey-file deliverables/TUKUYO_GEN4_DEV_TRUST_ANCHOR.txt
# テストは TUKUYO_TEST_RUNTIME_ANCHOR=…/deliverables/TUKUYO_GEN4_DEV_TRUST_ANCHOR.txt で回す
```

- 鍵が変わると、代謝を動かしている個体は `runtime-trust-rebind --previous-trust-file 古いアンカー` を 1 回実行する必要があります（v1022.6 の README「採用と移行」と同じ）。
- 第4世代の版を出すときは、版の名前で署名し、アンカーのファイル名も版の名前にします。正式に採用するときは、利用者ご自身の鍵で署名し直します（v1022.6 の README §3 と同じ手順）。
