# TUKUYO v1022.8.2+gen4-r12 — プログラム本体

ここがプログラムの本体です。全体の説明と始め方は、一つ上の `../README.md` にあります。

今の版は `v1022.8.2+gen4-r12` です。第4世代の第11回（`v1022.8.2+gen4-r11`）に、adaptive-life の系統（`v1022.8.2-adaptive-life`）を融合しました。adaptive-life の系統は、こちらの第7回（r7）から分かれて独自に進んだものです。融合の記録は `../evidence_gen4/FUSION_ADAPTIVE_LIFE_2026-10-15.md` にあります。意識や文字どおりの魂を示すものではありません。

## ここにあるもの

| ファイル・フォルダ | 中身 |
|---|---|
| `run_tukuyo.py` | すべてのコマンドの入口（`python3 -B run_tukuyo.py --help`） |
| `START_TUKUYO.sh`／`START_TUKUYO.bat` | 署名を確かめ、初めてなら個体を作り、会話を始めます |
| `run_selftest.py` | 自己テスト |
| `STATUS.json` | 版の状態（主張の境界つき） |
| `requirements*.txt` | 必要な部品（基本は `requirements.txt`。ChatGPT と Gemini の親を使うときは `requirements-dev.txt`） |
| `src/` | ソース（第4世代は `src/tukuyo_g4/`、v1022 の核は `src/tukuyo_v1022/` など） |
| `tests/` | テスト（`python3 -B -m pytest -q`） |
| `tools/` | 署名の確認（`verify_release.py`）・計測・実験の道具（目次は `tools/README.md`） |
| `examples/` | 例のファイル |
| `META/` | 署名つきの manifest と受領書。これを変えると起動の検査で止まります |
| `docs/` | 機能ごとの説明（下の表） |
| `docs/history/` | 古い版（v943〜v1022.6.5）の説明・状態・道筋。今は使いません |
| `history/`、`research_layers/` | 過去の研究の記録（起動の検査が使います） |

## よく使うコマンド

`A=../deliverables/TUKUYO_v1022_6_TRUST_ANCHOR.txt`、`D=個体のフォルダ`（配布フォルダの外）とします。

| すること | コマンド |
|---|---|
| 配布物の署名を確かめる | `python3 -B tools/verify_release.py . --trusted-pubkey-file $A` |
| 個体を作る | `python3 -B run_tukuyo.py --runtime-trust-file $A --data $D init` |
| 問題を考える（核と第4世代） | `... --data $D think -- '問題'` |
| 第4世代だけで解く | `... --data $D g4-solve --llm off -- '問題'` |
| 子が自分を語る | `... --data $D g4-self` |
| 親の設定を見る（費用なし） | `... --data $D g4-parents` |
| 全体の監査 | `... --data $D whole-audit` |
| 生態系 | `metabolism-init`・`metabolism-step`・`metabolism-audit`（選択肢は `docs/README_V1022_8_2_JA.md` と `../docs/README_GEN4_DEV_JA.md` §2） |
| 外部の台帳 | `identity-ledger-*`（`docs/README_V1022_7_8_IDENTITY_JA.md`） |
| 経験の出どころ | `soul-provenance-*`（`docs/README_V1022_7_9_PROVENANCE_JA.md`）、`experience-provenance-status` |

## 機能ごとの説明（`docs/`）

| 説明 | 中身 |
|---|---|
| `README_V1022_8_2_JA.md` | 変わる環境と、暫定の文化の継承（adaptive-life） |
| `README_V1022_8_1_JA.md` | 必要と経験から目標を選ぶ（adaptive-life） |
| `README_V1022_8_JA.md` | 人物・品物・時点を追う在庫の読み手（adaptive-life） |
| `README_V1022_7_9_PROVENANCE_JA.md` | 魂の学習での経験の出どころの区別（adaptive-life） |
| `README_V1022_7_8_IDENTITY_JA.md` | 共有する外部の台帳と、数の分からない量の検査（adaptive-life） |
| `README_V1022_7_7_EXPERIENTIAL_SOUL_JA.md` | 経験による魂 |
| `README_V1022_7_6_LLM_CONNECTIVITY_JA.md`、`README_V1022_6_6_CHATGPT_JA.md` | ChatGPT の API キーとログイン |
| `README_V1022_7_EVIDENCE_BOUND_SOUL_JA.md`、`README_V1022_6_8_FUNCTIONAL_SOUL_JA.md`、`README_V1022_6_9_REFLECTIVE_SOUL_JA.md` | 証拠に縛られた魂・機能としての魂・振り返る魂 |
| `README_V1022_7_1_*`〜`README_V1022_7_3_*` | 意味の真偽・観測装置・証拠による判断 |
| `README_V1022_6_7_BRAIN_JA.md` | 頭脳 |
| `README_V1022_6_JA.md` | v1022.6 の版（自分の鍵で署名し直して採用する手順は §3） |

第4世代（`src/tukuyo_g4/`）の説明は `../docs/README_GEN4_DEV_JA.md` にあります。各回の記録は `../evidence_gen4/` にあります。これまでの長い版の説明（第11回まで）は `docs/history/README_SYSTEM_UNTIL_r11.md` に残しました。
