# TUKUYO v1008 — Whole Living Cognition

v1008は、v1003の認知provider/RAG基盤を、検証付きtool reasoning・未知規則研究・拡張homeostasis・自己保存・不可逆mortalityへ接続した統合研究版です。

## v1004 Tool Deliberation
許可されたcalculator / memory_search / self_stateだけを使うbounded tool loop。高性能provider接続時も外部コマンドをTUKUYO自身が任意実行することはありません。

## v1005 Verified Reasoning
候補回答を検証し、agreementとconfidenceを記録します。低信頼はuncertainとして残します。これは一般的な真理判定器ではありません。

## v1006 Autonomous Research
未知の記号規則に対し、仮説集合を作り、仮説の予測が最も分かれるprobeを能動選択し、fresh holdoutで検証します。6/6 domainで同定するbounded assayです。一般AGIやcross-domain知能の証明ではありません。

## v1007 Organism 2 / Mortality
energy, integrity, cognitive_load, social_need, information_need, purpose_coherence, damage, threatを内部状態として保持します。負傷時は破壊リスクへの重みが増え、自己保存選択に直接影響します。ALIVE→INJURED→CRITICAL→DEADを持ち、DEADは同一個体内で不可逆です。

## v1008 Whole Living Cognition
認知作業→必要に応じた研究→検証付き回答→内部維持を1 cycleに統合します。内部維持は自律実行できますが、外部への無断行動は行いません。死亡個体はcycleを拒否します。死亡後に作れるsuccessor seedは別個体で、episodic memoryは継承しません。

## AI性能について
軽量内蔵コア単独がGPT-4級になったわけではありません。高性能LLM providerを接続した場合、その言語・推論能力をTUKUYOのidentity/memory/purpose/relation/auditと統合して利用できます。内蔵側では安全計算、検索、bounded tool use、検証、未知規則研究を提供します。

## claim boundary
consciousness / literal soul / literal biological life / general AGI / GPT-4-equivalent standalone capability は未確立です。実装されているのは反証可能な機能モデルです。
