# TUKUYO v990 — Closed Environment Perception–Action Loop

v990は、内部だけで計算したutilityから一段進み、閉じたシミュレーション環境の観測・行動・環境変化・結果を一つのhash連鎖として記録する層です。

- 観測には source / logical_tick / uncertainty を持たせる。
- 行動は MOVE_FORWARD / MOVE_BACK / GATHER / REST / SHIELD の有限集合。
- 結果は resource_gain / hazard_exposure / progress_to_goal / reached_goal / information_gain として環境遷移から算出する。
- 各イベントはpre/post world SHAへ束縛し、originから全遷移を再演して監査する。

これは物理センサーではなく、決定論的な閉環境シミュレーションです。現実世界へのgroundingや身体行動を主張しません。
