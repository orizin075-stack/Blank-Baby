# V1022.7.7 — 経験によるSoulの判断強化

これは自己同一性、経験の連続性、価値判断、結果の振り返りを扱う有限ソフトウェアモデルです。文字通りの魂、主観的意識、感覚質、人間同等の人格性を証明する版ではありません。

## 改良

`evidence-soul-deliberate` は、未認証の `reflective-soul-outcome` による全体の重み調整を使いません。通常の `reflective-soul-*` は、互換性のため呼出者の申告によるシナリオ評価として残り、`LEGACY_UNAUTHENTICATED_SCENARIO` と明示します。署名付き判断側では、誓約と正規のSoul/Heart経験を維持しつつ、次の条件で結果の予測を補正します。

- 同じcontext文字列・同じ正規化済み選択肢で実行した2回以上の異なる判断。
- 各回、登録された異なる3鍵・3domainの署名付き結果。confidenceは0.7以上。自己申告種別は対象外。
- 各回の5効果項目の最大差が0.25以下。食い違う結果は学習から保留。
- 1回の判断について1鍵・1domainの最初の適格報告だけを使う。繰り返し報告で重みを増やさない。

選択した案の当初予測と結果の差を計算し、平均差の0.5倍、各項目最大±0.6で補正します。bodily_costは0〜1、他の効果は−1〜1の範囲を保ちます。外部が書いたsurprise値から補正量を決めません。別のcontext、signal、themeへ教訓を広げません。これは有限の保守的な学習で、未知の自然言語状況への一般化ではありません。

新しい判断は、使った過去判断、結果署名、予測誤差、補正、当時の結果履歴の末尾を証明記録へ残します。後から届いた結果を過去の判断が先に知っていたようには扱いません。古い署名・判断・誓約・identity・代謝資源を変更しません。私的な判断・結果はsuccessorの公開技能へ自動移送しません。

通常CLIの `soul-experience` は、既にHeartがある場合は新しい正規Soulイベントへの参照と現在のself-modelを同期します。正規イベントを二重に作らず、経験直後の `HEART_SOUL_DRIFT` を防ぎます。感情・value_bias・goal・過去のHeart記憶を再解釈せず、以前の相手別の判断を保ちます。感情を含む経験更新には `heart-experience` を使います。Heartがまだ無い場合の従来のSoul経験操作は保持します。

## 実験と操作

通常操作は、既存の `evidence-soul-authority-add`、`evidence-soul-witness-add`、`evidence-soul-deliberate`、`evidence-soul-attest` を使います。JSON形式は `README_V1022_7_EVIDENCE_BOUND_SOUL_JA.md` を参照してください。authoritiesとwitnessesの秘密鍵は個体root外で管理します。

```bash
python -B tools/v1022_7_7_soul_experiment.py \
  --data /absolute/fresh-individual \
  --trust /absolute/TUKUYO_v1022_7_7_TRUST_ANCHOR.txt \
  --out /absolute/soul-experiment.json
python -B tools/v1022_7_7_experience_verifier.py --data /absolute/fresh-individual
python -B run_tukuyo.py --runtime-trust-file /absolute/TUKUYO_v1022_7_7_TRUST_ANCHOR.txt \
  --data /absolute/fresh-individual evidence-soul-status
```

実験scriptは3組の鍵と模擬結果を作り、正規APIと通常CLIで試験します。実世界の3独立主体、実センサー、長時間の外部AI教師は使いません。別verifierはTUKUYOのruntimeや学習実装をimportせず、生JSONから署名と学習計算・履歴末尾・選択を再検算します。自然言語の意味や世界の真偽を独立に判定するverifierではありません。

## 研究から採った設計上の視点

2026年のWoitowらの研究では、自身および観察した他者の経験における結果の予測誤差と記憶を調べています。本実装では「予測と結果の差を記録し、次の判断へ返す」という工学上の設計を参考にしました。脳内回路、ドーパミン機構、主観体験を再現したとは主張しません。

- https://www.nature.com/articles/s41539-026-00409-7
- https://www.nature.com/articles/s41586-025-08888-1

後者の意識理論の対抗的実験も参考に、機能試験の成功と意識の成立を別の主張として扱います。

## 未達

3domainの一致は実世界の真実や独立性を証明しません。同じ管理者が全鍵を持つ場合、全員が同じ誤りをする場合、悪意ある多数派は検出できません。任意の文章から教訓を抽出する能力、自発的な長期目的、現実の他者との共成長、24時間運転は未証明です。V1022.7.5で観測されたworkspace出生付き復元の未来ファイル再出現も根本解決していません。新版の少数回復元試験で解決済みとは扱いません。LLM接続は7.6の両方式を維持しますが、資格情報無しで実接続済みと主張しません。

新規・既存試験の実測件数と失敗は、配布版に添える検証報告を参照してください。全件成功をこのREADMEから推定しないでください。
