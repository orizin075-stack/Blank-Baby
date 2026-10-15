# TUKUYO v956 — Blind Representation-Gap Discovery

外部Challenge Authorityが未知suiteをsalt付きcommitし署名した後、revealする。TUKUYOはcommitment前像を検証してからsearch evidenceを自分でfresh再計算する。外部由来の分類ラベルや探索summaryは信用しない。

fresh外部別鍵デモでは36件suiteでfull searchがREPRESENTATION_INSUFFICIENT、同じsuiteのbudget=2ではSEARCH_INSUFFICIENT。

これはbounded known class (ADD/SUB/MUL/MAX/MIN) 上のgap判定であり、未知primitiveを発明するv957とは別。
