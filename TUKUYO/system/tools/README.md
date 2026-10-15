# 道具の目次（`system/tools/`）

`system/` で `python3 -B tools/道具の名前.py --help` として使います。ふだん使うのは「1. 確かめる」と「2. 第4世代の計測」の道具です。親（LLM）を呼ぶものは、そう書いてあります。ほかはすべて費用 0 です。

## 1. 確かめる・署名する

| 道具 | すること |
|---|---|
| `verify_release.py` | 配布物の署名と manifest を確かめる（`verify_release.py . --trusted-pubkey-file ../deliverables/TUKUYO_v1022_6_TRUST_ANCHOR.txt`） |
| `verify_zip.py`、`verify_release_zip.py`、`strict_zip_preflight.py` | zip を、展開する前と展開したあとに確かめる |
| `claude_patch_sign.py` | 自分の鍵を作り（`keygen`）、配布物を署名し直す（`sign`）。採用の手順は `../docs/README_V1022_6_JA.md` §3 |

## 2. 第4世代の計測と実験（記録は `../../evidence_gen4/`）

| 道具 | すること |
|---|---|
| `g4_measure.py` | 親を使わない計測（例外・壊れた読み・学習した型・ASDiv と MGSM の開発用） |
| `g4_bench.py` | 他の人が作った問題集（ASDiv・MGSM・SVAMP）を読み込む。鍵のかかった test は最終版で 1 回だけ |
| `private_eval.py`、`private_eval_sets.py` | 非公開の日英の問題（開発用と、凍結した本番用） |
| `exactness_probe.py` | 答えが決まらないように書き換えた問題を読まないか |
| `limits_probes.py`、`review_probes.py`、`parent_variation.py`、`fusion_gates.py` | 限界の問題・外部の検証の問題・親の書き方の違い・統合の関所 |
| `soul_assay.py`、`contamination_assay.py`、`growth_experiment.py` | 魂らしさ・親の言葉による汚染・成長の実験 |
| `experience_authenticity_experiment.py`、`goal_formation_experiment.py`、`identity_branch_experiment.py`、`restore_cycles.py` | 経験の出どころ・目標・個体の同一性・復元 100 回 |
| `ecology_long_run.py` | 生態系の長い実行（`--max-ticks`、`--resume`） |
| `g4_contamination_probe.py` | 親が問題集を覚えていないかの探針（**親を呼ぶ。費用がかかる**） |
| `llm_eval.py`、`llm_eval_sets.json`、`mock_llm_provider.py` | LLM が足すものを測る（patch1。模擬の LLM つき） |
| `chatgpt_connect.py` | ChatGPT のログイン（`../docs/README_V1022_6_6_CHATGPT_JA.md`） |

## 3. v1022.7〜8.2 の系統の道具（説明は `../docs/`）

| 道具 | すること |
|---|---|
| `identity_ledger_admin.py`、`identity_ledger_verifier.py` | 外部の台帳を作る・確かめる |
| `v1022_7_9_experience_verifier.py` | 魂の学習の厳格な出どころを、外から読み直す |
| `v1022_8_quantity_verifier.py` | 在庫の読み手の別の検査器を、単独で動かす |
| `v1022_7_1_truth_verifier.py`、`v1022_7_2_grounded_verifier.py`、`v1022_7_3_*`、`v1022_7_evidence_verifier.py`、`v1022_7_7_*` | v1022.7.1〜7.7（意味の真偽・観測装置・証拠による判断・証拠に縛られた魂・経験による魂）の検証器と実験 |

## 4. それより前の版の道具（今は使わない）

v1015〜v1021 の長時間・証人・挑戦の道具（`v1015_*`、`realtime_witness.py`、`recovery_stress.py`、`run_runtime_ecology.py`、`population_campaign.py`、`longrun_fusion.py`、`research_lineage.py`）、v9xx の道具（`v946_*`、`v958_*`、`v966_*`、`blind_gap_authority.py`、`capability_authority.py`、`external_actor.py`、`mock_grounding_attack.py`、`run_dialogue_school.py`、`stdlib_test_runner.py`）。テストと、昔の結果の再現に使います。説明は `../docs/history/` にあります。
