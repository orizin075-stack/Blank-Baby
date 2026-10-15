# TUKUYO v1018 — Lineage Scalability / Succession Hardening

v1017の三世代継承を維持しつつ、系譜proofの再帰包含を平坦な署名certificate chainへ置換した。各certificateは親個体、子個体、世代、家系ID、親鍵、子鍵、前certificate hash、継承値、死亡commitmentへ署名する。successor packageはflat certificate listのみを運び、祖先packageを内包しない。

追加修正:
- 死亡済みindividualへの organism2-init を拒否。
- succession private key欠落時に新鍵を黙って生成しない。
- successor packageを子のsuccession public keyへ束縛。
- import packageをone-time使用として記録。
- inherited value profileをheart decision score / goal derivationへ実際に反映。
- 基本加算文章題とcontainer消費文章題の回帰を修正。
- v1017の0-byte一時ファイルを配布物から除外。

Claim boundary: これはbounded functional lineage modelであり、literal reproduction / consciousness / literal soul / general L5 / generational evolutionの成立を主張しない。
