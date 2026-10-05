# TUKUYO v936 — Failure-Driven Grammar Discovery (standalone research harness)

This is a **bounded synthetic research harness**, not the complete TUKUYO agent. It builds decision-rule source files from labeled failures using a finite grammar: atomic metrics and automatically evaluated pairwise sums/differences/products. It does not contain the full v827/v833 agent or claim general open-ended code generation.

`python -B tools/reproduce.py --out /tmp/v936_fresh` freshly reconstructs all models and metrics from fixed development seeds. `python -B run_selftest.py` verifies reproducibility, randomized-label falsification, grammar ablation, frozen-parent comparison, constrained code generation, input validation and fail-closed promotion.

The **v935 frozen policy stays active** on its protected reference domain. The learned v936 tree, while helpful on the novel synthetic oracles, regresses on the protected reference task. It is therefore only a shadow research candidate. All reported holdouts are reproducible **internal development tests**, not external blind evaluations: all evaluator source and seeds are included for auditability.

`STATUS.json` lists missing real H3/H4 inputs, third-party evaluation, actual 30-day two-fork continuity, old-to-new authority rotation and full TUKUYO core. Release signing uses a new, explicitly *unbridged* trust epoch. Pin the separately distributed public key out-of-band; do not trust a key provided only within the release ZIP.

## v937: independent challenge handoff

`challenge/CHALLENGE_CONTRACT.json` pins three candidate model/source SHA-256 values. A genuinely independent evaluator must supply **their own** never-before-shared JSONL cases with keys `case_id`, `input` containing `a`,`b`,`c` numeric values in [0,1], and `truth` containing one of `audit`,`hold`,`probe`,`propose`. The package ships no third-party dataset, credentials, signed positive receipt or assertion of external completion.

On the evaluator's machine, generate an Ed25519 32-byte private key, keep it private, publish its public key/fingerprint through an **independent** trusted channel and run:

`python -B tools/challenge.py evaluate --task coupled_product --dataset private_cases.jsonl --signer-key-file evaluator.key --out external_result --evaluator-declaration 'Independent Lab'`

Then another party with the independently pinned public key can run:

`python -B tools/challenge.py verify --task coupled_product --dataset private_cases.jsonl --receipt external_result/EVALUATION_RECEIPT.json --result-rows external_result/RESULT_ROWS.json --trusted-evaluator-pubkey-b64 <EXTERNAL_PINNED_KEY>`

The verifier checks real candidate execution, every case hash, row-level correctness and the signature. This cannot authenticate the truth of labels, prove the evaluator's independence, or prove that the dataset was hidden when the candidate was frozen. Those claims require separate evidence and trusted timestamps.
