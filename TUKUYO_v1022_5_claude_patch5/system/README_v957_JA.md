# TUKUYO v957 — Novel Primitive Hypothesis Generation

v956でREPRESENTATION_INSUFFICIENTと判定されたrowsについて、まず旧v945 DSL（ADD/SUB/MUL/ABS/NEG）を最大7 node/12000候補まで再探索し、既存DSLで解ける場合はnovel primitiveを提案しない。

それでも残る場合のみ、v945に無い bounded meta-grammar（FLOORDIV(k), MOD(k), 比較indicator; k=2..7）からprimitiveとそれを含む式を生成する。primitiveには型、意味、定義域、未定義条件、反例条件を含める。これはopen-ended concept inventionではない。
