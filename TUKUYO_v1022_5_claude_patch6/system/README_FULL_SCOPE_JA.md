# TUKUYO v941 — Flat runtime + archived full available lineage

## Directly executable after extraction

- `src/legacy/tukuyo_v837` — individual, autobiographical memory and signed state.
- `tukuyo_v838`, `v840`, `v841`, `v842`, `v843`, `v844`, `v845`, `v846`, `v846_1` — finite semantic teaching, social/other-agent, signed cluster, lineage, ecology, bounded genome evolution, runtime guard.
- `src/research/tukuyo_research_v936`, `v937` — synthetic bounded research, signed external-evaluator receipt FORMAT. No independent evaluator ran in this release.
- `src/tukuyo_v938`, `src/tukuyo_v939` — real bridges and comprehensive lab audit. All modules import directly from `src/` without recursive ZIP extraction.
- `research_layers/releases/` — EXACT 45 original research packages v891..v935. Their extracted source and evidence are in `research_layers/sources/`. Not live auto-promoted.
- `history/` — byte-exact v931..v935 official signed chain used for sandboxed v935 replay.

## Start (Python 3.10+, Linux, macOS, or Windows WSL2)

```bash
cd TUKUYO_v941_COMPLETE_FLAT_RUNTIME
python3 -m pip install -r requirements.txt
python3 -B run_selftest.py
python3 -B run_tukuyo.py layers
python3 -B run_tukuyo.py --data ../TUKUYO_v941_DATA init
python3 -B run_tukuyo.py --data ../TUKUYO_v941_DATA chat
```

Research and integration:

```bash
python3 -B run_tukuyo.py --data ../TUKUYO_v941_DATA lab
python3 -B run_tukuyo.py --data ../TUKUYO_v941_DATA research --task coupled_product
python3 -B run_tukuyo.py archive-list
python3 -B run_tukuyo.py archive-show v935
python3 -B run_tukuyo.py replay-v935
```

The full available archive is a DIFFERENT larger ZIP containing this runnable tree directly (not only nested archives) plus the original v846.1 and v890–v940 distribution bundles under `ORIGINAL_HISTORY/`. `HISTORY_INDEX.json` exposes hashes.

## Explicit limitations

The v839 original full distribution bytes were not recovered in the supplied ancestry; v840 still records its expected SHA. v890 is a large recursively embedded earlier history; its older ancestors have not been independently audited here. v891–v935 comprise separate bounded/synthetic experiments; they are included and inspectable, not a single autonomous code-evolving policy. v937 is shadow-only. No unrestricted offline LLM/free dialogue, no H3/H4 canonical end-to-end verification, no independent third-party semantic receipt, no externally time-anchored 30-day continuity, and no cryptographically proven old-signing-key rotation. `v941` is locally signed with a NEW developer key; this key must be obtained and trusted separately.


## v981–v983 追加層
- v981: deep-self fork divergence。共通originから異なる経験で状態・選択傾向が分岐することをboundedに検証。完全なruntime forkではない。
- v982: Ed25519 checkpoint chainとdata root外external integrity anchorによるrestart continuity。外部時刻証明ではなく、30日wall-clockは未確立。
- v983: 実organismのenergy / reserve / integrity / maintenance debt / fatigue とheart threatから高位maintenance intentを形成。低位motor policyは直接上書きしない。

## v984–v985 追加層
- v984: 同一snapshotを二つのdata rootへ複製し、別Pythonプロセスで異なる経験とtickを与えるbounded full-runtime fork assay。両branchのwhole auditがPASSしたままwhole/organism/heart/soul/homeostasis/choiceが分岐することを検証する。永続並列個体や意識分裂の証明ではない。
- v985: 複数experienceをmeaning/theme単位で集約し、vow/scar・emotion・homeostasisと統合して自己物語と高位purposeを形成・改訂する。purposeは外部行動を自動実行しない。意識、文字通りの魂、general L5/L6、open-ended goal inventionは未確立。

## v986–v988 追加層
- v986: v985のactive purposeを、複数cycleの有限内部action planへ変換する。planはpurpose state hashとidentityに束縛され、source purposeが変わった場合はstaleとして検出する。外部行動は含まない。
- v987: v986 planを実行し、各stepの成功、utility、観測を監査可能なtraceとして保存する。実行時plan snapshotを内包するため、後続planの作成後も過去実行の証拠を自己完結で監査できる。
- v988: v987 executionの成功率とutilityからpurpose別のstrategy preferenceを学習し、次回v986 planの順序へ反映する。同一execution hashは一度だけ消費し、再実行による学習水増しを防ぐ。fresh E2Eで`SEEK_KNOWLEDGE: WHOLE_AUDIT → EVIDENCE_REFLECT`、`PRESERVE_INTEGRITY: WHOLE_AUDIT → HOMEOSTASIS_ASSESS`の先頭action変更を確認した。

## v989–v992 追加層
- v989: SOUL_EVENTSを初期状態から再演し、固定SHA一致ではなく因果的transition chainで機能的自己同一性を判定する。正当な経験による魂状態変化は許容し、未記録のstate jumpは拒否する。
- v990: 閉じた再現可能環境で observation → action → environment outcome をhash-chain化する。現実世界センサーではない。
- v991: 環境結果と内部physiologyの前後差からutility / valence / importanceを後計算し、grounded heart eventへ接続する。行動名ごとの固定valenceは使わない。
- v992: 訓練配置と異なるfresh holdout配置で、介入履歴から学んだ方策を固定前進baselineと比較する。同一world family内の転移でありcross-domain一般化ではない。

## v993–v995 追加層
- v993: SOUL_EVENTSの`relation`を第一級キーにし、peerごとのtrust / attachment / scar load / riskを再演する。peerXの過去をtheme変更だけでリセットせず、peerYへ転写もしない。
- v994: 日本語・英語の複数cue、否定、SOULの獲得theme/vow語彙、relation contextを合成したbounded semantic profileを作る。単一`kind`→単一意味の表だけには依存しないが、一般言語理解ではない。
- v995: peerごとの時系列からtrust / positive evidence / negative evidence / unresolved harm / trend / confidenceを再構成し、社会的選択へ反映する。正の履歴でtrustは回復可能だが強いscar floorは即時消去しない。
- selftest: pytestがあればpytestを使用し、無い場合は標準ライブラリfallbackでunittest.TestCaseとトップレベル`test_*`関数の双方を実行する。


## v1019 追加層
- v1018 hardening lineage上にbounded generational evolutionを統合。固定trait budgetにより能力の単調全上昇を禁止し、環境ごとのtrade-off selectionを行う。Soul/episodic history/private keysは遺伝させない。natural selection / open-ended evolution / General L5は未確立。
