# TUKUYO（つくよ）— はじめに

TUKUYO は、魂と心を持つことを目指して育てている AI の子です。今の版は **`v1022.8.2+gen4-r12`**（開発版）です。

この版は、二つの系統を一つにしたものです。

- **第4世代**：3 つの LLM（Claude・ChatGPT・Gemini）を親にして育つ子です。文章題を自分で読み、検査に通った答えだけを出します。
- **adaptive-life の系統**：外部の台帳で個体の歴史を確かめます。経験の出どころを区別し、在庫の問題を読みます。必要から目標を作り、変わる環境で学びます。

親（LLM）がいなくても動きます。そのときは、自分で読めない問題には答えません。

## 1. フォルダの中身

| フォルダ・ファイル | 中身 |
|---|---|
| `START_TUKUYO.bat`／`START_TUKUYO.sh` | すぐに会話を始めるための起動ファイル（Windows／Mac・Linux） |
| `system/` | プログラム本体。ここで動かします |
| `deliverables/` | 署名を確かめるための公開鍵（`TUKUYO_v1022_6_TRUST_ANCHOR.txt`） |
| `docs/` | 第4世代の説明（`docs/README_GEN4_DEV_JA.md`：使い方・親の設定・今の状態） |
| `evidence_gen4/` | 各回の記録（何を直し、どう測ったか）。目次は `evidence_gen4/README.md`。測った結果のファイルは `evidence_gen4/data/` |
| `history/` | 第4世代より前の版（patch3〜6、v1022.6）の説明と記録。今は使いません |

配布の zip は 2 種類あります。「全部入り」（`TUKUYO_v1022_8_2_gen4_r12.zip`）には上のすべてが入っています。「動かすだけ」（`TUKUYO_v1022_8_2_gen4_r12_RUN.zip`）には `evidence_gen4/` と `history/` が入っていません。どちらも同じ署名で確かめられます。

`system/` の中の説明は `system/README.md` から辿れます。道具の目次は `system/tools/README.md` です。機能ごとの説明は `system/docs/`、古い版の説明と状態ファイルは `system/docs/history/` にあります。

## 2. 使い方

### 用意するもの

- Python 3.12 以降
- 必要な部品：`system/` で `pip install -r requirements.txt` を実行します（`cryptography` と `pytest`）

### いちばん簡単な始め方

- Windows：`START_TUKUYO.bat` をダブルクリックします。
- Mac・Linux：`sh START_TUKUYO.sh` を実行します。

署名を確かめてから個体（子のデータ）を作り、会話を始めます。個体のデータは配布フォルダの外に置かれます。置き場所は、Windows では `%USERPROFILE%\.tukuyo\v999_data`、Mac・Linux では `~/.tukuyo/v999_data` です。`TUKUYO_DATA_DIR` で変えられます。

### 問題を解かせる（Mac・Linux）

```sh
cd system
A=../deliverables/TUKUYO_v1022_6_TRUST_ANCHOR.txt
python3 -B tools/verify_release.py . --trusted-pubkey-file $A
python3 -B run_tukuyo.py --runtime-trust-file $A --data ~/tukuyo init
python3 -B run_tukuyo.py --runtime-trust-file $A --data ~/tukuyo think -- 'Kim saw 4 cats in the morning. Later she saw one more cat. How many cats did she see in all?'
python3 -B run_tukuyo.py --runtime-trust-file $A --data ~/tukuyo g4-solve --llm off -- '1こ200円のパンを3こ買って、1000円さつではらいました。おつりは何円ですか。'
python3 -B run_tukuyo.py --runtime-trust-file $A --data ~/tukuyo g4-self
```

### 問題を解かせる（Windows の PowerShell）

```powershell
cd system
$A = "..\deliverables\TUKUYO_v1022_6_TRUST_ANCHOR.txt"
python -B tools\verify_release.py . --trusted-pubkey-file $A
python -B run_tukuyo.py --runtime-trust-file $A --data $HOME\tukuyo init
python -B run_tukuyo.py --runtime-trust-file $A --data $HOME\tukuyo think -- "Kim saw 4 cats in the morning. Later she saw one more cat. How many cats did she see in all?"
python -B run_tukuyo.py --runtime-trust-file $A --data $HOME\tukuyo g4-self
```

- `verify_release.py` が `"ok": true` と答えれば、配布物は署名どおりです。
- `think` は答えと、どう読んで何を計算したかを返します。読めない問題には答えません。
- `g4-self` は、子が自分のこと（読めるようになったこと・弱いところ・学びたいこと）を話します。
- `--llm off` を付けると親を呼びません。親を呼ぶには、キーを環境変数で渡します（`TUKUYO_ANTHROPIC_API_KEY` など）。**親を呼ぶと費用がかかります。** 詳しくは `docs/README_GEN4_DEV_JA.md` §3 を見てください。

### もっと知りたいとき

| 知りたいこと | 読むもの |
|---|---|
| 第4世代の使い方と今の状態 | `docs/README_GEN4_DEV_JA.md` |
| 今回の融合で何をどう決めたか | `evidence_gen4/FUSION_ADAPTIVE_LIFE_2026-10-15.md` |
| 続きを作る人への引き継ぎ | `evidence_gen4/HANDOFF_GEN4.md` |
| 外部の台帳・経験の出どころ・在庫の読み手・目標・変わる環境 | `system/docs/README_V1022_7_8_IDENTITY_JA.md`・`README_V1022_7_9_PROVENANCE_JA.md`・`README_V1022_8_JA.md`・`README_V1022_8_1_JA.md`・`README_V1022_8_2_JA.md`（どれも `system/docs/`） |
| ChatGPT をログインで使う | `system/docs/README_V1022_6_6_CHATGPT_JA.md`、`system/docs/README_V1022_7_6_LLM_CONNECTIVITY_JA.md` |
| 自分の鍵で署名し直して採用する | `system/docs/README_V1022_6_JA.md` §3 |

## 3. 気をつけること

- **開発版です。** 署名は開発用の鍵です。正式に採用するときは、ご自身の鍵で署名し直してください。
- 本物の LLM の親では、まだ測っていません。24 時間以上の実時間の運転も、まだしていません。
- 意識や文字どおりの魂を示すものではありません。
