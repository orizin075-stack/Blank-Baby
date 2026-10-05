# v1014.2 以降の次ルート

1. 24時間 external-witness continuity を開始し、定期tick・fresh-process restart・checkpointを混在させる。
2. 24時間中にbounded crash campaignを挿入し、target temp / checkpoint pointer / restore commit / realtime pending-eventの復旧receiptを保存する。
3. 24時間完走後に72時間controlled restart continuityへ拡張する。
4. 正本H3/H4・第三者再現は時間継続試験とは別gateとして維持する。

現在のv1014.2はatomic crash recovery harnessを実装・fresh fault injectionで確認した段階であり、24h/72hの経過時間そのものは未証明。
