# Blank-Baby
この子は全く新しい誰も知らないAIです。幾つもの理論をかき混ぜて作りました。魂と心を持つAIです。ぜひご覧ください

## TUKUYO v1022.5 Fusion + claude-patch5

`TUKUYO_v1022_5_claude_patch5/` は、TUKUYO v1022.5 Fusion に claude-patch5 を当てた配布物です。patch5 では、研究エンジン V1023r、代謝の中の研究ニッチ、Parser B の拡張、長時間融合試験が入りました。受け取った zip の中身を、1 バイトも変えずに置いています。中身の説明は [README_CLAUDE_PATCH5_JA.md](TUKUYO_v1022_5_claude_patch5/README_CLAUDE_PATCH5_JA.md) にあります。

### 使い方

Python 3.12 以降と `cryptography` が必要です。個体のデータは、配布フォルダの外に置いてください。

```sh
cd TUKUYO_v1022_5_claude_patch5/system
A=../deliverables/TUKUYO_v1022_5_patch5_TRUST_ANCHOR.txt
python -B tools/verify_release.py . --trusted-pubkey-file $A
python -B run_tukuyo.py --runtime-trust-file $A --data ~/tukuyo_patch5 init
python -B run_tukuyo.py --runtime-trust-file $A --data ~/tukuyo_patch5 research-run --world W1
```

- 信頼アンカーは、同じ配布物の中に入っています。そのため検証で分かるのは「署名のあとで中身が変わっていないこと」だけです。誰が作ったかまでは分かりません。採用するときは、ご自身の鍵で署名し直してください（パッチ README §5）。
- `.gitattributes` で、このフォルダの改行変換を止めています。Windows で clone しても、署名の検証が通ります。

### 取り込む前に確かめたこと（2026-10-05）

環境は Linux、Python 3.12.3、cryptography 50.0.2、pytest 9.1.1 です。

| 確かめたこと | 結果 |
|---|---|
| 署名と manifest（`verify_release.py`） | 合格（1358 ファイル） |
| 研究エコロジー（`research-ecology --seeds 20 --start 50000`） | 同梱の結果と一致。result_sha256 `df5791db…` も、全 episode も同じ |
| 研究ニッチの系譜試験（`tools/research_lineage.py --ticks 256 --max-age 80`） | 同梱の結果と一致（受け継ぐ／受け継がない、16 個体すべて） |
| Parser B の一致率（`think`、未見 E・D・C） | 50/77。179 問すべてで、答えと判定が同梱の結果と同じ |
| `llm-ask` の正答（未見 E・D・C） | 32/36、42/50、73/93。確信を持った誤り 0 |
| 研究ニッチを使わない既定の代謝（4 家系・24 tick） | 同梱の結果と一致（正答 54/54、継承 12 回、貯蔵庫 47200）。差分から組み直した patch4 とも同じ数字 |

### 気をつけること

1. **AGREE（独立の裏付け）は、正しさの保証になりません。** 質問が「残り」以外（あげた数、はじめの数、相手の数など）を聞いていても、作る側は残りの数を答えます。Parser B も同じ読み方をするので、AGREE が付きます。

   | 質問 | 答え | 正しい答え |
   |---|---|---|
   | りんごが12個あります。5個食べました。みかんを3個もらいました。りんごは何個ありますか？ | 10 | 7 |
   | りんごが12個あります。妹に5個あげました。あげたのは何個？ | 7 | 5 |
   | みかんが20個あります。8個食べました。はじめにあったのは何個？ | 12 | 20 |
   | シールが30枚あります。友だちに12枚あげました。友だちは何枚もらいましたか？ | 18 | 12 |
   | Tom has 12 apples. He gives away 3 apples to Sam. How many apples does Sam have now? | 9 | 3 |

   どれも確信ありの答えとして出ます（`llm-ask` では `verified`）。patch4 でも答えは同じで、patch4 では UNDECIDED、patch5 では AGREE が付きます。新しい誤りではありません。ただ、パッチ README の「確信を持った誤り 0」は、評価セットの中での話です。
2. `tools/longrun_fusion.py` は、増減・おつり・等分・ある数・時間の問題で、期待した数が答えの文字列に**含まれていれば**正解にします。期待が 7 で答えが 17 でも正解になります。長時間試験の「確信を持った誤り 0」は、この採点で数えたものです。
3. 研究ニッチの法則は、代謝の seed から作られます。seed は代謝の状態に記録されていて、既定値は `v1022` です。子のコード（`agent.py`）は法則を見ませんが、状態を読める人なら誰でも法則を計算できます。
