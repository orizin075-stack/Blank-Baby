# V1022.7.2 Grounded Sensor Challenge Experimental

## 目的

V1022.7.1は、署名付き合議が真実ではないことを明示し、事前commit済み有限benchmark内での一致・反証を検証した。本版は一段進み、型付きclaimを物理的な観測経路と行動結果へ接続する。ただし、電子署名されたセンサー値も外界の真実そのものではない。

## 観測経路

確定可能な観測bundleは、3個以上の別device鍵、3つ以上の設定済みsensor domain、3つ以上の校正domain、2種類以上のadapter hash、authority署名済み校正証明、校正有効期間、観測nonce、単調な論理時刻、型・単位・contextを必要とする。1台の故障にはmedianで耐えるが、2/3共謀は防げない。このため観測結果は常に `CALIBRATED_SENSOR_CONSENSUS_ONLY` であり、`external_truth_verified=false` である。

## 行動と代謝

sensor・校正authorityと別鍵のaction verifierだけが結果receiptを署名できる。receiptはobservation hash、nonce、runtime ID、action ID、action context、結果証拠、時刻、成功可否、資源量へ束縛される。成功receiptだけが既存のmetabolism reservoirから対象実runtimeへ最大1000単位を移す。失敗receiptの資源量は必ず0である。移動後も `initial + regenerated = reservoir + burned + living energy` を維持する。

## 監査と復元

authority、device、verifier、observation、outcomeはそれぞれhash chainで保存され、Whole Stateとtransactionへ統合される。cache欠落は署名済みcommitとWhole headから再構築できる。古い履歴、cache改変、将来outcome、nonce・reading・receipt再送は拒否する。private sensor stateはsuccessor packageへ継承しない。

## 証明しないもの

- センサーが外界を正確に測定したこと
- 設定されたdomain・adapter・authorityの社会的または製造上の独立性
- 2/3以上の共謀耐性
- 人間による第三者再現、cross-host、電源断、24時間運転
- 文字通りの魂、主観意識、クオリア、人格

本版におけるSoul強化は、情報源、校正、観測、行動、結果、資源変化を区別し、誤りを訂正できる機能的自己モデルである。
