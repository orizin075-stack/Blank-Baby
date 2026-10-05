# TUKUYO v967 Unified System

v967は、v943〜v966で追加された機能を1つのCLIと1つのデータrootへ統合した実行版です。過去のモジュールをZIPに置くだけではなく、研究agenda、外部観測campaign、meta-improver比較、public inheritance、primitive/family promotion、open-ended assay、個体・意味処理・訂正系を同じ `run_tukuyo.py --data <ROOT>` から操作します。

## 主な統合点
- `system-status`: 個体状態・統合ledger・v958 primitive registry・v962 inherited knowledge・v967 family registryをまとめて表示
- `agenda-propose` / `agenda-authorize`: v959研究agenda
- `campaign-run`: v960外部観測付き仮説切替
- `improver-compare`: v961改善器比較
- `inherit-export/import/eval`: v962 public knowledge継承
- `family-propose` / `family-promote-verify` / `family-eval`: v965/v966 family拡張
- `reproduce-current`: v963 fresh-process再現（外部runtime trust anchor必須）
- 既存の `ep-*`, `primitive-*`, `open-ended-assay`, `teach`, `eval`, `social`, `lab` も同じCLIで維持

研究イベントは `<data>/research_v967/INTEGRATED_LEDGER.json` にhash-chainで記録され、改竄時は `system-status` が失敗します。外部Authorityの秘密鍵は配布物にもdata rootにも置きません。

## 起動
```bash
python3 -m pip install -r requirements.txt
python3 -B run_tukuyo.py --data ../TUKUYO_v967_DATA init --individual-id TUKUYO-v967-001
python3 -B run_tukuyo.py --data ../TUKUYO_v967_DATA system-status
python3 -B run_tukuyo.py --data ../TUKUYO_v967_DATA chat
```

## claim boundary
これはbounded autonomous-research systemの統合版です。独立第三者再現、30日wall-clock、true open-ended evolution、general L5/L6は未確立です。
