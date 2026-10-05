# TUKUYO v1014.1 — Integrity / Semantic / Scale Repair

v1014 fresh外部実験で見つかった3つの合否停止問題と、検索スケーリング問題を修正する保守リリース。

- recovery signer continuity: 初回checkpointより前に鍵を確立し、公開鍵欠損時は秘密鍵から同一公開鍵を再導出する。片側欠損で黙って鍵ローテーションしない。
- independent semantic verification: verified-queryは回答器のcore_reasoningを自己検証に再利用せず、別実装でquery role / entity / exactness / unit / event balanceを検査する。
- whole-state transaction closure: LAST_VERIFIED_REASONING更新後にunified whole stateを同じsolve遷移内で同期する。
- indexed retrieval scaling: rare-token候補面を優先し、common queryは候補数をboundedにし、候補文書とpostingをbatch取得する。

24h / 72h / 7day実時間運転、書込途中・restore commit途中の電源断相当試験、正本H3/H4、第三者再現は未完了。

- stdlib fallback selftest: `tmp_path` を必要とする v1000–v1003 の4テストも一時ディレクトリ注入で実行する。
