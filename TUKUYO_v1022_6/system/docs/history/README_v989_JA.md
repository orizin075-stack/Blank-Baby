# TUKUYO v989 — Temporal Soul Identity

v989 は、魂の同一性判定を「現在の魂SHAが起点時と同一か」から、**正当な変化の因果鎖が切れていないか**へ変更する。

同一個体の判定条件は次の4点。

- same_origin: v977初期魂と同じ起点から始まる
- valid_transition_chain: SOUL_EVENTS を初期状態から再演した遷移列が全件一致する
- no_illegal_state_jump: eventを伴わない SOUL_CORE の直接変更がない
- lineage_continuity: individual / lineage / branch の連続性が保たれる

魂SHAそのものは経験によって変化してよい。各経験は `Soul_t -> source_event -> Soul_t+1` として `v989/SOUL_TRANSITIONS.json` に再構成される。既存のv977履歴も決定論的に再演するため、v989導入以前のSOUL_EVENTSについても現在のSOUL_COREまで到達できるか検査する。

またv981のFORK_ORIGINは「現在魂と永遠に一致すべき値」ではなく、fork作成時の**不変な歴史スナップショット**へ修正した。正当な後続経験で親の魂が変化しても `FORK_ORIGIN_DRIFT` にはならない。

v980 continuity assay は経験なしcounterfactual controlを必須化した。同じ選択肢で経験なし個体と同じ選択しか出ない場合は `NON_DISCRIMINATING_CONTINUITY_ASSAY` として証拠不十分扱いになる。

出荷基盤も修正し、`run_selftest.py` は unittest discovery ではなく pytest を使用する。これによりv978以降のfunction-style testも自己試験へ含まれる。起動時integrity guardはmanifest掲載済みPythonだけでなく配布木全体のexact file set、cache、symlink、release receipt署名を検査する。

## コマンド

```bash
python3 -B run_tukuyo.py --data ../TUKUYO_DATA soul-identity-sync
python3 -B run_tukuyo.py --data ../TUKUYO_DATA soul-identity-status
python3 -B run_tukuyo.py --data ../TUKUYO_DATA soul-identity-audit
```

## Claim boundary

本版が検証するのは機能的・因果的な時間的自己同一性であり、文字通りの魂、意識、生命の成立を主張しない。
