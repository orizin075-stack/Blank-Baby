# TUKUYO V1022.7.1 Semantic Truth Challenge Experimental

## 目的

V1022.7は、登録鍵、authority署名付きwitness証明書、三つの設定済みtrust domain、署名付き評価、中央値集約を導入しました。しかし三者全員が同じ誤りを署名した場合でも合議自体は成立します。署名は発言者とbytesを証明しますが、内容の真実を証明しません。

V1022.7.1は、この限界を隠さず、次の二段階へ分離します。

1. 三領域の署名付き報告は `CONFIGURED_CONSENSUS_ONLY` として保存する。
2. 事前にhashを登録した有限benchmarkを、別鍵のoracle receiptと独立再計算でchallengeする。

## 新しい保証

- claimはsubject、predicate、context hash、value type、unit、comparator、tolerance、asserted valueを全て持つ型付き構造に限定する。
- 自然文だけの曖昧なclaimを確定処理へ入れない。
- witness reportはclaim hash、nonce、value type、unit、観測値、evidence hash、method hashへ署名する。
- 三つの異なるwitness鍵と三つの設定済み領域を必要とする。
- report consensusだけではtruthを名乗らない。
- oracle鍵はauthority鍵・witness鍵と共有できない。
- oracle registryとbenchmark manifest hashは最初のreport前に固定する。
- oracle receiptのexpected valueをmanifestから再計算し、署名だけでなく内容一致も検査する。
- report、claim、nonce、evidence、receipt、challengeの再利用を拒否する。
- Whole State、transaction、recovery、mortality auditへ統合する。
- private semantic-truth stateはsuccessor packageへ継承しない。
- TUKUYO runtimeをimportしない独立raw verifierを同梱する。

## 判定語

- `CONFIGURED_CONSENSUS_ONLY`: 設定済み三領域の署名付き合議。真実とは扱わない。
- `BOUNDED_BENCHMARK_VERIFIED`: claimが事前commit済み有限benchmarkの該当entryと一致した。
- `BOUNDED_BENCHMARK_REFUTED`: claimが該当entryと一致しなかった。

これらは外界一般の真理判定ではありません。benchmarkが現実を正しく表すこと自体は別の仮定です。

## CLI

```bash
python -B run_tukuyo.py --runtime-trust-file TRUST_ANCHOR.txt --data DATA semantic-truth-integrate
python -B run_tukuyo.py --runtime-trust-file TRUST_ANCHOR.txt --data DATA semantic-truth-oracle-add oracle.json
python -B run_tukuyo.py --runtime-trust-file TRUST_ANCHOR.txt --data DATA semantic-truth-report reports.json
python -B run_tukuyo.py --runtime-trust-file TRUST_ANCHOR.txt --data DATA semantic-truth-challenge challenge.json
python -B run_tukuyo.py --runtime-trust-file TRUST_ANCHOR.txt --data DATA semantic-truth-status
python -B run_tukuyo.py --runtime-trust-file TRUST_ANCHOR.txt --data DATA semantic-truth-audit
python -B tools/v1022_7_1_truth_verifier.py --data DATA
```

## 主張境界

本版が検証するのは、暗号学的著者性、型・単位・contextの束縛、設定済みreport quorum、manifestの事前commit、有限manifestに対する一致または不一致です。

本版は、外部世界の真実、authorityやdomainの現実的独立性、sensorの正確性、benchmark作成者の誠実性、文字通りの魂、意識、クオリア、人格を証明しません。また24時間運転、電源断、別host、独立第三者再現も未完了です。

## fresh検証

- 全体: 787/787 PASS、failure/error/skip 0/0/0。
- 新規Semantic Truth: 15/15 PASS。
- 近接回帰: 44/44 PASS。
- 三領域が12 kmへ一致した虚偽合議は、challenge前には `CONFIGURED_CONSENSUS_ONLY` のまま。
- 事前commit済みbenchmarkの15 kmにより `BOUNDED_BENCHMARK_REFUTED`。
- wrong unit、署名改変receipt、事後差替えmanifest、report後のoracle追加を全て拒否し、拒否前後の個体bytesは一致。
- 独立raw verifier PASS。
- 2家系8tickで、累計6実runtime、4実継承、第2世代、wrong 0。
- 子runtimeへprivate `semantic_truth` directoryの継承0。
- Semantic Truth、Metabolism、Whole AuditはいずれもPASS。
