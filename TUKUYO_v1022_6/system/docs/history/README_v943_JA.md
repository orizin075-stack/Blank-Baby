# TUKUYO v943 — 完全性検査・自己訂正・能動質問の結合試作

## 実装範囲
既存v941の個体、意味学習、他個体・社会・集団・系譜・生態・進化、v937隔離研究機能を維持。追加したv943 `epistemic` は**既存のv838/v840で実際に学習した演算子**を読み、矛盾観測に対して利用者向け評価を一時停止し、既知のADD/MUL/SUB/MAX/MINから区別質問を生成する。観測者・再評価者・承認者の別公開鍵の受領書がなければ訂正は起きない。元の署名済み学習状態を変更せず、独立の追記台帳と実行Facade上のoverrideで訂正する。

- 旧能力の有効化・訂正はこの `run_tukuyo.py` **CLI経由だけを保証**する。内部のv838を直接呼ぶ古いコードはoverrideしない。完全な全経路retractionではない。
- native learned capabilityの旧受領書は既存のローカル署名であり、外部評価済みとは数えない。
- 外部3役の鍵を同じ管理者が用意したテストは署名役割の分離のみ証明し、独立第三者による評価は別途必要。
- 一回の2件サンプル（矛盾観測＋能動質問）は一般意味能力を検証しない。表現発明や人間相当の自由会話は実装していない。
- この版は30日実時間稼働の結果を主張しない。鍵epochの旧版との暗号学的ローテーションも主張しない。

## 依存と起動
Linux/macOS/Windows WSL2上のPython3.10+。

```sh
python3 -m pip install -r requirements.txt
python3 -B run_selftest.py
python3 -B run_tukuyo.py --data ../TUKUYO_v943_DATA init
python3 -B run_tukuyo.py --data ../TUKUYO_v943_DATA teach examples/SEMANTIC_TEACH_SAMPLE.json --apply
python3 -B run_tukuyo.py --data ../TUKUYO_v943_DATA eval '2 とけあわせる 3'
```

## v943の能動質問・訂正
`--data` は実行コードの**外部**の永続ディレクトリを指定。外部公開鍵と各秘密鍵も**配布物・個体データとは別の場所**に保存する。

```sh
python3 -B run_tukuyo.py --data ../TUKUYO_v943_DATA ep-init --pin-out ../TRUST/local.pub
python3 -B tools/external_actor.py generate --private-out ../TRUST/observer.key --public-out ../TRUST/observer.pub
python3 -B tools/external_actor.py generate --private-out ../TRUST/evaluator.key --public-out ../TRUST/evaluator.pub
python3 -B tools/external_actor.py generate --private-out ../TRUST/authority.key --public-out ../TRUST/authority.pub
python3 -B run_tukuyo.py --data ../TUKUYO_v943_DATA --ep-trust-dir ../TRUST ep-import とけあわせる
printf '{"a":3,"b":4,"expected":12}\n' > ../contradiction.json
python3 -B run_tukuyo.py --data ../TUKUYO_v943_DATA --ep-trust-dir ../TRUST ep-challenge とけあわせる ../contradiction.json
```

生成された `challenge_sha256`・`query_sha256`・`individual_id`・質問のa,bを用い、外部観測者から観測値を取得して次のJSONを作る。質問に回答不能なときは `observed: null` とする。回答不能なら昇格しない。

```json
{"schema":"tukuyo.v943.observation/1","challenge_sha256":"<実際の出力>","query_sha256":"<実際の出力>","a":-5,"b":-5,"observed":25,"individual_id":"<実際の個体ID>"}
```

```sh
python3 -B tools/external_actor.py sign --private ../TRUST/observer.key --payload ../observation_payload.json --out ../observation_signed.json
python3 -B run_tukuyo.py --data ../TUKUYO_v943_DATA --ep-trust-dir ../TRUST ep-observe とけあわせる ../observation_signed.json
python3 -B run_tukuyo.py --data ../TUKUYO_v943_DATA --ep-trust-dir ../TRUST ep-options とけあわせる
```

`ep-options`が出す再計算済みの候補1件を `eval_payload.json` として保存し、**独立した評価者**がその内容を検査して署名する。

```sh
python3 -B tools/external_actor.py sign --private ../TRUST/evaluator.key --payload ../eval_payload.json --out ../eval_signed.json
```

評価受領書ファイルの正規化JSON（空白なし・ソート済み・Unicode非エスケープ）のSHA-256を`evaluator_receipt_sha256`として、以下の承認payloadを**別の昇格権限者**が署名する。

```json
{"schema":"tukuyo.v943.promotion_authority/1","challenge_sha256":"<eval_payloadから>","observation_sha256":"<eval_payloadから>","evaluator_receipt_sha256":"<sha256 of canonical signed eval JSON>","new_operator":"MUL","individual_id":"<eval_payloadから>"}
```

```sh
python3 -B tools/external_actor.py sign --private ../TRUST/authority.key --payload ../approval_payload.json --out ../approval_signed.json
python3 -B run_tukuyo.py --data ../TUKUYO_v943_DATA --ep-trust-dir ../TRUST ep-revise とけあわせる ../eval_signed.json ../approval_signed.json
python3 -B run_tukuyo.py --data ../TUKUYO_v943_DATA --ep-trust-dir ../TRUST ep-audit
python3 -B run_tukuyo.py --data ../TUKUYO_v943_DATA --ep-trust-dir ../TRUST eval '2 とけあわせる 3'
```

元の学習データの再評価と正規外部holdoutの検証は別途必要。訂正済みの2件以外に新演算子を一般化していない。

`TUKUYO_v943_DATA/epistemic/events`にはIMPORT→CHALLENGE→OBSERVATION→REVISEの4つの署名付きハッシュ連鎖、`objects`には元観測・仮説・質問・3署名受領書が内容アドレスで残る。証拠欠落・改竄・別個体・再署名/別鍵・受領書使い回しは監査時に拒否される。

## 配布物の真正性
単体ZIPは別途配る `TUKUYO_v943_TRUST_ANCHOR.txt` で検証。最新の完全履歴を含むアーカイブは `VERIFY_COMPLETE.py` と**外部**公開鍵で正確な全ファイル集合を検証。これは今回生成した**新しいE8開発者によるスナップショット認証**であり、過去E1〜E4の暗号学的な鍵継続を事後的に証明するものではない。

**重要：旧学習のholdout生データはv840記録では再取得できない。新たな観測2件はグローバルな演算子置換を正当化しないため、v943は署名で承認された2入力だけを訂正し、それ以外の入力はOPENを返す。旧trainingと同じ入力に異なるラベルを与える矛盾は、別の証拠裁定機能がない限り拒否する。**
