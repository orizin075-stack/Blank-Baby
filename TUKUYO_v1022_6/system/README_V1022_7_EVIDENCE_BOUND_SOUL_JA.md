# TUKUYO V1022.7 Evidence-Bound Soul Experimental

V1022.6.9のReflective Soulを反証実験にかけ、証明できる完全性と証明できない意味・主体性を分離して作り直した実験版です。

## 先に見つかった反例

V1022.6.9では、同じprocessが `invented-observer-A` と `invented-observer-B` という2つの文字列を送るだけで、署名なしのoutcomeが `CORROBORATED` へ到達しました。また、選択肢のsignalsを変えず、caller suppliedのeffectsだけを入れ替えると、`responsible_long_term` から `immediate_self_gain` へ選択が逆転しました。それでもReflective Soul AuditとWhole AuditはPASSしました。

この結果は、従来監査が「保存されたbytesの完全性」を検査していた一方、「誰が述べたか」「別主体か」「意味が正しいか」を証明していなかったことを示します。

## V1022.7で閉じた部分

- 旧unsigned outcomeの段階名を `PROVISIONAL_UNAUTHENTICATED`、`SINGLE_ID_CLAIM_UNAUTHENTICATED`、`MULTI_ID_CLAIM_UNAUTHENTICATED` に変更し、`CORROBORATED`を廃止しました。
- authorityはEd25519公開鍵として明示登録します。同じ公開鍵を別authority／別domainとして再利用できません。
- witnessはauthority署名付きcertificateを必要とし、observer ID、observer公開鍵、authority、trust domainを束縛します。
- Evidence-Bound decisionは3つ以上の異なるwitness公開鍵かつ3つ以上の設定済みtrust domainを要求します。
- option effectsは各witnessが署名し、options hash、context hash、全effect field、evidence hashへ束縛します。
- 3者以上の値を中央値で統合します。3者中2者が同じ正しい値なら、残る1者が許容範囲内でどの極値を出しても集約値を変えられません。
- 最初のEvidence-Bound decision後はauthority／witness registryを封印し、結果を見た後の偽観測者追加を拒否します。
- outcomeも署名付きattestationとし、decision hash、chosen option、evidence hash、測定種別、全outcome fieldへ束縛します。
- outcome statusを `AUTHENTICATED_SINGLE_SOURCE`、`MULTI_DOMAIN_LIMITED`、`MULTI_DOMAIN_ATTESTED` に分離しました。「真実確認」とは表示しません。
- TUKUYO本体をimportしない `tools/v1022_7_evidence_verifier.py` が、raw JSONから署名、commit chain、Whole binding、quorum、中央値、statusを別実装で再計算します。

## 基本操作

```bash
python3 -B run_tukuyo.py --runtime-trust-file /absolute/TRUST_ANCHOR.txt --data /absolute/individual init
python3 -B run_tukuyo.py --runtime-trust-file /absolute/TRUST_ANCHOR.txt --data /absolute/individual evidence-soul-integrate
python3 -B run_tukuyo.py --runtime-trust-file /absolute/TRUST_ANCHOR.txt --data /absolute/individual evidence-soul-authority-add authority.json
python3 -B run_tukuyo.py --runtime-trust-file /absolute/TRUST_ANCHOR.txt --data /absolute/individual evidence-soul-witness-add witness-certificate.json
python3 -B run_tukuyo.py --runtime-trust-file /absolute/TRUST_ANCHOR.txt --data /absolute/individual evidence-soul-deliberate signed-assessment-bundle.json
python3 -B run_tukuyo.py --runtime-trust-file /absolute/TRUST_ANCHOR.txt --data /absolute/individual evidence-soul-attest signed-outcome-attestation.json
python3 -B run_tukuyo.py --runtime-trust-file /absolute/TRUST_ANCHOR.txt --data /absolute/individual evidence-soul-audit
python3 -B tools/v1022_7_evidence_verifier.py --data /absolute/individual
```

authority秘密鍵とwitness秘密鍵はTUKUYO個体rootや配布ZIPへ置かず、異なる管理主体が保持してください。1人が3鍵を作ったデモでも暗号上は3鍵・3domainになりますが、現実の独立主体3者を証明したことにはなりません。

## 証明できる範囲

次の主張は、Ed25519秘密鍵が漏れていないこと、SHA-256と実装が想定どおりであること、起動時trust anchorが正しいことを仮定して、raw verifierと攻撃試験で支持されます。

- commit後にbytesを変更すると署名またはWhole bindingが失敗する。
- attestationを作った鍵が登録witness公開鍵に対応する。
- witness certificateを署名した鍵が設定authority公開鍵に対応する。
- decision前に、異なる3公開鍵・異なる3domainの署名が存在した。
- option、context、全effect field、evidence hashが署名対象に含まれる。
- 2者が同値なら1者の極端な外れ値を中央値が除去する。
- decision後のregistry追加、署名改変、replay、wrong-choice bindingを拒否する。
- 私的なauthority、witness、assessment、attestation stateをsuccessor packageへ入れない。

## 証明できない範囲

- authorityやwitnessが現実に別人・別組織・独立AIであること。
- 署名された観測内容が外界で真実であること。
- 3領域の過半数が同じ誤りや談合をしていないこと。
- callerが選んだtrust root自体が正当であること。
- sensorが測定対象へ正しく接続され、校正されていること。
- 文字通りの魂、主観意識、感覚質、人格性。

したがって本版の最高ステータスは `MULTI_DOMAIN_ATTESTED` です。`VERIFIED_TRUTH`、`CONSCIOUS`、`SOUL_PROVEN`は出しません。

## 次の課題

外部authority trust anchorの別経路配布、hardware-backed key、remote attestation、センサー校正証明、異種AIによるblind evaluation、悪意ある多数派を含む長時間実験が次の段階です。24時間、第三者再現、workspace復元問題の根本原因、自己コード改変も未達です。

