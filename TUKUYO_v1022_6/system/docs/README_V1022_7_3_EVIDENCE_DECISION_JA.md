# V1022.7.3 — Evidence Decision Experimental

今回の改良は、有限の観測から行動を決める判断と、結果に基づく資源移動です。

## 改良した経路

1. 3台以上の署名付き測定を受け取る。
2. 数値では各機器の申告誤差範囲の共通部分を求める。文字列・真偽値では全測定の一致を要求する。
3. 共通部分全体が主張を満たす場合だけ `ACT`。食い違う場合は `ACQUIRE`。同じ主張で最大2回の追加観測を使っても解決できなければ `ABSTAIN`。
4. 実runtimeの現在の署名付きhead、行動、期待する結果、報酬上限、論理期限を事前記録する。
5. 事前記録より後の新しい測定を、期待した結果と照合する。
6. 測定から導いた成功判定と役割分離した検証者の署名が一致した場合、有限reservoirから実runtimeへ資源を移す。

中央値は従来どおり情報として残しますが、行動条件にはしません。1台だけ大きく外れる場合も、再測定を要求します。故障が続く場合は前版より多く保留します。

資源受取は年齢を進めません。時間経過は `metabolism-step` が扱います。

## 復元後の追加防御

今回の新規実個体実験で、workspace上の復元後に未来commit 2本と子個体のキャッシュ等が再出現する現象を観測しました。チェックポイント内のファイル内容は一致し、余分なファイルだけが残りました。再出現元の根本原因は未確定です。

このため、復元完了時に署名付き `RESTORE_FRONTIER.json` を保存します。元のWhole headが維持されている期間だけ、チェックポイントのファイル集合を強制します。余分な管理対象ファイルは署名付き記録を添えて隔離し、変更されたチェックポイント内のbytesは書き直さず拒否します。鍵は保持します。正当な操作でWhole headが進んだら古い境界を使いません。PREPAREDのredoも優先します。

これは再出現に対する防御策です。根本原因を除去した証明、全filesystemでの長期安定性、100回復元や24時間運転の証明とは区別します。

## CLI

通常の `grounded-sensor-observe` に加え、次の2操作を追加しました。各入力はJSONです。

```bash
python -B run_tukuyo.py --runtime-trust-file /absolute/path/TRUST_ANCHOR.txt --data /absolute/path/individual grounded-sensor-decide decision.json
python -B run_tukuyo.py --runtime-trust-file /absolute/path/TRUST_ANCHOR.txt --data /absolute/path/individual grounded-sensor-precommit intent.json
python -B run_tukuyo.py --runtime-trust-file /absolute/path/TRUST_ANCHOR.txt --data /absolute/path/individual grounded-sensor-outcome measured-outcome.json
python -B tools/v1022_7_2_grounded_verifier.py --data /absolute/path/individual
```

Decision入力は `schema=tukuyo.v1022_7_3.sensor_decision_request/1`、`observation_sha256`、`predecessor_sha256`（初回null）。追加観測は前回decisionのhashを指定します。

Intent入力は `schema=tukuyo.v1022_7_3.action_intent_request/1`、`intent_id`、`decision_sha256`、`runtime_id`、`action_id`、`action_context_sha256`、`expected_result`（typed claim）、`maximum_credit`（1〜1000）、`started_at_tick`、`deadline_tick`。

成功報酬receiptは `schema=tukuyo.v1022_7_3.measured_outcome_receipt/1`。従来フィールドに `intent_sha256`、`result_observation_sha256` を追加し、`result_evidence_sha256` は結果観測hashに一致させます。成功フラグは測定の照合結果と一致しなければ拒否します。

同じintent・結果観測・receiptを再利用できません。行動事前記録後に対象runtimeが更新されていたら、新しい判断と事前記録が必要です。

## 互換性

従来のV1022.7.2 outcome receiptは、報酬0の記録に限って受理します。成功署名だけでの資源移動を禁止しました。旧2テストを、この仕様変更に合わせて強化しています。テスト削除・skipは行っていません。

grounded_sensorのstate schemaを7.3に変更しました。7.2の既存個体への自動移行は実装していません。この版は新規data rootで検証してください。旧個体を消したり初期化し直したりしないでください。下位moduleの歴史的な版番号は残します。

## 研究との関係と限界

2026年のBCEA研究の「回答・保留・追加観測」という三択を設計参考にしました。Conformal predictionそのものは実装していません。校正のprecisionは機器設定が宣言した誤差限界であり、確率的な信頼区間ではありません。

独立検証器はTUKUYO runtimeをimportせず、分数演算で判断を再実行します。生成側はDecimal演算を使います。別実装でも、入力の意味・校正の正しさ・機器の物理的独立性まで保証するものではありません。

自動で実機を操作するactuatorはありません。追加観測は要求を記録し、外部が測定を供給します。論理tickは本物の時計ではありません。全機器の共通故障や共謀で同じ誤値を署名すれば、誤判断し得ます。設定名やadapter hashの相違だけで現実の独立性を証明していません。

今回の実験は生成した鍵と模擬測定によるソフトウェア試験です。実物の質量、外界の真理、意識、文字通りの魂・生命は証明していません。汎用知能の上昇、自然選択、24時間運転、複数の異種AIによる長時間学習も今回の証拠の範囲外です。

## 一次資料

- Xu et al., 2026, [Look Again Before You Abstain: Budgeted Conformal Evidence Acquisition](https://arxiv.org/abs/2606.16667v4)。限定予算下で証拠を追加する判断の設計参考。
- Chau et al., 2026, [Quantifying Epistemic Predictive Uncertainty in Conformal Prediction](https://arxiv.org/abs/2602.01667)。予測候補間の不一致を判断に反映する考え方の参考。論文の手法を実装したとは主張しません。
- NIST, 2026, [Expanding the AI Evaluation Toolbox with Statistical Models](https://www.nist.gov/news-events/news/2026/02/new-report-expanding-ai-evaluation-toolbox-statistical-models)。固定試験上の成績と未知問題への一般化を分け、評価の仮定を明示する方針を採用。

全体試験は `python -m pytest -q tests --dist loadscope -n 4`。`TUKUYO_TEST_RUNTIME_ANCHOR` に外部trust anchorの絶対パスを指定します。歴史資料の `research_layers` は現行pytest収集の対象にしません。

新規個体の再現実験（dataは未作成の絶対パス）：

```bash
python -B tools/v1022_7_3_proof_experiment.py --trust /absolute/path/TRUST_ANCHOR.txt --data /absolute/path/new-individual --out /absolute/path/proof.json
```

この実験は公開CLIで校正・観測・判断・事前記録・結果照合・代謝・継承・別プロセス復元を行います。生成する秘密鍵・個体データは配布しません。入力JSONには公開鍵と署名のみ含めます。
