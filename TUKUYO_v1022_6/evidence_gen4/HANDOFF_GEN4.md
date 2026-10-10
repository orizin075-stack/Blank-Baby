# TUKUYO 第4世代（開発中）— 引き継ぎメモ

このメモは、第4世代の作業を別のセッションで続けるためのものです。第4世代は、3 つの LLM（Claude・ChatGPT・Gemini）を親にして育つ子です。親の API キーを使う測定は、キーを入れたあとの**新しいセッション**でしかできません。

## 1. 第4世代の考え方

- 問題を「式の言葉」（FPL, `src/tukuyo_g4/fpl.py`）に書き直し、厳密に解き（`solve.py`）、別に書いた検査（`check.py`）で確かめてから答えます。
- 書き直す手段は 4 つあります。
  - 学んだ型（`learn.py`）
  - TUKUYO 自身の読み取り器（英語、`reader_en.py`（物語）と `forms_en.py`・`forms_more_en.py`・`forms_algebra_en.py`（物語でない問題の形）。形の決まりと確かめ方は `FORMS_2026-10-10.md`）
  - v1022 の核（日本語）
  - 親：Claude・ChatGPT・Gemini（`llm.py`）
- 答えを確定するのは、検査に通った読みが一致したときだけです（`api.py`）。
  - TUKUYO 自身の読みが通ったときは、最初の親 1 つに読ませて突き合わせます。
  - TUKUYO が読めないときは、設定されている親がそれぞれ 1 回読みます。**別々の親の読みが 2 つ以上一致したとき**だけ答えます（route は `claude+gemini` など）。親が 1 つしかないときは、その親の 2 つの読み方（story・goal）が一致したときに答えます（`llm+llm`）。
  - 1 つの親の読みだけが通ったときは、答えを保留します（`SINGLE_LLM_READING`）。読みが食い違えば答えません（`DISAGREE`）。
- 親の読みが一致して答えが確定したら、その読みを型として覚えます（どの親が一致したかも記録）。同じ文で数だけが違う問題は、次から親なしで解けます。
- 計算の問題でない問い（知識・会話）は、声の親（`TUKUYO_LLM_VOICE`、既定は最初の親）が答えます。`g4-ask --voices all` で、全部の親の答えと、一致しているか（`agree`）を見られます。どれも「確かめていない」答えです。
- この子と魂（`life.py`・`memory.py`・`own.py`）：考えたことのうち学びになったこと（親から学んだ・親の誤り・正直に控えた・独りで解けた・知識を覚えた）を、心と魂に正式な経験として渡します。第4世代の経験は魂の法則 2（`tukuyo_v977/whole_state.py` の `_law2`）で入り、各経験の記録に `law: 2` が残ります（古い層は法則 1 のまま、どちらも記録からやり直せる）。親への信頼は、魂がその親ごとに持つ記録 `trust`（当たった読み・外れた読み、最近ほど重い）から計算し（`whole_state.trust_record`）、いちばん信頼する親が声になり、声には魂から作った人柄を渡します。2 つ以上の親が一致した短い答えは `g4/remembered.json` に覚えます（確かめた答えではない）。学んだもの 3 つ（型・答え・自分の記録）は個体の鍵で署名し、全体の状態にも記録します（`own.py`）。1 つの考えの経験は `g4/private/EPISODE.json` に先に書き、次の起動が残りを渡し終えます（`life.recover`、`tukuyo_v1014_2/crash_recovery.py`）。成長の記録は `g4-self`（`life_story` は魂の記録から）。魂らしさは `tools/soul_assay.py` で測ります（`SOUL_ASSAY_2026-10-09.md`）。親の本物の測定では、親ごとの信頼がどう育つかも記録すること。
- 自前の読み取り器は男女を知りません。2 人以上が出てくる he/she は、直前の主語として読んだうえで、ほかの読み方（同じ人を he とも she とも呼ばないもの）もすべて試します。別の答えになる読み方が 1 つでもあれば答えません。

## 2. 今の結果（2026-10-10）

ASDiv の開発用 1,083 問（他の人が作った英語の文章題）、親（LLM）なし：

| | 正解 | 誤り | 答えない |
|---|---|---|---|
| v1022.6 の `think` | 24 | 9 | 1,050 |
| 第4世代の読み取り器だけ（`g4-solve`） | 377 | 3（※） | 703 |
| 第4世代をつないだ `think` | 378 | 3（※） | 702 |

読める形を足す前（2026-10-06）は、`g4-solve` 287・`think` 290（誤りはどちらも 1）でした。種類ごとの内訳は `FORMS_2026-10-10.md`。

※ 3 問とも、読みは正しく、問題集の答えが違うと見ています。採点からは外していません。
- 「86 人を 9 人乗りのバスで運ぶ。必要なバスは？」：問題集は 9、読み取り器は 10。ASDiv の他の「必要な数」の問題はすべて切り上げです。
- 「5 列目は 50 脚。6 列目は？」：問題集は 50（5 列目の数）、読み取り器は 59。
- 7 つの数の平均：問題集は 100.1（丸めた数）、読み取り器は 701/7（約 100.14）。

いちばん大きい残りは、物語の読み取り器が文を読めても合う形がない問題（`NO_SCHEMA`、足し算・引き算・かけ算・わり算で約 400 問）です。

`think` での第4世代の使い方（`api.think`）：

- 数の出てこない問い（論理・記憶）と、答えが数でない問いは、これまでどおり v1022 の核が答えます。
- 日本語の文章題：v1022 の核の読みは、読みの 1 つです。親が設定されていれば、親の読みと突き合わせます。
- 英語の文章題：第4世代が読みます。v1022 の核の英語の物語の読み（証明に `schema` があるもの）は、ASDiv で 20 回正しく 9 回誤ったので、答えにも反対にも使いません（第4世代で確かめられないときは `withheld_answer` として見せ、答えは確定しません）。式（`12*(5+4)`）と公式の問題（平均・面積・最大公約数など、`mathprob`）の答えは、読みの 1 つとして使います（ASDiv で 4 回とも正解）。
- `llm-ask` も、最初の自前の答えを同じ `think` の決まりで出します。
- `--engine v1022` で、v1022 の核だけの `think` に戻せます。`--llm off|auto|on` で親を使うかを決めます（既定は auto：親のキーがあるときだけ使う）。
- テストは親を呼びません（`tests/conftest.py` が親の設定を外します）。

鍵のかかったテストでの v1022.6 の結果（1 回だけ回したもの。`locked_test_runs.jsonl` に記録）:

| | 正解 | 誤り | 答えない |
|---|---|---|---|
| MGSM 日本語（111 問） | 0 | 0 | 111 |
| SVAMP（1,000 問） | 19 | 19 | 962 |
| ASDiv（1,009 問） | 21 | 14 | 974 |

## 3. 親での測定（新しいセッションで）

1. クラウド環境の設定に、親のキーを入れます（Network secrets、古いアプリでは API credentials。なければ環境変数）。キーをチャットに貼ってはいけません。作業環境が自分で使う `ANTHROPIC_*` などとぶつからないよう、名前はこのとおりにします。

| 親 | キー | モデル |
|---|---|---|
| Claude | `TUKUYO_ANTHROPIC_API_KEY` | `TUKUYO_LLM_MODEL`（既定は `llm.py` の `MODEL_DEFAULT`） |
| ChatGPT | `TUKUYO_OPENAI_API_KEY` | `TUKUYO_OPENAI_MODEL`（**既定なし**） |
| Gemini | `TUKUYO_GEMINI_API_KEY` | `TUKUYO_GEMINI_MODEL`（**既定なし**） |

2. ChatGPT と Gemini のモデル名は、そのときの各社の文書で今のモデルを確かめ、セッションの中で `export` します（コードには既定を置いていません。名前がよく変わるため）。
3. ネットワーク：2026-10-08 の時点で、この作業環境から `api.anthropic.com` と `generativelanguage.googleapis.com` には届き、**`api.openai.com` は環境のネットワークの決まりで止められていました**。ChatGPT を使うには、環境の設定の Network access で `api.openai.com` を Allowed domains に足すか、許す範囲を広げてもらいます。
4. 道具を入れます：`pip install anthropic openai google-genai`（使う親の分だけでよい）。
5. 問題集を取ってきます：`python3 -B tools/g4_bench.py fetch DATA`。sha256 を固定してあります。
6. 生きた個体を作ります。日本語の v1022 の核と、学んだ型の置き場所に使います。

```bash
cd TUKUYO_v1022_6/system
python3 -B run_tukuyo.py --runtime-trust-file ../deliverables/TUKUYO_v1022_6_TRUST_ANCHOR.txt --data WORK/v1022_individual init
```

7. まず少数で試します。`--limit 10` は、各問題集の dev から決まった 10 問を取ります（毎回同じ 10 問）。結果の `llm_usage` に、親ごとの呼び出しの数とトークン数が出ます（`claude:calls`、`gemini:output_tokens` など）。ここから本当の費用を計算してください。

```bash
export TUKUYO_LLM_RECORD=$HOME/g4_llm_record.jsonl   # 親の返事をすべて記録（あとで再生できる）
python3 -B tools/g4_bench.py run DATA --system g4 --split dev --limit 10 --llm on --work WORK --out trial.json --show 10
```

8. 利用者が費用を承認したら、dev 全体を回します。`--learn` を付けると、親の一致した読みを型として覚えます。親を絞るときは `TUKUYO_LLM_PARENTS=claude,gemini` のようにします。

```bash
python3 -B tools/g4_bench.py run DATA --system g4 --split dev --set mgsm_ja --llm on --learn --work WORK --out mgsm_dev.json --show 10
```

- 記録したファイルを `TUKUYO_LLM_REPLAY` に指定すると、キーなしで同じ測定を再現できます（費用はかかりません）。
- 親の読みの失敗の理由（`LLM_NOT_CONFIGURED`、`MODEL_NOT_SET`、`PACKAGE_MISSING:openai`、`AUTHENTICATION`、`CONNECTION` など）は、`api.solve` の `readings` に出ます。

### 費用の目安（Claude は `llm.py` の既定のモデル、effort medium、指示文はキャッシュ）

- Claude の 1 回の読みで、出力は約 2,000〜5,000 トークン（考える分を含む）です。1 回あたり 0.04〜0.10 ドルです。
- 親が 3 つあると、TUKUYO が自分で読めない問題は 1 問あたり 3 回読みます。ChatGPT と Gemini の値段はモデルによって違うので、ここでは見積もっていません。
- 目安（Claude だけのとき）：試し（`--limit 10`、20 問）で約 2〜4 ドル、MGSM の dev 139 問で約 11〜28 ドル、SVAMP のテスト 1,000 問で約 80〜200 ドル。親が増えれば、そのぶん増えます。
- これは見積もりです。試しの `llm_usage` から計算した本当の費用で、見積もりを直してください。
- **実行する前に、どこまでやるか（費用）を利用者に確認すること。**

### 親を使わない計測

`python3 -B tools/g4_measure.py DATA --work WORK --out report.json` で、壊れ方・検査器の強さ・親の決まりの模擬・学習・正確さと速さを測れます（親は呼ばない、費用 0、dev だけ）。2026-10-08 の結果は `MEASURE_2026-10-08.md`。

## 4. 鍵のかかったテストの扱い

- テスト（MGSM 111、SVAMP 1,000、ASDiv 1,009）は、`--locked-test-run 理由 --log evidence_gen4/locked_test_runs.jsonl` を付けたときだけ回ります。出力は件数だけです。
- 第4世代の最終版で、**1 回だけ**回します。回す前の開発には dev だけを使います。
- 最終の測定は 3 通り、それぞれ 1 回ずつ行います。
  1. 親なし（自前の読み取り器と v1022 の核）
  2. 親あり（`--llm on`）
  3. dev で学んだあと、親なし（学習の効果）

## 5. 残っている作業

- 魂（`SOUL_ASSAY_2026-10-09.md` の「残っていること」）：古い層（`heart-experience` など）の経験は法則 1 のままです。いちばん信頼する親だけが確かめ役になるので、ほかの親の記録は育ちにくい（模擬では、確かさの近い親の順番を 7% ほどの一生で取り違える。ときどき知らない親に聞く案は、模擬で 93→95% と小さな得）。
- 魂の仕組みのメモ：v989 の推移の鎖は追記だけの記録 `v989/SOUL_TRANSITIONS.jsonl` です（1 行 1 推移。前の形 `SOUL_TRANSITIONS.json` は、次の経験のときに移します。読むのは `load_chain`）。心の経験は先に `v978/private/PENDING_FEELING.json` に書き留め、魂が受け取って心が受け取る前に止まったら、次の起動で心が受け取ります（`heart_loop.recover_pending`）。振り返り（`hindsight.py`）：親の読みが食い違って控えた問題を `g4/unresolved.json` に覚え、同じ形を学んだ（または確かめ直した）ときに、学んだ読みで昔の問題を解いて親ごとの当たり外れを入れます（`life.looking_back`、エピソードの一部）。検査に落ちた読みは、答えを控えたときも親の誤りです。

- 自前の読み取り器の範囲を広げる（英語）。日本語の FPL 読み取り器は、まだありません。日本語は v1022 の核を使っています。
- 親での dev の測定と、学習の効果の測定（キーが必要）。親ごとの正確さと、親どうしの一致の割合も記録する。
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
