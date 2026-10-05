# TUKUYO v1020 Population Ecology

v1019.1の署名付き継承・個体死亡・世代更新・復旧を維持し、複数家系が共有資源を使う有限な集団生態系モデルを追加した。

## 何を実装したか

- 1〜8家系、最大64モデル個体、最大512 tick。初期資源を創始個体のエネルギーへ移し、外部補充・維持消費・出生費用・死亡時の資源返還を整数で記録する。家系の追加は開始前だけ。
- 個体の資質と環境から資源需要を決め、不足時は比例配分する。余りの単位はハッシュで公平に決める。候補の固定適応度による勝者選びとは異なり、エネルギーが出生条件を満たした個体のみが子を持てる。
- 協力者が摂取資源の20%を提供し、協力者の不足分へ配分する。自分への返却を協力実績に数えず、家系をまたぐ実移転を追跡する。資源の生成や協力ボーナスはない。
- 子は親の5資質を受け継ぎ、1資質から別資質へ最大0.12移す。総量3.15は固定。環境に有利な子を出生時に選んだり、死亡個体を復活させたりしない。
- 署名付きコマンド列を意味検証付きで再実行し、キャッシュと照合する。キャッシュ欠落時は、署名付き個体全体状態のハッシュに一致する場合に再構築する。履歴末尾欠落は復旧として受け入れない。
- 初期化・家系参加・複数tick更新をv1019.1のトランザクションへ接続した。途中終了時は準備前の状態、または準備済み更新の全体へ復旧する。更新後には全ての書込みと全体状態の署名束縛を読み戻し、照合が済むまで復旧用記録を削除しない。

## 境界

これは既存個体の公開資質を起点にした生態系モデルである。`E000000`等のモデル子は、独立した鍵や魂・心・記憶を持つv1018後継個体ではない。モデル内の飢餓・寿命は、出典個体の不可逆な死亡を起こさない。実個体の継承は引き続き`evolution-export/import`等で行う。自然選択の成立、開放的進化、一般L5、実時間24時間の運用を達成したとは主張しない。

出典個体は生存中で、家系が確定済みで、継承・進化・全体監査に合格する必要がある。参加処理は出典のコピーを監査し、現在の公開進化資質について署名付き証言を作る。外部家系には明示した公開鍵ファイルを要求する。この証言は署名元の認証であり、外部の真の個体・死亡・権限を第三者が証明する仕組みではない。非公開の会話や経験は持ち込まない。

既存のSoul/Heart/学習ループをモデル全個体に実行する機能や、モデル出生を実個体の後継作成へ変換する機能は今後の課題。有限資源と繁殖の収支を先に検証する版である。

## 起動

Python 3.10+と既存依存関係を使用する。署名付き本体外に新しいデータディレクトリを指定する。旧STARTスクリプトの既定データ先をそのまま使わず、`TUKUYO_DATA_DIR`を設定するかCLIの`--data`を指定する。下記の`anchor.txt`は同梱外の`TUKUYO_v1020_TRUST_ANCHOR.txt`を指す。

```sh
python -B run_tukuyo.py --runtime-trust-file anchor.txt --data ../owner init --individual-id owner
python -B run_tukuyo.py --runtime-trust-file anchor.txt --data ../owner population-init --seed trial
python -B run_tukuyo.py --runtime-trust-file anchor.txt --data ../peer init --individual-id peer
python -B run_tukuyo.py --runtime-trust-file anchor.txt --data ../peer succession-founder-init
python -B run_tukuyo.py --runtime-trust-file anchor.txt --data ../peer succession-pubkey-export --out ../peer.pub
python -B run_tukuyo.py --runtime-trust-file anchor.txt --data ../owner population-join ../peer --source-trust-file ../peer.pub
python -B run_tukuyo.py --runtime-trust-file anchor.txt --data ../owner population-step resource --ticks 16
python -B run_tukuyo.py --runtime-trust-file anchor.txt --data ../owner population-step volatile --ticks 16
python -B run_tukuyo.py --runtime-trust-file anchor.txt --data ../owner population-audit
python -B run_tukuyo.py --runtime-trust-file anchor.txt --data ../owner whole-audit
```

`population-init`: 資源上限240000、補充50000/tick、創始個体3、人口上限24、寿命18tick、協力あり。`--capacity`、`--regeneration`、`--founders`、`--max-population`、`--max-age`、`--no-cooperation`で開始前に設定する。設定は途中変更できない。環境はresource/research/social/volatile。volatileの補充は60%。同じ開始状態・seed・コマンド列は同じ結果になる。

出生には24000のエネルギーが必要で、親は9000を払い、子に6000を渡し、3000を消費する。維持費は2400+curiosity×400、volatileは追加600。不足なら飢餓、年齢上限でも死亡する。資源が潤沢でも人口増加で不足する場合があり、絶滅しても自動的に再導入しない。tickは実時間を表さない。

補充ゼロ・不足・中程度・高補充・潤沢・協力なしを、同じ出典個体から比較する再現用コマンド:

```sh
python -B tools/population_campaign.py --runtime-trust-file anchor.txt --out-dir ../population-campaign --ticks 64
```

実験の更新・削除・復旧は同一プロセスでCLIを呼び出して検査し、各条件の最後に別の新規プロセスから集団監査・全体監査を行う。全tickが別プロセスで再起動する実験ではない。出力先は新規のディレクトリ。内部のruntimeデータには秘密鍵が含まれるため公開しない。`public`サブディレクトリに公開実験結果を作成する。公開証言は初期家系の鍵に依存するので、試行ごとのfamily IDと署名は変わり得る。

## 互換性・検証

配布署名のversionとCLIの`release_revision`はv1020。既存の継承・進化などのプロトコルversionは従来値を維持する。新規データを推奨。v1019.1の初期状態を使う際はバックアップを用意し、全体監査後に開始する。既存証明を新形式へ無断で書き換えない。

実行は単一書込みプロセスが前提。v1019.1のトランザクションは本機能の書込みも直列化するが、旧機能を別プロセスから同時に書くことの安全は保証しない。512tickと人口64は検証用の上限で、無期限運用・ディスク上限・Windows/macOS・実電源断は別途確認が必要。

```sh
TUKUYO_TEST_RUNTIME_ANCHOR=/absolute/path/anchor.txt python -B run_selftest.py
python -B tools/verify_release.py . --trusted-pubkey-file anchor.txt
```

この版の配布鍵は新しい検査用署名者。前版の署名者によるクロス署名はない。

## 初期試行で検出した不整合

子プロセスで更新したファイルを親の実験スクリプトで削除・検査する初期方式では、古いキャッシュの再出現や出典の進化キャッシュ不一致を断続的に検出した。署名付き履歴と一致しない状態は拒否された。直後の読み戻しでは正しい状態が観測されており、根本原因は確定していない。単純な書込み欠落と断定しない。

現在の再現スクリプトは更新と削除・再構築を同じプロセスで確認した後、別プロセスで再監査する。署名付き最新ハッシュに一致する欠落キャッシュの再構築のみ最大3回確認し、既存の不一致キャッシュを無断修復しない。トランザクションも書込み確認が通るまで復旧記録を残す。ただし初期方式の不整合が一般に解消したとは主張しない。実環境でキャッシュ不一致が出た場合は書込みを止め、データを保全して原因を調査する。
