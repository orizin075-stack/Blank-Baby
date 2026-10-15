# TUKUYO V1022.6.7 Brain Experimental

V1022.6.6 からの派生版です。頭脳面では、条件を補う会話の保存と、教師から学んだ同じ解法の統合を追加しました。検証の実測値は配布 ZIP 外の検証報告・evidence にあります。過去の版の文書と数値は歴史資料です。

## 条件を補う会話

```bash
python -B run_tukuyo.py --runtime-trust-file /absolute/path/TRUST_ANCHOR.txt --data /absolute/path/individual init
python -B run_tukuyo.py --runtime-trust-file /absolute/path/TRUST_ANCHOR.txt --data /absolute/path/individual clarify-start '制約: A+B=18。Aは何？'
python -B run_tukuyo.py --runtime-trust-file /absolute/path/TRUST_ANCHOR.txt --data /absolute/path/individual clarify-add 'B=2*A'
python -B run_tukuyo.py --runtime-trust-file /absolute/path/TRUST_ANCHOR.txt --data /absolute/path/individual clarify-status
python -B run_tukuyo.py --runtime-trust-file /absolute/path/TRUST_ANCHOR.txt --data /absolute/path/individual clarify-audit
```

最初は答えを保留し、独立した条件を求めます。追加条件の後は同じ目標 A を解き直して 6 を返します。別プロセスでも会話を継続できます。追加条件は利用者が与える前提であり、外界で正しい事実だと認証したものではありません。回答の `verified` は、指定された有限の一次制約からの結論を別の字句解析器と証明検査で確認した意味です。

自然文は既存の限定された合計・平均・倍・差・単位の構文を利用できます。一般会話の意味理解ではありません。条件は1回1文、最大8回、16セッションです。元の目標を変える入力、非線形条件、矛盾、未証明の数量領域を拒否します。拒否した更新は元の会話へ反映しません。受理した条件・証明は署名付き commit と Whole State に束縛し、監査で再実行します。

保留する場合も、全条件を満たす二つの例で目標の値が異なることを別実装で検査します。`ambiguity_proof` は原文と単位に束縛した二つの例です。人数・個数が負になる例や条件を満たさない例は根拠にせず、検査できない場合は会話の更新を拒否します。

## 学んだ解法の統合

同じ文章の数値違いから学ぶ仕組みを維持し、変数名・式の左右・項の順序が異なる同じ方法を統合します。多項式の正規化は次数4、128項などの上限があります。入力中の数値の役割、単位、整数・符号属性、目標、引用した原文が一致する範囲だけを対象にします。範囲外の式は従来の厳密な一致へ戻ります。任意のプログラムの等価判定や、一般的な言い換え学習ではありません。

年・順位など、式の入力として束縛していない数値は固定します。その数値を変えた文章は新しく読み直す必要があります。percent と通常の量を入れ替える転移も拒否します。旧署名付きテンプレートには自身の元例から同じ保守的な制限を導き、未署名データを承認しません。転移した問題は毎回、厳密な分数計算と別実装の FPL 検査を通します。

`chatgpt-study` は、異なる数値例2つ以上からの方法の統合にこの判定を利用します。教師が出す変数名の違いだけで学習に失敗するケースを減らします。同じ provider の2つの見方は独立した教師ではありません。数値スロットへの転移は、自然言語の翻訳が正しいことを完全には証明しません。

## ChatGPT 接続と境界

前版の専用認証、API key、署名付き対話、呼出し数の予約を保持しています。接続手順は `README_V1022_6_6_CHATGPT_JA.md` と `tools/chatgpt_connect.py` を参照してください。依存関係には認証側が直接使う httpx も明記しました。認証情報を個体のデータ・配布 ZIP・文化継承へ入れないでください。

この版は EXPERIMENTAL です。実サービスへ接続した証拠、長時間の異種教師学習、24h、汎用知能、重み更新、自己コード改変、主観意識の成立はありません。合成の教師応答による試験は実 ChatGPT 学習ではありません。G4 の新しい学習型は公開文化継承へ未接続です。workspace 復元後の未来ファイル再出現の根本原因も未解決であり、今回の成功した限定試験から解決済みとはしません。
