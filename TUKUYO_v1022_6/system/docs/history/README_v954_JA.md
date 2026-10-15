# TUKUYO v954 — Meta-Improver Generalization Authority

## 今回閉じたもの
- legacy learned capability は外部 Capability Authority seal が無ければ runtime answer に使用されない。
- capability provenance は proposal / holdout / commitment / verifier receipt / promotion / learning entry の実在オブジェクトをSHA-256で束縛する。
- zero hash、missing object、wrong individual は拒否。
- mixed unseen task family に poly / MAX / MIN / ABS を混在させ、family regression が1件でもあれば meta-improver promotion を拒否。
- improver候補は削除だけでなく、演算子探索順・piecewise優先・定数優先の編集を含む。
- production src の assert 依存を除去し、python -Oでも検証が消えない。
- top STATUS.json は v954 を正本とする。

## Capability Authority の使い方
1. 外部ディレクトリで `python -B tools/capability_authority.py keygen --out /path/to/trust`
2. `teach --apply` 後、`cap-request SURFACE --out request.json`
3. 外部側で `capability_authority.py sign ...`
4. `--cap-trust-dir /path/to/trust cap-install request.json receipt.json`
5. 以後、同じ `--cap-trust-dir` を付けた runtime だけが seal 済み能力を回答に使用する。

## Claim boundary
これは bounded L5 research / bounded meta-improvement の硬化版であり、general L6 を確立しない。
