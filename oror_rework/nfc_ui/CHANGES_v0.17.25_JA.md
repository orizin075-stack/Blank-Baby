# OROR War × Nightfall 0.17.25 — 監査・修正、NightfallCraft の画面、満腹度なし

Minecraft 1.21.1 / NeoForge 21.1.262 / Java 21。いただいた 0.17.24（Native Combat Restoration：NightfallCraft の
敵の行動・Nightfall 本来のパリィを移植した版）を土台にしています。その中身はそのまま引き継ぎ、監査で見つけた不具合を
直し、画面と HUD を NightfallCraft に合わせ、満腹度をなくしました。

## 監査で見つけて直した不具合

- **通常ガードを選んでも Nightfall のパリィに戻される**：ガード枠が Epic Fight の通常ガードだと、1秒ごとに
  Nightfall のパリィへ付け替えていました。付け替えは最初の1回だけにし、その後スキル画面で通常ガードを選べば
  そのまま使えます。空のガード枠はこれまでどおり Nightfall のパリィで埋めます。
- **Nightfall／Indestructible がないと起動できない**：Nightfall や Indestructible のクラスへ組み込む処理が
  「必須」扱いで、`SETUP_NIGHTFALL.cmd` を実行していない場合や、手動更新で Indestructible の JAR を入れ忘れた場合に
  起動時のエラーで止まっていました。足りない MOD がある時はその処理を飛ばして起動し、ワールド参加時に
  「何が足りないか・どうすればよいか」を表示します。
- **村人が敵に気づかない**：待機中の AI 間引き（5tick ごと）が村人の警戒処理（10tick ごと）とずれ、5人に4人の村人が
  殴られるまで迎撃も避難もしていませんでした。村人は間引きの対象から外しました。
- **魔法武器の自動詠唱がマナ・クールダウンを無視**：TCR の魔法武器のダッシュ／空中攻撃の呪文が、マナ不足・
  クールダウン中・未習得でも発動していました。通常の詠唱と同じ確認を通し、発動できない理由をアクションバーに出します。
- **パリィ通知の安全化**：攻撃元のないダメージでパリィ判定が起きた時に、敵への通知処理が空の参照を扱わないようにしました。
- 名前が表示されなかった TCR の5アイテム（The Incinerator Soul と鞘4種）に日本語・英語・中国語の名前を追加しました。

確認した上で問題がなかった点：敵のスタミナ回復の補正は、Indestructible の該当処理にある1か所だけに効くこと
（ほかの防御判定を反転させないこと）、敵のパリィ受付が防御開始から6tickで閉じること（開始は1回だけ呼ばれること）。

## 満腹度をなくしました

- **Hunger Strike**（NightfallCraft と同じ設定）：満腹度は減らず、空腹で弱ることもありません。食べ物は満腹度の代わりに
  HP を回復します（食料値の 0.75 倍）。満腹度は常に半分のまま固定のため、自然回復はなく、ダッシュはできます
  （NightfallCraft と同じ。自然回復も欲しい場合は config/hungerstrike-common.toml の hungerBaseline を 18 に）。
- **HUD**：満腹度バーがあった場所（上段の右）に防御力（防具値）を表示します。上段の左が HP、下段がスタミナとマナです。

## HUD と画面（NightfallCraft と同じ）

- **スタミナ・ガード・パリィ・マナの表示（Ares HUD）を戻しました**：0.17.22 からの軽量化設定（compactHud=true）が
  Ares HUD をまるごと隠し、標準のホットバーと割合ハートだけにしていました。0.17.25 では NightfallCraft と同じ
  「中央下に1列のホットバー、その上に HP・防御力・スタミナ・マナのバー」（Ares HUD の HOTBAR_1X9）です。
  （config/oror-nightfall-patch.properties の compactHud=true で以前の表示に戻せます）
- **タイトル画面・起動中のロード画面・ワールド読み込み画面**：NightfallCraft と同じ FancyMenu / Drippy Loading Screen の
  レイアウトです。タイトル画面は NightfallCraft と同じく、Minecraft のロゴ・スプラッシュ文字・左下のバージョン表記を出さず
  （右下の Mojang の著作権表示は、1.21.1 の FancyMenu が必ず表示するため残ります）、左下に「終了・アクセシビリティ・Mod・言語・設定・Discord」のアイコンが並びます（1.21.1 では言語と
  アクセシビリティのボタンの内部名が変わり、そのままでは元の位置に残って文字と重なっていたのを直しました）。
  Create の設定ボタン（ゴーグル）と Ice and Fire の独自タイトル画面はタイトルに出しません（Create の設定は「Mod」から開けます）。
  アイコンにマウスを乗せた時の説明も日本語で出ます。
- **メニュー（ボタン・タブ・区切り線・背景）**：NightfallCraft のメニューの見た目は、NightfallCraft の中核 MOD
  「TCR Core」が出していました（ボタンの画像の差し替え、タブと区切り線の差し替え、土の背景の代わりに月夜のぼかし絵）。
  TCR Core は 1.20.1 版しかないため、OROR がその画像から 1.21.1 用のボタン・タブ・区切り線を作る内蔵パック
  「NightfallCraft GUI (TCR Core)」を常に適用し、ワールドの外で開くメニューには同じ背景を表示します。
- **画像の取得**：タイトル画面とメニューの画像は TCR Core のものなので、`SETUP_NIGHTFALL.cmd` が CurseForge から
  TCR Core 2.8.7（約39MB）を取得し、使う画像 33 枚だけを config/fancymenu/assets/nightfallcraft に置きます
  （1枚ずつ SHA-256 を照合。失敗してもゲームは遊べ、もう一度実行すれば入ります）。
- **リソースパック**：NightfallCraft と同じく、最初はどれも無効です（NightfallCraft は初期設定ファイルを持たず、
  Mandala の暗い GUI なども最初は無効でした）。NightfallCraft に入っていたパック（Mandala's GUI ダークモード、
  剣の軌跡4種、DMC5 yamato、Eclectic Trove、Stay True、xali's Enhanced Vanilla、True Nitwit、Vulmoon's）は導入済みなので、
  「設定 → リソースパック」から有効にできます。
- Modern UI（背景ぼかし・フォント。日本語は Yu Gothic UI / Meiryo UI を優先）、Legendary Tooltips、Item Borders、
  Enchantment Descriptions（＋Prickle）、Jade、Xaero's Minimap / World Map、Fancy Toasts、You Died、Chat Plus、
  InvMove、Mouse Tweaks、Visual Keybinder、Configured。
- 言語は日本語、キー配置は NightfallCraft の初期設定（回避＝左Alt、モード切替＝F、ロックオン＝中ボタン など）。
  どちらも新規プロファイルの初回起動時だけ設定されます（Default Options）。

## 戦闘の手触り（NightfallCraft と同じ設定）

- Epic Fight：3人称カメラは常に Epic Fight のカメラ（横位置-4、距離7）、F5 で正面視点を飛ばす。武器を持つと自動で
  戦闘モード、素手で採掘モード（対象は NightfallCraft の一覧のうちこのパックにある武器と、Epic Fight の武器設定を持つ
  すべての武器 439 個）。ブロック採掘ガイドと対象ガイドは非表示。
- Better Lock On（ロックオン）、Combat Evolution の HUD、Nightfall の VFX Plus は NightfallCraft の設定。
- 演出：AAA Particles、P1nero's Bow、Cinematic Cataclysm（＋FDLib）、Better Trident Model。音：Extra Sounds、Sound Physics Remastered、Medieval Music。
- 動作：Sodium 0.8、Entity Culling、FerriteCore、ModernFix、Sodium Dynamic Lights。

## 入れられなかったもの

- **シェーダー（Iris）**：Create Aeronautics に同梱の Sable が Sodium 0.8.12 以上を必須にしていて、1.21.1 用の
  最新の Iris（1.8.12）は Sodium 0.6 でしか動きません（実起動でワールド参加時のクラッシュを確認）。
  NightfallCraft も初期状態ではシェーダーはオフでした。
- 1.21.1 版がない NightfallCraft の MOD：Kill-Cam、Fancy Trail、EFN Enhance、TCR Core 本体と TCR のボス、
  Epic Fight のボス追加（Leonidas、Mimic、Arachne など）。

## 導入

- **新しいプロファイル（おすすめ）**：`OROR_War_Nightfall_v0.17.25_Import.zip` を展開せずに CurseForge へインポートし、
  起動前にプロファイルのフォルダーで `SETUP_NIGHTFALL.cmd` を1回実行します（Nightfall・御剣・タイトル画面の画像を
  取得）。追加の MOD とリソースパックは CurseForge が自動で入れます。
- **0.17.24 のプロファイルを使い続ける場合**：追加の MOD（Hunger Strike・UI 関係）は入りません。ゲームを終了し、
  `mods` の `oror_supreme_bosses-0.17.24.jar` を外して `OROR_War_Nightfall_v0.17.25_Patch.zip` の `mods` の中身を入れ、
  `config` と `oror-install` をプロファイルへ上書きします。Ares HUD の表示、Epic Fight のカメラ・自動戦闘モード、
  不具合修正はこれで入ります。

## 検証の範囲

- 変更したクラスは、NeoForge 21.1.262 とパックと同じ版の実 JAR（Epic Fight・Iron's Spells・Nightfall・Indestructible・
  Dodge Parry Reward など。CurseForge から取得し SHA-256 を記録）に対して GitHub Actions 上でコンパイルしました。
- このパックの全 MOD を実際の NeoForge クライアントで起動し（ソフトウェア描画）、タイトル画面 → 設定画面 →
  ワールド新規作成 → ワールド内で HUD・インベントリ・ポーズ画面・3人称の画面写真を撮り、依存関係のエラーやクラッシュが
  ないこと、満腹度の代わりに防御力が出ること、Nightfall のパリィが装備されることを確認しました。
- NightfallCraft のメニューとタイトル画面の作りは、TCR Core 2.8.7 と FancyMenu 3.9.14（1.20.1 / 1.21.1）の該当コードと
  画像を読んで確認しました。NightfallCraft 2.2.8.6 本体も同じ方法で起動し（公開版のままでは依存関係の不整合で起動しない
  ため、画面に関係しない MOD を数個外しています）、タイトル画面を撮影して比べました。CI 上ではタイトル画面までで
  止まり、FancyMenu の配置も適用されなかったため、ワールド内やメニューの比較写真は撮れていません。
- セットアップの画像取得（PowerShell）は、実際の CurseForge からの取得・2回目の省略・壊れた画像の復元・通信失敗時を確認済み。
- CI の起動では、Sword Soaring 互換版と falchion 互換版（配布物にだけ含まれる改変 JAR）は外し、Indestructible は
  互換版の元になった公式の fork 版を使っています。
- 実際の戦闘（パリィ・ロックオン・軌跡）、Windows での起動、マルチプレイは試していません。

OROR JAR SHA-256：`68f6f96def5bec5c49b94eb8f610f63bcd23e1ed252d2427c65c8262c739f526`
