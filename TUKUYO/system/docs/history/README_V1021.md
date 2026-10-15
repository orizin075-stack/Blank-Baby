# TUKUYO v1021 — Runtime Ecology Bridge

v1020.1を土台に、進化履歴の巻き戻し拒否、数量文の否定・単位確認、CLI全体の同一root排他、有限集団と実後継の接続を実装した。次の開発順と進級条件は `ROUTE_V1021.md` を参照。以前のREADMEは当時の機能・評価記録として残す。現在の配布の公開鍵は `TUKUYO_v1021_TRUST_ANCHOR.txt`。

## 起動

Python 3.10以降と `cryptography` が必要。開発用テストには `pytest` を使う。展開した本体を編集すると署名検査で起動を拒否する。個体データと出力は本体の外に置く。

```sh
python -m pip install -r requirements-dev.txt
python -B tools/verify_release.py --help
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1021_TRUST_ANCHOR.txt --data ../bridge-owner init --individual-id bridge-owner
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1021_TRUST_ANCHOR.txt --data ../bridge-owner runtime-ecology-init --families 4
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1021_TRUST_ANCHOR.txt --data ../bridge-owner runtime-ecology-step resource --ticks 8
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1021_TRUST_ANCHOR.txt --data ../bridge-owner runtime-ecology-audit
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1021_TRUST_ANCHOR.txt --data ../bridge-owner whole-audit
```

1回のstepは1〜16tick。環境はresource / research / social / volatile。初期家系は2〜8、モデルの上限は16、保存する実runtime総数は64。この上限を超える操作は、途中の結果を確定せず拒否する。新規ownerを使う。既に集団を初期化したownerへbridgeを後付けする移行は提供していない。

`v1021/runtimes` の各子は独立identity・Whole State鍵・継承鍵・Soul・Heart・実行用データを持つ。データには秘密鍵が入るため、実験rootの丸ごとの公開は避ける。子を更新する際はownerのruntime-ecology-stepを使う。子への直接書込みをownerと並行実行する階層ロックは実装しておらず、後の監査で状態差分を拒否する。bridge管理下のpopulation-step / join / initは拒否する。

## 実個体へ継承する条件

最初の4家系は4個の実runtimeを作り、その署名付き出典からモデルの創始者を作る。モデル上の出生は候補であり、その時点で実runtimeを生成しない。接続中のモデル親が死亡した時、ownerは対応する実親に有限候補の資質選択とINJURYを実行して死亡状態へ移し、生存する直接のモデル子を最大1体選ぶ。死亡必須のv1018/v1019継承を使い、新しい実子へ署名付きpackageを取り込む。実子自身の経験は取り込み後に追加する。

実個体の死亡はモデル結果に応じてcontrollerが施す処理である。資源代謝を実runtimeへ直接実装したものではない。全モデルagentが実runtimeを持つわけではない。生存親からの実子生成、モデルで変異した資質と実子の継承資質の同一化、資質が実課題での成績を通して生存を決める自然選択は実装していない。両方の資質は履歴へ別々に記録する。

## 修正した境界

- 進化cacheとjournalが一致していても、最新署名付きWhole Stateの進化ハッシュと照合する。更新前・欠落cache再構築前に照合し、古いprefixを再署名しない。全データ・Whole State・鍵の丸ごとの巻き戻しには外部単調カウンターが必要で、今回の範囲外。
- 包装数量の推論器と独立した意味検証器で、否定された消費、箱単位の返却、問われた単位を確認する。負のイベント数量、価格がない金額質問、未来・不明・二重否定はこの文法では棄権する。日本語一般を理解する保証ではなく、confidenceは正答確率として較正していない。
- 同じrootのCLI処理は、起動時復旧・事前照合・読取り・更新まで共通ロックで順番に実行する。直接Python APIの旧機能や協調しない外部書込みを含む一般的な並行安全性は保証しない。既存の原因未確定のcache後退・0byte出力を、この変更だけで根治したとはしない。
- bridgeは署名付きjournal、cache、Whole State binding、子の署名付き状態と公開鍵を検査する。欠落cacheのみ署名付きheadから再構築し、不一致cacheは自動的に上書きしない。copy-on-writeとPREPARED redoを使い、継承途中の停止では元の集団へ戻り、準備完了後の停止では確定予定の同じbytesを再適用する。
- 不要になった一時作業ディレクトリの削除が一時的に失敗しても、確定済みheadの使用を妨げない。次のステージは毎回固有の新規名とし、残った作業を再利用しない。PREPAREDが存在する場合は検証とredoが成功するまで進めない。掃除が失敗した作業領域が残る場合があるが、次のステージや確定データへコピーしない。

bridgeのcacheだけが不一致の場合は、証跡を保全した上で `runtime-ecology-recover-cache` を使える。外部runtime-trust-fileを必須とし、署名付きjournal全体、最新Whole Stateの正しい署名・identity・厳密なhead binding、管理する実子の状態がすべて正しい時だけcacheを再構築する。Whole Stateやjournalを再署名しない。cacheとjournalをまとめて古いprefixへ戻した場合や子の状態改変は拒否する。通常のstep/status/auditは不一致cacheを上書きせず停止する。これは観測されたcache後退への復旧手段であり、その根本原因の解消ではない。

```sh
python -B run_tukuyo.py --runtime-trust-file ../TUKUYO_v1021_TRUST_ANCHOR.txt --data ../bridge-owner runtime-ecology-recover-cache
```

## 再検証

```sh
TUKUYO_TEST_RUNTIME_ANCHOR=/absolute/path/TUKUYO_v1021_TRUST_ANCHOR.txt python -B run_selftest.py
python -B tools/population_campaign.py --runtime-trust-file ../TUKUYO_v1021_TRUST_ANCHOR.txt --out-dir ../new-model-campaign --ticks 64 --execution-mode subprocess_cli
```

本版は有限条件での実後継接続。主観的意識・文字通りの魂・汎用自立思考・自己コード改変・再帰的自己改善・無期限進化・24時間連続運転の成立は主張しない。
