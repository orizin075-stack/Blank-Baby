# TUKUYO v1022.8.2 — 環境変化と暫定文化継承（実験版）

予測が高い確信で外れたとき、失敗した操作を保留し、限られた実験で予測を作り直す版です。実個体のHeartが、生存資源の確保・学習・検証・予測修復・休息の候補から選びます。語彙、予算、環境、Goalの計算則は人間が設計した有限モデルです。

ノイズのない作業結果の強い反例はモデル修復へ直結し、ノイズを含むセンサーの反例は再観測を求めます。未知の表を学ぶ場合は、既知の法則候補の情報量ではなく表の各入力の不確実性を使います。仕事の期待収支には基本代謝も含めます。生存を保証する制御ではありません。

予測モデルを作り直しても、個体の経験は削除しません。`adaptive_life/EPISODES.jsonl` に全行を残し、署名付きコミットとWhole headに結び付けます。監査は候補、Heart選択、観測、計算、モデル更新を再実行します。プロセス内の再計算省略は、コミットと経験・Heart記録の既検証prefixが完全一致するときだけです。`adaptive-audit` は先頭から再計算します。旧`developmental_life`の署名済み形式と旧Goal方式は保持します。親のチェックポイントから復元された子の読み込みにも、親が署名した復元境界を適用します。境界に含まれる既存バイトの改変は拒否し、境界に無い未来のファイルは証拠付きで隔離します。未来の再出現原因そのものを解明したとは主張しません。

親は死後、最新の公開観測を最大16件、実後継個体へ渡せます。親の継承鍵で署名し、子のID・家系・環境全体の範囲に束縛します。子は未確定の観測として使い、自分の予測を持って観測を続けます。親のGoal履歴、感情履歴、私的事実、秘密鍵、個体の自伝はコピーしません。親の法則を確認済みとして自動採用しません。環境監査は公開観測を親の実記録とも照合します。

## 実行例

Python 3.12で`python -m pip install -r requirements-dev.txt`を実行し、配布ZIPと別に渡された公開trust anchorを使います。

```bash
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1022_8_2_TRUST_ANCHOR.txt --data ../life init --individual-id LIFE --blank-learning
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1022_8_2_TRUST_ANCHOR.txt --data ../life metabolism-init --families 2 --seed development-38 --reservoir 90000 --regeneration 2200 --max-age 64 --adaptive-goals --world-change-interval 32
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1022_8_2_TRUST_ANCHOR.txt --data ../life metabolism-step --ticks 16
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1022_8_2_TRUST_ANCHOR.txt --data ../life metabolism-audit
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1022_8_2_TRUST_ANCHOR.txt --data ../life/v1022_ecology/runtimes/R000000 adaptive-audit
```

`--adaptive-goals`は`--research-world`を含みます。`--developmental-goals`との併用は拒否します。`--world-change-interval 0`は定常環境、8〜512は実験環境の法則変更間隔です。変更予定や環境の秘密はGoal方式へ渡しません。`--max-ticks`は標準512、適応方式では1024/2048/4096も設定可能ですが、設定できることはその長さの検証完了を意味しません。子の公開観測は`--no-research-culture`、全行動は`--no-actions`で対照実験できます。

## 判定の範囲

同梱の既存試験、追加回帰、独自の未使用条件での比較、実個体と復元の実測結果は、同版の検証報告・資料ZIPを参照してください。STATUSやこの説明から合格を推定しません。シミュレーションtickと実時間を区別します。現実の観測の真実性、自然選択、開放的な進化、汎用推論、ソース自己改変、24時間稼働、主観的意識、文字どおりの魂の成立は未証明です。
