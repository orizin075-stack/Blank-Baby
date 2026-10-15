# TUKUYO v1022.7.8 — 個体史と未知数量の検証

開発・実験版。基準は `TUKUYO_v1022_7_7_gen4_r7.zip`、SHA-256 `3ddd37c2d8b8e66fe2f2974c15b5b348528069d79e164fa34a853650050bde96`。既存Soul、Heart、G4、代謝、継承、教師接続のコードを保持します。判定は別添の検証報告を参照してください。

## 共有する外部台帳

一つの署名付き台帳を個体の外へ置き、参加者が同じ公開鍵ピンで照合します。Whole Stateには署名付き登録情報の内容ハッシュを束縛します。登録したCLIは台帳引数を必須とし、台帳と個体の書込みロックで照合・操作・受理を直列化します。直接APIを呼ぶ場合は `identity_ledger.guard` を使用してください。

同一IDや同一Whole鍵の重複登録、共有台帳に受理済みの履歴と異なる複製、古い受領証・個体状態、台帳が観測した死亡後の生存コピーを拒否します。PREPARED後の停止は同じ遷移を一度だけredoします。受領証の復旧は外部台帳が受理した状態に完全一致する場合に限定します。

`identity-ledger-branch` は、別ID・別Whole鍵で初期化済みの個体を双方の署名で関連付けます。この操作自体は子個体を作らず、私的な自伝・鍵も移しません。従来の死後継承とは別の登録操作です。

```bash
python -B tools/identity_ledger_admin.py create --ledger /tmp/tukuyo-witness
python -B run_tukuyo.py --data /tmp/tukuyo-parent init --individual-id PARENT-78
python -B run_tukuyo.py --data /tmp/tukuyo-parent --identity-ledger /tmp/tukuyo-witness --identity-ledger-trust-file /tmp/tukuyo-witness/witness.pub identity-ledger-enroll
python -B run_tukuyo.py --data /tmp/tukuyo-parent --identity-ledger /tmp/tukuyo-witness --identity-ledger-trust-file /tmp/tukuyo-witness/witness.pub heart-experience learning .8 .8 --theme example
python -B tools/identity_ledger_verifier.py --ledger /tmp/tukuyo-witness --trust-file /tmp/tukuyo-witness/witness.pub --data /tmp/tukuyo-parent
```

配布署名を明示的にピンするときはCLIへ `--runtime-trust-file /absolute/TUKUYO_v1022_7_8_TRUST_ANCHOR.txt` も渡してください。これは公開鍵です。個体データを署名された配布ソースの中に作らないでください。

登録済み個体のinteractive chatと同一IDへのrecovery-restoreは、この実験版では操作前に拒否します。過去のcheckpointを別IDへ移植する機能と、死後successor全個体の台帳への自動登録は未実装です。別台帳に登録済みの子を同時操作する複合構成は検証範囲外です。

### 保証の範囲

この同じ台帳へ提出された履歴の衝突を検出する機構です。物理的なコピーの存在・防止、世界中の個体の一意性、外界の観測の真偽を証明しません。台帳と個体を両方丸ごと巻き戻せる管理者に対する保護はありません。外部の単調カウンターは未導入です。署名者は実験用のローカル運営者で、現実の独立した第三者ではありません。台帳鍵を管理する運営者を信頼する必要があります。

Linuxで検証する構成です。Windows/macOSは未検証です。全履歴を読み直す方式のため、大規模・長期の性能は未測定です。登録していない既存個体の操作は従来どおりです。

## 未知量の検証

`a few`、`an unknown number of`、`a handful of`などをゼロとして省略せず、未知量として扱います。生成側とは別の字句検査器が、不明の数量表現と解答に関連する形式変数・原文出典の対応を点検します。関係する未知量が形式化されていない解は `UNKNOWN_QUANTITY_NOT_ACCOUNTED` で拒否します。無関係な未知変数を足して対応したふりをする翻訳も拒否します。

未知量があっても、残量や比率等の条件から一意に答えが決まる既存の問題は解くことができます。有限な英語表現に対する処理であり、完全に独立した意味理解や一般的な自然言語理解を証明するものではありません。

## 未達と署名

主観意識・文字どおりの魂、汎用知能、自己コード改変、24h/72h/7日の稼働、実LLM教師との長時間学習は今回証明していません。workspaceの未来ファイル再出現の根本原因も未解明です。この台帳はその原因を修正する機能ではありません。

魂の評価点を別の尺度と混ぜて更新せず、機能ごとの証明を報告します。今回のパッチ署名は開発用の鍵によるもので、元の発行者の承認を意味しません。配布はr7のsystemを基準としたcompact形式です。外側の過去研究資料は元のr7 ZIPにあります。
