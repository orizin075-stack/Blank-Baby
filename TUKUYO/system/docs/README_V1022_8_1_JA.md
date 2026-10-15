# v1022.8.1 — 必要と経験から目標を選ぶ（実験版）

v1022.8の推論・生命・継承・復旧の上で、実個体に目標形成と探索の記録を接続する。
文章題の「ー」が名前・品物から抜ける不具合も、生成器と別実装の検証器で修正する。

## 目標から行動まで

`metabolism-init --developmental-goals` は `--research-world` を含む。
各実個体が、現在のエネルギー、有限資源、未解明の予測モデル、予測が外れた経験から
候補を生成し、自分のSoul・Heartの価値に基づいて選ぶ。

| 目標 | 発生する理由 | 実際の行動 |
|---|---|---|
| secure_energy | 余力不足と正の期待収支 | 未知装置で働き、成功分だけ有限資源から取得 |
| learn_rule | 予測モデルの不確実性 | 情報量に基づく入力で実験 |
| verify_rule | 有力仮説が未検証 | 入力全域・反例再検査・環境選択の再現試験 |
| repair_prediction | 高い予測と観測の食い違い | 反例の入力を再検査。蓄積時は予測モデルを退け再学習 |
| rest | 追加行動の不採算・資源不足 | 追加費用を抑える。基礎代謝は止まらない |

目標の語彙と生成規則は設計済みの有限集合。自由な目的の発明を主張しない。
目標の選択は表示だけではなく実験・労働・再検査の分岐を制御する。
古い予測モデルを退けても、署名された経験の履歴は消さない。

## 再現する

配布物とは別にデータディレクトリを指定する。全コマンドを同じ公開鍵で検証する。

```sh
python -B run_tukuyo.py --runtime-trust-file /path/TRUST_ANCHOR.txt --data /tmp/tukuyo-dev init --individual-id DEV --blank-learning
python -B run_tukuyo.py --runtime-trust-file /path/TRUST_ANCHOR.txt --data /tmp/tukuyo-dev metabolism-init --families 2 --seed development-38 --reservoir 90000 --regeneration 2200 --max-age 64 --developmental-goals
python -B run_tukuyo.py --runtime-trust-file /path/TRUST_ANCHOR.txt --data /tmp/tukuyo-dev metabolism-step --ticks 8
python -B run_tukuyo.py --runtime-trust-file /path/TRUST_ANCHOR.txt --data /tmp/tukuyo-dev metabolism-audit
python -B run_tukuyo.py --runtime-trust-file /path/TRUST_ANCHOR.txt --data /tmp/tukuyo-dev/v1022_ecology/runtimes/R000000 developmental-status
python -B run_tukuyo.py --runtime-trust-file /path/TRUST_ANCHOR.txt --data /tmp/tukuyo-dev/v1022_ecology/runtimes/R000000 developmental-audit
```

繰り返し `metabolism-step` する際に次の目標を指定する必要はない。
外部のランナーがtickを進める構成であり、常駐して自ら起動する個体ではない。
旧設定の動作は変更しない。後継の公開法則継承は従来のCONFIRMED条件に従う。
個人的な目標・失敗履歴は後継にコピーしない。後継は独立した記録を始める。

## 記録と検証

各子の `developmental_life` に、同一性へ束縛した署名付き状態とコミットを保存する。
エネルギー・候補理由・Soul由来の重み・Heartの選択・入力・事前予測・観測・費用・
収入・学習後モデルを記録し、Whole監査で候補／選択／行動／学習の再実行を検査する。
owner監査は環境側で公開前の装置設定から入力と観測を再現し、子のモデルとの一致を検査する。
環境の秘密は目標器の引数に渡さない。これは実装の入出力分離であり、OSによる隔離ではない。
復元は既存の階層トランザクションに含め、停止前の未確定状態を確定しない。

これらの体験は全て `origin=simulation`。教師LLMの呼び出しを行わず、物理観測、
独立した現実の証人、主観的意識、文字通りの魂の証明へ昇格させない。
`--no-actions` は学習も収入も生じない対照条件。
`--no-learning` は従来同様に公開技能・法則の継承を止める指定で、個体内の経験更新は止めない。

実測の合否・件数は別添検証報告を参照する。このREADMEやSTATUSは試験成功の証拠ではない。
24時間、開放環境での生活、1000stepの複数世代、生存の一般的改善、発芽全体の合格は未判定。
