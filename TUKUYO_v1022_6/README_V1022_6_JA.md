# TUKUYO v1022.6（V1022.5 Fusion ＋ claude-patch3〜6）

V1022.5 Fusion に claude-patch3〜6 を積み重ねたものを、**1 つの版**としてまとめました。改良の中身は各パッチの README に書いてあります。この README は、版として使う・採用する・以前の版から移るための説明です。

- 版の名前（`release_revision`）は **v1022.6** です。CLI は、署名した受領書（`META/RELEASE_RECEIPT.json`）に書かれた版の名前を、毎回の出力に載せます。そのため、ご自身の鍵で `--revision v1022.6` として署名し直せば、コードを変えずにその名前が出ます。
- 分類は **EXPERIMENTAL**（実験版）です。V1022.5 Fusion と同じです。
- 版の状態は `STATUS_V1022_6.json`、まだ足りないことは `META/KNOWN_GAPS.json` にあります。

## 0. この版でできること

| | できること | どのパッチ |
|---|---|---|
| 文章題 | 質問が何を聞いているか（残り・はじめ・あげた数・相手の数・別の物・合計）を読んでから答える。読み切れなければ答えない | patch6 |
| 問題の型 | 平均・面積・最小公倍数・数列・割合・あまりと切り上げ・何倍・速さ・1 個の値段・おつりなど。どの答えにも、再計算できる証明が付く | patch3・patch6 |
| 独立の裏付け | 作る側とコードを分けた読み取り器（Parser B）と、数の網羅・役割の監査が、確定の前に答えを確かめる | patch4〜6 |
| 論理・記憶 | 論理の強化（patch3）、「できる」「される」を出来事と数えない（patch4）、時の言葉・主語のない規則（patch6）、多段の記憶（patch3）と言い換え（patch6） | patch3・patch4・patch6 |
| 研究 | 隠れた法則の世界で、情報量で実験を選び、確かめてから法則を主張する。手持ちの言葉で説明できなければ表に切り替え、文法から新しい法則を組み立てて試す | patch5・patch6 |
| 本物の代謝の中の研究 | 家系ごとの装置。確定した法則だけを後継ぎに渡す（使うかは選べる） | patch5 |
| 長時間融合試験 | 推論・教示・自習・代謝・checkpoint・復元・停止注入をランダムに混ぜて回す試験 | patch5（この版では 2 時間 7 分まで。§1） |

## 1. 版としての確認

| 確認 | 結果 |
|---|---|
| 署名と manifest（`verify_release.py`） | 合格（1367 ファイル） |
| 全体テスト | **432/432 合格**（30 分）。patch5 までの 421 件、patch6 の 10 件、版の確認の 1 件（`evidence_v1022_6/selftest_v1022_6.txt`） |
| V1022.6 の長時間融合試験（4 時間の予定） | **完走していません。** 2 時間 7 分のところで、作業環境（クラウドの仮想マシン）が止まって中断しました。そこまでの 1,384 操作（推論 796 問）で、**確信を持った誤り 0、監査の違反 0** でした（`evidence_v1022_6/longrun_v1022_6_gate_note.json`） |
| 予定外の停止のあと | 止まった個体をそのまま調べると、`whole-audit`・代謝の監査（資源の保存を含む）・学習の監査・LLM の監査がすべて合格し、代謝もそのまま続けられました。停止注入ではなく、本当の停止です |
| 未見 F・T（作る前に固定し、1 回だけ回した） | T 38/38、F 72/79、確信を持った誤り 0（どちらも、開発用の問題と同じ私が書いた点に注意。patch6 README §6.1） |
| 研究（新しい鍵の未見世界、1 回だけ） | 新しい法則を 36 個組み立てて確定、誤った主張 0。発明を止めると patch5 の同梱の結果と 480/480 同じ |
| 採用の予行（自分の鍵での署名・patch5 の個体・代謝の付け替え） | すべて合格（`evidence_v1022_6/adoption_rehearsal.log`） |
| リリース zip | 根のフォルダが 1 つ、構造の検査に合格、中の `system/` の署名も合格。作り直しても同じ zip |

- 長時間試験で答えなかった 19 問は、`verified-query`（慎重な検査を足した経路）です。同じ形の問題は patch5 の `verified-query` も答えません。`think` と `llm-ask` は、同じ問題に正しく答えます。答えてはいけない問題 178 問は、すべて答えませんでした。
- 4 時間を完走させるには、作業環境が止まらない状態で 4 時間動かし続ける必要があります。クラウドの作業環境は、何も実行していない間に止まることがあります。手元の機械なら、次のコマンドで同じ試験を回せます。

  ```bash
  python3 -B system/tools/longrun_fusion.py --data ./longrun_individual --runtime-trust-file deliverables/TUKUYO_v1022_6_TRUST_ANCHOR.txt --report longrun.json --minutes 240 --seed 20261008
  ```

## 2. 始め方

Python 3.12 以降と `cryptography` が必要です。個体のデータは、配布フォルダの外に置いてください。

```bash
cd TUKUYO_v1022_6/system
A=../deliverables/TUKUYO_v1022_6_TRUST_ANCHOR.txt
python3 -B tools/verify_release.py . --trusted-pubkey-file $A
python3 -B run_tukuyo.py --runtime-trust-file $A --data ~/tukuyo init
python3 -B run_tukuyo.py --runtime-trust-file $A --data ~/tukuyo think -- 'りんごが12個あります。妹に5個あげました。あげたのは何個？'
python3 -B run_tukuyo.py --runtime-trust-file $A --data ~/tukuyo research-run --world W1
python3 -B run_tukuyo.py --runtime-trust-file $A --data ~/tukuyo whole-audit
```

全体テストは次のとおりです（約 30 分）。

```bash
TUKUYO_TEST_RUNTIME_ANCHOR=$(pwd)/../deliverables/TUKUYO_v1022_6_TRUST_ANCHOR.txt python3 -B -m pytest -q tests -p no:cacheprovider
```

## 3. 採用する（ご自身の鍵で署名する）

同梱のアンカーは、配布物の中にあります。そのため検証で分かるのは「署名のあとで中身が変わっていないこと」だけで、誰が作ったかまでは分かりません。また、patch1〜5 の鍵による相互署名もありません。この版を正式に採用するときは、**ご自身の鍵で署名し直して**ください。

```bash
cd TUKUYO_v1022_6
# 1. 鍵を作る（秘密鍵は配布物の外に置き、配らない）
python3 -B system/tools/claude_patch_sign.py keygen --out-dir ~/tukuyo_publisher_key
# 2. 版の名前を付けて署名する（manifest・受領書・学習済みの種を、この鍵で署名し直す）
python3 -B system/tools/claude_patch_sign.py sign system --private-key ~/tukuyo_publisher_key/patch_signing.key --revision v1022.6
# 3. 公開鍵をアンカーにして、検証する
cp ~/tukuyo_publisher_key/patch_signing.pub deliverables/TUKUYO_v1022_6_TRUST_ANCHOR.txt
python3 -B system/tools/verify_release.py system --trusted-pubkey-file deliverables/TUKUYO_v1022_6_TRUST_ANCHOR.txt
```

- 署名し直すと、元のアンカーでは検証が通らなくなります（`TRUST_ROOT_MISMATCH`）。これは正しい動きです。
- 新しく作る個体も、以前の版の個体も、学習済みの種の署名の確認が通ります（今の受領書の鍵と、これまでの鍵を記録した `META/PATCH_LINEAGE_v1022_*.json` の鍵を受け付けます）。
- この手順を、使い捨ての鍵で最初から最後まで試した記録が `evidence_v1022_6/adoption_rehearsal.log` です（台本は `adoption_rehearsal.sh`）。

## 4. 以前の版から移る

| 個体 | すること |
|---|---|
| 新しい個体 | 何もいりません |
| patch5 で作った個体 | そのまま使えます（`whole-audit`・`research-audit`・記憶・推論まで確認）。patch3・patch4・V1022.5 Fusion の個体も、同じ鍵で署名された種なので同じ扱いのはずですが、確かめたのは patch5 の個体です |
| **代謝（`metabolism-init`）を動かしている個体** | 署名の鍵が変わったので、子の実行に使う信頼アンカーを **1 回だけ明示的に付け替えます**。付け替える前は、子の実行が `EXTERNAL_RUNTIME_TRUST_MISMATCH` で止まります（安全側に止まる） |

```bash
python3 -B system/run_tukuyo.py --runtime-trust-file NEW_ANCHOR --data D runtime-trust-rebind --previous-trust-file OLD_ANCHOR
```

- patch5 で記録した研究の探索は、そのまま再生して照合できます（発明なしで記録された探索は、発明なしで再生します）。
- 研究の状態の主張の境界は、次に保存するときに v1022.6 のものに変わります。

## 5. リリース zip

- `evidence_v1022_6/build_release_zip.py` で作ります。根のフォルダは 1 つ（`TUKUYO_v1022_6/`）、項目は名前順、時刻と権限は固定、キャッシュは入れません。同じ木からは同じ zip ができます（同じ zlib の場合）。
- 作ったあとに、`system/tools/strict_zip_preflight.py`（根が 1 つ、危険なパスなし、リンクなし、CRC）と、zip の中の `system/` の署名の検証を自動で行います。
- この版の zip は `TUKUYO_v1022_6.zip` です。zip の中にその zip 自身のハッシュは書けないので、大きさと sha256 は、リポジトリの README に書いてあります。

## 6. 版の中身

- **土台**：V1022.5 Fusion（V1022.4 の復元・停止復旧・子個体監査 ＋ claude-patch2 の文章題・論理・記憶・複数教師・自習）
- **claude-patch3**：数量・時間・暦・割合、多段の記憶、論理の強化、教える対話
- **claude-patch4**：意味の関門（数の網羅・役割の監査・作る側と別に書いた Parser B）
- **claude-patch5**：V1023r 研究プレビュー（隠れた法則の世界・実験の選び方・方法の切り替え・再現試験・反証・記憶）、本物の代謝の中の研究ニッチ、長時間融合試験、Parser B の拡張
- **claude-patch6**：質問の役割を読む場面モデル、問題の型と証明、patch5 の確信を持った誤りの修正、英語の数詞、論理と記憶の言い換え、文法から法則を組み立てる研究、研究エンジンの高速化、長時間試験の厳密な採点
- **v1022.6 として**：CLI の版の名前を署名した受領書から読む、`STATUS_V1022_6.json`、`META/KNOWN_GAPS.json` の追記、版の確認テスト（`tests/test_v1022_6.py`）、採用の予行、決まった形のリリース zip
- patch5 からの差分は `claude_patch6_vs_patch5.diff` にあります。

## 7. 限界

- 長時間融合試験は、この版では 2 時間 7 分までです（4 時間の予定が、作業環境の停止で中断）。24 時間の運転も、まだ実施していません。
- 文章の読み取りは、今も有限の型です。読めないときは答えません。
- 未見の評価（F・T）も、開発用の問題も、Parser B の新しい読み取り器も、作る側と同じ私が書きました。F・T の多くは開発用の問題と同じ型です。別の人が書いた問題での評価は、まだありません。
- 研究の文法と段 5 の世界は、私が設計しました。子が新しい種類の法則を作るわけではありません。世界も 1 種類です。
- 署名の鍵は、patch6 で新しくしたパッチ鍵です。以前の鍵による相互署名はありません。発行者の連続性は、配布物の外での信頼（またはご自身の鍵での署名）に頼ります。
- 本物の LLM での効果は測っていません。一般知能・自己コード改変・意識・文字どおりの生命の成立は主張しません。
