# TUKUYO v1014.4 — Continuous Witness / Soul Atomicity / Scalable Campaign

v1014.3の長期campaignハーネス修復版。今回の主目的は、短い外部時刻証明を「連続稼働」と誤認しないこと、会話中クラッシュでSoul履歴を壊さないこと、長期campaignが履歴量に比例して重くならないこと、巨大な再構築可能検索indexによってrecovery checkpointが停止しないことにある。

## 主要変更

- Soul transitionを **event-first → materialized SOUL_CORE** の順に変更。event書込後・core反映前に停止した場合は次起動でjournalからcoreを再構成する。
- 会話処理をtransaction化。mutable stateは事前snapshot、append-only journalは開始時byte lengthを保存し、途中停止時はjournal truncate + materialization再生成で直前の整合状態へ戻す。
- campaign auditで **最大tick gap** と **中間external witness gap** を検査。start/endの二点間に時間が経過しただけではcontinuous campaignをPASSしない。
- checkpoint失敗をcampaign state/eventへ記録し、campaign-auditをfail-closedにする。
- recovery snapshotをcontent-addressed delta方式へ変更し、`v1001/knowledge_index.sqlite3`のような再構築可能派生indexをsnapshotから除外する。
- campaign stepは直近headのincremental検査とappend-only eventを使い、毎stepの全履歴再署名検証・全ファイル再書込を避ける。
- `restart_observations`は実process_instance_idが変化した時だけ増加する。
- bounded reasoningは質問節をpremiseから除外し、袋・箱・パック・ケース・束、個・枚・本・冊・台・人のpackage数量、使用後残数、container数質問を拡張。最大/最低/少なくとも等のboundからexact値を断定しない。独立semantic verifierも別実装で同じ意味条件を再構成する。
- aggregate `audit`は子監査の`ok=false`をトップレベルへ伝播する。
- `STATUS.json.version`は旧selftest互換の整数版`v1014`を維持し、枝版は`release_version=v1014.4` / `latest_layer=v1014.4`で表す。
- `TRUST_KEY_LINEAGE.json`は親v1014.3 archive/anchorと現v1014.4 anchorを記録する。ただし親鍵によるcross-signは未実装。

## fresh重点実測

- v1014.4新規回帰: **9/9 PASS**
- 親focused regression: v1014.3 3/3, v1014.2 4/4, v1014.1 5/5, v1014 3/3, v1013 3/3, v1012.1 7/7 = **25/25 PASS**
- 合計重点回帰: **34/34 PASS**
- transaction開始後を狙った会話kill: **12/12次step成功、Whole audit failure 0、stranded marker 0**
- campaign 600step: first10中央値 約5.91ms / 100step付近 約6.12ms / last10 約6.49ms（同一process内部計測）
- 約4.19MB knowledge source / 約37.23MB rebuildable index: recovery checkpoint 約4.21MB、checkpoint/audit PASS、index除外確認
- continuous witness short gate: 中間witnessを含む3秒targetでformal gate PASS。無観測gap negative controlはFAILとして検出。
- 前回selftestで落ちたSTATUS numeric versionチェックは単独再実行PASS。

## Claim boundary

配布時点で24h / 72h / 7dayの実時間完走は未実施。short gate、ローカルwall clock、start/end witnessのみを24h Living Continuityの証拠として扱わない。一般L5、literal life、literal soul、consciousness、third-party reproduction、external H4は未確立またはPENDING。全歴代selftestの現releaseでの完全再走はwall-time制約により完了主張しない。
