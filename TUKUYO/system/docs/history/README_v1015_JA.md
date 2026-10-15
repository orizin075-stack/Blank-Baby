# TUKUYO v1015 — Functional Living Continuity Gate

v1014.4のcontinuous witness / Soul atomicity / crash recoveryを親として、経験→意味→価値・自己モデル→目的→行動→内部状態変化→検証済み認知を、restartを越えて同一の生活史イベント鎖へ束縛する層。

## 新規コマンド
- `living-episode KIND VALENCE IMPORTANCE [--theme ... --relation ... --query ...]`
- `living-continuity-status` / `living-continuity-audit`
- `living-gate-assay`
- `living-gate-audit`

各episodeは開始intentをdurable markerへ記録する。途中kill時は次回起動で無かったことにせず、実際に残った状態を `EPISODE_INTERRUPTED_RECOVERED` として生活史へ束縛する。event fileだけ書かれてstate head更新前に停止した場合もheadを自動修復する。

`functional_living_continuity_gate` と完全な `electronic_life_gate` は区別する。後者は7日実時間external witnessとsuccessor≠resurrectionの統合実証が揃うまでPENDING。consciousness / literal soul / literal biological lifeは主張しない。
