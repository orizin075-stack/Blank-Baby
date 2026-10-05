# TUKUYO v984 — Bounded Full-Runtime Fork Divergence Assay

v981のdeep-self branchだけではなく、同一のlive individual snapshotを二つの独立data rootへ複製し、**別Pythonプロセス**で異なる経験系列とorganism tickを与える。各branchでheart、soul、organism、homeostasis、whole unified stateを実際に更新し、両branchの監査が通ったまま状態・選択・maintenance intentが分岐することを測定する。

`full-runtime-fork-assay` は親個体を直接分岐稼働させる機能ではなく、隔離された一時コピー上でのbounded assayである。したがって「永続並列エージェントが実運用で成立した」「意識が分裂した」「魂が複製された」という主張は行わない。一方、v983まで未検証だった **full runtime stateの別プロセス分岐** は、whole/organism/heart/soul/homeostasisを含む範囲で直接試験可能になった。

主なコマンド:

```bash
python3 -B run_tukuyo.py --data ../TUKUYO_DATA full-runtime-fork-assay
python3 -B run_tukuyo.py --data ../TUKUYO_DATA full-runtime-fork-audit
```
