# TUKUYO V1022.6.3 Hypothesis Research Cognition Experimental

仮説が複数残ったとき、出力を見分ける入力を選び、観測で候補を絞り、次の質問を変える有限研究機能を追加しました。各分岐を探索し、目標の答えが一致するまでの最悪費用が最小になる質問を選びます。候補すべてと矛盾する観測では、仮説クラス全体が外れたとして保留します。

新しい公開CLIは `hypothesis-research task.json --events events.json` と `hypothesis-research-check packet.json`。操作と合格範囲は `ROUTE_V1022_6_3.md` に記載しています。前版の一次制約・観測研究・生命・代謝・継承・復元機能は保持しました。

候補は明示された有限の係数集合と二次式までです。現実の法則がこの範囲に属すると証明したわけではありません。観測値・測れる入力・費用は外部提供です。現実ツール、runtime内部の永続研究記憶、代謝への自動接続、汎用AGI、自己コード改変は未実装です。

# TUKUYO V1022.6.2 Active Research Cognition Experimental

明示された有理数の一次制約から、測定質問を生成し、費用内で目標を確定できる観測を選びます。観測を一つ受け取るごとに再計画し、センサーが利用不可なら費用を計上して別手段へ切り替えます。全履歴は、別の入力parserと零空間検査器で再検査します。

`think --research-capabilities capabilities.json --research-events events.json` が新しい入口です。使い方と境界は `ROUTE_V1022_6_2.md` を参照してください。公開CLIの前版機能は引き続き使えます。

センサー変数・費用・観測値は外部提供です。現実のツールを実行する機能、研究記憶のruntimeへの永続化、自由な自然言語理解、汎用AGI、自己コード改変は含みません。履歴JSONの独立検査は整合性を確認し、観測の真偽を世界に照らして認証しません。新規機能は `think` の明示研究モードで、代謝runnerへ自動接続していません。

# TUKUYO v1022.6.1 — Observation Cognition

不足条件を診断した後、予算内の最小費用の観測組合せを選び、受け取った値で目標を再検証します。[ROUTE_V1022_6_1.md](ROUTE_V1022_6_1.md)を参照してください。観測候補と値は外部から与え、現実への観測ツールは実行しません。

# TUKUYO v1022.6 — Goal-directed Constraint Cognition

頭脳面の改良として、複数条件の逆算・目標の一意性検査・不足条件の診断をthink / verified-queryへ加えました。例: `制約: A+B=18。B=2*A。Aは何？` → `6`。

現行の範囲は [ROUTE_V1022_6.md](ROUTE_V1022_6.md) を参照してください。V1022.5.2の数量意味・生命・復元機能を保持しています。新規の100回復元や24h運転を完了したという版ではありません。

v1021から、局所的な対話学習と「実個体の課題成績→資源→エネルギー→死亡→実後継個体」の有限ループへ進めた版です。実行時のLLM接続は不要です。

## 今回入ったもの

- 3人のAI教師役（数量意味・計画・人物記憶）との教材、学生の実応答、それを読んだ教師の追試。教師は同じモデル系列の別エージェントです。最終配布用個体には504例を適用しました。教材の正答をそのまま返すQA表ではなく、数値を抽象化したイベント規則、語彙の対応、出典付きの明示事実を学びます。
- 算術、数量の保存、肯定の多段論理、条件・費用付きの形式計画を局所的に処理します。計画は最大24行動・4096探索ノード。別の証明検査器は計算・推論手順・計画の再実行を検査します。自然言語から前提への翻訳の正しさまでは証明しません。
- 否定・予定・別在庫は実行済みの消費と区別します。数量範囲、単位不一致、未確認の報告、引用訂正、複数種類の在庫など、解釈できないものは保留します。学習の矛盾も保留理由になります。
- 2〜8個の実ランタイムがHeartで課題を選び、正答で有限資源からエネルギーを受け取り、活動費を払います。エネルギーゼロで不可逆に死亡します。モデル個体の代用やINJURYによる強制死亡を使いません。
- 死後継承の既存署名手順を保持します。出生時の6500単位も共有資源から払います。子には独立したidentity・Soul・Heart・鍵があります。遺伝形質は実個体の一本だけです。公開規則・語彙だけを文化として渡し、親の秘密鍵・私的事実・伝記は渡しません。
- 子を含む復元用コピーへ既存の個体鍵を保ちます。チェックポイント自体には秘密鍵を入れません。復元にはその個体の保存済み秘密鍵が必要です。

## 開始

Python 3.12以降と `cryptography` を使います。データは配布ディレクトリの外に置いてください。

```sh
python -B tools/verify_release.py . --trusted-pubkey-file ../TUKUYO_v1022_6_3_TRUST_ANCHOR.txt
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1022_6_3_TRUST_ANCHOR.txt --data ../my_tukuyo init --individual-id MY-TUKUYO
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1022_6_3_TRUST_ANCHOR.txt --data ../my_tukuyo think '1箱に13個入りが7箱あります。5個売った。残りは何個？'
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1022_6_3_TRUST_ANCHOR.txt --data ../my_tukuyo learning-audit
```

新規initは署名済みの公開学習規則を導入します。`init --blank-learning` は同じコードで学習なしの対照個体を作ります。既存個体を初期化し直して学習を上書きしません。CLIの `release_revision` が今回の配布版で、下位モジュールの `version` には元の版番号が残ります。

`think QUERY --formal-task task.json` は `initial`・`goal`・`actions` の明示条件を使います。行動はid・前提pre・代入set・整数変化delta・正のcostです。任意のPythonコードや外部コマンドは実行しません。`core-reason`、`cognitive-query`、`verified-query` も認識できる問いはこの処理へ渡します。

## 続けて教える

```sh
python -B tools/run_dialogue_school.py --runtime-trust-file ../TUKUYO_v1022_6_3_TRUST_ANCHOR.txt --data ../my_tukuyo --max-rounds 504
```

これは同梱教材のオフライン再演です。新しいAIとの会話や、新しい知識の獲得を自動で主張しません。実際に複数AI教師を使う場合は `--inbox ../teacher_inbox --duration-seconds 3600` を指定し、各教師が学生のresponseを読んで新しいJSONをinboxへ置きます。JSONは `teacher` と `examples` を持ち、例には `question`・`expected_answer`・`explanation`、必要なら `aliases`・`facts`・`event_labels`・`formal_task` を置きます。数値を変えた2例以上が必要です。教師の事実や語彙注釈は監督情報であり、真偽を世界全体に照らして自動検証する機能はありません。

学習は1万例、規則512件、語彙512件、明示事実1024件までです。新しい認識回路や自分の実装コードを書き換える機能ではありません。

## 実個体を運転する

```sh
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1022_6_3_TRUST_ANCHOR.txt --data ../my_tukuyo metabolism-init --families 4 --reservoir 160000 --regeneration 1600
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1022_6_3_TRUST_ANCHOR.txt --data ../my_tukuyo metabolism-step --ticks 8
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1022_6_3_TRUST_ANCHOR.txt --data ../my_tukuyo metabolism-audit
```

資源は百分の一の整数単位です。`initial_total + regenerated = reservoir + living_energy + burned` を毎tick監査します。課題の外部正解で採点した結果を資源移転に使います。学生には正解を渡しません。課題環境は設計された有限の算術・数量領域です。世代選択も既存のbounded trait選択で、自然選択の成立を証明したものではありません。

`--no-learning` と `--no-actions` はそれぞれ公開技能継承と行動を止める対照です。現在は最大512tick、累計64実個体、同時8実個体です。生存親の繁殖は未実装です。ownerとchildのCLIを直列化し、別経路からの子の更新はowner監査で検出します。

```sh
python -B tools/run_runtime_ecology.py --runtime-trust-file ../TUKUYO_v1022_6_3_TRUST_ANCHOR.txt --data ../my_tukuyo --duration-seconds 86400 --tick-seconds 300
```

実時間runnerを用意しました。短時間試験や加速tickを24時間運転の証拠に数えません。24時間完走、電源断、Windows/macOSは今回の合格主張に含めません。

## 検証

```sh
TUKUYO_TEST_RUNTIME_ANCHOR=/absolute/path/TUKUYO_v1022_6_3_TRUST_ANCHOR.txt python -B run_selftest.py
```

今回の実測結果・失敗と修正・再現スクリプトは、別配布の検証レポートとEVIDENCE ZIPを参照してください。古いREADME/STATUSは歴代層の記録です。現行の主張はこのREADME、STATUS.json、ROUTE_V1022.mdを使ってください。

汎用知能、自己コード改変、自然選択、開放的進化、主観的な意識・本物の魂や心の成立は主張しません。言い換えと情動を自由文全般で理解する機能もまだ限定的です。