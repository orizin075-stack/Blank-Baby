# TUKUYO V1022.5 Fusion Experimental

V1022.4の復元・停止復旧・子個体監査と、添付claude-patch2の文章題・有限モデル論理・記憶質問・複数教師・道具・自習を統合した版です。V1022.1〜.3の多段推論、仮説比較、依存グラフ、探索打切り時の棄権も保持します。

既存技能seedのpayloadは両版で同一です。知識を重複して投入していません。個体のSoul・Heart・秘密鍵・死亡と継承の仕組みも保持します。LLMは未設定なら呼ばれません。

## 融合時の追加修正

- 速さ・単価・等分で否定された行動を実行済みと数えません。旧多段推論へ回り込んでも同じ拒否判定が働きます。既知の在庫問題の否定は、従来どおり実行量ゼロとして計算できます。
- 文章題の全数値を確認し、対応していない数値を捨てません。既存の割引・比率・方程式は既存推論で扱います。
- 複数品目の購入で旧ソルバーが後半の品目を落とす場合は、全数値を消費した新しい式を優先して再検算し、旧候補の値も結果へ記録します。速さの問いでも、求める量と単位を混同しません。
- 命題・大小関係の矛盾を、古い単方向推論の結論より優先します。論理の入力長・文数・節点数に上限を設けています。
- 雨の「降る／降らない／降っていない」を同じ命題の肯定と否定として扱います。二段以上の割引・値上げは、同じ商品への明示された順次操作を全段計算し、操作対象が曖昧なら棄権します。
- 新しい論理証明を元の質問へ、記憶証明を質問・実体・属性へ束縛して再検算します。これは有限の構文解析と証明再生であり、一般的な言語理解の証明ではありません。
- 同一のprovider/model/接続先/command設定を重複登録しても教師数が増えません。設定が違うことは、教師の誤りが統計的に独立している証拠にはなりません。全員の合議でも共通する系統誤りは除去できません。
- 自習の件数を1〜128に制限し、自習journalとheadも`llm-audit`で照合します。ハッシュ鎖だけで、journalとhead全体の共同改変や外部の巻戻しを防げるとは主張しません。

## 起動

プログラムを展開した`system`の外へanchorとdataを置きます。

```bash
python3 -B system/tools/verify_release.py system --trusted-pubkey-file TUKUYO_v1022_5_TRUST_ANCHOR.txt
python3 -B system/run_tukuyo.py --runtime-trust-file TUKUYO_v1022_5_TRUST_ANCHOR.txt --data ./individual init
python3 -B system/run_tukuyo.py --runtime-trust-file TUKUYO_v1022_5_TRUST_ANCHOR.txt --data ./individual think 'バスに12人乗っていて、5人降りて7人乗った。今何人？'
python3 -B system/run_tukuyo.py --runtime-trust-file TUKUYO_v1022_5_TRUST_ANCHOR.txt --data ./individual self-study --dry-run
```

教師を使う場合の設定は`README_CLAUDE_PATCH2_JA.md`と既存patch1のREADMEを参照してください。API鍵の値は保存する設定ファイルへ書かず、環境変数で渡します。自習は設定した教師へ対象質問を送ります。外部モデルの回答の検算範囲には限界があり、検証可能なclaimの検算と、自由文全体の真偽は別です。

V1022.4と同じ開発用publisher鍵で署名するため、V1022.4個体のruntime pinを取り替える必要はありません。添付patch2個体は別のpublisher鍵なので、旧anchorを明示した`runtime-trust-rebind`を使います。任意の自己署名seedは受け入れません。両親archiveとreceiptのhashは`META/PATCH_LINEAGE_v1022_5.json`へ記録しています。添付側publisherとの相互署名はありません。

## 検証範囲

最終実測は外部の融合検証報告を参照してください。V1022.4で観測したworkspace保存先の未来ファイル再出現とキャッシュ不一致は未解決として引き継ぎます。今回の試験成功を、全環境の安定性・24h運転・本物の複数AIとの長時間会話・一般知能・自然選択・自己コード改変・意識や文字通りの生命の証明には使いません。
