# TUKUYO V1022.6.9 Reflective Soul Experimental

V1022.6.8 の6面Functional Soulを、判断後の結果から再評価できる署名付き反省層へ拡張した実験版です。過去を都合よく書き換えず、元の経験・決定・反実仮想を保存したまま、新しい解釈を追加します。文字通りの魂、主観意識、感覚質、人格性を証明するものではありません。

## 今回の強化

- 自分の利益、他者の利益、未来の自分、真実との整合、身体コストを別々に評価します。単一の善悪点へ早い段階で潰しません。
- 自己・他者・未来の利害が衝突するほど判断保留の閾値を上げます。不確実性も同じ閾値へ反映します。
- Heartだけ、V1022.6.8 Functional Soulまで、V1022.6.9 Reflective Soulまで、という3段階の反実仮想を署名付き決定証明へ残します。
- 判断結果は `reflective-soul-outcome` で追加します。元の決定は不変で、再解釈だけをappend-onlyの署名列へ積みます。
- outcomeは `PROVISIONAL`、`EVIDENCE_BACKED`、`CORROBORATED` を区別します。追認には異なる `observer_id` が必要です。
- 同じ観測者が証拠IDだけを変えて学習を増幅し続けないよう、観測者ごとの総信頼寄与を2.0で上限化します。
- 私的な反省・outcome・観測者IDはsuccessor packageへ入れません。
- cache再構築、整合rollback拒否、改ざん拒否、死亡後更新拒否、checkpoint復元をWhole Stateとtransaction内で監査します。

## 基本操作

```bash
python3 -B run_tukuyo.py --runtime-trust-file /absolute/TRUST_ANCHOR.txt --data /absolute/individual init
python3 -B run_tukuyo.py --runtime-trust-file /absolute/TRUST_ANCHOR.txt --data /absolute/individual reflective-soul-integrate
python3 -B run_tukuyo.py --runtime-trust-file /absolute/TRUST_ANCHOR.txt --data /absolute/individual reflective-soul-deliberate examples/REFLECTIVE_SOUL_OPTIONS.json --context 'self other future conflict'
python3 -B run_tukuyo.py --runtime-trust-file /absolute/TRUST_ANCHOR.txt --data /absolute/individual reflective-soul-outcome DECISION_SHA256 examples/REFLECTIVE_SOUL_OUTCOME.json
python3 -B run_tukuyo.py --runtime-trust-file /absolute/TRUST_ANCHOR.txt --data /absolute/individual reflective-soul-audit
python3 -B run_tukuyo.py --runtime-trust-file /absolute/TRUST_ANCHOR.txt --data /absolute/individual whole-audit
```

optionsとoutcomeの意味注釈はcaller suppliedです。数値範囲・署名・履歴・反実仮想は検査しますが、外界における意味の正しさを独立認証していません。

## 研究との対応

自伝的記憶の再活性化は保持を強める一方で誤認も増やし得るため、既往記録を上書きせず、再解釈を別証明として残します。allostasis/interoceptionは身体コストと切迫度の独立化、他者への責任がconfidenceへ影響する研究は自己・他者葛藤時の保留閾値に対応します。脳と同じ機構だとは主張しません。

アリストテレスの能力としてのpsyche、仏教の非我、日本のtama/mitama、インドのatman、古代エジプトの複数的人格要素は互いに両立する一つの理論ではありません。本版では、固定的な単一実体へ還元しない、生命機能と判断を結ぶ、連続性と変化を区別する、という設計上の問いとしてのみ参照します。

## 未達

意味注釈の独立生成、実世界センサー認証、24時間運転、一般自然言語、自然選択、自己コード改変、第三者再現、workspace復元不具合の根本原因解明は未達です。ChatGPT接続機構は維持していますが、この版の開発・試験で外部ChatGPT教師を実運転した証拠はありません。
