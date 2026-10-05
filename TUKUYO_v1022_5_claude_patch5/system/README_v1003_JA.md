# TUKUYO v1000-v1003 Cognitive Backbone

## 目的
v999までの個体・心・魂・関係・grounded closed-world loopを保持したまま、AIとしての実用知能を引き上げるための認知バックボーンを追加する。

## v1000 Provider Boundary
高性能言語モデルをTUKUYO本体から分離した交換可能providerとして接続する。`TUKUYO_LLM_COMMAND`にJSON stdin/stdout対応コマンドを明示設定した場合だけ使用する。providerへ渡すのは質問、TUKUYOの目的/同一性/peer状態、検索済み証拠であり、個体状態の正本はTUKUYO側に残る。provider未設定でも軽量builtin cognitionは動作する。

## v1001 Local Retrieval Memory
UTF-8日本語/英語に対応した軽量BM25系検索を追加。TUKUYO自身のknowledge storeへ文書を追加し、質問に関連する証拠を取得できる。大規模埋め込みモデルは同梱しない。

## v1002 Cognitive Orchestrator
安全な算術評価、ローカル検索、TUKUYO状態のcontext化、外部provider呼び出し、回答ログを統合する。chat入力は従来どおりheart/semanticへ入り、その後cognitive answerを生成する。

## v1003 Capability Benchmark
最低限の算術・検索・RAG回答をfresh data rootで検証する。これはGPT-4相当性能の証明ではない。高性能provider接続時にTUKUYOの個体アーキテクチャを保ったまま言語・推論能力を増幅できることを目的とする。

## 境界
- 14MB級のstandaloneコア自体がGPT-4級モデルになったわけではない。
- 大規模一般知識・高度な自然言語推論は接続providerの性能に依存する。
- providerはlive stateを直接書換えない。TUKUYOの状態更新は既存の監査対象経路で行う。
- unattended external action / auto-promotionは導入しない。
