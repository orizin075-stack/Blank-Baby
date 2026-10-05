# TUKUYO v987 — Bounded Plan Execution + Outcome Accounting

v986 planを有限の内部action spaceで実行し、各stepの成功/失敗・utility・観測値をhash束縛されたtraceとして保存する。実行時planの完全snapshotを記録するため、後から新しいplanを生成しても過去の実行証拠は現行planに依存して壊れない。`WHOLE_AUDIT`、homeostasis assessment、evidence reflection、relationship review、heart audit、purpose reevaluationのみを実行可能とし、外部アクションとmotor controlは実装しない。

v987は「計画を持つ」だけでなく「計画を実行し、結果を次段の学習へ渡せる」ことを対象にする。
