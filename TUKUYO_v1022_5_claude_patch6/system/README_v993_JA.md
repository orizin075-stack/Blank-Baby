# TUKUYO v993 — Relation-Bound Scar / Attachment

v993は、v977以来SOUL_COREへ記録されていた`relation`を選択計算へ接続する層です。従来はscarに`relation: peerX`が保存されても、選択時には主としてtheme一致だけが参照されていました。v993ではSOUL_EVENTSを決定論的に再演し、相手IDごとにtrust / attachment / scar_load / risk / support_loadを再構成します。

`relation-choose`では、各候補の通常のvalue scoreに、**その相手との履歴だけ**から導いたrelation adjustmentを加えます。このためpeerXが過去の`broken_promise`を`collaboration`へ言い換えても、peerXへのscarは消えません。一方、履歴のないpeerYにはpeerXの傷を転写しません。表層episodic memoryを消してもSOUL_EVENTSとscarに基づくrelation modelは残ります。

境界: これは相手別の機能的関係モデルであり、他者の主観を理解したこと、文字どおりの愛着、Theory of Mindを確立したことを意味しません。
