# TUKUYO v1017 — Parent → Successor → Grandchild

v1016 の bounded Multi-Agent Society を土台に、親個体の不可逆死亡後にのみ署名済み successor package を発行し、fresh な子個体へ限定的な系譜情報を継承する三世代ゲートを追加した。Parent → Child → Grandchild の3個体は同一 family lineage を共有する一方、individual ID、identity lineage、branch、succession key、Soul履歴は別個に保たれる。

継承対象は署名された系譜情報、許可された public capability ID、減衰した value bias に限定する。親の秘密鍵、生のepisodic/autobiographical memory、Soul event履歴、private relation noteは successor package に含めない。これは復活やstate cloneではなく、別個体への限定的継承として扱う。

fresh regression は v1017 新規 7/7 PASS、親 focused regression 68/68 PASS、合計 75/75 PASS。開発中に v1017 のprivate succession keyをcheckpointへ含めずにrestore staged auditだけ成立させる統合穴を検出し、live keyをstage監査にだけ供給するよう修正した。checkpoint/restore後も秘密鍵はsnapshot対象外のままである。

## Claim boundary

- bounded Parent → Child → Grandchild lineage: PASS
- successor ≠ resurrection: enforced
- private memory/key inheritance: prohibited and tested
- literal biological/electronic reproduction: NOT ESTABLISHED
- open-ended generational evolution: NOT ESTABLISHED (v1018 scope)
- 24h multi-generation ecology: NOT COMPLETED
- General L5 / literal soul / consciousness: NOT ESTABLISHED
- full historical suite on this exact release: NOT RERUN TO COMPLETION
