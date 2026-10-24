# OROR War × Nightfall 0.17.25 — NightfallCraft と同じ画面・戦闘の手触りへ

Minecraft 1.21.1 / NeoForge 21.1.262 / Java 21。0.17.24 を土台に、NightfallCraft 2.2.8.6 の画面と戦闘まわりを
1.21.1 で再現しました。

## 消えていた表示を戻しました

- **スタミナ・ガード・パリィ・マナの表示（Ares HUD）**：0.17.22 の軽量化設定（compactHud=true）が Ares HUD を
  まるごと隠し、代わりに簡易HPだけを描いていました。0.17.25 では既定で Ares HUD を表示します
  （config/oror-nightfall-patch.properties の compactHud=false。true にすると以前の簡易表示に戻ります）。

## NightfallCraft と同じ設定にしました（Epic Fight）

- 3人称カメラを常に Epic Fight のカメラにする（camera_mode=ALWAYS、横位置-4、距離7）。F5 で正面視点を飛ばす。
- 武器を持つと自動で戦闘モード、素手で採掘モード（camera_auto_switch とお気に入りアイテム一覧）。
  一覧は NightfallCraft の一覧のうちこのパックにある武器と、Epic Fight の武器設定を持つすべての武器
  （OROR のレリック武器・TCR 武器を含む）から作っています。
- ブロック採掘ガイドと対象ガイドを非表示、コスメ非表示、コンピュートシェーダー有効（NightfallCraft と同じ）。
- キー配置：NightfallCraft の初期キー配置（回避＝左Alt、モード切替＝F、ロックオン＝中ボタン など）。新規プロファイルのみ。

<!-- 追加MOD・検証結果はCIの結果を見て書く -->
