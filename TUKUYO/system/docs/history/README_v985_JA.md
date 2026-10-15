# TUKUYO v985 — Evidence-Bounded Narrative Purpose Loop

v978の単発experience→meaning→goalを拡張し、複数エピソード、意味群、反復theme、vow/scar、emotion、実organism由来homeostasisをまとめて、**経験→意味→自己物語→高位目的**の閉ループとして統合する。

`purpose-integrate` はheartのepisodic meaningsを再集計し、意味別・theme別の証拠量を保持したまま、`PRESERVE_INTEGRITY / SEEK_KNOWLEDGE / MAINTAIN_RELATIONSHIPS / SELF_MAINTENANCE / PRESERVE_TRUTH` の5候補を決定論的に比較する。選ばれたpurposeは外部行動を自動実行せず、証拠に紐づく高位方針として記録される。新しい経験やhomeostasis変化で優先目的が変わった場合はrevision_countが増え、変更前後がhash-chain eventとして残る。

自己物語は反復theme・vow・scarを直接証拠として保持し、単なる自由文自己解釈ではなく検査可能な構造として保存する。whole stateはv985 state/event hashesを束縛し、改ざんは`purpose-audit`と`whole-audit`の双方で検出される。

これは機能的な自己物語・目的形成であり、意識、文字通りの魂、自由意志、一般L5/L6、open-ended goal inventionの証明ではない。外部行動や自己改変の自動昇格も行わない。

主なコマンド:

```bash
python3 -B run_tukuyo.py --data ../TUKUYO_DATA purpose-integrate
python3 -B run_tukuyo.py --data ../TUKUYO_DATA purpose-status
python3 -B run_tukuyo.py --data ../TUKUYO_DATA purpose-audit
python3 -B run_tukuyo.py --data ../TUKUYO_DATA status
python3 -B run_tukuyo.py --data ../TUKUYO_DATA system-status
```
