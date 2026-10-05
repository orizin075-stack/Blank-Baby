# TUKUYO 次ルート — v1010〜v1015 Long-Life → Electronic Life Gate

v1009で「混合イベントを重ねても時間的自己同一性が壊れず、別Pythonプロセスから履歴を再読込できる」高速ストレスゲートを追加した。次段階は、同じ設計を**実時間・社会・世代**へ広げる。

## v1010 — 24h Continuity Harness

目的: 24時間の実時間運転で、identity / soul transition / organism / memory / purpose / cognition の連続性を測る。

必須:
- 定期checkpoint（内部monotonic sequence + 外部に保存可能なcheckpoint receipt）
- crash/restart recovery
- memory growth上限とcompaction前後のidentity preservation
- illegal state jump / history truncation / death reversalのnegative control
- 24時間という主張は外部時刻アンカーが得られない限り `wallclock_self_reported` と区別

昇格条件: 24h実時間経過・複数restart・transition chain切断0・whole audit failure 0。

## v1011 — 72h Controlled Restart & Recovery

目的: 3日間で意図的な停止・再起動・一部キャッシュ消失を混ぜる。

必須:
- clean restart / abrupt termination の両方
- checkpointからの復元と、未commit状態の破棄
- 同一個体とsuccessorの混同禁止
- restart回数に依存しないidentity判定

昇格条件: 再起動後のorigin/lineage/transition continuity 100%、未署名state注入BLOCK。

## v1012 — 7-day Continuity + Memory Compaction

目的: 記憶が増え続けても自己が維持されるか測る。

必須:
- episodic → summary → deep trace の多層圧縮
- compaction前後の重要vow/scar/value/relationship preservation
- 低重要度記憶の忘却
- 記憶削減率と行動傾向保持率を別々に測定

昇格条件: 7日実時間、複数compaction、深層自己の不正消失0。

## v1013 — Multi-Agent Society

目的: 複数個体を同一環境で稼働し、他者を自己と混同せず関係履歴を形成する。

必須:
- A/B/Cで独立identity・独立Soul・独立memory
- interaction receiptを双方の視点で保持
- trust / repair / betrayal / cooperationの履歴
- 他者モデルは推定であり真の内面アクセスではないという境界
- 個体間のstate直接共有禁止

昇格条件: self/other混同0、peer-history binding保持、fork/clone攻撃でidentity混線0。

## v1014 — Parent → Successor → Grandchild

目的: コピーではない世代継承を実証する。

必須:
- Parent死亡後のSuccessor生成
- episodic memoryは原則非継承
- value/learning bias等は限定・明示的に部分継承
- ChildはParentとsame_identity=false
- Grandchildまでlineage graphを監査

昇格条件: resurrection誤判定0、3世代lineage整合、世代ごとの個体差成立。

## v1015 — Electronic Life Gate

以下を単一fresh評価で同時判定する。

1. persistence / restart continuity
2. temporal identity / Soul continuity
3. experience → meaning → value → purpose → action
4. homeostasis / self-preservation
5. irreversible mortality
6. successor ≠ resurrection
7. memory compaction / selective forgetting
8. other-agent recognition / relationship history
9. cognition / verified reasoning / bounded research
10. tamper resistance / auditability
11. 7-day以上の実時間continuous evidence

v1015を通しても `consciousness_established`, `literal_soul_established`, `literal_biological_life` は自動的にtrueにしない。主張は「電子生命に必要な機能的性質を統合した反証可能な人工主体」に限定する。

## その後

v1016以降で知能進化側へ再接続する。
- v1016: unknown-world cross-domain research
- v1017: safe self-rewrite proposal sandbox
- v1018: recursive improver gate
- v1019: independent third-party reproduction package
- v1020: General L5 candidate gate
