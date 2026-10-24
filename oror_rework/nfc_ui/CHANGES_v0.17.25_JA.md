# OROR War × Nightfall 0.17.25 — NightfallCraft と同じ画面・戦闘の手触りへ

Minecraft 1.21.1 / NeoForge 21.1.262 / Java 21。0.17.24 を土台に、NightfallCraft 2.2.8.6 の画面と戦闘まわりを
1.21.1 で再現しました。追加した MOD・リソースパックは、NightfallCraft で使われていたもののうち 1.21.1 版があるものです。

## 消えていた表示を戻しました

- **スタミナ・ガード・パリィ・マナの表示（Ares HUD）**：0.17.22 の軽量化設定（compactHud=true）が Ares HUD を
  まるごと隠し、簡易な HP 表示だけを出していました。0.17.25 では Ares HUD を表示します。
  配置は NightfallCraft と同じ「中央下に1列のホットバー＋その上に HP・スタミナ・マナのバー」（HOTBAR_1X9）です。
  （config/oror-nightfall-patch.properties の compactHud=true で以前の簡易表示に戻せます）

## 画面（NightfallCraft と同じ）

- **タイトル画面・起動中のロード画面・ワールド読み込み画面**：NightfallCraft と同じ FancyMenu / Drippy Loading Screen の
  レイアウトです。画像は TCR Core（1.20.1 版のみ）のものなので、`SETUP_NIGHTFALL.cmd` が CurseForge から
  TCR Core 2.8.7（約39MB）を取得し、使う画像 25 枚だけを config/fancymenu/assets/nightfallcraft に置きます
  （1枚ずつ SHA-256 を照合。失敗してもゲームは遊べ、もう一度実行すれば入ります）。
- **GUI**：Modern UI（背景ぼかし・フォント。日本語は Yu Gothic UI / Meiryo UI を優先）、Mandala's GUI ダークモード＋
  KOTS 互換パック、Legendary Tooltips＋Eclectic Trove の枠、Item Borders、Enchantment Descriptions（＋Prickle）、
  Jade＋Jade Addons、Xaero's Minimap / World Map（NightfallCraft の設定）、Fancy Toasts、You Died、Chat Plus、InvMove、
  Mouse Tweaks、Visual Keybinder、Configured。
- **リソースパック**（新規プロファイルでは最初から有効）：Mandala's GUI Dark＋KOTS Compat、Eclectic Trove、
  剣の軌跡4種（EpicFight-Extra's Sword Trail Optimization、More Power Trail、BD&Hill Reforge the Sword Edge、
  Better Trident Model trail）、DMC5 yamato for Nightfall、Vulmoon's Cataclysm remake、True Nitwit、
  xali's Enhanced Vanilla、Stay True。1.21.1 の表記がないパックも、中身が 1.21.1 の Epic Fight と同じ形式
  （item_skins など）であることを確認して入れています。
- 言語は日本語、キー配置は NightfallCraft の初期設定（回避＝左Alt、モード切替＝F、ロックオン＝中ボタン など）。
  どちらも新規プロファイルの初回起動時だけ設定されます（Default Options）。

## 戦闘の手触り（NightfallCraft と同じ設定）

- Epic Fight：3人称カメラは常に Epic Fight のカメラ（横位置-4、距離7）、F5 で正面視点を飛ばす。武器を持つと自動で
  戦闘モード、素手で採掘モード。対象の武器は NightfallCraft の一覧のうちこのパックにあるものと、Epic Fight の武器設定を
  持つすべての武器（OROR のレリック武器・TCR 武器・Epic Knights・WOM・Cataclysm・Iron's Spells など 439 個）。
  ブロック採掘ガイドと対象ガイドは非表示（NightfallCraft と同じ）。
- Better Lock On（ロックオン、NightfallCraft の設定）、Combat Evolution の HUD 設定、Nightfall の VFX Plus 設定。
- 演出：AAA Particles（＋World）、P1nero's Bow、Cinematic Cataclysm（＋FDLib）、Better Trident Model。
- 音：Extra Sounds、Sound Physics Remastered、Medieval Music。
- 動作：Sodium 0.8、Entity Culling、FerriteCore、ModernFix、Sodium Dynamic Lights。

## 入れられなかったもの

- **シェーダー（Iris／Complementary）**：Create Aeronautics に同梱の Sable が Sodium 0.8.12 以上を必須にしていて、
  1.21.1 用の最新の Iris（1.8.12）は Sodium 0.6 でしか動きません（CI の実起動で、組み合わせるとワールド参加時に
  クラッシュすることを確認）。NightfallCraft も初期状態ではシェーダーはオフでした。
- 1.21.1 版がない NightfallCraft の MOD：Kill-Cam、Fancy Trail、EFN Enhance、TCR Core 本体と TCR のボス、
  Epic Fight のボス追加（Leonidas、Mimic、Arachne、Wraithon、Super Golem、Super Warden）など。

## 導入

- **新しいプロファイル（おすすめ）**：`OROR_War_Nightfall_v0.17.25_Import.zip` を展開せずに CurseForge へインポートし、
  起動前にプロファイルのフォルダーで `SETUP_NIGHTFALL.cmd` を1回実行します。追加の MOD とリソースパックは
  CurseForge が自動で入れます。
- **今の 0.17.23／0.17.24 のプロファイルを使い続ける場合**：追加の MOD は入りません。ゲームを終了し、`mods` の
  ORORの JAR を外して `OROR_War_Nightfall_v0.17.25_Patch.zip` の `mods/oror_supreme_bosses-0.17.25.jar` を入れ、
  `config` と `oror-install` をプロファイルへ上書きします。Ares HUD の表示と Epic Fight のカメラ・自動戦闘モードは
  これで戻ります。

## 検証の範囲

- GitHub Actions 上で、このパックの全 MOD（CurseForge から取得し SHA-256 を記録）を実際の NeoForge 21.1.262
  クライアントで起動しました（ソフトウェア描画）。タイトル画面 → ワールド新規作成 → ワールド内で、HUD・インベントリ・
  ポーズ画面・3人称カメラの画面写真を撮り、NeoForge の依存関係エラーもクラッシュもないことを確認しています。
  この過程で、Prickle・FDLib の不足、Sodium と Iris の組み合わせ、リソースパックが初回に選ばれない問題を見つけて直しました。
- セットアップの画像取得（PowerShell）は、実際の CurseForge からの取得・2回目の省略・壊れた画像の復元・通信失敗時を確認済み。
- CI の起動では Sword Soaring 互換版と falchion 互換版（配布物にだけ含まれる改変 JAR）を外しています。
- 実際の戦闘（パリィ・ロックオン・軌跡）、Windows での起動、マルチプレイは試していません。
