# TUKUYO v1022.7.9 — 経験の出所を区別するSoul学習

開発・実験版。基準はv1022.7.8です。署名付き結果を学ぶSoulに、元の情報源の登録・署名・種別・環境を束縛する厳格モードを追加します。単に記録にラベルを付ける機能ではなく、実際の選択に使う予測誤差の補正を制限します。

## 出所と学習範囲

| 元の情報源の種別 | 対応する学習範囲 | 意味 |
|---|---|---|
| simulation | simulation | 模擬環境の経験。外部観測として採用しない |
| teacher | teacher | 教師の情報。外部観測として採用しない |
| external_observation | external_channel | 設定した外部チャネルからの署名付き申告。物理的な真偽は未証明 |
| self_report | 対応する確定経験モードなし | 自己申告として記録。外部確認済み経験に昇格しない |

範囲と環境IDは初期化後に変更できません。旧式の未分類記録を新しい範囲へ遡って昇格しません。過去の個体史や価値観を消去する機能ではありません。

元の情報源と転送した観測者を別の署名鍵として扱います。情報源の種別を登録済みのauthorityが署名し、情報源が結果の本文を署名し、観測者がその報告と結果・選択を結び付けて署名します。一つの教師を3人が転送しても、情報源の数は1です。3鍵でも設定した元情報源のdomainが同じなら3domainとして数えません。鍵はBase64の表記ではなく、復号した鍵のfingerprintで比較します。

予測誤差の補正には、同じ範囲・環境・状況・選択について、3つの設定済み情報源domainと鍵、3つの観測者domainと鍵、2回の実行済みエピソードが必要です。結果の不一致が大きい場合も補正を保留します。補正の上限0.6等は7.7の方式を保持します。

## 使用手順

個体データを配布ソースの外へ置き、通常のinit、evidence-soulのauthority・witness登録を完了してください。authorityとwitnessは各3組以上必要です。証明実験は模擬鍵で行います。実運用の信頼する相手の鍵と同じものではありません。

```bash
python -B run_tukuyo.py --data /path/individual --runtime-trust-file /path/TUKUYO_v1022_7_9_TRUST_ANCHOR.txt soul-provenance-init --scope simulation --environment sandbox-one
python -B run_tukuyo.py --data /path/individual --runtime-trust-file /path/TUKUYO_v1022_7_9_TRUST_ANCHOR.txt soul-provenance-source-add /path/source-certificate.json
python -B run_tukuyo.py --data /path/individual --runtime-trust-file /path/TUKUYO_v1022_7_9_TRUST_ANCHOR.txt evidence-soul-deliberate /path/bundle.json
python -B run_tukuyo.py --data /path/individual --runtime-trust-file /path/TUKUYO_v1022_7_9_TRUST_ANCHOR.txt soul-provenance-attest /path/observer-attestation.json /path/producer-report.json
python -B run_tukuyo.py --data /path/individual --runtime-trust-file /path/TUKUYO_v1022_7_9_TRUST_ANCHOR.txt soul-provenance-audit
python -B tools/v1022_7_9_experience_verifier.py --data /path/individual
```

次のevidence-soul-deliberateは自動的に、この出所の検査を経た経験だけで補正します。旧式のevidence-soul-attestだけで追加した結果は、厳格モードでは未分類のままで経験補正に使いません。元情報源の登録は最初の厳格な判断で封じられ、authority・witnessの登録は出所モードを初期化した時点で封じられます。

情報源の証明書・報告はそれぞれ `source_certificate/1` と `source_report/1` を使います。報告は個体・policy hash・決定・選択・環境・種別・測定方式・raw evidence・5つの結果数値を束縛します。観測者の `evidence_sha256` は `observer_evidence(report, observer_id)` で求めます。実行例とフィールドはテストと別添の再現スクリプトを参照してください。

## 互換性と未達

厳格モードは個体ごとに有効化します。既存個体の旧式の有界学習を一律に削除せず、未分類モードとして表示します。新規個体のinitだけでは有効になりません。後継へ私的な出所・経験の記録は自動継承しません。子の信頼設定は別途必要です。

v7.9はSoulの結果学習の経路に適用する機能です。G4の知識・教師学習・全ての記憶保存経路を置き換える機能ではありません。判断前の評価は予測であり、確認済み体験として扱いません。

authorityの設定と役割宣言を信頼する方式です。署名で保証するのは署名者と本文の束縛です。正規の署名者やauthorityが嘘をつく場合の物理的な真偽、domainの現実の社会的・統計的独立性、実AI業者が直接署名した返答、主観的意識、文字どおりの魂は証明しません。実験のexternal_channelも模擬の鍵と結果です。

Wholeの署名、コミット、復旧、死亡後の更新拒否、私的経験の非継承に接続します。v7.8の共有台帳は別機能です。登録済み個体では台帳引数も必要で、同じIDへのcheckpoint restoreを拒否する制約も引き続き適用します。台帳と個体全体の巻戻し、workspaceの未来ファイル再出現の根本原因、24h等の長時間、実LLM教師対話、自己コード改変は今回の完成を意味しません。

今回のパッチは開発用の鍵で署名しています。元の発行者の承認を意味しません。試験の合否は別添の検証報告で確認してください。
