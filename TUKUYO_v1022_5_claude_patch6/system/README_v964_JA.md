# TUKUYO v964

v964はopen-ended evolutionを宣言する版ではなく、有限meta-grammar上で「新しいprimitiveが時系列で増えるか」「以前の発見を保持するか」「文法外課題に出会ったとき天井を正しく検出するか」を測るassay。

4つの独立waveで FLOORDIV / MOD / GE / LT 系の新primitiveを発見・hidden再評価し、最後にmeta-grammar外の整数平方根型課題を投入する。最後の課題を無理に昇格せず `META_GRAMMAR_CEILING_DETECTED` とすることが成功条件。

したがって、これは bounded novelty growth + explicit ceiling detection の証拠であり、真のopen-endednessやgeneral L5/L6の証明ではない。
