# TUKUYO v1012.1 Reasoning Soundness + Legacy Capability Reintegration

v1012の長期基盤を維持しながら、否定推論、数量推論のsoundness、verified-query接続、実journal監査、Heartを含むcheckpoint、legacy audit再統合を行う修復版。

- A→B と ¬A からBを導出しない。矛盾時は棄権。
- 数量問題は単位不一致・未実装変換・曖昧な倍/ずつを棄権。明示pack/単価乗算と合計を限定対応。
- verified-queryはbounded core reasoningを再計算して検証する。
- conversation/semantic .jsonlのhash-chain監査をWhole Auditへ接続。
- 会話ごとにrelation/peer差分同期を行い、相手なし会話でも監査headをstaleにしない。
- memory checkpointはSoul/Heart/Conversation/Semantic/Knowledgeの実保存先を対象にする。
- WORKING_MEMORY.jsonを生成しcognition contextから実際に使用する。canonical履歴は削除しない。
- v978 Heart、v979 Deep Soul、v982 continuity ledger、v983 homeostasis等をWhole Auditへ再結合。

主観・意識・文字どおりの魂/生命、一般L5/L6は主張しない。
