# TUKUYO v982 — Signed Restart Continuity Ledger
whole/heart/deep auditを通過した状態をEd25519署名付きcheckpoint chainへ記録し、別プロセス再起動後に同一個体・同一状態の継続を検証する。さらにhead hash・公開鍵・個体IDをdata root外のexternal anchorへ書き出し、root全体の巻き戻し／履歴書換えを検知できる。anchorは時刻証明ではないため、30日実時間継続の証明には用いない。
