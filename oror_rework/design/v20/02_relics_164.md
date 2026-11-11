# V19｜神討伐報酬164品：現行効果命令・動作・FX・未実装の線引き

元の`relics.json`と`relic_arts.json`、戦利品のアイテム修飾子を対象にした。`damage`は登録パラメータであり、実ダメージではない。`cd`はtick。神威触媒・神格装飾品は**手持ち／設置アイテムではなく、Curiosアクセサリースロットに装備する神具**。

`cast`は発動命令、`passive`は常時命令、`hit`は命中命令。各命令のパラメータを省かず記載する。「実際に各tickで描画される」ことの実機確認は未完了。V15設計資料にある独立武器技123件は**未実装案**。

## 01. 剣神 炬珀

**モブ側の動きの方向性**：足裏から腰、肩、手首、刀先へ伝える精密な剣術。鞘と刀を独立駆動する。。

### 蒼白断界刀・虚 — 討伐武器（メイン／武器欄） (`kokuhaku_weapon`)

**現行パラメータ**：rank=1、damage登録値=316.66667、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:sweeping_edge:25。

**装備中の常時命令（5命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"speed","t":40,"a":1}` — 強化〔e="speed", t=40, a=1〕
03. `{"op":"reflect","t":25,"r":5}` — 反射〔t=25, r=5〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（8命令）**：

01. `{"op":"around","r":3.5,"n":16,"exclude":1}` — around〔r=3.5, n=16, exclude=1〕
02. `{"op":"dmg","m":0.3}` — 追加攻撃〔m=0.3〕
03. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"slow","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"slow","t":90,"a":0}]〕
04. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":9,"at":"t","s":0.24},{"op":"mark","t":120,"x":1.65},{"op":"eff","e":"slow","t":55,"a":1}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":9,"at":"t","s":0.24},{"op":"mark","t":120,"x":1.65},{"op":"eff","e":"slow","t":55,"a":1}]〕
05. `{"op":"chance","p":0.15,"ops":[{"op":"victim"},{"op":"dmg","m":0.2}]}` — 抽選〔p=0.15, ops=[{"op":"victim"},{"op":"dmg","m":0.2}]〕
06. `{"op":"chance","p":0.085,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":8,"at":"t","s":0.25},{"op":"strip"}]}` — 抽選〔p=0.085, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":8,"at":"t","s":0.25},{"op":"strip"}]〕
07. `{"op":"chance","p":0.18,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.18, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]〕
08. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]〕

**権能発動時の命令（27命令）**：

01. `{"op":"fx","p":"crit","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="crit", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"crit","n":4,"at":"self","s":0.7}` — 粒子演出〔p="crit", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"ash","n":40,"at":"self","s":1.2}` — 粒子演出〔p="ash", n=40, at="self", s=1.2〕
04. `{"op":"fx","p":"rportal","n":30,"at":"self"}` — 粒子演出〔p="rportal", n=30, at="self"〕
05. `{"op":"sound","s":"sonic","v":0.8,"pi":1.4}` — 効果音〔s="sonic", v=0.8, pi=1.4〕
06. `{"op":"line","r":28,"w":3}` — 線分対象の取得〔r=28, w=3〕
07. `{"op":"dmg","m":1.8}` — 追加攻撃〔m=1.8〕
08. `{"op":"stun","t":60}` — 行動停止〔t=60〕
09. `{"op":"mark","t":160,"x":1.5}` — 刻印〔t=160, x=1.5〕
10. `{"op":"fx","p":"sonic","n":10,"at":"line","r":28}` — 粒子演出〔p="sonic", n=10, at="line", r=28〕
11. `{"op":"blink","d":12}` — blink〔d=12〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"fx","p":"crit","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="crit", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"end_rod","n":36,"at":"line","r":24}` — 粒子演出〔p="end_rod", n=36, at="line", r=24〕
15. `{"op":"line","r":54.0,"w":3.0}` — 線分対象の取得〔r=54.0, w=3.0〕
16. `{"op":"dmg","m":2.9}` — 追加攻撃〔m=2.9〕
17. `{"op":"strip"}` — 強化解除〔〕
18. `{"op":"mark","t":140,"x":1.7}` — 刻印〔t=140, x=1.7〕
19. `{"op":"fx","p":"crit","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="crit", n=16, at="ring", r=5.0〕
20. `{"op":"sound","s":"sonic","v":0.75,"pi":1.15}` — 効果音〔s="sonic", v=0.75, pi=1.15〕
21. `{"op":"line","r":18,"w":2}` — 線分対象の取得〔r=18, w=2〕
22. `{"op":"dmg","m":1.05}` — 追加攻撃〔m=1.05〕
23. `{"op":"eff","e":"slow","t":65,"a":0}` — 敵への状態異常〔e="slow", t=65, a=0〕
24. `{"op":"fx","p":"crit","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="crit", n=24, at="ring", r=4.5, y=0.6〕
25. `{"op":"sound","s":"sonic","v":0.8,"pi":0.8}` — 効果音〔s="sonic", v=0.8, pi=0.8〕
26. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
27. `{"op":"eff","e":"slow","t":32,"a":124}` — 敵への状態異常〔e="slow", t=32, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 無音の鞘 — 神威触媒（Curios relic_focus） (`kokuhaku_focus`)

**現行パラメータ**：rank=2、damage登録値=75.8241、relics側CD=160tick、art側CD=160tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"reflect","t":25,"r":7}` — 反射〔t=25, r=7〕
03. `{"op":"buff","e":"speed","t":40,"a":0}` — 強化〔e="speed", t=40, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"speed","t":45,"a":0}` — 強化〔e="speed", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"speed","t":45,"a":2}` — 強化〔e="speed", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"speed","t":42,"a":2}` — 強化〔e="speed", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（41命令）**：

01. `{"op":"fx","p":"crit","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="crit", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"crit","n":6,"at":"self","s":0.7}` — 粒子演出〔p="crit", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"ash","n":40,"at":"self","s":1.2}` — 粒子演出〔p="ash", n=40, at="self", s=1.2〕
04. `{"op":"fx","p":"rportal","n":30,"at":"self"}` — 粒子演出〔p="rportal", n=30, at="self"〕
05. `{"op":"sound","s":"sonic","v":0.8,"pi":1.4}` — 効果音〔s="sonic", v=0.8, pi=1.4〕
06. `{"op":"area","r":24,"n":36}` — 円形対象の取得〔r=24, n=36〕
07. `{"op":"stun","t":90}` — 行動停止〔t=90〕
08. `{"op":"erase","r":24}` — erase〔r=24〕
09. `{"op":"guard","t":60}` — 防御〔t=60〕
10. `{"op":"fx","p":"ash","n":60,"at":"ring","r":6}` — 粒子演出〔p="ash", n=60, at="ring", r=6〕
11. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"speed","t":150,"a":1}` — 強化〔e="speed", t=150, a=1〕
14. `{"op":"fx","p":"end_rod","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="end_rod", n=50, at="ring", r=8.0, y=0.6〕
15. `{"op":"fx","p":"enchant","n":32,"at":"line","r":30}` — 粒子演出〔p="enchant", n=32, at="line", r=30〕
16. `{"op":"sound","s":"sonic","v":1.15,"pi":0.95}` — 効果音〔s="sonic", v=1.15, pi=0.95〕
17. `{"op":"area","r":12.0,"n":12}` — 円形対象の取得〔r=12.0, n=12〕
18. `{"op":"stun","t":40}` — 行動停止〔t=40〕
19. `{"op":"erase","r":12.0}` — erase〔r=12.0〕
20. `{"op":"dmg","m":1.4}` — 追加攻撃〔m=1.4〕
21. `{"op":"self"}` — 対象を自分へ〔〕
22. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
23. `{"op":"buff","e":"speed","t":150,"a":3}` — 強化〔e="speed", t=150, a=3〕
24. `{"op":"fx","p":"crit","n":24,"at":"ring","r":10,"y":0.5}` — 粒子演出〔p="crit", n=24, at="ring", r=10, y=0.5〕
25. `{"op":"sound","s":"sonic","v":0.85,"pi":0.9}` — 効果音〔s="sonic", v=0.85, pi=0.9〕
26. `{"op":"line","r":28.0,"w":2.5}` — 線分対象の取得〔r=28.0, w=2.5〕
27. `{"op":"dmg","m":0.85}` — 追加攻撃〔m=0.85〕
28. `{"op":"eff","e":"slow","t":100,"a":1}` — 敵への状態異常〔e="slow", t=100, a=1〕
29. `{"op":"self"}` — 対象を自分へ〔〕
30. `{"op":"buff","e":"speed","t":200,"a":3}` — 強化〔e="speed", t=200, a=3〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"reflect","t":80,"r":14}` — 反射〔t=80, r=14〕
33. `{"op":"fx","p":"crit","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="crit", n=24, at="ring", r=5.5, y=0.7〕
34. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
35. `{"op":"eff","e":"slow","t":43,"a":123}` — 敵への状態異常〔e="slow", t=43, a=123〕
36. `{"op":"self"}` — 対象を自分へ〔〕
37. `{"op":"buff","e":"speed","t":120,"a":4}` — 強化〔e="speed", t=120, a=4〕
38. `{"op":"fx","p":"crit","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="crit", n=16, at="ring", r=3.7, y=0.55〕
39. `{"op":"cone","r":12,"a":100}` — 扇形対象の取得〔r=12, a=100〕
40. `{"op":"eff","e":"slow","t":50,"a":5}` — 敵への状態異常〔e="slow", t=50, a=5〕
41. `{"op":"knock","f":2.1}` — knock〔f=2.1〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 封龍の尾環 — 神格装飾品（Curios relic_charm） (`kokuhaku_charm`)

**現行パラメータ**：rank=1、damage登録値=75.8241、relics側CD=190tick、art側CD=190tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（14命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"speed","t":40,"a":2}` — 強化〔e="speed", t=40, a=2〕
03. `{"op":"buff","e":"jump","t":40,"a":1}` — 強化〔e="jump", t=40, a=1〕
04. `{"op":"reflect","t":25,"r":6}` — 反射〔t=25, r=6〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"speed","t":45,"a":0}` — 強化〔e="speed", t=45, a=0〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
09. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
10. `{"op":"buff","e":"speed","t":45,"a":1}` — 強化〔e="speed", t=45, a=1〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"speed","t":42,"a":2}` — 強化〔e="speed", t=42, a=2〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"speed","t":48,"a":5}` — 強化〔e="speed", t=48, a=5〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（36命令）**：

01. `{"op":"fx","p":"crit","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="crit", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"crit","n":4,"at":"self","s":0.7}` — 粒子演出〔p="crit", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"ash","n":40,"at":"self","s":1.2}` — 粒子演出〔p="ash", n=40, at="self", s=1.2〕
04. `{"op":"fx","p":"rportal","n":30,"at":"self"}` — 粒子演出〔p="rportal", n=30, at="self"〕
05. `{"op":"sound","s":"sonic","v":0.8,"pi":1.4}` — 効果音〔s="sonic", v=0.8, pi=1.4〕
06. `{"op":"area","r":8,"n":36}` — 円形対象の取得〔r=8, n=36〕
07. `{"op":"dmg","m":0.6}` — 追加攻撃〔m=0.6〕
08. `{"op":"knock","f":3.0}` — knock〔f=3.0〕
09. `{"op":"fx","p":"crit","n":40,"at":"ring","r":4}` — 粒子演出〔p="crit", n=40, at="ring", r=4〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"speed","t":210,"a":1}` — 強化〔e="speed", t=210, a=1〕
13. `{"op":"fx","p":"crit","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="crit", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"end_rod","n":36,"at":"line","r":24}` — 粒子演出〔p="end_rod", n=36, at="line", r=24〕
15. `{"op":"sound","s":"sonic","v":1.05,"pi":1.14}` — 効果音〔s="sonic", v=1.05, pi=1.14〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"guard","t":95}` — 防御〔t=95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
20. `{"op":"cleanse"}` — 状態異常解除〔〕
21. `{"op":"buff","e":"speed","t":180,"a":3}` — 強化〔e="speed", t=180, a=3〕
22. `{"op":"guard","t":95}` — 防御〔t=95〕
23. `{"op":"fx","p":"crit","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="crit", n=30, at="ring", r=4.0, y=0.7〕
24. `{"op":"sound","s":"sonic","v":0.8,"pi":1.1}` — 効果音〔s="sonic", v=0.8, pi=1.1〕
25. `{"op":"self"}` — 対象を自分へ〔〕
26. `{"op":"buff","e":"speed","t":260,"a":4}` — 強化〔e="speed", t=260, a=4〕
27. `{"op":"guard","t":125}` — 防御〔t=125〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"reflect","t":80,"r":14}` — 反射〔t=80, r=14〕
30. `{"op":"fx","p":"crit","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="crit", n=20, at="ring", r=4, y=0.4〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"speed","t":120,"a":4}` — 強化〔e="speed", t=120, a=4〕
33. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
34. `{"op":"eff","e":"slow","t":32,"a":123}` — 敵への状態異常〔e="slow", t=32, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 剣理終極・虚無一閃 — 超越神器（武器欄） (`kokuhaku_legend`)

**現行パラメータ**：rank=3、damage登録値=479.75、relics側CD=345tick、art側CD=345tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:sweeping_edge:25。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"buff","e":"speed","t":40,"a":2}` — 強化〔e="speed", t=40, a=2〕
06. `{"op":"reflect","t":25,"r":12}` — 反射〔t=25, r=12〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
09. `{"op":"buff","e":"speed","t":45,"a":3}` — 強化〔e="speed", t=45, a=3〕
10. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（8命令）**：

01. `{"op":"chain","n":6,"r":12}` — chain〔n=6, r=12〕
02. `{"op":"dmg","m":0.5}` — 追加攻撃〔m=0.5〕
03. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"slow","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"slow","t":160,"a":1}]〕
04. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
05. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"crit","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"crit","n":10,"at":"t","s":0.35}]〕
06. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
07. `{"op":"chance","p":0.3,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.3, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]〕
08. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]〕

**権能発動時の命令（27命令）**：

01. `{"op":"fx","p":"crit","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="crit", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"crit","n":4,"at":"self","s":0.7}` — 粒子演出〔p="crit", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"ash","n":40,"at":"self","s":1.2}` — 粒子演出〔p="ash", n=40, at="self", s=1.2〕
04. `{"op":"fx","p":"rportal","n":30,"at":"self"}` — 粒子演出〔p="rportal", n=30, at="self"〕
05. `{"op":"sound","s":"sonic","v":0.8,"pi":1.4}` — 効果音〔s="sonic", v=0.8, pi=1.4〕
06. `{"op":"line","r":64,"w":5}` — 線分対象の取得〔r=64, w=5〕
07. `{"op":"dmg","m":3.36}` — 追加攻撃〔m=3.36〕
08. `{"op":"stun","t":105}` — 行動停止〔t=105〕
09. `{"op":"mark","t":400,"x":3.0}` — 刻印〔t=400, x=3.0〕
10. `{"op":"fx","p":"sonic","n":16,"at":"line","r":64}` — 粒子演出〔p="sonic", n=16, at="line", r=64〕
11. `{"op":"area","r":32,"n":36}` — 円形対象の取得〔r=32, n=36〕
12. `{"op":"dmg","m":1.12}` — 追加攻撃〔m=1.12〕
13. `{"op":"stun","t":100}` — 行動停止〔t=100〕
14. `{"op":"erase","r":48}` — erase〔r=48〕
15. `{"op":"guard","t":100}` — 防御〔t=100〕
16. `{"op":"blink","d":16}` — blink〔d=16〕
17. `{"op":"fx","p":"sonic","n":12,"at":"t","s":0.5}` — 粒子演出〔p="sonic", n=12, at="t", s=0.5〕
18. `{"op":"line","r":64,"w":3}` — 線分対象の取得〔r=64, w=3〕
19. `{"op":"dmg","m":1.8}` — 追加攻撃〔m=1.8〕
20. `{"op":"strip"}` — 強化解除〔〕
21. `{"op":"mark","t":120,"x":1.6}` — 刻印〔t=120, x=1.6〕
22. `{"op":"fx","p":"end_rod","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="end_rod", n=50, at="ring", r=8.0, y=0.6〕
23. `{"op":"fx","p":"enchant","n":32,"at":"line","r":30}` — 粒子演出〔p="enchant", n=32, at="line", r=30〕
24. `{"op":"sound","s":"sonic","v":1.15,"pi":0.95}` — 効果音〔s="sonic", v=1.15, pi=0.95〕
25. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.kokuhaku_legend.stage0","ops":[{"op":"fx","p":"crit","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"sonic","v":0.9,"pi":1.2},{"op":"fx","p":"crit","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":10},{"op":"fx","p":"crit","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"end_rod","n":36,"at":"line","r":24},{"op":"sound","s":"sonic","v":1.05,"pi":1.14},{"op":"line","r":54.0,"w":3.0},{"op":"dmg","m":3.915},{"op":"strip"},{"op":"mark","t":140,"x":2.21},{"op":"self"},{"op":"buff","e":"speed","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.kokuhaku_legend.stage1","ops":[{"op":"fx","p":"crit","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"sonic","v":1.05,"pi":1.0},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"crit","n":6,"at":"line","r":15},{"op":"fx","p":"end_rod","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"enchant","n":32,"at":"line","r":30},{"op":"sound","s":"sonic","v":1.15,"pi":0.95},{"op":"area","r":12.0,"n":12},{"op":"stun","t":40},{"op":"erase","r":12.0},{"op":"dmg","m":2.03},{"op":"area","r":12.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.kokuhaku_legend.stage2","ops":[{"op":"fx","p":"crit","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"sonic","v":1.25,"pi":0.75},{"op":"fx","p":"end_rod","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"crit","n":10,"at":"line","r":20},{"op":"fx","p":"crit","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"end_rod","n":48,"at":"line","r":48},{"op":"fx","p":"enchant","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"sonic","v":1.5,"pi":0.75},{"op":"line","r":76.0,"w":3.0},{"op":"dmg","m":11.016},{"op":"strip"},{"op":"mark","t":180,"x":2.6},{"op":"area","r":20.0,"n":16},{"op":"dmg","m":4.05},{"op":"fx","p":"enchant","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"crit","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"line","r":72.0,"w":3.0},{"op":"dmg","m":2.6},{"op":"strip"},{"op":"mark","t":200,"x":2.3},{"op":"self"},{"op":"buff","e":"speed","t":180,"a":3},{"op":"line","r":35.0,"w":4.0},{"op":"dmg","m":0.8},{"op":"eff","e":"slow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"speed","t":240,"a":4},{"op":"area","r":14,"n":10},{"op":"strip"},{"op":"fx","p":"crit","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"sonic","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"slow","t":50,"a":5},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.kokuhaku_legend.stage0","ops":[{"op":"fx","p":"crit","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"sonic","v":0.9,"pi":1.2},{"op":"fx","p":"crit","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":10},{"op":"fx","p":"crit","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"end_rod","n":36,"at":"line","r":24},{"op":"sound","s":"sonic","v":1.05,"pi":1.14},{"op":"line","r":54.0,"w":3.0},{"op":"dmg","m":3.915},{"op":"strip"},{"op":"mark","t":140,"x":2.21},{"op":"self"},{"op":"buff","e":"speed","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.kokuhaku_legend.stage1","ops":[{"op":"fx","p":"crit","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"sonic","v":1.05,"pi":1.0},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"crit","n":6,"at":"line","r":15},{"op":"fx","p":"end_rod","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"enchant","n":32,"at":"line","r":30},{"op":"sound","s":"sonic","v":1.15,"pi":0.95},{"op":"area","r":12.0,"n":12},{"op":"stun","t":40},{"op":"erase","r":12.0},{"op":"dmg","m":2.03},{"op":"area","r":12.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.kokuhaku_legend.stage2","ops":[{"op":"fx","p":"crit","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"sonic","v":1.25,"pi":0.75},{"op":"fx","p":"end_rod","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"crit","n":10,"at":"line","r":20},{"op":"fx","p":"crit","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"end_rod","n":48,"at":"line","r":48},{"op":"fx","p":"enchant","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"sonic","v":1.5,"pi":0.75},{"op":"line","r":76.0,"w":3.0},{"op":"dmg","m":11.016},{"op":"strip"},{"op":"mark","t":180,"x":2.6},{"op":"area","r":20.0,"n":16},{"op":"dmg","m":4.05},{"op":"fx","p":"enchant","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"crit","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"line","r":72.0,"w":3.0},{"op":"dmg","m":2.6},{"op":"strip"},{"op":"mark","t":200,"x":2.3},{"op":"self"},{"op":"buff","e":"speed","t":180,"a":3},{"op":"line","r":35.0,"w":4.0},{"op":"dmg","m":0.8},{"op":"eff","e":"slow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"speed","t":240,"a":4},{"op":"area","r":14,"n":10},{"op":"strip"},{"op":"fx","p":"crit","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"sonic","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"slow","t":50,"a":5},{"op":"mark","t":135,"x":1.8}]}]〕
26. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
27. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 02. 天冠詠者 理覇

**モブ側の動きの方向性**：少女の指先、口元、天冠を同期させる。文字を書く方向が術の方向となる。。

### 天冠言霊筆 — 討伐武器（メイン／武器欄） (`riha_weapon`)

**現行パラメータ**：rank=1、damage登録値=578.5、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（5命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"luck","t":40,"a":2}` — 強化〔e="luck", t=40, a=2〕
03. `{"op":"buff","e":"regen","t":40,"a":0}` — 強化〔e="regen", t=40, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（8命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"stun","t":30}` — 行動停止〔t=30〕
03. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"glow","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"glow","t":90,"a":0}]〕
04. `{"op":"chance","p":0.465,"ops":[{"op":"victim"},{"op":"fx","p":"firework","n":11,"at":"t","s":0.24},{"op":"mark","t":140,"x":1.79},{"op":"eff","e":"levitate","t":28,"a":0}]}` — 抽選〔p=0.465, ops=[{"op":"victim"},{"op":"fx","p":"firework","n":11,"at":"t","s":0.24},{"op":"mark","t":140,"x":1.79},{"op":"eff","e":"levitate","t":28,"a":0}]〕
05. `{"op":"chance","p":0.177,"ops":[{"op":"victim"},{"op":"dmg","m":0.235}]}` — 抽選〔p=0.177, ops=[{"op":"victim"},{"op":"dmg","m":0.235}]〕
06. `{"op":"chance","p":0.104,"ops":[{"op":"victim"},{"op":"fx","p":"firework","n":8,"at":"t","s":0.25},{"op":"stun","t":8}]}` — 抽選〔p=0.104, ops=[{"op":"victim"},{"op":"fx","p":"firework","n":8,"at":"t","s":0.25},{"op":"stun","t":8}]〕
07. `{"op":"chance","p":0.2,"ops":[{"op":"victim"},{"op":"fx","p":"firework","n":14,"at":"t","s":0.28},{"op":"eff","e":"fatigue","t":110,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.2, ops=[{"op":"victim"},{"op":"fx","p":"firework","n":14,"at":"t","s":0.28},{"op":"eff","e":"fatigue","t":110,"a":124},{"op":"mark","t":100,"x":2.15}]〕
08. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"firework","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"firework","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]〕

**権能発動時の命令（20命令）**：

01. `{"op":"fx","p":"firework","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="firework", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"firework","n":4,"at":"self","s":0.7}` — 粒子演出〔p="firework", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"enchant","n":72,"at":"self","s":1.5}` — 粒子演出〔p="enchant", n=72, at="self", s=1.5〕
04. `{"op":"sound","s":"chime","v":1.0,"pi":0.8}` — 効果音〔s="chime", v=1.0, pi=0.8〕
05. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.riha_weapon.say0","ops":[{"op":"area","r":20,"n":36},{"op":"stun","t":160},{"op":"erase","r":20}]},{"say":"relic_art.oror_supreme_bosses.riha_weapon.say1","ops":[{"op":"allies","r":20},{"op":"healpct","v":1.0,"to":1},{"op":"cleanse","to":1}]},{"say":"relic_art.oror_supreme_bosses.riha_weapon.say2","ops":[{"op":"area","r":16,"n":36},{"op":"knock","f":4.0},{"op":"launch","f":1.2}]},{"say":"relic_art.oror_supreme_bosses.riha_weapon.say3","ops":[{"op":"area","r":20,"n":36},{"op":"dmg","m":1.6},{"op":"dmg","m":2.0,"magic":1}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.riha_weapon.say0","ops":[{"op":"area","r":20,"n":36},{"op":"stun","t":160},{"op":"erase","r":20}]},{"say":"relic_art.oror_supreme_bosses.riha_weapon.say1","ops":[{"op":"allies","r":20},{"op":"healpct","v":1.0,"to":1},{"op":"cleanse","to":1}]},{"say":"relic_art.oror_supreme_bosses.riha_weapon.say2","ops":[{"op":"area","r":16,"n":36},{"op":"knock","f":4.0},{"op":"launch","f":1.2}]},{"say":"relic_art.oror_supreme_bosses.riha_weapon.say3","ops":[{"op":"area","r":20,"n":36},{"op":"dmg","m":1.6},{"op":"dmg","m":2.0,"magic":1}]}]〕
06. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
07. `{"op":"fx","p":"firework","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="firework", n=46, at="ring", r=5.5, y=0.25〕
08. `{"op":"fx","p":"happy","n":36,"at":"line","r":24}` — 粒子演出〔p="happy", n=36, at="line", r=24〕
09. `{"op":"area","r":25.0,"n":18}` — 円形対象の取得〔r=25.0, n=18〕
10. `{"op":"stun","t":52}` — 行動停止〔t=52〕
11. `{"op":"eff","e":"glow","t":120,"a":0}` — 敵への状態異常〔e="glow", t=120, a=0〕
12. `{"op":"fx","p":"firework","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="firework", n=16, at="ring", r=5.0〕
13. `{"op":"sound","s":"spell","v":0.75,"pi":1.15}` — 効果音〔s="spell", v=0.75, pi=1.15〕
14. `{"op":"area","r":9,"n":8}` — 円形対象の取得〔r=9, n=8〕
15. `{"op":"dmg","m":0.9}` — 追加攻撃〔m=0.9〕
16. `{"op":"eff","e":"levitate","t":65,"a":0}` — 敵への状態異常〔e="levitate", t=65, a=0〕
17. `{"op":"fx","p":"firework","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="firework", n=24, at="ring", r=4.5, y=0.6〕
18. `{"op":"sound","s":"chime","v":0.8,"pi":0.8}` — 効果音〔s="chime", v=0.8, pi=0.8〕
19. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
20. `{"op":"eff","e":"fatigue","t":110,"a":124}` — 敵への状態異常〔e="fatigue", t=110, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 天冠詠譜 — 神威触媒（Curios relic_focus） (`riha_focus`)

**現行パラメータ**：rank=2、damage登録値=68.31、relics側CD=155tick、art側CD=155tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（11命令）**：

01. `{"op":"allies","r":12}` — 味方対象〔r=12〕
02. `{"op":"buff","e":"regen","t":40,"a":0,"to":1}` — 強化〔e="regen", t=40, a=0, to=1〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"luck","t":45,"a":0}` — 強化〔e="luck", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"fx","p":"happy","n":10,"at":"self","s":0.12}` — 粒子演出〔p="happy", n=10, at="self", s=0.12〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"buff","e":"luck","t":45,"a":2}` — 強化〔e="luck", t=45, a=2〕
09. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"luck","t":42,"a":2}` — 強化〔e="luck", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（35命令）**：

01. `{"op":"fx","p":"firework","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="firework", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"firework","n":6,"at":"self","s":0.7}` — 粒子演出〔p="firework", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"enchant","n":72,"at":"self","s":1.5}` — 粒子演出〔p="enchant", n=72, at="self", s=1.5〕
04. `{"op":"sound","s":"chime","v":1.0,"pi":0.8}` — 効果音〔s="chime", v=1.0, pi=0.8〕
05. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.riha_focus.say0","ops":[{"op":"fx","p":"firework","n":18,"at":"ring","r":6},{"op":"allies","r":24},{"op":"cleanse","to":1},{"op":"buff","e":"speed","t":300,"a":1,"to":1}]},{"say":"relic_art.oror_supreme_bosses.riha_focus.say1","ops":[{"op":"fx","p":"firework","n":18,"at":"ring","r":6},{"op":"allies","r":24},{"op":"healpct","v":1.0,"to":1},{"op":"buff","e":"regen","t":300,"a":2,"to":1}]},{"say":"relic_art.oror_supreme_bosses.riha_focus.say2","ops":[{"op":"fx","p":"firework","n":18,"at":"ring","r":6},{"op":"area","r":24,"n":36},{"op":"lightning"},{"op":"dmg","m":1.2},{"op":"stun","t":60}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.riha_focus.say0","ops":[{"op":"fx","p":"firework","n":18,"at":"ring","r":6},{"op":"allies","r":24},{"op":"cleanse","to":1},{"op":"buff","e":"speed","t":300,"a":1,"to":1}]},{"say":"relic_art.oror_supreme_bosses.riha_focus.say1","ops":[{"op":"fx","p":"firework","n":18,"at":"ring","r":6},{"op":"allies","r":24},{"op":"healpct","v":1.0,"to":1},{"op":"buff","e":"regen","t":300,"a":2,"to":1}]},{"say":"relic_art.oror_supreme_bosses.riha_focus.say2","ops":[{"op":"fx","p":"firework","n":18,"at":"ring","r":6},{"op":"area","r":24,"n":36},{"op":"lightning"},{"op":"dmg","m":1.2},{"op":"stun","t":60}]}]〕
06. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"buff","e":"luck","t":150,"a":1}` — 強化〔e="luck", t=150, a=1〕
09. `{"op":"fx","p":"happy","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="happy", n=50, at="ring", r=8.0, y=0.6〕
10. `{"op":"fx","p":"end_rod","n":32,"at":"line","r":30}` — 粒子演出〔p="end_rod", n=32, at="line", r=30〕
11. `{"op":"sound","s":"spell","v":1.15,"pi":0.95}` — 効果音〔s="spell", v=1.15, pi=0.95〕
12. `{"op":"area","r":22.0,"n":18}` — 円形対象の取得〔r=22.0, n=18〕
13. `{"op":"eff","e":"levitate","t":65,"a":1}` — 敵への状態異常〔e="levitate", t=65, a=1〕
14. `{"op":"knock","f":2.3}` — knock〔f=2.3〕
15. `{"op":"self"}` — 対象を自分へ〔〕
16. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
17. `{"op":"buff","e":"luck","t":150,"a":3}` — 強化〔e="luck", t=150, a=3〕
18. `{"op":"fx","p":"firework","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="firework", n=24, at="ring", r=12, y=0.5〕
19. `{"op":"sound","s":"chime","v":0.85,"pi":0.97}` — 効果音〔s="chime", v=0.85, pi=0.97〕
20. `{"op":"area","r":12.0,"n":12}` — 円形対象の取得〔r=12.0, n=12〕
21. `{"op":"dmg","m":0.8}` — 追加攻撃〔m=0.8〕
22. `{"op":"eff","e":"levitate","t":120,"a":1}` — 敵への状態異常〔e="levitate", t=120, a=1〕
23. `{"op":"self"}` — 対象を自分へ〔〕
24. `{"op":"buff","e":"luck","t":220,"a":3}` — 強化〔e="luck", t=220, a=3〕
25. `{"op":"area","r":16,"n":6}` — 円形対象の取得〔r=16, n=6〕
26. `{"op":"launch","f":1.4}` — launch〔f=1.4〕
27. `{"op":"fx","p":"firework","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="firework", n=24, at="ring", r=5.5, y=0.7〕
28. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
29. `{"op":"eff","e":"fatigue","t":148,"a":123}` — 敵への状態異常〔e="fatigue", t=148, a=123〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"luck","t":100,"a":123}` — 強化〔e="luck", t=100, a=123〕
32. `{"op":"fx","p":"firework","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="firework", n=16, at="ring", r=3.7, y=0.55〕
33. `{"op":"area","r":16,"n":9}` — 円形対象の取得〔r=16, n=9〕
34. `{"op":"eff","e":"levitate","t":26,"a":3}` — 敵への状態異常〔e="levitate", t=26, a=3〕
35. `{"op":"mark","t":135,"x":1.8}` — 刻印〔t=135, x=1.8〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 虚飾の天冠 — 神格装飾品（Curios relic_charm） (`riha_charm`)

**現行パラメータ**：rank=1、damage登録値=68.31、relics側CD=185tick、art側CD=185tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（14命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"slowfall","t":40,"a":0}` — 強化〔e="slowfall", t=40, a=0〕
03. `{"op":"buff","e":"speed","t":40,"a":0}` — 強化〔e="speed", t=40, a=0〕
04. `{"op":"buff","e":"luck","t":40,"a":1}` — 強化〔e="luck", t=40, a=1〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"luck","t":45,"a":0}` — 強化〔e="luck", t=45, a=0〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
09. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
10. `{"op":"buff","e":"luck","t":45,"a":1}` — 強化〔e="luck", t=45, a=1〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"luck","t":42,"a":2}` — 強化〔e="luck", t=42, a=2〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"absorb","t":48,"a":4}` — 強化〔e="absorb", t=48, a=4〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（37命令）**：

01. `{"op":"fx","p":"firework","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="firework", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"firework","n":4,"at":"self","s":0.7}` — 粒子演出〔p="firework", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"enchant","n":72,"at":"self","s":1.5}` — 粒子演出〔p="enchant", n=72, at="self", s=1.5〕
04. `{"op":"sound","s":"chime","v":1.0,"pi":0.8}` — 効果音〔s="chime", v=1.0, pi=0.8〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"invis","t":200,"a":0}` — 強化〔e="invis", t=200, a=0〕
07. `{"op":"guard","t":40}` — 防御〔t=40〕
08. `{"op":"area","r":20,"n":36}` — 円形対象の取得〔r=20, n=36〕
09. `{"op":"eff","e":"nausea","t":160,"a":0}` — 敵への状態異常〔e="nausea", t=160, a=0〕
10. `{"op":"eff","e":"blind","t":100,"a":0}` — 敵への状態異常〔e="blind", t=100, a=0〕
11. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"luck","t":210,"a":1}` — 強化〔e="luck", t=210, a=1〕
14. `{"op":"fx","p":"firework","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="firework", n=46, at="ring", r=5.5, y=0.25〕
15. `{"op":"fx","p":"happy","n":36,"at":"line","r":24}` — 粒子演出〔p="happy", n=36, at="line", r=24〕
16. `{"op":"sound","s":"spell","v":1.05,"pi":1.14}` — 効果音〔s="spell", v=1.05, pi=1.14〕
17. `{"op":"self"}` — 対象を自分へ〔〕
18. `{"op":"guard","t":95}` — 防御〔t=95〕
19. `{"op":"self"}` — 対象を自分へ〔〕
20. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
21. `{"op":"cleanse"}` — 状態異常解除〔〕
22. `{"op":"buff","e":"luck","t":180,"a":3}` — 強化〔e="luck", t=180, a=3〕
23. `{"op":"guard","t":95}` — 防御〔t=95〕
24. `{"op":"fx","p":"firework","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="firework", n=30, at="ring", r=4.0, y=0.7〕
25. `{"op":"sound","s":"chime","v":0.8,"pi":1.1}` — 効果音〔s="chime", v=0.8, pi=1.1〕
26. `{"op":"self"}` — 対象を自分へ〔〕
27. `{"op":"buff","e":"luck","t":280,"a":4}` — 強化〔e="luck", t=280, a=4〕
28. `{"op":"guard","t":140}` — 防御〔t=140〕
29. `{"op":"self"}` — 対象を自分へ〔〕
30. `{"op":"buff","e":"jump","t":240,"a":2}` — 強化〔e="jump", t=240, a=2〕
31. `{"op":"fx","p":"firework","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="firework", n=20, at="ring", r=4, y=0.4〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"buff","e":"luck","t":160,"a":123}` — 強化〔e="luck", t=160, a=123〕
34. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
35. `{"op":"eff","e":"fatigue","t":110,"a":123}` — 敵への状態異常〔e="fatigue", t=110, a=123〕
36. `{"op":"self"}` — 対象を自分へ〔〕
37. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 世界詠替・絶対真言 — 超越神器（武器欄） (`riha_legend`)

**現行パラメータ**：rank=3、damage登録値=1157.875、relics側CD=340tick、art側CD=340tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10、minecraft:luck_of_the_sea:25。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"allies","r":16}` — 味方対象〔r=16〕
06. `{"op":"buff","e":"regen","t":40,"a":1,"to":1}` — 強化〔e="regen", t=40, a=1, to=1〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
09. `{"op":"buff","e":"luck","t":45,"a":3}` — 強化〔e="luck", t=45, a=3〕
10. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（9命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"stun","t":60}` — 行動停止〔t=60〕
03. `{"op":"mark","t":100,"x":2.0}` — 刻印〔t=100, x=2.0〕
04. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"glow","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"glow","t":160,"a":1}]〕
05. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"firework","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"firework","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
06. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"levitate","t":135,"a":2},{"op":"fx","p":"firework","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"levitate","t":135,"a":2},{"op":"fx","p":"firework","n":10,"at":"t","s":0.35}]〕
07. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
08. `{"op":"chance","p":0.325,"ops":[{"op":"victim"},{"op":"fx","p":"firework","n":20,"at":"t","s":0.33},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.325, ops=[{"op":"victim"},{"op":"fx","p":"firework","n":20,"at":"t","s":0.33},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":160,"x":2.5}]〕
09. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"firework","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"firework","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]〕

**権能発動時の命令（25命令）**：

01. `{"op":"fx","p":"firework","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="firework", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"firework","n":4,"at":"self","s":0.7}` — 粒子演出〔p="firework", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"enchant","n":72,"at":"self","s":1.5}` — 粒子演出〔p="enchant", n=72, at="self", s=1.5〕
04. `{"op":"sound","s":"chime","v":1.0,"pi":0.8}` — 効果音〔s="chime", v=1.0, pi=0.8〕
05. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
06. `{"op":"stun","t":105}` — 行動停止〔t=105〕
07. `{"op":"erase","r":48}` — erase〔r=48〕
08. `{"op":"allies","r":32}` — 味方対象〔r=32〕
09. `{"op":"healpct","v":0.6,"to":1}` — 最大HP割合回復〔v=0.6, to=1〕
10. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
11. `{"op":"guard","t":180,"to":1}` — 防御〔t=180, to=1〕
12. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
13. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
14. `{"op":"dmg","m":5.6,"magic":1}` — 追加攻撃〔m=5.6, magic=1〕
15. `{"op":"fx","p":"end_rod","n":44,"at":"ring","r":10}` — 粒子演出〔p="end_rod", n=44, at="ring", r=10〕
16. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
17. `{"op":"area","r":26,"n":24}` — 円形対象の取得〔r=26, n=24〕
18. `{"op":"stun","t":45}` — 行動停止〔t=45〕
19. `{"op":"fx","p":"end_rod","n":35,"at":"ring","r":9}` — 粒子演出〔p="end_rod", n=35, at="ring", r=9〕
20. `{"op":"fx","p":"happy","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="happy", n=50, at="ring", r=8.0, y=0.6〕
21. `{"op":"fx","p":"end_rod","n":32,"at":"line","r":30}` — 粒子演出〔p="end_rod", n=32, at="line", r=30〕
22. `{"op":"sound","s":"spell","v":1.15,"pi":0.95}` — 効果音〔s="spell", v=1.15, pi=0.95〕
23. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.riha_legend.stage0","ops":[{"op":"fx","p":"firework","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"chime","v":0.9,"pi":1.2},{"op":"fx","p":"firework","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"happy","n":6,"at":"line","r":10},{"op":"fx","p":"firework","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"happy","n":36,"at":"line","r":24},{"op":"sound","s":"spell","v":1.05,"pi":1.14},{"op":"area","r":25.0,"n":18},{"op":"stun","t":52},{"op":"eff","e":"glow","t":120,"a":0},{"op":"self"},{"op":"buff","e":"luck","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.riha_legend.stage1","ops":[{"op":"fx","p":"firework","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"chime","v":1.05,"pi":1.0},{"op":"fx","p":"happy","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"firework","n":6,"at":"line","r":15},{"op":"fx","p":"happy","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"end_rod","n":32,"at":"line","r":30},{"op":"sound","s":"spell","v":1.15,"pi":0.95},{"op":"area","r":22.0,"n":18},{"op":"eff","e":"levitate","t":65,"a":1},{"op":"knock","f":2.3},{"op":"area","r":14.0,"n":10},{"op":"eff","e":"levitate","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.riha_legend.stage2","ops":[{"op":"fx","p":"firework","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"chime","v":1.25,"pi":0.75},{"op":"fx","p":"happy","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"firework","n":10,"at":"line","r":20},{"op":"fx","p":"firework","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"happy","n":48,"at":"line","r":48},{"op":"fx","p":"end_rod","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"spell","v":1.5,"pi":0.75},{"op":"area","r":32.0,"n":28},{"op":"dmg","m":8.748},{"op":"stun","t":67},{"op":"strip"},{"op":"self"},{"op":"buff","e":"absorb","t":140,"a":3},{"op":"fx","p":"end_rod","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"firework","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":30.0,"n":24},{"op":"dmg","m":2.6},{"op":"stun","t":30},{"op":"self"},{"op":"buff","e":"absorb","t":180,"a":4},{"op":"area","r":18.0,"n":16},{"op":"dmg","m":0.9},{"op":"eff","e":"levitate","t":160,"a":2},{"op":"self"},{"op":"buff","e":"luck","t":240,"a":4},{"op":"area","r":16,"n":8},{"op":"stun","t":25},{"op":"fx","p":"firework","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"chime","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"levitate","t":26,"a":3},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.riha_legend.stage0","ops":[{"op":"fx","p":"firework","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"chime","v":0.9,"pi":1.2},{"op":"fx","p":"firework","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"happy","n":6,"at":"line","r":10},{"op":"fx","p":"firework","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"happy","n":36,"at":"line","r":24},{"op":"sound","s":"spell","v":1.05,"pi":1.14},{"op":"area","r":25.0,"n":18},{"op":"stun","t":52},{"op":"eff","e":"glow","t":120,"a":0},{"op":"self"},{"op":"buff","e":"luck","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.riha_legend.stage1","ops":[{"op":"fx","p":"firework","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"chime","v":1.05,"pi":1.0},{"op":"fx","p":"happy","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"firework","n":6,"at":"line","r":15},{"op":"fx","p":"happy","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"end_rod","n":32,"at":"line","r":30},{"op":"sound","s":"spell","v":1.15,"pi":0.95},{"op":"area","r":22.0,"n":18},{"op":"eff","e":"levitate","t":65,"a":1},{"op":"knock","f":2.3},{"op":"area","r":14.0,"n":10},{"op":"eff","e":"levitate","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.riha_legend.stage2","ops":[{"op":"fx","p":"firework","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"chime","v":1.25,"pi":0.75},{"op":"fx","p":"happy","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"firework","n":10,"at":"line","r":20},{"op":"fx","p":"firework","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"happy","n":48,"at":"line","r":48},{"op":"fx","p":"end_rod","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"spell","v":1.5,"pi":0.75},{"op":"area","r":32.0,"n":28},{"op":"dmg","m":8.748},{"op":"stun","t":67},{"op":"strip"},{"op":"self"},{"op":"buff","e":"absorb","t":140,"a":3},{"op":"fx","p":"end_rod","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"firework","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":30.0,"n":24},{"op":"dmg","m":2.6},{"op":"stun","t":30},{"op":"self"},{"op":"buff","e":"absorb","t":180,"a":4},{"op":"area","r":18.0,"n":16},{"op":"dmg","m":0.9},{"op":"eff","e":"levitate","t":160,"a":2},{"op":"self"},{"op":"buff","e":"luck","t":240,"a":4},{"op":"area","r":16,"n":8},{"op":"stun","t":25},{"op":"fx","p":"firework","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"chime","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"levitate","t":26,"a":3},{"op":"mark","t":135,"x":1.8}]}]〕
24. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
25. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 03. 唯我万象 天輝

**モブ側の動きの方向性**：動かない直立姿勢と一歩の重み。掌・視線・体幹のみで結果を作る。。

### 唯我の王剣 — 討伐武器（メイン／武器欄） (`tenki_weapon`)

**現行パラメータ**：rank=1、damage登録値=289.33333、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:sweeping_edge:25。

**装備中の常時命令（5命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"absorb","t":40,"a":1}` — 強化〔e="absorb", t=40, a=1〕
03. `{"op":"cleanse"}` — 状態異常解除〔〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（8命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"strip"}` — 強化解除〔〕
03. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"weakness","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"weakness","t":90,"a":0}]〕
04. `{"op":"chance","p":0.53,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":13,"at":"t","s":0.24},{"op":"mark","t":160,"x":1.93},{"op":"eff","e":"weakness","t":79,"a":1}]}` — 抽選〔p=0.53, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":13,"at":"t","s":0.24},{"op":"mark","t":160,"x":1.93},{"op":"eff","e":"weakness","t":79,"a":1}]〕
05. `{"op":"chance","p":0.204,"ops":[{"op":"victim"},{"op":"dmg","m":0.27}]}` — 抽選〔p=0.204, ops=[{"op":"victim"},{"op":"dmg","m":0.27}]〕
06. `{"op":"chance","p":0.123,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":8,"at":"t","s":0.25},{"op":"strip"}]}` — 抽選〔p=0.123, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":8,"at":"t","s":0.25},{"op":"strip"}]〕
07. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]〕
08. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]〕

**権能発動時の命令（30命令）**：

01. `{"op":"fx","p":"end_rod","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="end_rod", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"end_rod","n":4,"at":"self","s":0.7}` — 粒子演出〔p="end_rod", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":40,"at":"ring","r":4,"y":0.1}` — 粒子演出〔p="end_rod", n=40, at="ring", r=4, y=0.1〕
04. `{"op":"fx","p":"wax","n":30,"at":"self"}` — 粒子演出〔p="wax", n=30, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":0.6}` — 効果音〔s="chime", v=1.0, pi=0.6〕
06. `{"op":"cone","r":18,"a":120}` — 扇形対象の取得〔r=18, a=120〕
07. `{"op":"dmg","m":1.68}` — 追加攻撃〔m=1.68〕
08. `{"op":"strip"}` — 強化解除〔〕
09. `{"op":"eff","e":"weakness","t":200,"a":3}` — 敵への状態異常〔e="weakness", t=200, a=3〕
10. `{"op":"knock","f":2.5}` — knock〔f=2.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"cleanse"}` — 状態異常解除〔〕
13. `{"op":"erase","r":18}` — erase〔r=18〕
14. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
15. `{"op":"fx","p":"end_rod","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="end_rod", n=46, at="ring", r=5.5, y=0.25〕
16. `{"op":"fx","p":"enchant","n":36,"at":"line","r":24}` — 粒子演出〔p="enchant", n=36, at="line", r=24〕
17. `{"op":"area","r":16.0,"n":12}` — 円形対象の取得〔r=16.0, n=12〕
18. `{"op":"strip"}` — 強化解除〔〕
19. `{"op":"stun","t":24}` — 行動停止〔t=24〕
20. `{"op":"self"}` — 対象を自分へ〔〕
21. `{"op":"cleanse"}` — 状態異常解除〔〕
22. `{"op":"fx","p":"end_rod","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="end_rod", n=16, at="ring", r=5.0〕
23. `{"op":"sound","s":"sonic","v":0.75,"pi":1.15}` — 効果音〔s="sonic", v=0.75, pi=1.15〕
24. `{"op":"cone","r":11,"a":85}` — 扇形対象の取得〔r=11, a=85〕
25. `{"op":"dmg","m":1.0}` — 追加攻撃〔m=1.0〕
26. `{"op":"eff","e":"weakness","t":65,"a":0}` — 敵への状態異常〔e="weakness", t=65, a=0〕
27. `{"op":"fx","p":"end_rod","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="end_rod", n=24, at="ring", r=4.5, y=0.6〕
28. `{"op":"sound","s":"sonic","v":0.8,"pi":0.8}` — 効果音〔s="sonic", v=0.8, pi=0.8〕
29. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
30. `{"op":"eff","e":"weakness","t":100,"a":124}` — 敵への状態異常〔e="weakness", t=100, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 優先律の王笏 — 神威触媒（Curios relic_focus） (`tenki_focus`)

**現行パラメータ**：rank=2、damage登録値=77.8734、relics側CD=150tick、art側CD=150tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"cleanse"}` — 状態異常解除〔〕
03. `{"op":"buff","e":"resist","t":40,"a":1}` — 強化〔e="resist", t=40, a=1〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"resist","t":45,"a":0}` — 強化〔e="resist", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"resist","t":42,"a":2}` — 強化〔e="resist", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（46命令）**：

01. `{"op":"fx","p":"end_rod","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="end_rod", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"end_rod","n":6,"at":"self","s":0.7}` — 粒子演出〔p="end_rod", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":40,"at":"ring","r":4,"y":0.1}` — 粒子演出〔p="end_rod", n=40, at="ring", r=4, y=0.1〕
04. `{"op":"fx","p":"wax","n":30,"at":"self"}` — 粒子演出〔p="wax", n=30, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":0.6}` — 効果音〔s="chime", v=1.0, pi=0.6〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"cleanse"}` — 状態異常解除〔〕
08. `{"op":"guard","t":80}` — 防御〔t=80〕
09. `{"op":"adapt","t":200}` — adapt〔t=200〕
10. `{"op":"area","r":24,"n":36}` — 円形対象の取得〔r=24, n=36〕
11. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
12. `{"op":"eff","e":"weakness","t":300,"a":4}` — 敵への状態異常〔e="weakness", t=300, a=4〕
13. `{"op":"eff","e":"slow","t":200,"a":3}` — 敵への状態異常〔e="slow", t=200, a=3〕
14. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
15. `{"op":"self"}` — 対象を自分へ〔〕
16. `{"op":"buff","e":"resist","t":150,"a":1}` — 強化〔e="resist", t=150, a=1〕
17. `{"op":"fx","p":"enchant","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="enchant", n=50, at="ring", r=8.0, y=0.6〕
18. `{"op":"fx","p":"spark","n":32,"at":"line","r":30}` — 粒子演出〔p="spark", n=32, at="line", r=30〕
19. `{"op":"sound","s":"totem","v":1.15,"pi":0.95}` — 効果音〔s="totem", v=1.15, pi=0.95〕
20. `{"op":"line","r":60.0,"w":3.0}` — 線分対象の取得〔r=60.0, w=3.0〕
21. `{"op":"dmg","m":3.8}` — 追加攻撃〔m=3.8〕
22. `{"op":"strip"}` — 強化解除〔〕
23. `{"op":"self"}` — 対象を自分へ〔〕
24. `{"op":"guard","t":90}` — 防御〔t=90〕
25. `{"op":"self"}` — 対象を自分へ〔〕
26. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
27. `{"op":"buff","e":"resist","t":150,"a":3}` — 強化〔e="resist", t=150, a=3〕
28. `{"op":"fx","p":"end_rod","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="end_rod", n=24, at="ring", r=12, y=0.5〕
29. `{"op":"sound","s":"sonic","v":0.85,"pi":1.04}` — 効果音〔s="sonic", v=0.85, pi=1.04〕
30. `{"op":"cone","r":14.0,"a":95.0}` — 扇形対象の取得〔r=14.0, a=95.0〕
31. `{"op":"dmg","m":0.95}` — 追加攻撃〔m=0.95〕
32. `{"op":"eff","e":"weakness","t":140,"a":1}` — 敵への状態異常〔e="weakness", t=140, a=1〕
33. `{"op":"self"}` — 対象を自分へ〔〕
34. `{"op":"buff","e":"resist","t":240,"a":3}` — 強化〔e="resist", t=240, a=3〕
35. `{"op":"area","r":18,"n":10}` — 円形対象の取得〔r=18, n=10〕
36. `{"op":"strip"}` — 強化解除〔〕
37. `{"op":"fx","p":"end_rod","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="end_rod", n=24, at="ring", r=5.5, y=0.7〕
38. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
39. `{"op":"eff","e":"weakness","t":135,"a":123}` — 敵への状態異常〔e="weakness", t=135, a=123〕
40. `{"op":"self"}` — 対象を自分へ〔〕
41. `{"op":"buff","e":"resist","t":140,"a":2}` — 強化〔e="resist", t=140, a=2〕
42. `{"op":"fx","p":"end_rod","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="end_rod", n=16, at="ring", r=3.7, y=0.55〕
43. `{"op":"self"}` — 対象を自分へ〔〕
44. `{"op":"cleanse"}` — 状態異常解除〔〕
45. `{"op":"guard","t":100}` — 防御〔t=100〕
46. `{"op":"reflect","t":100,"r":9}` — 反射〔t=100, r=9〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 万象後位の冠 — 神格装飾品（Curios relic_charm） (`tenki_charm`)

**現行パラメータ**：rank=1、damage登録値=77.8734、relics側CD=180tick、art側CD=180tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（13命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"cleanse"}` — 状態異常解除〔〕
03. `{"op":"buff","e":"absorb","t":40,"a":1}` — 強化〔e="absorb", t=40, a=1〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"resist","t":45,"a":0}` — 強化〔e="resist", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
09. `{"op":"buff","e":"resist","t":45,"a":1}` — 強化〔e="resist", t=45, a=1〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"resist","t":42,"a":2}` — 強化〔e="resist", t=42, a=2〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"resist","t":48,"a":3}` — 強化〔e="resist", t=48, a=3〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（37命令）**：

01. `{"op":"fx","p":"end_rod","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="end_rod", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"end_rod","n":4,"at":"self","s":0.7}` — 粒子演出〔p="end_rod", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":40,"at":"ring","r":4,"y":0.1}` — 粒子演出〔p="end_rod", n=40, at="ring", r=4, y=0.1〕
04. `{"op":"fx","p":"wax","n":30,"at":"self"}` — 粒子演出〔p="wax", n=30, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":0.6}` — 効果音〔s="chime", v=1.0, pi=0.6〕
06. `{"op":"area","r":20,"n":36}` — 円形対象の取得〔r=20, n=36〕
07. `{"op":"eff","e":"glow","t":300,"a":0}` — 敵への状態異常〔e="glow", t=300, a=0〕
08. `{"op":"mark","t":300,"x":2.0}` — 刻印〔t=300, x=2.0〕
09. `{"op":"eff","e":"slow","t":200,"a":2}` — 敵への状態異常〔e="slow", t=200, a=2〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"resist","t":210,"a":1}` — 強化〔e="resist", t=210, a=1〕
13. `{"op":"fx","p":"end_rod","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="end_rod", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"enchant","n":36,"at":"line","r":24}` — 粒子演出〔p="enchant", n=36, at="line", r=24〕
15. `{"op":"sound","s":"totem","v":1.05,"pi":1.14}` — 効果音〔s="totem", v=1.05, pi=1.14〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"guard","t":95}` — 防御〔t=95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
20. `{"op":"cleanse"}` — 状態異常解除〔〕
21. `{"op":"buff","e":"resist","t":180,"a":3}` — 強化〔e="resist", t=180, a=3〕
22. `{"op":"guard","t":95}` — 防御〔t=95〕
23. `{"op":"fx","p":"end_rod","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="end_rod", n=30, at="ring", r=4.0, y=0.7〕
24. `{"op":"sound","s":"sonic","v":0.8,"pi":1.1}` — 効果音〔s="sonic", v=0.8, pi=1.1〕
25. `{"op":"self"}` — 対象を自分へ〔〕
26. `{"op":"buff","e":"resist","t":300,"a":4}` — 強化〔e="resist", t=300, a=4〕
27. `{"op":"guard","t":155}` — 防御〔t=155〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"cleanse"}` — 状態異常解除〔〕
30. `{"op":"fx","p":"end_rod","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="end_rod", n=20, at="ring", r=4, y=0.4〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"resist","t":140,"a":2}` — 強化〔e="resist", t=140, a=2〕
33. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
34. `{"op":"eff","e":"weakness","t":100,"a":123}` — 敵への状態異常〔e="weakness", t=100, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"guard","t":95}` — 防御〔t=95〕
37. `{"op":"cleanse"}` — 状態異常解除〔〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 唯一絶対・王権万象 — 超越神器（武器欄） (`tenki_legend`)

**現行パラメータ**：rank=3、damage登録値=378.88462、relics側CD=335tick、art側CD=335tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:sweeping_edge:25、minecraft:knockback:6。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"cleanse"}` — 状態異常解除〔〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
08. `{"op":"buff","e":"resist","t":45,"a":3}` — 強化〔e="resist", t=45, a=3〕
09. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（9命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
03. `{"op":"mark","t":200,"x":2.0}` — 刻印〔t=200, x=2.0〕
04. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"weakness","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"weakness","t":160,"a":1}]〕
05. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
06. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"end_rod","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"end_rod","n":10,"at":"t","s":0.35}]〕
07. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
08. `{"op":"chance","p":0.35,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.35, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]〕
09. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]〕

**権能発動時の命令（28命令）**：

01. `{"op":"fx","p":"end_rod","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="end_rod", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"end_rod","n":4,"at":"self","s":0.7}` — 粒子演出〔p="end_rod", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":40,"at":"ring","r":4,"y":0.1}` — 粒子演出〔p="end_rod", n=40, at="ring", r=4, y=0.1〕
04. `{"op":"fx","p":"wax","n":30,"at":"self"}` — 粒子演出〔p="wax", n=30, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":0.6}` — 効果音〔s="chime", v=1.0, pi=0.6〕
06. `{"op":"area","r":40,"n":36}` — 円形対象の取得〔r=40, n=36〕
07. `{"op":"slam","f":4.0}` — slam〔f=4.0〕
08. `{"op":"stun","t":105}` — 行動停止〔t=105〕
09. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
10. `{"op":"eff","e":"weakness","t":400,"a":9}` — 敵への状態異常〔e="weakness", t=400, a=9〕
11. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"undying","t":180}` — 死亡防護〔t=180〕
14. `{"op":"guard","t":100}` — 防御〔t=100〕
15. `{"op":"cleanse"}` — 状態異常解除〔〕
16. `{"op":"buff","e":"absorb","t":600,"a":9}` — 強化〔e="absorb", t=600, a=9〕
17. `{"op":"erase","r":48}` — erase〔r=48〕
18. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
19. `{"op":"self"}` — 対象を自分へ〔〕
20. `{"op":"guard","t":135}` — 防御〔t=135〕
21. `{"op":"cleanse"}` — 状態異常解除〔〕
22. `{"op":"buff","e":"resist","a":2,"t":140}` — 強化〔e="resist", a=2, t=140〕
23. `{"op":"fx","p":"enchant","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="enchant", n=50, at="ring", r=8.0, y=0.6〕
24. `{"op":"fx","p":"spark","n":32,"at":"line","r":30}` — 粒子演出〔p="spark", n=32, at="line", r=30〕
25. `{"op":"sound","s":"totem","v":1.15,"pi":0.95}` — 効果音〔s="totem", v=1.15, pi=0.95〕
26. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.tenki_legend.stage0","ops":[{"op":"fx","p":"end_rod","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"sonic","v":0.9,"pi":1.2},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"enchant","n":6,"at":"line","r":10},{"op":"fx","p":"end_rod","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"enchant","n":36,"at":"line","r":24},{"op":"sound","s":"totem","v":1.05,"pi":1.14},{"op":"area","r":16.0,"n":12},{"op":"strip"},{"op":"stun","t":24},{"op":"self"},{"op":"cleanse"},{"op":"self"},{"op":"buff","e":"resist","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.tenki_legend.stage1","ops":[{"op":"fx","p":"end_rod","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"sonic","v":1.05,"pi":1.0},{"op":"fx","p":"enchant","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":15},{"op":"fx","p":"enchant","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"spark","n":32,"at":"line","r":30},{"op":"sound","s":"totem","v":1.15,"pi":0.95},{"op":"line","r":60.0,"w":3.0},{"op":"dmg","m":5.51},{"op":"strip"},{"op":"self"},{"op":"guard","t":90},{"op":"area","r":16.0,"n":10},{"op":"eff","e":"weakness","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.tenki_legend.stage2","ops":[{"op":"fx","p":"end_rod","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"sonic","v":1.25,"pi":0.75},{"op":"fx","p":"enchant","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"end_rod","n":10,"at":"line","r":20},{"op":"fx","p":"end_rod","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"enchant","n":48,"at":"line","r":48},{"op":"fx","p":"spark","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"totem","v":1.5,"pi":0.75},{"op":"area","r":26.0,"n":20},{"op":"strip"},{"op":"dmg","m":10.044},{"op":"self"},{"op":"cleanse"},{"op":"guard","t":150},{"op":"buff","e":"resist","t":180,"a":3},{"op":"fx","p":"spark","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"end_rod","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":24.0,"n":18},{"op":"strip"},{"op":"dmg","m":2.5},{"op":"self"},{"op":"cleanse"},{"op":"guard","t":95},{"op":"cone","r":21.0,"a":110.0},{"op":"dmg","m":1.0},{"op":"eff","e":"weakness","t":160,"a":2},{"op":"self"},{"op":"buff","e":"resist","t":240,"a":4},{"op":"area","r":18,"n":10},{"op":"strip"},{"op":"fx","p":"end_rod","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"sonic","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"self"},{"op":"cleanse"},{"op":"guard","t":105},{"op":"area","r":17,"n":8},{"op":"strip"}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.tenki_legend.stage0","ops":[{"op":"fx","p":"end_rod","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"sonic","v":0.9,"pi":1.2},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"enchant","n":6,"at":"line","r":10},{"op":"fx","p":"end_rod","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"enchant","n":36,"at":"line","r":24},{"op":"sound","s":"totem","v":1.05,"pi":1.14},{"op":"area","r":16.0,"n":12},{"op":"strip"},{"op":"stun","t":24},{"op":"self"},{"op":"cleanse"},{"op":"self"},{"op":"buff","e":"resist","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.tenki_legend.stage1","ops":[{"op":"fx","p":"end_rod","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"sonic","v":1.05,"pi":1.0},{"op":"fx","p":"enchant","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":15},{"op":"fx","p":"enchant","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"spark","n":32,"at":"line","r":30},{"op":"sound","s":"totem","v":1.15,"pi":0.95},{"op":"line","r":60.0,"w":3.0},{"op":"dmg","m":5.51},{"op":"strip"},{"op":"self"},{"op":"guard","t":90},{"op":"area","r":16.0,"n":10},{"op":"eff","e":"weakness","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.tenki_legend.stage2","ops":[{"op":"fx","p":"end_rod","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"sonic","v":1.25,"pi":0.75},{"op":"fx","p":"enchant","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"end_rod","n":10,"at":"line","r":20},{"op":"fx","p":"end_rod","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"enchant","n":48,"at":"line","r":48},{"op":"fx","p":"spark","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"totem","v":1.5,"pi":0.75},{"op":"area","r":26.0,"n":20},{"op":"strip"},{"op":"dmg","m":10.044},{"op":"self"},{"op":"cleanse"},{"op":"guard","t":150},{"op":"buff","e":"resist","t":180,"a":3},{"op":"fx","p":"spark","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"end_rod","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":24.0,"n":18},{"op":"strip"},{"op":"dmg","m":2.5},{"op":"self"},{"op":"cleanse"},{"op":"guard","t":95},{"op":"cone","r":21.0,"a":110.0},{"op":"dmg","m":1.0},{"op":"eff","e":"weakness","t":160,"a":2},{"op":"self"},{"op":"buff","e":"resist","t":240,"a":4},{"op":"area","r":18,"n":10},{"op":"strip"},{"op":"fx","p":"end_rod","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"sonic","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"self"},{"op":"cleanse"},{"op":"guard","t":105},{"op":"area","r":17,"n":8},{"op":"strip"}]}]〕
27. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
28. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 04. 万象混沌 カオス

**モブ側の動きの方向性**：固定骨格に依存せず、触腕と表面の独立メッシュを変形させる。。

### 万象変転の混沌核 — 討伐武器（メイン／武器欄） (`chaos_weapon`)

**現行パラメータ**：rank=1、damage登録値=578.5、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（4命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"luck","t":40,"a":3}` — 強化〔e="luck", t=40, a=3〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（7命令）**：

01. `{"op":"chance","p":0.3,"ops":[{"op":"victim"},{"op":"transmute"}],"else":[{"op":"victim"},{"op":"dmg","m":0.2}]}` — 抽選〔p=0.3, ops=[{"op":"victim"},{"op":"transmute"}], else=[{"op":"victim"},{"op":"dmg","m":0.2}]〕
02. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"nausea","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"nausea","t":90,"a":0}]〕
03. `{"op":"chance","p":0.535,"ops":[{"op":"victim"},{"op":"fx","p":"dragon","n":15,"at":"t","s":0.24},{"op":"mark","t":180,"x":2.07},{"op":"eff","e":"wither","t":91,"a":0}]}` — 抽選〔p=0.535, ops=[{"op":"victim"},{"op":"fx","p":"dragon","n":15,"at":"t","s":0.24},{"op":"mark","t":180,"x":2.07},{"op":"eff","e":"wither","t":91,"a":0}]〕
04. `{"op":"chance","p":0.231,"ops":[{"op":"victim"},{"op":"dmg","m":0.305}]}` — 抽選〔p=0.231, ops=[{"op":"victim"},{"op":"dmg","m":0.305}]〕
05. `{"op":"chance","p":0.142,"ops":[{"op":"victim"},{"op":"fx","p":"dragon","n":8,"at":"t","s":0.25},{"op":"eff","e":"poison","t":65,"a":1}]}` — 抽選〔p=0.142, ops=[{"op":"victim"},{"op":"fx","p":"dragon","n":8,"at":"t","s":0.25},{"op":"eff","e":"poison","t":65,"a":1}]〕
06. `{"op":"chance","p":0.24,"ops":[{"op":"victim"},{"op":"fx","p":"portal","n":14,"at":"t","s":0.28},{"op":"eff","e":"wither","t":22,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.24, ops=[{"op":"victim"},{"op":"fx","p":"portal","n":14,"at":"t","s":0.28},{"op":"eff","e":"wither","t":22,"a":124},{"op":"mark","t":100,"x":2.15}]〕
07. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"dragon","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"dragon","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]〕

**権能発動時の命令（22命令）**：

01. `{"op":"fx","p":"dragon","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="dragon", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"dragon","n":4,"at":"self","s":0.7}` — 粒子演出〔p="dragon", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"witch","n":40,"at":"self","s":1.4}` — 粒子演出〔p="witch", n=40, at="self", s=1.4〕
04. `{"op":"fx","p":"firework","n":30,"at":"self"}` — 粒子演出〔p="firework", n=30, at="self"〕
05. `{"op":"sound","s":"mirror","v":1.0,"pi":0.7}` — 効果音〔s="mirror", v=1.0, pi=0.7〕
06. `{"op":"area","r":16,"n":36}` — 円形対象の取得〔r=16, n=36〕
07. `{"op":"each","ops":[{"op":"transmute"},{"op":"launch","f":2.4},{"op":"eff","e":"levitate","t":100,"a":3},{"op":"stun","t":65},{"op":"dmg","m":1.5},{"op":"freeze","t":300},{"op":"burn","s":10}]}` — each〔ops=[{"op":"transmute"},{"op":"launch","f":2.4},{"op":"eff","e":"levitate","t":100,"a":3},{"op":"stun","t":65},{"op":"dmg","m":1.5},{"op":"freeze","t":300},{"op":"burn","s":10}]〕
08. `{"op":"fx","p":"witch","n":12,"at":"t","s":0.5}` — 粒子演出〔p="witch", n=12, at="t", s=0.5〕
09. `{"op":"fx","p":"dragon","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="dragon", n=46, at="ring", r=5.5, y=0.25〕
10. `{"op":"fx","p":"witch","n":36,"at":"line","r":24}` — 粒子演出〔p="witch", n=36, at="line", r=24〕
11. `{"op":"area","r":28.0,"n":20}` — 円形対象の取得〔r=28.0, n=20〕
12. `{"op":"dmg","m":2.1}` — 追加攻撃〔m=2.1〕
13. `{"op":"eff","e":"nausea","t":110,"a":0}` — 敵への状態異常〔e="nausea", t=110, a=0〕
14. `{"op":"fx","p":"portal","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="portal", n=16, at="ring", r=5.0〕
15. `{"op":"sound","s":"spell","v":0.75,"pi":1.15}` — 効果音〔s="spell", v=0.75, pi=1.15〕
16. `{"op":"area","r":9,"n":8}` — 円形対象の取得〔r=9, n=8〕
17. `{"op":"dmg","m":0.9}` — 追加攻撃〔m=0.9〕
18. `{"op":"eff","e":"wither","t":65,"a":0}` — 敵への状態異常〔e="wither", t=65, a=0〕
19. `{"op":"fx","p":"portal","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="portal", n=24, at="ring", r=4.5, y=0.6〕
20. `{"op":"sound","s":"wither","v":0.8,"pi":0.8}` — 効果音〔s="wither", v=0.8, pi=0.8〕
21. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
22. `{"op":"eff","e":"wither","t":22,"a":124}` — 敵への状態異常〔e="wither", t=22, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 虹核の触媒 — 神威触媒（Curios relic_focus） (`chaos_focus`)

**現行パラメータ**：rank=2、damage登録値=71.7255、relics側CD=145tick、art側CD=145tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"slowfall","t":40,"a":0}` — 強化〔e="slowfall", t=40, a=0〕
03. `{"op":"buff","e":"jump","t":40,"a":2}` — 強化〔e="jump", t=40, a=2〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"regen","t":45,"a":0}` — 強化〔e="regen", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"regen","t":42,"a":2}` — 強化〔e="regen", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（40命令）**：

01. `{"op":"fx","p":"dragon","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="dragon", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"dragon","n":6,"at":"self","s":0.7}` — 粒子演出〔p="dragon", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"witch","n":40,"at":"self","s":1.4}` — 粒子演出〔p="witch", n=40, at="self", s=1.4〕
04. `{"op":"fx","p":"firework","n":30,"at":"self"}` — 粒子演出〔p="firework", n=30, at="self"〕
05. `{"op":"sound","s":"mirror","v":1.0,"pi":0.7}` — 効果音〔s="mirror", v=1.0, pi=0.7〕
06. `{"op":"area","r":24,"n":36}` — 円形対象の取得〔r=24, n=36〕
07. `{"op":"launch","f":2.6}` — launch〔f=2.6〕
08. `{"op":"eff","e":"levitate","t":120,"a":2}` — 敵への状態異常〔e="levitate", t=120, a=2〕
09. `{"op":"dmg","m":1.0}` — 追加攻撃〔m=1.0〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"regen","t":150,"a":1}` — 強化〔e="regen", t=150, a=1〕
13. `{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="witch", n=50, at="ring", r=8.0, y=0.6〕
14. `{"op":"fx","p":"portal","n":32,"at":"line","r":30}` — 粒子演出〔p="portal", n=32, at="line", r=30〕
15. `{"op":"sound","s":"roar","v":1.15,"pi":0.95}` — 効果音〔s="roar", v=1.15, pi=0.95〕
16. `{"op":"cone","r":32.0,"a":130.0}` — 扇形対象の取得〔r=32.0, a=130.0〕
17. `{"op":"dmg","m":2.4}` — 追加攻撃〔m=2.4〕
18. `{"op":"pull","f":1.6}` — pull〔f=1.6〕
19. `{"op":"eff","e":"poison","t":100,"a":1}` — 敵への状態異常〔e="poison", t=100, a=1〕
20. `{"op":"self"}` — 対象を自分へ〔〕
21. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
22. `{"op":"buff","e":"regen","t":150,"a":3}` — 強化〔e="regen", t=150, a=3〕
23. `{"op":"fx","p":"portal","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="portal", n=24, at="ring", r=12, y=0.5〕
24. `{"op":"sound","s":"wither","v":0.85,"pi":1.11}` — 効果音〔s="wither", v=0.85, pi=1.11〕
25. `{"op":"area","r":16.0,"n":12}` — 円形対象の取得〔r=16.0, n=12〕
26. `{"op":"dmg","m":0.8}` — 追加攻撃〔m=0.8〕
27. `{"op":"eff","e":"wither","t":160,"a":1}` — 敵への状態異常〔e="wither", t=160, a=1〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"buff","e":"regen","t":200,"a":3}` — 強化〔e="regen", t=200, a=3〕
30. `{"op":"area","r":20,"n":8}` — 円形対象の取得〔r=20, n=8〕
31. `{"op":"eff","e":"wither","t":100,"a":1}` — 敵への状態異常〔e="wither", t=100, a=1〕
32. `{"op":"fx","p":"portal","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="portal", n=24, at="ring", r=5.5, y=0.7〕
33. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
34. `{"op":"eff","e":"wither","t":30,"a":123}` — 敵への状態異常〔e="wither", t=30, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"buff","e":"regen","t":140,"a":7}` — 強化〔e="regen", t=140, a=7〕
37. `{"op":"fx","p":"dragon","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="dragon", n=16, at="ring", r=3.7, y=0.55〕
38. `{"op":"area","r":14,"n":7}` — 円形対象の取得〔r=14, n=7〕
39. `{"op":"eff","e":"wither","t":45,"a":7}` — 敵への状態異常〔e="wither", t=45, a=7〕
40. `{"op":"mark","t":115,"x":1.8}` — 刻印〔t=115, x=1.8〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 無名混沌の殻 — 神格装飾品（Curios relic_charm） (`chaos_charm`)

**現行パラメータ**：rank=1、damage登録値=71.7255、relics側CD=175tick、art側CD=175tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（12命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"adapt","t":40}` — adapt〔t=40〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"regen","t":45,"a":0}` — 強化〔e="regen", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"regen","t":42,"a":2}` — 強化〔e="regen", t=42, a=2〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"regen","t":48,"a":4}` — 強化〔e="regen", t=48, a=4〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（37命令）**：

01. `{"op":"fx","p":"dragon","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="dragon", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"dragon","n":4,"at":"self","s":0.7}` — 粒子演出〔p="dragon", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"witch","n":40,"at":"self","s":1.4}` — 粒子演出〔p="witch", n=40, at="self", s=1.4〕
04. `{"op":"fx","p":"firework","n":30,"at":"self"}` — 粒子演出〔p="firework", n=30, at="self"〕
05. `{"op":"sound","s":"mirror","v":1.0,"pi":0.7}` — 効果音〔s="mirror", v=1.0, pi=0.7〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"guard","t":60}` — 防御〔t=60〕
08. `{"op":"adapt","t":300}` — adapt〔t=300〕
09. `{"op":"area","r":10,"n":36}` — 円形対象の取得〔r=10, n=36〕
10. `{"op":"each","ops":[{"op":"knock","f":3.0},{"op":"eff","e":"nausea","t":200,"a":0},{"op":"eff","e":"levitate","t":80,"a":2}]}` — each〔ops=[{"op":"knock","f":3.0},{"op":"eff","e":"nausea","t":200,"a":0},{"op":"eff","e":"levitate","t":80,"a":2}]〕
11. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"regen","t":210,"a":1}` — 強化〔e="regen", t=210, a=1〕
14. `{"op":"fx","p":"dragon","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="dragon", n=46, at="ring", r=5.5, y=0.25〕
15. `{"op":"fx","p":"witch","n":36,"at":"line","r":24}` — 粒子演出〔p="witch", n=36, at="line", r=24〕
16. `{"op":"sound","s":"roar","v":1.05,"pi":1.14}` — 効果音〔s="roar", v=1.05, pi=1.14〕
17. `{"op":"self"}` — 対象を自分へ〔〕
18. `{"op":"guard","t":95}` — 防御〔t=95〕
19. `{"op":"self"}` — 対象を自分へ〔〕
20. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
21. `{"op":"cleanse"}` — 状態異常解除〔〕
22. `{"op":"buff","e":"regen","t":180,"a":3}` — 強化〔e="regen", t=180, a=3〕
23. `{"op":"guard","t":95}` — 防御〔t=95〕
24. `{"op":"fx","p":"portal","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="portal", n=30, at="ring", r=4.0, y=0.7〕
25. `{"op":"sound","s":"wither","v":0.8,"pi":1.1}` — 効果音〔s="wither", v=0.8, pi=1.1〕
26. `{"op":"self"}` — 対象を自分へ〔〕
27. `{"op":"buff","e":"regen","t":260,"a":4}` — 強化〔e="regen", t=260, a=4〕
28. `{"op":"guard","t":170}` — 防御〔t=170〕
29. `{"op":"self"}` — 対象を自分へ〔〕
30. `{"op":"buff","e":"regen","t":240,"a":2}` — 強化〔e="regen", t=240, a=2〕
31. `{"op":"fx","p":"portal","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="portal", n=20, at="ring", r=4, y=0.4〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"buff","e":"regen","t":140,"a":7}` — 強化〔e="regen", t=140, a=7〕
34. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
35. `{"op":"eff","e":"wither","t":22,"a":123}` — 敵への状態異常〔e="wither", t=22, a=123〕
36. `{"op":"self"}` — 対象を自分へ〔〕
37. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 万象錯綜・虹核崩界 — 超越神器（武器欄） (`chaos_legend`)

**現行パラメータ**：rank=3、damage登録値=1157.875、relics側CD=330tick、art側CD=330tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"adapt","t":40}` — adapt〔t=40〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
08. `{"op":"buff","e":"regen","t":45,"a":3}` — 強化〔e="regen", t=45, a=3〕
09. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（7命令）**：

01. `{"op":"chance","p":0.5,"ops":[{"op":"victim"},{"op":"transmute"}],"else":[{"op":"victim"},{"op":"dmg","m":0.5}]}` — 抽選〔p=0.5, ops=[{"op":"victim"},{"op":"transmute"}], else=[{"op":"victim"},{"op":"dmg","m":0.5}]〕
02. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"nausea","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"nausea","t":160,"a":1}]〕
03. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"dragon","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"dragon","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
04. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"wither","t":135,"a":2},{"op":"fx","p":"dragon","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"wither","t":135,"a":2},{"op":"fx","p":"dragon","n":10,"at":"t","s":0.35}]〕
05. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
06. `{"op":"chance","p":0.375,"ops":[{"op":"victim"},{"op":"fx","p":"portal","n":20,"at":"t","s":0.33},{"op":"eff","e":"wither","t":30,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.375, ops=[{"op":"victim"},{"op":"fx","p":"portal","n":20,"at":"t","s":0.33},{"op":"eff","e":"wither","t":30,"a":124},{"op":"mark","t":160,"x":2.5}]〕
07. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"dragon","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"dragon","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]〕

**権能発動時の命令（22命令）**：

01. `{"op":"fx","p":"dragon","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="dragon", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"dragon","n":4,"at":"self","s":0.7}` — 粒子演出〔p="dragon", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"witch","n":40,"at":"self","s":1.4}` — 粒子演出〔p="witch", n=40, at="self", s=1.4〕
04. `{"op":"fx","p":"firework","n":30,"at":"self"}` — 粒子演出〔p="firework", n=30, at="self"〕
05. `{"op":"sound","s":"mirror","v":1.0,"pi":0.7}` — 効果音〔s="mirror", v=1.0, pi=0.7〕
06. `{"op":"area","r":40,"n":36}` — 円形対象の取得〔r=40, n=36〕
07. `{"op":"transmute"}` — transmute〔〕
08. `{"op":"area","r":40,"n":36}` — 円形対象の取得〔r=40, n=36〕
09. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
10. `{"op":"eff","e":"levitate","t":200,"a":4}` — 敵への状態異常〔e="levitate", t=200, a=4〕
11. `{"op":"stun","t":105}` — 行動停止〔t=105〕
12. `{"op":"fx","p":"firework","n":60,"at":"t"}` — 粒子演出〔p="firework", n=60, at="t"〕
13. `{"op":"fx","p":"witch","n":12,"at":"t","s":0.5}` — 粒子演出〔p="witch", n=12, at="t", s=0.5〕
14. `{"op":"area","r":26,"n":24}` — 円形対象の取得〔r=26, n=24〕
15. `{"op":"dmg","m":1.3}` — 追加攻撃〔m=1.3〕
16. `{"op":"eff","e":"nausea","t":95,"a":0}` — 敵への状態異常〔e="nausea", t=95, a=0〕
17. `{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="witch", n=50, at="ring", r=8.0, y=0.6〕
18. `{"op":"fx","p":"portal","n":32,"at":"line","r":30}` — 粒子演出〔p="portal", n=32, at="line", r=30〕
19. `{"op":"sound","s":"roar","v":1.15,"pi":0.95}` — 効果音〔s="roar", v=1.15, pi=0.95〕
20. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.chaos_legend.stage0","ops":[{"op":"fx","p":"portal","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"wither","v":0.9,"pi":1.2},{"op":"fx","p":"dragon","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"portal","n":6,"at":"line","r":10},{"op":"fx","p":"dragon","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"witch","n":36,"at":"line","r":24},{"op":"sound","s":"roar","v":1.05,"pi":1.14},{"op":"area","r":28.0,"n":20},{"op":"dmg","m":2.835},{"op":"eff","e":"nausea","t":110,"a":0},{"op":"self"},{"op":"buff","e":"regen","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.chaos_legend.stage1","ops":[{"op":"fx","p":"portal","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"wither","v":1.05,"pi":1.0},{"op":"fx","p":"portal","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"dragon","n":6,"at":"line","r":15},{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"portal","n":32,"at":"line","r":30},{"op":"sound","s":"roar","v":1.15,"pi":0.95},{"op":"cone","r":32.0,"a":130.0},{"op":"dmg","m":3.48},{"op":"pull","f":1.6},{"op":"eff","e":"poison","t":100,"a":1},{"op":"area","r":18.0,"n":10},{"op":"eff","e":"wither","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.chaos_legend.stage2","ops":[{"op":"fx","p":"portal","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"wither","v":1.25,"pi":0.75},{"op":"fx","p":"portal","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"dragon","n":10,"at":"line","r":20},{"op":"fx","p":"dragon","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"witch","n":48,"at":"line","r":48},{"op":"fx","p":"portal","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"roar","v":1.5,"pi":0.75},{"op":"area","r":34.0,"n":28},{"op":"dmg","m":9.396},{"op":"eff","e":"wither","t":100,"a":1},{"op":"summon","k":"golem","n":4},{"op":"self"},{"op":"buff","e":"regen","t":130,"a":2},{"op":"fx","p":"portal","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"dragon","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":29.0,"n":22},{"op":"dmg","m":2.6},{"op":"eff","e":"wither","t":130,"a":2},{"op":"self"},{"op":"buff","e":"regen","t":180,"a":3},{"op":"area","r":24.0,"n":16},{"op":"dmg","m":1.1},{"op":"eff","e":"wither","t":160,"a":2},{"op":"self"},{"op":"buff","e":"regen","t":240,"a":4},{"op":"area","r":20,"n":8},{"op":"eff","e":"wither","t":100,"a":1},{"op":"fx","p":"portal","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"wither","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"wither","t":30,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"wither","t":45,"a":7},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.chaos_legend.stage0","ops":[{"op":"fx","p":"portal","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"wither","v":0.9,"pi":1.2},{"op":"fx","p":"dragon","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"portal","n":6,"at":"line","r":10},{"op":"fx","p":"dragon","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"witch","n":36,"at":"line","r":24},{"op":"sound","s":"roar","v":1.05,"pi":1.14},{"op":"area","r":28.0,"n":20},{"op":"dmg","m":2.835},{"op":"eff","e":"nausea","t":110,"a":0},{"op":"self"},{"op":"buff","e":"regen","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.chaos_legend.stage1","ops":[{"op":"fx","p":"portal","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"wither","v":1.05,"pi":1.0},{"op":"fx","p":"portal","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"dragon","n":6,"at":"line","r":15},{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"portal","n":32,"at":"line","r":30},{"op":"sound","s":"roar","v":1.15,"pi":0.95},{"op":"cone","r":32.0,"a":130.0},{"op":"dmg","m":3.48},{"op":"pull","f":1.6},{"op":"eff","e":"poison","t":100,"a":1},{"op":"area","r":18.0,"n":10},{"op":"eff","e":"wither","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.chaos_legend.stage2","ops":[{"op":"fx","p":"portal","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"wither","v":1.25,"pi":0.75},{"op":"fx","p":"portal","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"dragon","n":10,"at":"line","r":20},{"op":"fx","p":"dragon","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"witch","n":48,"at":"line","r":48},{"op":"fx","p":"portal","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"roar","v":1.5,"pi":0.75},{"op":"area","r":34.0,"n":28},{"op":"dmg","m":9.396},{"op":"eff","e":"wither","t":100,"a":1},{"op":"summon","k":"golem","n":4},{"op":"self"},{"op":"buff","e":"regen","t":130,"a":2},{"op":"fx","p":"portal","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"dragon","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":29.0,"n":22},{"op":"dmg","m":2.6},{"op":"eff","e":"wither","t":130,"a":2},{"op":"self"},{"op":"buff","e":"regen","t":180,"a":3},{"op":"area","r":24.0,"n":16},{"op":"dmg","m":1.1},{"op":"eff","e":"wither","t":160,"a":2},{"op":"self"},{"op":"buff","e":"regen","t":240,"a":4},{"op":"area","r":20,"n":8},{"op":"eff","e":"wither","t":100,"a":1},{"op":"fx","p":"portal","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"wither","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"wither","t":30,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"wither","t":45,"a":7},{"op":"mark","t":135,"x":1.8}]}]〕
21. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
22. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 05. 万界錬成 ベーリット

**モブ側の動きの方向性**：掌で物体を溶かし、鋳型へ流し、形を作ってから武器として握る。。

### 万界錬成の籠手 — 討伐武器（メイン／武器欄） (`berit_weapon`)

**現行パラメータ**：rank=1、damage登録値=384.33333、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:efficiency:125。

**装備中の常時命令（5命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"repair","v":4}` — 修理〔v=4〕
03. `{"op":"buff","e":"haste","t":40,"a":1}` — 強化〔e="haste", t=40, a=1〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（7命令）**：

01. `{"op":"chance","p":0.25,"ops":[{"op":"give","item":"gold","n":1}]}` — 抽選〔p=0.25, ops=[{"op":"give","item":"gold","n":1}]〕
02. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"fatigue","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"fatigue","t":90,"a":0}]〕
03. `{"op":"chance","p":0.58,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":17,"at":"t","s":0.24},{"op":"mark","t":200,"x":2.21},{"op":"eff","e":"weakness","t":103,"a":1}]}` — 抽選〔p=0.58, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":17,"at":"t","s":0.24},{"op":"mark","t":200,"x":2.21},{"op":"eff","e":"weakness","t":103,"a":1}]〕
04. `{"op":"chance","p":0.258,"ops":[{"op":"victim"},{"op":"dmg","m":0.34}]}` — 抽選〔p=0.258, ops=[{"op":"victim"},{"op":"dmg","m":0.34}]〕
05. `{"op":"chance","p":0.085,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":8,"at":"t","s":0.25},{"op":"strip"}]}` — 抽選〔p=0.085, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":8,"at":"t","s":0.25},{"op":"strip"}]〕
06. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]〕
07. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]〕

**権能発動時の命令（28命令）**：

01. `{"op":"fx","p":"enchant","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="enchant", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"enchant","n":4,"at":"self","s":0.7}` — 粒子演出〔p="enchant", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"wax","n":40,"at":"self","s":1.0}` — 粒子演出〔p="wax", n=40, at="self", s=1.0〕
04. `{"op":"fx","p":"happy","n":20,"at":"self"}` — 粒子演出〔p="happy", n=20, at="self"〕
05. `{"op":"sound","s":"smith","v":1.0,"pi":1.2}` — 効果音〔s="smith", v=1.0, pi=1.2〕
06. `{"op":"cone","r":12,"a":100}` — 扇形対象の取得〔r=12, a=100〕
07. `{"op":"dmg","m":1.68}` — 追加攻撃〔m=1.68〕
08. `{"op":"disarm"}` — disarm〔〕
09. `{"op":"strip"}` — 強化解除〔〕
10. `{"op":"give","item":"gold","n":4}` — give〔item="gold", n=4〕
11. `{"op":"give","item":"iron","n":6}` — give〔item="iron", n=6〕
12. `{"op":"repair","v":128}` — 修理〔v=128〕
13. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
14. `{"op":"fx","p":"enchant","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="enchant", n=46, at="ring", r=5.5, y=0.25〕
15. `{"op":"fx","p":"wax","n":36,"at":"line","r":24}` — 粒子演出〔p="wax", n=36, at="line", r=24〕
16. `{"op":"line","r":58.0,"w":3.0}` — 線分対象の取得〔r=58.0, w=3.0〕
17. `{"op":"dmg","m":2.6}` — 追加攻撃〔m=2.6〕
18. `{"op":"strip"}` — 強化解除〔〕
19. `{"op":"mark","t":120,"x":1.5}` — 刻印〔t=120, x=1.5〕
20. `{"op":"fx","p":"enchant","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="enchant", n=16, at="ring", r=5.0〕
21. `{"op":"sound","s":"sonic","v":0.75,"pi":1.15}` — 効果音〔s="sonic", v=0.75, pi=1.15〕
22. `{"op":"line","r":18,"w":2}` — 線分対象の取得〔r=18, w=2〕
23. `{"op":"dmg","m":1.05}` — 追加攻撃〔m=1.05〕
24. `{"op":"eff","e":"weakness","t":65,"a":0}` — 敵への状態異常〔e="weakness", t=65, a=0〕
25. `{"op":"fx","p":"enchant","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="enchant", n=24, at="ring", r=4.5, y=0.6〕
26. `{"op":"sound","s":"smith","v":0.8,"pi":0.8}` — 効果音〔s="smith", v=0.8, pi=0.8〕
27. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
28. `{"op":"eff","e":"weakness","t":100,"a":124}` — 敵への状態異常〔e="weakness", t=100, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 無価値錬成炉 — 神威触媒（Curios relic_focus） (`berit_focus`)

**現行パラメータ**：rank=2、damage登録値=68.31、relics側CD=160tick、art側CD=160tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"repair","v":8}` — 修理〔v=8〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"haste","t":45,"a":0}` — 強化〔e="haste", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"haste","t":42,"a":2}` — 強化〔e="haste", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（43命令）**：

01. `{"op":"fx","p":"enchant","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="enchant", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"enchant","n":6,"at":"self","s":0.7}` — 粒子演出〔p="enchant", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"wax","n":40,"at":"self","s":1.0}` — 粒子演出〔p="wax", n=40, at="self", s=1.0〕
04. `{"op":"fx","p":"happy","n":20,"at":"self"}` — 粒子演出〔p="happy", n=20, at="self"〕
05. `{"op":"sound","s":"smith","v":1.0,"pi":1.2}` — 効果音〔s="smith", v=1.0, pi=1.2〕
06. `{"op":"give","item":"diamond","n":2}` — give〔item="diamond", n=2〕
07. `{"op":"give","item":"emerald","n":6}` — give〔item="emerald", n=6〕
08. `{"op":"give","item":"netherite","n":1}` — give〔item="netherite", n=1〕
09. `{"op":"xp","v":80}` — xp〔v=80〕
10. `{"op":"repair","v":512}` — 修理〔v=512〕
11. `{"op":"food"}` — food〔〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"haste","t":150,"a":1}` — 強化〔e="haste", t=150, a=1〕
15. `{"op":"fx","p":"wax","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="wax", n=50, at="ring", r=8.0, y=0.6〕
16. `{"op":"fx","p":"crit","n":32,"at":"line","r":30}` — 粒子演出〔p="crit", n=32, at="line", r=30〕
17. `{"op":"sound","s":"smith","v":1.15,"pi":0.95}` — 効果音〔s="smith", v=1.15, pi=0.95〕
18. `{"op":"area","r":28.0,"n":22}` — 円形対象の取得〔r=28.0, n=22〕
19. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
20. `{"op":"stun","t":34}` — 行動停止〔t=34〕
21. `{"op":"self"}` — 対象を自分へ〔〕
22. `{"op":"repair","n":36}` — 修理〔n=36〕
23. `{"op":"self"}` — 対象を自分へ〔〕
24. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
25. `{"op":"buff","e":"haste","t":150,"a":3}` — 強化〔e="haste", t=150, a=3〕
26. `{"op":"fx","p":"enchant","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="enchant", n=24, at="ring", r=12, y=0.5〕
27. `{"op":"sound","s":"smith","v":0.85,"pi":1.18}` — 効果音〔s="smith", v=0.85, pi=1.18〕
28. `{"op":"line","r":36.0,"w":2.5}` — 線分対象の取得〔r=36.0, w=2.5〕
29. `{"op":"dmg","m":0.85}` — 追加攻撃〔m=0.85〕
30. `{"op":"eff","e":"weakness","t":100,"a":1}` — 敵への状態異常〔e="weakness", t=100, a=1〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"haste","t":220,"a":3}` — 強化〔e="haste", t=220, a=3〕
33. `{"op":"self"}` — 対象を自分へ〔〕
34. `{"op":"repair","v":240}` — 修理〔v=240〕
35. `{"op":"fx","p":"enchant","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="enchant", n=24, at="ring", r=5.5, y=0.7〕
36. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
37. `{"op":"eff","e":"weakness","t":135,"a":123}` — 敵への状態異常〔e="weakness", t=135, a=123〕
38. `{"op":"self"}` — 対象を自分へ〔〕
39. `{"op":"buff","e":"haste","t":100,"a":123}` — 強化〔e="haste", t=100, a=123〕
40. `{"op":"fx","p":"enchant","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="enchant", n=16, at="ring", r=3.7, y=0.55〕
41. `{"op":"self"}` — 対象を自分へ〔〕
42. `{"op":"repair","v":180}` — 修理〔v=180〕
43. `{"op":"buff","e":"haste","t":170,"a":6}` — 強化〔e="haste", t=170, a=6〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 等価破戒の指輪 — 神格装飾品（Curios relic_charm） (`berit_charm`)

**現行パラメータ**：rank=1、damage登録値=68.31、relics側CD=190tick、art側CD=190tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（13命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"luck","t":40,"a":2}` — 強化〔e="luck", t=40, a=2〕
03. `{"op":"buff","e":"haste","t":40,"a":2}` — 強化〔e="haste", t=40, a=2〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":0}` — 強化〔e="haste", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
09. `{"op":"buff","e":"haste","t":45,"a":1}` — 強化〔e="haste", t=45, a=1〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"haste","t":42,"a":2}` — 強化〔e="haste", t=42, a=2〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"haste","t":48,"a":7}` — 強化〔e="haste", t=48, a=7〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（37命令）**：

01. `{"op":"fx","p":"enchant","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="enchant", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"enchant","n":4,"at":"self","s":0.7}` — 粒子演出〔p="enchant", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"wax","n":40,"at":"self","s":1.0}` — 粒子演出〔p="wax", n=40, at="self", s=1.0〕
04. `{"op":"fx","p":"happy","n":20,"at":"self"}` — 粒子演出〔p="happy", n=20, at="self"〕
05. `{"op":"sound","s":"smith","v":1.0,"pi":1.2}` — 効果音〔s="smith", v=1.0, pi=1.2〕
06. `{"op":"area","r":16,"n":36}` — 円形対象の取得〔r=16, n=36〕
07. `{"op":"disarm"}` — disarm〔〕
08. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
09. `{"op":"stun","t":80}` — 行動停止〔t=80〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"haste","t":210,"a":1}` — 強化〔e="haste", t=210, a=1〕
13. `{"op":"fx","p":"enchant","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="enchant", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"wax","n":36,"at":"line","r":24}` — 粒子演出〔p="wax", n=36, at="line", r=24〕
15. `{"op":"sound","s":"smith","v":1.05,"pi":1.14}` — 効果音〔s="smith", v=1.05, pi=1.14〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"guard","t":95}` — 防御〔t=95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
20. `{"op":"cleanse"}` — 状態異常解除〔〕
21. `{"op":"buff","e":"haste","t":180,"a":3}` — 強化〔e="haste", t=180, a=3〕
22. `{"op":"guard","t":95}` — 防御〔t=95〕
23. `{"op":"fx","p":"enchant","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="enchant", n=30, at="ring", r=4.0, y=0.7〕
24. `{"op":"sound","s":"smith","v":0.8,"pi":1.1}` — 効果音〔s="smith", v=0.8, pi=1.1〕
25. `{"op":"self"}` — 対象を自分へ〔〕
26. `{"op":"buff","e":"haste","t":280,"a":4}` — 強化〔e="haste", t=280, a=4〕
27. `{"op":"guard","t":125}` — 防御〔t=125〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"repair","v":240}` — 修理〔v=240〕
30. `{"op":"fx","p":"enchant","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="enchant", n=20, at="ring", r=4, y=0.4〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"haste","t":160,"a":123}` — 強化〔e="haste", t=160, a=123〕
33. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
34. `{"op":"eff","e":"weakness","t":100,"a":123}` — 敵への状態異常〔e="weakness", t=100, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"repair","v":220}` — 修理〔v=220〕
37. `{"op":"guard","t":80}` — 防御〔t=80〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 塵芥創界・神域錬成 — 超越神器（武器欄） (`berit_legend`)

**現行パラメータ**：rank=3、damage登録値=770.58333、relics側CD=345tick、art側CD=345tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:efficiency:125。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"repair","v":64}` — 修理〔v=64〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
08. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕
09. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（7命令）**：

01. `{"op":"chance","p":0.3,"ops":[{"op":"victim"},{"op":"transmute"}],"else":[{"op":"give","item":"gold","n":1}]}` — 抽選〔p=0.3, ops=[{"op":"victim"},{"op":"transmute"}], else=[{"op":"give","item":"gold","n":1}]〕
02. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"fatigue","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"fatigue","t":160,"a":1}]〕
03. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
04. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"enchant","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"enchant","n":10,"at":"t","s":0.35}]〕
05. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
06. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]〕
07. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]〕

**権能発動時の命令（29命令）**：

01. `{"op":"fx","p":"enchant","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="enchant", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"enchant","n":4,"at":"self","s":0.7}` — 粒子演出〔p="enchant", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"wax","n":40,"at":"self","s":1.0}` — 粒子演出〔p="wax", n=40, at="self", s=1.0〕
04. `{"op":"fx","p":"happy","n":20,"at":"self"}` — 粒子演出〔p="happy", n=20, at="self"〕
05. `{"op":"sound","s":"smith","v":1.0,"pi":1.2}` — 効果音〔s="smith", v=1.0, pi=1.2〕
06. `{"op":"area","r":40,"n":36}` — 円形対象の取得〔r=40, n=36〕
07. `{"op":"disarm"}` — disarm〔〕
08. `{"op":"transmute"}` — transmute〔〕
09. `{"op":"area","r":40,"n":36}` — 円形対象の取得〔r=40, n=36〕
10. `{"op":"dmg","m":2.24}` — 追加攻撃〔m=2.24〕
11. `{"op":"give","item":"netherite","n":2}` — give〔item="netherite", n=2〕
12. `{"op":"give","item":"diamond","n":8}` — give〔item="diamond", n=8〕
13. `{"op":"repair","v":4096}` — 修理〔v=4096〕
14. `{"op":"self"}` — 対象を自分へ〔〕
15. `{"op":"healpct","v":0.6}` — 最大HP割合回復〔v=0.6〕
16. `{"op":"buff","e":"absorb","t":600,"a":6}` — 強化〔e="absorb", t=600, a=6〕
17. `{"op":"allies","r":24}` — 味方対象〔r=24〕
18. `{"op":"buff","e":"absorb","t":600,"a":4,"to":1}` — 強化〔e="absorb", t=600, a=4, to=1〕
19. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
20. `{"op":"summon","k":"golem","n":3}` — 召喚〔k="golem", n=3〕
21. `{"op":"repair","n":32}` — 修理〔n=32〕
22. `{"op":"self"}` — 対象を自分へ〔〕
23. `{"op":"buff","e":"haste","a":2,"t":180}` — 強化〔e="haste", a=2, t=180〕
24. `{"op":"fx","p":"wax","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="wax", n=50, at="ring", r=8.0, y=0.6〕
25. `{"op":"fx","p":"crit","n":32,"at":"line","r":30}` — 粒子演出〔p="crit", n=32, at="line", r=30〕
26. `{"op":"sound","s":"smith","v":1.15,"pi":0.95}` — 効果音〔s="smith", v=1.15, pi=0.95〕
27. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.berit_legend.stage0","ops":[{"op":"fx","p":"enchant","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"smith","v":0.9,"pi":1.2},{"op":"fx","p":"enchant","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"wax","n":6,"at":"line","r":10},{"op":"fx","p":"enchant","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"wax","n":36,"at":"line","r":24},{"op":"sound","s":"smith","v":1.05,"pi":1.14},{"op":"line","r":58.0,"w":3.0},{"op":"dmg","m":3.51},{"op":"strip"},{"op":"mark","t":120,"x":1.95},{"op":"self"},{"op":"buff","e":"haste","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.berit_legend.stage1","ops":[{"op":"fx","p":"enchant","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"smith","v":1.05,"pi":1.0},{"op":"fx","p":"wax","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"enchant","n":6,"at":"line","r":15},{"op":"fx","p":"wax","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"crit","n":32,"at":"line","r":30},{"op":"sound","s":"smith","v":1.15,"pi":0.95},{"op":"area","r":28.0,"n":22},{"op":"dmg","m":4.06},{"op":"stun","t":34},{"op":"self"},{"op":"repair","n":36},{"op":"area","r":20.0,"n":10},{"op":"eff","e":"weakness","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.berit_legend.stage2","ops":[{"op":"fx","p":"enchant","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"smith","v":1.25,"pi":0.75},{"op":"fx","p":"wax","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"enchant","n":10,"at":"line","r":20},{"op":"fx","p":"enchant","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"wax","n":48,"at":"line","r":48},{"op":"fx","p":"crit","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"smith","v":1.5,"pi":0.75},{"op":"area","r":34.0,"n":26},{"op":"dmg","m":9.882},{"op":"strip"},{"op":"stun","t":55},{"op":"self"},{"op":"guard","t":130},{"op":"fx","p":"crit","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"enchant","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"line","r":64.0,"w":4.0},{"op":"dmg","m":2.9},{"op":"strip"},{"op":"self"},{"op":"repair","n":70},{"op":"line","r":47.0,"w":4.0},{"op":"dmg","m":1.2},{"op":"eff","e":"weakness","t":160,"a":2},{"op":"self"},{"op":"buff","e":"haste","t":240,"a":4},{"op":"self"},{"op":"repair","v":240},{"op":"fx","p":"enchant","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"smith","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"self"},{"op":"repair","v":260},{"op":"area","r":17,"n":9},{"op":"eff","e":"fatigue","t":65,"a":25}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.berit_legend.stage0","ops":[{"op":"fx","p":"enchant","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"smith","v":0.9,"pi":1.2},{"op":"fx","p":"enchant","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"wax","n":6,"at":"line","r":10},{"op":"fx","p":"enchant","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"wax","n":36,"at":"line","r":24},{"op":"sound","s":"smith","v":1.05,"pi":1.14},{"op":"line","r":58.0,"w":3.0},{"op":"dmg","m":3.51},{"op":"strip"},{"op":"mark","t":120,"x":1.95},{"op":"self"},{"op":"buff","e":"haste","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.berit_legend.stage1","ops":[{"op":"fx","p":"enchant","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"smith","v":1.05,"pi":1.0},{"op":"fx","p":"wax","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"enchant","n":6,"at":"line","r":15},{"op":"fx","p":"wax","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"crit","n":32,"at":"line","r":30},{"op":"sound","s":"smith","v":1.15,"pi":0.95},{"op":"area","r":28.0,"n":22},{"op":"dmg","m":4.06},{"op":"stun","t":34},{"op":"self"},{"op":"repair","n":36},{"op":"area","r":20.0,"n":10},{"op":"eff","e":"weakness","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.berit_legend.stage2","ops":[{"op":"fx","p":"enchant","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"smith","v":1.25,"pi":0.75},{"op":"fx","p":"wax","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"enchant","n":10,"at":"line","r":20},{"op":"fx","p":"enchant","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"wax","n":48,"at":"line","r":48},{"op":"fx","p":"crit","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"smith","v":1.5,"pi":0.75},{"op":"area","r":34.0,"n":26},{"op":"dmg","m":9.882},{"op":"strip"},{"op":"stun","t":55},{"op":"self"},{"op":"guard","t":130},{"op":"fx","p":"crit","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"enchant","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"line","r":64.0,"w":4.0},{"op":"dmg","m":2.9},{"op":"strip"},{"op":"self"},{"op":"repair","n":70},{"op":"line","r":47.0,"w":4.0},{"op":"dmg","m":1.2},{"op":"eff","e":"weakness","t":160,"a":2},{"op":"self"},{"op":"buff","e":"haste","t":240,"a":4},{"op":"self"},{"op":"repair","v":240},{"op":"fx","p":"enchant","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"smith","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"self"},{"op":"repair","v":260},{"op":"area","r":17,"n":9},{"op":"eff","e":"fatigue","t":65,"a":25}]}]〕
28. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
29. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 06. 星脈魔祖 エルセリア・アークノア

**モブ側の動きの方向性**：杖、両手、星陣の回転を別レイヤーで重ねる。。

### 原初星辰杖 — 討伐武器（メイン／武器欄） (`elseria_weapon`)

**現行パラメータ**：rank=1、damage登録値=578.5、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（4命令）**：

01. `{"op":"allies","r":10}` — 味方対象〔r=10〕
02. `{"op":"buff","e":"regen","t":40,"a":0,"to":1}` — 強化〔e="regen", t=40, a=0, to=1〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（8命令）**：

01. `{"op":"chain","n":3,"r":8}` — chain〔n=3, r=8〕
02. `{"op":"dmg","m":0.3}` — 追加攻撃〔m=0.3〕
03. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"slow","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"slow","t":90,"a":0}]〕
04. `{"op":"chance","p":0.46,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":9,"at":"t","s":0.24},{"op":"mark","t":120,"x":1.65},{"op":"eff","e":"slow","t":115,"a":0}]}` — 抽選〔p=0.46, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":9,"at":"t","s":0.24},{"op":"mark","t":120,"x":1.65},{"op":"eff","e":"slow","t":115,"a":0}]〕
05. `{"op":"chance","p":0.15,"ops":[{"op":"victim"},{"op":"dmg","m":0.2}]}` — 抽選〔p=0.15, ops=[{"op":"victim"},{"op":"dmg","m":0.2}]〕
06. `{"op":"chance","p":0.104,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":8,"at":"t","s":0.25},{"op":"eff","e":"slow","t":60,"a":1}]}` — 抽選〔p=0.104, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":8,"at":"t","s":0.25},{"op":"eff","e":"slow","t":60,"a":1}]〕
07. `{"op":"chance","p":0.18,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.18, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]〕
08. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":32,"a":3}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":32,"a":3}]〕

**権能発動時の命令（27命令）**：

01. `{"op":"fx","p":"enchant","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="enchant", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"enchant","n":4,"at":"self","s":0.7}` — 粒子演出〔p="enchant", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":40,"at":"self","s":1.6}` — 粒子演出〔p="end_rod", n=40, at="self", s=1.6〕
04. `{"op":"fx","p":"firework","n":20,"at":"self"}` — 粒子演出〔p="firework", n=20, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":1.6}` — 効果音〔s="chime", v=1.0, pi=1.6〕
06. `{"op":"fx","p":"end_rod","n":60,"at":"line","r":48}` — 粒子演出〔p="end_rod", n=60, at="line", r=48〕
07. `{"op":"line","r":48,"w":2}` — 線分対象の取得〔r=48, w=2〕
08. `{"op":"dmg","m":1.92}` — 追加攻撃〔m=1.92〕
09. `{"op":"burn","s":6}` — burn〔s=6〕
10. `{"op":"chain","n":5,"r":10}` — chain〔n=5, r=10〕
11. `{"op":"lightning"}` — lightning〔〕
12. `{"op":"dmg","m":0.72}` — 追加攻撃〔m=0.72〕
13. `{"op":"fx","p":"spark","n":12,"at":"t","s":0.5}` — 粒子演出〔p="spark", n=12, at="t", s=0.5〕
14. `{"op":"fx","p":"enchant","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="enchant", n=46, at="ring", r=5.5, y=0.25〕
15. `{"op":"fx","p":"witch","n":36,"at":"line","r":24}` — 粒子演出〔p="witch", n=36, at="line", r=24〕
16. `{"op":"chain","n":6,"r":20.0}` — chain〔n=6, r=20.0〕
17. `{"op":"dmg","m":2.6}` — 追加攻撃〔m=2.6〕
18. `{"op":"eff","e":"slow","t":70,"a":2}` — 敵への状態異常〔e="slow", t=70, a=2〕
19. `{"op":"fx","p":"enchant","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="enchant", n=16, at="ring", r=5.0〕
20. `{"op":"sound","s":"spell","v":0.75,"pi":1.15}` — 効果音〔s="spell", v=0.75, pi=1.15〕
21. `{"op":"chain","n":4,"r":12}` — chain〔n=4, r=12〕
22. `{"op":"dmg","m":1.0}` — 追加攻撃〔m=1.0〕
23. `{"op":"eff","e":"slow","t":65,"a":0}` — 敵への状態異常〔e="slow", t=65, a=0〕
24. `{"op":"fx","p":"end_rod","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="end_rod", n=24, at="ring", r=4.5, y=0.6〕
25. `{"op":"sound","s":"spell","v":0.8,"pi":0.8}` — 効果音〔s="spell", v=0.8, pi=0.8〕
26. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
27. `{"op":"eff","e":"slow","t":32,"a":124}` — 敵への状態異常〔e="slow", t=32, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 星脈の天球儀 — 神威触媒（Curios relic_focus） (`elseria_focus`)

**現行パラメータ**：rank=2、damage登録値=68.31、relics側CD=155tick、art側CD=155tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（12命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"night","t":300,"a":0}` — 強化〔e="night", t=300, a=0〕
03. `{"op":"buff","e":"regen","t":40,"a":0}` — 強化〔e="regen", t=40, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"night","t":45,"a":0}` — 強化〔e="night", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"fx","p":"witch","n":10,"at":"self","s":0.12}` — 粒子演出〔p="witch", n=10, at="self", s=0.12〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"night","t":45,"a":2}` — 強化〔e="night", t=45, a=2〕
10. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"night","t":42,"a":2}` — 強化〔e="night", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（44命令）**：

01. `{"op":"fx","p":"enchant","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="enchant", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"enchant","n":6,"at":"self","s":0.7}` — 粒子演出〔p="enchant", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":40,"at":"self","s":1.6}` — 粒子演出〔p="end_rod", n=40, at="self", s=1.6〕
04. `{"op":"fx","p":"firework","n":20,"at":"self"}` — 粒子演出〔p="firework", n=20, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":1.6}` — 効果音〔s="chime", v=1.0, pi=1.6〕
06. `{"op":"fx","p":"end_rod","n":44,"at":"ring","r":10}` — 粒子演出〔p="end_rod", n=44, at="ring", r=10〕
07. `{"op":"area","r":32,"n":36}` — 円形対象の取得〔r=32, n=36〕
08. `{"op":"lightning"}` — lightning〔〕
09. `{"op":"dmg","m":1.5}` — 追加攻撃〔m=1.5〕
10. `{"op":"eff","e":"slow","t":200,"a":3}` — 敵への状態異常〔e="slow", t=200, a=3〕
11. `{"op":"allies","r":24}` — 味方対象〔r=24〕
12. `{"op":"healpct","v":0.4,"to":1}` — 最大HP割合回復〔v=0.4, to=1〕
13. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
14. `{"op":"self"}` — 対象を自分へ〔〕
15. `{"op":"buff","e":"night","t":150,"a":1}` — 強化〔e="night", t=150, a=1〕
16. `{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="witch", n=50, at="ring", r=8.0, y=0.6〕
17. `{"op":"fx","p":"end_rod","n":32,"at":"line","r":30}` — 粒子演出〔p="end_rod", n=32, at="line", r=30〕
18. `{"op":"sound","s":"spell","v":1.15,"pi":0.95}` — 効果音〔s="spell", v=1.15, pi=0.95〕
19. `{"op":"area","r":30.0,"n":24}` — 円形対象の取得〔r=30.0, n=24〕
20. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
21. `{"op":"eff","e":"slow","t":70,"a":2}` — 敵への状態異常〔e="slow", t=70, a=2〕
22. `{"op":"self"}` — 対象を自分へ〔〕
23. `{"op":"buff","e":"regen","t":125,"a":2}` — 強化〔e="regen", t=125, a=2〕
24. `{"op":"self"}` — 対象を自分へ〔〕
25. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
26. `{"op":"buff","e":"night","t":150,"a":3}` — 強化〔e="night", t=150, a=3〕
27. `{"op":"fx","p":"end_rod","n":24,"at":"ring","r":10,"y":0.5}` — 粒子演出〔p="end_rod", n=24, at="ring", r=10, y=0.5〕
28. `{"op":"sound","s":"spell","v":0.85,"pi":0.9}` — 効果音〔s="spell", v=0.85, pi=0.9〕
29. `{"op":"chain","n":4,"r":12.0}` — chain〔n=4, r=12.0〕
30. `{"op":"dmg","m":0.7}` — 追加攻撃〔m=0.7〕
31. `{"op":"eff","e":"slow","t":120,"a":1}` — 敵への状態異常〔e="slow", t=120, a=1〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"buff","e":"night","t":240,"a":3}` — 強化〔e="night", t=240, a=3〕
34. `{"op":"chain","n":6,"r":22.0}` — chain〔n=6, r=22.0〕
35. `{"op":"dmg","m":0.45}` — 追加攻撃〔m=0.45〕
36. `{"op":"fx","p":"end_rod","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="end_rod", n=24, at="ring", r=5.5, y=0.7〕
37. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
38. `{"op":"eff","e":"slow","t":43,"a":123}` — 敵への状態異常〔e="slow", t=43, a=123〕
39. `{"op":"self"}` — 対象を自分へ〔〕
40. `{"op":"buff","e":"night","t":160,"a":0}` — 強化〔e="night", t=160, a=0〕
41. `{"op":"fx","p":"enchant","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="enchant", n=16, at="ring", r=3.7, y=0.55〕
42. `{"op":"area","r":16,"n":9}` — 円形対象の取得〔r=16, n=9〕
43. `{"op":"eff","e":"glow","t":120,"a":0}` — 敵への状態異常〔e="glow", t=120, a=0〕
44. `{"op":"mark","t":135,"x":1.8}` — 刻印〔t=135, x=1.8〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 自然魔流の耳飾り — 神格装飾品（Curios relic_charm） (`elseria_charm`)

**現行パラメータ**：rank=1、damage登録値=68.31、relics側CD=185tick、art側CD=185tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（13命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"regen","t":40,"a":0}` — 強化〔e="regen", t=40, a=0〕
03. `{"op":"buff","e":"haste","t":40,"a":0}` — 強化〔e="haste", t=40, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"night","t":45,"a":0}` — 強化〔e="night", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
09. `{"op":"buff","e":"night","t":45,"a":1}` — 強化〔e="night", t=45, a=1〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"night","t":42,"a":2}` — 強化〔e="night", t=42, a=2〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"absorb","t":48,"a":4}` — 強化〔e="absorb", t=48, a=4〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（38命令）**：

01. `{"op":"fx","p":"enchant","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="enchant", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"enchant","n":4,"at":"self","s":0.7}` — 粒子演出〔p="enchant", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":40,"at":"self","s":1.6}` — 粒子演出〔p="end_rod", n=40, at="self", s=1.6〕
04. `{"op":"fx","p":"firework","n":20,"at":"self"}` — 粒子演出〔p="firework", n=20, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":1.6}` — 効果音〔s="chime", v=1.0, pi=1.6〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.25}` — 最大HP割合回復〔v=0.25〕
08. `{"op":"cleanse"}` — 状態異常解除〔〕
09. `{"op":"xp","v":30}` — xp〔v=30〕
10. `{"op":"allies","r":16}` — 味方対象〔r=16〕
11. `{"op":"buff","e":"regen","t":200,"a":2,"to":1}` — 強化〔e="regen", t=200, a=2, to=1〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"night","t":210,"a":1}` — 強化〔e="night", t=210, a=1〕
15. `{"op":"fx","p":"enchant","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="enchant", n=46, at="ring", r=5.5, y=0.25〕
16. `{"op":"fx","p":"witch","n":36,"at":"line","r":24}` — 粒子演出〔p="witch", n=36, at="line", r=24〕
17. `{"op":"sound","s":"spell","v":1.05,"pi":1.14}` — 効果音〔s="spell", v=1.05, pi=1.14〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"guard","t":95}` — 防御〔t=95〕
20. `{"op":"self"}` — 対象を自分へ〔〕
21. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
22. `{"op":"cleanse"}` — 状態異常解除〔〕
23. `{"op":"buff","e":"night","t":180,"a":3}` — 強化〔e="night", t=180, a=3〕
24. `{"op":"guard","t":95}` — 防御〔t=95〕
25. `{"op":"fx","p":"end_rod","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="end_rod", n=30, at="ring", r=4.0, y=0.7〕
26. `{"op":"sound","s":"spell","v":0.8,"pi":1.1}` — 効果音〔s="spell", v=0.8, pi=1.1〕
27. `{"op":"self"}` — 対象を自分へ〔〕
28. `{"op":"buff","e":"night","t":300,"a":4}` — 強化〔e="night", t=300, a=4〕
29. `{"op":"guard","t":140}` — 防御〔t=140〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"night","t":240,"a":2}` — 強化〔e="night", t=240, a=2〕
32. `{"op":"fx","p":"end_rod","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="end_rod", n=20, at="ring", r=4, y=0.4〕
33. `{"op":"self"}` — 対象を自分へ〔〕
34. `{"op":"buff","e":"night","t":160,"a":0}` — 強化〔e="night", t=160, a=0〕
35. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
36. `{"op":"eff","e":"slow","t":32,"a":123}` — 敵への状態異常〔e="slow", t=32, a=123〕
37. `{"op":"self"}` — 対象を自分へ〔〕
38. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 星界大術・原初魔典 — 超越神器（武器欄） (`elseria_legend`)

**現行パラメータ**：rank=3、damage登録値=1157.875、relics側CD=340tick、art側CD=340tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（8命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
07. `{"op":"buff","e":"night","t":45,"a":3}` — 強化〔e="night", t=45, a=3〕
08. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（9命令）**：

01. `{"op":"chain","n":6,"r":12}` — chain〔n=6, r=12〕
02. `{"op":"dmg","m":0.4}` — 追加攻撃〔m=0.4〕
03. `{"op":"lightning"}` — lightning〔〕
04. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"slow","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"slow","t":160,"a":1}]〕
05. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
06. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"enchant","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"enchant","n":10,"at":"t","s":0.35}]〕
07. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
08. `{"op":"chance","p":0.3,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.3, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]〕
09. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":62,"a":5}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":62,"a":5}]〕

**権能発動時の命令（26命令）**：

01. `{"op":"fx","p":"enchant","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="enchant", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"enchant","n":4,"at":"self","s":0.7}` — 粒子演出〔p="enchant", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":40,"at":"self","s":1.6}` — 粒子演出〔p="end_rod", n=40, at="self", s=1.6〕
04. `{"op":"fx","p":"firework","n":20,"at":"self"}` — 粒子演出〔p="firework", n=20, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":1.6}` — 効果音〔s="chime", v=1.0, pi=1.6〕
06. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
07. `{"op":"lightning"}` — lightning〔〕
08. `{"op":"dmg","m":3.36}` — 追加攻撃〔m=3.36〕
09. `{"op":"burn","s":15}` — burn〔s=15〕
10. `{"op":"stun","t":105}` — 行動停止〔t=105〕
11. `{"op":"line","r":64,"w":4}` — 線分対象の取得〔r=64, w=4〕
12. `{"op":"dmg","m":2.24}` — 追加攻撃〔m=2.24〕
13. `{"op":"fx","p":"end_rod","n":72,"at":"line","r":64}` — 粒子演出〔p="end_rod", n=72, at="line", r=64〕
14. `{"op":"allies","r":32}` — 味方対象〔r=32〕
15. `{"op":"healpct","v":0.6,"to":1}` — 最大HP割合回復〔v=0.6, to=1〕
16. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
17. `{"op":"fx","p":"spark","n":12,"at":"t","s":0.5}` — 粒子演出〔p="spark", n=12, at="t", s=0.5〕
18. `{"op":"chain","n":5,"r":16}` — chain〔n=5, r=16〕
19. `{"op":"dmg","m":1.7}` — 追加攻撃〔m=1.7〕
20. `{"op":"mark","t":100,"x":1.4}` — 刻印〔t=100, x=1.4〕
21. `{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="witch", n=50, at="ring", r=8.0, y=0.6〕
22. `{"op":"fx","p":"end_rod","n":32,"at":"line","r":30}` — 粒子演出〔p="end_rod", n=32, at="line", r=30〕
23. `{"op":"sound","s":"spell","v":1.15,"pi":0.95}` — 効果音〔s="spell", v=1.15, pi=0.95〕
24. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.elseria_legend.stage0","ops":[{"op":"fx","p":"end_rod","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"spell","v":0.9,"pi":1.2},{"op":"fx","p":"enchant","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":10},{"op":"fx","p":"enchant","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"witch","n":36,"at":"line","r":24},{"op":"sound","s":"spell","v":1.05,"pi":1.14},{"op":"chain","n":6,"r":20.0},{"op":"dmg","m":3.51},{"op":"eff","e":"slow","t":70,"a":2},{"op":"self"},{"op":"buff","e":"night","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.elseria_legend.stage1","ops":[{"op":"fx","p":"end_rod","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"spell","v":1.05,"pi":1.0},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"enchant","n":6,"at":"line","r":15},{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"end_rod","n":32,"at":"line","r":30},{"op":"sound","s":"spell","v":1.15,"pi":0.95},{"op":"area","r":30.0,"n":24},{"op":"dmg","m":4.06},{"op":"eff","e":"slow","t":70,"a":2},{"op":"self"},{"op":"buff","e":"regen","t":125,"a":2},{"op":"area","r":12.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.elseria_legend.stage2","ops":[{"op":"fx","p":"end_rod","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"spell","v":1.25,"pi":0.75},{"op":"fx","p":"end_rod","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"enchant","n":10,"at":"line","r":20},{"op":"fx","p":"enchant","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"witch","n":48,"at":"line","r":48},{"op":"fx","p":"end_rod","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"spell","v":1.5,"pi":0.75},{"op":"area","r":36.0,"n":30},{"op":"dmg","m":9.396},{"op":"strip"},{"op":"stun","t":50},{"op":"self"},{"op":"buff","e":"strength","t":160,"a":3},{"op":"fx","p":"end_rod","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"enchant","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"chain","n":7,"r":22.0},{"op":"dmg","m":3.0},{"op":"eff","e":"slow","t":100,"a":3},{"op":"self"},{"op":"buff","e":"regen","t":180,"a":2},{"op":"chain","n":5,"r":30.0},{"op":"dmg","m":0.8},{"op":"eff","e":"slow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"night","t":240,"a":4},{"op":"chain","n":6,"r":22.0},{"op":"dmg","m":0.45},{"op":"fx","p":"end_rod","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"spell","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"glow","t":120,"a":0},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.elseria_legend.stage0","ops":[{"op":"fx","p":"end_rod","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"spell","v":0.9,"pi":1.2},{"op":"fx","p":"enchant","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":10},{"op":"fx","p":"enchant","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"witch","n":36,"at":"line","r":24},{"op":"sound","s":"spell","v":1.05,"pi":1.14},{"op":"chain","n":6,"r":20.0},{"op":"dmg","m":3.51},{"op":"eff","e":"slow","t":70,"a":2},{"op":"self"},{"op":"buff","e":"night","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.elseria_legend.stage1","ops":[{"op":"fx","p":"end_rod","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"spell","v":1.05,"pi":1.0},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"enchant","n":6,"at":"line","r":15},{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"end_rod","n":32,"at":"line","r":30},{"op":"sound","s":"spell","v":1.15,"pi":0.95},{"op":"area","r":30.0,"n":24},{"op":"dmg","m":4.06},{"op":"eff","e":"slow","t":70,"a":2},{"op":"self"},{"op":"buff","e":"regen","t":125,"a":2},{"op":"area","r":12.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.elseria_legend.stage2","ops":[{"op":"fx","p":"end_rod","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"spell","v":1.25,"pi":0.75},{"op":"fx","p":"end_rod","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"enchant","n":10,"at":"line","r":20},{"op":"fx","p":"enchant","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"witch","n":48,"at":"line","r":48},{"op":"fx","p":"end_rod","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"spell","v":1.5,"pi":0.75},{"op":"area","r":36.0,"n":30},{"op":"dmg","m":9.396},{"op":"strip"},{"op":"stun","t":50},{"op":"self"},{"op":"buff","e":"strength","t":160,"a":3},{"op":"fx","p":"end_rod","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"enchant","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"chain","n":7,"r":22.0},{"op":"dmg","m":3.0},{"op":"eff","e":"slow","t":100,"a":3},{"op":"self"},{"op":"buff","e":"regen","t":180,"a":2},{"op":"chain","n":5,"r":30.0},{"op":"dmg","m":0.8},{"op":"eff","e":"slow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"night","t":240,"a":4},{"op":"chain","n":6,"r":22.0},{"op":"dmg","m":0.45},{"op":"fx","p":"end_rod","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"spell","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"glow","t":120,"a":0},{"op":"mark","t":135,"x":1.8}]}]〕
25. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
26. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 07. 万機創匠 ヴァレリア・フォルジェ

**モブ側の動きの方向性**：人型の重心と可変武器の連結構造を一体として制御する。。

### 万機創匠の変形槌 — 討伐武器（メイン／武器欄） (`valeria_weapon`)

**現行パラメータ**：rank=1、damage登録値=246.57471、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:knockback:5。

**装備中の常時命令（4命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"repair","v":6}` — 修理〔v=6〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（9命令）**：

01. `{"op":"around","r":3,"n":16,"exclude":1}` — around〔r=3, n=16, exclude=1〕
02. `{"op":"dmg","m":0.3}` — 追加攻撃〔m=0.3〕
03. `{"op":"knock","f":1.0}` — knock〔f=1.0〕
04. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"weakness","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"weakness","t":90,"a":0}]〕
05. `{"op":"chance","p":0.505,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":11,"at":"t","s":0.24},{"op":"mark","t":140,"x":1.79},{"op":"eff","e":"slow","t":55,"a":1}]}` — 抽選〔p=0.505, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":11,"at":"t","s":0.24},{"op":"mark","t":140,"x":1.79},{"op":"eff","e":"slow","t":55,"a":1}]〕
06. `{"op":"chance","p":0.177,"ops":[{"op":"victim"},{"op":"dmg","m":0.235}]}` — 抽選〔p=0.177, ops=[{"op":"victim"},{"op":"dmg","m":0.235}]〕
07. `{"op":"chance","p":0.123,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":8,"at":"t","s":0.25},{"op":"knock","f":0.65}]}` — 抽選〔p=0.123, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":8,"at":"t","s":0.25},{"op":"knock","f":0.65}]〕
08. `{"op":"chance","p":0.2,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.2, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]〕
09. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"wither","t":48,"a":5}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"wither","t":48,"a":5}]〕

**権能発動時の命令（26命令）**：

01. `{"op":"fx","p":"spark","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="spark", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"spark","n":4,"at":"self","s":0.7}` — 粒子演出〔p="spark", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"spark","n":50,"at":"self","s":1.0}` — 粒子演出〔p="spark", n=50, at="self", s=1.0〕
04. `{"op":"fx","p":"smoke","n":20,"at":"self"}` — 粒子演出〔p="smoke", n=20, at="self"〕
05. `{"op":"sound","s":"smith","v":1.0,"pi":0.8}` — 効果音〔s="smith", v=1.0, pi=0.8〕
06. `{"op":"area","r":8,"n":36}` — 円形対象の取得〔r=8, n=36〕
07. `{"op":"dmg","m":1.92}` — 追加攻撃〔m=1.92〕
08. `{"op":"knock","f":3.0}` — knock〔f=3.0〕
09. `{"op":"launch","f":1.2}` — launch〔f=1.2〕
10. `{"op":"repair","v":256}` — 修理〔v=256〕
11. `{"op":"summon","k":"golem","n":1}` — 召喚〔k="golem", n=1〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"fx","p":"spark","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="spark", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"smoke","n":36,"at":"line","r":24}` — 粒子演出〔p="smoke", n=36, at="line", r=24〕
15. `{"op":"line","r":60.0,"w":4.0}` — 線分対象の取得〔r=60.0, w=4.0〕
16. `{"op":"dmg","m":3.1}` — 追加攻撃〔m=3.1〕
17. `{"op":"knock","f":2.4}` — knock〔f=2.4〕
18. `{"op":"fx","p":"spark","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="spark", n=16, at="ring", r=5.0〕
19. `{"op":"sound","s":"spell","v":0.75,"pi":1.15}` — 効果音〔s="spell", v=0.75, pi=1.15〕
20. `{"op":"area","r":9,"n":8}` — 円形対象の取得〔r=9, n=8〕
21. `{"op":"dmg","m":0.9}` — 追加攻撃〔m=0.9〕
22. `{"op":"eff","e":"slow","t":65,"a":0}` — 敵への状態異常〔e="slow", t=65, a=0〕
23. `{"op":"fx","p":"spark","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="spark", n=24, at="ring", r=4.5, y=0.6〕
24. `{"op":"sound","s":"smith","v":0.8,"pi":0.8}` — 効果音〔s="smith", v=0.8, pi=0.8〕
25. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
26. `{"op":"eff","e":"slow","t":32,"a":124}` — 敵への状態異常〔e="slow", t=32, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 万機工作手甲 — 神威触媒（Curios relic_focus） (`valeria_focus`)

**現行パラメータ**：rank=2、damage登録値=68.31、relics側CD=150tick、art側CD=150tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"repair","v":8}` — 修理〔v=8〕
03. `{"op":"buff","e":"haste","t":40,"a":1}` — 強化〔e="haste", t=40, a=1〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"resist","t":45,"a":0}` — 強化〔e="resist", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"haste","t":42,"a":2}` — 強化〔e="haste", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（40命令）**：

01. `{"op":"fx","p":"spark","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="spark", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"spark","n":6,"at":"self","s":0.7}` — 粒子演出〔p="spark", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"spark","n":50,"at":"self","s":1.0}` — 粒子演出〔p="spark", n=50, at="self", s=1.0〕
04. `{"op":"fx","p":"smoke","n":20,"at":"self"}` — 粒子演出〔p="smoke", n=20, at="self"〕
05. `{"op":"sound","s":"smith","v":1.0,"pi":0.8}` — 効果音〔s="smith", v=1.0, pi=0.8〕
06. `{"op":"summon","k":"golem","n":3}` — 召喚〔k="golem", n=3〕
07. `{"op":"repair","v":1024}` — 修理〔v=1024〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"absorb","t":400,"a":4}` — 強化〔e="absorb", t=400, a=4〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"resist","t":150,"a":1}` — 強化〔e="resist", t=150, a=1〕
13. `{"op":"fx","p":"smoke","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="smoke", n=50, at="ring", r=8.0, y=0.6〕
14. `{"op":"fx","p":"firework","n":32,"at":"line","r":30}` — 粒子演出〔p="firework", n=32, at="line", r=30〕
15. `{"op":"sound","s":"anvil","v":1.15,"pi":0.95}` — 効果音〔s="anvil", v=1.15, pi=0.95〕
16. `{"op":"summon","k":"golem","n":3}` — 召喚〔k="golem", n=3〕
17. `{"op":"self"}` — 対象を自分へ〔〕
18. `{"op":"repair","n":48}` — 修理〔n=48〕
19. `{"op":"buff","e":"resist","t":110,"a":2}` — 強化〔e="resist", t=110, a=2〕
20. `{"op":"self"}` — 対象を自分へ〔〕
21. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
22. `{"op":"buff","e":"haste","t":150,"a":3}` — 強化〔e="haste", t=150, a=3〕
23. `{"op":"fx","p":"spark","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="spark", n=24, at="ring", r=12, y=0.5〕
24. `{"op":"sound","s":"smith","v":0.85,"pi":0.97}` — 効果音〔s="smith", v=0.85, pi=0.97〕
25. `{"op":"cone","r":12.0,"a":95.0}` — 扇形対象の取得〔r=12.0, a=95.0〕
26. `{"op":"dmg","m":0.95}` — 追加攻撃〔m=0.95〕
27. `{"op":"eff","e":"slow","t":140,"a":1}` — 敵への状態異常〔e="slow", t=140, a=1〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"buff","e":"haste","t":200,"a":3}` — 強化〔e="haste", t=200, a=3〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"summon","k":"golem","n":1}` — 召喚〔k="golem", n=1〕
32. `{"op":"fx","p":"spark","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="spark", n=24, at="ring", r=5.5, y=0.7〕
33. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
34. `{"op":"eff","e":"slow","t":43,"a":123}` — 敵への状態異常〔e="slow", t=43, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"buff","e":"haste","t":100,"a":123}` — 強化〔e="haste", t=100, a=123〕
37. `{"op":"fx","p":"spark","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="spark", n=16, at="ring", r=3.7, y=0.55〕
38. `{"op":"self"}` — 対象を自分へ〔〕
39. `{"op":"repair","v":180}` — 修理〔v=180〕
40. `{"op":"buff","e":"haste","t":170,"a":6}` — 強化〔e="haste", t=170, a=6〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 自動迎撃の外殻 — 神格装飾品（Curios relic_charm） (`valeria_charm`)

**現行パラメータ**：rank=1、damage登録値=68.31、relics側CD=180tick、art側CD=180tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（13命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"reflect","t":25,"r":8}` — 反射〔t=25, r=8〕
03. `{"op":"buff","e":"resist","t":40,"a":0}` — 強化〔e="resist", t=40, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"resist","t":45,"a":0}` — 強化〔e="resist", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
09. `{"op":"buff","e":"haste","t":45,"a":1}` — 強化〔e="haste", t=45, a=1〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"haste","t":42,"a":2}` — 強化〔e="haste", t=42, a=2〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"haste","t":48,"a":7}` — 強化〔e="haste", t=48, a=7〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（36命令）**：

01. `{"op":"fx","p":"spark","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="spark", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"spark","n":4,"at":"self","s":0.7}` — 粒子演出〔p="spark", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"spark","n":50,"at":"self","s":1.0}` — 粒子演出〔p="spark", n=50, at="self", s=1.0〕
04. `{"op":"fx","p":"smoke","n":20,"at":"self"}` — 粒子演出〔p="smoke", n=20, at="self"〕
05. `{"op":"sound","s":"smith","v":1.0,"pi":0.8}` — 効果音〔s="smith", v=1.0, pi=0.8〕
06. `{"op":"reflect","t":200,"r":16}` — 反射〔t=200, r=16〕
07. `{"op":"erase","r":24}` — erase〔r=24〕
08. `{"op":"guard","t":40}` — 防御〔t=40〕
09. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"resist","t":210,"a":1}` — 強化〔e="resist", t=210, a=1〕
12. `{"op":"fx","p":"spark","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="spark", n=46, at="ring", r=5.5, y=0.25〕
13. `{"op":"fx","p":"smoke","n":36,"at":"line","r":24}` — 粒子演出〔p="smoke", n=36, at="line", r=24〕
14. `{"op":"sound","s":"anvil","v":1.05,"pi":1.14}` — 効果音〔s="anvil", v=1.05, pi=1.14〕
15. `{"op":"self"}` — 対象を自分へ〔〕
16. `{"op":"guard","t":95}` — 防御〔t=95〕
17. `{"op":"self"}` — 対象を自分へ〔〕
18. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
19. `{"op":"cleanse"}` — 状態異常解除〔〕
20. `{"op":"buff","e":"haste","t":180,"a":3}` — 強化〔e="haste", t=180, a=3〕
21. `{"op":"guard","t":95}` — 防御〔t=95〕
22. `{"op":"fx","p":"spark","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="spark", n=30, at="ring", r=4.0, y=0.7〕
23. `{"op":"sound","s":"smith","v":0.8,"pi":1.1}` — 効果音〔s="smith", v=0.8, pi=1.1〕
24. `{"op":"self"}` — 対象を自分へ〔〕
25. `{"op":"buff","e":"haste","t":260,"a":4}` — 強化〔e="haste", t=260, a=4〕
26. `{"op":"guard","t":155}` — 防御〔t=155〕
27. `{"op":"self"}` — 対象を自分へ〔〕
28. `{"op":"repair","v":150}` — 修理〔v=150〕
29. `{"op":"fx","p":"spark","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="spark", n=20, at="ring", r=4, y=0.4〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"haste","t":160,"a":123}` — 強化〔e="haste", t=160, a=123〕
32. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
33. `{"op":"eff","e":"slow","t":32,"a":123}` — 敵への状態異常〔e="slow", t=32, a=123〕
34. `{"op":"self"}` — 対象を自分へ〔〕
35. `{"op":"repair","v":220}` — 修理〔v=220〕
36. `{"op":"guard","t":80}` — 防御〔t=80〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 終着無限・万機工房 — 超越神器（武器欄） (`valeria_legend`)

**現行パラメータ**：rank=3、damage登録値=339.27586、relics側CD=335tick、art側CD=335tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:knockback:5。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"reflect","t":25,"r":10}` — 反射〔t=25, r=10〕
06. `{"op":"repair","v":64}` — 修理〔v=64〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
09. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕
10. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（9命令）**：

01. `{"op":"around","r":4,"n":16,"exclude":1}` — around〔r=4, n=16, exclude=1〕
02. `{"op":"dmg","m":0.4}` — 追加攻撃〔m=0.4〕
03. `{"op":"knock","f":1.5}` — knock〔f=1.5〕
04. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"weakness","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"weakness","t":160,"a":1}]〕
05. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
06. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"spark","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"spark","n":10,"at":"t","s":0.35}]〕
07. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
08. `{"op":"chance","p":0.325,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.325, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]〕
09. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"wither","t":78,"a":7}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"wither","t":78,"a":7}]〕

**権能発動時の命令（25命令）**：

01. `{"op":"fx","p":"spark","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="spark", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"spark","n":4,"at":"self","s":0.7}` — 粒子演出〔p="spark", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"spark","n":50,"at":"self","s":1.0}` — 粒子演出〔p="spark", n=50, at="self", s=1.0〕
04. `{"op":"fx","p":"smoke","n":20,"at":"self"}` — 粒子演出〔p="smoke", n=20, at="self"〕
05. `{"op":"sound","s":"smith","v":1.0,"pi":0.8}` — 効果音〔s="smith", v=1.0, pi=0.8〕
06. `{"op":"summon","k":"golem","n":5}` — 召喚〔k="golem", n=5〕
07. `{"op":"repair","v":99999}` — 修理〔v=99999〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"absorb","t":1200,"a":9}` — 強化〔e="absorb", t=1200, a=9〕
10. `{"op":"guard","t":100}` — 防御〔t=100〕
11. `{"op":"area","r":40,"n":36}` — 円形対象の取得〔r=40, n=36〕
12. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
13. `{"op":"stun","t":105}` — 行動停止〔t=105〕
14. `{"op":"fx","p":"explosion","n":4,"at":"t"}` — 粒子演出〔p="explosion", n=4, at="t"〕
15. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
16. `{"op":"summon","k":"golem","n":3}` — 召喚〔k="golem", n=3〕
17. `{"op":"repair","n":32}` — 修理〔n=32〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"buff","e":"haste","a":2,"t":180}` — 強化〔e="haste", a=2, t=180〕
20. `{"op":"fx","p":"smoke","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="smoke", n=50, at="ring", r=8.0, y=0.6〕
21. `{"op":"fx","p":"firework","n":32,"at":"line","r":30}` — 粒子演出〔p="firework", n=32, at="line", r=30〕
22. `{"op":"sound","s":"anvil","v":1.15,"pi":0.95}` — 効果音〔s="anvil", v=1.15, pi=0.95〕
23. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.valeria_legend.stage0","ops":[{"op":"fx","p":"spark","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"smith","v":0.9,"pi":1.2},{"op":"fx","p":"spark","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"wax","n":6,"at":"line","r":10},{"op":"fx","p":"spark","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"smoke","n":36,"at":"line","r":24},{"op":"sound","s":"anvil","v":1.05,"pi":1.14},{"op":"line","r":60.0,"w":4.0},{"op":"dmg","m":4.185},{"op":"knock","f":2.4},{"op":"self"},{"op":"buff","e":"haste","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.valeria_legend.stage1","ops":[{"op":"fx","p":"spark","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"smith","v":1.05,"pi":1.0},{"op":"fx","p":"wax","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"spark","n":6,"at":"line","r":15},{"op":"fx","p":"smoke","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"firework","n":32,"at":"line","r":30},{"op":"sound","s":"anvil","v":1.15,"pi":0.95},{"op":"summon","k":"golem","n":3},{"op":"self"},{"op":"repair","n":48},{"op":"buff","e":"resist","t":110,"a":2},{"op":"area","r":14.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.valeria_legend.stage2","ops":[{"op":"fx","p":"spark","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"smith","v":1.25,"pi":0.75},{"op":"fx","p":"wax","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"spark","n":10,"at":"line","r":20},{"op":"fx","p":"spark","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"smoke","n":48,"at":"line","r":48},{"op":"fx","p":"firework","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"anvil","v":1.5,"pi":0.75},{"op":"area","r":34.0,"n":28},{"op":"dmg","m":10.368},{"op":"stun","t":55},{"op":"summon","k":"golem","n":4},{"op":"self"},{"op":"guard","t":135},{"op":"fx","p":"firework","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"spark","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":30.0,"n":25},{"op":"dmg","m":2.7},{"op":"stun","t":45},{"op":"summon","k":"golem","n":3},{"op":"self"},{"op":"repair","n":60},{"op":"cone","r":15.0,"a":110.0},{"op":"dmg","m":0.9},{"op":"eff","e":"slow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"haste","t":240,"a":4},{"op":"self"},{"op":"summon","k":"golem","n":2},{"op":"fx","p":"spark","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"smith","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"self"},{"op":"repair","v":260},{"op":"area","r":17,"n":9},{"op":"eff","e":"fatigue","t":65,"a":20}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.valeria_legend.stage0","ops":[{"op":"fx","p":"spark","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"smith","v":0.9,"pi":1.2},{"op":"fx","p":"spark","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"wax","n":6,"at":"line","r":10},{"op":"fx","p":"spark","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"smoke","n":36,"at":"line","r":24},{"op":"sound","s":"anvil","v":1.05,"pi":1.14},{"op":"line","r":60.0,"w":4.0},{"op":"dmg","m":4.185},{"op":"knock","f":2.4},{"op":"self"},{"op":"buff","e":"haste","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.valeria_legend.stage1","ops":[{"op":"fx","p":"spark","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"smith","v":1.05,"pi":1.0},{"op":"fx","p":"wax","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"spark","n":6,"at":"line","r":15},{"op":"fx","p":"smoke","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"firework","n":32,"at":"line","r":30},{"op":"sound","s":"anvil","v":1.15,"pi":0.95},{"op":"summon","k":"golem","n":3},{"op":"self"},{"op":"repair","n":48},{"op":"buff","e":"resist","t":110,"a":2},{"op":"area","r":14.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.valeria_legend.stage2","ops":[{"op":"fx","p":"spark","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"smith","v":1.25,"pi":0.75},{"op":"fx","p":"wax","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"spark","n":10,"at":"line","r":20},{"op":"fx","p":"spark","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"smoke","n":48,"at":"line","r":48},{"op":"fx","p":"firework","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"anvil","v":1.5,"pi":0.75},{"op":"area","r":34.0,"n":28},{"op":"dmg","m":10.368},{"op":"stun","t":55},{"op":"summon","k":"golem","n":4},{"op":"self"},{"op":"guard","t":135},{"op":"fx","p":"firework","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"spark","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":30.0,"n":25},{"op":"dmg","m":2.7},{"op":"stun","t":45},{"op":"summon","k":"golem","n":3},{"op":"self"},{"op":"repair","n":60},{"op":"cone","r":15.0,"a":110.0},{"op":"dmg","m":0.9},{"op":"eff","e":"slow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"haste","t":240,"a":4},{"op":"self"},{"op":"summon","k":"golem","n":2},{"op":"fx","p":"spark","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"smith","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"self"},{"op":"repair","v":260},{"op":"area","r":17,"n":9},{"op":"eff","e":"fatigue","t":65,"a":20}]}]〕
24. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
25. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 08. 黄天龍仙 皇玲華

**モブ側の動きの方向性**：指印、太極円運動、踏み込み、龍気の流線を同期させる。。

### 黄天龍仙槍 — 討伐武器（メイン／武器欄） (`huang_linghua_weapon`)

**現行パラメータ**：rank=1、damage登録値=301.39683、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12。

**装備中の常時命令（5命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"absorb","t":40,"a":1}` — 強化〔e="absorb", t=40, a=1〕
03. `{"op":"buff","e":"regen","t":40,"a":0}` — 強化〔e="regen", t=40, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（10命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"stun","t":20}` — 行動停止〔t=20〕
03. `{"op":"around","r":3,"n":16,"exclude":1}` — around〔r=3, n=16, exclude=1〕
04. `{"op":"dmg","m":0.2}` — 追加攻撃〔m=0.2〕
05. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"slow","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"slow","t":90,"a":0}]〕
06. `{"op":"chance","p":0.51,"ops":[{"op":"victim"},{"op":"fx","p":"electric_spark","n":13,"at":"t","s":0.24},{"op":"mark","t":160,"x":1.93},{"op":"eff","e":"slow","t":67,"a":0}]}` — 抽選〔p=0.51, ops=[{"op":"victim"},{"op":"fx","p":"electric_spark","n":13,"at":"t","s":0.24},{"op":"mark","t":160,"x":1.93},{"op":"eff","e":"slow","t":67,"a":0}]〕
07. `{"op":"chance","p":0.204,"ops":[{"op":"victim"},{"op":"dmg","m":0.27}]}` — 抽選〔p=0.204, ops=[{"op":"victim"},{"op":"dmg","m":0.27}]〕
08. `{"op":"chance","p":0.142,"ops":[{"op":"victim"},{"op":"fx","p":"electric_spark","n":8,"at":"t","s":0.25},{"op":"stun","t":8}]}` — 抽選〔p=0.142, ops=[{"op":"victim"},{"op":"fx","p":"electric_spark","n":8,"at":"t","s":0.25},{"op":"stun","t":8}]〕
09. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"electric_spark","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"electric_spark","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]〕
10. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]〕

**権能発動時の命令（26命令）**：

01. `{"op":"fx","p":"electric_spark","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="electric_spark", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"electric_spark","n":4,"at":"self","s":0.7}` — 粒子演出〔p="electric_spark", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"wax","n":30,"at":"ring","r":3}` — 粒子演出〔p="wax", n=30, at="ring", r=3〕
04. `{"op":"fx","p":"spark","n":30,"at":"self"}` — 粒子演出〔p="spark", n=30, at="self"〕
05. `{"op":"sound","s":"roar","v":0.5,"pi":1.4}` — 効果音〔s="roar", v=0.5, pi=1.4〕
06. `{"op":"line","r":32,"w":3}` — 線分対象の取得〔r=32, w=3〕
07. `{"op":"dmg","m":1.8}` — 追加攻撃〔m=1.8〕
08. `{"op":"knock","f":3.0}` — knock〔f=3.0〕
09. `{"op":"launch","f":1.0}` — launch〔f=1.0〕
10. `{"op":"allies","r":12}` — 味方対象〔r=12〕
11. `{"op":"healpct","v":0.25,"to":1}` — 最大HP割合回復〔v=0.25, to=1〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"fx","p":"spark","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="spark", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"splash","n":36,"at":"line","r":24}` — 粒子演出〔p="splash", n=36, at="line", r=24〕
15. `{"op":"chain","n":5,"r":18.0}` — chain〔n=5, r=18.0〕
16. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
17. `{"op":"eff","e":"slow","t":80,"a":1}` — 敵への状態異常〔e="slow", t=80, a=1〕
18. `{"op":"fx","p":"electric_spark","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="electric_spark", n=16, at="ring", r=5.0〕
19. `{"op":"sound","s":"sonic","v":0.75,"pi":1.15}` — 効果音〔s="sonic", v=0.75, pi=1.15〕
20. `{"op":"line","r":18,"w":2}` — 線分対象の取得〔r=18, w=2〕
21. `{"op":"dmg","m":1.05}` — 追加攻撃〔m=1.05〕
22. `{"op":"eff","e":"slow","t":65,"a":0}` — 敵への状態異常〔e="slow", t=65, a=0〕
23. `{"op":"fx","p":"electric_spark","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="electric_spark", n=24, at="ring", r=4.5, y=0.6〕
24. `{"op":"sound","s":"roar","v":0.8,"pi":0.8}` — 効果音〔s="roar", v=0.8, pi=0.8〕
25. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
26. `{"op":"eff","e":"slow","t":32,"a":124}` — 敵への状態異常〔e="slow", t=32, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 三界龍文の霊符 — 神威触媒（Curios relic_focus） (`huang_linghua_focus`)

**現行パラメータ**：rank=2、damage登録値=71.7255、relics側CD=145tick、art側CD=145tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"water","t":300,"a":0}` — 強化〔e="water", t=300, a=0〕
03. `{"op":"buff","e":"dolphin","t":40,"a":1}` — 強化〔e="dolphin", t=40, a=1〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"jump","t":45,"a":0}` — 強化〔e="jump", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"speed","t":45,"a":2}` — 強化〔e="speed", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"strength","t":42,"a":2}` — 強化〔e="strength", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（44命令）**：

01. `{"op":"fx","p":"electric_spark","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="electric_spark", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"electric_spark","n":6,"at":"self","s":0.7}` — 粒子演出〔p="electric_spark", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"wax","n":30,"at":"ring","r":3}` — 粒子演出〔p="wax", n=30, at="ring", r=3〕
04. `{"op":"fx","p":"spark","n":30,"at":"self"}` — 粒子演出〔p="spark", n=30, at="self"〕
05. `{"op":"sound","s":"roar","v":0.5,"pi":1.4}` — 効果音〔s="roar", v=0.5, pi=1.4〕
06. `{"op":"fx","p":"end_rod","n":44,"at":"ring","r":10}` — 粒子演出〔p="end_rod", n=44, at="ring", r=10〕
07. `{"op":"area","r":32,"n":36}` — 円形対象の取得〔r=32, n=36〕
08. `{"op":"lightning"}` — lightning〔〕
09. `{"op":"dmg","m":1.2}` — 追加攻撃〔m=1.2〕
10. `{"op":"slam","f":2.0}` — slam〔f=2.0〕
11. `{"op":"stun","t":90}` — 行動停止〔t=90〕
12. `{"op":"eff","e":"slow","t":200,"a":4}` — 敵への状態異常〔e="slow", t=200, a=4〕
13. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
14. `{"op":"self"}` — 対象を自分へ〔〕
15. `{"op":"buff","e":"jump","t":150,"a":1}` — 強化〔e="jump", t=150, a=1〕
16. `{"op":"fx","p":"splash","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="splash", n=50, at="ring", r=8.0, y=0.6〕
17. `{"op":"fx","p":"end_rod","n":32,"at":"line","r":30}` — 粒子演出〔p="end_rod", n=32, at="line", r=30〕
18. `{"op":"sound","s":"roar","v":1.15,"pi":0.95}` — 効果音〔s="roar", v=1.15, pi=0.95〕
19. `{"op":"cone","r":32.0,"a":95.0}` — 扇形対象の取得〔r=32.0, a=95.0〕
20. `{"op":"dmg","m":2.5}` — 追加攻撃〔m=2.5〕
21. `{"op":"knock","f":3.2}` — knock〔f=3.2〕
22. `{"op":"self"}` — 対象を自分へ〔〕
23. `{"op":"buff","e":"jump","t":160,"a":3}` — 強化〔e="jump", t=160, a=3〕
24. `{"op":"self"}` — 対象を自分へ〔〕
25. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
26. `{"op":"buff","e":"speed","t":150,"a":3}` — 強化〔e="speed", t=150, a=3〕
27. `{"op":"fx","p":"electric_spark","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="electric_spark", n=24, at="ring", r=12, y=0.5〕
28. `{"op":"sound","s":"roar","v":0.85,"pi":1.04}` — 効果音〔s="roar", v=0.85, pi=1.04〕
29. `{"op":"chain","n":4,"r":16.0}` — chain〔n=4, r=16.0〕
30. `{"op":"dmg","m":0.7}` — 追加攻撃〔m=0.7〕
31. `{"op":"eff","e":"slow","t":160,"a":1}` — 敵への状態異常〔e="slow", t=160, a=1〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"buff","e":"strength","t":220,"a":3}` — 強化〔e="strength", t=220, a=3〕
34. `{"op":"area","r":20,"n":5}` — 円形対象の取得〔r=20, n=5〕
35. `{"op":"lightning"}` — lightning〔〕
36. `{"op":"fx","p":"electric_spark","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="electric_spark", n=24, at="ring", r=5.5, y=0.7〕
37. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
38. `{"op":"eff","e":"slow","t":43,"a":123}` — 敵への状態異常〔e="slow", t=43, a=123〕
39. `{"op":"self"}` — 対象を自分へ〔〕
40. `{"op":"buff","e":"strength","t":80,"a":19}` — 強化〔e="strength", t=80, a=19〕
41. `{"op":"fx","p":"spark","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="spark", n=16, at="ring", r=3.7, y=0.55〕
42. `{"op":"cone","r":12,"a":100}` — 扇形対象の取得〔r=12, a=100〕
43. `{"op":"eff","e":"levitate","t":24,"a":3}` — 敵への状態異常〔e="levitate", t=24, a=3〕
44. `{"op":"knock","f":2.1}` — knock〔f=2.1〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 龍炉の心臓飾り — 神格装飾品（Curios relic_charm） (`huang_linghua_charm`)

**現行パラメータ**：rank=1、damage登録値=71.7255、relics側CD=175tick、art側CD=175tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（12命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"jump","t":45,"a":0}` — 強化〔e="jump", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
08. `{"op":"buff","e":"speed","t":45,"a":1}` — 強化〔e="speed", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"strength","t":42,"a":2}` — 強化〔e="strength", t=42, a=2〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"speed","t":48,"a":5}` — 強化〔e="speed", t=48, a=5〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（37命令）**：

01. `{"op":"fx","p":"electric_spark","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="electric_spark", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"electric_spark","n":4,"at":"self","s":0.7}` — 粒子演出〔p="electric_spark", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"wax","n":30,"at":"ring","r":3}` — 粒子演出〔p="wax", n=30, at="ring", r=3〕
04. `{"op":"fx","p":"spark","n":30,"at":"self"}` — 粒子演出〔p="spark", n=30, at="self"〕
05. `{"op":"sound","s":"roar","v":0.5,"pi":1.4}` — 効果音〔s="roar", v=0.5, pi=1.4〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.25}` — 最大HP割合回復〔v=0.25〕
08. `{"op":"cleanse"}` — 状態異常解除〔〕
09. `{"op":"buff","e":"regen","t":200,"a":3}` — 強化〔e="regen", t=200, a=3〕
10. `{"op":"buff","e":"absorb","t":400,"a":4}` — 強化〔e="absorb", t=400, a=4〕
11. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"jump","t":210,"a":1}` — 強化〔e="jump", t=210, a=1〕
14. `{"op":"fx","p":"spark","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="spark", n=46, at="ring", r=5.5, y=0.25〕
15. `{"op":"fx","p":"splash","n":36,"at":"line","r":24}` — 粒子演出〔p="splash", n=36, at="line", r=24〕
16. `{"op":"sound","s":"roar","v":1.05,"pi":1.14}` — 効果音〔s="roar", v=1.05, pi=1.14〕
17. `{"op":"self"}` — 対象を自分へ〔〕
18. `{"op":"guard","t":95}` — 防御〔t=95〕
19. `{"op":"self"}` — 対象を自分へ〔〕
20. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
21. `{"op":"cleanse"}` — 状態異常解除〔〕
22. `{"op":"buff","e":"speed","t":180,"a":3}` — 強化〔e="speed", t=180, a=3〕
23. `{"op":"guard","t":95}` — 防御〔t=95〕
24. `{"op":"fx","p":"electric_spark","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="electric_spark", n=30, at="ring", r=4.0, y=0.7〕
25. `{"op":"sound","s":"roar","v":0.8,"pi":1.1}` — 効果音〔s="roar", v=0.8, pi=1.1〕
26. `{"op":"self"}` — 対象を自分へ〔〕
27. `{"op":"buff","e":"strength","t":280,"a":4}` — 強化〔e="strength", t=280, a=4〕
28. `{"op":"guard","t":170}` — 防御〔t=170〕
29. `{"op":"self"}` — 対象を自分へ〔〕
30. `{"op":"buff","e":"jump","t":240,"a":2}` — 強化〔e="jump", t=240, a=2〕
31. `{"op":"fx","p":"electric_spark","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="electric_spark", n=20, at="ring", r=4, y=0.4〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"buff","e":"strength","t":110,"a":31}` — 強化〔e="strength", t=110, a=31〕
34. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
35. `{"op":"eff","e":"slow","t":32,"a":123}` — 敵への状態異常〔e="slow", t=32, a=123〕
36. `{"op":"self"}` — 対象を自分へ〔〕
37. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 皇龍創法・万龍封界 — 超越神器（武器欄） (`huang_linghua_legend`)

**現行パラメータ**：rank=3、damage登録値=461.2381、relics側CD=330tick、art側CD=330tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"allies","r":16}` — 味方対象〔r=16〕
06. `{"op":"buff","e":"regen","t":40,"a":0,"to":1}` — 強化〔e="regen", t=40, a=0, to=1〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
09. `{"op":"buff","e":"speed","t":45,"a":3}` — 強化〔e="speed", t=45, a=3〕
10. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（8命令）**：

01. `{"op":"chain","n":5,"r":10}` — chain〔n=5, r=10〕
02. `{"op":"dmg","m":0.3}` — 追加攻撃〔m=0.3〕
03. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"slow","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"slow","t":160,"a":1}]〕
04. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
05. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"spark","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"spark","n":10,"at":"t","s":0.35}]〕
06. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
07. `{"op":"chance","p":0.35,"ops":[{"op":"victim"},{"op":"fx","p":"electric_spark","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.35, ops=[{"op":"victim"},{"op":"fx","p":"electric_spark","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]〕
08. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]〕

**権能発動時の命令（26命令）**：

01. `{"op":"fx","p":"electric_spark","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="electric_spark", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"electric_spark","n":4,"at":"self","s":0.7}` — 粒子演出〔p="electric_spark", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"wax","n":30,"at":"ring","r":3}` — 粒子演出〔p="wax", n=30, at="ring", r=3〕
04. `{"op":"fx","p":"spark","n":30,"at":"self"}` — 粒子演出〔p="spark", n=30, at="self"〕
05. `{"op":"sound","s":"roar","v":0.5,"pi":1.4}` — 効果音〔s="roar", v=0.5, pi=1.4〕
06. `{"op":"fx","p":"end_rod","n":44,"at":"ring","r":10}` — 粒子演出〔p="end_rod", n=44, at="ring", r=10〕
07. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
08. `{"op":"stun","t":105}` — 行動停止〔t=105〕
09. `{"op":"lightning"}` — lightning〔〕
10. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
11. `{"op":"mark","t":400,"x":2.5}` — 刻印〔t=400, x=2.5〕
12. `{"op":"allies","r":32}` — 味方対象〔r=32〕
13. `{"op":"healpct","v":0.6,"to":1}` — 最大HP割合回復〔v=0.6, to=1〕
14. `{"op":"buff","e":"absorb","t":600,"a":5,"to":1}` — 強化〔e="absorb", t=600, a=5, to=1〕
15. `{"op":"self"}` — 対象を自分へ〔〕
16. `{"op":"undying","t":180}` — 死亡防護〔t=180〕
17. `{"op":"fx","p":"spark","n":12,"at":"t","s":0.5}` — 粒子演出〔p="spark", n=12, at="t", s=0.5〕
18. `{"op":"cone","r":36,"a":85}` — 扇形対象の取得〔r=36, a=85〕
19. `{"op":"dmg","m":1.6}` — 追加攻撃〔m=1.6〕
20. `{"op":"knock","f":2.5}` — knock〔f=2.5〕
21. `{"op":"fx","p":"splash","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="splash", n=50, at="ring", r=8.0, y=0.6〕
22. `{"op":"fx","p":"end_rod","n":32,"at":"line","r":30}` — 粒子演出〔p="end_rod", n=32, at="line", r=30〕
23. `{"op":"sound","s":"roar","v":1.15,"pi":0.95}` — 効果音〔s="roar", v=1.15, pi=0.95〕
24. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.huang_linghua_legend.stage0","ops":[{"op":"fx","p":"electric_spark","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"roar","v":0.9,"pi":1.2},{"op":"fx","p":"spark","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"splash","n":6,"at":"line","r":10},{"op":"fx","p":"spark","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"splash","n":36,"at":"line","r":24},{"op":"sound","s":"roar","v":1.05,"pi":1.14},{"op":"chain","n":5,"r":18.0},{"op":"dmg","m":3.78},{"op":"eff","e":"slow","t":80,"a":1},{"op":"self"},{"op":"buff","e":"strength","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.huang_linghua_legend.stage1","ops":[{"op":"fx","p":"electric_spark","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"roar","v":1.05,"pi":1.0},{"op":"fx","p":"splash","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"spark","n":6,"at":"line","r":15},{"op":"fx","p":"splash","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"end_rod","n":32,"at":"line","r":30},{"op":"sound","s":"roar","v":1.15,"pi":0.95},{"op":"cone","r":32.0,"a":95.0},{"op":"dmg","m":3.625},{"op":"knock","f":3.2},{"op":"self"},{"op":"buff","e":"jump","t":160,"a":3},{"op":"area","r":16.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.huang_linghua_legend.stage2","ops":[{"op":"fx","p":"electric_spark","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"roar","v":1.25,"pi":0.75},{"op":"fx","p":"splash","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"spark","n":10,"at":"line","r":20},{"op":"fx","p":"spark","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"splash","n":48,"at":"line","r":48},{"op":"fx","p":"end_rod","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"roar","v":1.5,"pi":0.75},{"op":"area","r":36.0,"n":26},{"op":"dmg","m":10.044},{"op":"stun","t":60},{"op":"self"},{"op":"buff","e":"strength","t":180,"a":3},{"op":"fx","p":"end_rod","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"spark","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":32.0,"n":25},{"op":"dmg","m":3.0},{"op":"knock","f":3.4},{"op":"self"},{"op":"buff","e":"strength","t":180,"a":4},{"op":"chain","n":5,"r":18.0},{"op":"dmg","m":1.0},{"op":"eff","e":"slow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"strength","t":240,"a":4},{"op":"area","r":20,"n":5},{"op":"lightning"},{"op":"fx","p":"electric_spark","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"roar","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"levitate","t":24,"a":3},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.huang_linghua_legend.stage0","ops":[{"op":"fx","p":"electric_spark","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"roar","v":0.9,"pi":1.2},{"op":"fx","p":"spark","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"splash","n":6,"at":"line","r":10},{"op":"fx","p":"spark","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"splash","n":36,"at":"line","r":24},{"op":"sound","s":"roar","v":1.05,"pi":1.14},{"op":"chain","n":5,"r":18.0},{"op":"dmg","m":3.78},{"op":"eff","e":"slow","t":80,"a":1},{"op":"self"},{"op":"buff","e":"strength","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.huang_linghua_legend.stage1","ops":[{"op":"fx","p":"electric_spark","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"roar","v":1.05,"pi":1.0},{"op":"fx","p":"splash","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"spark","n":6,"at":"line","r":15},{"op":"fx","p":"splash","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"end_rod","n":32,"at":"line","r":30},{"op":"sound","s":"roar","v":1.15,"pi":0.95},{"op":"cone","r":32.0,"a":95.0},{"op":"dmg","m":3.625},{"op":"knock","f":3.2},{"op":"self"},{"op":"buff","e":"jump","t":160,"a":3},{"op":"area","r":16.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.huang_linghua_legend.stage2","ops":[{"op":"fx","p":"electric_spark","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"roar","v":1.25,"pi":0.75},{"op":"fx","p":"splash","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"spark","n":10,"at":"line","r":20},{"op":"fx","p":"spark","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"splash","n":48,"at":"line","r":48},{"op":"fx","p":"end_rod","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"roar","v":1.5,"pi":0.75},{"op":"area","r":36.0,"n":26},{"op":"dmg","m":10.044},{"op":"stun","t":60},{"op":"self"},{"op":"buff","e":"strength","t":180,"a":3},{"op":"fx","p":"end_rod","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"spark","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":32.0,"n":25},{"op":"dmg","m":3.0},{"op":"knock","f":3.4},{"op":"self"},{"op":"buff","e":"strength","t":180,"a":4},{"op":"chain","n":5,"r":18.0},{"op":"dmg","m":1.0},{"op":"eff","e":"slow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"strength","t":240,"a":4},{"op":"area","r":20,"n":5},{"op":"lightning"},{"op":"fx","p":"electric_spark","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"roar","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"levitate","t":24,"a":3},{"op":"mark","t":135,"x":1.8}]}]〕
25. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
26. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 09. 文明遊匠 フェルディナント・カーディア

**モブ側の動きの方向性**：本人の操作より都市建築、生産設備、物流の成長を主役にする。。

### 試作零号魔導連射砲 — 討伐武器（メイン／武器欄） (`ferdinand_weapon`)

**現行パラメータ**：rank=1、damage登録値=661.71429、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10、minecraft:quick_charge:4、minecraft:efficiency:125。

**装備中の常時命令（4命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"repair","v":4}` — 修理〔v=4〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（7命令）**：

01. `{"op":"chance","p":0.3,"ops":[{"op":"around","r":4,"n":16,"exclude":1},{"op":"dmg","m":0.3},{"op":"fx","p":"explosion","n":2,"at":"t"}]}` — 抽選〔p=0.3, ops=[{"op":"around","r":4,"n":16,"exclude":1},{"op":"dmg","m":0.3},{"op":"fx","p":"explosion","n":2,"at":"t"}]〕
02. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"glow","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"glow","t":90,"a":0}]〕
03. `{"op":"chance","p":0.535,"ops":[{"op":"victim"},{"op":"fx","p":"smoke","n":15,"at":"t","s":0.24},{"op":"mark","t":180,"x":2.07},{"op":"eff","e":"weakness","t":79,"a":0}]}` — 抽選〔p=0.535, ops=[{"op":"victim"},{"op":"fx","p":"smoke","n":15,"at":"t","s":0.24},{"op":"mark","t":180,"x":2.07},{"op":"eff","e":"weakness","t":79,"a":0}]〕
04. `{"op":"chance","p":0.231,"ops":[{"op":"victim"},{"op":"dmg","m":0.305}]}` — 抽選〔p=0.231, ops=[{"op":"victim"},{"op":"dmg","m":0.305}]〕
05. `{"op":"chance","p":0.085,"ops":[{"op":"victim"},{"op":"fx","p":"smoke","n":8,"at":"t","s":0.25},{"op":"dmg","m":0.25}]}` — 抽選〔p=0.085, ops=[{"op":"victim"},{"op":"fx","p":"smoke","n":8,"at":"t","s":0.25},{"op":"dmg","m":0.25}]〕
06. `{"op":"chance","p":0.24,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":14,"at":"t","s":0.28},{"op":"eff","e":"fatigue","t":110,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.24, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":14,"at":"t","s":0.28},{"op":"eff","e":"fatigue","t":110,"a":124},{"op":"mark","t":100,"x":2.15}]〕
07. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]〕

**権能発動時の命令（27命令）**：

01. `{"op":"fx","p":"smoke","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="smoke", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"smoke","n":4,"at":"self","s":0.7}` — 粒子演出〔p="smoke", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"spark","n":50,"at":"self","s":1.0}` — 粒子演出〔p="spark", n=50, at="self", s=1.0〕
04. `{"op":"fx","p":"smoke","n":20,"at":"self"}` — 粒子演出〔p="smoke", n=20, at="self"〕
05. `{"op":"sound","s":"smith","v":1.0,"pi":0.8}` — 効果音〔s="smith", v=1.0, pi=0.8〕
06. `{"op":"fx","p":"firework","n":40,"at":"line","r":48}` — 粒子演出〔p="firework", n=40, at="line", r=48〕
07. `{"op":"line","r":48,"w":2}` — 線分対象の取得〔r=48, w=2〕
08. `{"op":"dmg","m":1.44}` — 追加攻撃〔m=1.44〕
09. `{"op":"arrows","n":6,"d":30}` — arrows〔n=6, d=30〕
10. `{"op":"cone","r":20,"a":40}` — 扇形対象の取得〔r=20, a=40〕
11. `{"op":"dmg","m":0.72}` — 追加攻撃〔m=0.72〕
12. `{"op":"burn","s":4}` — burn〔s=4〕
13. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
14. `{"op":"fx","p":"smoke","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="smoke", n=46, at="ring", r=5.5, y=0.25〕
15. `{"op":"fx","p":"spark","n":36,"at":"line","r":24}` — 粒子演出〔p="spark", n=36, at="line", r=24〕
16. `{"op":"line","r":55.0,"w":5.0}` — 線分対象の取得〔r=55.0, w=5.0〕
17. `{"op":"dmg","m":2.9}` — 追加攻撃〔m=2.9〕
18. `{"op":"mark","t":130,"x":1.6}` — 刻印〔t=130, x=1.6〕
19. `{"op":"fx","p":"spark","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="spark", n=16, at="ring", r=5.0〕
20. `{"op":"sound","s":"sonic","v":0.75,"pi":1.15}` — 効果音〔s="sonic", v=0.75, pi=1.15〕
21. `{"op":"line","r":18,"w":2}` — 線分対象の取得〔r=18, w=2〕
22. `{"op":"dmg","m":1.05}` — 追加攻撃〔m=1.05〕
23. `{"op":"eff","e":"weakness","t":65,"a":0}` — 敵への状態異常〔e="weakness", t=65, a=0〕
24. `{"op":"fx","p":"spark","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="spark", n=24, at="ring", r=4.5, y=0.6〕
25. `{"op":"sound","s":"smith","v":0.8,"pi":0.8}` — 効果音〔s="smith", v=0.8, pi=0.8〕
26. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
27. `{"op":"eff","e":"fatigue","t":110,"a":124}` — 敵への状態異常〔e="fatigue", t=110, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 文明遊匠の万能工具 — 神威触媒（Curios relic_focus） (`ferdinand_focus`)

**現行パラメータ**：rank=2、damage登録値=68.31、relics側CD=160tick、art側CD=160tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"haste","t":40,"a":2}` — 強化〔e="haste", t=40, a=2〕
03. `{"op":"repair","v":6}` — 修理〔v=6〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":0}` — 強化〔e="haste", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"haste","t":42,"a":2}` — 強化〔e="haste", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（42命令）**：

01. `{"op":"fx","p":"smoke","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="smoke", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"smoke","n":6,"at":"self","s":0.7}` — 粒子演出〔p="smoke", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"spark","n":50,"at":"self","s":1.0}` — 粒子演出〔p="spark", n=50, at="self", s=1.0〕
04. `{"op":"fx","p":"smoke","n":20,"at":"self"}` — 粒子演出〔p="smoke", n=20, at="self"〕
05. `{"op":"sound","s":"smith","v":1.0,"pi":0.8}` — 効果音〔s="smith", v=1.0, pi=0.8〕
06. `{"op":"give","item":"redstone","n":8}` — give〔item="redstone", n=8〕
07. `{"op":"give","item":"iron","n":8}` — give〔item="iron", n=8〕
08. `{"op":"give","item":"gold","n":4}` — give〔item="gold", n=4〕
09. `{"op":"give","item":"coal","n":8}` — give〔item="coal", n=8〕
10. `{"op":"repair","v":2048}` — 修理〔v=2048〕
11. `{"op":"summon","k":"golem","n":2}` — 召喚〔k="golem", n=2〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"haste","t":150,"a":1}` — 強化〔e="haste", t=150, a=1〕
15. `{"op":"fx","p":"spark","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="spark", n=50, at="ring", r=8.0, y=0.6〕
16. `{"op":"fx","p":"blast","n":32,"at":"line","r":30}` — 粒子演出〔p="blast", n=32, at="line", r=30〕
17. `{"op":"sound","s":"anvil","v":1.15,"pi":0.95}` — 効果音〔s="anvil", v=1.15, pi=0.95〕
18. `{"op":"summon","k":"golem","n":4}` — 召喚〔k="golem", n=4〕
19. `{"op":"self"}` — 対象を自分へ〔〕
20. `{"op":"repair","n":44}` — 修理〔n=44〕
21. `{"op":"guard","t":105}` — 防御〔t=105〕
22. `{"op":"self"}` — 対象を自分へ〔〕
23. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
24. `{"op":"buff","e":"haste","t":150,"a":3}` — 強化〔e="haste", t=150, a=3〕
25. `{"op":"fx","p":"spark","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="spark", n=24, at="ring", r=12, y=0.5〕
26. `{"op":"sound","s":"smith","v":0.85,"pi":1.11}` — 効果音〔s="smith", v=0.85, pi=1.11〕
27. `{"op":"area","r":16.0,"n":12}` — 円形対象の取得〔r=16.0, n=12〕
28. `{"op":"dmg","m":0.8}` — 追加攻撃〔m=0.8〕
29. `{"op":"eff","e":"fatigue","t":100,"a":1}` — 敵への状態異常〔e="fatigue", t=100, a=1〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"haste","t":240,"a":3}` — 強化〔e="haste", t=240, a=3〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"summon","k":"golem","n":1}` — 召喚〔k="golem", n=1〕
34. `{"op":"fx","p":"spark","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="spark", n=24, at="ring", r=5.5, y=0.7〕
35. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
36. `{"op":"eff","e":"fatigue","t":148,"a":123}` — 敵への状態異常〔e="fatigue", t=148, a=123〕
37. `{"op":"self"}` — 対象を自分へ〔〕
38. `{"op":"buff","e":"haste","t":100,"a":123}` — 強化〔e="haste", t=100, a=123〕
39. `{"op":"fx","p":"spark","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="spark", n=16, at="ring", r=3.7, y=0.55〕
40. `{"op":"self"}` — 対象を自分へ〔〕
41. `{"op":"repair","v":180}` — 修理〔v=180〕
42. `{"op":"buff","e":"haste","t":170,"a":6}` — 強化〔e="haste", t=170, a=6〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 魔導歯車の時計 — 神格装飾品（Curios relic_charm） (`ferdinand_charm`)

**現行パラメータ**：rank=1、damage登録値=68.31、relics側CD=190tick、art側CD=190tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（13命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"speed","t":40,"a":0}` — 強化〔e="speed", t=40, a=0〕
03. `{"op":"buff","e":"night","t":300,"a":0}` — 強化〔e="night", t=300, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":0}` — 強化〔e="haste", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
09. `{"op":"buff","e":"haste","t":45,"a":1}` — 強化〔e="haste", t=45, a=1〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"haste","t":42,"a":2}` — 強化〔e="haste", t=42, a=2〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"haste","t":48,"a":7}` — 強化〔e="haste", t=48, a=7〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（38命令）**：

01. `{"op":"fx","p":"smoke","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="smoke", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"smoke","n":4,"at":"self","s":0.7}` — 粒子演出〔p="smoke", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"spark","n":50,"at":"self","s":1.0}` — 粒子演出〔p="spark", n=50, at="self", s=1.0〕
04. `{"op":"fx","p":"smoke","n":20,"at":"self"}` — 粒子演出〔p="smoke", n=20, at="self"〕
05. `{"op":"sound","s":"smith","v":1.0,"pi":0.8}` — 効果音〔s="smith", v=1.0, pi=0.8〕
06. `{"op":"fx","p":"end_rod","n":44,"at":"ring","r":10}` — 粒子演出〔p="end_rod", n=44, at="ring", r=10〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"buff","e":"speed","t":300,"a":3}` — 強化〔e="speed", t=300, a=3〕
09. `{"op":"buff","e":"haste","t":300,"a":2}` — 強化〔e="haste", t=300, a=2〕
10. `{"op":"erase","r":24}` — erase〔r=24〕
11. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"haste","t":210,"a":1}` — 強化〔e="haste", t=210, a=1〕
14. `{"op":"fx","p":"smoke","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="smoke", n=46, at="ring", r=5.5, y=0.25〕
15. `{"op":"fx","p":"spark","n":36,"at":"line","r":24}` — 粒子演出〔p="spark", n=36, at="line", r=24〕
16. `{"op":"sound","s":"anvil","v":1.05,"pi":1.14}` — 効果音〔s="anvil", v=1.05, pi=1.14〕
17. `{"op":"self"}` — 対象を自分へ〔〕
18. `{"op":"guard","t":95}` — 防御〔t=95〕
19. `{"op":"self"}` — 対象を自分へ〔〕
20. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
21. `{"op":"cleanse"}` — 状態異常解除〔〕
22. `{"op":"buff","e":"haste","t":180,"a":3}` — 強化〔e="haste", t=180, a=3〕
23. `{"op":"guard","t":95}` — 防御〔t=95〕
24. `{"op":"fx","p":"spark","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="spark", n=30, at="ring", r=4.0, y=0.7〕
25. `{"op":"sound","s":"smith","v":0.8,"pi":1.1}` — 効果音〔s="smith", v=0.8, pi=1.1〕
26. `{"op":"self"}` — 対象を自分へ〔〕
27. `{"op":"buff","e":"haste","t":300,"a":4}` — 強化〔e="haste", t=300, a=4〕
28. `{"op":"guard","t":125}` — 防御〔t=125〕
29. `{"op":"self"}` — 対象を自分へ〔〕
30. `{"op":"repair","v":210}` — 修理〔v=210〕
31. `{"op":"fx","p":"spark","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="spark", n=20, at="ring", r=4, y=0.4〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"buff","e":"haste","t":160,"a":123}` — 強化〔e="haste", t=160, a=123〕
34. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
35. `{"op":"eff","e":"fatigue","t":110,"a":123}` — 敵への状態異常〔e="fatigue", t=110, a=123〕
36. `{"op":"self"}` — 対象を自分へ〔〕
37. `{"op":"repair","v":220}` — 修理〔v=220〕
38. `{"op":"guard","t":80}` — 防御〔t=80〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 文明跳躍・未来工廠 — 超越神器（武器欄） (`ferdinand_legend`)

**現行パラメータ**：rank=3、damage登録値=1323.85714、relics側CD=345tick、art側CD=345tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10、minecraft:quick_charge:4、minecraft:efficiency:125。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"buff","e":"haste","t":40,"a":3}` — 強化〔e="haste", t=40, a=3〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
08. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕
09. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（9命令）**：

01. `{"op":"around","r":5,"n":16,"exclude":1}` — around〔r=5, n=16, exclude=1〕
02. `{"op":"dmg","m":0.4}` — 追加攻撃〔m=0.4〕
03. `{"op":"fx","p":"explosion","n":3,"at":"t"}` — 粒子演出〔p="explosion", n=3, at="t"〕
04. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"glow","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"glow","t":160,"a":1}]〕
05. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"smoke","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"smoke","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
06. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"smoke","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"smoke","n":10,"at":"t","s":0.35}]〕
07. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
08. `{"op":"chance","p":0.375,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":20,"at":"t","s":0.33},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.375, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":20,"at":"t","s":0.33},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":160,"x":2.5}]〕
09. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]〕

**権能発動時の命令（24命令）**：

01. `{"op":"fx","p":"smoke","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="smoke", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"smoke","n":4,"at":"self","s":0.7}` — 粒子演出〔p="smoke", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"spark","n":50,"at":"self","s":1.0}` — 粒子演出〔p="spark", n=50, at="self", s=1.0〕
04. `{"op":"fx","p":"smoke","n":20,"at":"self"}` — 粒子演出〔p="smoke", n=20, at="self"〕
05. `{"op":"sound","s":"smith","v":1.0,"pi":0.8}` — 効果音〔s="smith", v=1.0, pi=0.8〕
06. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
07. `{"op":"lightning"}` — lightning〔〕
08. `{"op":"arrows","n":10,"d":60}` — arrows〔n=10, d=60〕
09. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
10. `{"op":"summon","k":"golem","n":5}` — 召喚〔k="golem", n=5〕
11. `{"op":"give","item":"diamond","n":8}` — give〔item="diamond", n=8〕
12. `{"op":"give","item":"netherite","n":2}` — give〔item="netherite", n=2〕
13. `{"op":"repair","v":99999}` — 修理〔v=99999〕
14. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
15. `{"op":"summon","k":"golem","n":3}` — 召喚〔k="golem", n=3〕
16. `{"op":"repair","n":32}` — 修理〔n=32〕
17. `{"op":"self"}` — 対象を自分へ〔〕
18. `{"op":"buff","e":"haste","a":2,"t":180}` — 強化〔e="haste", a=2, t=180〕
19. `{"op":"fx","p":"spark","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="spark", n=50, at="ring", r=8.0, y=0.6〕
20. `{"op":"fx","p":"blast","n":32,"at":"line","r":30}` — 粒子演出〔p="blast", n=32, at="line", r=30〕
21. `{"op":"sound","s":"anvil","v":1.15,"pi":0.95}` — 効果音〔s="anvil", v=1.15, pi=0.95〕
22. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.ferdinand_legend.stage0","ops":[{"op":"fx","p":"spark","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"smith","v":0.9,"pi":1.2},{"op":"fx","p":"spark","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"smoke","n":6,"at":"line","r":10},{"op":"fx","p":"smoke","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"spark","n":36,"at":"line","r":24},{"op":"sound","s":"anvil","v":1.05,"pi":1.14},{"op":"line","r":55.0,"w":5.0},{"op":"dmg","m":3.915},{"op":"mark","t":130,"x":2.08},{"op":"self"},{"op":"buff","e":"haste","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.ferdinand_legend.stage1","ops":[{"op":"fx","p":"spark","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"smith","v":1.05,"pi":1.0},{"op":"fx","p":"smoke","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"spark","n":6,"at":"line","r":15},{"op":"fx","p":"spark","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"blast","n":32,"at":"line","r":30},{"op":"sound","s":"anvil","v":1.15,"pi":0.95},{"op":"summon","k":"golem","n":4},{"op":"self"},{"op":"repair","n":44},{"op":"guard","t":105},{"op":"area","r":18.0,"n":10},{"op":"eff","e":"fatigue","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.ferdinand_legend.stage2","ops":[{"op":"fx","p":"spark","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"smith","v":1.25,"pi":0.75},{"op":"fx","p":"smoke","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"spark","n":10,"at":"line","r":20},{"op":"fx","p":"smoke","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"spark","n":48,"at":"line","r":48},{"op":"fx","p":"blast","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"anvil","v":1.5,"pi":0.75},{"op":"area","r":34.0,"n":28},{"op":"dmg","m":9.882},{"op":"summon","k":"golem","n":5},{"op":"stun","t":55},{"op":"self"},{"op":"buff","e":"haste","t":180,"a":4},{"op":"fx","p":"blast","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"smoke","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":32.0,"n":28},{"op":"dmg","m":2.7},{"op":"summon","k":"golem","n":3},{"op":"self"},{"op":"buff","e":"haste","t":180,"a":4},{"op":"area","r":21.0,"n":16},{"op":"dmg","m":1.1},{"op":"eff","e":"fatigue","t":160,"a":2},{"op":"self"},{"op":"buff","e":"haste","t":240,"a":4},{"op":"self"},{"op":"summon","k":"golem","n":2},{"op":"fx","p":"spark","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"smith","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"self"},{"op":"repair","v":260},{"op":"area","r":17,"n":9},{"op":"eff","e":"fatigue","t":65,"a":35}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.ferdinand_legend.stage0","ops":[{"op":"fx","p":"spark","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"smith","v":0.9,"pi":1.2},{"op":"fx","p":"spark","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"smoke","n":6,"at":"line","r":10},{"op":"fx","p":"smoke","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"spark","n":36,"at":"line","r":24},{"op":"sound","s":"anvil","v":1.05,"pi":1.14},{"op":"line","r":55.0,"w":5.0},{"op":"dmg","m":3.915},{"op":"mark","t":130,"x":2.08},{"op":"self"},{"op":"buff","e":"haste","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.ferdinand_legend.stage1","ops":[{"op":"fx","p":"spark","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"smith","v":1.05,"pi":1.0},{"op":"fx","p":"smoke","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"spark","n":6,"at":"line","r":15},{"op":"fx","p":"spark","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"blast","n":32,"at":"line","r":30},{"op":"sound","s":"anvil","v":1.15,"pi":0.95},{"op":"summon","k":"golem","n":4},{"op":"self"},{"op":"repair","n":44},{"op":"guard","t":105},{"op":"area","r":18.0,"n":10},{"op":"eff","e":"fatigue","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.ferdinand_legend.stage2","ops":[{"op":"fx","p":"spark","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"smith","v":1.25,"pi":0.75},{"op":"fx","p":"smoke","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"spark","n":10,"at":"line","r":20},{"op":"fx","p":"smoke","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"spark","n":48,"at":"line","r":48},{"op":"fx","p":"blast","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"anvil","v":1.5,"pi":0.75},{"op":"area","r":34.0,"n":28},{"op":"dmg","m":9.882},{"op":"summon","k":"golem","n":5},{"op":"stun","t":55},{"op":"self"},{"op":"buff","e":"haste","t":180,"a":4},{"op":"fx","p":"blast","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"smoke","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":32.0,"n":28},{"op":"dmg","m":2.7},{"op":"summon","k":"golem","n":3},{"op":"self"},{"op":"buff","e":"haste","t":180,"a":4},{"op":"area","r":21.0,"n":16},{"op":"dmg","m":1.1},{"op":"eff","e":"fatigue","t":160,"a":2},{"op":"self"},{"op":"buff","e":"haste","t":240,"a":4},{"op":"self"},{"op":"summon","k":"golem","n":2},{"op":"fx","p":"spark","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"smith","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"self"},{"op":"repair","v":260},{"op":"area","r":17,"n":9},{"op":"eff","e":"fatigue","t":65,"a":35}]}]〕
23. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
24. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 10. 至高武王 メルス

**モブ側の動きの方向性**：球体の圧縮・伸長・薄膜化を武術の重心移動として再現する。。

### 無形流武の水刃 — 討伐武器（メイン／武器欄） (`mels_weapon`)

**現行パラメータ**：rank=1、damage登録値=301.39683、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12。

**装備中の常時命令（5命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":0}` — 強化〔e="resist", t=40, a=0〕
03. `{"op":"buff","e":"speed","t":40,"a":0}` — 強化〔e="speed", t=40, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（10命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"dmg","m":0.15}` — 追加攻撃〔m=0.15〕
03. `{"op":"dmg","m":0.15}` — 追加攻撃〔m=0.15〕
04. `{"op":"stun","t":10}` — 行動停止〔t=10〕
05. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"fatigue","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"fatigue","t":90,"a":0}]〕
06. `{"op":"chance","p":0.54,"ops":[{"op":"victim"},{"op":"fx","p":"splash","n":17,"at":"t","s":0.24},{"op":"mark","t":200,"x":2.21},{"op":"eff","e":"slow","t":91,"a":0}]}` — 抽選〔p=0.54, ops=[{"op":"victim"},{"op":"fx","p":"splash","n":17,"at":"t","s":0.24},{"op":"mark","t":200,"x":2.21},{"op":"eff","e":"slow","t":91,"a":0}]〕
07. `{"op":"chance","p":0.258,"ops":[{"op":"victim"},{"op":"dmg","m":0.34}]}` — 抽選〔p=0.258, ops=[{"op":"victim"},{"op":"dmg","m":0.34}]〕
08. `{"op":"chance","p":0.104,"ops":[{"op":"victim"},{"op":"fx","p":"splash","n":8,"at":"t","s":0.25},{"op":"stun","t":9}]}` — 抽選〔p=0.104, ops=[{"op":"victim"},{"op":"fx","p":"splash","n":8,"at":"t","s":0.25},{"op":"stun","t":9}]〕
09. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"fx","p":"splash","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"fx","p":"splash","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]〕
10. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"splash","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"splash","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]〕

**権能発動時の命令（29命令）**：

01. `{"op":"fx","p":"splash","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="splash", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"splash","n":4,"at":"self","s":0.7}` — 粒子演出〔p="splash", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"splash","n":72,"at":"self","s":1.5}` — 粒子演出〔p="splash", n=72, at="self", s=1.5〕
04. `{"op":"fx","p":"bubble","n":40,"at":"self"}` — 粒子演出〔p="bubble", n=40, at="self"〕
05. `{"op":"sound","s":"chime","v":0.8,"pi":0.5}` — 効果音〔s="chime", v=0.8, pi=0.5〕
06. `{"op":"area","r":10,"n":36}` — 円形対象の取得〔r=10, n=36〕
07. `{"op":"pull","f":1.2}` — pull〔f=1.2〕
08. `{"op":"dmg","m":0.6}` — 追加攻撃〔m=0.6〕
09. `{"op":"dmg","m":0.6}` — 追加攻撃〔m=0.6〕
10. `{"op":"dmg","m":0.6}` — 追加攻撃〔m=0.6〕
11. `{"op":"dmg","m":0.6}` — 追加攻撃〔m=0.6〕
12. `{"op":"stun","t":65}` — 行動停止〔t=65〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"resist","t":200,"a":3}` — 強化〔e="resist", t=200, a=3〕
15. `{"op":"fx","p":"splash","n":12,"at":"t","s":0.5}` — 粒子演出〔p="splash", n=12, at="t", s=0.5〕
16. `{"op":"fx","p":"splash","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="splash", n=46, at="ring", r=5.5, y=0.25〕
17. `{"op":"fx","p":"bubble","n":36,"at":"line","r":24}` — 粒子演出〔p="bubble", n=36, at="line", r=24〕
18. `{"op":"cone","r":11.0,"a":130.0}` — 扇形対象の取得〔r=11.0, a=130.0〕
19. `{"op":"dmg","m":3.0}` — 追加攻撃〔m=3.0〕
20. `{"op":"knock","f":2.3}` — knock〔f=2.3〕
21. `{"op":"fx","p":"splash","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="splash", n=16, at="ring", r=5.0〕
22. `{"op":"sound","s":"sonic","v":0.75,"pi":1.15}` — 効果音〔s="sonic", v=0.75, pi=1.15〕
23. `{"op":"cone","r":11,"a":85}` — 扇形対象の取得〔r=11, a=85〕
24. `{"op":"dmg","m":1.0}` — 追加攻撃〔m=1.0〕
25. `{"op":"eff","e":"slow","t":65,"a":0}` — 敵への状態異常〔e="slow", t=65, a=0〕
26. `{"op":"fx","p":"splash","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="splash", n=24, at="ring", r=4.5, y=0.6〕
27. `{"op":"sound","s":"sonic","v":0.8,"pi":0.8}` — 効果音〔s="sonic", v=0.8, pi=0.8〕
28. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
29. `{"op":"eff","e":"slow","t":32,"a":124}` — 敵への状態異常〔e="slow", t=32, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 百拳の流体核 — 神威触媒（Curios relic_focus） (`mels_focus`)

**現行パラメータ**：rank=2、damage登録値=73.7748、relics側CD=155tick、art側CD=155tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"jump","t":40,"a":2}` — 強化〔e="jump", t=40, a=2〕
03. `{"op":"buff","e":"slowfall","t":40,"a":0}` — 強化〔e="slowfall", t=40, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"speed","t":45,"a":0}` — 強化〔e="speed", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"speed","t":45,"a":2}` — 強化〔e="speed", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"speed","t":42,"a":2}` — 強化〔e="speed", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（42命令）**：

01. `{"op":"fx","p":"splash","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="splash", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"splash","n":6,"at":"self","s":0.7}` — 粒子演出〔p="splash", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"splash","n":72,"at":"self","s":1.5}` — 粒子演出〔p="splash", n=72, at="self", s=1.5〕
04. `{"op":"fx","p":"bubble","n":40,"at":"self"}` — 粒子演出〔p="bubble", n=40, at="self"〕
05. `{"op":"sound","s":"chime","v":0.8,"pi":0.5}` — 効果音〔s="chime", v=0.8, pi=0.5〕
06. `{"op":"area","r":20,"n":36}` — 円形対象の取得〔r=20, n=36〕
07. `{"op":"pull","f":2.5}` — pull〔f=2.5〕
08. `{"op":"stun","t":90}` — 行動停止〔t=90〕
09. `{"op":"eff","e":"slow","t":300,"a":5}` — 敵への状態異常〔e="slow", t=300, a=5〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"guard","t":40}` — 防御〔t=40〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"speed","t":150,"a":1}` — 強化〔e="speed", t=150, a=1〕
15. `{"op":"fx","p":"bubble","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="bubble", n=50, at="ring", r=8.0, y=0.6〕
16. `{"op":"fx","p":"crit","n":32,"at":"line","r":30}` — 粒子演出〔p="crit", n=32, at="line", r=30〕
17. `{"op":"sound","s":"sonic","v":1.15,"pi":0.95}` — 効果音〔s="sonic", v=1.15, pi=0.95〕
18. `{"op":"area","r":12.0,"n":12}` — 円形対象の取得〔r=12.0, n=12〕
19. `{"op":"stun","t":50}` — 行動停止〔t=50〕
20. `{"op":"pull","f":1.7}` — pull〔f=1.7〕
21. `{"op":"dmg","m":2.2}` — 追加攻撃〔m=2.2〕
22. `{"op":"self"}` — 対象を自分へ〔〕
23. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
24. `{"op":"buff","e":"speed","t":150,"a":3}` — 強化〔e="speed", t=150, a=3〕
25. `{"op":"fx","p":"splash","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="splash", n=24, at="ring", r=12, y=0.5〕
26. `{"op":"sound","s":"sonic","v":0.85,"pi":1.18}` — 効果音〔s="sonic", v=0.85, pi=1.18〕
27. `{"op":"cone","r":18.0,"a":95.0}` — 扇形対象の取得〔r=18.0, a=95.0〕
28. `{"op":"dmg","m":0.95}` — 追加攻撃〔m=0.95〕
29. `{"op":"eff","e":"slow","t":120,"a":1}` — 敵への状態異常〔e="slow", t=120, a=1〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"speed","t":200,"a":3}` — 強化〔e="speed", t=200, a=3〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"reflect","t":80,"r":16}` — 反射〔t=80, r=16〕
34. `{"op":"fx","p":"splash","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="splash", n=24, at="ring", r=5.5, y=0.7〕
35. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
36. `{"op":"eff","e":"slow","t":43,"a":123}` — 敵への状態異常〔e="slow", t=43, a=123〕
37. `{"op":"self"}` — 対象を自分へ〔〕
38. `{"op":"buff","e":"speed","t":120,"a":4}` — 強化〔e="speed", t=120, a=4〕
39. `{"op":"fx","p":"splash","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="splash", n=16, at="ring", r=3.7, y=0.55〕
40. `{"op":"cone","r":12,"a":100}` — 扇形対象の取得〔r=12, a=100〕
41. `{"op":"eff","e":"slow","t":60,"a":8}` — 敵への状態異常〔e="slow", t=60, a=8〕
42. `{"op":"knock","f":2.1}` — knock〔f=2.1〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 至硬核の護符 — 神格装飾品（Curios relic_charm） (`mels_charm`)

**現行パラメータ**：rank=1、damage登録値=73.7748、relics側CD=185tick、art側CD=185tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（12命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":1}` — 強化〔e="resist", t=40, a=1〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"speed","t":45,"a":0}` — 強化〔e="speed", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
08. `{"op":"buff","e":"speed","t":45,"a":1}` — 強化〔e="speed", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"speed","t":42,"a":2}` — 強化〔e="speed", t=42, a=2〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"speed","t":48,"a":5}` — 強化〔e="speed", t=48, a=5〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（36命令）**：

01. `{"op":"fx","p":"splash","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="splash", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"splash","n":4,"at":"self","s":0.7}` — 粒子演出〔p="splash", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"splash","n":72,"at":"self","s":1.5}` — 粒子演出〔p="splash", n=72, at="self", s=1.5〕
04. `{"op":"fx","p":"bubble","n":40,"at":"self"}` — 粒子演出〔p="bubble", n=40, at="self"〕
05. `{"op":"sound","s":"chime","v":0.8,"pi":0.5}` — 効果音〔s="chime", v=0.8, pi=0.5〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"guard","t":100}` — 防御〔t=100〕
08. `{"op":"adapt","t":400}` — adapt〔t=400〕
09. `{"op":"buff","e":"resist","t":400,"a":4}` — 強化〔e="resist", t=400, a=4〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"speed","t":210,"a":1}` — 強化〔e="speed", t=210, a=1〕
13. `{"op":"fx","p":"splash","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="splash", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"bubble","n":36,"at":"line","r":24}` — 粒子演出〔p="bubble", n=36, at="line", r=24〕
15. `{"op":"sound","s":"sonic","v":1.05,"pi":1.14}` — 効果音〔s="sonic", v=1.05, pi=1.14〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"guard","t":95}` — 防御〔t=95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
20. `{"op":"cleanse"}` — 状態異常解除〔〕
21. `{"op":"buff","e":"speed","t":180,"a":3}` — 強化〔e="speed", t=180, a=3〕
22. `{"op":"guard","t":95}` — 防御〔t=95〕
23. `{"op":"fx","p":"splash","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="splash", n=30, at="ring", r=4.0, y=0.7〕
24. `{"op":"sound","s":"sonic","v":0.8,"pi":1.1}` — 効果音〔s="sonic", v=0.8, pi=1.1〕
25. `{"op":"self"}` — 対象を自分へ〔〕
26. `{"op":"buff","e":"speed","t":260,"a":4}` — 強化〔e="speed", t=260, a=4〕
27. `{"op":"guard","t":140}` — 防御〔t=140〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"reflect","t":80,"r":16}` — 反射〔t=80, r=16〕
30. `{"op":"fx","p":"splash","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="splash", n=20, at="ring", r=4, y=0.4〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"speed","t":120,"a":4}` — 強化〔e="speed", t=120, a=4〕
33. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
34. `{"op":"eff","e":"slow","t":32,"a":123}` — 敵への状態異常〔e="slow", t=32, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 武理完成・無形万武 — 超越神器（武器欄） (`mels_legend`)

**現行パラメータ**：rank=3、damage登録値=461.2381、relics側CD=340tick、art側CD=340tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"buff","e":"resist","t":40,"a":1}` — 強化〔e="resist", t=40, a=1〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
08. `{"op":"buff","e":"speed","t":45,"a":3}` — 強化〔e="speed", t=45, a=3〕
09. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（12命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"dmg","m":0.3}` — 追加攻撃〔m=0.3〕
03. `{"op":"dmg","m":0.3}` — 追加攻撃〔m=0.3〕
04. `{"op":"dmg","m":0.3}` — 追加攻撃〔m=0.3〕
05. `{"op":"around","r":4,"n":16,"exclude":1}` — around〔r=4, n=16, exclude=1〕
06. `{"op":"dmg","m":0.2}` — 追加攻撃〔m=0.2〕
07. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"fatigue","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"fatigue","t":160,"a":1}]〕
08. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"splash","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"splash","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
09. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"bubble","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"bubble","n":10,"at":"t","s":0.35}]〕
10. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
11. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"fx","p":"splash","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"fx","p":"splash","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]〕
12. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"splash","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"wither","t":78,"a":7}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"splash","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"wither","t":78,"a":7}]〕

**権能発動時の命令（28命令）**：

01. `{"op":"fx","p":"splash","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="splash", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"splash","n":4,"at":"self","s":0.7}` — 粒子演出〔p="splash", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"splash","n":72,"at":"self","s":1.5}` — 粒子演出〔p="splash", n=72, at="self", s=1.5〕
04. `{"op":"fx","p":"bubble","n":40,"at":"self"}` — 粒子演出〔p="bubble", n=40, at="self"〕
05. `{"op":"sound","s":"chime","v":0.8,"pi":0.5}` — 効果音〔s="chime", v=0.8, pi=0.5〕
06. `{"op":"area","r":32,"n":36}` — 円形対象の取得〔r=32, n=36〕
07. `{"op":"pull","f":3.0}` — pull〔f=3.0〕
08. `{"op":"dmg","m":1.12}` — 追加攻撃〔m=1.12〕
09. `{"op":"dmg","m":1.12}` — 追加攻撃〔m=1.12〕
10. `{"op":"dmg","m":1.12}` — 追加攻撃〔m=1.12〕
11. `{"op":"dmg","m":1.12}` — 追加攻撃〔m=1.12〕
12. `{"op":"dmg","m":1.12}` — 追加攻撃〔m=1.12〕
13. `{"op":"dmg","m":1.12}` — 追加攻撃〔m=1.12〕
14. `{"op":"stun","t":105}` — 行動停止〔t=105〕
15. `{"op":"knock","f":4.0}` — knock〔f=4.0〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"guard","t":80}` — 防御〔t=80〕
18. `{"op":"adapt","t":600}` — adapt〔t=600〕
19. `{"op":"fx","p":"splash","n":12,"at":"t","s":0.5}` — 粒子演出〔p="splash", n=12, at="t", s=0.5〕
20. `{"op":"cone","r":12,"a":120}` — 扇形対象の取得〔r=12, a=120〕
21. `{"op":"dmg","m":2.5}` — 追加攻撃〔m=2.5〕
22. `{"op":"slam"}` — slam〔〕
23. `{"op":"fx","p":"bubble","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="bubble", n=50, at="ring", r=8.0, y=0.6〕
24. `{"op":"fx","p":"crit","n":32,"at":"line","r":30}` — 粒子演出〔p="crit", n=32, at="line", r=30〕
25. `{"op":"sound","s":"sonic","v":1.15,"pi":0.95}` — 効果音〔s="sonic", v=1.15, pi=0.95〕
26. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.mels_legend.stage0","ops":[{"op":"fx","p":"splash","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"sonic","v":0.9,"pi":1.2},{"op":"fx","p":"splash","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"crit","n":6,"at":"line","r":10},{"op":"fx","p":"splash","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"bubble","n":36,"at":"line","r":24},{"op":"sound","s":"sonic","v":1.05,"pi":1.14},{"op":"cone","r":11.0,"a":130.0},{"op":"dmg","m":4.05},{"op":"knock","f":2.3},{"op":"self"},{"op":"buff","e":"speed","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.mels_legend.stage1","ops":[{"op":"fx","p":"splash","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"sonic","v":1.05,"pi":1.0},{"op":"fx","p":"crit","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"splash","n":6,"at":"line","r":15},{"op":"fx","p":"bubble","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"crit","n":32,"at":"line","r":30},{"op":"sound","s":"sonic","v":1.15,"pi":0.95},{"op":"area","r":12.0,"n":12},{"op":"stun","t":50},{"op":"pull","f":1.7},{"op":"dmg","m":3.19},{"op":"area","r":20.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.mels_legend.stage2","ops":[{"op":"fx","p":"splash","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"sonic","v":1.25,"pi":0.75},{"op":"fx","p":"crit","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"splash","n":10,"at":"line","r":20},{"op":"fx","p":"splash","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"bubble","n":48,"at":"line","r":48},{"op":"fx","p":"crit","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"sonic","v":1.5,"pi":0.75},{"op":"cone","r":18.0,"a":140.0},{"op":"dmg","m":11.664},{"op":"slam"},{"op":"self"},{"op":"guard","t":130},{"op":"buff","e":"speed","t":145,"a":3},{"op":"fx","p":"crit","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"bubble","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"cone","r":20.0,"a":150.0},{"op":"dmg","m":3.2},{"op":"slam"},{"op":"self"},{"op":"guard","t":110},{"op":"cone","r":24.0,"a":110.0},{"op":"dmg","m":1.2},{"op":"eff","e":"slow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"speed","t":240,"a":4},{"op":"cone","r":16.0,"a":110.0},{"op":"knock","f":2.8},{"op":"fx","p":"splash","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"sonic","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"slow","t":60,"a":8},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.mels_legend.stage0","ops":[{"op":"fx","p":"splash","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"sonic","v":0.9,"pi":1.2},{"op":"fx","p":"splash","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"crit","n":6,"at":"line","r":10},{"op":"fx","p":"splash","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"bubble","n":36,"at":"line","r":24},{"op":"sound","s":"sonic","v":1.05,"pi":1.14},{"op":"cone","r":11.0,"a":130.0},{"op":"dmg","m":4.05},{"op":"knock","f":2.3},{"op":"self"},{"op":"buff","e":"speed","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.mels_legend.stage1","ops":[{"op":"fx","p":"splash","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"sonic","v":1.05,"pi":1.0},{"op":"fx","p":"crit","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"splash","n":6,"at":"line","r":15},{"op":"fx","p":"bubble","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"crit","n":32,"at":"line","r":30},{"op":"sound","s":"sonic","v":1.15,"pi":0.95},{"op":"area","r":12.0,"n":12},{"op":"stun","t":50},{"op":"pull","f":1.7},{"op":"dmg","m":3.19},{"op":"area","r":20.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.mels_legend.stage2","ops":[{"op":"fx","p":"splash","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"sonic","v":1.25,"pi":0.75},{"op":"fx","p":"crit","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"splash","n":10,"at":"line","r":20},{"op":"fx","p":"splash","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"bubble","n":48,"at":"line","r":48},{"op":"fx","p":"crit","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"sonic","v":1.5,"pi":0.75},{"op":"cone","r":18.0,"a":140.0},{"op":"dmg","m":11.664},{"op":"slam"},{"op":"self"},{"op":"guard","t":130},{"op":"buff","e":"speed","t":145,"a":3},{"op":"fx","p":"crit","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"bubble","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"cone","r":20.0,"a":150.0},{"op":"dmg","m":3.2},{"op":"slam"},{"op":"self"},{"op":"guard","t":110},{"op":"cone","r":24.0,"a":110.0},{"op":"dmg","m":1.2},{"op":"eff","e":"slow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"speed","t":240,"a":4},{"op":"cone","r":16.0,"a":110.0},{"op":"knock","f":2.8},{"op":"fx","p":"splash","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"sonic","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"slow","t":60,"a":8},{"op":"mark","t":135,"x":1.8}]}]〕
27. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
28. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 11. 典域工廠 ヘファイストス

**モブ側の動きの方向性**：球殻の開閉と砲身、工作腕、炉心の機械駆動を段階表示する。。

### 概念加工の切削槍 — 討伐武器（メイン／武器欄） (`hephaistos_weapon`)

**現行パラメータ**：rank=1、damage登録値=296.0、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:efficiency:125。

**装備中の常時命令（4命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"repair","v":6}` — 修理〔v=6〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（9命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"strip"}` — 強化解除〔〕
03. `{"op":"dmg","m":1.8,"magic":1}` — 追加攻撃〔m=1.8, magic=1〕
04. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"fatigue","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"fatigue","t":90,"a":0}]〕
05. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":9,"at":"t","s":0.24},{"op":"mark","t":120,"x":1.65},{"op":"eff","e":"weakness","t":103,"a":1}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":9,"at":"t","s":0.24},{"op":"mark","t":120,"x":1.65},{"op":"eff","e":"weakness","t":103,"a":1}]〕
06. `{"op":"chance","p":0.15,"ops":[{"op":"victim"},{"op":"dmg","m":0.2}]}` — 抽選〔p=0.15, ops=[{"op":"victim"},{"op":"dmg","m":0.2}]〕
07. `{"op":"chance","p":0.123,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":8,"at":"t","s":0.25},{"op":"strip"}]}` — 抽選〔p=0.123, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":8,"at":"t","s":0.25},{"op":"strip"}]〕
08. `{"op":"chance","p":0.18,"ops":[{"op":"victim"},{"op":"fx","p":"lava","n":14,"at":"t","s":0.28},{"op":"eff","e":"fatigue","t":110,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.18, ops=[{"op":"victim"},{"op":"fx","p":"lava","n":14,"at":"t","s":0.28},{"op":"eff","e":"fatigue","t":110,"a":124},{"op":"mark","t":100,"x":2.15}]〕
09. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]〕

**権能発動時の命令（26命令）**：

01. `{"op":"fx","p":"spark","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="spark", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"spark","n":4,"at":"self","s":0.7}` — 粒子演出〔p="spark", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"spark","n":50,"at":"self","s":1.0}` — 粒子演出〔p="spark", n=50, at="self", s=1.0〕
04. `{"op":"fx","p":"smoke","n":20,"at":"self"}` — 粒子演出〔p="smoke", n=20, at="self"〕
05. `{"op":"sound","s":"smith","v":1.0,"pi":0.8}` — 効果音〔s="smith", v=1.0, pi=0.8〕
06. `{"op":"line","r":24,"w":2.5}` — 線分対象の取得〔r=24, w=2.5〕
07. `{"op":"dmg","m":1.92}` — 追加攻撃〔m=1.92〕
08. `{"op":"strip"}` — 強化解除〔〕
09. `{"op":"disarm"}` — disarm〔〕
10. `{"op":"dmg","m":2.16,"magic":1}` — 追加攻撃〔m=2.16, magic=1〕
11. `{"op":"fx","p":"crit","n":40,"at":"line","r":24}` — 粒子演出〔p="crit", n=40, at="line", r=24〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"fx","p":"lava","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="lava", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"spark","n":36,"at":"line","r":24}` — 粒子演出〔p="spark", n=36, at="line", r=24〕
15. `{"op":"line","r":62.0,"w":5.0}` — 線分対象の取得〔r=62.0, w=5.0〕
16. `{"op":"dmg","m":3.1}` — 追加攻撃〔m=3.1〕
17. `{"op":"stun","t":25}` — 行動停止〔t=25〕
18. `{"op":"fx","p":"spark","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="spark", n=16, at="ring", r=5.0〕
19. `{"op":"sound","s":"sonic","v":0.75,"pi":1.15}` — 効果音〔s="sonic", v=0.75, pi=1.15〕
20. `{"op":"line","r":18,"w":2}` — 線分対象の取得〔r=18, w=2〕
21. `{"op":"dmg","m":1.05}` — 追加攻撃〔m=1.05〕
22. `{"op":"eff","e":"weakness","t":65,"a":0}` — 敵への状態異常〔e="weakness", t=65, a=0〕
23. `{"op":"fx","p":"lava","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="lava", n=24, at="ring", r=4.5, y=0.6〕
24. `{"op":"sound","s":"anvil","v":0.8,"pi":0.8}` — 効果音〔s="anvil", v=0.8, pi=0.8〕
25. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
26. `{"op":"eff","e":"fatigue","t":110,"a":124}` — 敵への状態異常〔e="fatigue", t=110, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 分散工廠キューブ — 神威触媒（Curios relic_focus） (`hephaistos_focus`)

**現行パラメータ**：rank=2、damage登録値=69.6762、relics側CD=150tick、art側CD=150tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"repair","v":12}` — 修理〔v=12〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"resist","t":45,"a":0}` — 強化〔e="resist", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"haste","t":42,"a":2}` — 強化〔e="haste", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（42命令）**：

01. `{"op":"fx","p":"spark","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="spark", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"spark","n":6,"at":"self","s":0.7}` — 粒子演出〔p="spark", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"spark","n":50,"at":"self","s":1.0}` — 粒子演出〔p="spark", n=50, at="self", s=1.0〕
04. `{"op":"fx","p":"smoke","n":20,"at":"self"}` — 粒子演出〔p="smoke", n=20, at="self"〕
05. `{"op":"sound","s":"smith","v":1.0,"pi":0.8}` — 効果音〔s="smith", v=1.0, pi=0.8〕
06. `{"op":"summon","k":"golem","n":4}` — 召喚〔k="golem", n=4〕
07. `{"op":"give","item":"netherite","n":1}` — give〔item="netherite", n=1〕
08. `{"op":"give","item":"diamond","n":4}` — give〔item="diamond", n=4〕
09. `{"op":"repair","v":4096}` — 修理〔v=4096〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"absorb","t":600,"a":6}` — 強化〔e="absorb", t=600, a=6〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"resist","t":150,"a":1}` — 強化〔e="resist", t=150, a=1〕
15. `{"op":"fx","p":"spark","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="spark", n=50, at="ring", r=8.0, y=0.6〕
16. `{"op":"fx","p":"smoke","n":32,"at":"line","r":30}` — 粒子演出〔p="smoke", n=32, at="line", r=30〕
17. `{"op":"sound","s":"anvil","v":1.15,"pi":0.95}` — 効果音〔s="anvil", v=1.15, pi=0.95〕
18. `{"op":"summon","k":"golem","n":4}` — 召喚〔k="golem", n=4〕
19. `{"op":"self"}` — 対象を自分へ〔〕
20. `{"op":"repair","n":60}` — 修理〔n=60〕
21. `{"op":"guard","t":90}` — 防御〔t=90〕
22. `{"op":"self"}` — 対象を自分へ〔〕
23. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
24. `{"op":"buff","e":"resist","t":150,"a":3}` — 強化〔e="resist", t=150, a=3〕
25. `{"op":"fx","p":"lava","n":24,"at":"ring","r":10,"y":0.5}` — 粒子演出〔p="lava", n=24, at="ring", r=10, y=0.5〕
26. `{"op":"sound","s":"anvil","v":0.85,"pi":0.9}` — 効果音〔s="anvil", v=0.85, pi=0.9〕
27. `{"op":"area","r":10.0,"n":12}` — 円形対象の取得〔r=10.0, n=12〕
28. `{"op":"dmg","m":0.8}` — 追加攻撃〔m=0.8〕
29. `{"op":"eff","e":"fatigue","t":140,"a":1}` — 敵への状態異常〔e="fatigue", t=140, a=1〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"haste","t":220,"a":3}` — 強化〔e="haste", t=220, a=3〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"summon","k":"golem","n":1}` — 召喚〔k="golem", n=1〕
34. `{"op":"fx","p":"lava","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="lava", n=24, at="ring", r=5.5, y=0.7〕
35. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
36. `{"op":"eff","e":"fatigue","t":148,"a":123}` — 敵への状態異常〔e="fatigue", t=148, a=123〕
37. `{"op":"self"}` — 対象を自分へ〔〕
38. `{"op":"buff","e":"haste","t":100,"a":123}` — 強化〔e="haste", t=100, a=123〕
39. `{"op":"fx","p":"spark","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="spark", n=16, at="ring", r=3.7, y=0.55〕
40. `{"op":"self"}` — 対象を自分へ〔〕
41. `{"op":"repair","v":180}` — 修理〔v=180〕
42. `{"op":"buff","e":"haste","t":170,"a":6}` — 強化〔e="haste", t=170, a=6〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 自己複製の演算環 — 神格装飾品（Curios relic_charm） (`hephaistos_charm`)

**現行パラメータ**：rank=1、damage登録値=69.6762、relics側CD=180tick、art側CD=180tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（12命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"adapt","t":40}` — adapt〔t=40〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"resist","t":45,"a":0}` — 強化〔e="resist", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
08. `{"op":"buff","e":"resist","t":45,"a":1}` — 強化〔e="resist", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"haste","t":42,"a":2}` — 強化〔e="haste", t=42, a=2〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"haste","t":48,"a":7}` — 強化〔e="haste", t=48, a=7〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（37命令）**：

01. `{"op":"fx","p":"spark","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="spark", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"spark","n":4,"at":"self","s":0.7}` — 粒子演出〔p="spark", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"spark","n":50,"at":"self","s":1.0}` — 粒子演出〔p="spark", n=50, at="self", s=1.0〕
04. `{"op":"fx","p":"smoke","n":20,"at":"self"}` — 粒子演出〔p="smoke", n=20, at="self"〕
05. `{"op":"sound","s":"smith","v":1.0,"pi":0.8}` — 効果音〔s="smith", v=1.0, pi=0.8〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"adapt","t":600}` — adapt〔t=600〕
08. `{"op":"guard","t":60}` — 防御〔t=60〕
09. `{"op":"buff","e":"resist","t":400,"a":4}` — 強化〔e="resist", t=400, a=4〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"resist","t":210,"a":1}` — 強化〔e="resist", t=210, a=1〕
13. `{"op":"fx","p":"lava","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="lava", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"spark","n":36,"at":"line","r":24}` — 粒子演出〔p="spark", n=36, at="line", r=24〕
15. `{"op":"sound","s":"anvil","v":1.05,"pi":1.14}` — 効果音〔s="anvil", v=1.05, pi=1.14〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"guard","t":95}` — 防御〔t=95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
20. `{"op":"cleanse"}` — 状態異常解除〔〕
21. `{"op":"buff","e":"resist","t":180,"a":3}` — 強化〔e="resist", t=180, a=3〕
22. `{"op":"guard","t":95}` — 防御〔t=95〕
23. `{"op":"fx","p":"lava","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="lava", n=30, at="ring", r=4.0, y=0.7〕
24. `{"op":"sound","s":"anvil","v":0.8,"pi":1.1}` — 効果音〔s="anvil", v=0.8, pi=1.1〕
25. `{"op":"self"}` — 対象を自分へ〔〕
26. `{"op":"buff","e":"haste","t":280,"a":4}` — 強化〔e="haste", t=280, a=4〕
27. `{"op":"guard","t":155}` — 防御〔t=155〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"repair","v":120}` — 修理〔v=120〕
30. `{"op":"fx","p":"lava","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="lava", n=20, at="ring", r=4, y=0.4〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"haste","t":160,"a":123}` — 強化〔e="haste", t=160, a=123〕
33. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
34. `{"op":"eff","e":"fatigue","t":110,"a":123}` — 敵への状態異常〔e="fatigue", t=110, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"repair","v":220}` — 修理〔v=220〕
37. `{"op":"guard","t":80}` — 防御〔t=80〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 製造神格・無限工廠 — 超越神器（武器欄） (`hephaistos_legend`)

**現行パラメータ**：rank=3、damage登録値=461.2381、relics側CD=335tick、art側CD=335tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:efficiency:125。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"adapt","t":40}` — adapt〔t=40〕
06. `{"op":"repair","v":64}` — 修理〔v=64〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
09. `{"op":"buff","e":"resist","t":45,"a":3}` — 強化〔e="resist", t=45, a=3〕
10. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（8命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"dmg","m":5.0,"magic":1}` — 追加攻撃〔m=5.0, magic=1〕
03. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"fatigue","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"fatigue","t":160,"a":1}]〕
04. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"lava","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"lava","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
05. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"spark","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"spark","n":10,"at":"t","s":0.35}]〕
06. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
07. `{"op":"chance","p":0.3,"ops":[{"op":"victim"},{"op":"fx","p":"lava","n":20,"at":"t","s":0.33},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.3, ops=[{"op":"victim"},{"op":"fx","p":"lava","n":20,"at":"t","s":0.33},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":160,"x":2.5}]〕
08. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]〕

**権能発動時の命令（27命令）**：

01. `{"op":"fx","p":"spark","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="spark", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"spark","n":4,"at":"self","s":0.7}` — 粒子演出〔p="spark", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"spark","n":50,"at":"self","s":1.0}` — 粒子演出〔p="spark", n=50, at="self", s=1.0〕
04. `{"op":"fx","p":"smoke","n":20,"at":"self"}` — 粒子演出〔p="smoke", n=20, at="self"〕
05. `{"op":"sound","s":"smith","v":1.0,"pi":0.8}` — 効果音〔s="smith", v=1.0, pi=0.8〕
06. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
07. `{"op":"dmg","m":3.36}` — 追加攻撃〔m=3.36〕
08. `{"op":"disarm"}` — disarm〔〕
09. `{"op":"dmg","m":5.6,"magic":1}` — 追加攻撃〔m=5.6, magic=1〕
10. `{"op":"stun","t":105}` — 行動停止〔t=105〕
11. `{"op":"summon","k":"golem","n":5}` — 召喚〔k="golem", n=5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"undying","t":180}` — 死亡防護〔t=180〕
14. `{"op":"adapt","t":1200}` — adapt〔t=1200〕
15. `{"op":"give","item":"netherite","n":4}` — give〔item="netherite", n=4〕
16. `{"op":"repair","v":99999}` — 修理〔v=99999〕
17. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
18. `{"op":"summon","k":"golem","n":3}` — 召喚〔k="golem", n=3〕
19. `{"op":"repair","n":32}` — 修理〔n=32〕
20. `{"op":"self"}` — 対象を自分へ〔〕
21. `{"op":"buff","e":"haste","a":2,"t":180}` — 強化〔e="haste", a=2, t=180〕
22. `{"op":"fx","p":"spark","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="spark", n=50, at="ring", r=8.0, y=0.6〕
23. `{"op":"fx","p":"smoke","n":32,"at":"line","r":30}` — 粒子演出〔p="smoke", n=32, at="line", r=30〕
24. `{"op":"sound","s":"anvil","v":1.15,"pi":0.95}` — 効果音〔s="anvil", v=1.15, pi=0.95〕
25. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.hephaistos_legend.stage0","ops":[{"op":"fx","p":"lava","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"anvil","v":0.9,"pi":1.2},{"op":"fx","p":"spark","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"lava","n":6,"at":"line","r":10},{"op":"fx","p":"lava","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"spark","n":36,"at":"line","r":24},{"op":"sound","s":"anvil","v":1.05,"pi":1.14},{"op":"line","r":62.0,"w":5.0},{"op":"dmg","m":4.185},{"op":"stun","t":25},{"op":"self"},{"op":"buff","e":"haste","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.hephaistos_legend.stage1","ops":[{"op":"fx","p":"lava","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"anvil","v":1.05,"pi":1.0},{"op":"fx","p":"lava","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"spark","n":6,"at":"line","r":15},{"op":"fx","p":"spark","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"smoke","n":32,"at":"line","r":30},{"op":"sound","s":"anvil","v":1.15,"pi":0.95},{"op":"summon","k":"golem","n":4},{"op":"self"},{"op":"repair","n":60},{"op":"guard","t":90},{"op":"area","r":12.0,"n":10},{"op":"eff","e":"fatigue","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.hephaistos_legend.stage2","ops":[{"op":"fx","p":"lava","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"anvil","v":1.25,"pi":0.75},{"op":"fx","p":"lava","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"spark","n":10,"at":"line","r":20},{"op":"fx","p":"lava","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"spark","n":48,"at":"line","r":48},{"op":"fx","p":"smoke","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"anvil","v":1.5,"pi":0.75},{"op":"area","r":38.0,"n":30},{"op":"dmg","m":10.044},{"op":"summon","k":"golem","n":5},{"op":"stun","t":55},{"op":"self"},{"op":"buff","e":"resist","t":180,"a":3},{"op":"fx","p":"smoke","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"spark","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":35.0,"n":30},{"op":"dmg","m":2.9},{"op":"summon","k":"golem","n":3},{"op":"self"},{"op":"repair","n":80},{"op":"area","r":27.0,"n":16},{"op":"dmg","m":0.8},{"op":"eff","e":"fatigue","t":160,"a":2},{"op":"self"},{"op":"buff","e":"haste","t":240,"a":4},{"op":"self"},{"op":"summon","k":"golem","n":2},{"op":"fx","p":"lava","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"anvil","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"self"},{"op":"repair","v":260},{"op":"area","r":17,"n":9},{"op":"eff","e":"fatigue","t":65,"a":45}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.hephaistos_legend.stage0","ops":[{"op":"fx","p":"lava","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"anvil","v":0.9,"pi":1.2},{"op":"fx","p":"spark","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"lava","n":6,"at":"line","r":10},{"op":"fx","p":"lava","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"spark","n":36,"at":"line","r":24},{"op":"sound","s":"anvil","v":1.05,"pi":1.14},{"op":"line","r":62.0,"w":5.0},{"op":"dmg","m":4.185},{"op":"stun","t":25},{"op":"self"},{"op":"buff","e":"haste","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.hephaistos_legend.stage1","ops":[{"op":"fx","p":"lava","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"anvil","v":1.05,"pi":1.0},{"op":"fx","p":"lava","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"spark","n":6,"at":"line","r":15},{"op":"fx","p":"spark","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"smoke","n":32,"at":"line","r":30},{"op":"sound","s":"anvil","v":1.15,"pi":0.95},{"op":"summon","k":"golem","n":4},{"op":"self"},{"op":"repair","n":60},{"op":"guard","t":90},{"op":"area","r":12.0,"n":10},{"op":"eff","e":"fatigue","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.hephaistos_legend.stage2","ops":[{"op":"fx","p":"lava","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"anvil","v":1.25,"pi":0.75},{"op":"fx","p":"lava","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"spark","n":10,"at":"line","r":20},{"op":"fx","p":"lava","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"spark","n":48,"at":"line","r":48},{"op":"fx","p":"smoke","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"anvil","v":1.5,"pi":0.75},{"op":"area","r":38.0,"n":30},{"op":"dmg","m":10.044},{"op":"summon","k":"golem","n":5},{"op":"stun","t":55},{"op":"self"},{"op":"buff","e":"resist","t":180,"a":3},{"op":"fx","p":"smoke","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"spark","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":35.0,"n":30},{"op":"dmg","m":2.9},{"op":"summon","k":"golem","n":3},{"op":"self"},{"op":"repair","n":80},{"op":"area","r":27.0,"n":16},{"op":"dmg","m":0.8},{"op":"eff","e":"fatigue","t":160,"a":2},{"op":"self"},{"op":"buff","e":"haste","t":240,"a":4},{"op":"self"},{"op":"summon","k":"golem","n":2},{"op":"fx","p":"lava","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"anvil","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"self"},{"op":"repair","v":260},{"op":"area","r":17,"n":9},{"op":"eff","e":"fatigue","t":65,"a":45}]}]〕
26. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
27. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 12. 無法遊戯 ノルティア

**モブ側の動きの方向性**：拍手、跳躍、指差し、玩具投げをリズミカルに行う。。

### 無法遊戯のピコピコハンマー — 討伐武器（メイン／武器欄） (`nortia_weapon`)

**現行パラメータ**：rank=1、damage登録値=333.14286、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:knockback:5。

**装備中の常時命令（5命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"luck","t":40,"a":3}` — 強化〔e="luck", t=40, a=3〕
03. `{"op":"buff","e":"jump","t":40,"a":1}` — 強化〔e="jump", t=40, a=1〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（9命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"launch","f":1.0}` — launch〔f=1.0〕
03. `{"op":"eff","e":"levitate","t":20,"a":2}` — 敵への状態異常〔e="levitate", t=20, a=2〕
04. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"slow","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"slow","t":90,"a":0}]〕
05. `{"op":"chance","p":0.465,"ops":[{"op":"victim"},{"op":"fx","p":"firework","n":11,"at":"t","s":0.24},{"op":"mark","t":140,"x":1.79},{"op":"eff","e":"levitate","t":28,"a":0}]}` — 抽選〔p=0.465, ops=[{"op":"victim"},{"op":"fx","p":"firework","n":11,"at":"t","s":0.24},{"op":"mark","t":140,"x":1.79},{"op":"eff","e":"levitate","t":28,"a":0}]〕
06. `{"op":"chance","p":0.177,"ops":[{"op":"victim"},{"op":"dmg","m":0.235}]}` — 抽選〔p=0.177, ops=[{"op":"victim"},{"op":"dmg","m":0.235}]〕
07. `{"op":"chance","p":0.142,"ops":[{"op":"victim"},{"op":"fx","p":"firework","n":8,"at":"t","s":0.25},{"op":"launch","f":0.24}]}` — 抽選〔p=0.142, ops=[{"op":"victim"},{"op":"fx","p":"firework","n":8,"at":"t","s":0.25},{"op":"launch","f":0.24}]〕
08. `{"op":"chance","p":0.2,"ops":[{"op":"victim"},{"op":"fx","p":"firework","n":14,"at":"t","s":0.28},{"op":"eff","e":"fatigue","t":110,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.2, ops=[{"op":"victim"},{"op":"fx","p":"firework","n":14,"at":"t","s":0.28},{"op":"eff","e":"fatigue","t":110,"a":124},{"op":"mark","t":100,"x":2.15}]〕
09. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"firework","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"firework","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]〕

**権能発動時の命令（29命令）**：

01. `{"op":"fx","p":"firework","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="firework", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"firework","n":4,"at":"self","s":0.7}` — 粒子演出〔p="firework", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"firework","n":40,"at":"self"}` — 粒子演出〔p="firework", n=40, at="self"〕
04. `{"op":"fx","p":"heart","n":8,"at":"self"}` — 粒子演出〔p="heart", n=8, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":2.0}` — 効果音〔s="chime", v=1.0, pi=2.0〕
06. `{"op":"area","r":16,"n":36}` — 円形対象の取得〔r=16, n=36〕
07. `{"op":"dmg","m":1.44}` — 追加攻撃〔m=1.44〕
08. `{"op":"stun","t":65}` — 行動停止〔t=65〕
09. `{"op":"launch","f":1.2}` — launch〔f=1.2〕
10. `{"op":"eff","e":"levitate","t":60,"a":1}` — 敵への状態異常〔e="levitate", t=60, a=1〕
11. `{"op":"eff","e":"nausea","t":160,"a":0}` — 敵への状態異常〔e="nausea", t=160, a=0〕
12. `{"op":"allies","r":16}` — 味方対象〔r=16〕
13. `{"op":"heal","v":12,"to":1}` — heal〔v=12, to=1〕
14. `{"op":"say","k":"relic_art.oror_supreme_bosses.nortia_weapon.say0"}` — say〔k="relic_art.oror_supreme_bosses.nortia_weapon.say0"〕
15. `{"op":"fx","p":"heart","n":12,"at":"t","s":0.5}` — 粒子演出〔p="heart", n=12, at="t", s=0.5〕
16. `{"op":"fx","p":"happy","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="happy", n=46, at="ring", r=5.5, y=0.25〕
17. `{"op":"fx","p":"firework","n":36,"at":"line","r":24}` — 粒子演出〔p="firework", n=36, at="line", r=24〕
18. `{"op":"area","r":23.0,"n":17}` — 円形対象の取得〔r=23.0, n=17〕
19. `{"op":"stun","t":40}` — 行動停止〔t=40〕
20. `{"op":"eff","e":"glow","t":120,"a":0}` — 敵への状態異常〔e="glow", t=120, a=0〕
21. `{"op":"fx","p":"firework","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="firework", n=16, at="ring", r=5.0〕
22. `{"op":"sound","s":"spell","v":0.75,"pi":1.15}` — 効果音〔s="spell", v=0.75, pi=1.15〕
23. `{"op":"area","r":9,"n":8}` — 円形対象の取得〔r=9, n=8〕
24. `{"op":"dmg","m":0.9}` — 追加攻撃〔m=0.9〕
25. `{"op":"eff","e":"levitate","t":65,"a":0}` — 敵への状態異常〔e="levitate", t=65, a=0〕
26. `{"op":"fx","p":"firework","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="firework", n=24, at="ring", r=4.5, y=0.6〕
27. `{"op":"sound","s":"chime","v":0.8,"pi":0.8}` — 効果音〔s="chime", v=0.8, pi=0.8〕
28. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
29. `{"op":"eff","e":"fatigue","t":110,"a":124}` — 敵への状態異常〔e="fatigue", t=110, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 無法盤面の骰子 — 神威触媒（Curios relic_focus） (`nortia_focus`)

**現行パラメータ**：rank=2、damage登録値=68.31、relics側CD=145tick、art側CD=145tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"luck","t":40,"a":4}` — 強化〔e="luck", t=40, a=4〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"jump","t":45,"a":0}` — 強化〔e="jump", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"luck","t":45,"a":2}` — 強化〔e="luck", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"luck","t":42,"a":2}` — 強化〔e="luck", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（37命令）**：

01. `{"op":"fx","p":"firework","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="firework", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"firework","n":6,"at":"self","s":0.7}` — 粒子演出〔p="firework", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"firework","n":40,"at":"self"}` — 粒子演出〔p="firework", n=40, at="self"〕
04. `{"op":"fx","p":"heart","n":8,"at":"self"}` — 粒子演出〔p="heart", n=8, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":2.0}` — 効果音〔s="chime", v=1.0, pi=2.0〕
06. `{"op":"chance","p":0.5,"ops":[{"op":"area","r":24,"n":36},{"op":"dmg","m":2.5},{"op":"stun","t":90},{"op":"fx","p":"firework","n":30,"at":"t"}],"else":[{"op":"allies","r":24},{"op":"healpct","v":0.4,"to":1},{"op":"buff","e":"strength","t":600,"a":4,"to":1}]}` — 抽選〔p=0.5, ops=[{"op":"area","r":24,"n":36},{"op":"dmg","m":2.5},{"op":"stun","t":90},{"op":"fx","p":"firework","n":30,"at":"t"}], else=[{"op":"allies","r":24},{"op":"healpct","v":0.4,"to":1},{"op":"buff","e":"strength","t":600,"a":4,"to":1}]〕
07. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"jump","t":150,"a":1}` — 強化〔e="jump", t=150, a=1〕
10. `{"op":"fx","p":"firework","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="firework", n=50, at="ring", r=8.0, y=0.6〕
11. `{"op":"fx","p":"compost","n":32,"at":"line","r":30}` — 粒子演出〔p="compost", n=32, at="line", r=30〕
12. `{"op":"sound","s":"totem","v":1.15,"pi":0.95}` — 効果音〔s="totem", v=1.15, pi=0.95〕
13. `{"op":"area","r":25.0,"n":22}` — 円形対象の取得〔r=25.0, n=22〕
14. `{"op":"launch","f":1.3}` — launch〔f=1.3〕
15. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
16. `{"op":"eff","e":"slow","t":85,"a":1}` — 敵への状態異常〔e="slow", t=85, a=1〕
17. `{"op":"self"}` — 対象を自分へ〔〕
18. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
19. `{"op":"buff","e":"luck","t":150,"a":3}` — 強化〔e="luck", t=150, a=3〕
20. `{"op":"fx","p":"firework","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="firework", n=24, at="ring", r=12, y=0.5〕
21. `{"op":"sound","s":"chime","v":0.85,"pi":0.97}` — 効果音〔s="chime", v=0.85, pi=0.97〕
22. `{"op":"area","r":12.0,"n":12}` — 円形対象の取得〔r=12.0, n=12〕
23. `{"op":"dmg","m":0.8}` — 追加攻撃〔m=0.8〕
24. `{"op":"eff","e":"levitate","t":160,"a":1}` — 敵への状態異常〔e="levitate", t=160, a=1〕
25. `{"op":"self"}` — 対象を自分へ〔〕
26. `{"op":"buff","e":"luck","t":240,"a":3}` — 強化〔e="luck", t=240, a=3〕
27. `{"op":"area","r":20,"n":6}` — 円形対象の取得〔r=20, n=6〕
28. `{"op":"launch","f":1.4}` — launch〔f=1.4〕
29. `{"op":"fx","p":"firework","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="firework", n=24, at="ring", r=5.5, y=0.7〕
30. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
31. `{"op":"eff","e":"fatigue","t":148,"a":123}` — 敵への状態異常〔e="fatigue", t=148, a=123〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"buff","e":"luck","t":100,"a":123}` — 強化〔e="luck", t=100, a=123〕
34. `{"op":"fx","p":"firework","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="firework", n=16, at="ring", r=3.7, y=0.55〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"guard","t":90}` — 防御〔t=90〕
37. `{"op":"buff","e":"luck","t":160,"a":5}` — 強化〔e="luck", t=160, a=5〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 無限リトライの札 — 神格装飾品（Curios relic_charm） (`nortia_charm`)

**現行パラメータ**：rank=1、damage登録値=68.31、relics側CD=175tick、art側CD=175tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（13命令）**：

01. `{"op":"snapshot"}` — 状態保存〔〕
02. `{"op":"self"}` — 対象を自分へ〔〕
03. `{"op":"buff","e":"luck","t":40,"a":1}` — 強化〔e="luck", t=40, a=1〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"jump","t":45,"a":0}` — 強化〔e="jump", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
09. `{"op":"buff","e":"luck","t":45,"a":1}` — 強化〔e="luck", t=45, a=1〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"luck","t":42,"a":2}` — 強化〔e="luck", t=42, a=2〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"luck","t":48,"a":8}` — 強化〔e="luck", t=48, a=8〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（36命令）**：

01. `{"op":"fx","p":"firework","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="firework", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"firework","n":4,"at":"self","s":0.7}` — 粒子演出〔p="firework", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"firework","n":40,"at":"self"}` — 粒子演出〔p="firework", n=40, at="self"〕
04. `{"op":"fx","p":"heart","n":8,"at":"self"}` — 粒子演出〔p="heart", n=8, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":2.0}` — 効果音〔s="chime", v=1.0, pi=2.0〕
06. `{"op":"rewind"}` — 復元〔〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"guard","t":40}` — 防御〔t=40〕
09. `{"op":"cleanse"}` — 状態異常解除〔〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"jump","t":210,"a":1}` — 強化〔e="jump", t=210, a=1〕
13. `{"op":"fx","p":"happy","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="happy", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"firework","n":36,"at":"line","r":24}` — 粒子演出〔p="firework", n=36, at="line", r=24〕
15. `{"op":"sound","s":"totem","v":1.05,"pi":1.14}` — 効果音〔s="totem", v=1.05, pi=1.14〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"guard","t":95}` — 防御〔t=95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
20. `{"op":"cleanse"}` — 状態異常解除〔〕
21. `{"op":"buff","e":"luck","t":180,"a":3}` — 強化〔e="luck", t=180, a=3〕
22. `{"op":"guard","t":95}` — 防御〔t=95〕
23. `{"op":"fx","p":"firework","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="firework", n=30, at="ring", r=4.0, y=0.7〕
24. `{"op":"sound","s":"chime","v":0.8,"pi":1.1}` — 効果音〔s="chime", v=0.8, pi=1.1〕
25. `{"op":"self"}` — 対象を自分へ〔〕
26. `{"op":"buff","e":"luck","t":300,"a":4}` — 強化〔e="luck", t=300, a=4〕
27. `{"op":"guard","t":170}` — 防御〔t=170〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"buff","e":"luck","t":240,"a":2}` — 強化〔e="luck", t=240, a=2〕
30. `{"op":"fx","p":"firework","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="firework", n=20, at="ring", r=4, y=0.4〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"luck","t":160,"a":123}` — 強化〔e="luck", t=160, a=123〕
33. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
34. `{"op":"eff","e":"fatigue","t":110,"a":123}` — 敵への状態異常〔e="fatigue", t=110, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 世界遊戯・絶対ルール — 超越神器（武器欄） (`nortia_legend`)

**現行パラメータ**：rank=3、damage登録値=659.92857、relics側CD=330tick、art側CD=330tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:knockback:5。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"snapshot"}` — 状態保存〔〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
08. `{"op":"buff","e":"luck","t":45,"a":3}` — 強化〔e="luck", t=45, a=3〕
09. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（9命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"launch","f":1.4}` — launch〔f=1.4〕
03. `{"op":"stun","t":30}` — 行動停止〔t=30〕
04. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"slow","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"slow","t":160,"a":1}]〕
05. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"happy","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"happy","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
06. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"levitate","t":135,"a":2},{"op":"fx","p":"happy","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"levitate","t":135,"a":2},{"op":"fx","p":"happy","n":10,"at":"t","s":0.35}]〕
07. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
08. `{"op":"chance","p":0.325,"ops":[{"op":"victim"},{"op":"fx","p":"firework","n":20,"at":"t","s":0.33},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.325, ops=[{"op":"victim"},{"op":"fx","p":"firework","n":20,"at":"t","s":0.33},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":160,"x":2.5}]〕
09. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"firework","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"firework","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]〕

**権能発動時の命令（23命令）**：

01. `{"op":"fx","p":"firework","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="firework", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"firework","n":4,"at":"self","s":0.7}` — 粒子演出〔p="firework", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"firework","n":40,"at":"self"}` — 粒子演出〔p="firework", n=40, at="self"〕
04. `{"op":"fx","p":"heart","n":8,"at":"self"}` — 粒子演出〔p="heart", n=8, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":2.0}` — 効果音〔s="chime", v=1.0, pi=2.0〕
06. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
07. `{"op":"stun","t":105}` — 行動停止〔t=105〕
08. `{"op":"eff","e":"levitate","t":200,"a":3}` — 敵への状態異常〔e="levitate", t=200, a=3〕
09. `{"op":"strip"}` — 強化解除〔〕
10. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
11. `{"op":"allies","r":32}` — 味方対象〔r=32〕
12. `{"op":"healpct","v":0.6,"to":1}` — 最大HP割合回復〔v=0.6, to=1〕
13. `{"op":"undying","t":180,"to":1}` — 死亡防護〔t=180, to=1〕
14. `{"op":"fx","p":"heart","n":12,"at":"t","s":0.5}` — 粒子演出〔p="heart", n=12, at="t", s=0.5〕
15. `{"op":"area","r":26,"n":24}` — 円形対象の取得〔r=26, n=24〕
16. `{"op":"stun","t":45}` — 行動停止〔t=45〕
17. `{"op":"fx","p":"end_rod","n":35,"at":"ring","r":9}` — 粒子演出〔p="end_rod", n=35, at="ring", r=9〕
18. `{"op":"fx","p":"firework","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="firework", n=50, at="ring", r=8.0, y=0.6〕
19. `{"op":"fx","p":"compost","n":32,"at":"line","r":30}` — 粒子演出〔p="compost", n=32, at="line", r=30〕
20. `{"op":"sound","s":"totem","v":1.15,"pi":0.95}` — 効果音〔s="totem", v=1.15, pi=0.95〕
21. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.nortia_legend.stage0","ops":[{"op":"fx","p":"firework","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"chime","v":0.9,"pi":1.2},{"op":"fx","p":"firework","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"happy","n":6,"at":"line","r":10},{"op":"fx","p":"happy","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"firework","n":36,"at":"line","r":24},{"op":"sound","s":"totem","v":1.05,"pi":1.14},{"op":"area","r":23.0,"n":17},{"op":"stun","t":40},{"op":"eff","e":"glow","t":120,"a":0},{"op":"self"},{"op":"buff","e":"luck","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.nortia_legend.stage1","ops":[{"op":"fx","p":"firework","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"chime","v":1.05,"pi":1.0},{"op":"fx","p":"happy","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"firework","n":6,"at":"line","r":15},{"op":"fx","p":"firework","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"compost","n":32,"at":"line","r":30},{"op":"sound","s":"totem","v":1.15,"pi":0.95},{"op":"area","r":25.0,"n":22},{"op":"launch","f":1.3},{"op":"dmg","m":4.06},{"op":"eff","e":"slow","t":85,"a":1},{"op":"area","r":14.0,"n":10},{"op":"eff","e":"levitate","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.nortia_legend.stage2","ops":[{"op":"fx","p":"firework","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"chime","v":1.25,"pi":0.75},{"op":"fx","p":"happy","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"firework","n":10,"at":"line","r":20},{"op":"fx","p":"happy","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"firework","n":48,"at":"line","r":48},{"op":"fx","p":"compost","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"totem","v":1.5,"pi":0.75},{"op":"area","r":32.0,"n":28},{"op":"dmg","m":9.072},{"op":"stun","t":60},{"op":"knock","f":3.2},{"op":"self"},{"op":"buff","e":"jump","t":160,"a":4},{"op":"fx","p":"compost","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"happy","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":28.0,"n":24},{"op":"dmg","m":2.4},{"op":"launch","f":1.9},{"op":"self"},{"op":"buff","e":"jump","t":180,"a":4},{"op":"area","r":30.0,"n":16},{"op":"dmg","m":0.9},{"op":"eff","e":"levitate","t":160,"a":2},{"op":"self"},{"op":"buff","e":"luck","t":240,"a":4},{"op":"area","r":20,"n":6},{"op":"launch","f":1.4},{"op":"fx","p":"firework","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"chime","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"levitate","t":38,"a":3},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.nortia_legend.stage0","ops":[{"op":"fx","p":"firework","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"chime","v":0.9,"pi":1.2},{"op":"fx","p":"firework","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"happy","n":6,"at":"line","r":10},{"op":"fx","p":"happy","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"firework","n":36,"at":"line","r":24},{"op":"sound","s":"totem","v":1.05,"pi":1.14},{"op":"area","r":23.0,"n":17},{"op":"stun","t":40},{"op":"eff","e":"glow","t":120,"a":0},{"op":"self"},{"op":"buff","e":"luck","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.nortia_legend.stage1","ops":[{"op":"fx","p":"firework","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"chime","v":1.05,"pi":1.0},{"op":"fx","p":"happy","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"firework","n":6,"at":"line","r":15},{"op":"fx","p":"firework","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"compost","n":32,"at":"line","r":30},{"op":"sound","s":"totem","v":1.15,"pi":0.95},{"op":"area","r":25.0,"n":22},{"op":"launch","f":1.3},{"op":"dmg","m":4.06},{"op":"eff","e":"slow","t":85,"a":1},{"op":"area","r":14.0,"n":10},{"op":"eff","e":"levitate","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.nortia_legend.stage2","ops":[{"op":"fx","p":"firework","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"chime","v":1.25,"pi":0.75},{"op":"fx","p":"happy","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"firework","n":10,"at":"line","r":20},{"op":"fx","p":"happy","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"firework","n":48,"at":"line","r":48},{"op":"fx","p":"compost","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"totem","v":1.5,"pi":0.75},{"op":"area","r":32.0,"n":28},{"op":"dmg","m":9.072},{"op":"stun","t":60},{"op":"knock","f":3.2},{"op":"self"},{"op":"buff","e":"jump","t":160,"a":4},{"op":"fx","p":"compost","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"happy","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":28.0,"n":24},{"op":"dmg","m":2.4},{"op":"launch","f":1.9},{"op":"self"},{"op":"buff","e":"jump","t":180,"a":4},{"op":"area","r":30.0,"n":16},{"op":"dmg","m":0.9},{"op":"eff","e":"levitate","t":160,"a":2},{"op":"self"},{"op":"buff","e":"luck","t":240,"a":4},{"op":"area","r":20,"n":6},{"op":"launch","f":1.4},{"op":"fx","p":"firework","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"chime","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"levitate","t":38,"a":3},{"op":"mark","t":135,"x":1.8}]}]〕
22. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
23. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 13. 失楽堕天 ルシファーラ

**モブ側の動きの方向性**：翼の微細な揺れ、視線、指先、薔薇の動きで誘惑を演出する。。

### 失楽堕天の大鎌 — 討伐武器（メイン／武器欄） (`lucifara_weapon`)

**現行パラメータ**：rank=1、damage登録値=280.05797、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:sweeping_edge:25、minecraft:fire_aspect:10。

**装備中の常時命令（4命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"regen","t":40,"a":0}` — 強化〔e="regen", t=40, a=0〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（10命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"heal","v":4}` — heal〔v=4〕
05. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"weakness","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"weakness","t":90,"a":0}]〕
06. `{"op":"chance","p":0.51,"ops":[{"op":"victim"},{"op":"fx","p":"witch","n":13,"at":"t","s":0.24},{"op":"mark","t":160,"x":1.93},{"op":"eff","e":"weakness","t":55,"a":0}]}` — 抽選〔p=0.51, ops=[{"op":"victim"},{"op":"fx","p":"witch","n":13,"at":"t","s":0.24},{"op":"mark","t":160,"x":1.93},{"op":"eff","e":"weakness","t":55,"a":0}]〕
07. `{"op":"chance","p":0.204,"ops":[{"op":"victim"},{"op":"dmg","m":0.27}]}` — 抽選〔p=0.204, ops=[{"op":"victim"},{"op":"dmg","m":0.27}]〕
08. `{"op":"chance","p":0.085,"ops":[{"op":"victim"},{"op":"fx","p":"witch","n":8,"at":"t","s":0.25},{"op":"self"},{"op":"healpct","v":0.035}]}` — 抽選〔p=0.085, ops=[{"op":"victim"},{"op":"fx","p":"witch","n":8,"at":"t","s":0.25},{"op":"self"},{"op":"healpct","v":0.035}]〕
09. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"witch","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"witch","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]〕
10. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"soul","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":32,"a":3}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"soul","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":32,"a":3}]〕

**権能発動時の命令（27命令）**：

01. `{"op":"fx","p":"soul","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="soul", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"soul","n":4,"at":"self","s":0.7}` — 粒子演出〔p="soul", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"dragon","n":40,"at":"self","s":1.2}` — 粒子演出〔p="dragon", n=40, at="self", s=1.2〕
04. `{"op":"fx","p":"heart","n":10,"at":"self"}` — 粒子演出〔p="heart", n=10, at="self"〕
05. `{"op":"sound","s":"mirror","v":0.8,"pi":0.6}` — 効果音〔s="mirror", v=0.8, pi=0.6〕
06. `{"op":"cone","r":14,"a":160}` — 扇形対象の取得〔r=14, a=160〕
07. `{"op":"dmg","m":1.8}` — 追加攻撃〔m=1.8〕
08. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
09. `{"op":"eff","e":"weakness","t":300,"a":4}` — 敵への状態異常〔e="weakness", t=300, a=4〕
10. `{"op":"eff","e":"nausea","t":200,"a":0}` — 敵への状態異常〔e="nausea", t=200, a=0〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"healpct","v":0.25}` — 最大HP割合回復〔v=0.25〕
13. `{"op":"fx","p":"heart","n":12,"at":"t","s":0.5}` — 粒子演出〔p="heart", n=12, at="t", s=0.5〕
14. `{"op":"fx","p":"witch","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="witch", n=46, at="ring", r=5.5, y=0.25〕
15. `{"op":"fx","p":"heart","n":36,"at":"line","r":24}` — 粒子演出〔p="heart", n=36, at="line", r=24〕
16. `{"op":"area","r":25.0,"n":20}` — 円形対象の取得〔r=25.0, n=20〕
17. `{"op":"eff","e":"weakness","t":125,"a":2}` — 敵への状態異常〔e="weakness", t=125, a=2〕
18. `{"op":"dmg","m":2.0}` — 追加攻撃〔m=2.0〕
19. `{"op":"fx","p":"witch","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="witch", n=16, at="ring", r=5.0〕
20. `{"op":"sound","s":"sonic","v":0.75,"pi":1.15}` — 効果音〔s="sonic", v=0.75, pi=1.15〕
21. `{"op":"cone","r":11,"a":85}` — 扇形対象の取得〔r=11, a=85〕
22. `{"op":"dmg","m":1.0}` — 追加攻撃〔m=1.0〕
23. `{"op":"eff","e":"weakness","t":65,"a":0}` — 敵への状態異常〔e="weakness", t=65, a=0〕
24. `{"op":"fx","p":"witch","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="witch", n=24, at="ring", r=4.5, y=0.6〕
25. `{"op":"sound","s":"wither","v":0.8,"pi":0.8}` — 効果音〔s="wither", v=0.8, pi=0.8〕
26. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
27. `{"op":"eff","e":"weakness","t":100,"a":124}` — 敵への状態異常〔e="weakness", t=100, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 深紅の誘惑羽根 — 神威触媒（Curios relic_focus） (`lucifara_focus`)

**現行パラメータ**：rank=2、damage登録値=68.31、relics側CD=160tick、art側CD=160tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"night","t":300,"a":0}` — 強化〔e="night", t=300, a=0〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"regen","t":45,"a":0}` — 強化〔e="regen", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"regen","t":42,"a":2}` — 強化〔e="regen", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（43命令）**：

01. `{"op":"fx","p":"soul","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="soul", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"soul","n":6,"at":"self","s":0.7}` — 粒子演出〔p="soul", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"dragon","n":40,"at":"self","s":1.2}` — 粒子演出〔p="dragon", n=40, at="self", s=1.2〕
04. `{"op":"fx","p":"heart","n":10,"at":"self"}` — 粒子演出〔p="heart", n=10, at="self"〕
05. `{"op":"sound","s":"mirror","v":0.8,"pi":0.6}` — 効果音〔s="mirror", v=0.8, pi=0.6〕
06. `{"op":"area","r":24,"n":36}` — 円形対象の取得〔r=24, n=36〕
07. `{"op":"pull","f":2.5}` — pull〔f=2.5〕
08. `{"op":"eff","e":"nausea","t":300,"a":0}` — 敵への状態異常〔e="nausea", t=300, a=0〕
09. `{"op":"eff","e":"weakness","t":400,"a":5}` — 敵への状態異常〔e="weakness", t=400, a=5〕
10. `{"op":"eff","e":"slow","t":300,"a":3}` — 敵への状態異常〔e="slow", t=300, a=3〕
11. `{"op":"mark","t":300,"x":2.0}` — 刻印〔t=300, x=2.0〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"regen","t":150,"a":1}` — 強化〔e="regen", t=150, a=1〕
15. `{"op":"fx","p":"heart","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="heart", n=50, at="ring", r=8.0, y=0.6〕
16. `{"op":"fx","p":"ash","n":32,"at":"line","r":30}` — 粒子演出〔p="ash", n=32, at="line", r=30〕
17. `{"op":"sound","s":"wither","v":1.15,"pi":0.95}` — 効果音〔s="wither", v=1.15, pi=0.95〕
18. `{"op":"chain","n":5,"r":18.0}` — chain〔n=5, r=18.0〕
19. `{"op":"dmg","m":2.7}` — 追加攻撃〔m=2.7〕
20. `{"op":"mark","t":140,"x":1.6}` — 刻印〔t=140, x=1.6〕
21. `{"op":"self"}` — 対象を自分へ〔〕
22. `{"op":"healpct","v":0.2}` — 最大HP割合回復〔v=0.2〕
23. `{"op":"self"}` — 対象を自分へ〔〕
24. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
25. `{"op":"buff","e":"regen","t":150,"a":3}` — 強化〔e="regen", t=150, a=3〕
26. `{"op":"fx","p":"witch","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="witch", n=24, at="ring", r=12, y=0.5〕
27. `{"op":"sound","s":"wither","v":0.85,"pi":1.04}` — 効果音〔s="wither", v=0.85, pi=1.04〕
28. `{"op":"area","r":14.0,"n":12}` — 円形対象の取得〔r=14.0, n=12〕
29. `{"op":"dmg","m":0.8}` — 追加攻撃〔m=0.8〕
30. `{"op":"eff","e":"weakness","t":100,"a":1}` — 敵への状態異常〔e="weakness", t=100, a=1〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"regen","t":200,"a":3}` — 強化〔e="regen", t=200, a=3〕
33. `{"op":"area","r":14,"n":7}` — 円形対象の取得〔r=14, n=7〕
34. `{"op":"pull","f":1.7}` — pull〔f=1.7〕
35. `{"op":"fx","p":"witch","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="witch", n=24, at="ring", r=5.5, y=0.7〕
36. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
37. `{"op":"eff","e":"weakness","t":135,"a":123}` — 敵への状態異常〔e="weakness", t=135, a=123〕
38. `{"op":"self"}` — 対象を自分へ〔〕
39. `{"op":"buff","e":"regen","t":140,"a":7}` — 強化〔e="regen", t=140, a=7〕
40. `{"op":"fx","p":"soul","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="soul", n=16, at="ring", r=3.7, y=0.55〕
41. `{"op":"area","r":16,"n":9}` — 円形対象の取得〔r=16, n=9〕
42. `{"op":"eff","e":"weakness","t":70,"a":12}` — 敵への状態異常〔e="weakness", t=70, a=12〕
43. `{"op":"mark","t":135,"x":1.8}` — 刻印〔t=135, x=1.8〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 甘夢の翼飾り — 神格装飾品（Curios relic_charm） (`lucifara_charm`)

**現行パラメータ**：rank=1、damage登録値=68.31、relics側CD=190tick、art側CD=190tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（13命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"slowfall","t":40,"a":0}` — 強化〔e="slowfall", t=40, a=0〕
03. `{"op":"buff","e":"speed","t":40,"a":0}` — 強化〔e="speed", t=40, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"regen","t":45,"a":0}` — 強化〔e="regen", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
09. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"regen","t":42,"a":2}` — 強化〔e="regen", t=42, a=2〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"absorb","t":48,"a":4}` — 強化〔e="absorb", t=48, a=4〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（38命令）**：

01. `{"op":"fx","p":"soul","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="soul", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"soul","n":4,"at":"self","s":0.7}` — 粒子演出〔p="soul", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"dragon","n":40,"at":"self","s":1.2}` — 粒子演出〔p="dragon", n=40, at="self", s=1.2〕
04. `{"op":"fx","p":"heart","n":10,"at":"self"}` — 粒子演出〔p="heart", n=10, at="self"〕
05. `{"op":"sound","s":"mirror","v":0.8,"pi":0.6}` — 効果音〔s="mirror", v=0.8, pi=0.6〕
06. `{"op":"area","r":20,"n":36}` — 円形対象の取得〔r=20, n=36〕
07. `{"op":"stun","t":80}` — 行動停止〔t=80〕
08. `{"op":"eff","e":"blind","t":200,"a":0}` — 敵への状態異常〔e="blind", t=200, a=0〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"invis","t":200,"a":0}` — 強化〔e="invis", t=200, a=0〕
11. `{"op":"buff","e":"regen","t":200,"a":2}` — 強化〔e="regen", t=200, a=2〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"regen","t":210,"a":1}` — 強化〔e="regen", t=210, a=1〕
15. `{"op":"fx","p":"witch","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="witch", n=46, at="ring", r=5.5, y=0.25〕
16. `{"op":"fx","p":"heart","n":36,"at":"line","r":24}` — 粒子演出〔p="heart", n=36, at="line", r=24〕
17. `{"op":"sound","s":"wither","v":1.05,"pi":1.14}` — 効果音〔s="wither", v=1.05, pi=1.14〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"guard","t":95}` — 防御〔t=95〕
20. `{"op":"self"}` — 対象を自分へ〔〕
21. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
22. `{"op":"cleanse"}` — 状態異常解除〔〕
23. `{"op":"buff","e":"regen","t":180,"a":3}` — 強化〔e="regen", t=180, a=3〕
24. `{"op":"guard","t":95}` — 防御〔t=95〕
25. `{"op":"fx","p":"witch","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="witch", n=30, at="ring", r=4.0, y=0.7〕
26. `{"op":"sound","s":"wither","v":0.8,"pi":1.1}` — 効果音〔s="wither", v=0.8, pi=1.1〕
27. `{"op":"self"}` — 対象を自分へ〔〕
28. `{"op":"buff","e":"regen","t":260,"a":4}` — 強化〔e="regen", t=260, a=4〕
29. `{"op":"guard","t":125}` — 防御〔t=125〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"absorb","t":240,"a":3}` — 強化〔e="absorb", t=240, a=3〕
32. `{"op":"fx","p":"witch","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="witch", n=20, at="ring", r=4, y=0.4〕
33. `{"op":"self"}` — 対象を自分へ〔〕
34. `{"op":"buff","e":"regen","t":140,"a":7}` — 強化〔e="regen", t=140, a=7〕
35. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
36. `{"op":"eff","e":"weakness","t":100,"a":123}` — 敵への状態異常〔e="weakness", t=100, a=123〕
37. `{"op":"self"}` — 対象を自分へ〔〕
38. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 欲望王権・魂宴の聖杯 — 超越神器（武器欄） (`lucifara_legend`)

**現行パラメータ**：rank=3、damage登録値=428.82609、relics側CD=345tick、art側CD=345tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:sweeping_edge:25、minecraft:fire_aspect:10。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
08. `{"op":"buff","e":"regen","t":45,"a":3}` — 強化〔e="regen", t=45, a=3〕
09. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（10命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"heal","v":10}` — heal〔v=10〕
05. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"weakness","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"weakness","t":160,"a":1}]〕
06. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"witch","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"witch","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
07. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"wither","t":135,"a":2},{"op":"fx","p":"witch","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"wither","t":135,"a":2},{"op":"fx","p":"witch","n":10,"at":"t","s":0.35}]〕
08. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
09. `{"op":"chance","p":0.35,"ops":[{"op":"victim"},{"op":"fx","p":"witch","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.35, ops=[{"op":"victim"},{"op":"fx","p":"witch","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]〕
10. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"soul","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":62,"a":5}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"soul","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":62,"a":5}]〕

**権能発動時の命令（27命令）**：

01. `{"op":"fx","p":"soul","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="soul", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"soul","n":4,"at":"self","s":0.7}` — 粒子演出〔p="soul", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"dragon","n":40,"at":"self","s":1.2}` — 粒子演出〔p="dragon", n=40, at="self", s=1.2〕
04. `{"op":"fx","p":"heart","n":10,"at":"self"}` — 粒子演出〔p="heart", n=10, at="self"〕
05. `{"op":"sound","s":"mirror","v":0.8,"pi":0.6}` — 効果音〔s="mirror", v=0.8, pi=0.6〕
06. `{"op":"area","r":40,"n":36}` — 円形対象の取得〔r=40, n=36〕
07. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
08. `{"op":"pull","f":2.0}` — pull〔f=2.0〕
09. `{"op":"stun","t":105}` — 行動停止〔t=105〕
10. `{"op":"eff","e":"weakness","t":600,"a":9}` — 敵への状態異常〔e="weakness", t=600, a=9〕
11. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"healpct","v":0.6}` — 最大HP割合回復〔v=0.6〕
14. `{"op":"buff","e":"absorb","t":600,"a":8}` — 強化〔e="absorb", t=600, a=8〕
15. `{"op":"allies","r":32}` — 味方対象〔r=32〕
16. `{"op":"healpct","v":0.6,"to":1}` — 最大HP割合回復〔v=0.6, to=1〕
17. `{"op":"fx","p":"heart","n":12,"at":"t","s":0.5}` — 粒子演出〔p="heart", n=12, at="t", s=0.5〕
18. `{"op":"area","r":30,"n":24}` — 円形対象の取得〔r=30, n=24〕
19. `{"op":"strip"}` — 強化解除〔〕
20. `{"op":"eff","e":"wither","t":160,"a":1}` — 敵への状態異常〔e="wither", t=160, a=1〕
21. `{"op":"dmg","m":1.2}` — 追加攻撃〔m=1.2〕
22. `{"op":"fx","p":"heart","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="heart", n=50, at="ring", r=8.0, y=0.6〕
23. `{"op":"fx","p":"ash","n":32,"at":"line","r":30}` — 粒子演出〔p="ash", n=32, at="line", r=30〕
24. `{"op":"sound","s":"wither","v":1.15,"pi":0.95}` — 効果音〔s="wither", v=1.15, pi=0.95〕
25. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.lucifara_legend.stage0","ops":[{"op":"fx","p":"witch","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"wither","v":0.9,"pi":1.2},{"op":"fx","p":"soul","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"witch","n":6,"at":"line","r":10},{"op":"fx","p":"witch","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"heart","n":36,"at":"line","r":24},{"op":"sound","s":"wither","v":1.05,"pi":1.14},{"op":"area","r":25.0,"n":20},{"op":"eff","e":"weakness","t":125,"a":2},{"op":"dmg","m":2.7},{"op":"self"},{"op":"buff","e":"regen","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.lucifara_legend.stage1","ops":[{"op":"fx","p":"witch","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"wither","v":1.05,"pi":1.0},{"op":"fx","p":"witch","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"soul","n":6,"at":"line","r":15},{"op":"fx","p":"heart","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"ash","n":32,"at":"line","r":30},{"op":"sound","s":"wither","v":1.15,"pi":0.95},{"op":"chain","n":5,"r":18.0},{"op":"dmg","m":3.915},{"op":"mark","t":140,"x":2.08},{"op":"self"},{"op":"healpct","v":0.2},{"op":"area","r":16.0,"n":10},{"op":"eff","e":"weakness","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.lucifara_legend.stage2","ops":[{"op":"fx","p":"witch","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"wither","v":1.25,"pi":0.75},{"op":"fx","p":"witch","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"soul","n":10,"at":"line","r":20},{"op":"fx","p":"witch","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"heart","n":48,"at":"line","r":48},{"op":"fx","p":"ash","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"wither","v":1.5,"pi":0.75},{"op":"area","r":34.0,"n":28},{"op":"strip"},{"op":"dmg","m":9.72},{"op":"eff","e":"wither","t":130,"a":2},{"op":"self"},{"op":"buff","e":"regen","t":180,"a":3},{"op":"fx","p":"ash","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"witch","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":28.0,"n":22},{"op":"dmg","m":2.9},{"op":"eff","e":"weakness","t":160,"a":2},{"op":"self"},{"op":"healpct","v":0.35},{"op":"area","r":15.0,"n":16},{"op":"dmg","m":1.0},{"op":"eff","e":"weakness","t":160,"a":2},{"op":"self"},{"op":"buff","e":"regen","t":240,"a":4},{"op":"area","r":14,"n":8},{"op":"eff","e":"weakness","t":100,"a":1},{"op":"fx","p":"witch","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"wither","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"weakness","t":70,"a":12},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.lucifara_legend.stage0","ops":[{"op":"fx","p":"witch","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"wither","v":0.9,"pi":1.2},{"op":"fx","p":"soul","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"witch","n":6,"at":"line","r":10},{"op":"fx","p":"witch","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"heart","n":36,"at":"line","r":24},{"op":"sound","s":"wither","v":1.05,"pi":1.14},{"op":"area","r":25.0,"n":20},{"op":"eff","e":"weakness","t":125,"a":2},{"op":"dmg","m":2.7},{"op":"self"},{"op":"buff","e":"regen","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.lucifara_legend.stage1","ops":[{"op":"fx","p":"witch","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"wither","v":1.05,"pi":1.0},{"op":"fx","p":"witch","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"soul","n":6,"at":"line","r":15},{"op":"fx","p":"heart","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"ash","n":32,"at":"line","r":30},{"op":"sound","s":"wither","v":1.15,"pi":0.95},{"op":"chain","n":5,"r":18.0},{"op":"dmg","m":3.915},{"op":"mark","t":140,"x":2.08},{"op":"self"},{"op":"healpct","v":0.2},{"op":"area","r":16.0,"n":10},{"op":"eff","e":"weakness","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.lucifara_legend.stage2","ops":[{"op":"fx","p":"witch","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"wither","v":1.25,"pi":0.75},{"op":"fx","p":"witch","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"soul","n":10,"at":"line","r":20},{"op":"fx","p":"witch","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"heart","n":48,"at":"line","r":48},{"op":"fx","p":"ash","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"wither","v":1.5,"pi":0.75},{"op":"area","r":34.0,"n":28},{"op":"strip"},{"op":"dmg","m":9.72},{"op":"eff","e":"wither","t":130,"a":2},{"op":"self"},{"op":"buff","e":"regen","t":180,"a":3},{"op":"fx","p":"ash","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"witch","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":28.0,"n":22},{"op":"dmg","m":2.9},{"op":"eff","e":"weakness","t":160,"a":2},{"op":"self"},{"op":"healpct","v":0.35},{"op":"area","r":15.0,"n":16},{"op":"dmg","m":1.0},{"op":"eff","e":"weakness","t":160,"a":2},{"op":"self"},{"op":"buff","e":"regen","t":240,"a":4},{"op":"area","r":14,"n":8},{"op":"eff","e":"weakness","t":100,"a":1},{"op":"fx","p":"witch","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"wither","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"weakness","t":70,"a":12},{"op":"mark","t":135,"x":1.8}]}]〕
26. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
27. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 14. 超克覇王 辿迦

**モブ側の動きの方向性**：拳法の足腰と投げの受け流しを分け、剛柔転換を重視する。。

### 超克覇王の拳甲 — 討伐武器（メイン／武器欄） (`taika_weapon`)

**現行パラメータ**：rank=1、damage登録値=399.33333、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12。

**装備中の常時命令（5命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"speed","t":40,"a":1}` — 強化〔e="speed", t=40, a=1〕
03. `{"op":"buff","e":"strength","t":40,"a":1}` — 強化〔e="strength", t=40, a=1〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（9命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"dmg","m":0.3}` — 追加攻撃〔m=0.3〕
03. `{"op":"knock","f":1.5}` — knock〔f=1.5〕
04. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"weakness","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"weakness","t":90,"a":0}]〕
05. `{"op":"chance","p":0.535,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":15,"at":"t","s":0.24},{"op":"mark","t":180,"x":2.07},{"op":"eff","e":"weakness","t":67,"a":0}]}` — 抽選〔p=0.535, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":15,"at":"t","s":0.24},{"op":"mark","t":180,"x":2.07},{"op":"eff","e":"weakness","t":67,"a":0}]〕
06. `{"op":"chance","p":0.231,"ops":[{"op":"victim"},{"op":"dmg","m":0.305}]}` — 抽選〔p=0.231, ops=[{"op":"victim"},{"op":"dmg","m":0.305}]〕
07. `{"op":"chance","p":0.104,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":8,"at":"t","s":0.25},{"op":"knock","f":0.6}]}` — 抽選〔p=0.104, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":8,"at":"t","s":0.25},{"op":"knock","f":0.6}]〕
08. `{"op":"chance","p":0.24,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.24, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]〕
09. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]〕

**権能発動時の命令（29命令）**：

01. `{"op":"fx","p":"sonic","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="sonic", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"sonic","n":4,"at":"self","s":0.7}` — 粒子演出〔p="sonic", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"explosion","n":6,"at":"self","s":1.0}` — 粒子演出〔p="explosion", n=6, at="self", s=1.0〕
04. `{"op":"fx","p":"crit","n":40,"at":"self"}` — 粒子演出〔p="crit", n=40, at="self"〕
05. `{"op":"sound","s":"blast","v":1.0,"pi":0.7}` — 効果音〔s="blast", v=1.0, pi=0.7〕
06. `{"op":"near","r":20,"n":1}` — near〔r=20, n=1〕
07. `{"op":"behind"}` — behind〔〕
08. `{"op":"dmg","m":1.2}` — 追加攻撃〔m=1.2〕
09. `{"op":"dmg","m":1.2}` — 追加攻撃〔m=1.2〕
10. `{"op":"dmg","m":1.2}` — 追加攻撃〔m=1.2〕
11. `{"op":"knock","f":4.0}` — knock〔f=4.0〕
12. `{"op":"launch","f":1.5}` — launch〔f=1.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"strength","t":300,"a":6}` — 強化〔e="strength", t=300, a=6〕
15. `{"op":"fx","p":"explosion","n":12,"at":"t","s":0.5}` — 粒子演出〔p="explosion", n=12, at="t", s=0.5〕
16. `{"op":"fx","p":"crit","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="crit", n=46, at="ring", r=5.5, y=0.25〕
17. `{"op":"fx","p":"sonic","n":36,"at":"line","r":24}` — 粒子演出〔p="sonic", n=36, at="line", r=24〕
18. `{"op":"cone","r":13.0,"a":110.0}` — 扇形対象の取得〔r=13.0, a=110.0〕
19. `{"op":"dmg","m":3.5}` — 追加攻撃〔m=3.5〕
20. `{"op":"slam"}` — slam〔〕
21. `{"op":"fx","p":"crit","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="crit", n=16, at="ring", r=5.0〕
22. `{"op":"sound","s":"sonic","v":0.75,"pi":1.15}` — 効果音〔s="sonic", v=0.75, pi=1.15〕
23. `{"op":"cone","r":11,"a":85}` — 扇形対象の取得〔r=11, a=85〕
24. `{"op":"dmg","m":1.0}` — 追加攻撃〔m=1.0〕
25. `{"op":"eff","e":"weakness","t":65,"a":0}` — 敵への状態異常〔e="weakness", t=65, a=0〕
26. `{"op":"fx","p":"crit","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="crit", n=24, at="ring", r=4.5, y=0.6〕
27. `{"op":"sound","s":"sonic","v":0.8,"pi":0.8}` — 効果音〔s="sonic", v=0.8, pi=0.8〕
28. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
29. `{"op":"eff","e":"weakness","t":100,"a":124}` — 敵への状態異常〔e="weakness", t=100, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 仙境修練の腕輪 — 神威触媒（Curios relic_focus） (`taika_focus`)

**現行パラメータ**：rank=2、damage登録値=75.8241、relics側CD=155tick、art側CD=155tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"haste","t":40,"a":1}` — 強化〔e="haste", t=40, a=1〕
03. `{"op":"buff","e":"jump","t":40,"a":1}` — 強化〔e="jump", t=40, a=1〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"strength","t":45,"a":0}` — 強化〔e="strength", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"strength","t":45,"a":2}` — 強化〔e="strength", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"strength","t":42,"a":2}` — 強化〔e="strength", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（42命令）**：

01. `{"op":"fx","p":"sonic","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="sonic", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"sonic","n":6,"at":"self","s":0.7}` — 粒子演出〔p="sonic", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"explosion","n":6,"at":"self","s":1.0}` — 粒子演出〔p="explosion", n=6, at="self", s=1.0〕
04. `{"op":"fx","p":"crit","n":40,"at":"self"}` — 粒子演出〔p="crit", n=40, at="self"〕
05. `{"op":"sound","s":"blast","v":1.0,"pi":0.7}` — 効果音〔s="blast", v=1.0, pi=0.7〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"strength","t":600,"a":9}` — 強化〔e="strength", t=600, a=9〕
08. `{"op":"buff","e":"speed","t":600,"a":3}` — 強化〔e="speed", t=600, a=3〕
09. `{"op":"buff","e":"resist","t":600,"a":3}` — 強化〔e="resist", t=600, a=3〕
10. `{"op":"buff","e":"jump","t":600,"a":2}` — 強化〔e="jump", t=600, a=2〕
11. `{"op":"healpct","v":0.4}` — 最大HP割合回復〔v=0.4〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"strength","t":150,"a":1}` — 強化〔e="strength", t=150, a=1〕
15. `{"op":"fx","p":"sonic","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="sonic", n=50, at="ring", r=8.0, y=0.6〕
16. `{"op":"fx","p":"smoke","n":32,"at":"line","r":30}` — 粒子演出〔p="smoke", n=32, at="line", r=30〕
17. `{"op":"sound","s":"sonic","v":1.15,"pi":0.95}` — 効果音〔s="sonic", v=1.15, pi=0.95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"adapt"}` — adapt〔〕
20. `{"op":"guard","t":125}` — 防御〔t=125〕
21. `{"op":"buff","e":"strength","t":170,"a":3}` — 強化〔e="strength", t=170, a=3〕
22. `{"op":"self"}` — 対象を自分へ〔〕
23. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
24. `{"op":"buff","e":"strength","t":150,"a":3}` — 強化〔e="strength", t=150, a=3〕
25. `{"op":"fx","p":"crit","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="crit", n=24, at="ring", r=12, y=0.5〕
26. `{"op":"sound","s":"sonic","v":0.85,"pi":1.11}` — 効果音〔s="sonic", v=0.85, pi=1.11〕
27. `{"op":"cone","r":16.0,"a":95.0}` — 扇形対象の取得〔r=16.0, a=95.0〕
28. `{"op":"dmg","m":0.95}` — 追加攻撃〔m=0.95〕
29. `{"op":"eff","e":"weakness","t":120,"a":1}` — 敵への状態異常〔e="weakness", t=120, a=1〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"strength","t":220,"a":3}` — 強化〔e="strength", t=220, a=3〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"adapt","t":160}` — adapt〔t=160〕
34. `{"op":"fx","p":"crit","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="crit", n=24, at="ring", r=5.5, y=0.7〕
35. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
36. `{"op":"eff","e":"weakness","t":135,"a":123}` — 敵への状態異常〔e="weakness", t=135, a=123〕
37. `{"op":"self"}` — 対象を自分へ〔〕
38. `{"op":"buff","e":"strength","t":80,"a":19}` — 強化〔e="strength", t=80, a=19〕
39. `{"op":"fx","p":"crit","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="crit", n=16, at="ring", r=3.7, y=0.55〕
40. `{"op":"cone","r":12,"a":100}` — 扇形対象の取得〔r=12, a=100〕
41. `{"op":"eff","e":"weakness","t":45,"a":16}` — 敵への状態異常〔e="weakness", t=45, a=16〕
42. `{"op":"knock","f":2.1}` — knock〔f=2.1〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 限界超越の角飾り — 神格装飾品（Curios relic_charm） (`taika_charm`)

**現行パラメータ**：rank=1、damage登録値=75.8241、relics側CD=185tick、art側CD=185tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（11命令）**：

01. `{"op":"low","pct":0.5,"ops":[{"op":"self"},{"op":"buff","e":"strength","t":40,"a":6},{"op":"buff","e":"resist","t":40,"a":2}]}` — low〔pct=0.5, ops=[{"op":"self"},{"op":"buff","e":"strength","t":40,"a":6},{"op":"buff","e":"resist","t":40,"a":2}]〕
02. `{"op":"self"}` — 対象を自分へ〔〕
03. `{"op":"buff","e":"strength","t":45,"a":0}` — 強化〔e="strength", t=45, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
06. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
07. `{"op":"buff","e":"strength","t":45,"a":1}` — 強化〔e="strength", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"strength","t":42,"a":2}` — 強化〔e="strength", t=42, a=2〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"speed","t":48,"a":5}` — 強化〔e="speed", t=48, a=5〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（35命令）**：

01. `{"op":"fx","p":"sonic","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="sonic", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"sonic","n":4,"at":"self","s":0.7}` — 粒子演出〔p="sonic", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"explosion","n":6,"at":"self","s":1.0}` — 粒子演出〔p="explosion", n=6, at="self", s=1.0〕
04. `{"op":"fx","p":"crit","n":40,"at":"self"}` — 粒子演出〔p="crit", n=40, at="self"〕
05. `{"op":"sound","s":"blast","v":1.0,"pi":0.7}` — 効果音〔s="blast", v=1.0, pi=0.7〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"adapt","t":400}` — adapt〔t=400〕
08. `{"op":"low","pct":0.4,"ops":[{"op":"self"},{"op":"healpct","v":0.25},{"op":"buff","e":"strength","t":400,"a":9},{"op":"guard","t":60}]}` — low〔pct=0.4, ops=[{"op":"self"},{"op":"healpct","v":0.25},{"op":"buff","e":"strength","t":400,"a":9},{"op":"guard","t":60}]〕
09. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"strength","t":210,"a":1}` — 強化〔e="strength", t=210, a=1〕
12. `{"op":"fx","p":"crit","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="crit", n=46, at="ring", r=5.5, y=0.25〕
13. `{"op":"fx","p":"sonic","n":36,"at":"line","r":24}` — 粒子演出〔p="sonic", n=36, at="line", r=24〕
14. `{"op":"sound","s":"sonic","v":1.05,"pi":1.14}` — 効果音〔s="sonic", v=1.05, pi=1.14〕
15. `{"op":"self"}` — 対象を自分へ〔〕
16. `{"op":"guard","t":95}` — 防御〔t=95〕
17. `{"op":"self"}` — 対象を自分へ〔〕
18. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
19. `{"op":"cleanse"}` — 状態異常解除〔〕
20. `{"op":"buff","e":"strength","t":180,"a":3}` — 強化〔e="strength", t=180, a=3〕
21. `{"op":"guard","t":95}` — 防御〔t=95〕
22. `{"op":"fx","p":"crit","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="crit", n=30, at="ring", r=4.0, y=0.7〕
23. `{"op":"sound","s":"sonic","v":0.8,"pi":1.1}` — 効果音〔s="sonic", v=0.8, pi=1.1〕
24. `{"op":"self"}` — 対象を自分へ〔〕
25. `{"op":"buff","e":"strength","t":280,"a":4}` — 強化〔e="strength", t=280, a=4〕
26. `{"op":"guard","t":140}` — 防御〔t=140〕
27. `{"op":"self"}` — 対象を自分へ〔〕
28. `{"op":"buff","e":"strength","t":240,"a":3}` — 強化〔e="strength", t=240, a=3〕
29. `{"op":"fx","p":"crit","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="crit", n=20, at="ring", r=4, y=0.4〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"strength","t":110,"a":31}` — 強化〔e="strength", t=110, a=31〕
32. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
33. `{"op":"eff","e":"weakness","t":100,"a":123}` — 敵への状態異常〔e="weakness", t=100, a=123〕
34. `{"op":"self"}` — 対象を自分へ〔〕
35. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 覇王更新・無限超克 — 超越神器（武器欄） (`taika_legend`)

**現行パラメータ**：rank=3、damage登録値=770.58333、relics側CD=340tick、art側CD=340tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"buff","e":"speed","t":40,"a":1}` — 強化〔e="speed", t=40, a=1〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
08. `{"op":"buff","e":"strength","t":45,"a":3}` — 強化〔e="strength", t=45, a=3〕
09. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（10命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"dmg","m":0.5}` — 追加攻撃〔m=0.5〕
03. `{"op":"dmg","m":0.5}` — 追加攻撃〔m=0.5〕
04. `{"op":"knock","f":3.0}` — knock〔f=3.0〕
05. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"weakness","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"weakness","t":160,"a":1}]〕
06. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
07. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"crit","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"crit","n":10,"at":"t","s":0.35}]〕
08. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
09. `{"op":"chance","p":0.375,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.375, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]〕
10. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]〕

**権能発動時の命令（28命令）**：

01. `{"op":"fx","p":"sonic","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="sonic", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"sonic","n":4,"at":"self","s":0.7}` — 粒子演出〔p="sonic", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"explosion","n":6,"at":"self","s":1.0}` — 粒子演出〔p="explosion", n=6, at="self", s=1.0〕
04. `{"op":"fx","p":"crit","n":40,"at":"self"}` — 粒子演出〔p="crit", n=40, at="self"〕
05. `{"op":"sound","s":"blast","v":1.0,"pi":0.7}` — 効果音〔s="blast", v=1.0, pi=0.7〕
06. `{"op":"area","r":32,"n":36}` — 円形対象の取得〔r=32, n=36〕
07. `{"op":"dmg","m":1.12}` — 追加攻撃〔m=1.12〕
08. `{"op":"dmg","m":1.12}` — 追加攻撃〔m=1.12〕
09. `{"op":"dmg","m":1.12}` — 追加攻撃〔m=1.12〕
10. `{"op":"dmg","m":1.12}` — 追加攻撃〔m=1.12〕
11. `{"op":"dmg","m":1.12}` — 追加攻撃〔m=1.12〕
12. `{"op":"launch","f":2.0}` — launch〔f=2.0〕
13. `{"op":"knock","f":5.0}` — knock〔f=5.0〕
14. `{"op":"self"}` — 対象を自分へ〔〕
15. `{"op":"buff","e":"strength","t":1200,"a":20}` — 強化〔e="strength", t=1200, a=20〕
16. `{"op":"buff","e":"speed","t":1200,"a":4}` — 強化〔e="speed", t=1200, a=4〕
17. `{"op":"undying","t":180}` — 死亡防護〔t=180〕
18. `{"op":"adapt","t":1200}` — adapt〔t=1200〕
19. `{"op":"fx","p":"explosion","n":12,"at":"t","s":0.5}` — 粒子演出〔p="explosion", n=12, at="t", s=0.5〕
20. `{"op":"cone","r":12,"a":120}` — 扇形対象の取得〔r=12, a=120〕
21. `{"op":"dmg","m":2.5}` — 追加攻撃〔m=2.5〕
22. `{"op":"slam"}` — slam〔〕
23. `{"op":"fx","p":"sonic","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="sonic", n=50, at="ring", r=8.0, y=0.6〕
24. `{"op":"fx","p":"smoke","n":32,"at":"line","r":30}` — 粒子演出〔p="smoke", n=32, at="line", r=30〕
25. `{"op":"sound","s":"sonic","v":1.15,"pi":0.95}` — 効果音〔s="sonic", v=1.15, pi=0.95〕
26. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.taika_legend.stage0","ops":[{"op":"fx","p":"crit","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"sonic","v":0.9,"pi":1.2},{"op":"fx","p":"crit","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"explosion","n":6,"at":"line","r":10},{"op":"fx","p":"crit","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"sonic","n":36,"at":"line","r":24},{"op":"sound","s":"sonic","v":1.05,"pi":1.14},{"op":"cone","r":13.0,"a":110.0},{"op":"dmg","m":4.725},{"op":"slam"},{"op":"self"},{"op":"buff","e":"strength","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.taika_legend.stage1","ops":[{"op":"fx","p":"crit","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"sonic","v":1.05,"pi":1.0},{"op":"fx","p":"explosion","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"crit","n":6,"at":"line","r":15},{"op":"fx","p":"sonic","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"smoke","n":32,"at":"line","r":30},{"op":"sound","s":"sonic","v":1.15,"pi":0.95},{"op":"self"},{"op":"adapt"},{"op":"guard","t":125},{"op":"buff","e":"strength","t":170,"a":3},{"op":"area","r":18.0,"n":10},{"op":"eff","e":"weakness","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.taika_legend.stage2","ops":[{"op":"fx","p":"crit","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"sonic","v":1.25,"pi":0.75},{"op":"fx","p":"explosion","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"crit","n":10,"at":"line","r":20},{"op":"fx","p":"crit","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"sonic","n":48,"at":"line","r":48},{"op":"fx","p":"smoke","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"sonic","v":1.5,"pi":0.75},{"op":"cone","r":20.0,"a":130.0},{"op":"dmg","m":11.664},{"op":"strip"},{"op":"slam"},{"op":"self"},{"op":"buff","e":"strength","t":180,"a":4},{"op":"fx","p":"smoke","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"crit","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"cone","r":19.0,"a":140.0},{"op":"dmg","m":3.4},{"op":"slam"},{"op":"self"},{"op":"buff","e":"strength","t":180,"a":4},{"op":"cone","r":18.0,"a":110.0},{"op":"dmg","m":1.1},{"op":"eff","e":"weakness","t":160,"a":2},{"op":"self"},{"op":"buff","e":"strength","t":240,"a":4},{"op":"area","r":16,"n":8},{"op":"stun","t":25},{"op":"fx","p":"crit","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"sonic","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"weakness","t":45,"a":16},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.taika_legend.stage0","ops":[{"op":"fx","p":"crit","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"sonic","v":0.9,"pi":1.2},{"op":"fx","p":"crit","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"explosion","n":6,"at":"line","r":10},{"op":"fx","p":"crit","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"sonic","n":36,"at":"line","r":24},{"op":"sound","s":"sonic","v":1.05,"pi":1.14},{"op":"cone","r":13.0,"a":110.0},{"op":"dmg","m":4.725},{"op":"slam"},{"op":"self"},{"op":"buff","e":"strength","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.taika_legend.stage1","ops":[{"op":"fx","p":"crit","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"sonic","v":1.05,"pi":1.0},{"op":"fx","p":"explosion","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"crit","n":6,"at":"line","r":15},{"op":"fx","p":"sonic","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"smoke","n":32,"at":"line","r":30},{"op":"sound","s":"sonic","v":1.15,"pi":0.95},{"op":"self"},{"op":"adapt"},{"op":"guard","t":125},{"op":"buff","e":"strength","t":170,"a":3},{"op":"area","r":18.0,"n":10},{"op":"eff","e":"weakness","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.taika_legend.stage2","ops":[{"op":"fx","p":"crit","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"sonic","v":1.25,"pi":0.75},{"op":"fx","p":"explosion","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"crit","n":10,"at":"line","r":20},{"op":"fx","p":"crit","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"sonic","n":48,"at":"line","r":48},{"op":"fx","p":"smoke","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"sonic","v":1.5,"pi":0.75},{"op":"cone","r":20.0,"a":130.0},{"op":"dmg","m":11.664},{"op":"strip"},{"op":"slam"},{"op":"self"},{"op":"buff","e":"strength","t":180,"a":4},{"op":"fx","p":"smoke","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"crit","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"cone","r":19.0,"a":140.0},{"op":"dmg","m":3.4},{"op":"slam"},{"op":"self"},{"op":"buff","e":"strength","t":180,"a":4},{"op":"cone","r":18.0,"a":110.0},{"op":"dmg","m":1.1},{"op":"eff","e":"weakness","t":160,"a":2},{"op":"self"},{"op":"buff","e":"strength","t":240,"a":4},{"op":"area","r":16,"n":8},{"op":"stun","t":25},{"op":"fx","p":"crit","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"sonic","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"weakness","t":45,"a":16},{"op":"mark","t":135,"x":1.8}]}]〕
27. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
28. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 15. 覚醒進化 メアリー・スー

**モブ側の動きの方向性**：物語が進むほど剣の型、装備、光翼が増える。。

### 次章の英雄譚 — 討伐武器（メイン／武器欄） (`mary_sue_weapon`)

**現行パラメータ**：rank=1、damage登録値=578.5、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（3命令）**：

01. `{"op":"low","pct":0.35,"ops":[{"op":"self"},{"op":"buff","e":"strength","t":40,"a":5},{"op":"buff","e":"regen","t":40,"a":3}]}` — low〔pct=0.35, ops=[{"op":"self"},{"op":"buff","e":"strength","t":40,"a":5},{"op":"buff","e":"regen","t":40,"a":3}]〕
02. `{"op":"self"}` — 対象を自分へ〔〕
03. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（7命令）**：

01. `{"op":"low","pct":0.5,"ops":[{"op":"victim"},{"op":"dmg","m":0.5}]}` — low〔pct=0.5, ops=[{"op":"victim"},{"op":"dmg","m":0.5}]〕
02. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"glow","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"glow","t":90,"a":0}]〕
03. `{"op":"chance","p":0.56,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":17,"at":"t","s":0.24},{"op":"mark","t":200,"x":2.21},{"op":"eff","e":"glow","t":79,"a":0}]}` — 抽選〔p=0.56, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":17,"at":"t","s":0.24},{"op":"mark","t":200,"x":2.21},{"op":"eff","e":"glow","t":79,"a":0}]〕
04. `{"op":"chance","p":0.258,"ops":[{"op":"victim"},{"op":"dmg","m":0.34}]}` — 抽選〔p=0.258, ops=[{"op":"victim"},{"op":"dmg","m":0.34}]〕
05. `{"op":"chance","p":0.123,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":8,"at":"t","s":0.25},{"op":"self"},{"op":"healpct","v":0.05}]}` — 抽選〔p=0.123, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":8,"at":"t","s":0.25},{"op":"self"},{"op":"healpct","v":0.05}]〕
06. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":14,"at":"t","s":0.28},{"op":"eff","e":"fatigue","t":110,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":14,"at":"t","s":0.28},{"op":"eff","e":"fatigue","t":110,"a":124},{"op":"mark","t":100,"x":2.15}]〕
07. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]〕

**権能発動時の命令（28命令）**：

01. `{"op":"fx","p":"firework","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="firework", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"firework","n":4,"at":"self","s":0.7}` — 粒子演出〔p="firework", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"enchant","n":60,"at":"self"}` — 粒子演出〔p="enchant", n=60, at="self"〕
04. `{"op":"fx","p":"end_rod","n":20,"at":"self"}` — 粒子演出〔p="end_rod", n=20, at="self"〕
05. `{"op":"sound","s":"totem","v":0.5,"pi":1.6}` — 効果音〔s="totem", v=0.5, pi=1.6〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.25}` — 最大HP割合回復〔v=0.25〕
08. `{"op":"cleanse"}` — 状態異常解除〔〕
09. `{"op":"buff","e":"absorb","t":400,"a":5}` — 強化〔e="absorb", t=400, a=5〕
10. `{"op":"buff","e":"strength","t":400,"a":4}` — 強化〔e="strength", t=400, a=4〕
11. `{"op":"area","r":16,"n":36}` — 円形対象の取得〔r=16, n=36〕
12. `{"op":"dmg","m":1.68}` — 追加攻撃〔m=1.68〕
13. `{"op":"low","pct":0.3,"ops":[{"op":"self"},{"op":"undying","t":100},{"op":"guard","t":60},{"op":"area","r":24,"n":36},{"op":"dmg","m":2.0}]}` — low〔pct=0.3, ops=[{"op":"self"},{"op":"undying","t":100},{"op":"guard","t":60},{"op":"area","r":24,"n":36},{"op":"dmg","m":2.0}]〕
14. `{"op":"fx","p":"end_rod","n":12,"at":"t","s":0.5}` — 粒子演出〔p="end_rod", n=12, at="t", s=0.5〕
15. `{"op":"fx","p":"end_rod","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="end_rod", n=46, at="ring", r=5.5, y=0.25〕
16. `{"op":"fx","p":"firework","n":36,"at":"line","r":24}` — 粒子演出〔p="firework", n=36, at="line", r=24〕
17. `{"op":"line","r":53.0,"w":3.0}` — 線分対象の取得〔r=53.0, w=3.0〕
18. `{"op":"dmg","m":3.1}` — 追加攻撃〔m=3.1〕
19. `{"op":"mark","t":115,"x":1.5}` — 刻印〔t=115, x=1.5〕
20. `{"op":"fx","p":"end_rod","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="end_rod", n=16, at="ring", r=5.0〕
21. `{"op":"sound","s":"sonic","v":0.75,"pi":1.15}` — 効果音〔s="sonic", v=0.75, pi=1.15〕
22. `{"op":"line","r":18,"w":2}` — 線分対象の取得〔r=18, w=2〕
23. `{"op":"dmg","m":1.05}` — 追加攻撃〔m=1.05〕
24. `{"op":"eff","e":"glow","t":65,"a":0}` — 敵への状態異常〔e="glow", t=65, a=0〕
25. `{"op":"fx","p":"end_rod","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="end_rod", n=24, at="ring", r=4.5, y=0.6〕
26. `{"op":"sound","s":"totem","v":0.8,"pi":0.8}` — 効果音〔s="totem", v=0.8, pi=0.8〕
27. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
28. `{"op":"eff","e":"fatigue","t":110,"a":124}` — 敵への状態異常〔e="fatigue", t=110, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 覚醒の物語頁 — 神威触媒（Curios relic_focus） (`mary_sue_focus`)

**現行パラメータ**：rank=2、damage登録値=69.6762、relics側CD=150tick、art側CD=150tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"luck","t":40,"a":2}` — 強化〔e="luck", t=40, a=2〕
03. `{"op":"buff","e":"health","t":40,"a":0}` — 強化〔e="health", t=40, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"strength","t":45,"a":0}` — 強化〔e="strength", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"strength","t":45,"a":2}` — 強化〔e="strength", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"luck","t":42,"a":2}` — 強化〔e="luck", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（43命令）**：

01. `{"op":"fx","p":"firework","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="firework", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"firework","n":6,"at":"self","s":0.7}` — 粒子演出〔p="firework", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"enchant","n":60,"at":"self"}` — 粒子演出〔p="enchant", n=60, at="self"〕
04. `{"op":"fx","p":"end_rod","n":20,"at":"self"}` — 粒子演出〔p="end_rod", n=20, at="self"〕
05. `{"op":"sound","s":"totem","v":0.5,"pi":1.6}` — 効果音〔s="totem", v=0.5, pi=1.6〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"xp","v":200}` — xp〔v=200〕
08. `{"op":"buff","e":"health","t":1200,"a":4}` — 強化〔e="health", t=1200, a=4〕
09. `{"op":"healpct","v":0.4}` — 最大HP割合回復〔v=0.4〕
10. `{"op":"buff","e":"strength","t":600,"a":5}` — 強化〔e="strength", t=600, a=5〕
11. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"strength","t":150,"a":1}` — 強化〔e="strength", t=150, a=1〕
14. `{"op":"fx","p":"firework","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="firework", n=50, at="ring", r=8.0, y=0.6〕
15. `{"op":"fx","p":"happy","n":32,"at":"line","r":30}` — 粒子演出〔p="happy", n=32, at="line", r=30〕
16. `{"op":"sound","s":"totem","v":1.15,"pi":0.95}` — 効果音〔s="totem", v=1.15, pi=0.95〕
17. `{"op":"allies","r":24.0}` — 味方対象〔r=24.0〕
18. `{"op":"healpct","v":0.35}` — 最大HP割合回復〔v=0.35〕
19. `{"op":"cleanse"}` — 状態異常解除〔〕
20. `{"op":"self"}` — 対象を自分へ〔〕
21. `{"op":"guard","t":115}` — 防御〔t=115〕
22. `{"op":"self"}` — 対象を自分へ〔〕
23. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
24. `{"op":"buff","e":"strength","t":150,"a":3}` — 強化〔e="strength", t=150, a=3〕
25. `{"op":"fx","p":"end_rod","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="end_rod", n=24, at="ring", r=12, y=0.5〕
26. `{"op":"sound","s":"totem","v":0.85,"pi":1.18}` — 効果音〔s="totem", v=0.85, pi=1.18〕
27. `{"op":"line","r":36.0,"w":2.5}` — 線分対象の取得〔r=36.0, w=2.5〕
28. `{"op":"dmg","m":0.85}` — 追加攻撃〔m=0.85〕
29. `{"op":"eff","e":"glow","t":140,"a":1}` — 敵への状態異常〔e="glow", t=140, a=1〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"luck","t":240,"a":3}` — 強化〔e="luck", t=240, a=3〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"buff","e":"strength","t":240,"a":3}` — 強化〔e="strength", t=240, a=3〕
34. `{"op":"fx","p":"end_rod","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="end_rod", n=24, at="ring", r=5.5, y=0.7〕
35. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
36. `{"op":"eff","e":"fatigue","t":148,"a":123}` — 敵への状態異常〔e="fatigue", t=148, a=123〕
37. `{"op":"self"}` — 対象を自分へ〔〕
38. `{"op":"buff","e":"luck","t":100,"a":123}` — 強化〔e="luck", t=100, a=123〕
39. `{"op":"fx","p":"end_rod","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="end_rod", n=16, at="ring", r=3.7, y=0.55〕
40. `{"op":"self"}` — 対象を自分へ〔〕
41. `{"op":"cleanse"}` — 状態異常解除〔〕
42. `{"op":"guard","t":100}` — 防御〔t=100〕
43. `{"op":"reflect","t":100,"r":9}` — 反射〔t=100, r=9〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 敗北転換の栞 — 神格装飾品（Curios relic_charm） (`mary_sue_charm`)

**現行パラメータ**：rank=1、damage登録値=69.6762、relics側CD=180tick、art側CD=180tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（11命令）**：

01. `{"op":"low","pct":0.25,"ops":[{"op":"self"},{"op":"buff","e":"regen","t":40,"a":4},{"op":"buff","e":"resist","t":40,"a":3}]}` — low〔pct=0.25, ops=[{"op":"self"},{"op":"buff","e":"regen","t":40,"a":4},{"op":"buff","e":"resist","t":40,"a":3}]〕
02. `{"op":"self"}` — 対象を自分へ〔〕
03. `{"op":"buff","e":"strength","t":45,"a":0}` — 強化〔e="strength", t=45, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
06. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
07. `{"op":"buff","e":"strength","t":45,"a":1}` — 強化〔e="strength", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"luck","t":42,"a":2}` — 強化〔e="luck", t=42, a=2〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"resist","t":48,"a":3}` — 強化〔e="resist", t=48, a=3〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（37命令）**：

01. `{"op":"fx","p":"firework","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="firework", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"firework","n":4,"at":"self","s":0.7}` — 粒子演出〔p="firework", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"enchant","n":60,"at":"self"}` — 粒子演出〔p="enchant", n=60, at="self"〕
04. `{"op":"fx","p":"end_rod","n":20,"at":"self"}` — 粒子演出〔p="end_rod", n=20, at="self"〕
05. `{"op":"sound","s":"totem","v":0.5,"pi":1.6}` — 効果音〔s="totem", v=0.5, pi=1.6〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"undying","t":100}` — 死亡防護〔t=100〕
08. `{"op":"guard","t":40}` — 防御〔t=40〕
09. `{"op":"cleanse"}` — 状態異常解除〔〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"strength","t":210,"a":1}` — 強化〔e="strength", t=210, a=1〕
13. `{"op":"fx","p":"end_rod","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="end_rod", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"firework","n":36,"at":"line","r":24}` — 粒子演出〔p="firework", n=36, at="line", r=24〕
15. `{"op":"sound","s":"totem","v":1.05,"pi":1.14}` — 効果音〔s="totem", v=1.05, pi=1.14〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"guard","t":95}` — 防御〔t=95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
20. `{"op":"cleanse"}` — 状態異常解除〔〕
21. `{"op":"buff","e":"strength","t":180,"a":3}` — 強化〔e="strength", t=180, a=3〕
22. `{"op":"guard","t":95}` — 防御〔t=95〕
23. `{"op":"fx","p":"end_rod","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="end_rod", n=30, at="ring", r=4.0, y=0.7〕
24. `{"op":"sound","s":"totem","v":0.8,"pi":1.1}` — 効果音〔s="totem", v=0.8, pi=1.1〕
25. `{"op":"self"}` — 対象を自分へ〔〕
26. `{"op":"buff","e":"luck","t":300,"a":4}` — 強化〔e="luck", t=300, a=4〕
27. `{"op":"guard","t":155}` — 防御〔t=155〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"guard","t":130}` — 防御〔t=130〕
30. `{"op":"fx","p":"end_rod","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="end_rod", n=20, at="ring", r=4, y=0.4〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"luck","t":160,"a":123}` — 強化〔e="luck", t=160, a=123〕
33. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
34. `{"op":"eff","e":"fatigue","t":110,"a":123}` — 敵への状態異常〔e="fatigue", t=110, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"guard","t":95}` — 防御〔t=95〕
37. `{"op":"cleanse"}` — 状態異常解除〔〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 物語永続・無限覚醒 — 超越神器（武器欄） (`mary_sue_legend`)

**現行パラメータ**：rank=3、damage登録値=1157.875、relics側CD=335tick、art側CD=335tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"low","pct":0.5,"ops":[{"op":"self"},{"op":"undying","t":40}]}` — low〔pct=0.5, ops=[{"op":"self"},{"op":"undying","t":40}]〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
08. `{"op":"buff","e":"strength","t":45,"a":3}` — 強化〔e="strength", t=45, a=3〕
09. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（7命令）**：

01. `{"op":"low","pct":0.5,"ops":[{"op":"victim"},{"op":"dmg","m":1.0}]}` — low〔pct=0.5, ops=[{"op":"victim"},{"op":"dmg","m":1.0}]〕
02. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"glow","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"glow","t":160,"a":1}]〕
03. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
04. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"end_rod","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"end_rod","n":10,"at":"t","s":0.35}]〕
05. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
06. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":20,"at":"t","s":0.33},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":20,"at":"t","s":0.33},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":160,"x":2.5}]〕
07. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]〕

**権能発動時の命令（26命令）**：

01. `{"op":"fx","p":"firework","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="firework", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"firework","n":4,"at":"self","s":0.7}` — 粒子演出〔p="firework", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"enchant","n":60,"at":"self"}` — 粒子演出〔p="enchant", n=60, at="self"〕
04. `{"op":"fx","p":"end_rod","n":20,"at":"self"}` — 粒子演出〔p="end_rod", n=20, at="self"〕
05. `{"op":"sound","s":"totem","v":0.5,"pi":1.6}` — 効果音〔s="totem", v=0.5, pi=1.6〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"undying","t":180}` — 死亡防護〔t=180〕
08. `{"op":"healpct","v":0.6}` — 最大HP割合回復〔v=0.6〕
09. `{"op":"cleanse"}` — 状態異常解除〔〕
10. `{"op":"buff","e":"health","t":2400,"a":9}` — 強化〔e="health", t=2400, a=9〕
11. `{"op":"buff","e":"strength","t":1200,"a":12}` — 強化〔e="strength", t=1200, a=12〕
12. `{"op":"buff","e":"absorb","t":1200,"a":9}` — 強化〔e="absorb", t=1200, a=9〕
13. `{"op":"area","r":40,"n":36}` — 円形対象の取得〔r=40, n=36〕
14. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
15. `{"op":"stun","t":105}` — 行動停止〔t=105〕
16. `{"op":"fx","p":"end_rod","n":12,"at":"t","s":0.5}` — 粒子演出〔p="end_rod", n=12, at="t", s=0.5〕
17. `{"op":"self"}` — 対象を自分へ〔〕
18. `{"op":"guard","t":135}` — 防御〔t=135〕
19. `{"op":"cleanse"}` — 状態異常解除〔〕
20. `{"op":"buff","e":"resist","a":2,"t":140}` — 強化〔e="resist", a=2, t=140〕
21. `{"op":"fx","p":"firework","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="firework", n=50, at="ring", r=8.0, y=0.6〕
22. `{"op":"fx","p":"happy","n":32,"at":"line","r":30}` — 粒子演出〔p="happy", n=32, at="line", r=30〕
23. `{"op":"sound","s":"totem","v":1.15,"pi":0.95}` — 効果音〔s="totem", v=1.15, pi=0.95〕
24. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.mary_sue_legend.stage0","ops":[{"op":"fx","p":"end_rod","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"totem","v":0.9,"pi":1.2},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"firework","n":6,"at":"line","r":10},{"op":"fx","p":"end_rod","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"firework","n":36,"at":"line","r":24},{"op":"sound","s":"totem","v":1.05,"pi":1.14},{"op":"line","r":53.0,"w":3.0},{"op":"dmg","m":4.185},{"op":"mark","t":115,"x":1.95},{"op":"self"},{"op":"buff","e":"luck","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.mary_sue_legend.stage1","ops":[{"op":"fx","p":"end_rod","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"totem","v":1.05,"pi":1.0},{"op":"fx","p":"firework","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":15},{"op":"fx","p":"firework","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"happy","n":32,"at":"line","r":30},{"op":"sound","s":"totem","v":1.15,"pi":0.95},{"op":"allies","r":24.0},{"op":"healpct","v":0.35},{"op":"cleanse"},{"op":"self"},{"op":"guard","t":115},{"op":"area","r":20.0,"n":10},{"op":"eff","e":"glow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.mary_sue_legend.stage2","ops":[{"op":"fx","p":"end_rod","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"totem","v":1.25,"pi":0.75},{"op":"fx","p":"firework","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"end_rod","n":10,"at":"line","r":20},{"op":"fx","p":"end_rod","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"firework","n":48,"at":"line","r":48},{"op":"fx","p":"happy","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"totem","v":1.5,"pi":0.75},{"op":"area","r":32.0,"n":28},{"op":"dmg","m":9.234},{"op":"strip"},{"op":"self"},{"op":"buff","e":"strength","t":200,"a":4},{"op":"buff","e":"regen","t":170,"a":3},{"op":"fx","p":"happy","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"end_rod","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":30.0,"n":26},{"op":"dmg","m":2.8},{"op":"allies","r":26.0},{"op":"healpct","v":0.4},{"op":"cleanse"},{"op":"self"},{"op":"buff","e":"strength","t":180,"a":4},{"op":"line","r":41.0,"w":4.0},{"op":"dmg","m":1.2},{"op":"eff","e":"glow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"luck","t":240,"a":4},{"op":"self"},{"op":"guard","t":130},{"op":"fx","p":"end_rod","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"totem","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"self"},{"op":"cleanse"},{"op":"guard","t":105},{"op":"area","r":17,"n":8},{"op":"strip"}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.mary_sue_legend.stage0","ops":[{"op":"fx","p":"end_rod","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"totem","v":0.9,"pi":1.2},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"firework","n":6,"at":"line","r":10},{"op":"fx","p":"end_rod","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"firework","n":36,"at":"line","r":24},{"op":"sound","s":"totem","v":1.05,"pi":1.14},{"op":"line","r":53.0,"w":3.0},{"op":"dmg","m":4.185},{"op":"mark","t":115,"x":1.95},{"op":"self"},{"op":"buff","e":"luck","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.mary_sue_legend.stage1","ops":[{"op":"fx","p":"end_rod","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"totem","v":1.05,"pi":1.0},{"op":"fx","p":"firework","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":15},{"op":"fx","p":"firework","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"happy","n":32,"at":"line","r":30},{"op":"sound","s":"totem","v":1.15,"pi":0.95},{"op":"allies","r":24.0},{"op":"healpct","v":0.35},{"op":"cleanse"},{"op":"self"},{"op":"guard","t":115},{"op":"area","r":20.0,"n":10},{"op":"eff","e":"glow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.mary_sue_legend.stage2","ops":[{"op":"fx","p":"end_rod","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"totem","v":1.25,"pi":0.75},{"op":"fx","p":"firework","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"end_rod","n":10,"at":"line","r":20},{"op":"fx","p":"end_rod","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"firework","n":48,"at":"line","r":48},{"op":"fx","p":"happy","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"totem","v":1.5,"pi":0.75},{"op":"area","r":32.0,"n":28},{"op":"dmg","m":9.234},{"op":"strip"},{"op":"self"},{"op":"buff","e":"strength","t":200,"a":4},{"op":"buff","e":"regen","t":170,"a":3},{"op":"fx","p":"happy","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"end_rod","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":30.0,"n":26},{"op":"dmg","m":2.8},{"op":"allies","r":26.0},{"op":"healpct","v":0.4},{"op":"cleanse"},{"op":"self"},{"op":"buff","e":"strength","t":180,"a":4},{"op":"line","r":41.0,"w":4.0},{"op":"dmg","m":1.2},{"op":"eff","e":"glow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"luck","t":240,"a":4},{"op":"self"},{"op":"guard","t":130},{"op":"fx","p":"end_rod","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"totem","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"self"},{"op":"cleanse"},{"op":"guard","t":105},{"op":"area","r":17,"n":8},{"op":"strip"}]}]〕
25. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
26. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 16. 救世天主 セイヴァー

**モブ側の動きの方向性**：光翼を多数の仲間へ向けて独立展開し、救出と庇護を行う。。

### 救世の聖盾 — 討伐武器（メイン／武器欄） (`savior_weapon`)

**現行パラメータ**：rank=1、damage登録値=462.0、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:knockback:4、minecraft:thorns:15。

**装備中の常時命令（6命令）**：

01. `{"op":"allies","r":12}` — 味方対象〔r=12〕
02. `{"op":"buff","e":"regen","t":40,"a":0,"to":1}` — 強化〔e="regen", t=40, a=0, to=1〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"resist","t":40,"a":1}` — 強化〔e="resist", t=40, a=1〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（8命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"knock","f":2.0}` — knock〔f=2.0〕
03. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"weakness","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"weakness","t":90,"a":0}]〕
04. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"fx","p":"heart","n":9,"at":"t","s":0.24},{"op":"mark","t":120,"x":1.65},{"op":"eff","e":"weakness","t":91,"a":0}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"fx","p":"heart","n":9,"at":"t","s":0.24},{"op":"mark","t":120,"x":1.65},{"op":"eff","e":"weakness","t":91,"a":0}]〕
05. `{"op":"chance","p":0.15,"ops":[{"op":"victim"},{"op":"dmg","m":0.2}]}` — 抽選〔p=0.15, ops=[{"op":"victim"},{"op":"dmg","m":0.2}]〕
06. `{"op":"chance","p":0.142,"ops":[{"op":"victim"},{"op":"fx","p":"heart","n":8,"at":"t","s":0.25},{"op":"self"},{"op":"healpct","v":0.07}]}` — 抽選〔p=0.142, ops=[{"op":"victim"},{"op":"fx","p":"heart","n":8,"at":"t","s":0.25},{"op":"self"},{"op":"healpct","v":0.07}]〕
07. `{"op":"chance","p":0.18,"ops":[{"op":"victim"},{"op":"fx","p":"heart","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.18, ops=[{"op":"victim"},{"op":"fx","p":"heart","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]〕
08. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"heart","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"heart","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]〕

**権能発動時の命令（30命令）**：

01. `{"op":"fx","p":"heart","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="heart", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"heart","n":4,"at":"self","s":0.7}` — 粒子演出〔p="heart", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":50,"at":"ring","r":3.5,"y":0.2}` — 粒子演出〔p="end_rod", n=50, at="ring", r=3.5, y=0.2〕
04. `{"op":"fx","p":"end_rod","n":30,"at":"self"}` — 粒子演出〔p="end_rod", n=30, at="self"〕
05. `{"op":"sound","s":"totem","v":0.6,"pi":1.4}` — 効果音〔s="totem", v=0.6, pi=1.4〕
06. `{"op":"allies","r":24}` — 味方対象〔r=24〕
07. `{"op":"healpct","v":0.25,"to":1}` — 最大HP割合回復〔v=0.25, to=1〕
08. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
09. `{"op":"guard","t":60,"to":1}` — 防御〔t=60, to=1〕
10. `{"op":"buff","e":"absorb","t":400,"a":4,"to":1}` — 強化〔e="absorb", t=400, a=4, to=1〕
11. `{"op":"area","r":16,"n":36}` — 円形対象の取得〔r=16, n=36〕
12. `{"op":"knock","f":3.0}` — knock〔f=3.0〕
13. `{"op":"erase","r":24}` — erase〔r=24〕
14. `{"op":"fx","p":"end_rod","n":12,"at":"t","s":0.5}` — 粒子演出〔p="end_rod", n=12, at="t", s=0.5〕
15. `{"op":"fx","p":"heart","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="heart", n=46, at="ring", r=5.5, y=0.25〕
16. `{"op":"fx","p":"end_rod","n":36,"at":"line","r":24}` — 粒子演出〔p="end_rod", n=36, at="line", r=24〕
17. `{"op":"allies","r":24.0}` — 味方対象〔r=24.0〕
18. `{"op":"healpct","v":0.35}` — 最大HP割合回復〔v=0.35〕
19. `{"op":"cleanse"}` — 状態異常解除〔〕
20. `{"op":"self"}` — 対象を自分へ〔〕
21. `{"op":"guard","t":95}` — 防御〔t=95〕
22. `{"op":"fx","p":"heart","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="heart", n=16, at="ring", r=5.0〕
23. `{"op":"sound","s":"spell","v":0.75,"pi":1.15}` — 効果音〔s="spell", v=0.75, pi=1.15〕
24. `{"op":"area","r":9,"n":8}` — 円形対象の取得〔r=9, n=8〕
25. `{"op":"dmg","m":0.9}` — 追加攻撃〔m=0.9〕
26. `{"op":"eff","e":"weakness","t":65,"a":0}` — 敵への状態異常〔e="weakness", t=65, a=0〕
27. `{"op":"fx","p":"heart","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="heart", n=24, at="ring", r=4.5, y=0.6〕
28. `{"op":"sound","s":"totem","v":0.8,"pi":0.8}` — 効果音〔s="totem", v=0.8, pi=0.8〕
29. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
30. `{"op":"eff","e":"weakness","t":100,"a":124}` — 敵への状態異常〔e="weakness", t=100, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 慈愛の祈祷杖 — 神威触媒（Curios relic_focus） (`savior_focus`)

**現行パラメータ**：rank=2、damage登録値=68.31、relics側CD=145tick、art側CD=145tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"allies","r":16}` — 味方対象〔r=16〕
02. `{"op":"buff","e":"regen","t":40,"a":0,"to":1}` — 強化〔e="regen", t=40, a=0, to=1〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"regen","t":45,"a":0}` — 強化〔e="regen", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"regen","t":42,"a":2}` — 強化〔e="regen", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（43命令）**：

01. `{"op":"fx","p":"heart","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="heart", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"heart","n":6,"at":"self","s":0.7}` — 粒子演出〔p="heart", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":50,"at":"ring","r":3.5,"y":0.2}` — 粒子演出〔p="end_rod", n=50, at="ring", r=3.5, y=0.2〕
04. `{"op":"fx","p":"end_rod","n":30,"at":"self"}` — 粒子演出〔p="end_rod", n=30, at="self"〕
05. `{"op":"sound","s":"totem","v":0.6,"pi":1.4}` — 効果音〔s="totem", v=0.6, pi=1.4〕
06. `{"op":"allies","r":32}` — 味方対象〔r=32〕
07. `{"op":"healpct","v":0.4,"to":1}` — 最大HP割合回復〔v=0.4, to=1〕
08. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
09. `{"op":"buff","e":"regen","t":600,"a":3,"to":1}` — 強化〔e="regen", t=600, a=3, to=1〕
10. `{"op":"buff","e":"health","t":1200,"a":2,"to":1}` — 強化〔e="health", t=1200, a=2, to=1〕
11. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"regen","t":150,"a":1}` — 強化〔e="regen", t=150, a=1〕
14. `{"op":"fx","p":"end_rod","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="end_rod", n=50, at="ring", r=8.0, y=0.6〕
15. `{"op":"fx","p":"happy","n":32,"at":"line","r":30}` — 粒子演出〔p="happy", n=32, at="line", r=30〕
16. `{"op":"sound","s":"totem","v":1.15,"pi":0.95}` — 効果音〔s="totem", v=1.15, pi=0.95〕
17. `{"op":"area","r":22.0,"n":16}` — 円形対象の取得〔r=22.0, n=16〕
18. `{"op":"dmg","m":2.2}` — 追加攻撃〔m=2.2〕
19. `{"op":"eff","e":"weakness","t":105,"a":1}` — 敵への状態異常〔e="weakness", t=105, a=1〕
20. `{"op":"allies","r":22.0}` — 味方対象〔r=22.0〕
21. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
22. `{"op":"self"}` — 対象を自分へ〔〕
23. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
24. `{"op":"buff","e":"regen","t":150,"a":3}` — 強化〔e="regen", t=150, a=3〕
25. `{"op":"fx","p":"heart","n":24,"at":"ring","r":10,"y":0.5}` — 粒子演出〔p="heart", n=24, at="ring", r=10, y=0.5〕
26. `{"op":"sound","s":"totem","v":0.85,"pi":0.9}` — 効果音〔s="totem", v=0.85, pi=0.9〕
27. `{"op":"allies","r":18.0}` — 味方対象〔r=18.0〕
28. `{"op":"healpct","v":0.14,"to":1}` — 最大HP割合回復〔v=0.14, to=1〕
29. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"regen","t":200,"a":3}` — 強化〔e="regen", t=200, a=3〕
32. `{"op":"allies","r":30.0}` — 味方対象〔r=30.0〕
33. `{"op":"healpct","v":0.14,"to":1}` — 最大HP割合回復〔v=0.14, to=1〕
34. `{"op":"fx","p":"heart","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="heart", n=24, at="ring", r=5.5, y=0.7〕
35. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
36. `{"op":"eff","e":"weakness","t":135,"a":123}` — 敵への状態異常〔e="weakness", t=135, a=123〕
37. `{"op":"self"}` — 対象を自分へ〔〕
38. `{"op":"buff","e":"regen","t":140,"a":7}` — 強化〔e="regen", t=140, a=7〕
39. `{"op":"fx","p":"heart","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="heart", n=16, at="ring", r=3.7, y=0.55〕
40. `{"op":"allies","r":18.0}` — 味方対象〔r=18.0〕
41. `{"op":"healpct","v":0.24}` — 最大HP割合回復〔v=0.24〕
42. `{"op":"cleanse"}` — 状態異常解除〔〕
43. `{"op":"buff","e":"regen","t":130,"a":3}` — 強化〔e="regen", t=130, a=3〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 避難聖域の護符 — 神格装飾品（Curios relic_charm） (`savior_charm`)

**現行パラメータ**：rank=1、damage登録値=68.31、relics側CD=175tick、art側CD=175tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（12命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"reflect","t":25,"r":6}` — 反射〔t=25, r=6〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"regen","t":45,"a":0}` — 強化〔e="regen", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"regen","t":42,"a":2}` — 強化〔e="regen", t=42, a=2〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"regen","t":48,"a":5}` — 強化〔e="regen", t=48, a=5〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（38命令）**：

01. `{"op":"fx","p":"heart","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="heart", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"heart","n":4,"at":"self","s":0.7}` — 粒子演出〔p="heart", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":50,"at":"ring","r":3.5,"y":0.2}` — 粒子演出〔p="end_rod", n=50, at="ring", r=3.5, y=0.2〕
04. `{"op":"fx","p":"end_rod","n":30,"at":"self"}` — 粒子演出〔p="end_rod", n=30, at="self"〕
05. `{"op":"sound","s":"totem","v":0.6,"pi":1.4}` — 効果音〔s="totem", v=0.6, pi=1.4〕
06. `{"op":"allies","r":20}` — 味方対象〔r=20〕
07. `{"op":"guard","t":100,"to":1}` — 防御〔t=100, to=1〕
08. `{"op":"area","r":20,"n":36}` — 円形対象の取得〔r=20, n=36〕
09. `{"op":"knock","f":4.0}` — knock〔f=4.0〕
10. `{"op":"erase","r":32}` — erase〔r=32〕
11. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"regen","t":210,"a":1}` — 強化〔e="regen", t=210, a=1〕
14. `{"op":"fx","p":"heart","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="heart", n=46, at="ring", r=5.5, y=0.25〕
15. `{"op":"fx","p":"end_rod","n":36,"at":"line","r":24}` — 粒子演出〔p="end_rod", n=36, at="line", r=24〕
16. `{"op":"sound","s":"totem","v":1.05,"pi":1.14}` — 効果音〔s="totem", v=1.05, pi=1.14〕
17. `{"op":"self"}` — 対象を自分へ〔〕
18. `{"op":"guard","t":95}` — 防御〔t=95〕
19. `{"op":"self"}` — 対象を自分へ〔〕
20. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
21. `{"op":"cleanse"}` — 状態異常解除〔〕
22. `{"op":"buff","e":"regen","t":180,"a":3}` — 強化〔e="regen", t=180, a=3〕
23. `{"op":"guard","t":95}` — 防御〔t=95〕
24. `{"op":"fx","p":"heart","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="heart", n=30, at="ring", r=4.0, y=0.7〕
25. `{"op":"sound","s":"totem","v":0.8,"pi":1.1}` — 効果音〔s="totem", v=0.8, pi=1.1〕
26. `{"op":"self"}` — 対象を自分へ〔〕
27. `{"op":"buff","e":"regen","t":260,"a":4}` — 強化〔e="regen", t=260, a=4〕
28. `{"op":"guard","t":170}` — 防御〔t=170〕
29. `{"op":"allies","r":30.0}` — 味方対象〔r=30.0〕
30. `{"op":"healpct","v":0.14,"to":1}` — 最大HP割合回復〔v=0.14, to=1〕
31. `{"op":"fx","p":"heart","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="heart", n=20, at="ring", r=4, y=0.4〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"buff","e":"regen","t":140,"a":7}` — 強化〔e="regen", t=140, a=7〕
34. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
35. `{"op":"eff","e":"weakness","t":100,"a":123}` — 敵への状態異常〔e="weakness", t=100, a=123〕
36. `{"op":"allies","r":16}` — 味方対象〔r=16〕
37. `{"op":"healpct","v":0.18}` — 最大HP割合回復〔v=0.18〕
38. `{"op":"cleanse"}` — 状態異常解除〔〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 万命救済・最後の聖域 — 超越神器（武器欄） (`savior_legend`)

**現行パラメータ**：rank=3、damage登録値=925.5、relics側CD=330tick、art側CD=330tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:knockback:4、minecraft:thorns:15。

**装備中の常時命令（11命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"allies","r":16}` — 味方対象〔r=16〕
06. `{"op":"buff","e":"regen","t":40,"a":1,"to":1}` — 強化〔e="regen", t=40, a=1, to=1〕
07. `{"op":"reflect","t":25,"r":8}` — 反射〔t=25, r=8〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
10. `{"op":"buff","e":"regen","t":45,"a":3}` — 強化〔e="regen", t=45, a=3〕
11. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（9命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"knock","f":3.0}` — knock〔f=3.0〕
03. `{"op":"stun","t":20}` — 行動停止〔t=20〕
04. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"weakness","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"weakness","t":160,"a":1}]〕
05. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"heart","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"heart","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
06. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"heart","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"heart","n":10,"at":"t","s":0.35}]〕
07. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
08. `{"op":"chance","p":0.3,"ops":[{"op":"victim"},{"op":"fx","p":"heart","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.3, ops=[{"op":"victim"},{"op":"fx","p":"heart","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]〕
09. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"heart","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"heart","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]〕

**権能発動時の命令（27命令）**：

01. `{"op":"fx","p":"heart","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="heart", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"heart","n":4,"at":"self","s":0.7}` — 粒子演出〔p="heart", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":50,"at":"ring","r":3.5,"y":0.2}` — 粒子演出〔p="end_rod", n=50, at="ring", r=3.5, y=0.2〕
04. `{"op":"fx","p":"end_rod","n":30,"at":"self"}` — 粒子演出〔p="end_rod", n=30, at="self"〕
05. `{"op":"sound","s":"totem","v":0.6,"pi":1.4}` — 効果音〔s="totem", v=0.6, pi=1.4〕
06. `{"op":"allies","r":48}` — 味方対象〔r=48〕
07. `{"op":"healpct","v":0.6,"to":1}` — 最大HP割合回復〔v=0.6, to=1〕
08. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
09. `{"op":"guard","t":180,"to":1}` — 防御〔t=180, to=1〕
10. `{"op":"undying","t":180,"to":1}` — 死亡防護〔t=180, to=1〕
11. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
12. `{"op":"knock","f":5.0}` — knock〔f=5.0〕
13. `{"op":"stun","t":105}` — 行動停止〔t=105〕
14. `{"op":"dmg","m":2.24}` — 追加攻撃〔m=2.24〕
15. `{"op":"erase","r":64}` — erase〔r=64〕
16. `{"op":"fx","p":"end_rod","n":12,"at":"t","s":0.5}` — 粒子演出〔p="end_rod", n=12, at="t", s=0.5〕
17. `{"op":"allies","r":26}` — 味方対象〔r=26〕
18. `{"op":"healpct","v":0.35}` — 最大HP割合回復〔v=0.35〕
19. `{"op":"cleanse"}` — 状態異常解除〔〕
20. `{"op":"self"}` — 対象を自分へ〔〕
21. `{"op":"buff","e":"regen","t":200,"a":2}` — 強化〔e="regen", t=200, a=2〕
22. `{"op":"fx","p":"end_rod","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="end_rod", n=50, at="ring", r=8.0, y=0.6〕
23. `{"op":"fx","p":"happy","n":32,"at":"line","r":30}` — 粒子演出〔p="happy", n=32, at="line", r=30〕
24. `{"op":"sound","s":"totem","v":1.15,"pi":0.95}` — 効果音〔s="totem", v=1.15, pi=0.95〕
25. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.savior_legend.stage0","ops":[{"op":"fx","p":"heart","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"totem","v":0.9,"pi":1.2},{"op":"fx","p":"heart","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":10},{"op":"fx","p":"heart","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"end_rod","n":36,"at":"line","r":24},{"op":"sound","s":"totem","v":1.05,"pi":1.14},{"op":"allies","r":24.0},{"op":"healpct","v":0.35},{"op":"cleanse"},{"op":"self"},{"op":"guard","t":95},{"op":"self"},{"op":"buff","e":"regen","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.savior_legend.stage1","ops":[{"op":"fx","p":"heart","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"totem","v":1.05,"pi":1.0},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"heart","n":6,"at":"line","r":15},{"op":"fx","p":"end_rod","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"happy","n":32,"at":"line","r":30},{"op":"sound","s":"totem","v":1.15,"pi":0.95},{"op":"area","r":22.0,"n":16},{"op":"dmg","m":3.19},{"op":"eff","e":"weakness","t":105,"a":1},{"op":"allies","r":22.0},{"op":"healpct","v":0.3},{"op":"area","r":12.0,"n":10},{"op":"eff","e":"weakness","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.savior_legend.stage2","ops":[{"op":"fx","p":"heart","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"totem","v":1.25,"pi":0.75},{"op":"fx","p":"end_rod","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"heart","n":10,"at":"line","r":20},{"op":"fx","p":"heart","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"end_rod","n":48,"at":"line","r":48},{"op":"fx","p":"happy","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"totem","v":1.5,"pi":0.75},{"op":"allies","r":36.0},{"op":"healpct","v":0.6},{"op":"cleanse"},{"op":"self"},{"op":"guard","t":170},{"op":"undying","t":140},{"op":"area","r":28.0,"n":20},{"op":"dmg","m":7.29},{"op":"fx","p":"happy","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"heart","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":26.0,"n":22},{"op":"dmg","m":2.3},{"op":"allies","r":34.0},{"op":"healpct","v":0.75},{"op":"cleanse"},{"op":"self"},{"op":"guard","t":125},{"op":"allies","r":34.0},{"op":"healpct","v":0.28,"to":1},{"op":"cleanse","to":1},{"op":"self"},{"op":"guard","t":180},{"op":"allies","r":28.0},{"op":"guard","t":125,"to":1},{"op":"fx","p":"heart","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"totem","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"allies","r":22},{"op":"healpct","v":0.24},{"op":"cleanse"},{"op":"guard","t":110}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.savior_legend.stage0","ops":[{"op":"fx","p":"heart","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"totem","v":0.9,"pi":1.2},{"op":"fx","p":"heart","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":10},{"op":"fx","p":"heart","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"end_rod","n":36,"at":"line","r":24},{"op":"sound","s":"totem","v":1.05,"pi":1.14},{"op":"allies","r":24.0},{"op":"healpct","v":0.35},{"op":"cleanse"},{"op":"self"},{"op":"guard","t":95},{"op":"self"},{"op":"buff","e":"regen","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.savior_legend.stage1","ops":[{"op":"fx","p":"heart","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"totem","v":1.05,"pi":1.0},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"heart","n":6,"at":"line","r":15},{"op":"fx","p":"end_rod","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"happy","n":32,"at":"line","r":30},{"op":"sound","s":"totem","v":1.15,"pi":0.95},{"op":"area","r":22.0,"n":16},{"op":"dmg","m":3.19},{"op":"eff","e":"weakness","t":105,"a":1},{"op":"allies","r":22.0},{"op":"healpct","v":0.3},{"op":"area","r":12.0,"n":10},{"op":"eff","e":"weakness","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.savior_legend.stage2","ops":[{"op":"fx","p":"heart","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"totem","v":1.25,"pi":0.75},{"op":"fx","p":"end_rod","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"heart","n":10,"at":"line","r":20},{"op":"fx","p":"heart","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"end_rod","n":48,"at":"line","r":48},{"op":"fx","p":"happy","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"totem","v":1.5,"pi":0.75},{"op":"allies","r":36.0},{"op":"healpct","v":0.6},{"op":"cleanse"},{"op":"self"},{"op":"guard","t":170},{"op":"undying","t":140},{"op":"area","r":28.0,"n":20},{"op":"dmg","m":7.29},{"op":"fx","p":"happy","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"heart","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":26.0,"n":22},{"op":"dmg","m":2.3},{"op":"allies","r":34.0},{"op":"healpct","v":0.75},{"op":"cleanse"},{"op":"self"},{"op":"guard","t":125},{"op":"allies","r":34.0},{"op":"healpct","v":0.28,"to":1},{"op":"cleanse","to":1},{"op":"self"},{"op":"guard","t":180},{"op":"allies","r":28.0},{"op":"guard","t":125,"to":1},{"op":"fx","p":"heart","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"totem","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"allies","r":22},{"op":"healpct","v":0.24},{"op":"cleanse"},{"op":"guard","t":110}]}]〕
26. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
27. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 17. 外業呪禍 獄華

**モブ側の動きの方向性**：怨霊の流出と封印の両方向を身体表面で表す。。

### 外業呪禍の鉤爪 — 討伐武器（メイン／武器欄） (`gokuka_weapon`)

**現行パラメータ**：rank=1、damage登録値=384.33333、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:fire_aspect:10。

**装備中の常時命令（4命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"night","t":300,"a":0}` — 強化〔e="night", t=300, a=0〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（9命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"eff","e":"wither","t":100,"a":2}` — 敵への状態異常〔e="wither", t=100, a=2〕
03. `{"op":"eff","e":"poison","t":100,"a":2}` — 敵への状態異常〔e="poison", t=100, a=2〕
04. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"wither","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"wither","t":90,"a":0}]〕
05. `{"op":"chance","p":0.485,"ops":[{"op":"victim"},{"op":"fx","p":"soul","n":11,"at":"t","s":0.24},{"op":"mark","t":140,"x":1.79},{"op":"eff","e":"wither","t":103,"a":0}]}` — 抽選〔p=0.485, ops=[{"op":"victim"},{"op":"fx","p":"soul","n":11,"at":"t","s":0.24},{"op":"mark","t":140,"x":1.79},{"op":"eff","e":"wither","t":103,"a":0}]〕
06. `{"op":"chance","p":0.177,"ops":[{"op":"victim"},{"op":"dmg","m":0.235}]}` — 抽選〔p=0.177, ops=[{"op":"victim"},{"op":"dmg","m":0.235}]〕
07. `{"op":"chance","p":0.085,"ops":[{"op":"victim"},{"op":"fx","p":"soul","n":8,"at":"t","s":0.25},{"op":"eff","e":"poison","t":55,"a":0}]}` — 抽選〔p=0.085, ops=[{"op":"victim"},{"op":"fx","p":"soul","n":8,"at":"t","s":0.25},{"op":"eff","e":"poison","t":55,"a":0}]〕
08. `{"op":"chance","p":0.2,"ops":[{"op":"victim"},{"op":"fx","p":"soul","n":14,"at":"t","s":0.28},{"op":"eff","e":"wither","t":22,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.2, ops=[{"op":"victim"},{"op":"fx","p":"soul","n":14,"at":"t","s":0.28},{"op":"eff","e":"wither","t":22,"a":124},{"op":"mark","t":100,"x":2.15}]〕
09. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"witch","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"witch","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]〕

**権能発動時の命令（27命令）**：

01. `{"op":"fx","p":"witch","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="witch", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"witch","n":4,"at":"self","s":0.7}` — 粒子演出〔p="witch", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"sculk","n":30,"at":"self","s":1.2}` — 粒子演出〔p="sculk", n=30, at="self", s=1.2〕
04. `{"op":"fx","p":"witch","n":30,"at":"self"}` — 粒子演出〔p="witch", n=30, at="self"〕
05. `{"op":"sound","s":"wither","v":0.6,"pi":0.8}` — 効果音〔s="wither", v=0.6, pi=0.8〕
06. `{"op":"cone","r":12,"a":120}` — 扇形対象の取得〔r=12, a=120〕
07. `{"op":"dmg","m":1.68}` — 追加攻撃〔m=1.68〕
08. `{"op":"eff","e":"wither","t":400,"a":4}` — 敵への状態異常〔e="wither", t=400, a=4〕
09. `{"op":"eff","e":"poison","t":400,"a":4}` — 敵への状態異常〔e="poison", t=400, a=4〕
10. `{"op":"eff","e":"weakness","t":400,"a":3}` — 敵への状態異常〔e="weakness", t=400, a=3〕
11. `{"op":"eff","e":"hunger","t":400,"a":5}` — 敵への状態異常〔e="hunger", t=400, a=5〕
12. `{"op":"summon","k":"wolf","n":2}` — 召喚〔k="wolf", n=2〕
13. `{"op":"fx","p":"sculk","n":12,"at":"t","s":0.5}` — 粒子演出〔p="sculk", n=12, at="t", s=0.5〕
14. `{"op":"fx","p":"soul","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="soul", n=46, at="ring", r=5.5, y=0.25〕
15. `{"op":"fx","p":"witch","n":36,"at":"line","r":24}` — 粒子演出〔p="witch", n=36, at="line", r=24〕
16. `{"op":"area","r":23.0,"n":18}` — 円形対象の取得〔r=23.0, n=18〕
17. `{"op":"dmg","m":2.4}` — 追加攻撃〔m=2.4〕
18. `{"op":"eff","e":"wither","t":110,"a":1}` — 敵への状態異常〔e="wither", t=110, a=1〕
19. `{"op":"fx","p":"witch","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="witch", n=16, at="ring", r=5.0〕
20. `{"op":"sound","s":"sonic","v":0.75,"pi":1.15}` — 効果音〔s="sonic", v=0.75, pi=1.15〕
21. `{"op":"cone","r":11,"a":85}` — 扇形対象の取得〔r=11, a=85〕
22. `{"op":"dmg","m":1.0}` — 追加攻撃〔m=1.0〕
23. `{"op":"eff","e":"wither","t":65,"a":0}` — 敵への状態異常〔e="wither", t=65, a=0〕
24. `{"op":"fx","p":"soul","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="soul", n=24, at="ring", r=4.5, y=0.6〕
25. `{"op":"sound","s":"wither","v":0.8,"pi":0.8}` — 効果音〔s="wither", v=0.8, pi=0.8〕
26. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
27. `{"op":"eff","e":"wither","t":22,"a":124}` — 敵への状態異常〔e="wither", t=22, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 分御霊の黒液瓶 — 神威触媒（Curios relic_focus） (`gokuka_focus`)

**現行パラメータ**：rank=2、damage登録値=69.6762、relics側CD=160tick、art側CD=160tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"regen","t":40,"a":0}` — 強化〔e="regen", t=40, a=0〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"resist","t":45,"a":0}` — 強化〔e="resist", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"regen","t":42,"a":2}` — 強化〔e="regen", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（42命令）**：

01. `{"op":"fx","p":"witch","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="witch", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"witch","n":6,"at":"self","s":0.7}` — 粒子演出〔p="witch", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"sculk","n":30,"at":"self","s":1.2}` — 粒子演出〔p="sculk", n=30, at="self", s=1.2〕
04. `{"op":"fx","p":"witch","n":30,"at":"self"}` — 粒子演出〔p="witch", n=30, at="self"〕
05. `{"op":"sound","s":"wither","v":0.6,"pi":0.8}` — 効果音〔s="wither", v=0.6, pi=0.8〕
06. `{"op":"area","r":24,"n":36}` — 円形対象の取得〔r=24, n=36〕
07. `{"op":"eff","e":"wither","t":600,"a":6}` — 敵への状態異常〔e="wither", t=600, a=6〕
08. `{"op":"eff","e":"blind","t":200,"a":0}` — 敵への状態異常〔e="blind", t=200, a=0〕
09. `{"op":"eff","e":"dark","t":300,"a":0}` — 敵への状態異常〔e="dark", t=300, a=0〕
10. `{"op":"strip"}` — 強化解除〔〕
11. `{"op":"summon","k":"wolf","n":3}` — 召喚〔k="wolf", n=3〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"resist","t":150,"a":1}` — 強化〔e="resist", t=150, a=1〕
15. `{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="witch", n=50, at="ring", r=8.0, y=0.6〕
16. `{"op":"fx","p":"ash","n":32,"at":"line","r":30}` — 粒子演出〔p="ash", n=32, at="line", r=30〕
17. `{"op":"sound","s":"wither","v":1.15,"pi":0.95}` — 効果音〔s="wither", v=1.15, pi=0.95〕
18. `{"op":"chain","n":5,"r":15.0}` — chain〔n=5, r=15.0〕
19. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
20. `{"op":"stun","t":40}` — 行動停止〔t=40〕
21. `{"op":"mark","t":125,"x":1.6}` — 刻印〔t=125, x=1.6〕
22. `{"op":"self"}` — 対象を自分へ〔〕
23. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
24. `{"op":"buff","e":"resist","t":150,"a":3}` — 強化〔e="resist", t=150, a=3〕
25. `{"op":"fx","p":"soul","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="soul", n=24, at="ring", r=12, y=0.5〕
26. `{"op":"sound","s":"wither","v":0.85,"pi":0.97}` — 効果音〔s="wither", v=0.85, pi=0.97〕
27. `{"op":"area","r":12.0,"n":12}` — 円形対象の取得〔r=12.0, n=12〕
28. `{"op":"dmg","m":0.8}` — 追加攻撃〔m=0.8〕
29. `{"op":"eff","e":"wither","t":100,"a":1}` — 敵への状態異常〔e="wither", t=100, a=1〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"regen","t":220,"a":3}` — 強化〔e="regen", t=220, a=3〕
32. `{"op":"area","r":14,"n":8}` — 円形対象の取得〔r=14, n=8〕
33. `{"op":"eff","e":"wither","t":100,"a":1}` — 敵への状態異常〔e="wither", t=100, a=1〕
34. `{"op":"fx","p":"soul","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="soul", n=24, at="ring", r=5.5, y=0.7〕
35. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
36. `{"op":"eff","e":"wither","t":30,"a":123}` — 敵への状態異常〔e="wither", t=30, a=123〕
37. `{"op":"self"}` — 対象を自分へ〔〕
38. `{"op":"buff","e":"regen","t":140,"a":7}` — 強化〔e="regen", t=140, a=7〕
39. `{"op":"fx","p":"witch","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="witch", n=16, at="ring", r=3.7, y=0.55〕
40. `{"op":"area","r":14,"n":7}` — 円形対象の取得〔r=14, n=7〕
41. `{"op":"eff","e":"wither","t":56,"a":5}` — 敵への状態異常〔e="wither", t=56, a=5〕
42. `{"op":"mark","t":115,"x":1.8}` — 刻印〔t=115, x=1.8〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 静眠封呪の結界札 — 神格装飾品（Curios relic_charm） (`gokuka_charm`)

**現行パラメータ**：rank=1、damage登録値=69.6762、relics側CD=190tick、art側CD=190tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（12命令）**：

01. `{"op":"area","r":6,"n":36}` — 円形対象の取得〔r=6, n=36〕
02. `{"op":"eff","e":"weakness","t":40,"a":1}` — 敵への状態異常〔e="weakness", t=40, a=1〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"resist","t":45,"a":0}` — 強化〔e="resist", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
08. `{"op":"buff","e":"resist","t":45,"a":1}` — 強化〔e="resist", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"regen","t":42,"a":2}` — 強化〔e="regen", t=42, a=2〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"regen","t":48,"a":4}` — 強化〔e="regen", t=48, a=4〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（37命令）**：

01. `{"op":"fx","p":"witch","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="witch", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"witch","n":4,"at":"self","s":0.7}` — 粒子演出〔p="witch", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"sculk","n":30,"at":"self","s":1.2}` — 粒子演出〔p="sculk", n=30, at="self", s=1.2〕
04. `{"op":"fx","p":"witch","n":30,"at":"self"}` — 粒子演出〔p="witch", n=30, at="self"〕
05. `{"op":"sound","s":"wither","v":0.6,"pi":0.8}` — 効果音〔s="wither", v=0.6, pi=0.8〕
06. `{"op":"area","r":20,"n":36}` — 円形対象の取得〔r=20, n=36〕
07. `{"op":"stun","t":80}` — 行動停止〔t=80〕
08. `{"op":"eff","e":"slow","t":400,"a":5}` — 敵への状態異常〔e="slow", t=400, a=5〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"guard","t":40}` — 防御〔t=40〕
11. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"resist","t":210,"a":1}` — 強化〔e="resist", t=210, a=1〕
14. `{"op":"fx","p":"soul","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="soul", n=46, at="ring", r=5.5, y=0.25〕
15. `{"op":"fx","p":"witch","n":36,"at":"line","r":24}` — 粒子演出〔p="witch", n=36, at="line", r=24〕
16. `{"op":"sound","s":"wither","v":1.05,"pi":1.14}` — 効果音〔s="wither", v=1.05, pi=1.14〕
17. `{"op":"self"}` — 対象を自分へ〔〕
18. `{"op":"guard","t":95}` — 防御〔t=95〕
19. `{"op":"self"}` — 対象を自分へ〔〕
20. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
21. `{"op":"cleanse"}` — 状態異常解除〔〕
22. `{"op":"buff","e":"resist","t":180,"a":3}` — 強化〔e="resist", t=180, a=3〕
23. `{"op":"guard","t":95}` — 防御〔t=95〕
24. `{"op":"fx","p":"soul","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="soul", n=30, at="ring", r=4.0, y=0.7〕
25. `{"op":"sound","s":"wither","v":0.8,"pi":1.1}` — 効果音〔s="wither", v=0.8, pi=1.1〕
26. `{"op":"self"}` — 対象を自分へ〔〕
27. `{"op":"buff","e":"regen","t":280,"a":4}` — 強化〔e="regen", t=280, a=4〕
28. `{"op":"guard","t":125}` — 防御〔t=125〕
29. `{"op":"self"}` — 対象を自分へ〔〕
30. `{"op":"cleanse"}` — 状態異常解除〔〕
31. `{"op":"fx","p":"soul","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="soul", n=20, at="ring", r=4, y=0.4〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"buff","e":"regen","t":140,"a":7}` — 強化〔e="regen", t=140, a=7〕
34. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
35. `{"op":"eff","e":"wither","t":22,"a":123}` — 敵への状態異常〔e="wither", t=22, a=123〕
36. `{"op":"self"}` — 対象を自分へ〔〕
37. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 業禍根源・万呪外法 — 超越神器（武器欄） (`gokuka_legend`)

**現行パラメータ**：rank=3、damage登録値=770.58333、relics側CD=345tick、art側CD=345tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:fire_aspect:10。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"area","r":8,"n":36}` — 円形対象の取得〔r=8, n=36〕
06. `{"op":"eff","e":"wither","t":40,"a":2}` — 敵への状態異常〔e="wither", t=40, a=2〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
09. `{"op":"buff","e":"resist","t":45,"a":3}` — 強化〔e="resist", t=45, a=3〕
10. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（9命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"eff","e":"wither","t":200,"a":4}` — 敵への状態異常〔e="wither", t=200, a=4〕
03. `{"op":"dmg","m":5.0,"magic":1}` — 追加攻撃〔m=5.0, magic=1〕
04. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"wither","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"wither","t":160,"a":1}]〕
05. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"soul","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"soul","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
06. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"wither","t":135,"a":2},{"op":"fx","p":"soul","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"wither","t":135,"a":2},{"op":"fx","p":"soul","n":10,"at":"t","s":0.35}]〕
07. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
08. `{"op":"chance","p":0.325,"ops":[{"op":"victim"},{"op":"fx","p":"soul","n":20,"at":"t","s":0.33},{"op":"eff","e":"wither","t":30,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.325, ops=[{"op":"victim"},{"op":"fx","p":"soul","n":20,"at":"t","s":0.33},{"op":"eff","e":"wither","t":30,"a":124},{"op":"mark","t":160,"x":2.5}]〕
09. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"witch","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"witch","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]〕

**権能発動時の命令（27命令）**：

01. `{"op":"fx","p":"witch","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="witch", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"witch","n":4,"at":"self","s":0.7}` — 粒子演出〔p="witch", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"sculk","n":30,"at":"self","s":1.2}` — 粒子演出〔p="sculk", n=30, at="self", s=1.2〕
04. `{"op":"fx","p":"witch","n":30,"at":"self"}` — 粒子演出〔p="witch", n=30, at="self"〕
05. `{"op":"sound","s":"wither","v":0.6,"pi":0.8}` — 効果音〔s="wither", v=0.6, pi=0.8〕
06. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
07. `{"op":"eff","e":"wither","t":1200,"a":9}` — 敵への状態異常〔e="wither", t=1200, a=9〕
08. `{"op":"eff","e":"poison","t":1200,"a":9}` — 敵への状態異常〔e="poison", t=1200, a=9〕
09. `{"op":"eff","e":"weakness","t":1200,"a":9}` — 敵への状態異常〔e="weakness", t=1200, a=9〕
10. `{"op":"eff","e":"hunger","t":600,"a":9}` — 敵への状態異常〔e="hunger", t=600, a=9〕
11. `{"op":"eff","e":"blind","t":300,"a":0}` — 敵への状態異常〔e="blind", t=300, a=0〕
12. `{"op":"eff","e":"dark","t":600,"a":0}` — 敵への状態異常〔e="dark", t=600, a=0〕
13. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
14. `{"op":"dmg","m":5.6,"magic":1}` — 追加攻撃〔m=5.6, magic=1〕
15. `{"op":"mark","t":600,"x":3.0}` — 刻印〔t=600, x=3.0〕
16. `{"op":"summon","k":"wolf","n":5}` — 召喚〔k="wolf", n=5〕
17. `{"op":"fx","p":"sculk","n":12,"at":"t","s":0.5}` — 粒子演出〔p="sculk", n=12, at="t", s=0.5〕
18. `{"op":"area","r":30,"n":24}` — 円形対象の取得〔r=30, n=24〕
19. `{"op":"strip"}` — 強化解除〔〕
20. `{"op":"eff","e":"wither","t":160,"a":1}` — 敵への状態異常〔e="wither", t=160, a=1〕
21. `{"op":"dmg","m":1.2}` — 追加攻撃〔m=1.2〕
22. `{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="witch", n=50, at="ring", r=8.0, y=0.6〕
23. `{"op":"fx","p":"ash","n":32,"at":"line","r":30}` — 粒子演出〔p="ash", n=32, at="line", r=30〕
24. `{"op":"sound","s":"wither","v":1.15,"pi":0.95}` — 効果音〔s="wither", v=1.15, pi=0.95〕
25. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.gokuka_legend.stage0","ops":[{"op":"fx","p":"soul","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"wither","v":0.9,"pi":1.2},{"op":"fx","p":"witch","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"soul","n":6,"at":"line","r":10},{"op":"fx","p":"soul","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"witch","n":36,"at":"line","r":24},{"op":"sound","s":"wither","v":1.05,"pi":1.14},{"op":"area","r":23.0,"n":18},{"op":"dmg","m":3.24},{"op":"eff","e":"wither","t":110,"a":1},{"op":"self"},{"op":"buff","e":"regen","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.gokuka_legend.stage1","ops":[{"op":"fx","p":"soul","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"wither","v":1.05,"pi":1.0},{"op":"fx","p":"soul","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"witch","n":6,"at":"line","r":15},{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"ash","n":32,"at":"line","r":30},{"op":"sound","s":"wither","v":1.15,"pi":0.95},{"op":"chain","n":5,"r":15.0},{"op":"dmg","m":4.06},{"op":"stun","t":40},{"op":"mark","t":125,"x":2.08},{"op":"area","r":14.0,"n":10},{"op":"eff","e":"wither","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.gokuka_legend.stage2","ops":[{"op":"fx","p":"soul","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"wither","v":1.25,"pi":0.75},{"op":"fx","p":"soul","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"witch","n":10,"at":"line","r":20},{"op":"fx","p":"soul","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"witch","n":48,"at":"line","r":48},{"op":"fx","p":"ash","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"wither","v":1.5,"pi":0.75},{"op":"area","r":34.0,"n":30},{"op":"dmg","m":9.234},{"op":"eff","e":"wither","t":150,"a":3},{"op":"stun","t":50},{"op":"self"},{"op":"buff","e":"resist","t":155,"a":3},{"op":"fx","p":"ash","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"soul","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":28.0,"n":25},{"op":"dmg","m":2.8},{"op":"eff","e":"wither","t":165,"a":3},{"op":"self"},{"op":"buff","e":"resist","t":180,"a":3},{"op":"area","r":27.0,"n":16},{"op":"dmg","m":0.9},{"op":"eff","e":"wither","t":160,"a":2},{"op":"self"},{"op":"buff","e":"regen","t":240,"a":4},{"op":"area","r":14,"n":8},{"op":"eff","e":"wither","t":100,"a":1},{"op":"fx","p":"soul","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"wither","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"wither","t":30,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"wither","t":56,"a":5},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.gokuka_legend.stage0","ops":[{"op":"fx","p":"soul","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"wither","v":0.9,"pi":1.2},{"op":"fx","p":"witch","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"soul","n":6,"at":"line","r":10},{"op":"fx","p":"soul","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"witch","n":36,"at":"line","r":24},{"op":"sound","s":"wither","v":1.05,"pi":1.14},{"op":"area","r":23.0,"n":18},{"op":"dmg","m":3.24},{"op":"eff","e":"wither","t":110,"a":1},{"op":"self"},{"op":"buff","e":"regen","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.gokuka_legend.stage1","ops":[{"op":"fx","p":"soul","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"wither","v":1.05,"pi":1.0},{"op":"fx","p":"soul","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"witch","n":6,"at":"line","r":15},{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"ash","n":32,"at":"line","r":30},{"op":"sound","s":"wither","v":1.15,"pi":0.95},{"op":"chain","n":5,"r":15.0},{"op":"dmg","m":4.06},{"op":"stun","t":40},{"op":"mark","t":125,"x":2.08},{"op":"area","r":14.0,"n":10},{"op":"eff","e":"wither","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.gokuka_legend.stage2","ops":[{"op":"fx","p":"soul","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"wither","v":1.25,"pi":0.75},{"op":"fx","p":"soul","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"witch","n":10,"at":"line","r":20},{"op":"fx","p":"soul","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"witch","n":48,"at":"line","r":48},{"op":"fx","p":"ash","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"wither","v":1.5,"pi":0.75},{"op":"area","r":34.0,"n":30},{"op":"dmg","m":9.234},{"op":"eff","e":"wither","t":150,"a":3},{"op":"stun","t":50},{"op":"self"},{"op":"buff","e":"resist","t":155,"a":3},{"op":"fx","p":"ash","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"soul","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":28.0,"n":25},{"op":"dmg","m":2.8},{"op":"eff","e":"wither","t":165,"a":3},{"op":"self"},{"op":"buff","e":"resist","t":180,"a":3},{"op":"area","r":27.0,"n":16},{"op":"dmg","m":0.9},{"op":"eff","e":"wither","t":160,"a":2},{"op":"self"},{"op":"buff","e":"regen","t":240,"a":4},{"op":"area","r":14,"n":8},{"op":"eff","e":"wither","t":100,"a":1},{"op":"fx","p":"soul","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"wither","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"wither","t":30,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"wither","t":56,"a":5},{"op":"mark","t":135,"x":1.8}]}]〕
26. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
27. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 18. 魔導深淵 メルリヌス

**モブ側の動きの方向性**：魔法数式の書き順と術式の組立を、指先と杖へ同期させる。。

### 魔導深淵の杖 — 討伐武器（メイン／武器欄） (`merlinus_weapon`)

**現行パラメータ**：rank=1、damage登録値=578.5、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（4命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"reflect","t":25,"r":6}` — 反射〔t=25, r=6〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（8命令）**：

01. `{"op":"chain","n":3,"r":8}` — chain〔n=3, r=8〕
02. `{"op":"dmg","m":0.3}` — 追加攻撃〔m=0.3〕
03. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"fatigue","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"fatigue","t":90,"a":0}]〕
04. `{"op":"chance","p":0.51,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":13,"at":"t","s":0.24},{"op":"mark","t":160,"x":1.93},{"op":"eff","e":"slow","t":115,"a":0}]}` — 抽選〔p=0.51, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":13,"at":"t","s":0.24},{"op":"mark","t":160,"x":1.93},{"op":"eff","e":"slow","t":115,"a":0}]〕
05. `{"op":"chance","p":0.204,"ops":[{"op":"victim"},{"op":"dmg","m":0.27}]}` — 抽選〔p=0.204, ops=[{"op":"victim"},{"op":"dmg","m":0.27}]〕
06. `{"op":"chance","p":0.104,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":8,"at":"t","s":0.25},{"op":"strip"}]}` — 抽選〔p=0.104, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":8,"at":"t","s":0.25},{"op":"strip"}]〕
07. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]〕
08. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":32,"a":3}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":32,"a":3}]〕

**権能発動時の命令（26命令）**：

01. `{"op":"fx","p":"enchant","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="enchant", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"enchant","n":4,"at":"self","s":0.7}` — 粒子演出〔p="enchant", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"portal","n":72,"at":"self","s":1.4}` — 粒子演出〔p="portal", n=72, at="self", s=1.4〕
04. `{"op":"fx","p":"enchant","n":40,"at":"self"}` — 粒子演出〔p="enchant", n=40, at="self"〕
05. `{"op":"sound","s":"spell","v":1.0,"pi":1.0}` — 効果音〔s="spell", v=1.0, pi=1.0〕
06. `{"op":"fx","p":"portal","n":60,"at":"line","r":48}` — 粒子演出〔p="portal", n=60, at="line", r=48〕
07. `{"op":"line","r":48,"w":3}` — 線分対象の取得〔r=48, w=3〕
08. `{"op":"dmg","m":1.92}` — 追加攻撃〔m=1.92〕
09. `{"op":"stun","t":65}` — 行動停止〔t=65〕
10. `{"op":"reflect","t":100,"r":16}` — 反射〔t=100, r=16〕
11. `{"op":"back","d":6}` — back〔d=6〕
12. `{"op":"fx","p":"enchant","n":12,"at":"t","s":0.5}` — 粒子演出〔p="enchant", n=12, at="t", s=0.5〕
13. `{"op":"fx","p":"enchant","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="enchant", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"portal","n":36,"at":"line","r":24}` — 粒子演出〔p="portal", n=36, at="line", r=24〕
15. `{"op":"line","r":62.0,"w":4.0}` — 線分対象の取得〔r=62.0, w=4.0〕
16. `{"op":"strip"}` — 強化解除〔〕
17. `{"op":"dmg","m":2.7}` — 追加攻撃〔m=2.7〕
18. `{"op":"fx","p":"enchant","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="enchant", n=16, at="ring", r=5.0〕
19. `{"op":"sound","s":"sonic","v":0.75,"pi":1.15}` — 効果音〔s="sonic", v=0.75, pi=1.15〕
20. `{"op":"line","r":18,"w":2}` — 線分対象の取得〔r=18, w=2〕
21. `{"op":"dmg","m":1.05}` — 追加攻撃〔m=1.05〕
22. `{"op":"eff","e":"slow","t":65,"a":0}` — 敵への状態異常〔e="slow", t=65, a=0〕
23. `{"op":"fx","p":"enchant","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="enchant", n=24, at="ring", r=4.5, y=0.6〕
24. `{"op":"sound","s":"spell","v":0.8,"pi":0.8}` — 効果音〔s="spell", v=0.8, pi=0.8〕
25. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
26. `{"op":"eff","e":"slow","t":32,"a":124}` — 敵への状態異常〔e="slow", t=32, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 無詠唱の魔導書 — 神威触媒（Curios relic_focus） (`merlinus_focus`)

**現行パラメータ**：rank=2、damage登録値=69.6762、relics側CD=155tick、art側CD=155tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（12命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"night","t":300,"a":0}` — 強化〔e="night", t=300, a=0〕
03. `{"op":"buff","e":"haste","t":40,"a":1}` — 強化〔e="haste", t=40, a=1〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":0}` — 強化〔e="haste", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"fx","p":"portal","n":10,"at":"self","s":0.12}` — 粒子演出〔p="portal", n=10, at="self", s=0.12〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕
10. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"haste","t":42,"a":2}` — 強化〔e="haste", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（43命令）**：

01. `{"op":"fx","p":"enchant","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="enchant", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"enchant","n":6,"at":"self","s":0.7}` — 粒子演出〔p="enchant", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"portal","n":72,"at":"self","s":1.4}` — 粒子演出〔p="portal", n=72, at="self", s=1.4〕
04. `{"op":"fx","p":"enchant","n":40,"at":"self"}` — 粒子演出〔p="enchant", n=40, at="self"〕
05. `{"op":"sound","s":"spell","v":1.0,"pi":1.0}` — 効果音〔s="spell", v=1.0, pi=1.0〕
06. `{"op":"area","r":32,"n":36}` — 円形対象の取得〔r=32, n=36〕
07. `{"op":"stun","t":90}` — 行動停止〔t=90〕
08. `{"op":"freeze","t":300}` — freeze〔t=300〕
09. `{"op":"erase","r":32}` — erase〔r=32〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"speed","t":300,"a":3}` — 強化〔e="speed", t=300, a=3〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"haste","t":150,"a":1}` — 強化〔e="haste", t=150, a=1〕
15. `{"op":"fx","p":"portal","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="portal", n=50, at="ring", r=8.0, y=0.6〕
16. `{"op":"fx","p":"witch","n":32,"at":"line","r":30}` — 粒子演出〔p="witch", n=32, at="line", r=30〕
17. `{"op":"sound","s":"spell","v":1.15,"pi":0.95}` — 効果音〔s="spell", v=1.15, pi=0.95〕
18. `{"op":"chain","n":6,"r":18.0}` — chain〔n=6, r=18.0〕
19. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
20. `{"op":"mark","t":120,"x":1.6}` — 刻印〔t=120, x=1.6〕
21. `{"op":"self"}` — 対象を自分へ〔〕
22. `{"op":"buff","e":"haste","t":125,"a":3}` — 強化〔e="haste", t=125, a=3〕
23. `{"op":"self"}` — 対象を自分へ〔〕
24. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
25. `{"op":"buff","e":"haste","t":150,"a":3}` — 強化〔e="haste", t=150, a=3〕
26. `{"op":"fx","p":"enchant","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="enchant", n=24, at="ring", r=12, y=0.5〕
27. `{"op":"sound","s":"spell","v":0.85,"pi":1.04}` — 効果音〔s="spell", v=0.85, pi=1.04〕
28. `{"op":"chain","n":4,"r":16.0}` — chain〔n=4, r=16.0〕
29. `{"op":"dmg","m":0.7}` — 追加攻撃〔m=0.7〕
30. `{"op":"eff","e":"slow","t":120,"a":1}` — 敵への状態異常〔e="slow", t=120, a=1〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"haste","t":240,"a":3}` — 強化〔e="haste", t=240, a=3〕
33. `{"op":"area","r":16,"n":10}` — 円形対象の取得〔r=16, n=10〕
34. `{"op":"strip"}` — 強化解除〔〕
35. `{"op":"fx","p":"enchant","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="enchant", n=24, at="ring", r=5.5, y=0.7〕
36. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
37. `{"op":"eff","e":"slow","t":43,"a":123}` — 敵への状態異常〔e="slow", t=43, a=123〕
38. `{"op":"self"}` — 対象を自分へ〔〕
39. `{"op":"buff","e":"haste","t":100,"a":123}` — 強化〔e="haste", t=100, a=123〕
40. `{"op":"fx","p":"enchant","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="enchant", n=16, at="ring", r=3.7, y=0.55〕
41. `{"op":"area","r":16,"n":9}` — 円形対象の取得〔r=16, n=9〕
42. `{"op":"eff","e":"fatigue","t":65,"a":45}` — 敵への状態異常〔e="fatigue", t=65, a=45〕
43. `{"op":"mark","t":135,"x":1.8}` — 刻印〔t=135, x=1.8〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 時空理論の指輪 — 神格装飾品（Curios relic_charm） (`merlinus_charm`)

**現行パラメータ**：rank=1、damage登録値=69.6762、relics側CD=185tick、art側CD=185tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（12命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"reflect","t":25,"r":8}` — 反射〔t=25, r=8〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"haste","t":45,"a":0}` — 強化〔e="haste", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
08. `{"op":"buff","e":"haste","t":45,"a":1}` — 強化〔e="haste", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"haste","t":42,"a":2}` — 強化〔e="haste", t=42, a=2〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"absorb","t":48,"a":4}` — 強化〔e="absorb", t=48, a=4〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（35命令）**：

01. `{"op":"fx","p":"enchant","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="enchant", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"enchant","n":4,"at":"self","s":0.7}` — 粒子演出〔p="enchant", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"portal","n":72,"at":"self","s":1.4}` — 粒子演出〔p="portal", n=72, at="self", s=1.4〕
04. `{"op":"fx","p":"enchant","n":40,"at":"self"}` — 粒子演出〔p="enchant", n=40, at="self"〕
05. `{"op":"sound","s":"spell","v":1.0,"pi":1.0}` — 効果音〔s="spell", v=1.0, pi=1.0〕
06. `{"op":"blink","d":20}` — blink〔d=20〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"guard","t":30}` — 防御〔t=30〕
09. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"haste","t":210,"a":1}` — 強化〔e="haste", t=210, a=1〕
12. `{"op":"fx","p":"enchant","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="enchant", n=46, at="ring", r=5.5, y=0.25〕
13. `{"op":"fx","p":"portal","n":36,"at":"line","r":24}` — 粒子演出〔p="portal", n=36, at="line", r=24〕
14. `{"op":"sound","s":"spell","v":1.05,"pi":1.14}` — 効果音〔s="spell", v=1.05, pi=1.14〕
15. `{"op":"self"}` — 対象を自分へ〔〕
16. `{"op":"guard","t":95}` — 防御〔t=95〕
17. `{"op":"self"}` — 対象を自分へ〔〕
18. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
19. `{"op":"cleanse"}` — 状態異常解除〔〕
20. `{"op":"buff","e":"haste","t":180,"a":3}` — 強化〔e="haste", t=180, a=3〕
21. `{"op":"guard","t":95}` — 防御〔t=95〕
22. `{"op":"fx","p":"enchant","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="enchant", n=30, at="ring", r=4.0, y=0.7〕
23. `{"op":"sound","s":"spell","v":0.8,"pi":1.1}` — 効果音〔s="spell", v=0.8, pi=1.1〕
24. `{"op":"self"}` — 対象を自分へ〔〕
25. `{"op":"buff","e":"haste","t":300,"a":4}` — 強化〔e="haste", t=300, a=4〕
26. `{"op":"guard","t":140}` — 防御〔t=140〕
27. `{"op":"self"}` — 対象を自分へ〔〕
28. `{"op":"reflect","t":80,"r":16}` — 反射〔t=80, r=16〕
29. `{"op":"fx","p":"enchant","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="enchant", n=20, at="ring", r=4, y=0.4〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"haste","t":160,"a":123}` — 強化〔e="haste", t=160, a=123〕
32. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
33. `{"op":"eff","e":"slow","t":32,"a":123}` — 敵への状態異常〔e="slow", t=32, a=123〕
34. `{"op":"self"}` — 対象を自分へ〔〕
35. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 魔導真理・知の深淵 — 超越神器（武器欄） (`merlinus_legend`)

**現行パラメータ**：rank=3、damage登録値=1157.875、relics側CD=340tick、art側CD=340tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"reflect","t":25,"r":12}` — 反射〔t=25, r=12〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
08. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕
09. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（8命令）**：

01. `{"op":"chain","n":6,"r":12}` — chain〔n=6, r=12〕
02. `{"op":"dmg","m":0.5}` — 追加攻撃〔m=0.5〕
03. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"fatigue","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"fatigue","t":160,"a":1}]〕
04. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
05. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"enchant","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"enchant","n":10,"at":"t","s":0.35}]〕
06. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
07. `{"op":"chance","p":0.35,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.35, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]〕
08. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":62,"a":5}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":62,"a":5}]〕

**権能発動時の命令（26命令）**：

01. `{"op":"fx","p":"enchant","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="enchant", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"enchant","n":4,"at":"self","s":0.7}` — 粒子演出〔p="enchant", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"portal","n":72,"at":"self","s":1.4}` — 粒子演出〔p="portal", n=72, at="self", s=1.4〕
04. `{"op":"fx","p":"enchant","n":40,"at":"self"}` — 粒子演出〔p="enchant", n=40, at="self"〕
05. `{"op":"sound","s":"spell","v":1.0,"pi":1.0}` — 効果音〔s="spell", v=1.0, pi=1.0〕
06. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
07. `{"op":"stun","t":105}` — 行動停止〔t=105〕
08. `{"op":"freeze","t":400}` — freeze〔t=400〕
09. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
10. `{"op":"strip"}` — 強化解除〔〕
11. `{"op":"line","r":64,"w":4}` — 線分対象の取得〔r=64, w=4〕
12. `{"op":"dmg","m":2.24}` — 追加攻撃〔m=2.24〕
13. `{"op":"reflect","t":400,"r":48}` — 反射〔t=400, r=48〕
14. `{"op":"erase","r":64}` — erase〔r=64〕
15. `{"op":"self"}` — 対象を自分へ〔〕
16. `{"op":"guard","t":100}` — 防御〔t=100〕
17. `{"op":"fx","p":"enchant","n":12,"at":"t","s":0.5}` — 粒子演出〔p="enchant", n=12, at="t", s=0.5〕
18. `{"op":"chain","n":5,"r":16}` — chain〔n=5, r=16〕
19. `{"op":"dmg","m":1.7}` — 追加攻撃〔m=1.7〕
20. `{"op":"mark","t":100,"x":1.4}` — 刻印〔t=100, x=1.4〕
21. `{"op":"fx","p":"portal","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="portal", n=50, at="ring", r=8.0, y=0.6〕
22. `{"op":"fx","p":"witch","n":32,"at":"line","r":30}` — 粒子演出〔p="witch", n=32, at="line", r=30〕
23. `{"op":"sound","s":"spell","v":1.15,"pi":0.95}` — 効果音〔s="spell", v=1.15, pi=0.95〕
24. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.merlinus_legend.stage0","ops":[{"op":"fx","p":"enchant","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"spell","v":0.9,"pi":1.2},{"op":"fx","p":"enchant","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":10},{"op":"fx","p":"enchant","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"portal","n":36,"at":"line","r":24},{"op":"sound","s":"spell","v":1.05,"pi":1.14},{"op":"line","r":62.0,"w":4.0},{"op":"strip"},{"op":"dmg","m":3.645},{"op":"self"},{"op":"buff","e":"haste","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.merlinus_legend.stage1","ops":[{"op":"fx","p":"enchant","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"spell","v":1.05,"pi":1.0},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"enchant","n":6,"at":"line","r":15},{"op":"fx","p":"portal","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"witch","n":32,"at":"line","r":30},{"op":"sound","s":"spell","v":1.15,"pi":0.95},{"op":"chain","n":6,"r":18.0},{"op":"dmg","m":4.06},{"op":"mark","t":120,"x":2.08},{"op":"self"},{"op":"buff","e":"haste","t":125,"a":3},{"op":"area","r":16.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.merlinus_legend.stage2","ops":[{"op":"fx","p":"enchant","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"spell","v":1.25,"pi":0.75},{"op":"fx","p":"end_rod","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"enchant","n":10,"at":"line","r":20},{"op":"fx","p":"enchant","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"portal","n":48,"at":"line","r":48},{"op":"fx","p":"witch","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"spell","v":1.5,"pi":0.75},{"op":"area","r":35.0,"n":30},{"op":"dmg","m":9.558},{"op":"strip"},{"op":"stun","t":60},{"op":"self"},{"op":"guard","t":135},{"op":"fx","p":"witch","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"enchant","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"line","r":75.0,"w":5.0},{"op":"dmg","m":2.8},{"op":"strip"},{"op":"self"},{"op":"buff","e":"haste","t":180,"a":4},{"op":"chain","n":5,"r":30.0},{"op":"dmg","m":1.0},{"op":"eff","e":"slow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"haste","t":240,"a":4},{"op":"area","r":16,"n":10},{"op":"strip"},{"op":"fx","p":"enchant","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"spell","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"fatigue","t":65,"a":45},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.merlinus_legend.stage0","ops":[{"op":"fx","p":"enchant","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"spell","v":0.9,"pi":1.2},{"op":"fx","p":"enchant","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":10},{"op":"fx","p":"enchant","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"portal","n":36,"at":"line","r":24},{"op":"sound","s":"spell","v":1.05,"pi":1.14},{"op":"line","r":62.0,"w":4.0},{"op":"strip"},{"op":"dmg","m":3.645},{"op":"self"},{"op":"buff","e":"haste","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.merlinus_legend.stage1","ops":[{"op":"fx","p":"enchant","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"spell","v":1.05,"pi":1.0},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"enchant","n":6,"at":"line","r":15},{"op":"fx","p":"portal","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"witch","n":32,"at":"line","r":30},{"op":"sound","s":"spell","v":1.15,"pi":0.95},{"op":"chain","n":6,"r":18.0},{"op":"dmg","m":4.06},{"op":"mark","t":120,"x":2.08},{"op":"self"},{"op":"buff","e":"haste","t":125,"a":3},{"op":"area","r":16.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.merlinus_legend.stage2","ops":[{"op":"fx","p":"enchant","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"spell","v":1.25,"pi":0.75},{"op":"fx","p":"end_rod","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"enchant","n":10,"at":"line","r":20},{"op":"fx","p":"enchant","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"portal","n":48,"at":"line","r":48},{"op":"fx","p":"witch","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"spell","v":1.5,"pi":0.75},{"op":"area","r":35.0,"n":30},{"op":"dmg","m":9.558},{"op":"strip"},{"op":"stun","t":60},{"op":"self"},{"op":"guard","t":135},{"op":"fx","p":"witch","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"enchant","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"line","r":75.0,"w":5.0},{"op":"dmg","m":2.8},{"op":"strip"},{"op":"self"},{"op":"buff","e":"haste","t":180,"a":4},{"op":"chain","n":5,"r":30.0},{"op":"dmg","m":1.0},{"op":"eff","e":"slow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"haste","t":240,"a":4},{"op":"area","r":16,"n":10},{"op":"strip"},{"op":"fx","p":"enchant","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"spell","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"fatigue","t":65,"a":45},{"op":"mark","t":135,"x":1.8}]}]〕
25. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
26. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 19. 災極海獣 淵煌

**モブ側の動きの方向性**：泳ぐ鰭、尾、顎、発光器官、毒触腕を別々に制御する。。

### 深海災牙の三叉戟 — 討伐武器（メイン／武器欄） (`enkou_weapon`)

**現行パラメータ**：rank=1、damage登録値=313.14286、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:fire_aspect:10。

**装備中の常時命令（6命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"water","t":300,"a":0}` — 強化〔e="water", t=300, a=0〕
03. `{"op":"buff","e":"dolphin","t":40,"a":1}` — 強化〔e="dolphin", t=40, a=1〕
04. `{"op":"buff","e":"night","t":300,"a":0}` — 強化〔e="night", t=300, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（9命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"eff","e":"poison","t":80,"a":2}` — 敵への状態異常〔e="poison", t=80, a=2〕
03. `{"op":"eff","e":"slow","t":60,"a":1}` — 敵への状態異常〔e="slow", t=60, a=1〕
04. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"poison","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"poison","t":90,"a":0}]〕
05. `{"op":"chance","p":0.535,"ops":[{"op":"victim"},{"op":"fx","p":"bubble","n":15,"at":"t","s":0.24},{"op":"mark","t":180,"x":2.07},{"op":"eff","e":"poison","t":55,"a":0}]}` — 抽選〔p=0.535, ops=[{"op":"victim"},{"op":"fx","p":"bubble","n":15,"at":"t","s":0.24},{"op":"mark","t":180,"x":2.07},{"op":"eff","e":"poison","t":55,"a":0}]〕
06. `{"op":"chance","p":0.231,"ops":[{"op":"victim"},{"op":"dmg","m":0.305}]}` — 抽選〔p=0.231, ops=[{"op":"victim"},{"op":"dmg","m":0.305}]〕
07. `{"op":"chance","p":0.123,"ops":[{"op":"victim"},{"op":"fx","p":"bubble","n":8,"at":"t","s":0.25},{"op":"eff","e":"slow","t":45,"a":0}]}` — 抽選〔p=0.123, ops=[{"op":"victim"},{"op":"fx","p":"bubble","n":8,"at":"t","s":0.25},{"op":"eff","e":"slow","t":45,"a":0}]〕
08. `{"op":"chance","p":0.24,"ops":[{"op":"victim"},{"op":"fx","p":"bubble","n":14,"at":"t","s":0.28},{"op":"eff","e":"poison","t":38,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.24, ops=[{"op":"victim"},{"op":"fx","p":"bubble","n":14,"at":"t","s":0.28},{"op":"eff","e":"poison","t":38,"a":124},{"op":"mark","t":100,"x":2.15}]〕
09. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"bubble","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"wither","t":48,"a":5}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"bubble","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"wither","t":48,"a":5}]〕

**権能発動時の命令（29命令）**：

01. `{"op":"fx","p":"bubble","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="bubble", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"bubble","n":4,"at":"self","s":0.7}` — 粒子演出〔p="bubble", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"bubble","n":40,"at":"self","s":1.6}` — 粒子演出〔p="bubble", n=40, at="self", s=1.6〕
04. `{"op":"fx","p":"sculk","n":20,"at":"self"}` — 粒子演出〔p="sculk", n=20, at="self"〕
05. `{"op":"sound","s":"roar","v":0.6,"pi":0.6}` — 効果音〔s="roar", v=0.6, pi=0.6〕
06. `{"op":"area","r":16,"n":36}` — 円形対象の取得〔r=16, n=36〕
07. `{"op":"dmg","m":1.8}` — 追加攻撃〔m=1.8〕
08. `{"op":"slam","f":3.0}` — slam〔f=3.0〕
09. `{"op":"eff","e":"dark","t":300,"a":0}` — 敵への状態異常〔e="dark", t=300, a=0〕
10. `{"op":"eff","e":"poison","t":300,"a":3}` — 敵への状態異常〔e="poison", t=300, a=3〕
11. `{"op":"pull","f":2.0}` — pull〔f=2.0〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"water","t":600,"a":0}` — 強化〔e="water", t=600, a=0〕
14. `{"op":"buff","e":"dolphin","t":300,"a":1}` — 強化〔e="dolphin", t=300, a=1〕
15. `{"op":"fx","p":"bubble","n":12,"at":"t","s":0.5}` — 粒子演出〔p="bubble", n=12, at="t", s=0.5〕
16. `{"op":"fx","p":"bubble","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="bubble", n=46, at="ring", r=5.5, y=0.25〕
17. `{"op":"fx","p":"spark","n":36,"at":"line","r":24}` — 粒子演出〔p="spark", n=36, at="line", r=24〕
18. `{"op":"line","r":61.0,"w":5.0}` — 線分対象の取得〔r=61.0, w=5.0〕
19. `{"op":"dmg","m":3.2}` — 追加攻撃〔m=3.2〕
20. `{"op":"eff","e":"slow","t":90,"a":2}` — 敵への状態異常〔e="slow", t=90, a=2〕
21. `{"op":"fx","p":"bubble","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="bubble", n=16, at="ring", r=5.0〕
22. `{"op":"sound","s":"spell","v":0.75,"pi":1.15}` — 効果音〔s="spell", v=0.75, pi=1.15〕
23. `{"op":"area","r":9,"n":8}` — 円形対象の取得〔r=9, n=8〕
24. `{"op":"dmg","m":0.9}` — 追加攻撃〔m=0.9〕
25. `{"op":"eff","e":"poison","t":65,"a":0}` — 敵への状態異常〔e="poison", t=65, a=0〕
26. `{"op":"fx","p":"bubble","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="bubble", n=24, at="ring", r=4.5, y=0.6〕
27. `{"op":"sound","s":"roar","v":0.8,"pi":0.8}` — 効果音〔s="roar", v=0.8, pi=0.8〕
28. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
29. `{"op":"eff","e":"poison","t":38,"a":124}` — 敵への状態異常〔e="poison", t=38, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 海淵圧力の魔珠 — 神威触媒（Curios relic_focus） (`enkou_focus`)

**現行パラメータ**：rank=2、damage登録値=77.8734、relics側CD=150tick、art側CD=150tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"water","t":300,"a":0}` — 強化〔e="water", t=300, a=0〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"water","t":45,"a":0}` — 強化〔e="water", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"water","t":45,"a":2}` — 強化〔e="water", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"water","t":42,"a":2}` — 強化〔e="water", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（42命令）**：

01. `{"op":"fx","p":"bubble","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="bubble", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"bubble","n":6,"at":"self","s":0.7}` — 粒子演出〔p="bubble", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"bubble","n":40,"at":"self","s":1.6}` — 粒子演出〔p="bubble", n=40, at="self", s=1.6〕
04. `{"op":"fx","p":"sculk","n":20,"at":"self"}` — 粒子演出〔p="sculk", n=20, at="self"〕
05. `{"op":"sound","s":"roar","v":0.6,"pi":0.6}` — 効果音〔s="roar", v=0.6, pi=0.6〕
06. `{"op":"fx","p":"end_rod","n":44,"at":"ring","r":10}` — 粒子演出〔p="end_rod", n=44, at="ring", r=10〕
07. `{"op":"area","r":24,"n":36}` — 円形対象の取得〔r=24, n=36〕
08. `{"op":"slam","f":4.0}` — slam〔f=4.0〕
09. `{"op":"stun","t":90}` — 行動停止〔t=90〕
10. `{"op":"eff","e":"slow","t":400,"a":6}` — 敵への状態異常〔e="slow", t=400, a=6〕
11. `{"op":"eff","e":"dark","t":400,"a":0}` — 敵への状態異常〔e="dark", t=400, a=0〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"water","t":150,"a":1}` — 強化〔e="water", t=150, a=1〕
15. `{"op":"fx","p":"spark","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="spark", n=50, at="ring", r=8.0, y=0.6〕
16. `{"op":"fx","p":"splash","n":32,"at":"line","r":30}` — 粒子演出〔p="splash", n=32, at="line", r=30〕
17. `{"op":"sound","s":"roar","v":1.15,"pi":0.95}` — 効果音〔s="roar", v=1.15, pi=0.95〕
18. `{"op":"area","r":26.0,"n":22}` — 円形対象の取得〔r=26.0, n=22〕
19. `{"op":"dmg","m":2.5}` — 追加攻撃〔m=2.5〕
20. `{"op":"eff","e":"poison","t":140,"a":2}` — 敵への状態異常〔e="poison", t=140, a=2〕
21. `{"op":"pull","f":1.6}` — pull〔f=1.6〕
22. `{"op":"self"}` — 対象を自分へ〔〕
23. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
24. `{"op":"buff","e":"water","t":150,"a":3}` — 強化〔e="water", t=150, a=3〕
25. `{"op":"fx","p":"bubble","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="bubble", n=24, at="ring", r=12, y=0.5〕
26. `{"op":"sound","s":"roar","v":0.85,"pi":1.11}` — 効果音〔s="roar", v=0.85, pi=1.11〕
27. `{"op":"cone","r":16.0,"a":95.0}` — 扇形対象の取得〔r=16.0, a=95.0〕
28. `{"op":"dmg","m":0.95}` — 追加攻撃〔m=0.95〕
29. `{"op":"eff","e":"poison","t":140,"a":1}` — 敵への状態異常〔e="poison", t=140, a=1〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"water","t":200,"a":3}` — 強化〔e="water", t=200, a=3〕
32. `{"op":"area","r":18,"n":5}` — 円形対象の取得〔r=18, n=5〕
33. `{"op":"lightning"}` — lightning〔〕
34. `{"op":"fx","p":"bubble","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="bubble", n=24, at="ring", r=5.5, y=0.7〕
35. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
36. `{"op":"eff","e":"poison","t":51,"a":123}` — 敵への状態異常〔e="poison", t=51, a=123〕
37. `{"op":"self"}` — 対象を自分へ〔〕
38. `{"op":"buff","e":"water","t":160,"a":0}` — 強化〔e="water", t=160, a=0〕
39. `{"op":"fx","p":"bubble","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="bubble", n=16, at="ring", r=3.7, y=0.55〕
40. `{"op":"area","r":14,"n":7}` — 円形対象の取得〔r=14, n=7〕
41. `{"op":"eff","e":"poison","t":65,"a":9}` — 敵への状態異常〔e="poison", t=65, a=9〕
42. `{"op":"mark","t":115,"x":1.8}` — 刻印〔t=115, x=1.8〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 黒曜海鱗の護符 — 神格装飾品（Curios relic_charm） (`enkou_charm`)

**現行パラメータ**：rank=1、damage登録値=77.8734、relics側CD=180tick、art側CD=180tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（13命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":1}` — 強化〔e="resist", t=40, a=1〕
03. `{"op":"buff","e":"water","t":300,"a":0}` — 強化〔e="water", t=300, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"water","t":45,"a":0}` — 強化〔e="water", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
09. `{"op":"buff","e":"water","t":45,"a":1}` — 強化〔e="water", t=45, a=1〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"water","t":42,"a":2}` — 強化〔e="water", t=42, a=2〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"regen","t":48,"a":4}` — 強化〔e="regen", t=48, a=4〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（36命令）**：

01. `{"op":"fx","p":"bubble","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="bubble", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"bubble","n":4,"at":"self","s":0.7}` — 粒子演出〔p="bubble", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"bubble","n":40,"at":"self","s":1.6}` — 粒子演出〔p="bubble", n=40, at="self", s=1.6〕
04. `{"op":"fx","p":"sculk","n":20,"at":"self"}` — 粒子演出〔p="sculk", n=20, at="self"〕
05. `{"op":"sound","s":"roar","v":0.6,"pi":0.6}` — 効果音〔s="roar", v=0.6, pi=0.6〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"guard","t":80}` — 防御〔t=80〕
08. `{"op":"buff","e":"resist","t":400,"a":4}` — 強化〔e="resist", t=400, a=4〕
09. `{"op":"adapt","t":400}` — adapt〔t=400〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"water","t":210,"a":1}` — 強化〔e="water", t=210, a=1〕
13. `{"op":"fx","p":"bubble","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="bubble", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"spark","n":36,"at":"line","r":24}` — 粒子演出〔p="spark", n=36, at="line", r=24〕
15. `{"op":"sound","s":"roar","v":1.05,"pi":1.14}` — 効果音〔s="roar", v=1.05, pi=1.14〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"guard","t":95}` — 防御〔t=95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
20. `{"op":"cleanse"}` — 状態異常解除〔〕
21. `{"op":"buff","e":"water","t":180,"a":3}` — 強化〔e="water", t=180, a=3〕
22. `{"op":"guard","t":95}` — 防御〔t=95〕
23. `{"op":"fx","p":"bubble","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="bubble", n=30, at="ring", r=4.0, y=0.7〕
24. `{"op":"sound","s":"roar","v":0.8,"pi":1.1}` — 効果音〔s="roar", v=0.8, pi=1.1〕
25. `{"op":"self"}` — 対象を自分へ〔〕
26. `{"op":"buff","e":"water","t":260,"a":4}` — 強化〔e="water", t=260, a=4〕
27. `{"op":"guard","t":155}` — 防御〔t=155〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"buff","e":"water","t":240,"a":2}` — 強化〔e="water", t=240, a=2〕
30. `{"op":"fx","p":"bubble","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="bubble", n=20, at="ring", r=4, y=0.4〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"water","t":160,"a":0}` — 強化〔e="water", t=160, a=0〕
33. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
34. `{"op":"eff","e":"poison","t":38,"a":123}` — 敵への状態異常〔e="poison", t=38, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 海獣災極・深淵咆哮 — 超越神器（武器欄） (`enkou_legend`)

**現行パラメータ**：rank=3、damage登録値=461.2381、relics側CD=335tick、art側CD=335tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:fire_aspect:10。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"buff","e":"water","t":300,"a":0}` — 強化〔e="water", t=300, a=0〕
06. `{"op":"buff","e":"dolphin","t":40,"a":2}` — 強化〔e="dolphin", t=40, a=2〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
09. `{"op":"buff","e":"water","t":45,"a":3}` — 強化〔e="water", t=45, a=3〕
10. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（9命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"eff","e":"poison","t":100,"a":4}` — 敵への状態異常〔e="poison", t=100, a=4〕
03. `{"op":"eff","e":"dark","t":60,"a":0}` — 敵への状態異常〔e="dark", t=60, a=0〕
04. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"poison","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"poison","t":160,"a":1}]〕
05. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"bubble","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"bubble","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
06. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"poison","t":135,"a":2},{"op":"fx","p":"bubble","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"poison","t":135,"a":2},{"op":"fx","p":"bubble","n":10,"at":"t","s":0.35}]〕
07. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
08. `{"op":"chance","p":0.375,"ops":[{"op":"victim"},{"op":"fx","p":"bubble","n":20,"at":"t","s":0.33},{"op":"eff","e":"poison","t":51,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.375, ops=[{"op":"victim"},{"op":"fx","p":"bubble","n":20,"at":"t","s":0.33},{"op":"eff","e":"poison","t":51,"a":124},{"op":"mark","t":160,"x":2.5}]〕
09. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"bubble","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"wither","t":78,"a":7}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"bubble","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"wither","t":78,"a":7}]〕

**権能発動時の命令（24命令）**：

01. `{"op":"fx","p":"bubble","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="bubble", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"bubble","n":4,"at":"self","s":0.7}` — 粒子演出〔p="bubble", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"bubble","n":40,"at":"self","s":1.6}` — 粒子演出〔p="bubble", n=40, at="self", s=1.6〕
04. `{"op":"fx","p":"sculk","n":20,"at":"self"}` — 粒子演出〔p="sculk", n=20, at="self"〕
05. `{"op":"sound","s":"roar","v":0.6,"pi":0.6}` — 効果音〔s="roar", v=0.6, pi=0.6〕
06. `{"op":"fx","p":"end_rod","n":44,"at":"ring","r":10}` — 粒子演出〔p="end_rod", n=44, at="ring", r=10〕
07. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
08. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
09. `{"op":"slam","f":5.0}` — slam〔f=5.0〕
10. `{"op":"stun","t":105}` — 行動停止〔t=105〕
11. `{"op":"eff","e":"dark","t":600,"a":0}` — 敵への状態異常〔e="dark", t=600, a=0〕
12. `{"op":"eff","e":"poison","t":600,"a":9}` — 敵への状態異常〔e="poison", t=600, a=9〕
13. `{"op":"eff","e":"blind","t":200,"a":0}` — 敵への状態異常〔e="blind", t=200, a=0〕
14. `{"op":"pull","f":3.0}` — pull〔f=3.0〕
15. `{"op":"fx","p":"bubble","n":12,"at":"t","s":0.5}` — 粒子演出〔p="bubble", n=12, at="t", s=0.5〕
16. `{"op":"cone","r":36,"a":85}` — 扇形対象の取得〔r=36, a=85〕
17. `{"op":"dmg","m":1.6}` — 追加攻撃〔m=1.6〕
18. `{"op":"knock","f":2.5}` — knock〔f=2.5〕
19. `{"op":"fx","p":"spark","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="spark", n=50, at="ring", r=8.0, y=0.6〕
20. `{"op":"fx","p":"splash","n":32,"at":"line","r":30}` — 粒子演出〔p="splash", n=32, at="line", r=30〕
21. `{"op":"sound","s":"roar","v":1.15,"pi":0.95}` — 効果音〔s="roar", v=1.15, pi=0.95〕
22. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.enkou_legend.stage0","ops":[{"op":"fx","p":"bubble","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"roar","v":0.9,"pi":1.2},{"op":"fx","p":"bubble","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"splash","n":6,"at":"line","r":10},{"op":"fx","p":"bubble","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"spark","n":36,"at":"line","r":24},{"op":"sound","s":"roar","v":1.05,"pi":1.14},{"op":"line","r":61.0,"w":5.0},{"op":"dmg","m":4.32},{"op":"eff","e":"slow","t":90,"a":2},{"op":"self"},{"op":"buff","e":"water","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.enkou_legend.stage1","ops":[{"op":"fx","p":"bubble","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"roar","v":1.05,"pi":1.0},{"op":"fx","p":"splash","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"bubble","n":6,"at":"line","r":15},{"op":"fx","p":"spark","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"splash","n":32,"at":"line","r":30},{"op":"sound","s":"roar","v":1.15,"pi":0.95},{"op":"area","r":26.0,"n":22},{"op":"dmg","m":3.625},{"op":"eff","e":"poison","t":140,"a":2},{"op":"pull","f":1.6},{"op":"area","r":18.0,"n":10},{"op":"eff","e":"poison","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.enkou_legend.stage2","ops":[{"op":"fx","p":"bubble","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"roar","v":1.25,"pi":0.75},{"op":"fx","p":"splash","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"bubble","n":10,"at":"line","r":20},{"op":"fx","p":"bubble","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"spark","n":48,"at":"line","r":48},{"op":"fx","p":"splash","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"roar","v":1.5,"pi":0.75},{"op":"area","r":34.0,"n":29},{"op":"dmg","m":10.53},{"op":"eff","e":"poison","t":150,"a":3},{"op":"knock","f":3.5},{"op":"self"},{"op":"buff","e":"resist","t":155,"a":2},{"op":"fx","p":"splash","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"bubble","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"cone","r":32.0,"a":135.0},{"op":"dmg","m":3.1},{"op":"eff","e":"poison","t":140,"a":3},{"op":"self"},{"op":"buff","e":"resist","t":170,"a":3},{"op":"cone","r":15.0,"a":110.0},{"op":"dmg","m":1.1},{"op":"eff","e":"poison","t":160,"a":2},{"op":"self"},{"op":"buff","e":"water","t":240,"a":4},{"op":"area","r":18,"n":5},{"op":"lightning"},{"op":"fx","p":"bubble","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"roar","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"poison","t":51,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"poison","t":65,"a":9},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.enkou_legend.stage0","ops":[{"op":"fx","p":"bubble","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"roar","v":0.9,"pi":1.2},{"op":"fx","p":"bubble","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"splash","n":6,"at":"line","r":10},{"op":"fx","p":"bubble","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"spark","n":36,"at":"line","r":24},{"op":"sound","s":"roar","v":1.05,"pi":1.14},{"op":"line","r":61.0,"w":5.0},{"op":"dmg","m":4.32},{"op":"eff","e":"slow","t":90,"a":2},{"op":"self"},{"op":"buff","e":"water","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.enkou_legend.stage1","ops":[{"op":"fx","p":"bubble","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"roar","v":1.05,"pi":1.0},{"op":"fx","p":"splash","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"bubble","n":6,"at":"line","r":15},{"op":"fx","p":"spark","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"splash","n":32,"at":"line","r":30},{"op":"sound","s":"roar","v":1.15,"pi":0.95},{"op":"area","r":26.0,"n":22},{"op":"dmg","m":3.625},{"op":"eff","e":"poison","t":140,"a":2},{"op":"pull","f":1.6},{"op":"area","r":18.0,"n":10},{"op":"eff","e":"poison","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.enkou_legend.stage2","ops":[{"op":"fx","p":"bubble","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"roar","v":1.25,"pi":0.75},{"op":"fx","p":"splash","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"bubble","n":10,"at":"line","r":20},{"op":"fx","p":"bubble","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"spark","n":48,"at":"line","r":48},{"op":"fx","p":"splash","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"roar","v":1.5,"pi":0.75},{"op":"area","r":34.0,"n":29},{"op":"dmg","m":10.53},{"op":"eff","e":"poison","t":150,"a":3},{"op":"knock","f":3.5},{"op":"self"},{"op":"buff","e":"resist","t":155,"a":2},{"op":"fx","p":"splash","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"bubble","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"cone","r":32.0,"a":135.0},{"op":"dmg","m":3.1},{"op":"eff","e":"poison","t":140,"a":3},{"op":"self"},{"op":"buff","e":"resist","t":170,"a":3},{"op":"cone","r":15.0,"a":110.0},{"op":"dmg","m":1.1},{"op":"eff","e":"poison","t":160,"a":2},{"op":"self"},{"op":"buff","e":"water","t":240,"a":4},{"op":"area","r":18,"n":5},{"op":"lightning"},{"op":"fx","p":"bubble","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"roar","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"poison","t":51,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"poison","t":65,"a":9},{"op":"mark","t":135,"x":1.8}]}]〕
23. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
24. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 20. 嶺脈地龍 クールマ

**モブ側の動きの方向性**：巨大な岩殻の重みをゆっくりした四肢と地脈の波で見せる。。

### 嶺脈地龍の大槌 — 討伐武器（メイン／武器欄） (`kurma_weapon`)

**現行パラメータ**：rank=1、damage登録値=267.26437、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:knockback:5、minecraft:efficiency:125。

**装備中の常時命令（5命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":0}` — 強化〔e="resist", t=40, a=0〕
03. `{"op":"buff","e":"absorb","t":40,"a":1}` — 強化〔e="absorb", t=40, a=1〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（9命令）**：

01. `{"op":"around","r":4,"n":16,"exclude":1}` — around〔r=4, n=16, exclude=1〕
02. `{"op":"dmg","m":0.3}` — 追加攻撃〔m=0.3〕
03. `{"op":"launch","f":0.8}` — launch〔f=0.8〕
04. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"slow","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"slow","t":90,"a":0}]〕
05. `{"op":"chance","p":0.56,"ops":[{"op":"victim"},{"op":"fx","p":"ash","n":17,"at":"t","s":0.24},{"op":"mark","t":200,"x":2.21},{"op":"eff","e":"slow","t":67,"a":0}]}` — 抽選〔p=0.56, ops=[{"op":"victim"},{"op":"fx","p":"ash","n":17,"at":"t","s":0.24},{"op":"mark","t":200,"x":2.21},{"op":"eff","e":"slow","t":67,"a":0}]〕
06. `{"op":"chance","p":0.258,"ops":[{"op":"victim"},{"op":"dmg","m":0.34}]}` — 抽選〔p=0.258, ops=[{"op":"victim"},{"op":"dmg","m":0.34}]〕
07. `{"op":"chance","p":0.142,"ops":[{"op":"victim"},{"op":"fx","p":"ash","n":8,"at":"t","s":0.25},{"op":"launch","f":0.2}]}` — 抽選〔p=0.142, ops=[{"op":"victim"},{"op":"fx","p":"ash","n":8,"at":"t","s":0.25},{"op":"launch","f":0.2}]〕
08. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"fx","p":"bigsmoke","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"fx","p":"bigsmoke","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]〕
09. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"smoke","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"smoke","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]〕

**権能発動時の命令（26命令）**：

01. `{"op":"fx","p":"block","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="block", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"block","n":4,"at":"self","s":0.7}` — 粒子演出〔p="block", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"blast","n":1,"at":"self"}` — 粒子演出〔p="blast", n=1, at="self"〕
04. `{"op":"fx","p":"compost","n":40,"at":"self","s":1.6}` — 粒子演出〔p="compost", n=40, at="self", s=1.6〕
05. `{"op":"sound","s":"anvil","v":0.8,"pi":0.5}` — 効果音〔s="anvil", v=0.8, pi=0.5〕
06. `{"op":"area","r":20,"n":36}` — 円形対象の取得〔r=20, n=36〕
07. `{"op":"dmg","m":1.92}` — 追加攻撃〔m=1.92〕
08. `{"op":"launch","f":1.8}` — launch〔f=1.8〕
09. `{"op":"stun","t":65}` — 行動停止〔t=65〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"resist","t":300,"a":3}` — 強化〔e="resist", t=300, a=3〕
12. `{"op":"fx","p":"compost","n":12,"at":"t","s":0.5}` — 粒子演出〔p="compost", n=12, at="t", s=0.5〕
13. `{"op":"fx","p":"ash","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="ash", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"crit","n":36,"at":"line","r":24}` — 粒子演出〔p="crit", n=36, at="line", r=24〕
15. `{"op":"area","r":18.0,"n":15}` — 円形対象の取得〔r=18.0, n=15〕
16. `{"op":"dmg","m":3.5}` — 追加攻撃〔m=3.5〕
17. `{"op":"slam"}` — slam〔〕
18. `{"op":"fx","p":"block","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="block", n=16, at="ring", r=5.0〕
19. `{"op":"sound","s":"spell","v":0.75,"pi":1.15}` — 効果音〔s="spell", v=0.75, pi=1.15〕
20. `{"op":"area","r":9,"n":8}` — 円形対象の取得〔r=9, n=8〕
21. `{"op":"dmg","m":0.9}` — 追加攻撃〔m=0.9〕
22. `{"op":"eff","e":"slow","t":65,"a":0}` — 敵への状態異常〔e="slow", t=65, a=0〕
23. `{"op":"fx","p":"bigsmoke","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="bigsmoke", n=24, at="ring", r=4.5, y=0.6〕
24. `{"op":"sound","s":"stone","v":0.8,"pi":0.8}` — 効果音〔s="stone", v=0.8, pi=0.8〕
25. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
26. `{"op":"eff","e":"slow","t":32,"a":124}` — 敵への状態異常〔e="slow", t=32, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 霊脈地鎮の石碑 — 神威触媒（Curios relic_focus） (`kurma_focus`)

**現行パラメータ**：rank=2、damage登録値=71.7255、relics側CD=145tick、art側CD=145tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"allies","r":12}` — 味方対象〔r=12〕
02. `{"op":"buff","e":"regen","t":40,"a":0,"to":1}` — 強化〔e="regen", t=40, a=0, to=1〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"resist","t":45,"a":0}` — 強化〔e="resist", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"resist","t":42,"a":2}` — 強化〔e="resist", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（43命令）**：

01. `{"op":"fx","p":"block","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="block", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"block","n":6,"at":"self","s":0.7}` — 粒子演出〔p="block", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"blast","n":1,"at":"self"}` — 粒子演出〔p="blast", n=1, at="self"〕
04. `{"op":"fx","p":"compost","n":40,"at":"self","s":1.6}` — 粒子演出〔p="compost", n=40, at="self", s=1.6〕
05. `{"op":"sound","s":"anvil","v":0.8,"pi":0.5}` — 効果音〔s="anvil", v=0.8, pi=0.5〕
06. `{"op":"allies","r":24}` — 味方対象〔r=24〕
07. `{"op":"healpct","v":0.4,"to":1}` — 最大HP割合回復〔v=0.4, to=1〕
08. `{"op":"buff","e":"absorb","t":600,"a":6,"to":1}` — 強化〔e="absorb", t=600, a=6, to=1〕
09. `{"op":"buff","e":"resist","t":600,"a":3,"to":1}` — 強化〔e="resist", t=600, a=3, to=1〕
10. `{"op":"give","item":"bread","n":8}` — give〔item="bread", n=8〕
11. `{"op":"xp","v":40}` — xp〔v=40〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"resist","t":150,"a":1}` — 強化〔e="resist", t=150, a=1〕
15. `{"op":"fx","p":"crit","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="crit", n=50, at="ring", r=8.0, y=0.6〕
16. `{"op":"fx","p":"bigsmoke","n":32,"at":"line","r":30}` — 粒子演出〔p="bigsmoke", n=32, at="line", r=30〕
17. `{"op":"sound","s":"stone","v":1.15,"pi":0.95}` — 効果音〔s="stone", v=1.15, pi=0.95〕
18. `{"op":"line","r":58.0,"w":5.0}` — 線分対象の取得〔r=58.0, w=5.0〕
19. `{"op":"dmg","m":3.3}` — 追加攻撃〔m=3.3〕
20. `{"op":"stun","t":42}` — 行動停止〔t=42〕
21. `{"op":"self"}` — 対象を自分へ〔〕
22. `{"op":"guard","t":100}` — 防御〔t=100〕
23. `{"op":"self"}` — 対象を自分へ〔〕
24. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
25. `{"op":"buff","e":"resist","t":150,"a":3}` — 強化〔e="resist", t=150, a=3〕
26. `{"op":"fx","p":"bigsmoke","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="bigsmoke", n=24, at="ring", r=12, y=0.5〕
27. `{"op":"sound","s":"stone","v":0.85,"pi":1.18}` — 効果音〔s="stone", v=0.85, pi=1.18〕
28. `{"op":"area","r":18.0,"n":12}` — 円形対象の取得〔r=18.0, n=12〕
29. `{"op":"dmg","m":0.8}` — 追加攻撃〔m=0.8〕
30. `{"op":"eff","e":"slow","t":160,"a":1}` — 敵への状態異常〔e="slow", t=160, a=1〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"resist","t":220,"a":3}` — 強化〔e="resist", t=220, a=3〕
33. `{"op":"area","r":20,"n":10}` — 円形対象の取得〔r=20, n=10〕
34. `{"op":"slam","f":3.2}` — slam〔f=3.2〕
35. `{"op":"fx","p":"bigsmoke","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="bigsmoke", n=24, at="ring", r=5.5, y=0.7〕
36. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
37. `{"op":"eff","e":"slow","t":43,"a":123}` — 敵への状態異常〔e="slow", t=43, a=123〕
38. `{"op":"self"}` — 対象を自分へ〔〕
39. `{"op":"buff","e":"resist","t":140,"a":2}` — 強化〔e="resist", t=140, a=2〕
40. `{"op":"fx","p":"smoke","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="smoke", n=16, at="ring", r=3.7, y=0.55〕
41. `{"op":"cone","r":12,"a":100}` — 扇形対象の取得〔r=12, a=100〕
42. `{"op":"eff","e":"slow","t":55,"a":15}` — 敵への状態異常〔e="slow", t=55, a=15〕
43. `{"op":"knock","f":2.1}` — knock〔f=2.1〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 山脈甲殻の護符 — 神格装飾品（Curios relic_charm） (`kurma_charm`)

**現行パラメータ**：rank=1、damage登録値=71.7255、relics側CD=175tick、art側CD=175tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（12命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":2}` — 強化〔e="resist", t=40, a=2〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"resist","t":45,"a":0}` — 強化〔e="resist", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
08. `{"op":"buff","e":"resist","t":45,"a":1}` — 強化〔e="resist", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"resist","t":42,"a":2}` — 強化〔e="resist", t=42, a=2〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"resist","t":48,"a":4}` — 強化〔e="resist", t=48, a=4〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（36命令）**：

01. `{"op":"fx","p":"block","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="block", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"block","n":4,"at":"self","s":0.7}` — 粒子演出〔p="block", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"blast","n":1,"at":"self"}` — 粒子演出〔p="blast", n=1, at="self"〕
04. `{"op":"fx","p":"compost","n":40,"at":"self","s":1.6}` — 粒子演出〔p="compost", n=40, at="self", s=1.6〕
05. `{"op":"sound","s":"anvil","v":0.8,"pi":0.5}` — 効果音〔s="anvil", v=0.8, pi=0.5〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"guard","t":100}` — 防御〔t=100〕
08. `{"op":"buff","e":"resist","t":600,"a":4}` — 強化〔e="resist", t=600, a=4〕
09. `{"op":"buff","e":"absorb","t":600,"a":8}` — 強化〔e="absorb", t=600, a=8〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"resist","t":210,"a":1}` — 強化〔e="resist", t=210, a=1〕
13. `{"op":"fx","p":"ash","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="ash", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"crit","n":36,"at":"line","r":24}` — 粒子演出〔p="crit", n=36, at="line", r=24〕
15. `{"op":"sound","s":"stone","v":1.05,"pi":1.14}` — 効果音〔s="stone", v=1.05, pi=1.14〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"guard","t":95}` — 防御〔t=95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
20. `{"op":"cleanse"}` — 状態異常解除〔〕
21. `{"op":"buff","e":"resist","t":180,"a":3}` — 強化〔e="resist", t=180, a=3〕
22. `{"op":"guard","t":95}` — 防御〔t=95〕
23. `{"op":"fx","p":"bigsmoke","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="bigsmoke", n=30, at="ring", r=4.0, y=0.7〕
24. `{"op":"sound","s":"stone","v":0.8,"pi":1.1}` — 効果音〔s="stone", v=0.8, pi=1.1〕
25. `{"op":"self"}` — 対象を自分へ〔〕
26. `{"op":"buff","e":"resist","t":280,"a":4}` — 強化〔e="resist", t=280, a=4〕
27. `{"op":"guard","t":170}` — 防御〔t=170〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"buff","e":"resist","t":240,"a":2}` — 強化〔e="resist", t=240, a=2〕
30. `{"op":"fx","p":"bigsmoke","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="bigsmoke", n=20, at="ring", r=4, y=0.4〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"resist","t":140,"a":2}` — 強化〔e="resist", t=140, a=2〕
33. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
34. `{"op":"eff","e":"slow","t":32,"a":123}` — 敵への状態異常〔e="slow", t=32, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 地龍世界・大陸の心臓 — 超越神器（武器欄） (`kurma_legend`)

**現行パラメータ**：rank=3、damage登録値=339.27586、relics側CD=330tick、art側CD=330tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:knockback:5、minecraft:efficiency:125。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"buff","e":"absorb","t":40,"a":4}` — 強化〔e="absorb", t=40, a=4〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
08. `{"op":"buff","e":"resist","t":45,"a":3}` — 強化〔e="resist", t=45, a=3〕
09. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（9命令）**：

01. `{"op":"around","r":5,"n":16,"exclude":1}` — around〔r=5, n=16, exclude=1〕
02. `{"op":"dmg","m":0.4}` — 追加攻撃〔m=0.4〕
03. `{"op":"launch","f":1.0}` — launch〔f=1.0〕
04. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"slow","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"slow","t":160,"a":1}]〕
05. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"ash","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"ash","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
06. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"ash","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"ash","n":10,"at":"t","s":0.35}]〕
07. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
08. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"fx","p":"bigsmoke","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"fx","p":"bigsmoke","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]〕
09. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"smoke","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"smoke","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]〕

**権能発動時の命令（26命令）**：

01. `{"op":"fx","p":"block","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="block", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"block","n":4,"at":"self","s":0.7}` — 粒子演出〔p="block", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"blast","n":1,"at":"self"}` — 粒子演出〔p="blast", n=1, at="self"〕
04. `{"op":"fx","p":"compost","n":40,"at":"self","s":1.6}` — 粒子演出〔p="compost", n=40, at="self", s=1.6〕
05. `{"op":"sound","s":"anvil","v":0.8,"pi":0.5}` — 効果音〔s="anvil", v=0.8, pi=0.5〕
06. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
07. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
08. `{"op":"launch","f":3.0}` — launch〔f=3.0〕
09. `{"op":"stun","t":105}` — 行動停止〔t=105〕
10. `{"op":"allies","r":32}` — 味方対象〔r=32〕
11. `{"op":"healpct","v":0.6,"to":1}` — 最大HP割合回復〔v=0.6, to=1〕
12. `{"op":"buff","e":"absorb","t":1200,"a":9,"to":1}` — 強化〔e="absorb", t=1200, a=9, to=1〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"guard","t":100}` — 防御〔t=100〕
15. `{"op":"buff","e":"resist","t":1200,"a":4}` — 強化〔e="resist", t=1200, a=4〕
16. `{"op":"give","item":"diamond","n":4}` — give〔item="diamond", n=4〕
17. `{"op":"fx","p":"compost","n":12,"at":"t","s":0.5}` — 粒子演出〔p="compost", n=12, at="t", s=0.5〕
18. `{"op":"cone","r":12,"a":120}` — 扇形対象の取得〔r=12, a=120〕
19. `{"op":"dmg","m":2.5}` — 追加攻撃〔m=2.5〕
20. `{"op":"slam"}` — slam〔〕
21. `{"op":"fx","p":"crit","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="crit", n=50, at="ring", r=8.0, y=0.6〕
22. `{"op":"fx","p":"bigsmoke","n":32,"at":"line","r":30}` — 粒子演出〔p="bigsmoke", n=32, at="line", r=30〕
23. `{"op":"sound","s":"stone","v":1.15,"pi":0.95}` — 効果音〔s="stone", v=1.15, pi=0.95〕
24. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.kurma_legend.stage0","ops":[{"op":"fx","p":"bigsmoke","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"stone","v":0.9,"pi":1.2},{"op":"fx","p":"smoke","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"crit","n":6,"at":"line","r":10},{"op":"fx","p":"ash","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"crit","n":36,"at":"line","r":24},{"op":"sound","s":"stone","v":1.05,"pi":1.14},{"op":"area","r":18.0,"n":15},{"op":"dmg","m":4.725},{"op":"slam"},{"op":"self"},{"op":"buff","e":"resist","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.kurma_legend.stage1","ops":[{"op":"fx","p":"bigsmoke","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"stone","v":1.05,"pi":1.0},{"op":"fx","p":"crit","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"smoke","n":6,"at":"line","r":15},{"op":"fx","p":"crit","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"bigsmoke","n":32,"at":"line","r":30},{"op":"sound","s":"stone","v":1.15,"pi":0.95},{"op":"line","r":58.0,"w":5.0},{"op":"dmg","m":4.785},{"op":"stun","t":42},{"op":"self"},{"op":"guard","t":100},{"op":"area","r":20.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.kurma_legend.stage2","ops":[{"op":"fx","p":"bigsmoke","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"stone","v":1.25,"pi":0.75},{"op":"fx","p":"crit","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"smoke","n":10,"at":"line","r":20},{"op":"fx","p":"ash","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"crit","n":48,"at":"line","r":48},{"op":"fx","p":"bigsmoke","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"stone","v":1.5,"pi":0.75},{"op":"area","r":36.0,"n":30},{"op":"dmg","m":11.34},{"op":"slam"},{"op":"stun","t":60},{"op":"self"},{"op":"buff","e":"resist","t":180,"a":4},{"op":"fx","p":"bigsmoke","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"ash","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":34.0,"n":30},{"op":"dmg","m":3.5},{"op":"slam"},{"op":"self"},{"op":"guard","t":125},{"op":"area","r":18.0,"n":16},{"op":"dmg","m":1.2},{"op":"eff","e":"slow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"resist","t":240,"a":4},{"op":"area","r":20,"n":10},{"op":"slam","f":3.2},{"op":"fx","p":"bigsmoke","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"stone","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"slow","t":55,"a":15},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.kurma_legend.stage0","ops":[{"op":"fx","p":"bigsmoke","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"stone","v":0.9,"pi":1.2},{"op":"fx","p":"smoke","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"crit","n":6,"at":"line","r":10},{"op":"fx","p":"ash","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"crit","n":36,"at":"line","r":24},{"op":"sound","s":"stone","v":1.05,"pi":1.14},{"op":"area","r":18.0,"n":15},{"op":"dmg","m":4.725},{"op":"slam"},{"op":"self"},{"op":"buff","e":"resist","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.kurma_legend.stage1","ops":[{"op":"fx","p":"bigsmoke","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"stone","v":1.05,"pi":1.0},{"op":"fx","p":"crit","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"smoke","n":6,"at":"line","r":15},{"op":"fx","p":"crit","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"bigsmoke","n":32,"at":"line","r":30},{"op":"sound","s":"stone","v":1.15,"pi":0.95},{"op":"line","r":58.0,"w":5.0},{"op":"dmg","m":4.785},{"op":"stun","t":42},{"op":"self"},{"op":"guard","t":100},{"op":"area","r":20.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.kurma_legend.stage2","ops":[{"op":"fx","p":"bigsmoke","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"stone","v":1.25,"pi":0.75},{"op":"fx","p":"crit","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"smoke","n":10,"at":"line","r":20},{"op":"fx","p":"ash","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"crit","n":48,"at":"line","r":48},{"op":"fx","p":"bigsmoke","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"stone","v":1.5,"pi":0.75},{"op":"area","r":36.0,"n":30},{"op":"dmg","m":11.34},{"op":"slam"},{"op":"stun","t":60},{"op":"self"},{"op":"buff","e":"resist","t":180,"a":4},{"op":"fx","p":"bigsmoke","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"ash","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":34.0,"n":30},{"op":"dmg","m":3.5},{"op":"slam"},{"op":"self"},{"op":"guard","t":125},{"op":"area","r":18.0,"n":16},{"op":"dmg","m":1.2},{"op":"eff","e":"slow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"resist","t":240,"a":4},{"op":"area","r":20,"n":10},{"op":"slam","f":3.2},{"op":"fx","p":"bigsmoke","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"stone","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"slow","t":55,"a":15},{"op":"mark","t":135,"x":1.8}]}]〕
25. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
26. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 21. 光越天龍 テイア

**モブ側の動きの方向性**：翼の折畳み・空中旋回・急加速と制動の力学を重視する。。

### 光越天龍の光弓 — 討伐武器（メイン／武器欄） (`teia_weapon`)

**現行パラメータ**：rank=1、damage登録値=772.66667、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:power:125、minecraft:punch:4、minecraft:flame:1、minecraft:infinity:1。

**装備中の常時命令（5命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"speed","t":40,"a":2}` — 強化〔e="speed", t=40, a=2〕
03. `{"op":"reflect","t":25,"r":6}` — 反射〔t=25, r=6〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（8命令）**：

01. `{"op":"chain","n":3,"r":10}` — chain〔n=3, r=10〕
02. `{"op":"dmg","m":0.3}` — 追加攻撃〔m=0.3〕
03. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"glow","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"glow","t":90,"a":0}]〕
04. `{"op":"chance","p":0.46,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":9,"at":"t","s":0.24},{"op":"mark","t":120,"x":1.65},{"op":"eff","e":"glow","t":79,"a":0}]}` — 抽選〔p=0.46, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":9,"at":"t","s":0.24},{"op":"mark","t":120,"x":1.65},{"op":"eff","e":"glow","t":79,"a":0}]〕
05. `{"op":"chance","p":0.15,"ops":[{"op":"victim"},{"op":"dmg","m":0.2}]}` — 抽選〔p=0.15, ops=[{"op":"victim"},{"op":"dmg","m":0.2}]〕
06. `{"op":"chance","p":0.085,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":8,"at":"t","s":0.25},{"op":"dmg","m":0.32}]}` — 抽選〔p=0.085, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":8,"at":"t","s":0.25},{"op":"dmg","m":0.32}]〕
07. `{"op":"chance","p":0.18,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":14,"at":"t","s":0.28},{"op":"eff","e":"fatigue","t":110,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.18, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":14,"at":"t","s":0.28},{"op":"eff","e":"fatigue","t":110,"a":124},{"op":"mark","t":100,"x":2.15}]〕
08. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]〕

**権能発動時の命令（26命令）**：

01. `{"op":"fx","p":"end_rod","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="end_rod", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"end_rod","n":4,"at":"self","s":0.7}` — 粒子演出〔p="end_rod", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":60,"at":"line","r":24}` — 粒子演出〔p="end_rod", n=60, at="line", r=24〕
04. `{"op":"fx","p":"firework","n":20,"at":"self"}` — 粒子演出〔p="firework", n=20, at="self"〕
05. `{"op":"sound","s":"blast","v":1.0,"pi":1.6}` — 効果音〔s="blast", v=1.0, pi=1.6〕
06. `{"op":"line","r":64,"w":2}` — 線分対象の取得〔r=64, w=2〕
07. `{"op":"dmg","m":2.16}` — 追加攻撃〔m=2.16〕
08. `{"op":"burn","s":4}` — burn〔s=4〕
09. `{"op":"arrows","n":4,"d":30}` — arrows〔n=4, d=30〕
10. `{"op":"erase","r":24}` — erase〔r=24〕
11. `{"op":"blink","d":10}` — blink〔d=10〕
12. `{"op":"fx","p":"firework","n":12,"at":"t","s":0.5}` — 粒子演出〔p="firework", n=12, at="t", s=0.5〕
13. `{"op":"fx","p":"end_rod","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="end_rod", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"firework","n":36,"at":"line","r":24}` — 粒子演出〔p="firework", n=36, at="line", r=24〕
15. `{"op":"line","r":69.0,"w":2.0}` — 線分対象の取得〔r=69.0, w=2.0〕
16. `{"op":"dmg","m":3.0}` — 追加攻撃〔m=3.0〕
17. `{"op":"mark","t":105,"x":1.5}` — 刻印〔t=105, x=1.5〕
18. `{"op":"fx","p":"end_rod","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="end_rod", n=16, at="ring", r=5.0〕
19. `{"op":"sound","s":"sonic","v":0.75,"pi":1.15}` — 効果音〔s="sonic", v=0.75, pi=1.15〕
20. `{"op":"line","r":18,"w":2}` — 線分対象の取得〔r=18, w=2〕
21. `{"op":"dmg","m":1.05}` — 追加攻撃〔m=1.05〕
22. `{"op":"eff","e":"glow","t":65,"a":0}` — 敵への状態異常〔e="glow", t=65, a=0〕
23. `{"op":"fx","p":"end_rod","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="end_rod", n=24, at="ring", r=4.5, y=0.6〕
24. `{"op":"sound","s":"teleport","v":0.8,"pi":0.8}` — 効果音〔s="teleport", v=0.8, pi=0.8〕
25. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
26. `{"op":"eff","e":"fatigue","t":110,"a":124}` — 敵への状態異常〔e="fatigue", t=110, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 虹跡推進の光核 — 神威触媒（Curios relic_focus） (`teia_focus`)

**現行パラメータ**：rank=2、damage登録値=68.31、relics側CD=160tick、art側CD=160tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"speed","t":40,"a":1}` — 強化〔e="speed", t=40, a=1〕
03. `{"op":"buff","e":"jump","t":40,"a":1}` — 強化〔e="jump", t=40, a=1〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"speed","t":45,"a":0}` — 強化〔e="speed", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"speed","t":45,"a":2}` — 強化〔e="speed", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"speed","t":42,"a":2}` — 強化〔e="speed", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（42命令）**：

01. `{"op":"fx","p":"end_rod","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="end_rod", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"end_rod","n":6,"at":"self","s":0.7}` — 粒子演出〔p="end_rod", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":60,"at":"line","r":24}` — 粒子演出〔p="end_rod", n=60, at="line", r=24〕
04. `{"op":"fx","p":"firework","n":20,"at":"self"}` — 粒子演出〔p="firework", n=20, at="self"〕
05. `{"op":"sound","s":"blast","v":1.0,"pi":1.6}` — 効果音〔s="blast", v=1.0, pi=1.6〕
06. `{"op":"dash","f":4.5}` — dash〔f=4.5〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"buff","e":"speed","t":300,"a":5}` — 強化〔e="speed", t=300, a=5〕
09. `{"op":"buff","e":"jump","t":300,"a":3}` — 強化〔e="jump", t=300, a=3〕
10. `{"op":"guard","t":20}` — 防御〔t=20〕
11. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"speed","t":150,"a":1}` — 強化〔e="speed", t=150, a=1〕
14. `{"op":"fx","p":"firework","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="firework", n=50, at="ring", r=8.0, y=0.6〕
15. `{"op":"fx","p":"spark","n":32,"at":"line","r":30}` — 粒子演出〔p="spark", n=32, at="line", r=30〕
16. `{"op":"sound","s":"teleport","v":1.15,"pi":0.95}` — 効果音〔s="teleport", v=1.15, pi=0.95〕
17. `{"op":"chain","n":6,"r":24.0}` — chain〔n=6, r=24.0〕
18. `{"op":"dmg","m":2.9}` — 追加攻撃〔m=2.9〕
19. `{"op":"eff","e":"glow","t":135,"a":0}` — 敵への状態異常〔e="glow", t=135, a=0〕
20. `{"op":"self"}` — 対象を自分へ〔〕
21. `{"op":"buff","e":"speed","t":125,"a":4}` — 強化〔e="speed", t=125, a=4〕
22. `{"op":"self"}` — 対象を自分へ〔〕
23. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
24. `{"op":"buff","e":"speed","t":150,"a":3}` — 強化〔e="speed", t=150, a=3〕
25. `{"op":"fx","p":"end_rod","n":24,"at":"ring","r":10,"y":0.5}` — 粒子演出〔p="end_rod", n=24, at="ring", r=10, y=0.5〕
26. `{"op":"sound","s":"teleport","v":0.85,"pi":0.9}` — 効果音〔s="teleport", v=0.85, pi=0.9〕
27. `{"op":"line","r":28.0,"w":2.5}` — 線分対象の取得〔r=28.0, w=2.5〕
28. `{"op":"dmg","m":0.85}` — 追加攻撃〔m=0.85〕
29. `{"op":"eff","e":"glow","t":100,"a":1}` — 敵への状態異常〔e="glow", t=100, a=1〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"speed","t":240,"a":3}` — 強化〔e="speed", t=240, a=3〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"blink","d":6}` — blink〔d=6〕
34. `{"op":"fx","p":"end_rod","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="end_rod", n=24, at="ring", r=5.5, y=0.7〕
35. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
36. `{"op":"eff","e":"fatigue","t":148,"a":123}` — 敵への状態異常〔e="fatigue", t=148, a=123〕
37. `{"op":"self"}` — 対象を自分へ〔〕
38. `{"op":"buff","e":"speed","t":120,"a":4}` — 強化〔e="speed", t=120, a=4〕
39. `{"op":"fx","p":"end_rod","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="end_rod", n=16, at="ring", r=3.7, y=0.55〕
40. `{"op":"cone","r":12,"a":100}` — 扇形対象の取得〔r=12, a=100〕
41. `{"op":"eff","e":"glow","t":100,"a":0}` — 敵への状態異常〔e="glow", t=100, a=0〕
42. `{"op":"knock","f":2.1}` — knock〔f=2.1〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 因果越速の羽飾り — 神格装飾品（Curios relic_charm） (`teia_charm`)

**現行パラメータ**：rank=1、damage登録値=68.31、relics側CD=190tick、art側CD=190tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（13命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"slowfall","t":40,"a":0}` — 強化〔e="slowfall", t=40, a=0〕
03. `{"op":"buff","e":"speed","t":40,"a":0}` — 強化〔e="speed", t=40, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"speed","t":45,"a":0}` — 強化〔e="speed", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
09. `{"op":"buff","e":"speed","t":45,"a":1}` — 強化〔e="speed", t=45, a=1〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"speed","t":42,"a":2}` — 強化〔e="speed", t=42, a=2〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"speed","t":48,"a":5}` — 強化〔e="speed", t=48, a=5〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（34命令）**：

01. `{"op":"fx","p":"end_rod","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="end_rod", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"end_rod","n":4,"at":"self","s":0.7}` — 粒子演出〔p="end_rod", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":60,"at":"line","r":24}` — 粒子演出〔p="end_rod", n=60, at="line", r=24〕
04. `{"op":"fx","p":"firework","n":20,"at":"self"}` — 粒子演出〔p="firework", n=20, at="self"〕
05. `{"op":"sound","s":"blast","v":1.0,"pi":1.6}` — 効果音〔s="blast", v=1.0, pi=1.6〕
06. `{"op":"erase","r":32}` — erase〔r=32〕
07. `{"op":"reflect","t":200,"r":16}` — 反射〔t=200, r=16〕
08. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"speed","t":210,"a":1}` — 強化〔e="speed", t=210, a=1〕
11. `{"op":"fx","p":"end_rod","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="end_rod", n=46, at="ring", r=5.5, y=0.25〕
12. `{"op":"fx","p":"firework","n":36,"at":"line","r":24}` — 粒子演出〔p="firework", n=36, at="line", r=24〕
13. `{"op":"sound","s":"teleport","v":1.05,"pi":1.14}` — 効果音〔s="teleport", v=1.05, pi=1.14〕
14. `{"op":"self"}` — 対象を自分へ〔〕
15. `{"op":"guard","t":95}` — 防御〔t=95〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
18. `{"op":"cleanse"}` — 状態異常解除〔〕
19. `{"op":"buff","e":"speed","t":180,"a":3}` — 強化〔e="speed", t=180, a=3〕
20. `{"op":"guard","t":95}` — 防御〔t=95〕
21. `{"op":"fx","p":"end_rod","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="end_rod", n=30, at="ring", r=4.0, y=0.7〕
22. `{"op":"sound","s":"teleport","v":0.8,"pi":1.1}` — 効果音〔s="teleport", v=0.8, pi=1.1〕
23. `{"op":"self"}` — 対象を自分へ〔〕
24. `{"op":"buff","e":"speed","t":300,"a":4}` — 強化〔e="speed", t=300, a=4〕
25. `{"op":"guard","t":125}` — 防御〔t=125〕
26. `{"op":"self"}` — 対象を自分へ〔〕
27. `{"op":"buff","e":"slowfall","t":240,"a":2}` — 強化〔e="slowfall", t=240, a=2〕
28. `{"op":"fx","p":"end_rod","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="end_rod", n=20, at="ring", r=4, y=0.4〕
29. `{"op":"self"}` — 対象を自分へ〔〕
30. `{"op":"buff","e":"speed","t":120,"a":4}` — 強化〔e="speed", t=120, a=4〕
31. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
32. `{"op":"eff","e":"fatigue","t":110,"a":123}` — 敵への状態異常〔e="fatigue", t=110, a=123〕
33. `{"op":"self"}` — 対象を自分へ〔〕
34. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 超光翔空・天裂の神矢 — 超越神器（武器欄） (`teia_legend`)

**現行パラメータ**：rank=3、damage登録値=1545.16667、relics側CD=345tick、art側CD=345tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:power:125、minecraft:punch:4、minecraft:flame:1、minecraft:infinity:1、minecraft:luck_of_the_sea:25。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"buff","e":"speed","t":40,"a":3}` — 強化〔e="speed", t=40, a=3〕
06. `{"op":"reflect","t":25,"r":10}` — 反射〔t=25, r=10〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
09. `{"op":"buff","e":"speed","t":45,"a":3}` — 強化〔e="speed", t=45, a=3〕
10. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（8命令）**：

01. `{"op":"chain","n":5,"r":12}` — chain〔n=5, r=12〕
02. `{"op":"dmg","m":0.5}` — 追加攻撃〔m=0.5〕
03. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"glow","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"glow","t":160,"a":1}]〕
04. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
05. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"glow","t":135,"a":2},{"op":"fx","p":"end_rod","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"glow","t":135,"a":2},{"op":"fx","p":"end_rod","n":10,"at":"t","s":0.35}]〕
06. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
07. `{"op":"chance","p":0.3,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":20,"at":"t","s":0.33},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.3, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":20,"at":"t","s":0.33},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":160,"x":2.5}]〕
08. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]〕

**権能発動時の命令（27命令）**：

01. `{"op":"fx","p":"end_rod","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="end_rod", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"end_rod","n":4,"at":"self","s":0.7}` — 粒子演出〔p="end_rod", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":60,"at":"line","r":24}` — 粒子演出〔p="end_rod", n=60, at="line", r=24〕
04. `{"op":"fx","p":"firework","n":20,"at":"self"}` — 粒子演出〔p="firework", n=20, at="self"〕
05. `{"op":"sound","s":"blast","v":1.0,"pi":1.6}` — 効果音〔s="blast", v=1.0, pi=1.6〕
06. `{"op":"fx","p":"end_rod","n":72,"at":"line","r":128}` — 粒子演出〔p="end_rod", n=72, at="line", r=128〕
07. `{"op":"line","r":128,"w":4}` — 線分対象の取得〔r=128, w=4〕
08. `{"op":"dmg","m":3.36}` — 追加攻撃〔m=3.36〕
09. `{"op":"burn","s":10}` — burn〔s=10〕
10. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
11. `{"op":"arrows","n":10,"d":60}` — arrows〔n=10, d=60〕
12. `{"op":"lightning"}` — lightning〔〕
13. `{"op":"dmg","m":1.68}` — 追加攻撃〔m=1.68〕
14. `{"op":"erase","r":64}` — erase〔r=64〕
15. `{"op":"blink","d":24}` — blink〔d=24〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"buff","e":"speed","t":600,"a":5}` — 強化〔e="speed", t=600, a=5〕
18. `{"op":"fx","p":"firework","n":12,"at":"t","s":0.5}` — 粒子演出〔p="firework", n=12, at="t", s=0.5〕
19. `{"op":"cone","r":36,"a":85}` — 扇形対象の取得〔r=36, a=85〕
20. `{"op":"dmg","m":1.6}` — 追加攻撃〔m=1.6〕
21. `{"op":"knock","f":2.5}` — knock〔f=2.5〕
22. `{"op":"fx","p":"firework","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="firework", n=50, at="ring", r=8.0, y=0.6〕
23. `{"op":"fx","p":"spark","n":32,"at":"line","r":30}` — 粒子演出〔p="spark", n=32, at="line", r=30〕
24. `{"op":"sound","s":"teleport","v":1.15,"pi":0.95}` — 効果音〔s="teleport", v=1.15, pi=0.95〕
25. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.teia_legend.stage0","ops":[{"op":"fx","p":"end_rod","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"teleport","v":0.9,"pi":1.2},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"firework","n":6,"at":"line","r":10},{"op":"fx","p":"end_rod","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"firework","n":36,"at":"line","r":24},{"op":"sound","s":"teleport","v":1.05,"pi":1.14},{"op":"line","r":69.0,"w":2.0},{"op":"dmg","m":4.05},{"op":"mark","t":105,"x":1.95},{"op":"self"},{"op":"buff","e":"speed","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.teia_legend.stage1","ops":[{"op":"fx","p":"end_rod","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"teleport","v":1.05,"pi":1.0},{"op":"fx","p":"firework","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":15},{"op":"fx","p":"firework","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"spark","n":32,"at":"line","r":30},{"op":"sound","s":"teleport","v":1.15,"pi":0.95},{"op":"chain","n":6,"r":24.0},{"op":"dmg","m":4.205},{"op":"eff","e":"glow","t":135,"a":0},{"op":"self"},{"op":"buff","e":"speed","t":125,"a":4},{"op":"area","r":12.0,"n":10},{"op":"eff","e":"glow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.teia_legend.stage2","ops":[{"op":"fx","p":"end_rod","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"teleport","v":1.25,"pi":0.75},{"op":"fx","p":"firework","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"end_rod","n":10,"at":"line","r":20},{"op":"fx","p":"end_rod","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"firework","n":48,"at":"line","r":48},{"op":"fx","p":"spark","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"teleport","v":1.5,"pi":0.75},{"op":"line","r":79.0,"w":4.0},{"op":"dmg","m":11.178},{"op":"strip"},{"op":"area","r":24.0,"n":18},{"op":"dmg","m":4.05},{"op":"self"},{"op":"buff","e":"speed","t":170,"a":5},{"op":"fx","p":"spark","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"end_rod","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"line","r":80.0,"w":4.0},{"op":"dmg","m":3.5},{"op":"mark","t":170,"x":2.3},{"op":"self"},{"op":"buff","e":"speed","t":180,"a":5},{"op":"line","r":41.0,"w":4.0},{"op":"dmg","m":0.8},{"op":"eff","e":"glow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"speed","t":240,"a":4},{"op":"line","r":40.0,"w":2.5},{"op":"dmg","m":0.55},{"op":"fx","p":"end_rod","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"teleport","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"glow","t":100,"a":0},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.teia_legend.stage0","ops":[{"op":"fx","p":"end_rod","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"teleport","v":0.9,"pi":1.2},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"firework","n":6,"at":"line","r":10},{"op":"fx","p":"end_rod","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"firework","n":36,"at":"line","r":24},{"op":"sound","s":"teleport","v":1.05,"pi":1.14},{"op":"line","r":69.0,"w":2.0},{"op":"dmg","m":4.05},{"op":"mark","t":105,"x":1.95},{"op":"self"},{"op":"buff","e":"speed","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.teia_legend.stage1","ops":[{"op":"fx","p":"end_rod","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"teleport","v":1.05,"pi":1.0},{"op":"fx","p":"firework","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":15},{"op":"fx","p":"firework","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"spark","n":32,"at":"line","r":30},{"op":"sound","s":"teleport","v":1.15,"pi":0.95},{"op":"chain","n":6,"r":24.0},{"op":"dmg","m":4.205},{"op":"eff","e":"glow","t":135,"a":0},{"op":"self"},{"op":"buff","e":"speed","t":125,"a":4},{"op":"area","r":12.0,"n":10},{"op":"eff","e":"glow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.teia_legend.stage2","ops":[{"op":"fx","p":"end_rod","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"teleport","v":1.25,"pi":0.75},{"op":"fx","p":"firework","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"end_rod","n":10,"at":"line","r":20},{"op":"fx","p":"end_rod","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"firework","n":48,"at":"line","r":48},{"op":"fx","p":"spark","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"teleport","v":1.5,"pi":0.75},{"op":"line","r":79.0,"w":4.0},{"op":"dmg","m":11.178},{"op":"strip"},{"op":"area","r":24.0,"n":18},{"op":"dmg","m":4.05},{"op":"self"},{"op":"buff","e":"speed","t":170,"a":5},{"op":"fx","p":"spark","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"end_rod","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"line","r":80.0,"w":4.0},{"op":"dmg","m":3.5},{"op":"mark","t":170,"x":2.3},{"op":"self"},{"op":"buff","e":"speed","t":180,"a":5},{"op":"line","r":41.0,"w":4.0},{"op":"dmg","m":0.8},{"op":"eff","e":"glow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"speed","t":240,"a":4},{"op":"line","r":40.0,"w":2.5},{"op":"dmg","m":0.55},{"op":"fx","p":"end_rod","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"teleport","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"glow","t":100,"a":0},{"op":"mark","t":135,"x":1.8}]}]〕
26. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
27. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 22. 大海皇鯨 バハムート

**モブ側の動きの方向性**：巨大鯨のゆったりした遊泳と歌声の振動を連動させる。。

### 大海皇鯨の法螺貝 — 討伐武器（メイン／武器欄） (`bahamut_weapon`)

**現行パラメータ**：rank=1、damage登録値=578.5、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（6命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"water","t":300,"a":0}` — 強化〔e="water", t=300, a=0〕
03. `{"op":"buff","e":"dolphin","t":40,"a":1}` — 強化〔e="dolphin", t=40, a=1〕
04. `{"op":"buff","e":"regen","t":40,"a":0}` — 強化〔e="regen", t=40, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（8命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"knock","f":2.0}` — knock〔f=2.0〕
03. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"slow","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"slow","t":90,"a":0}]〕
04. `{"op":"chance","p":0.425,"ops":[{"op":"victim"},{"op":"fx","p":"bubble","n":11,"at":"t","s":0.24},{"op":"mark","t":140,"x":1.79},{"op":"eff","e":"slow","t":91,"a":0}]}` — 抽選〔p=0.425, ops=[{"op":"victim"},{"op":"fx","p":"bubble","n":11,"at":"t","s":0.24},{"op":"mark","t":140,"x":1.79},{"op":"eff","e":"slow","t":91,"a":0}]〕
05. `{"op":"chance","p":0.177,"ops":[{"op":"victim"},{"op":"dmg","m":0.235}]}` — 抽選〔p=0.177, ops=[{"op":"victim"},{"op":"dmg","m":0.235}]〕
06. `{"op":"chance","p":0.104,"ops":[{"op":"victim"},{"op":"fx","p":"bubble","n":8,"at":"t","s":0.25},{"op":"self"},{"op":"healpct","v":0.045}]}` — 抽選〔p=0.104, ops=[{"op":"victim"},{"op":"fx","p":"bubble","n":8,"at":"t","s":0.25},{"op":"self"},{"op":"healpct","v":0.045}]〕
07. `{"op":"chance","p":0.2,"ops":[{"op":"victim"},{"op":"fx","p":"splash","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.2, ops=[{"op":"victim"},{"op":"fx","p":"splash","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]〕
08. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"splash","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"splash","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]〕

**権能発動時の命令（29命令）**：

01. `{"op":"fx","p":"bubble","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="bubble", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"bubble","n":4,"at":"self","s":0.7}` — 粒子演出〔p="bubble", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"splash","n":72,"at":"self","s":2.0}` — 粒子演出〔p="splash", n=72, at="self", s=2.0〕
04. `{"op":"sound","s":"chime","v":1.0,"pi":0.4}` — 効果音〔s="chime", v=1.0, pi=0.4〕
05. `{"op":"fx","p":"end_rod","n":44,"at":"ring","r":10}` — 粒子演出〔p="end_rod", n=44, at="ring", r=10〕
06. `{"op":"cone","r":20,"a":120}` — 扇形対象の取得〔r=20, a=120〕
07. `{"op":"dmg","m":1.68}` — 追加攻撃〔m=1.68〕
08. `{"op":"knock","f":4.0}` — knock〔f=4.0〕
09. `{"op":"allies","r":20}` — 味方対象〔r=20〕
10. `{"op":"healpct","v":0.25,"to":1}` — 最大HP割合回復〔v=0.25, to=1〕
11. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"water","t":600,"a":0}` — 強化〔e="water", t=600, a=0〕
14. `{"op":"buff","e":"dolphin","t":300,"a":1}` — 強化〔e="dolphin", t=300, a=1〕
15. `{"op":"fx","p":"splash","n":12,"at":"t","s":0.5}` — 粒子演出〔p="splash", n=12, at="t", s=0.5〕
16. `{"op":"fx","p":"bubble","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="bubble", n=46, at="ring", r=5.5, y=0.25〕
17. `{"op":"fx","p":"splash","n":36,"at":"line","r":24}` — 粒子演出〔p="splash", n=36, at="line", r=24〕
18. `{"op":"cone","r":34.0,"a":120.0}` — 扇形対象の取得〔r=34.0, a=120.0〕
19. `{"op":"dmg","m":2.5}` — 追加攻撃〔m=2.5〕
20. `{"op":"knock","f":2.4}` — knock〔f=2.4〕
21. `{"op":"fx","p":"bubble","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="bubble", n=16, at="ring", r=5.0〕
22. `{"op":"sound","s":"sonic","v":0.75,"pi":1.15}` — 効果音〔s="sonic", v=0.75, pi=1.15〕
23. `{"op":"cone","r":11,"a":85}` — 扇形対象の取得〔r=11, a=85〕
24. `{"op":"dmg","m":1.0}` — 追加攻撃〔m=1.0〕
25. `{"op":"eff","e":"slow","t":65,"a":0}` — 敵への状態異常〔e="slow", t=65, a=0〕
26. `{"op":"fx","p":"splash","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="splash", n=24, at="ring", r=4.5, y=0.6〕
27. `{"op":"sound","s":"chime","v":0.8,"pi":0.8}` — 効果音〔s="chime", v=0.8, pi=0.8〕
28. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
29. `{"op":"eff","e":"slow","t":32,"a":124}` — 敵への状態異常〔e="slow", t=32, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 海洋循環の珊瑚杖 — 神威触媒（Curios relic_focus） (`bahamut_focus`)

**現行パラメータ**：rank=2、damage登録値=73.7748、relics側CD=155tick、art側CD=155tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"allies","r":16}` — 味方対象〔r=16〕
02. `{"op":"buff","e":"regen","t":40,"a":0,"to":1}` — 強化〔e="regen", t=40, a=0, to=1〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"water","t":45,"a":0}` — 強化〔e="water", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"water","t":42,"a":2}` — 強化〔e="water", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（42命令）**：

01. `{"op":"fx","p":"bubble","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="bubble", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"bubble","n":6,"at":"self","s":0.7}` — 粒子演出〔p="bubble", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"splash","n":72,"at":"self","s":2.0}` — 粒子演出〔p="splash", n=72, at="self", s=2.0〕
04. `{"op":"sound","s":"chime","v":1.0,"pi":0.4}` — 効果音〔s="chime", v=1.0, pi=0.4〕
05. `{"op":"allies","r":32}` — 味方対象〔r=32〕
06. `{"op":"healpct","v":0.4,"to":1}` — 最大HP割合回復〔v=0.4, to=1〕
07. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
08. `{"op":"buff","e":"regen","t":600,"a":3,"to":1}` — 強化〔e="regen", t=600, a=3, to=1〕
09. `{"op":"buff","e":"water","t":1200,"a":0,"to":1}` — 強化〔e="water", t=1200, a=0, to=1〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"water","t":150,"a":1}` — 強化〔e="water", t=150, a=1〕
13. `{"op":"fx","p":"splash","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="splash", n=50, at="ring", r=8.0, y=0.6〕
14. `{"op":"fx","p":"heart","n":32,"at":"line","r":30}` — 粒子演出〔p="heart", n=32, at="line", r=30〕
15. `{"op":"sound","s":"sonic","v":1.15,"pi":0.95}` — 効果音〔s="sonic", v=1.15, pi=0.95〕
16. `{"op":"allies","r":30.0}` — 味方対象〔r=30.0〕
17. `{"op":"healpct","v":0.45}` — 最大HP割合回復〔v=0.45〕
18. `{"op":"cleanse"}` — 状態異常解除〔〕
19. `{"op":"self"}` — 対象を自分へ〔〕
20. `{"op":"buff","e":"water","t":180,"a":2}` — 強化〔e="water", t=180, a=2〕
21. `{"op":"self"}` — 対象を自分へ〔〕
22. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
23. `{"op":"buff","e":"regen","t":150,"a":3}` — 強化〔e="regen", t=150, a=3〕
24. `{"op":"fx","p":"splash","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="splash", n=24, at="ring", r=12, y=0.5〕
25. `{"op":"sound","s":"chime","v":0.85,"pi":0.97}` — 効果音〔s="chime", v=0.85, pi=0.97〕
26. `{"op":"allies","r":20.0}` — 味方対象〔r=20.0〕
27. `{"op":"healpct","v":0.14,"to":1}` — 最大HP割合回復〔v=0.14, to=1〕
28. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
29. `{"op":"self"}` — 対象を自分へ〔〕
30. `{"op":"buff","e":"water","t":200,"a":3}` — 強化〔e="water", t=200, a=3〕
31. `{"op":"allies","r":26.0}` — 味方対象〔r=26.0〕
32. `{"op":"healpct","v":0.14,"to":1}` — 最大HP割合回復〔v=0.14, to=1〕
33. `{"op":"fx","p":"splash","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="splash", n=24, at="ring", r=5.5, y=0.7〕
34. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
35. `{"op":"eff","e":"slow","t":43,"a":123}` — 敵への状態異常〔e="slow", t=43, a=123〕
36. `{"op":"self"}` — 対象を自分へ〔〕
37. `{"op":"buff","e":"water","t":160,"a":0}` — 強化〔e="water", t=160, a=0〕
38. `{"op":"fx","p":"splash","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="splash", n=16, at="ring", r=3.7, y=0.55〕
39. `{"op":"allies","r":18.0}` — 味方対象〔r=18.0〕
40. `{"op":"healpct","v":0.24}` — 最大HP割合回復〔v=0.24〕
41. `{"op":"cleanse"}` — 状態異常解除〔〕
42. `{"op":"buff","e":"regen","t":130,"a":3}` — 強化〔e="regen", t=130, a=3〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 浅海調停の鱗飾り — 神格装飾品（Curios relic_charm） (`bahamut_charm`)

**現行パラメータ**：rank=1、damage登録値=73.7748、relics側CD=185tick、art側CD=185tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（13命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"water","t":300,"a":0}` — 強化〔e="water", t=300, a=0〕
03. `{"op":"buff","e":"dolphin","t":40,"a":2}` — 強化〔e="dolphin", t=40, a=2〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"water","t":45,"a":0}` — 強化〔e="water", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
09. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"water","t":42,"a":2}` — 強化〔e="water", t=42, a=2〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"regen","t":48,"a":5}` — 強化〔e="regen", t=48, a=5〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（37命令）**：

01. `{"op":"fx","p":"bubble","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="bubble", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"bubble","n":4,"at":"self","s":0.7}` — 粒子演出〔p="bubble", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"splash","n":72,"at":"self","s":2.0}` — 粒子演出〔p="splash", n=72, at="self", s=2.0〕
04. `{"op":"sound","s":"chime","v":1.0,"pi":0.4}` — 効果音〔s="chime", v=1.0, pi=0.4〕
05. `{"op":"area","r":20,"n":36}` — 円形対象の取得〔r=20, n=36〕
06. `{"op":"knock","f":3.0}` — knock〔f=3.0〕
07. `{"op":"eff","e":"slow","t":200,"a":3}` — 敵への状態異常〔e="slow", t=200, a=3〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"cleanse"}` — 状態異常解除〔〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"water","t":210,"a":1}` — 強化〔e="water", t=210, a=1〕
13. `{"op":"fx","p":"bubble","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="bubble", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"splash","n":36,"at":"line","r":24}` — 粒子演出〔p="splash", n=36, at="line", r=24〕
15. `{"op":"sound","s":"sonic","v":1.05,"pi":1.14}` — 効果音〔s="sonic", v=1.05, pi=1.14〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"guard","t":95}` — 防御〔t=95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
20. `{"op":"cleanse"}` — 状態異常解除〔〕
21. `{"op":"buff","e":"regen","t":180,"a":3}` — 強化〔e="regen", t=180, a=3〕
22. `{"op":"guard","t":95}` — 防御〔t=95〕
23. `{"op":"fx","p":"splash","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="splash", n=30, at="ring", r=4.0, y=0.7〕
24. `{"op":"sound","s":"chime","v":0.8,"pi":1.1}` — 効果音〔s="chime", v=0.8, pi=1.1〕
25. `{"op":"self"}` — 対象を自分へ〔〕
26. `{"op":"buff","e":"water","t":260,"a":4}` — 強化〔e="water", t=260, a=4〕
27. `{"op":"guard","t":140}` — 防御〔t=140〕
28. `{"op":"allies","r":26.0}` — 味方対象〔r=26.0〕
29. `{"op":"healpct","v":0.14,"to":1}` — 最大HP割合回復〔v=0.14, to=1〕
30. `{"op":"fx","p":"splash","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="splash", n=20, at="ring", r=4, y=0.4〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"water","t":160,"a":0}` — 強化〔e="water", t=160, a=0〕
33. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
34. `{"op":"eff","e":"slow","t":32,"a":123}` — 敵への状態異常〔e="slow", t=32, a=123〕
35. `{"op":"allies","r":16}` — 味方対象〔r=16〕
36. `{"op":"healpct","v":0.18}` — 最大HP割合回復〔v=0.18〕
37. `{"op":"cleanse"}` — 状態異常解除〔〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 海理皇権・世界潮歌 — 超越神器（武器欄） (`bahamut_legend`)

**現行パラメータ**：rank=3、damage登録値=1157.875、relics側CD=340tick、art側CD=340tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（11命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"allies","r":16}` — 味方対象〔r=16〕
06. `{"op":"buff","e":"regen","t":40,"a":1,"to":1}` — 強化〔e="regen", t=40, a=1, to=1〕
07. `{"op":"buff","e":"water","t":300,"a":0}` — 強化〔e="water", t=300, a=0〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
10. `{"op":"buff","e":"regen","t":45,"a":3}` — 強化〔e="regen", t=45, a=3〕
11. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（8命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"knock","f":3.0}` — knock〔f=3.0〕
03. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"slow","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"slow","t":160,"a":1}]〕
04. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"bubble","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"bubble","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
05. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"splash","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"splash","n":10,"at":"t","s":0.35}]〕
06. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
07. `{"op":"chance","p":0.325,"ops":[{"op":"victim"},{"op":"fx","p":"splash","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.325, ops=[{"op":"victim"},{"op":"fx","p":"splash","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]〕
08. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"splash","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"splash","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]〕

**権能発動時の命令（24命令）**：

01. `{"op":"fx","p":"bubble","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="bubble", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"bubble","n":4,"at":"self","s":0.7}` — 粒子演出〔p="bubble", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"splash","n":72,"at":"self","s":2.0}` — 粒子演出〔p="splash", n=72, at="self", s=2.0〕
04. `{"op":"sound","s":"chime","v":1.0,"pi":0.4}` — 効果音〔s="chime", v=1.0, pi=0.4〕
05. `{"op":"fx","p":"end_rod","n":44,"at":"ring","r":10}` — 粒子演出〔p="end_rod", n=44, at="ring", r=10〕
06. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
07. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
08. `{"op":"launch","f":2.0}` — launch〔f=2.0〕
09. `{"op":"knock","f":6.0}` — knock〔f=6.0〕
10. `{"op":"allies","r":48}` — 味方対象〔r=48〕
11. `{"op":"healpct","v":0.6,"to":1}` — 最大HP割合回復〔v=0.6, to=1〕
12. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
13. `{"op":"buff","e":"regen","t":1200,"a":4,"to":1}` — 強化〔e="regen", t=1200, a=4, to=1〕
14. `{"op":"undying","t":180,"to":1}` — 死亡防護〔t=180, to=1〕
15. `{"op":"fx","p":"splash","n":12,"at":"t","s":0.5}` — 粒子演出〔p="splash", n=12, at="t", s=0.5〕
16. `{"op":"cone","r":36,"a":85}` — 扇形対象の取得〔r=36, a=85〕
17. `{"op":"dmg","m":1.6}` — 追加攻撃〔m=1.6〕
18. `{"op":"knock","f":2.5}` — knock〔f=2.5〕
19. `{"op":"fx","p":"splash","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="splash", n=50, at="ring", r=8.0, y=0.6〕
20. `{"op":"fx","p":"heart","n":32,"at":"line","r":30}` — 粒子演出〔p="heart", n=32, at="line", r=30〕
21. `{"op":"sound","s":"sonic","v":1.15,"pi":0.95}` — 効果音〔s="sonic", v=1.15, pi=0.95〕
22. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.bahamut_legend.stage0","ops":[{"op":"fx","p":"splash","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"chime","v":0.9,"pi":1.2},{"op":"fx","p":"splash","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"bubble","n":6,"at":"line","r":10},{"op":"fx","p":"bubble","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"splash","n":36,"at":"line","r":24},{"op":"sound","s":"sonic","v":1.05,"pi":1.14},{"op":"cone","r":34.0,"a":120.0},{"op":"dmg","m":3.375},{"op":"knock","f":2.4},{"op":"self"},{"op":"buff","e":"water","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.bahamut_legend.stage1","ops":[{"op":"fx","p":"splash","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"chime","v":1.05,"pi":1.0},{"op":"fx","p":"bubble","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"splash","n":6,"at":"line","r":15},{"op":"fx","p":"splash","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"heart","n":32,"at":"line","r":30},{"op":"sound","s":"sonic","v":1.15,"pi":0.95},{"op":"allies","r":30.0},{"op":"healpct","v":0.45},{"op":"cleanse"},{"op":"self"},{"op":"buff","e":"water","t":180,"a":2},{"op":"area","r":14.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.bahamut_legend.stage2","ops":[{"op":"fx","p":"splash","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"chime","v":1.25,"pi":0.75},{"op":"fx","p":"bubble","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"splash","n":10,"at":"line","r":20},{"op":"fx","p":"bubble","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"splash","n":48,"at":"line","r":48},{"op":"fx","p":"heart","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"sonic","v":1.5,"pi":0.75},{"op":"area","r":36.0,"n":28},{"op":"dmg","m":9.072},{"op":"launch","f":1.7},{"op":"allies","r":34.0},{"op":"healpct","v":0.6},{"op":"cleanse"},{"op":"fx","p":"heart","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"splash","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":30.0,"n":24},{"op":"dmg","m":2.5},{"op":"allies","r":36.0},{"op":"healpct","v":0.75},{"op":"cleanse"},{"op":"self"},{"op":"buff","e":"regen","t":180,"a":3},{"op":"allies","r":34.0},{"op":"healpct","v":0.28,"to":1},{"op":"cleanse","to":1},{"op":"self"},{"op":"guard","t":180},{"op":"allies","r":26.0},{"op":"healpct","v":0.14,"to":1},{"op":"fx","p":"splash","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"chime","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"allies","r":22},{"op":"healpct","v":0.24},{"op":"cleanse"},{"op":"guard","t":110}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.bahamut_legend.stage0","ops":[{"op":"fx","p":"splash","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"chime","v":0.9,"pi":1.2},{"op":"fx","p":"splash","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"bubble","n":6,"at":"line","r":10},{"op":"fx","p":"bubble","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"splash","n":36,"at":"line","r":24},{"op":"sound","s":"sonic","v":1.05,"pi":1.14},{"op":"cone","r":34.0,"a":120.0},{"op":"dmg","m":3.375},{"op":"knock","f":2.4},{"op":"self"},{"op":"buff","e":"water","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.bahamut_legend.stage1","ops":[{"op":"fx","p":"splash","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"chime","v":1.05,"pi":1.0},{"op":"fx","p":"bubble","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"splash","n":6,"at":"line","r":15},{"op":"fx","p":"splash","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"heart","n":32,"at":"line","r":30},{"op":"sound","s":"sonic","v":1.15,"pi":0.95},{"op":"allies","r":30.0},{"op":"healpct","v":0.45},{"op":"cleanse"},{"op":"self"},{"op":"buff","e":"water","t":180,"a":2},{"op":"area","r":14.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.bahamut_legend.stage2","ops":[{"op":"fx","p":"splash","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"chime","v":1.25,"pi":0.75},{"op":"fx","p":"bubble","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"splash","n":10,"at":"line","r":20},{"op":"fx","p":"bubble","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"splash","n":48,"at":"line","r":48},{"op":"fx","p":"heart","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"sonic","v":1.5,"pi":0.75},{"op":"area","r":36.0,"n":28},{"op":"dmg","m":9.072},{"op":"launch","f":1.7},{"op":"allies","r":34.0},{"op":"healpct","v":0.6},{"op":"cleanse"},{"op":"fx","p":"heart","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"splash","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":30.0,"n":24},{"op":"dmg","m":2.5},{"op":"allies","r":36.0},{"op":"healpct","v":0.75},{"op":"cleanse"},{"op":"self"},{"op":"buff","e":"regen","t":180,"a":3},{"op":"allies","r":34.0},{"op":"healpct","v":0.28,"to":1},{"op":"cleanse","to":1},{"op":"self"},{"op":"guard","t":180},{"op":"allies","r":26.0},{"op":"healpct","v":0.14,"to":1},{"op":"fx","p":"splash","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"chime","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"allies","r":22},{"op":"healpct","v":0.24},{"op":"cleanse"},{"op":"guard","t":110}]}]〕
23. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
24. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 23. 天変万化 ヌン

**モブ側の動きの方向性**：体の部位ごとに獣・液体・結晶へ変え、攻撃途中でも形態を移す。。

### 天変万化の道化杖 — 討伐武器（メイン／武器欄） (`nun_weapon`)

**現行パラメータ**：rank=1、damage登録値=578.5、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（4命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"adapt","t":40}` — adapt〔t=40〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（8命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
03. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"nausea","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"nausea","t":90,"a":0}]〕
04. `{"op":"chance","p":0.51,"ops":[{"op":"victim"},{"op":"fx","p":"portal","n":13,"at":"t","s":0.24},{"op":"mark","t":160,"x":1.93},{"op":"eff","e":"nausea","t":65,"a":0}]}` — 抽選〔p=0.51, ops=[{"op":"victim"},{"op":"fx","p":"portal","n":13,"at":"t","s":0.24},{"op":"mark","t":160,"x":1.93},{"op":"eff","e":"nausea","t":65,"a":0}]〕
05. `{"op":"chance","p":0.204,"ops":[{"op":"victim"},{"op":"dmg","m":0.27}]}` — 抽選〔p=0.204, ops=[{"op":"victim"},{"op":"dmg","m":0.27}]〕
06. `{"op":"chance","p":0.123,"ops":[{"op":"victim"},{"op":"fx","p":"portal","n":8,"at":"t","s":0.25},{"op":"strip"}]}` — 抽選〔p=0.123, ops=[{"op":"victim"},{"op":"fx","p":"portal","n":8,"at":"t","s":0.25},{"op":"strip"}]〕
07. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"portal","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"portal","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]〕
08. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"portal","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"portal","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]〕

**権能発動時の命令（25命令）**：

01. `{"op":"fx","p":"portal","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="portal", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"portal","n":4,"at":"self","s":0.7}` — 粒子演出〔p="portal", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"smoke","n":40,"at":"self"}` — 粒子演出〔p="smoke", n=40, at="self"〕
04. `{"op":"fx","p":"witch","n":20,"at":"self"}` — 粒子演出〔p="witch", n=20, at="self"〕
05. `{"op":"sound","s":"mirror","v":1.0,"pi":1.0}` — 効果音〔s="mirror", v=1.0, pi=1.0〕
06. `{"op":"area","r":16,"n":36}` — 円形対象の取得〔r=16, n=36〕
07. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
08. `{"op":"dmg","m":1.44}` — 追加攻撃〔m=1.44〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"adapt","t":300}` — adapt〔t=300〕
11. `{"op":"fx","p":"smoke","n":12,"at":"t","s":0.5}` — 粒子演出〔p="smoke", n=12, at="t", s=0.5〕
12. `{"op":"fx","p":"witch","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="witch", n=46, at="ring", r=5.5, y=0.25〕
13. `{"op":"fx","p":"splash","n":36,"at":"line","r":24}` — 粒子演出〔p="splash", n=36, at="line", r=24〕
14. `{"op":"cone","r":24.0,"a":115.0}` — 扇形対象の取得〔r=24.0, a=115.0〕
15. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
16. `{"op":"eff","e":"nausea","t":100,"a":0}` — 敵への状態異常〔e="nausea", t=100, a=0〕
17. `{"op":"fx","p":"portal","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="portal", n=16, at="ring", r=5.0〕
18. `{"op":"sound","s":"spell","v":0.75,"pi":1.15}` — 効果音〔s="spell", v=0.75, pi=1.15〕
19. `{"op":"area","r":9,"n":8}` — 円形対象の取得〔r=9, n=8〕
20. `{"op":"dmg","m":0.9}` — 追加攻撃〔m=0.9〕
21. `{"op":"eff","e":"weakness","t":65,"a":0}` — 敵への状態異常〔e="weakness", t=65, a=0〕
22. `{"op":"fx","p":"portal","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="portal", n=24, at="ring", r=4.5, y=0.6〕
23. `{"op":"sound","s":"mirror","v":0.8,"pi":0.8}` — 効果音〔s="mirror", v=0.8, pi=0.8〕
24. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
25. `{"op":"eff","e":"weakness","t":100,"a":124}` — 敵への状態異常〔e="weakness", t=100, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 万化の仮面 — 神威触媒（Curios relic_focus） (`nun_focus`)

**現行パラメータ**：rank=2、damage登録値=68.31、relics側CD=150tick、art側CD=150tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"night","t":300,"a":0}` — 強化〔e="night", t=300, a=0〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"resist","t":45,"a":0}` — 強化〔e="resist", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"speed","t":42,"a":2}` — 強化〔e="speed", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（44命令）**：

01. `{"op":"fx","p":"portal","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="portal", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"portal","n":6,"at":"self","s":0.7}` — 粒子演出〔p="portal", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"smoke","n":40,"at":"self"}` — 粒子演出〔p="smoke", n=40, at="self"〕
04. `{"op":"fx","p":"witch","n":20,"at":"self"}` — 粒子演出〔p="witch", n=20, at="self"〕
05. `{"op":"sound","s":"mirror","v":1.0,"pi":1.0}` — 効果音〔s="mirror", v=1.0, pi=1.0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"invis","t":300,"a":0}` — 強化〔e="invis", t=300, a=0〕
08. `{"op":"buff","e":"speed","t":300,"a":3}` — 強化〔e="speed", t=300, a=3〕
09. `{"op":"near","r":24,"n":1}` — near〔r=24, n=1〕
10. `{"op":"swap"}` — swap〔〕
11. `{"op":"area","r":12,"n":36}` — 円形対象の取得〔r=12, n=36〕
12. `{"op":"eff","e":"nausea","t":200,"a":0}` — 敵への状態異常〔e="nausea", t=200, a=0〕
13. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
14. `{"op":"self"}` — 対象を自分へ〔〕
15. `{"op":"buff","e":"resist","t":150,"a":1}` — 強化〔e="resist", t=150, a=1〕
16. `{"op":"fx","p":"splash","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="splash", n=50, at="ring", r=8.0, y=0.6〕
17. `{"op":"fx","p":"portal","n":32,"at":"line","r":30}` — 粒子演出〔p="portal", n=32, at="line", r=30〕
18. `{"op":"sound","s":"mirror","v":1.15,"pi":0.95}` — 効果音〔s="mirror", v=1.15, pi=0.95〕
19. `{"op":"self"}` — 対象を自分へ〔〕
20. `{"op":"adapt"}` — adapt〔〕
21. `{"op":"guard","t":130}` — 防御〔t=130〕
22. `{"op":"area","r":20.0,"n":16}` — 円形対象の取得〔r=20.0, n=16〕
23. `{"op":"dmg","m":2.4}` — 追加攻撃〔m=2.4〕
24. `{"op":"self"}` — 対象を自分へ〔〕
25. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
26. `{"op":"buff","e":"resist","t":150,"a":3}` — 強化〔e="resist", t=150, a=3〕
27. `{"op":"fx","p":"portal","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="portal", n=24, at="ring", r=12, y=0.5〕
28. `{"op":"sound","s":"mirror","v":0.85,"pi":1.04}` — 効果音〔s="mirror", v=0.85, pi=1.04〕
29. `{"op":"cone","r":14.0,"a":95.0}` — 扇形対象の取得〔r=14.0, a=95.0〕
30. `{"op":"dmg","m":0.95}` — 追加攻撃〔m=0.95〕
31. `{"op":"eff","e":"weakness","t":140,"a":1}` — 敵への状態異常〔e="weakness", t=140, a=1〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"buff","e":"speed","t":220,"a":3}` — 強化〔e="speed", t=220, a=3〕
34. `{"op":"self"}` — 対象を自分へ〔〕
35. `{"op":"adapt","t":160}` — adapt〔t=160〕
36. `{"op":"fx","p":"portal","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="portal", n=24, at="ring", r=5.5, y=0.7〕
37. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
38. `{"op":"eff","e":"weakness","t":135,"a":123}` — 敵への状態異常〔e="weakness", t=135, a=123〕
39. `{"op":"self"}` — 対象を自分へ〔〕
40. `{"op":"buff","e":"speed","t":120,"a":4}` — 強化〔e="speed", t=120, a=4〕
41. `{"op":"fx","p":"portal","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="portal", n=16, at="ring", r=3.7, y=0.55〕
42. `{"op":"self"}` — 対象を自分へ〔〕
43. `{"op":"guard","t":90}` — 防御〔t=90〕
44. `{"op":"buff","e":"luck","t":160,"a":5}` — 強化〔e="luck", t=160, a=5〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 愚者の旅環 — 神格装飾品（Curios relic_charm） (`nun_charm`)

**現行パラメータ**：rank=1、damage登録値=68.31、relics側CD=180tick、art側CD=180tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（13命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"luck","t":40,"a":2}` — 強化〔e="luck", t=40, a=2〕
03. `{"op":"buff","e":"speed","t":40,"a":0}` — 強化〔e="speed", t=40, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"resist","t":45,"a":0}` — 強化〔e="resist", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
09. `{"op":"buff","e":"resist","t":45,"a":1}` — 強化〔e="resist", t=45, a=1〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"speed","t":42,"a":2}` — 強化〔e="speed", t=42, a=2〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"luck","t":48,"a":8}` — 強化〔e="luck", t=48, a=8〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（36命令）**：

01. `{"op":"fx","p":"portal","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="portal", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"portal","n":4,"at":"self","s":0.7}` — 粒子演出〔p="portal", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"smoke","n":40,"at":"self"}` — 粒子演出〔p="smoke", n=40, at="self"〕
04. `{"op":"fx","p":"witch","n":20,"at":"self"}` — 粒子演出〔p="witch", n=20, at="self"〕
05. `{"op":"sound","s":"mirror","v":1.0,"pi":1.0}` — 効果音〔s="mirror", v=1.0, pi=1.0〕
06. `{"op":"blink","d":16}` — blink〔d=16〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"buff","e":"luck","t":600,"a":5}` — 強化〔e="luck", t=600, a=5〕
09. `{"op":"guard","t":20}` — 防御〔t=20〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"resist","t":210,"a":1}` — 強化〔e="resist", t=210, a=1〕
13. `{"op":"fx","p":"witch","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="witch", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"splash","n":36,"at":"line","r":24}` — 粒子演出〔p="splash", n=36, at="line", r=24〕
15. `{"op":"sound","s":"mirror","v":1.05,"pi":1.14}` — 効果音〔s="mirror", v=1.05, pi=1.14〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"guard","t":95}` — 防御〔t=95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
20. `{"op":"cleanse"}` — 状態異常解除〔〕
21. `{"op":"buff","e":"resist","t":180,"a":3}` — 強化〔e="resist", t=180, a=3〕
22. `{"op":"guard","t":95}` — 防御〔t=95〕
23. `{"op":"fx","p":"portal","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="portal", n=30, at="ring", r=4.0, y=0.7〕
24. `{"op":"sound","s":"mirror","v":0.8,"pi":1.1}` — 効果音〔s="mirror", v=0.8, pi=1.1〕
25. `{"op":"self"}` — 対象を自分へ〔〕
26. `{"op":"buff","e":"speed","t":280,"a":4}` — 強化〔e="speed", t=280, a=4〕
27. `{"op":"guard","t":155}` — 防御〔t=155〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"buff","e":"speed","t":240,"a":2}` — 強化〔e="speed", t=240, a=2〕
30. `{"op":"fx","p":"portal","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="portal", n=20, at="ring", r=4, y=0.4〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"speed","t":120,"a":4}` — 強化〔e="speed", t=120, a=4〕
33. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
34. `{"op":"eff","e":"weakness","t":100,"a":123}` — 敵への状態異常〔e="weakness", t=100, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 存在万化・無限の仮面 — 超越神器（武器欄） (`nun_legend`)

**現行パラメータ**：rank=3、damage登録値=1157.875、relics側CD=335tick、art側CD=335tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"adapt","t":40}` — adapt〔t=40〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
08. `{"op":"buff","e":"resist","t":45,"a":3}` — 強化〔e="resist", t=45, a=3〕
09. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（9命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
03. `{"op":"dmg","m":0.3}` — 追加攻撃〔m=0.3〕
04. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"nausea","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"nausea","t":160,"a":1}]〕
05. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"witch","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"witch","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
06. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"nausea","t":135,"a":2},{"op":"fx","p":"portal","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"nausea","t":135,"a":2},{"op":"fx","p":"portal","n":10,"at":"t","s":0.35}]〕
07. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
08. `{"op":"chance","p":0.35,"ops":[{"op":"victim"},{"op":"fx","p":"portal","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.35, ops=[{"op":"victim"},{"op":"fx","p":"portal","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]〕
09. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"portal","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"portal","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]〕

**権能発動時の命令（22命令）**：

01. `{"op":"fx","p":"portal","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="portal", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"portal","n":4,"at":"self","s":0.7}` — 粒子演出〔p="portal", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"smoke","n":40,"at":"self"}` — 粒子演出〔p="smoke", n=40, at="self"〕
04. `{"op":"fx","p":"witch","n":20,"at":"self"}` — 粒子演出〔p="witch", n=20, at="self"〕
05. `{"op":"sound","s":"mirror","v":1.0,"pi":1.0}` — 効果音〔s="mirror", v=1.0, pi=1.0〕
06. `{"op":"area","r":40,"n":36}` — 円形対象の取得〔r=40, n=36〕
07. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
08. `{"op":"each","ops":[{"op":"dmg","m":2.5},{"op":"stun","t":105},{"op":"launch","f":3.0},{"op":"freeze","t":400}]}` — each〔ops=[{"op":"dmg","m":2.5},{"op":"stun","t":105},{"op":"launch","f":3.0},{"op":"freeze","t":400}]〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"adapt","t":1200}` — adapt〔t=1200〕
11. `{"op":"undying","t":180}` — 死亡防護〔t=180〕
12. `{"op":"buff","e":"strength","t":600,"a":9}` — 強化〔e="strength", t=600, a=9〕
13. `{"op":"fx","p":"smoke","n":12,"at":"t","s":0.5}` — 粒子演出〔p="smoke", n=12, at="t", s=0.5〕
14. `{"op":"area","r":26,"n":24}` — 円形対象の取得〔r=26, n=24〕
15. `{"op":"dmg","m":1.3}` — 追加攻撃〔m=1.3〕
16. `{"op":"eff","e":"nausea","t":95,"a":0}` — 敵への状態異常〔e="nausea", t=95, a=0〕
17. `{"op":"fx","p":"splash","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="splash", n=50, at="ring", r=8.0, y=0.6〕
18. `{"op":"fx","p":"portal","n":32,"at":"line","r":30}` — 粒子演出〔p="portal", n=32, at="line", r=30〕
19. `{"op":"sound","s":"mirror","v":1.15,"pi":0.95}` — 効果音〔s="mirror", v=1.15, pi=0.95〕
20. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.nun_legend.stage0","ops":[{"op":"fx","p":"portal","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"mirror","v":0.9,"pi":1.2},{"op":"fx","p":"portal","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"crit","n":6,"at":"line","r":10},{"op":"fx","p":"witch","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"splash","n":36,"at":"line","r":24},{"op":"sound","s":"mirror","v":1.05,"pi":1.14},{"op":"cone","r":24.0,"a":115.0},{"op":"dmg","m":3.78},{"op":"eff","e":"nausea","t":100,"a":0},{"op":"self"},{"op":"buff","e":"speed","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.nun_legend.stage1","ops":[{"op":"fx","p":"portal","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"mirror","v":1.05,"pi":1.0},{"op":"fx","p":"crit","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"portal","n":6,"at":"line","r":15},{"op":"fx","p":"splash","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"portal","n":32,"at":"line","r":30},{"op":"sound","s":"mirror","v":1.15,"pi":0.95},{"op":"self"},{"op":"adapt"},{"op":"guard","t":130},{"op":"area","r":20.0,"n":16},{"op":"dmg","m":3.48},{"op":"area","r":16.0,"n":10},{"op":"eff","e":"weakness","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.nun_legend.stage2","ops":[{"op":"fx","p":"portal","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"mirror","v":1.25,"pi":0.75},{"op":"fx","p":"crit","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"portal","n":10,"at":"line","r":20},{"op":"fx","p":"witch","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"splash","n":48,"at":"line","r":48},{"op":"fx","p":"portal","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"mirror","v":1.5,"pi":0.75},{"op":"area","r":34.0,"n":28},{"op":"dmg","m":9.882},{"op":"stun","t":55},{"op":"self"},{"op":"buff","e":"resist","t":160,"a":4},{"op":"buff","e":"speed","t":150,"a":3},{"op":"fx","p":"portal","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"portal","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":30.0,"n":26},{"op":"dmg","m":2.9},{"op":"self"},{"op":"adapt"},{"op":"buff","e":"resist","t":180,"a":3},{"op":"cone","r":27.0,"a":110.0},{"op":"dmg","m":1.0},{"op":"eff","e":"weakness","t":160,"a":2},{"op":"self"},{"op":"buff","e":"speed","t":240,"a":4},{"op":"self"},{"op":"adapt","t":160},{"op":"fx","p":"portal","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"mirror","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"weakness","t":60,"a":8},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.nun_legend.stage0","ops":[{"op":"fx","p":"portal","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"mirror","v":0.9,"pi":1.2},{"op":"fx","p":"portal","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"crit","n":6,"at":"line","r":10},{"op":"fx","p":"witch","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"splash","n":36,"at":"line","r":24},{"op":"sound","s":"mirror","v":1.05,"pi":1.14},{"op":"cone","r":24.0,"a":115.0},{"op":"dmg","m":3.78},{"op":"eff","e":"nausea","t":100,"a":0},{"op":"self"},{"op":"buff","e":"speed","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.nun_legend.stage1","ops":[{"op":"fx","p":"portal","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"mirror","v":1.05,"pi":1.0},{"op":"fx","p":"crit","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"portal","n":6,"at":"line","r":15},{"op":"fx","p":"splash","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"portal","n":32,"at":"line","r":30},{"op":"sound","s":"mirror","v":1.15,"pi":0.95},{"op":"self"},{"op":"adapt"},{"op":"guard","t":130},{"op":"area","r":20.0,"n":16},{"op":"dmg","m":3.48},{"op":"area","r":16.0,"n":10},{"op":"eff","e":"weakness","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.nun_legend.stage2","ops":[{"op":"fx","p":"portal","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"mirror","v":1.25,"pi":0.75},{"op":"fx","p":"crit","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"portal","n":10,"at":"line","r":20},{"op":"fx","p":"witch","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"splash","n":48,"at":"line","r":48},{"op":"fx","p":"portal","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"mirror","v":1.5,"pi":0.75},{"op":"area","r":34.0,"n":28},{"op":"dmg","m":9.882},{"op":"stun","t":55},{"op":"self"},{"op":"buff","e":"resist","t":160,"a":4},{"op":"buff","e":"speed","t":150,"a":3},{"op":"fx","p":"portal","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"portal","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":30.0,"n":26},{"op":"dmg","m":2.9},{"op":"self"},{"op":"adapt"},{"op":"buff","e":"resist","t":180,"a":3},{"op":"cone","r":27.0,"a":110.0},{"op":"dmg","m":1.0},{"op":"eff","e":"weakness","t":160,"a":2},{"op":"self"},{"op":"buff","e":"speed","t":240,"a":4},{"op":"self"},{"op":"adapt","t":160},{"op":"fx","p":"portal","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"mirror","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"weakness","t":60,"a":8},{"op":"mark","t":135,"x":1.8}]}]〕
21. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
22. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 24. 運命流転 アルカナ

**モブ側の動きの方向性**：運命糸を指で張り、分岐を結び、結果が閉じる瞬間を見せる。。

### 運命流転の糸巻杖 — 討伐武器（メイン／武器欄） (`arcana_weapon`)

**現行パラメータ**：rank=1、damage登録値=578.5、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（5命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"luck","t":40,"a":3}` — 強化〔e="luck", t=40, a=3〕
03. `{"op":"reflect","t":25,"r":5}` — 反射〔t=25, r=5〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（7命令）**：

01. `{"op":"chance","p":0.35,"ops":[{"op":"victim"},{"op":"dmg","m":1.0}]}` — 抽選〔p=0.35, ops=[{"op":"victim"},{"op":"dmg","m":1.0}]〕
02. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"glow","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"glow","t":90,"a":0}]〕
03. `{"op":"chance","p":0.515,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":15,"at":"t","s":0.24},{"op":"mark","t":180,"x":2.07},{"op":"eff","e":"slow","t":115,"a":0}]}` — 抽選〔p=0.515, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":15,"at":"t","s":0.24},{"op":"mark","t":180,"x":2.07},{"op":"eff","e":"slow","t":115,"a":0}]〕
04. `{"op":"chance","p":0.231,"ops":[{"op":"victim"},{"op":"dmg","m":0.305}]}` — 抽選〔p=0.231, ops=[{"op":"victim"},{"op":"dmg","m":0.305}]〕
05. `{"op":"chance","p":0.142,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":8,"at":"t","s":0.25},{"op":"eff","e":"glow","t":75,"a":0}]}` — 抽選〔p=0.142, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":8,"at":"t","s":0.25},{"op":"eff","e":"glow","t":75,"a":0}]〕
06. `{"op":"chance","p":0.24,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.24, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]〕
07. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":32,"a":3}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":32,"a":3}]〕

**権能発動時の命令（26命令）**：

01. `{"op":"fx","p":"enchant","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="enchant", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"enchant","n":4,"at":"self","s":0.7}` — 粒子演出〔p="enchant", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":40,"at":"ring","r":3}` — 粒子演出〔p="end_rod", n=40, at="ring", r=3〕
04. `{"op":"fx","p":"enchant","n":40,"at":"self"}` — 粒子演出〔p="enchant", n=40, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":1.2}` — 効果音〔s="chime", v=1.0, pi=1.2〕
06. `{"op":"chain","n":8,"r":12}` — chain〔n=8, r=12〕
07. `{"op":"dmg","m":1.44}` — 追加攻撃〔m=1.44〕
08. `{"op":"mark","t":300,"x":2.0}` — 刻印〔t=300, x=2.0〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"luck","t":600,"a":5}` — 強化〔e="luck", t=600, a=5〕
11. `{"op":"reflect","t":100,"r":16}` — 反射〔t=100, r=16〕
12. `{"op":"fx","p":"end_rod","n":12,"at":"t","s":0.5}` — 粒子演出〔p="end_rod", n=12, at="t", s=0.5〕
13. `{"op":"fx","p":"enchant","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="enchant", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"portal","n":36,"at":"line","r":24}` — 粒子演出〔p="portal", n=36, at="line", r=24〕
15. `{"op":"chain","n":5,"r":20.0}` — chain〔n=5, r=20.0〕
16. `{"op":"mark","t":170,"x":2.0}` — 刻印〔t=170, x=2.0〕
17. `{"op":"dmg","m":2.6}` — 追加攻撃〔m=2.6〕
18. `{"op":"fx","p":"enchant","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="enchant", n=16, at="ring", r=5.0〕
19. `{"op":"sound","s":"spell","v":0.75,"pi":1.15}` — 効果音〔s="spell", v=0.75, pi=1.15〕
20. `{"op":"chain","n":4,"r":12}` — chain〔n=4, r=12〕
21. `{"op":"dmg","m":1.0}` — 追加攻撃〔m=1.0〕
22. `{"op":"eff","e":"slow","t":65,"a":0}` — 敵への状態異常〔e="slow", t=65, a=0〕
23. `{"op":"fx","p":"enchant","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="enchant", n=24, at="ring", r=4.5, y=0.6〕
24. `{"op":"sound","s":"mirror","v":0.8,"pi":0.8}` — 効果音〔s="mirror", v=0.8, pi=0.8〕
25. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
26. `{"op":"eff","e":"slow","t":32,"a":124}` — 敵への状態異常〔e="slow", t=32, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 幸福編成の天羽 — 神威触媒（Curios relic_focus） (`arcana_focus`)

**現行パラメータ**：rank=2、damage登録値=68.31、relics側CD=145tick、art側CD=145tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"allies","r":12}` — 味方対象〔r=12〕
02. `{"op":"buff","e":"luck","t":40,"a":1,"to":1}` — 強化〔e="luck", t=40, a=1, to=1〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"luck","t":45,"a":0}` — 強化〔e="luck", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"luck","t":45,"a":2}` — 強化〔e="luck", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"luck","t":42,"a":2}` — 強化〔e="luck", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（40命令）**：

01. `{"op":"fx","p":"enchant","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="enchant", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"enchant","n":6,"at":"self","s":0.7}` — 粒子演出〔p="enchant", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":40,"at":"ring","r":3}` — 粒子演出〔p="end_rod", n=40, at="ring", r=3〕
04. `{"op":"fx","p":"enchant","n":40,"at":"self"}` — 粒子演出〔p="enchant", n=40, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":1.2}` — 効果音〔s="chime", v=1.0, pi=1.2〕
06. `{"op":"allies","r":32}` — 味方対象〔r=32〕
07. `{"op":"healpct","v":0.4,"to":1}` — 最大HP割合回復〔v=0.4, to=1〕
08. `{"op":"undying","t":100,"to":1}` — 死亡防護〔t=100, to=1〕
09. `{"op":"buff","e":"luck","t":1200,"a":5,"to":1}` — 強化〔e="luck", t=1200, a=5, to=1〕
10. `{"op":"buff","e":"absorb","t":600,"a":4,"to":1}` — 強化〔e="absorb", t=600, a=4, to=1〕
11. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"luck","t":150,"a":1}` — 強化〔e="luck", t=150, a=1〕
14. `{"op":"fx","p":"portal","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="portal", n=50, at="ring", r=8.0, y=0.6〕
15. `{"op":"fx","p":"end_rod","n":32,"at":"line","r":30}` — 粒子演出〔p="end_rod", n=32, at="line", r=30〕
16. `{"op":"sound","s":"totem","v":1.15,"pi":0.95}` — 効果音〔s="totem", v=1.15, pi=0.95〕
17. `{"op":"area","r":26.0,"n":22}` — 円形対象の取得〔r=26.0, n=22〕
18. `{"op":"eff","e":"slow","t":110,"a":2}` — 敵への状態異常〔e="slow", t=110, a=2〕
19. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
20. `{"op":"self"}` — 対象を自分へ〔〕
21. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
22. `{"op":"buff","e":"luck","t":150,"a":3}` — 強化〔e="luck", t=150, a=3〕
23. `{"op":"fx","p":"enchant","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="enchant", n=24, at="ring", r=12, y=0.5〕
24. `{"op":"sound","s":"mirror","v":0.85,"pi":1.11}` — 効果音〔s="mirror", v=0.85, pi=1.11〕
25. `{"op":"line","r":34.0,"w":2.5}` — 線分対象の取得〔r=34.0, w=2.5〕
26. `{"op":"dmg","m":0.85}` — 追加攻撃〔m=0.85〕
27. `{"op":"eff","e":"slow","t":160,"a":1}` — 敵への状態異常〔e="slow", t=160, a=1〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"buff","e":"luck","t":240,"a":3}` — 強化〔e="luck", t=240, a=3〕
30. `{"op":"area","r":20,"n":8}` — 円形対象の取得〔r=20, n=8〕
31. `{"op":"mark","t":140,"x":1.75}` — 刻印〔t=140, x=1.75〕
32. `{"op":"fx","p":"enchant","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="enchant", n=24, at="ring", r=5.5, y=0.7〕
33. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
34. `{"op":"eff","e":"slow","t":43,"a":123}` — 敵への状態異常〔e="slow", t=43, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"buff","e":"luck","t":100,"a":123}` — 強化〔e="luck", t=100, a=123〕
37. `{"op":"fx","p":"enchant","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="enchant", n=16, at="ring", r=3.7, y=0.55〕
38. `{"op":"area","r":16,"n":9}` — 円形対象の取得〔r=16, n=9〕
39. `{"op":"eff","e":"slow","t":65,"a":10}` — 敵への状態異常〔e="slow", t=65, a=10〕
40. `{"op":"mark","t":135,"x":1.8}` — 刻印〔t=135, x=1.8〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 奇跡の運命札 — 神格装飾品（Curios relic_charm） (`arcana_charm`)

**現行パラメータ**：rank=1、damage登録値=68.31、relics側CD=175tick、art側CD=175tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（12命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"luck","t":40,"a":4}` — 強化〔e="luck", t=40, a=4〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"luck","t":45,"a":0}` — 強化〔e="luck", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
08. `{"op":"buff","e":"luck","t":45,"a":1}` — 強化〔e="luck", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"luck","t":42,"a":2}` — 強化〔e="luck", t=42, a=2〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"absorb","t":48,"a":4}` — 強化〔e="absorb", t=48, a=4〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（36命令）**：

01. `{"op":"fx","p":"enchant","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="enchant", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"enchant","n":4,"at":"self","s":0.7}` — 粒子演出〔p="enchant", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":40,"at":"ring","r":3}` — 粒子演出〔p="end_rod", n=40, at="ring", r=3〕
04. `{"op":"fx","p":"enchant","n":40,"at":"self"}` — 粒子演出〔p="enchant", n=40, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":1.2}` — 効果音〔s="chime", v=1.0, pi=1.2〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"undying","t":100}` — 死亡防護〔t=100〕
08. `{"op":"guard","t":60}` — 防御〔t=60〕
09. `{"op":"cleanse"}` — 状態異常解除〔〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"luck","t":210,"a":1}` — 強化〔e="luck", t=210, a=1〕
13. `{"op":"fx","p":"enchant","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="enchant", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"portal","n":36,"at":"line","r":24}` — 粒子演出〔p="portal", n=36, at="line", r=24〕
15. `{"op":"sound","s":"totem","v":1.05,"pi":1.14}` — 効果音〔s="totem", v=1.05, pi=1.14〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"guard","t":95}` — 防御〔t=95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
20. `{"op":"cleanse"}` — 状態異常解除〔〕
21. `{"op":"buff","e":"luck","t":180,"a":3}` — 強化〔e="luck", t=180, a=3〕
22. `{"op":"guard","t":95}` — 防御〔t=95〕
23. `{"op":"fx","p":"enchant","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="enchant", n=30, at="ring", r=4.0, y=0.7〕
24. `{"op":"sound","s":"mirror","v":0.8,"pi":1.1}` — 効果音〔s="mirror", v=0.8, pi=1.1〕
25. `{"op":"self"}` — 対象を自分へ〔〕
26. `{"op":"buff","e":"luck","t":300,"a":4}` — 強化〔e="luck", t=300, a=4〕
27. `{"op":"guard","t":170}` — 防御〔t=170〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"buff","e":"luck","t":240,"a":2}` — 強化〔e="luck", t=240, a=2〕
30. `{"op":"fx","p":"enchant","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="enchant", n=20, at="ring", r=4, y=0.4〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"luck","t":160,"a":123}` — 強化〔e="luck", t=160, a=123〕
33. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
34. `{"op":"eff","e":"slow","t":32,"a":123}` — 敵への状態異常〔e="slow", t=32, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 最善終章・運命再編 — 超越神器（武器欄） (`arcana_legend`)

**現行パラメータ**：rank=3、damage登録値=1157.875、relics側CD=330tick、art側CD=330tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"buff","e":"luck","t":40,"a":5}` — 強化〔e="luck", t=40, a=5〕
06. `{"op":"reflect","t":25,"r":8}` — 反射〔t=25, r=8〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
09. `{"op":"buff","e":"luck","t":45,"a":3}` — 強化〔e="luck", t=45, a=3〕
10. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（7命令）**：

01. `{"op":"chance","p":0.5,"ops":[{"op":"victim"},{"op":"dmg","m":1.5}]}` — 抽選〔p=0.5, ops=[{"op":"victim"},{"op":"dmg","m":1.5}]〕
02. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"glow","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"glow","t":160,"a":1}]〕
03. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
04. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"enchant","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"enchant","n":10,"at":"t","s":0.35}]〕
05. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
06. `{"op":"chance","p":0.375,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.375, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]〕
07. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":62,"a":5}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":62,"a":5}]〕

**権能発動時の命令（24命令）**：

01. `{"op":"fx","p":"enchant","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="enchant", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"enchant","n":4,"at":"self","s":0.7}` — 粒子演出〔p="enchant", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":40,"at":"ring","r":3}` — 粒子演出〔p="end_rod", n=40, at="ring", r=3〕
04. `{"op":"fx","p":"enchant","n":40,"at":"self"}` — 粒子演出〔p="enchant", n=40, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":1.2}` — 効果音〔s="chime", v=1.0, pi=1.2〕
06. `{"op":"allies","r":48}` — 味方対象〔r=48〕
07. `{"op":"undying","t":180,"to":1}` — 死亡防護〔t=180, to=1〕
08. `{"op":"healpct","v":0.6,"to":1}` — 最大HP割合回復〔v=0.6, to=1〕
09. `{"op":"guard","t":100,"to":1}` — 防御〔t=100, to=1〕
10. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
11. `{"op":"strip"}` — 強化解除〔〕
12. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
13. `{"op":"mark","t":600,"x":3.0}` — 刻印〔t=600, x=3.0〕
14. `{"op":"reflect","t":400,"r":48}` — 反射〔t=400, r=48〕
15. `{"op":"fx","p":"end_rod","n":12,"at":"t","s":0.5}` — 粒子演出〔p="end_rod", n=12, at="t", s=0.5〕
16. `{"op":"chain","n":5,"r":16}` — chain〔n=5, r=16〕
17. `{"op":"dmg","m":1.7}` — 追加攻撃〔m=1.7〕
18. `{"op":"mark","t":100,"x":1.4}` — 刻印〔t=100, x=1.4〕
19. `{"op":"fx","p":"portal","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="portal", n=50, at="ring", r=8.0, y=0.6〕
20. `{"op":"fx","p":"end_rod","n":32,"at":"line","r":30}` — 粒子演出〔p="end_rod", n=32, at="line", r=30〕
21. `{"op":"sound","s":"totem","v":1.15,"pi":0.95}` — 効果音〔s="totem", v=1.15, pi=0.95〕
22. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.arcana_legend.stage0","ops":[{"op":"fx","p":"enchant","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"mirror","v":0.9,"pi":1.2},{"op":"fx","p":"enchant","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":10},{"op":"fx","p":"enchant","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"portal","n":36,"at":"line","r":24},{"op":"sound","s":"totem","v":1.05,"pi":1.14},{"op":"chain","n":5,"r":20.0},{"op":"mark","t":170,"x":2.6},{"op":"dmg","m":3.51},{"op":"self"},{"op":"buff","e":"luck","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.arcana_legend.stage1","ops":[{"op":"fx","p":"enchant","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"mirror","v":1.05,"pi":1.0},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"enchant","n":6,"at":"line","r":15},{"op":"fx","p":"portal","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"end_rod","n":32,"at":"line","r":30},{"op":"sound","s":"totem","v":1.15,"pi":0.95},{"op":"area","r":26.0,"n":22},{"op":"eff","e":"slow","t":110,"a":2},{"op":"dmg","m":4.06},{"op":"area","r":18.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.arcana_legend.stage2","ops":[{"op":"fx","p":"enchant","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"mirror","v":1.25,"pi":0.75},{"op":"fx","p":"end_rod","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"enchant","n":10,"at":"line","r":20},{"op":"fx","p":"enchant","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"portal","n":48,"at":"line","r":48},{"op":"fx","p":"end_rod","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"totem","v":1.5,"pi":0.75},{"op":"line","r":75.0,"w":5.0},{"op":"dmg","m":10.206},{"op":"strip"},{"op":"mark","t":170,"x":2.73},{"op":"self"},{"op":"buff","e":"luck","t":160,"a":3},{"op":"fx","p":"end_rod","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"enchant","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"line","r":74.0,"w":4.0},{"op":"dmg","m":3.0},{"op":"mark","t":195,"x":2.4},{"op":"self"},{"op":"buff","e":"luck","t":180,"a":5},{"op":"line","r":50.0,"w":4.0},{"op":"dmg","m":1.1},{"op":"eff","e":"slow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"luck","t":240,"a":4},{"op":"area","r":20,"n":8},{"op":"mark","t":140,"x":1.75},{"op":"fx","p":"enchant","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"mirror","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"slow","t":65,"a":10},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.arcana_legend.stage0","ops":[{"op":"fx","p":"enchant","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"mirror","v":0.9,"pi":1.2},{"op":"fx","p":"enchant","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":10},{"op":"fx","p":"enchant","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"portal","n":36,"at":"line","r":24},{"op":"sound","s":"totem","v":1.05,"pi":1.14},{"op":"chain","n":5,"r":20.0},{"op":"mark","t":170,"x":2.6},{"op":"dmg","m":3.51},{"op":"self"},{"op":"buff","e":"luck","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.arcana_legend.stage1","ops":[{"op":"fx","p":"enchant","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"mirror","v":1.05,"pi":1.0},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"enchant","n":6,"at":"line","r":15},{"op":"fx","p":"portal","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"end_rod","n":32,"at":"line","r":30},{"op":"sound","s":"totem","v":1.15,"pi":0.95},{"op":"area","r":26.0,"n":22},{"op":"eff","e":"slow","t":110,"a":2},{"op":"dmg","m":4.06},{"op":"area","r":18.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.arcana_legend.stage2","ops":[{"op":"fx","p":"enchant","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"mirror","v":1.25,"pi":0.75},{"op":"fx","p":"end_rod","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"enchant","n":10,"at":"line","r":20},{"op":"fx","p":"enchant","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"portal","n":48,"at":"line","r":48},{"op":"fx","p":"end_rod","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"totem","v":1.5,"pi":0.75},{"op":"line","r":75.0,"w":5.0},{"op":"dmg","m":10.206},{"op":"strip"},{"op":"mark","t":170,"x":2.73},{"op":"self"},{"op":"buff","e":"luck","t":160,"a":3},{"op":"fx","p":"end_rod","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"enchant","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"line","r":74.0,"w":4.0},{"op":"dmg","m":3.0},{"op":"mark","t":195,"x":2.4},{"op":"self"},{"op":"buff","e":"luck","t":180,"a":5},{"op":"line","r":50.0,"w":4.0},{"op":"dmg","m":1.1},{"op":"eff","e":"slow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"luck","t":240,"a":4},{"op":"area","r":20,"n":8},{"op":"mark","t":140,"x":1.75},{"op":"fx","p":"enchant","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"mirror","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"slow","t":65,"a":10},{"op":"mark","t":135,"x":1.8}]}]〕
23. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
24. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 25. 始祖神獣 エオマイア

**モブ側の動きの方向性**：四足獣の重心と翼・牙・角・尾の器官を切り替える。。

### 始祖神獣の角牙薙刀 — 討伐武器（メイン／武器欄） (`eomaia_weapon`)

**現行パラメータ**：rank=1、damage登録値=307.11111、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12。

**装備中の常時命令（5命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"speed","t":40,"a":0}` — 強化〔e="speed", t=40, a=0〕
03. `{"op":"buff","e":"night","t":300,"a":0}` — 強化〔e="night", t=300, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（8命令）**：

01. `{"op":"around","r":3,"n":16,"exclude":1}` — around〔r=3, n=16, exclude=1〕
02. `{"op":"dmg","m":0.25}` — 追加攻撃〔m=0.25〕
03. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"weakness","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"weakness","t":90,"a":0}]〕
04. `{"op":"chance","p":0.56,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":17,"at":"t","s":0.24},{"op":"mark","t":200,"x":2.21},{"op":"eff","e":"weakness","t":55,"a":0}]}` — 抽選〔p=0.56, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":17,"at":"t","s":0.24},{"op":"mark","t":200,"x":2.21},{"op":"eff","e":"weakness","t":55,"a":0}]〕
05. `{"op":"chance","p":0.258,"ops":[{"op":"victim"},{"op":"dmg","m":0.34}]}` — 抽選〔p=0.258, ops=[{"op":"victim"},{"op":"dmg","m":0.34}]〕
06. `{"op":"chance","p":0.085,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":8,"at":"t","s":0.25},{"op":"knock","f":0.55}]}` — 抽選〔p=0.085, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":8,"at":"t","s":0.25},{"op":"knock","f":0.55}]〕
07. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"fx","p":"compost","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"fx","p":"compost","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]〕
08. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]〕

**権能発動時の命令（29命令）**：

01. `{"op":"fx","p":"crit","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="crit", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"crit","n":4,"at":"self","s":0.7}` — 粒子演出〔p="crit", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"crit","n":40,"at":"self"}` — 粒子演出〔p="crit", n=40, at="self"〕
04. `{"op":"fx","p":"angry","n":6,"at":"self"}` — 粒子演出〔p="angry", n=6, at="self"〕
05. `{"op":"sound","s":"roar","v":0.5,"pi":1.0}` — 効果音〔s="roar", v=0.5, pi=1.0〕
06. `{"op":"summon","k":"wolf","n":4}` — 召喚〔k="wolf", n=4〕
07. `{"op":"cone","r":14,"a":140}` — 扇形対象の取得〔r=14, a=140〕
08. `{"op":"dmg","m":1.68}` — 追加攻撃〔m=1.68〕
09. `{"op":"knock","f":2.0}` — knock〔f=2.0〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"strength","t":300,"a":4}` — 強化〔e="strength", t=300, a=4〕
12. `{"op":"buff","e":"speed","t":300,"a":2}` — 強化〔e="speed", t=300, a=2〕
13. `{"op":"allies","r":24}` — 味方対象〔r=24〕
14. `{"op":"buff","e":"strength","t":300,"a":3,"to":1}` — 強化〔e="strength", t=300, a=3, to=1〕
15. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
16. `{"op":"fx","p":"happy","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="happy", n=46, at="ring", r=5.5, y=0.25〕
17. `{"op":"fx","p":"crit","n":36,"at":"line","r":24}` — 粒子演出〔p="crit", n=36, at="line", r=24〕
18. `{"op":"cone","r":22.0,"a":130.0}` — 扇形対象の取得〔r=22.0, a=130.0〕
19. `{"op":"dmg","m":3.1}` — 追加攻撃〔m=3.1〕
20. `{"op":"knock","f":2.6}` — knock〔f=2.6〕
21. `{"op":"fx","p":"crit","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="crit", n=16, at="ring", r=5.0〕
22. `{"op":"sound","s":"sonic","v":0.75,"pi":1.15}` — 効果音〔s="sonic", v=0.75, pi=1.15〕
23. `{"op":"cone","r":11,"a":85}` — 扇形対象の取得〔r=11, a=85〕
24. `{"op":"dmg","m":1.0}` — 追加攻撃〔m=1.0〕
25. `{"op":"eff","e":"weakness","t":65,"a":0}` — 敵への状態異常〔e="weakness", t=65, a=0〕
26. `{"op":"fx","p":"compost","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="compost", n=24, at="ring", r=4.5, y=0.6〕
27. `{"op":"sound","s":"roar","v":0.8,"pi":0.8}` — 効果音〔s="roar", v=0.8, pi=0.8〕
28. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
29. `{"op":"eff","e":"weakness","t":100,"a":124}` — 敵への状態異常〔e="weakness", t=100, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 原初獣群の角笛 — 神威触媒（Curios relic_focus） (`eomaia_focus`)

**現行パラメータ**：rank=2、damage登録値=75.8241、relics側CD=160tick、art側CD=160tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"allies","r":12}` — 味方対象〔r=12〕
02. `{"op":"buff","e":"speed","t":40,"a":0,"to":1}` — 強化〔e="speed", t=40, a=0, to=1〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"strength","t":45,"a":0}` — 強化〔e="strength", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"strength","t":42,"a":2}` — 強化〔e="strength", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（40命令）**：

01. `{"op":"fx","p":"crit","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="crit", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"crit","n":6,"at":"self","s":0.7}` — 粒子演出〔p="crit", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"crit","n":40,"at":"self"}` — 粒子演出〔p="crit", n=40, at="self"〕
04. `{"op":"fx","p":"angry","n":6,"at":"self"}` — 粒子演出〔p="angry", n=6, at="self"〕
05. `{"op":"sound","s":"roar","v":0.5,"pi":1.0}` — 効果音〔s="roar", v=0.5, pi=1.0〕
06. `{"op":"summon","k":"wolf","n":5}` — 召喚〔k="wolf", n=5〕
07. `{"op":"allies","r":24}` — 味方対象〔r=24〕
08. `{"op":"buff","e":"strength","t":600,"a":4,"to":1}` — 強化〔e="strength", t=600, a=4, to=1〕
09. `{"op":"buff","e":"speed","t":600,"a":2,"to":1}` — 強化〔e="speed", t=600, a=2, to=1〕
10. `{"op":"buff","e":"regen","t":600,"a":2,"to":1}` — 強化〔e="regen", t=600, a=2, to=1〕
11. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"strength","t":150,"a":1}` — 強化〔e="strength", t=150, a=1〕
14. `{"op":"fx","p":"crit","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="crit", n=50, at="ring", r=8.0, y=0.6〕
15. `{"op":"fx","p":"soul","n":32,"at":"line","r":30}` — 粒子演出〔p="soul", n=32, at="line", r=30〕
16. `{"op":"sound","s":"roar","v":1.15,"pi":0.95}` — 効果音〔s="roar", v=1.15, pi=0.95〕
17. `{"op":"summon","k":"golem","n":4}` — 召喚〔k="golem", n=4〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"buff","e":"strength","t":125,"a":3}` — 強化〔e="strength", t=125, a=3〕
20. `{"op":"self"}` — 対象を自分へ〔〕
21. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
22. `{"op":"buff","e":"regen","t":150,"a":3}` — 強化〔e="regen", t=150, a=3〕
23. `{"op":"fx","p":"compost","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="compost", n=24, at="ring", r=12, y=0.5〕
24. `{"op":"sound","s":"roar","v":0.85,"pi":1.18}` — 効果音〔s="roar", v=0.85, pi=1.18〕
25. `{"op":"cone","r":18.0,"a":95.0}` — 扇形対象の取得〔r=18.0, a=95.0〕
26. `{"op":"dmg","m":0.95}` — 追加攻撃〔m=0.95〕
27. `{"op":"eff","e":"weakness","t":100,"a":1}` — 敵への状態異常〔e="weakness", t=100, a=1〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"buff","e":"strength","t":200,"a":3}` — 強化〔e="strength", t=200, a=3〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"summon","k":"wolf","n":2}` — 召喚〔k="wolf", n=2〕
32. `{"op":"fx","p":"compost","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="compost", n=24, at="ring", r=5.5, y=0.7〕
33. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
34. `{"op":"eff","e":"weakness","t":135,"a":123}` — 敵への状態異常〔e="weakness", t=135, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"buff","e":"strength","t":80,"a":19}` — 強化〔e="strength", t=80, a=19〕
37. `{"op":"fx","p":"crit","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="crit", n=16, at="ring", r=3.7, y=0.55〕
38. `{"op":"cone","r":12,"a":100}` — 扇形対象の取得〔r=12, a=100〕
39. `{"op":"eff","e":"weakness","t":65,"a":10}` — 敵への状態異常〔e="weakness", t=65, a=10〕
40. `{"op":"knock","f":2.1}` — knock〔f=2.1〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 万獣記憶の爪飾り — 神格装飾品（Curios relic_charm） (`eomaia_charm`)

**現行パラメータ**：rank=1、damage登録値=75.8241、relics側CD=190tick、art側CD=190tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（14命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"jump","t":40,"a":1}` — 強化〔e="jump", t=40, a=1〕
03. `{"op":"buff","e":"speed","t":40,"a":0}` — 強化〔e="speed", t=40, a=0〕
04. `{"op":"buff","e":"night","t":300,"a":0}` — 強化〔e="night", t=300, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"strength","t":45,"a":0}` — 強化〔e="strength", t=45, a=0〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
09. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
10. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"strength","t":42,"a":2}` — 強化〔e="strength", t=42, a=2〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"speed","t":48,"a":5}` — 強化〔e="speed", t=48, a=5〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（36命令）**：

01. `{"op":"fx","p":"crit","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="crit", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"crit","n":4,"at":"self","s":0.7}` — 粒子演出〔p="crit", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"crit","n":40,"at":"self"}` — 粒子演出〔p="crit", n=40, at="self"〕
04. `{"op":"fx","p":"angry","n":6,"at":"self"}` — 粒子演出〔p="angry", n=6, at="self"〕
05. `{"op":"sound","s":"roar","v":0.5,"pi":1.0}` — 効果音〔s="roar", v=0.5, pi=1.0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"strength","t":400,"a":6}` — 強化〔e="strength", t=400, a=6〕
08. `{"op":"buff","e":"speed","t":400,"a":3}` — 強化〔e="speed", t=400, a=3〕
09. `{"op":"buff","e":"jump","t":400,"a":2}` — 強化〔e="jump", t=400, a=2〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"strength","t":210,"a":1}` — 強化〔e="strength", t=210, a=1〕
13. `{"op":"fx","p":"happy","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="happy", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"crit","n":36,"at":"line","r":24}` — 粒子演出〔p="crit", n=36, at="line", r=24〕
15. `{"op":"sound","s":"roar","v":1.05,"pi":1.14}` — 効果音〔s="roar", v=1.05, pi=1.14〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"guard","t":95}` — 防御〔t=95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
20. `{"op":"cleanse"}` — 状態異常解除〔〕
21. `{"op":"buff","e":"regen","t":180,"a":3}` — 強化〔e="regen", t=180, a=3〕
22. `{"op":"guard","t":95}` — 防御〔t=95〕
23. `{"op":"fx","p":"compost","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="compost", n=30, at="ring", r=4.0, y=0.7〕
24. `{"op":"sound","s":"roar","v":0.8,"pi":1.1}` — 効果音〔s="roar", v=0.8, pi=1.1〕
25. `{"op":"self"}` — 対象を自分へ〔〕
26. `{"op":"buff","e":"strength","t":260,"a":4}` — 強化〔e="strength", t=260, a=4〕
27. `{"op":"guard","t":125}` — 防御〔t=125〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"buff","e":"regen","t":240,"a":2}` — 強化〔e="regen", t=240, a=2〕
30. `{"op":"fx","p":"compost","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="compost", n=20, at="ring", r=4, y=0.4〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"strength","t":110,"a":31}` — 強化〔e="strength", t=110, a=31〕
33. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
34. `{"op":"eff","e":"weakness","t":100,"a":123}` — 敵への状態異常〔e="weakness", t=100, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 原初獣王・全獣の血脈 — 超越神器（武器欄） (`eomaia_legend`)

**現行パラメータ**：rank=3、damage登録値=461.2381、relics側CD=345tick、art側CD=345tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"allies","r":16}` — 味方対象〔r=16〕
06. `{"op":"buff","e":"strength","t":40,"a":2,"to":1}` — 強化〔e="strength", t=40, a=2, to=1〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
09. `{"op":"buff","e":"regen","t":45,"a":3}` — 強化〔e="regen", t=45, a=3〕
10. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（9命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"dmg","m":0.3}` — 追加攻撃〔m=0.3〕
03. `{"op":"dmg","m":0.3}` — 追加攻撃〔m=0.3〕
04. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"weakness","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"weakness","t":160,"a":1}]〕
05. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"happy","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"happy","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
06. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"happy","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"happy","n":10,"at":"t","s":0.35}]〕
07. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
08. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"fx","p":"compost","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"fx","p":"compost","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]〕
09. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]〕

**権能発動時の命令（28命令）**：

01. `{"op":"fx","p":"crit","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="crit", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"crit","n":4,"at":"self","s":0.7}` — 粒子演出〔p="crit", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"crit","n":40,"at":"self"}` — 粒子演出〔p="crit", n=40, at="self"〕
04. `{"op":"fx","p":"angry","n":6,"at":"self"}` — 粒子演出〔p="angry", n=6, at="self"〕
05. `{"op":"sound","s":"roar","v":0.5,"pi":1.0}` — 効果音〔s="roar", v=0.5, pi=1.0〕
06. `{"op":"summon","k":"wolf","n":5}` — 召喚〔k="wolf", n=5〕
07. `{"op":"area","r":40,"n":36}` — 円形対象の取得〔r=40, n=36〕
08. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
09. `{"op":"stun","t":105}` — 行動停止〔t=105〕
10. `{"op":"knock","f":3.0}` — knock〔f=3.0〕
11. `{"op":"allies","r":40}` — 味方対象〔r=40〕
12. `{"op":"buff","e":"strength","t":1200,"a":8,"to":1}` — 強化〔e="strength", t=1200, a=8, to=1〕
13. `{"op":"buff","e":"speed","t":1200,"a":2,"to":1}` — 強化〔e="speed", t=1200, a=2, to=1〕
14. `{"op":"buff","e":"regen","t":1200,"a":2,"to":1}` — 強化〔e="regen", t=1200, a=2, to=1〕
15. `{"op":"self"}` — 対象を自分へ〔〕
16. `{"op":"undying","t":180}` — 死亡防護〔t=180〕
17. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
18. `{"op":"allies","r":26}` — 味方対象〔r=26〕
19. `{"op":"healpct","v":0.35}` — 最大HP割合回復〔v=0.35〕
20. `{"op":"cleanse"}` — 状態異常解除〔〕
21. `{"op":"self"}` — 対象を自分へ〔〕
22. `{"op":"buff","e":"regen","t":200,"a":2}` — 強化〔e="regen", t=200, a=2〕
23. `{"op":"fx","p":"crit","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="crit", n=50, at="ring", r=8.0, y=0.6〕
24. `{"op":"fx","p":"soul","n":32,"at":"line","r":30}` — 粒子演出〔p="soul", n=32, at="line", r=30〕
25. `{"op":"sound","s":"roar","v":1.15,"pi":0.95}` — 効果音〔s="roar", v=1.15, pi=0.95〕
26. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.eomaia_legend.stage0","ops":[{"op":"fx","p":"compost","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"roar","v":0.9,"pi":1.2},{"op":"fx","p":"crit","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"compost","n":6,"at":"line","r":10},{"op":"fx","p":"happy","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"crit","n":36,"at":"line","r":24},{"op":"sound","s":"roar","v":1.05,"pi":1.14},{"op":"cone","r":22.0,"a":130.0},{"op":"dmg","m":4.185},{"op":"knock","f":2.6},{"op":"self"},{"op":"buff","e":"strength","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.eomaia_legend.stage1","ops":[{"op":"fx","p":"compost","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"roar","v":1.05,"pi":1.0},{"op":"fx","p":"compost","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"crit","n":6,"at":"line","r":15},{"op":"fx","p":"crit","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"soul","n":32,"at":"line","r":30},{"op":"sound","s":"roar","v":1.15,"pi":0.95},{"op":"summon","k":"golem","n":4},{"op":"self"},{"op":"buff","e":"strength","t":125,"a":3},{"op":"area","r":20.0,"n":10},{"op":"eff","e":"weakness","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.eomaia_legend.stage2","ops":[{"op":"fx","p":"compost","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"roar","v":1.25,"pi":0.75},{"op":"fx","p":"compost","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"crit","n":10,"at":"line","r":20},{"op":"fx","p":"happy","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"crit","n":48,"at":"line","r":48},{"op":"fx","p":"soul","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"roar","v":1.5,"pi":0.75},{"op":"area","r":34.0,"n":28},{"op":"dmg","m":10.368},{"op":"summon","k":"golem","n":5},{"op":"self"},{"op":"guard","t":150},{"op":"buff","e":"regen","t":170,"a":3},{"op":"fx","p":"soul","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"happy","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":29.0,"n":24},{"op":"dmg","m":2.9},{"op":"summon","k":"golem","n":3},{"op":"self"},{"op":"buff","e":"regen","t":180,"a":3},{"op":"cone","r":15.0,"a":110.0},{"op":"dmg","m":1.2},{"op":"eff","e":"weakness","t":160,"a":2},{"op":"self"},{"op":"buff","e":"strength","t":240,"a":4},{"op":"self"},{"op":"summon","k":"wolf","n":3},{"op":"fx","p":"compost","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"roar","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"weakness","t":65,"a":10},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.eomaia_legend.stage0","ops":[{"op":"fx","p":"compost","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"roar","v":0.9,"pi":1.2},{"op":"fx","p":"crit","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"compost","n":6,"at":"line","r":10},{"op":"fx","p":"happy","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"crit","n":36,"at":"line","r":24},{"op":"sound","s":"roar","v":1.05,"pi":1.14},{"op":"cone","r":22.0,"a":130.0},{"op":"dmg","m":4.185},{"op":"knock","f":2.6},{"op":"self"},{"op":"buff","e":"strength","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.eomaia_legend.stage1","ops":[{"op":"fx","p":"compost","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"roar","v":1.05,"pi":1.0},{"op":"fx","p":"compost","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"crit","n":6,"at":"line","r":15},{"op":"fx","p":"crit","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"soul","n":32,"at":"line","r":30},{"op":"sound","s":"roar","v":1.15,"pi":0.95},{"op":"summon","k":"golem","n":4},{"op":"self"},{"op":"buff","e":"strength","t":125,"a":3},{"op":"area","r":20.0,"n":10},{"op":"eff","e":"weakness","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.eomaia_legend.stage2","ops":[{"op":"fx","p":"compost","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"roar","v":1.25,"pi":0.75},{"op":"fx","p":"compost","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"crit","n":10,"at":"line","r":20},{"op":"fx","p":"happy","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"crit","n":48,"at":"line","r":48},{"op":"fx","p":"soul","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"roar","v":1.5,"pi":0.75},{"op":"area","r":34.0,"n":28},{"op":"dmg","m":10.368},{"op":"summon","k":"golem","n":5},{"op":"self"},{"op":"guard","t":150},{"op":"buff","e":"regen","t":170,"a":3},{"op":"fx","p":"soul","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"happy","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":29.0,"n":24},{"op":"dmg","m":2.9},{"op":"summon","k":"golem","n":3},{"op":"self"},{"op":"buff","e":"regen","t":180,"a":3},{"op":"cone","r":15.0,"a":110.0},{"op":"dmg","m":1.2},{"op":"eff","e":"weakness","t":160,"a":2},{"op":"self"},{"op":"buff","e":"strength","t":240,"a":4},{"op":"self"},{"op":"summon","k":"wolf","n":3},{"op":"fx","p":"compost","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"roar","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"weakness","t":65,"a":10},{"op":"mark","t":135,"x":1.8}]}]〕
27. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
28. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 26. 空創龍王 デミウルゴス

**モブ側の動きの方向性**：龍の首・翼膜に浮かぶ銀河、四肢を用いる創世動作。。

### 空想現実の黒龍剣 — 討伐武器（メイン／武器欄） (`demiurgos_weapon`)

**現行パラメータ**：rank=1、damage登録値=289.33333、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:sweeping_edge:25。

**装備中の常時命令（4命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"absorb","t":40,"a":1}` — 強化〔e="absorb", t=40, a=1〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（8命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"dmg","m":1.8,"magic":1}` — 追加攻撃〔m=1.8, magic=1〕
03. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"glow","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"glow","t":90,"a":0}]〕
04. `{"op":"chance","p":0.46,"ops":[{"op":"victim"},{"op":"fx","p":"dragon","n":9,"at":"t","s":0.24},{"op":"mark","t":120,"x":1.65},{"op":"eff","e":"glow","t":67,"a":0}]}` — 抽選〔p=0.46, ops=[{"op":"victim"},{"op":"fx","p":"dragon","n":9,"at":"t","s":0.24},{"op":"mark","t":120,"x":1.65},{"op":"eff","e":"glow","t":67,"a":0}]〕
05. `{"op":"chance","p":0.15,"ops":[{"op":"victim"},{"op":"dmg","m":0.2}]}` — 抽選〔p=0.15, ops=[{"op":"victim"},{"op":"dmg","m":0.2}]〕
06. `{"op":"chance","p":0.104,"ops":[{"op":"victim"},{"op":"fx","p":"dragon","n":8,"at":"t","s":0.25},{"op":"dmg","m":0.28}]}` — 抽選〔p=0.104, ops=[{"op":"victim"},{"op":"fx","p":"dragon","n":8,"at":"t","s":0.25},{"op":"dmg","m":0.28}]〕
07. `{"op":"chance","p":0.18,"ops":[{"op":"victim"},{"op":"fx","p":"dragon","n":14,"at":"t","s":0.28},{"op":"eff","e":"fatigue","t":110,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.18, ops=[{"op":"victim"},{"op":"fx","p":"dragon","n":14,"at":"t","s":0.28},{"op":"eff","e":"fatigue","t":110,"a":124},{"op":"mark","t":100,"x":2.15}]〕
08. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"portal","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":32,"a":3}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"portal","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":32,"a":3}]〕

**権能発動時の命令（25命令）**：

01. `{"op":"fx","p":"portal","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="portal", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"portal","n":4,"at":"self","s":0.7}` — 粒子演出〔p="portal", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"firework","n":30,"at":"self"}` — 粒子演出〔p="firework", n=30, at="self"〕
04. `{"op":"fx","p":"dragon","n":30,"at":"self"}` — 粒子演出〔p="dragon", n=30, at="self"〕
05. `{"op":"sound","s":"spell","v":1.0,"pi":1.4}` — 効果音〔s="spell", v=1.0, pi=1.4〕
06. `{"op":"summon","k":"golem","n":2}` — 召喚〔k="golem", n=2〕
07. `{"op":"line","r":32,"w":3}` — 線分対象の取得〔r=32, w=3〕
08. `{"op":"dmg","m":1.92}` — 追加攻撃〔m=1.92〕
09. `{"op":"dmg","m":2.16,"magic":1}` — 追加攻撃〔m=2.16, magic=1〕
10. `{"op":"blink","d":10}` — blink〔d=10〕
11. `{"op":"fx","p":"dragon","n":12,"at":"t","s":0.5}` — 粒子演出〔p="dragon", n=12, at="t", s=0.5〕
12. `{"op":"fx","p":"dragon","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="dragon", n=46, at="ring", r=5.5, y=0.25〕
13. `{"op":"fx","p":"portal","n":36,"at":"line","r":24}` — 粒子演出〔p="portal", n=36, at="line", r=24〕
14. `{"op":"line","r":68.0,"w":5.0}` — 線分対象の取得〔r=68.0, w=5.0〕
15. `{"op":"dmg","m":3.1}` — 追加攻撃〔m=3.1〕
16. `{"op":"mark","t":125,"x":1.6}` — 刻印〔t=125, x=1.6〕
17. `{"op":"fx","p":"dragon","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="dragon", n=16, at="ring", r=5.0〕
18. `{"op":"sound","s":"sonic","v":0.75,"pi":1.15}` — 効果音〔s="sonic", v=0.75, pi=1.15〕
19. `{"op":"line","r":18,"w":2}` — 線分対象の取得〔r=18, w=2〕
20. `{"op":"dmg","m":1.05}` — 追加攻撃〔m=1.05〕
21. `{"op":"eff","e":"glow","t":65,"a":0}` — 敵への状態異常〔e="glow", t=65, a=0〕
22. `{"op":"fx","p":"dragon","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="dragon", n=24, at="ring", r=4.5, y=0.6〕
23. `{"op":"sound","s":"roar","v":0.8,"pi":0.8}` — 効果音〔s="roar", v=0.8, pi=0.8〕
24. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
25. `{"op":"eff","e":"fatigue","t":110,"a":124}` — 敵への状態異常〔e="fatigue", t=110, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 創界の虹宝珠 — 神威触媒（Curios relic_focus） (`demiurgos_focus`)

**現行パラメータ**：rank=2、damage登録値=77.8734、relics側CD=155tick、art側CD=155tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"absorb","t":40,"a":2}` — 強化〔e="absorb", t=40, a=2〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"resist","t":45,"a":0}` — 強化〔e="resist", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"resist","t":42,"a":2}` — 強化〔e="resist", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（42命令）**：

01. `{"op":"fx","p":"portal","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="portal", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"portal","n":6,"at":"self","s":0.7}` — 粒子演出〔p="portal", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"firework","n":30,"at":"self"}` — 粒子演出〔p="firework", n=30, at="self"〕
04. `{"op":"fx","p":"dragon","n":30,"at":"self"}` — 粒子演出〔p="dragon", n=30, at="self"〕
05. `{"op":"sound","s":"spell","v":1.0,"pi":1.4}` — 効果音〔s="spell", v=1.0, pi=1.4〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"guard","t":100}` — 防御〔t=100〕
08. `{"op":"buff","e":"absorb","t":800,"a":8}` — 強化〔e="absorb", t=800, a=8〕
09. `{"op":"allies","r":24}` — 味方対象〔r=24〕
10. `{"op":"guard","t":60,"to":1}` — 防御〔t=60, to=1〕
11. `{"op":"summon","k":"golem","n":3}` — 召喚〔k="golem", n=3〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"resist","t":150,"a":1}` — 強化〔e="resist", t=150, a=1〕
15. `{"op":"fx","p":"portal","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="portal", n=50, at="ring", r=8.0, y=0.6〕
16. `{"op":"fx","p":"firework","n":32,"at":"line","r":30}` — 粒子演出〔p="firework", n=32, at="line", r=30〕
17. `{"op":"sound","s":"roar","v":1.15,"pi":0.95}` — 効果音〔s="roar", v=1.15, pi=0.95〕
18. `{"op":"area","r":28.0,"n":20}` — 円形対象の取得〔r=28.0, n=20〕
19. `{"op":"dmg","m":2.9}` — 追加攻撃〔m=2.9〕
20. `{"op":"summon","k":"golem","n":3}` — 召喚〔k="golem", n=3〕
21. `{"op":"eff","e":"glow","t":110,"a":0}` — 敵への状態異常〔e="glow", t=110, a=0〕
22. `{"op":"self"}` — 対象を自分へ〔〕
23. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
24. `{"op":"buff","e":"resist","t":150,"a":3}` — 強化〔e="resist", t=150, a=3〕
25. `{"op":"fx","p":"dragon","n":24,"at":"ring","r":10,"y":0.5}` — 粒子演出〔p="dragon", n=24, at="ring", r=10, y=0.5〕
26. `{"op":"sound","s":"roar","v":0.85,"pi":0.9}` — 効果音〔s="roar", v=0.85, pi=0.9〕
27. `{"op":"area","r":10.0,"n":12}` — 円形対象の取得〔r=10.0, n=12〕
28. `{"op":"dmg","m":0.8}` — 追加攻撃〔m=0.8〕
29. `{"op":"eff","e":"glow","t":120,"a":1}` — 敵への状態異常〔e="glow", t=120, a=1〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"resist","t":220,"a":3}` — 強化〔e="resist", t=220, a=3〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"summon","k":"golem","n":1}` — 召喚〔k="golem", n=1〕
34. `{"op":"fx","p":"dragon","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="dragon", n=24, at="ring", r=5.5, y=0.7〕
35. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
36. `{"op":"eff","e":"fatigue","t":148,"a":123}` — 敵への状態異常〔e="fatigue", t=148, a=123〕
37. `{"op":"self"}` — 対象を自分へ〔〕
38. `{"op":"buff","e":"resist","t":140,"a":2}` — 強化〔e="resist", t=140, a=2〕
39. `{"op":"fx","p":"portal","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="portal", n=16, at="ring", r=3.7, y=0.55〕
40. `{"op":"area","r":16,"n":9}` — 円形対象の取得〔r=16, n=9〕
41. `{"op":"eff","e":"glow","t":95,"a":0}` — 敵への状態異常〔e="glow", t=95, a=0〕
42. `{"op":"mark","t":135,"x":1.8}` — 刻印〔t=135, x=1.8〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 理想定着の龍鱗 — 神格装飾品（Curios relic_charm） (`demiurgos_charm`)

**現行パラメータ**：rank=1、damage登録値=77.8734、relics側CD=185tick、art側CD=185tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（12命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"reflect","t":25,"r":6}` — 反射〔t=25, r=6〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"resist","t":45,"a":0}` — 強化〔e="resist", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
08. `{"op":"buff","e":"resist","t":45,"a":1}` — 強化〔e="resist", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"resist","t":42,"a":2}` — 強化〔e="resist", t=42, a=2〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"absorb","t":48,"a":4}` — 強化〔e="absorb", t=48, a=4〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（36命令）**：

01. `{"op":"fx","p":"portal","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="portal", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"portal","n":4,"at":"self","s":0.7}` — 粒子演出〔p="portal", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"firework","n":30,"at":"self"}` — 粒子演出〔p="firework", n=30, at="self"〕
04. `{"op":"fx","p":"dragon","n":30,"at":"self"}` — 粒子演出〔p="dragon", n=30, at="self"〕
05. `{"op":"sound","s":"spell","v":1.0,"pi":1.4}` — 効果音〔s="spell", v=1.0, pi=1.4〕
06. `{"op":"reflect","t":200,"r":20}` — 反射〔t=200, r=20〕
07. `{"op":"erase","r":32}` — erase〔r=32〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"resist","t":400,"a":4}` — 強化〔e="resist", t=400, a=4〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"resist","t":210,"a":1}` — 強化〔e="resist", t=210, a=1〕
13. `{"op":"fx","p":"dragon","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="dragon", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"portal","n":36,"at":"line","r":24}` — 粒子演出〔p="portal", n=36, at="line", r=24〕
15. `{"op":"sound","s":"roar","v":1.05,"pi":1.14}` — 効果音〔s="roar", v=1.05, pi=1.14〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"guard","t":95}` — 防御〔t=95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
20. `{"op":"cleanse"}` — 状態異常解除〔〕
21. `{"op":"buff","e":"resist","t":180,"a":3}` — 強化〔e="resist", t=180, a=3〕
22. `{"op":"guard","t":95}` — 防御〔t=95〕
23. `{"op":"fx","p":"dragon","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="dragon", n=30, at="ring", r=4.0, y=0.7〕
24. `{"op":"sound","s":"roar","v":0.8,"pi":1.1}` — 効果音〔s="roar", v=0.8, pi=1.1〕
25. `{"op":"self"}` — 対象を自分へ〔〕
26. `{"op":"buff","e":"resist","t":280,"a":4}` — 強化〔e="resist", t=280, a=4〕
27. `{"op":"guard","t":140}` — 防御〔t=140〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"buff","e":"resist","t":240,"a":2}` — 強化〔e="resist", t=240, a=2〕
30. `{"op":"fx","p":"dragon","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="dragon", n=20, at="ring", r=4, y=0.4〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"resist","t":140,"a":2}` — 強化〔e="resist", t=140, a=2〕
33. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
34. `{"op":"eff","e":"fatigue","t":110,"a":123}` — 敵への状態異常〔e="fatigue", t=110, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 空創龍権・万物創現 — 超越神器（武器欄） (`demiurgos_legend`)

**現行パラメータ**：rank=3、damage登録値=378.88462、relics側CD=340tick、art側CD=340tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:sweeping_edge:25。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"reflect","t":25,"r":8}` — 反射〔t=25, r=8〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
08. `{"op":"buff","e":"resist","t":45,"a":3}` — 強化〔e="resist", t=45, a=3〕
09. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（8命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"dmg","m":5.0,"magic":1}` — 追加攻撃〔m=5.0, magic=1〕
03. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"glow","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"glow","t":160,"a":1}]〕
04. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"dragon","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"dragon","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
05. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"glow","t":135,"a":2},{"op":"fx","p":"dragon","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"glow","t":135,"a":2},{"op":"fx","p":"dragon","n":10,"at":"t","s":0.35}]〕
06. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
07. `{"op":"chance","p":0.3,"ops":[{"op":"victim"},{"op":"fx","p":"dragon","n":20,"at":"t","s":0.33},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.3, ops=[{"op":"victim"},{"op":"fx","p":"dragon","n":20,"at":"t","s":0.33},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":160,"x":2.5}]〕
08. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"portal","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":62,"a":5}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"portal","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":62,"a":5}]〕

**権能発動時の命令（24命令）**：

01. `{"op":"fx","p":"portal","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="portal", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"portal","n":4,"at":"self","s":0.7}` — 粒子演出〔p="portal", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"firework","n":30,"at":"self"}` — 粒子演出〔p="firework", n=30, at="self"〕
04. `{"op":"fx","p":"dragon","n":30,"at":"self"}` — 粒子演出〔p="dragon", n=30, at="self"〕
05. `{"op":"sound","s":"spell","v":1.0,"pi":1.4}` — 効果音〔s="spell", v=1.0, pi=1.4〕
06. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
07. `{"op":"dmg","m":5.6,"magic":1}` — 追加攻撃〔m=5.6, magic=1〕
08. `{"op":"dmg","m":3.36}` — 追加攻撃〔m=3.36〕
09. `{"op":"stun","t":105}` — 行動停止〔t=105〕
10. `{"op":"summon","k":"golem","n":5}` — 召喚〔k="golem", n=5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"undying","t":180}` — 死亡防護〔t=180〕
13. `{"op":"guard","t":100}` — 防御〔t=100〕
14. `{"op":"blink","d":20}` — blink〔d=20〕
15. `{"op":"fx","p":"dragon","n":12,"at":"t","s":0.5}` — 粒子演出〔p="dragon", n=12, at="t", s=0.5〕
16. `{"op":"area","r":26,"n":24}` — 円形対象の取得〔r=26, n=24〕
17. `{"op":"dmg","m":1.3}` — 追加攻撃〔m=1.3〕
18. `{"op":"eff","e":"nausea","t":95,"a":0}` — 敵への状態異常〔e="nausea", t=95, a=0〕
19. `{"op":"fx","p":"portal","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="portal", n=50, at="ring", r=8.0, y=0.6〕
20. `{"op":"fx","p":"firework","n":32,"at":"line","r":30}` — 粒子演出〔p="firework", n=32, at="line", r=30〕
21. `{"op":"sound","s":"roar","v":1.15,"pi":0.95}` — 効果音〔s="roar", v=1.15, pi=0.95〕
22. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.demiurgos_legend.stage0","ops":[{"op":"fx","p":"dragon","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"roar","v":0.9,"pi":1.2},{"op":"fx","p":"portal","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":10},{"op":"fx","p":"dragon","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"portal","n":36,"at":"line","r":24},{"op":"sound","s":"roar","v":1.05,"pi":1.14},{"op":"line","r":68.0,"w":5.0},{"op":"dmg","m":4.185},{"op":"mark","t":125,"x":2.08},{"op":"self"},{"op":"buff","e":"resist","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.demiurgos_legend.stage1","ops":[{"op":"fx","p":"dragon","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"roar","v":1.05,"pi":1.0},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"portal","n":6,"at":"line","r":15},{"op":"fx","p":"portal","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"firework","n":32,"at":"line","r":30},{"op":"sound","s":"roar","v":1.15,"pi":0.95},{"op":"area","r":28.0,"n":20},{"op":"dmg","m":4.205},{"op":"summon","k":"golem","n":3},{"op":"eff","e":"glow","t":110,"a":0},{"op":"area","r":12.0,"n":10},{"op":"eff","e":"glow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.demiurgos_legend.stage2","ops":[{"op":"fx","p":"dragon","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"roar","v":1.25,"pi":0.75},{"op":"fx","p":"end_rod","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"portal","n":10,"at":"line","r":20},{"op":"fx","p":"dragon","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"portal","n":48,"at":"line","r":48},{"op":"fx","p":"firework","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"roar","v":1.5,"pi":0.75},{"op":"area","r":38.0,"n":30},{"op":"dmg","m":11.34},{"op":"strip"},{"op":"summon","k":"golem","n":5},{"op":"self"},{"op":"guard","t":160},{"op":"fx","p":"firework","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"dragon","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":36.0,"n":32},{"op":"dmg","m":3.3},{"op":"summon","k":"golem","n":4},{"op":"self"},{"op":"guard","t":110},{"op":"area","r":18.0,"n":16},{"op":"dmg","m":0.8},{"op":"eff","e":"glow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"resist","t":240,"a":4},{"op":"self"},{"op":"summon","k":"golem","n":2},{"op":"fx","p":"dragon","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"roar","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"glow","t":95,"a":0},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.demiurgos_legend.stage0","ops":[{"op":"fx","p":"dragon","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"roar","v":0.9,"pi":1.2},{"op":"fx","p":"portal","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":10},{"op":"fx","p":"dragon","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"portal","n":36,"at":"line","r":24},{"op":"sound","s":"roar","v":1.05,"pi":1.14},{"op":"line","r":68.0,"w":5.0},{"op":"dmg","m":4.185},{"op":"mark","t":125,"x":2.08},{"op":"self"},{"op":"buff","e":"resist","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.demiurgos_legend.stage1","ops":[{"op":"fx","p":"dragon","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"roar","v":1.05,"pi":1.0},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"portal","n":6,"at":"line","r":15},{"op":"fx","p":"portal","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"firework","n":32,"at":"line","r":30},{"op":"sound","s":"roar","v":1.15,"pi":0.95},{"op":"area","r":28.0,"n":20},{"op":"dmg","m":4.205},{"op":"summon","k":"golem","n":3},{"op":"eff","e":"glow","t":110,"a":0},{"op":"area","r":12.0,"n":10},{"op":"eff","e":"glow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.demiurgos_legend.stage2","ops":[{"op":"fx","p":"dragon","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"roar","v":1.25,"pi":0.75},{"op":"fx","p":"end_rod","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"portal","n":10,"at":"line","r":20},{"op":"fx","p":"dragon","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"portal","n":48,"at":"line","r":48},{"op":"fx","p":"firework","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"roar","v":1.5,"pi":0.75},{"op":"area","r":38.0,"n":30},{"op":"dmg","m":11.34},{"op":"strip"},{"op":"summon","k":"golem","n":5},{"op":"self"},{"op":"guard","t":160},{"op":"fx","p":"firework","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"dragon","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":36.0,"n":32},{"op":"dmg","m":3.3},{"op":"summon","k":"golem","n":4},{"op":"self"},{"op":"guard","t":110},{"op":"area","r":18.0,"n":16},{"op":"dmg","m":0.8},{"op":"eff","e":"glow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"resist","t":240,"a":4},{"op":"self"},{"op":"summon","k":"golem","n":2},{"op":"fx","p":"dragon","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"roar","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"glow","t":95,"a":0},{"op":"mark","t":135,"x":1.8}]}]〕
23. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
24. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 27. 無窮覇帝 覇極

**モブ側の動きの方向性**：機械回路と生体器官の変形を別相として同期させる。。

### 無窮覇帝の捕食砲 — 討伐武器（メイン／武器欄） (`hakyoku_weapon`)

**現行パラメータ**：rank=1、damage登録値=462.0、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（4命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"adapt","t":40}` — adapt〔t=40〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（10命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"heal","v":6}` — heal〔v=6〕
05. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"fatigue","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"fatigue","t":90,"a":0}]〕
06. `{"op":"chance","p":0.485,"ops":[{"op":"victim"},{"op":"fx","p":"electric_spark","n":11,"at":"t","s":0.24},{"op":"mark","t":140,"x":1.79},{"op":"eff","e":"fatigue","t":79,"a":0}]}` — 抽選〔p=0.485, ops=[{"op":"victim"},{"op":"fx","p":"electric_spark","n":11,"at":"t","s":0.24},{"op":"mark","t":140,"x":1.79},{"op":"eff","e":"fatigue","t":79,"a":0}]〕
07. `{"op":"chance","p":0.177,"ops":[{"op":"victim"},{"op":"dmg","m":0.235}]}` — 抽選〔p=0.177, ops=[{"op":"victim"},{"op":"dmg","m":0.235}]〕
08. `{"op":"chance","p":0.123,"ops":[{"op":"victim"},{"op":"fx","p":"electric_spark","n":8,"at":"t","s":0.25},{"op":"strip"}]}` — 抽選〔p=0.123, ops=[{"op":"victim"},{"op":"fx","p":"electric_spark","n":8,"at":"t","s":0.25},{"op":"strip"}]〕
09. `{"op":"chance","p":0.2,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":14,"at":"t","s":0.28},{"op":"eff","e":"fatigue","t":110,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.2, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":14,"at":"t","s":0.28},{"op":"eff","e":"fatigue","t":110,"a":124},{"op":"mark","t":100,"x":2.15}]〕
10. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]〕

**権能発動時の命令（28命令）**：

01. `{"op":"fx","p":"sculk","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="sculk", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"sculk","n":4,"at":"self","s":0.7}` — 粒子演出〔p="sculk", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"lava","n":10,"at":"self"}` — 粒子演出〔p="lava", n=10, at="self"〕
04. `{"op":"fx","p":"sculk","n":30,"at":"self"}` — 粒子演出〔p="sculk", n=30, at="self"〕
05. `{"op":"sound","s":"roar","v":0.6,"pi":1.2}` — 効果音〔s="roar", v=0.6, pi=1.2〕
06. `{"op":"fx","p":"lava","n":30,"at":"line","r":40}` — 粒子演出〔p="lava", n=30, at="line", r=40〕
07. `{"op":"line","r":40,"w":3}` — 線分対象の取得〔r=40, w=3〕
08. `{"op":"dmg","m":2.16}` — 追加攻撃〔m=2.16〕
09. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
10. `{"op":"dmg","m":2.16,"magic":1}` — 追加攻撃〔m=2.16, magic=1〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"healpct","v":0.25}` — 最大HP割合回復〔v=0.25〕
13. `{"op":"adapt","t":600}` — adapt〔t=600〕
14. `{"op":"fx","p":"lava","n":12,"at":"t","s":0.5}` — 粒子演出〔p="lava", n=12, at="t", s=0.5〕
15. `{"op":"fx","p":"spark","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="spark", n=46, at="ring", r=5.5, y=0.25〕
16. `{"op":"fx","p":"crit","n":36,"at":"line","r":24}` — 粒子演出〔p="crit", n=36, at="line", r=24〕
17. `{"op":"cone","r":22.0,"a":125.0}` — 扇形対象の取得〔r=22.0, a=125.0〕
18. `{"op":"dmg","m":3.0}` — 追加攻撃〔m=3.0〕
19. `{"op":"mark","t":120,"x":1.7}` — 刻印〔t=120, x=1.7〕
20. `{"op":"fx","p":"electric_spark","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="electric_spark", n=16, at="ring", r=5.0〕
21. `{"op":"sound","s":"sonic","v":0.75,"pi":1.15}` — 効果音〔s="sonic", v=0.75, pi=1.15〕
22. `{"op":"line","r":18,"w":2}` — 線分対象の取得〔r=18, w=2〕
23. `{"op":"dmg","m":1.05}` — 追加攻撃〔m=1.05〕
24. `{"op":"eff","e":"fatigue","t":65,"a":0}` — 敵への状態異常〔e="fatigue", t=65, a=0〕
25. `{"op":"fx","p":"spark","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="spark", n=24, at="ring", r=4.5, y=0.6〕
26. `{"op":"sound","s":"anvil","v":0.8,"pi":0.8}` — 効果音〔s="anvil", v=0.8, pi=0.8〕
27. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
28. `{"op":"eff","e":"fatigue","t":110,"a":124}` — 敵への状態異常〔e="fatigue", t=110, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 無窮進化の記録核 — 神威触媒（Curios relic_focus） (`hakyoku_focus`)

**現行パラメータ**：rank=2、damage登録値=75.8241、relics側CD=150tick、art側CD=150tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"adapt","t":40}` — adapt〔t=40〕
03. `{"op":"buff","e":"regen","t":40,"a":0}` — 強化〔e="regen", t=40, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"regen","t":45,"a":0}` — 強化〔e="regen", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"strength","t":45,"a":2}` — 強化〔e="strength", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"resist","t":42,"a":2}` — 強化〔e="resist", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（42命令）**：

01. `{"op":"fx","p":"sculk","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="sculk", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"sculk","n":6,"at":"self","s":0.7}` — 粒子演出〔p="sculk", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"lava","n":10,"at":"self"}` — 粒子演出〔p="lava", n=10, at="self"〕
04. `{"op":"fx","p":"sculk","n":30,"at":"self"}` — 粒子演出〔p="sculk", n=30, at="self"〕
05. `{"op":"sound","s":"roar","v":0.6,"pi":1.2}` — 効果音〔s="roar", v=0.6, pi=1.2〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"adapt","t":1200}` — adapt〔t=1200〕
08. `{"op":"buff","e":"strength","t":600,"a":6}` — 強化〔e="strength", t=600, a=6〕
09. `{"op":"buff","e":"resist","t":600,"a":3}` — 強化〔e="resist", t=600, a=3〕
10. `{"op":"buff","e":"health","t":1200,"a":4}` — 強化〔e="health", t=1200, a=4〕
11. `{"op":"healpct","v":0.4}` — 最大HP割合回復〔v=0.4〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"regen","t":150,"a":1}` — 強化〔e="regen", t=150, a=1〕
15. `{"op":"fx","p":"crit","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="crit", n=50, at="ring", r=8.0, y=0.6〕
16. `{"op":"fx","p":"smoke","n":32,"at":"line","r":30}` — 粒子演出〔p="smoke", n=32, at="line", r=30〕
17. `{"op":"sound","s":"anvil","v":1.15,"pi":0.95}` — 効果音〔s="anvil", v=1.15, pi=0.95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"adapt"}` — adapt〔〕
20. `{"op":"guard","t":130}` — 防御〔t=130〕
21. `{"op":"buff","e":"strength","t":180,"a":3}` — 強化〔e="strength", t=180, a=3〕
22. `{"op":"self"}` — 対象を自分へ〔〕
23. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
24. `{"op":"buff","e":"strength","t":150,"a":3}` — 強化〔e="strength", t=150, a=3〕
25. `{"op":"fx","p":"spark","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="spark", n=24, at="ring", r=12, y=0.5〕
26. `{"op":"sound","s":"anvil","v":0.85,"pi":0.97}` — 効果音〔s="anvil", v=0.85, pi=0.97〕
27. `{"op":"cone","r":12.0,"a":95.0}` — 扇形対象の取得〔r=12.0, a=95.0〕
28. `{"op":"dmg","m":0.95}` — 追加攻撃〔m=0.95〕
29. `{"op":"eff","e":"fatigue","t":140,"a":1}` — 敵への状態異常〔e="fatigue", t=140, a=1〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"resist","t":240,"a":3}` — 強化〔e="resist", t=240, a=3〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"adapt","t":160}` — adapt〔t=160〕
34. `{"op":"fx","p":"spark","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="spark", n=24, at="ring", r=5.5, y=0.7〕
35. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
36. `{"op":"eff","e":"fatigue","t":148,"a":123}` — 敵への状態異常〔e="fatigue", t=148, a=123〕
37. `{"op":"self"}` — 対象を自分へ〔〕
38. `{"op":"buff","e":"resist","t":140,"a":2}` — 強化〔e="resist", t=140, a=2〕
39. `{"op":"fx","p":"spark","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="spark", n=16, at="ring", r=3.7, y=0.55〕
40. `{"op":"cone","r":12,"a":100}` — 扇形対象の取得〔r=12, a=100〕
41. `{"op":"eff","e":"weakness","t":75,"a":9}` — 敵への状態異常〔e="weakness", t=75, a=9〕
42. `{"op":"knock","f":2.1}` — knock〔f=2.1〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 死生反転の角冠 — 神格装飾品（Curios relic_charm） (`hakyoku_charm`)

**現行パラメータ**：rank=1、damage登録値=75.8241、relics側CD=180tick、art側CD=180tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（11命令）**：

01. `{"op":"low","pct":0.3,"ops":[{"op":"self"},{"op":"undying","t":40}]}` — low〔pct=0.3, ops=[{"op":"self"},{"op":"undying","t":40}]〕
02. `{"op":"self"}` — 対象を自分へ〔〕
03. `{"op":"buff","e":"regen","t":45,"a":0}` — 強化〔e="regen", t=45, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
06. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
07. `{"op":"buff","e":"strength","t":45,"a":1}` — 強化〔e="strength", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"resist","t":42,"a":2}` — 強化〔e="resist", t=42, a=2〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"speed","t":48,"a":5}` — 強化〔e="speed", t=48, a=5〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（36命令）**：

01. `{"op":"fx","p":"sculk","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="sculk", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"sculk","n":4,"at":"self","s":0.7}` — 粒子演出〔p="sculk", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"lava","n":10,"at":"self"}` — 粒子演出〔p="lava", n=10, at="self"〕
04. `{"op":"fx","p":"sculk","n":30,"at":"self"}` — 粒子演出〔p="sculk", n=30, at="self"〕
05. `{"op":"sound","s":"roar","v":0.6,"pi":1.2}` — 効果音〔s="roar", v=0.6, pi=1.2〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"undying","t":100}` — 死亡防護〔t=100〕
08. `{"op":"healpct","v":0.25}` — 最大HP割合回復〔v=0.25〕
09. `{"op":"cleanse"}` — 状態異常解除〔〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"regen","t":210,"a":1}` — 強化〔e="regen", t=210, a=1〕
13. `{"op":"fx","p":"spark","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="spark", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"crit","n":36,"at":"line","r":24}` — 粒子演出〔p="crit", n=36, at="line", r=24〕
15. `{"op":"sound","s":"anvil","v":1.05,"pi":1.14}` — 効果音〔s="anvil", v=1.05, pi=1.14〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"guard","t":95}` — 防御〔t=95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
20. `{"op":"cleanse"}` — 状態異常解除〔〕
21. `{"op":"buff","e":"strength","t":180,"a":3}` — 強化〔e="strength", t=180, a=3〕
22. `{"op":"guard","t":95}` — 防御〔t=95〕
23. `{"op":"fx","p":"spark","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="spark", n=30, at="ring", r=4.0, y=0.7〕
24. `{"op":"sound","s":"anvil","v":0.8,"pi":1.1}` — 効果音〔s="anvil", v=0.8, pi=1.1〕
25. `{"op":"self"}` — 対象を自分へ〔〕
26. `{"op":"buff","e":"resist","t":300,"a":4}` — 強化〔e="resist", t=300, a=4〕
27. `{"op":"guard","t":155}` — 防御〔t=155〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"buff","e":"resist","t":240,"a":2}` — 強化〔e="resist", t=240, a=2〕
30. `{"op":"fx","p":"spark","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="spark", n=20, at="ring", r=4, y=0.4〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"resist","t":140,"a":2}` — 強化〔e="resist", t=140, a=2〕
33. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
34. `{"op":"eff","e":"fatigue","t":110,"a":123}` — 敵への状態異常〔e="fatigue", t=110, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 討伐不能・無窮の覇核 — 超越神器（武器欄） (`hakyoku_legend`)

**現行パラメータ**：rank=3、damage登録値=925.5、relics側CD=335tick、art側CD=335tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10、minecraft:knockback:6。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"adapt","t":40}` — adapt〔t=40〕
06. `{"op":"low","pct":0.4,"ops":[{"op":"self"},{"op":"undying","t":40}]}` — low〔pct=0.4, ops=[{"op":"self"},{"op":"undying","t":40}]〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
09. `{"op":"buff","e":"strength","t":45,"a":3}` — 強化〔e="strength", t=45, a=3〕
10. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（9命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
03. `{"op":"dmg","m":5.0,"magic":1}` — 追加攻撃〔m=5.0, magic=1〕
04. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"fatigue","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"fatigue","t":160,"a":1}]〕
05. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
06. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"spark","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"spark","n":10,"at":"t","s":0.35}]〕
07. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
08. `{"op":"chance","p":0.325,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":20,"at":"t","s":0.33},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.325, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":20,"at":"t","s":0.33},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":160,"x":2.5}]〕
09. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]〕

**権能発動時の命令（25命令）**：

01. `{"op":"fx","p":"sculk","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="sculk", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"sculk","n":4,"at":"self","s":0.7}` — 粒子演出〔p="sculk", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"lava","n":10,"at":"self"}` — 粒子演出〔p="lava", n=10, at="self"〕
04. `{"op":"fx","p":"sculk","n":30,"at":"self"}` — 粒子演出〔p="sculk", n=30, at="self"〕
05. `{"op":"sound","s":"roar","v":0.6,"pi":1.2}` — 効果音〔s="roar", v=0.6, pi=1.2〕
06. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
07. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
08. `{"op":"dmg","m":3.36}` — 追加攻撃〔m=3.36〕
09. `{"op":"dmg","m":5.6,"magic":1}` — 追加攻撃〔m=5.6, magic=1〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"undying","t":180}` — 死亡防護〔t=180〕
12. `{"op":"adapt","t":2400}` — adapt〔t=2400〕
13. `{"op":"healpct","v":0.6}` — 最大HP割合回復〔v=0.6〕
14. `{"op":"buff","e":"strength","t":1200,"a":12}` — 強化〔e="strength", t=1200, a=12〕
15. `{"op":"fx","p":"lava","n":12,"at":"t","s":0.5}` — 粒子演出〔p="lava", n=12, at="t", s=0.5〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"guard","t":135}` — 防御〔t=135〕
18. `{"op":"cleanse"}` — 状態異常解除〔〕
19. `{"op":"buff","e":"resist","a":2,"t":140}` — 強化〔e="resist", a=2, t=140〕
20. `{"op":"fx","p":"crit","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="crit", n=50, at="ring", r=8.0, y=0.6〕
21. `{"op":"fx","p":"smoke","n":32,"at":"line","r":30}` — 粒子演出〔p="smoke", n=32, at="line", r=30〕
22. `{"op":"sound","s":"anvil","v":1.15,"pi":0.95}` — 効果音〔s="anvil", v=1.15, pi=0.95〕
23. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.hakyoku_legend.stage0","ops":[{"op":"fx","p":"spark","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"anvil","v":0.9,"pi":1.2},{"op":"fx","p":"spark","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":10},{"op":"fx","p":"spark","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"crit","n":36,"at":"line","r":24},{"op":"sound","s":"anvil","v":1.05,"pi":1.14},{"op":"cone","r":22.0,"a":125.0},{"op":"dmg","m":4.05},{"op":"mark","t":120,"x":2.21},{"op":"self"},{"op":"buff","e":"resist","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.hakyoku_legend.stage1","ops":[{"op":"fx","p":"spark","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"anvil","v":1.05,"pi":1.0},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"spark","n":6,"at":"line","r":15},{"op":"fx","p":"crit","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"smoke","n":32,"at":"line","r":30},{"op":"sound","s":"anvil","v":1.15,"pi":0.95},{"op":"self"},{"op":"adapt"},{"op":"guard","t":130},{"op":"buff","e":"strength","t":180,"a":3},{"op":"area","r":14.0,"n":10},{"op":"eff","e":"fatigue","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.hakyoku_legend.stage2","ops":[{"op":"fx","p":"spark","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"anvil","v":1.25,"pi":0.75},{"op":"fx","p":"end_rod","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"spark","n":10,"at":"line","r":20},{"op":"fx","p":"spark","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"crit","n":48,"at":"line","r":48},{"op":"fx","p":"smoke","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"anvil","v":1.5,"pi":0.75},{"op":"area","r":32.0,"n":25},{"op":"dmg","m":10.53},{"op":"strip"},{"op":"self"},{"op":"adapt"},{"op":"healpct","v":0.55},{"op":"buff","e":"resist","t":180,"a":3},{"op":"fx","p":"smoke","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"spark","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":28.0,"n":24},{"op":"dmg","m":3.2},{"op":"self"},{"op":"adapt"},{"op":"healpct","v":0.4},{"op":"buff","e":"strength","t":180,"a":4},{"op":"cone","r":21.0,"a":110.0},{"op":"dmg","m":0.9},{"op":"eff","e":"fatigue","t":160,"a":2},{"op":"self"},{"op":"buff","e":"resist","t":240,"a":4},{"op":"self"},{"op":"adapt","t":160},{"op":"fx","p":"spark","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"anvil","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"weakness","t":75,"a":9},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.hakyoku_legend.stage0","ops":[{"op":"fx","p":"spark","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"anvil","v":0.9,"pi":1.2},{"op":"fx","p":"spark","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":10},{"op":"fx","p":"spark","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"crit","n":36,"at":"line","r":24},{"op":"sound","s":"anvil","v":1.05,"pi":1.14},{"op":"cone","r":22.0,"a":125.0},{"op":"dmg","m":4.05},{"op":"mark","t":120,"x":2.21},{"op":"self"},{"op":"buff","e":"resist","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.hakyoku_legend.stage1","ops":[{"op":"fx","p":"spark","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"anvil","v":1.05,"pi":1.0},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"spark","n":6,"at":"line","r":15},{"op":"fx","p":"crit","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"smoke","n":32,"at":"line","r":30},{"op":"sound","s":"anvil","v":1.15,"pi":0.95},{"op":"self"},{"op":"adapt"},{"op":"guard","t":130},{"op":"buff","e":"strength","t":180,"a":3},{"op":"area","r":14.0,"n":10},{"op":"eff","e":"fatigue","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.hakyoku_legend.stage2","ops":[{"op":"fx","p":"spark","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"anvil","v":1.25,"pi":0.75},{"op":"fx","p":"end_rod","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"spark","n":10,"at":"line","r":20},{"op":"fx","p":"spark","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"crit","n":48,"at":"line","r":48},{"op":"fx","p":"smoke","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"anvil","v":1.5,"pi":0.75},{"op":"area","r":32.0,"n":25},{"op":"dmg","m":10.53},{"op":"strip"},{"op":"self"},{"op":"adapt"},{"op":"healpct","v":0.55},{"op":"buff","e":"resist","t":180,"a":3},{"op":"fx","p":"smoke","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"spark","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":28.0,"n":24},{"op":"dmg","m":3.2},{"op":"self"},{"op":"adapt"},{"op":"healpct","v":0.4},{"op":"buff","e":"strength","t":180,"a":4},{"op":"cone","r":21.0,"a":110.0},{"op":"dmg","m":0.9},{"op":"eff","e":"fatigue","t":160,"a":2},{"op":"self"},{"op":"buff","e":"resist","t":240,"a":4},{"op":"self"},{"op":"adapt","t":160},{"op":"fx","p":"spark","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"anvil","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"weakness","t":75,"a":9},{"op":"mark","t":135,"x":1.8}]}]〕
24. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
25. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 28. 万物天敵 シンラ

**モブ側の動きの方向性**：小さな視線・一指・静かな歩みのみで敵の能力へ対抗する。。

### 天敵の日傘 — 討伐武器（メイン／武器欄） (`shinra_weapon`)

**現行パラメータ**：rank=1、damage登録値=336.41667、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12。

**装備中の常時命令（5命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"adapt","t":40}` — adapt〔t=40〕
03. `{"op":"buff","e":"night","t":300,"a":0}` — 強化〔e="night", t=300, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（8命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"mark","t":200,"x":2.0}` — 刻印〔t=200, x=2.0〕
03. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"weakness","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"weakness","t":90,"a":0}]〕
04. `{"op":"chance","p":0.53,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":13,"at":"t","s":0.24},{"op":"mark","t":160,"x":1.93},{"op":"eff","e":"weakness","t":91,"a":1}]}` — 抽選〔p=0.53, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":13,"at":"t","s":0.24},{"op":"mark","t":160,"x":1.93},{"op":"eff","e":"weakness","t":91,"a":1}]〕
05. `{"op":"chance","p":0.204,"ops":[{"op":"victim"},{"op":"dmg","m":0.27}]}` — 抽選〔p=0.204, ops=[{"op":"victim"},{"op":"dmg","m":0.27}]〕
06. `{"op":"chance","p":0.142,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":8,"at":"t","s":0.25},{"op":"strip"}]}` — 抽選〔p=0.142, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":8,"at":"t","s":0.25},{"op":"strip"}]〕
07. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]〕
08. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]〕

**権能発動時の命令（27命令）**：

01. `{"op":"fx","p":"crit","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="crit", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"crit","n":4,"at":"self","s":0.7}` — 粒子演出〔p="crit", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"crit","n":40,"at":"self"}` — 粒子演出〔p="crit", n=40, at="self"〕
04. `{"op":"fx","p":"smoke","n":20,"at":"self"}` — 粒子演出〔p="smoke", n=20, at="self"〕
05. `{"op":"sound","s":"sonic","v":0.6,"pi":1.8}` — 効果音〔s="sonic", v=0.6, pi=1.8〕
06. `{"op":"area","r":24,"n":36}` — 円形対象の取得〔r=24, n=36〕
07. `{"op":"mark","t":600,"x":3.0}` — 刻印〔t=600, x=3.0〕
08. `{"op":"eff","e":"glow","t":600,"a":0}` — 敵への状態異常〔e="glow", t=600, a=0〕
09. `{"op":"strip"}` — 強化解除〔〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"adapt","t":600}` — adapt〔t=600〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"fx","p":"soul","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="soul", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"crit","n":36,"at":"line","r":24}` — 粒子演出〔p="crit", n=36, at="line", r=24〕
15. `{"op":"line","r":58.0,"w":3.0}` — 線分対象の取得〔r=58.0, w=3.0〕
16. `{"op":"strip"}` — 強化解除〔〕
17. `{"op":"mark","t":140,"x":1.9}` — 刻印〔t=140, x=1.9〕
18. `{"op":"dmg","m":2.4}` — 追加攻撃〔m=2.4〕
19. `{"op":"fx","p":"crit","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="crit", n=16, at="ring", r=5.0〕
20. `{"op":"sound","s":"sonic","v":0.75,"pi":1.15}` — 効果音〔s="sonic", v=0.75, pi=1.15〕
21. `{"op":"line","r":18,"w":2}` — 線分対象の取得〔r=18, w=2〕
22. `{"op":"dmg","m":1.05}` — 追加攻撃〔m=1.05〕
23. `{"op":"eff","e":"weakness","t":65,"a":0}` — 敵への状態異常〔e="weakness", t=65, a=0〕
24. `{"op":"fx","p":"crit","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="crit", n=24, at="ring", r=4.5, y=0.6〕
25. `{"op":"sound","s":"sonic","v":0.8,"pi":0.8}` — 効果音〔s="sonic", v=0.8, pi=0.8〕
26. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
27. `{"op":"eff","e":"weakness","t":100,"a":124}` — 敵への状態異常〔e="weakness", t=100, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 存在狩猟の解析眼 — 神威触媒（Curios relic_focus） (`shinra_focus`)

**現行パラメータ**：rank=2、damage登録値=73.7748、relics側CD=145tick、art側CD=145tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"night","t":300,"a":0}` — 強化〔e="night", t=300, a=0〕
03. `{"op":"buff","e":"speed","t":40,"a":0}` — 強化〔e="speed", t=40, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"resist","t":45,"a":0}` — 強化〔e="resist", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"resist","t":42,"a":2}` — 強化〔e="resist", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（42命令）**：

01. `{"op":"fx","p":"crit","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="crit", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"crit","n":6,"at":"self","s":0.7}` — 粒子演出〔p="crit", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"crit","n":40,"at":"self"}` — 粒子演出〔p="crit", n=40, at="self"〕
04. `{"op":"fx","p":"smoke","n":20,"at":"self"}` — 粒子演出〔p="smoke", n=20, at="self"〕
05. `{"op":"sound","s":"sonic","v":0.6,"pi":1.8}` — 効果音〔s="sonic", v=0.6, pi=1.8〕
06. `{"op":"near","r":48,"n":1}` — near〔r=48, n=1〕
07. `{"op":"behind"}` — behind〔〕
08. `{"op":"mark","t":600,"x":4.0}` — 刻印〔t=600, x=4.0〕
09. `{"op":"dmg","m":2.0}` — 追加攻撃〔m=2.0〕
10. `{"op":"dmg","m":1.8,"magic":1}` — 追加攻撃〔m=1.8, magic=1〕
11. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"resist","t":150,"a":1}` — 強化〔e="resist", t=150, a=1〕
14. `{"op":"fx","p":"crit","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="crit", n=50, at="ring", r=8.0, y=0.6〕
15. `{"op":"fx","p":"sonic","n":32,"at":"line","r":30}` — 粒子演出〔p="sonic", n=32, at="line", r=30〕
16. `{"op":"sound","s":"sonic","v":1.15,"pi":0.95}` — 効果音〔s="sonic", v=1.15, pi=0.95〕
17. `{"op":"area","r":22.0,"n":18}` — 円形対象の取得〔r=22.0, n=18〕
18. `{"op":"strip"}` — 強化解除〔〕
19. `{"op":"eff","e":"weakness","t":115,"a":3}` — 敵への状態異常〔e="weakness", t=115, a=3〕
20. `{"op":"dmg","m":2.3}` — 追加攻撃〔m=2.3〕
21. `{"op":"self"}` — 対象を自分へ〔〕
22. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
23. `{"op":"buff","e":"resist","t":150,"a":3}` — 強化〔e="resist", t=150, a=3〕
24. `{"op":"fx","p":"crit","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="crit", n=24, at="ring", r=12, y=0.5〕
25. `{"op":"sound","s":"sonic","v":0.85,"pi":1.04}` — 効果音〔s="sonic", v=0.85, pi=1.04〕
26. `{"op":"line","r":32.0,"w":2.5}` — 線分対象の取得〔r=32.0, w=2.5〕
27. `{"op":"dmg","m":0.85}` — 追加攻撃〔m=0.85〕
28. `{"op":"eff","e":"weakness","t":160,"a":1}` — 敵への状態異常〔e="weakness", t=160, a=1〕
29. `{"op":"self"}` — 対象を自分へ〔〕
30. `{"op":"buff","e":"resist","t":200,"a":3}` — 強化〔e="resist", t=200, a=3〕
31. `{"op":"area","r":20,"n":10}` — 円形対象の取得〔r=20, n=10〕
32. `{"op":"strip"}` — 強化解除〔〕
33. `{"op":"fx","p":"crit","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="crit", n=24, at="ring", r=5.5, y=0.7〕
34. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
35. `{"op":"eff","e":"weakness","t":135,"a":123}` — 敵への状態異常〔e="weakness", t=135, a=123〕
36. `{"op":"self"}` — 対象を自分へ〔〕
37. `{"op":"buff","e":"resist","t":140,"a":2}` — 強化〔e="resist", t=140, a=2〕
38. `{"op":"fx","p":"end_rod","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="end_rod", n=16, at="ring", r=3.7, y=0.55〕
39. `{"op":"self"}` — 対象を自分へ〔〕
40. `{"op":"cleanse"}` — 状態異常解除〔〕
41. `{"op":"guard","t":100}` — 防御〔t=100〕
42. `{"op":"reflect","t":100,"r":9}` — 反射〔t=100, r=9〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 無敵喰らいの鬼角 — 神格装飾品（Curios relic_charm） (`shinra_charm`)

**現行パラメータ**：rank=1、damage登録値=73.7748、relics側CD=175tick、art側CD=175tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（12命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"adapt","t":40}` — adapt〔t=40〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"resist","t":45,"a":0}` — 強化〔e="resist", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
08. `{"op":"buff","e":"resist","t":45,"a":1}` — 強化〔e="resist", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"resist","t":42,"a":2}` — 強化〔e="resist", t=42, a=2〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"resist","t":48,"a":3}` — 強化〔e="resist", t=48, a=3〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（38命令）**：

01. `{"op":"fx","p":"crit","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="crit", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"crit","n":4,"at":"self","s":0.7}` — 粒子演出〔p="crit", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"crit","n":40,"at":"self"}` — 粒子演出〔p="crit", n=40, at="self"〕
04. `{"op":"fx","p":"smoke","n":20,"at":"self"}` — 粒子演出〔p="smoke", n=20, at="self"〕
05. `{"op":"sound","s":"sonic","v":0.6,"pi":1.8}` — 効果音〔s="sonic", v=0.6, pi=1.8〕
06. `{"op":"area","r":20,"n":36}` — 円形対象の取得〔r=20, n=36〕
07. `{"op":"strip"}` — 強化解除〔〕
08. `{"op":"dmg","m":1.2}` — 追加攻撃〔m=1.2〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"guard","t":40}` — 防御〔t=40〕
11. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"resist","t":210,"a":1}` — 強化〔e="resist", t=210, a=1〕
14. `{"op":"fx","p":"soul","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="soul", n=46, at="ring", r=5.5, y=0.25〕
15. `{"op":"fx","p":"crit","n":36,"at":"line","r":24}` — 粒子演出〔p="crit", n=36, at="line", r=24〕
16. `{"op":"sound","s":"sonic","v":1.05,"pi":1.14}` — 効果音〔s="sonic", v=1.05, pi=1.14〕
17. `{"op":"self"}` — 対象を自分へ〔〕
18. `{"op":"guard","t":95}` — 防御〔t=95〕
19. `{"op":"self"}` — 対象を自分へ〔〕
20. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
21. `{"op":"cleanse"}` — 状態異常解除〔〕
22. `{"op":"buff","e":"resist","t":180,"a":3}` — 強化〔e="resist", t=180, a=3〕
23. `{"op":"guard","t":95}` — 防御〔t=95〕
24. `{"op":"fx","p":"crit","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="crit", n=30, at="ring", r=4.0, y=0.7〕
25. `{"op":"sound","s":"sonic","v":0.8,"pi":1.1}` — 効果音〔s="sonic", v=0.8, pi=1.1〕
26. `{"op":"self"}` — 対象を自分へ〔〕
27. `{"op":"buff","e":"resist","t":260,"a":4}` — 強化〔e="resist", t=260, a=4〕
28. `{"op":"guard","t":170}` — 防御〔t=170〕
29. `{"op":"self"}` — 対象を自分へ〔〕
30. `{"op":"cleanse"}` — 状態異常解除〔〕
31. `{"op":"fx","p":"crit","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="crit", n=20, at="ring", r=4, y=0.4〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"buff","e":"resist","t":140,"a":2}` — 強化〔e="resist", t=140, a=2〕
34. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
35. `{"op":"eff","e":"weakness","t":100,"a":123}` — 敵への状態異常〔e="weakness", t=100, a=123〕
36. `{"op":"self"}` — 対象を自分へ〔〕
37. `{"op":"guard","t":95}` — 防御〔t=95〕
38. `{"op":"cleanse"}` — 状態異常解除〔〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 終焉例外・万物天敵 — 超越神器（武器欄） (`shinra_legend`)

**現行パラメータ**：rank=3、damage登録値=578.1875、relics側CD=330tick、art側CD=330tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"adapt","t":40}` — adapt〔t=40〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
08. `{"op":"buff","e":"resist","t":45,"a":3}` — 強化〔e="resist", t=45, a=3〕
09. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（9命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"mark","t":200,"x":3.0}` — 刻印〔t=200, x=3.0〕
03. `{"op":"dmg","m":5.0,"magic":1}` — 追加攻撃〔m=5.0, magic=1〕
04. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"weakness","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"weakness","t":160,"a":1}]〕
05. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"soul","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"soul","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
06. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"crit","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"crit","n":10,"at":"t","s":0.35}]〕
07. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
08. `{"op":"chance","p":0.35,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.35, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]〕
09. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]〕

**権能発動時の命令（24命令）**：

01. `{"op":"fx","p":"crit","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="crit", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"crit","n":4,"at":"self","s":0.7}` — 粒子演出〔p="crit", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"crit","n":40,"at":"self"}` — 粒子演出〔p="crit", n=40, at="self"〕
04. `{"op":"fx","p":"smoke","n":20,"at":"self"}` — 粒子演出〔p="smoke", n=20, at="self"〕
05. `{"op":"sound","s":"sonic","v":0.6,"pi":1.8}` — 効果音〔s="sonic", v=0.6, pi=1.8〕
06. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
07. `{"op":"strip"}` — 強化解除〔〕
08. `{"op":"mark","t":1200,"x":5.0}` — 刻印〔t=1200, x=5.0〕
09. `{"op":"dmg","m":3.36}` — 追加攻撃〔m=3.36〕
10. `{"op":"dmg","m":5.6,"magic":1}` — 追加攻撃〔m=5.6, magic=1〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"adapt","t":2400}` — adapt〔t=2400〕
13. `{"op":"undying","t":180}` — 死亡防護〔t=180〕
14. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
15. `{"op":"line","r":64,"w":3}` — 線分対象の取得〔r=64, w=3〕
16. `{"op":"dmg","m":1.8}` — 追加攻撃〔m=1.8〕
17. `{"op":"strip"}` — 強化解除〔〕
18. `{"op":"mark","t":120,"x":1.6}` — 刻印〔t=120, x=1.6〕
19. `{"op":"fx","p":"crit","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="crit", n=50, at="ring", r=8.0, y=0.6〕
20. `{"op":"fx","p":"sonic","n":32,"at":"line","r":30}` — 粒子演出〔p="sonic", n=32, at="line", r=30〕
21. `{"op":"sound","s":"sonic","v":1.15,"pi":0.95}` — 効果音〔s="sonic", v=1.15, pi=0.95〕
22. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.shinra_legend.stage0","ops":[{"op":"fx","p":"crit","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"sonic","v":0.9,"pi":1.2},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"crit","n":6,"at":"line","r":10},{"op":"fx","p":"soul","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"crit","n":36,"at":"line","r":24},{"op":"sound","s":"sonic","v":1.05,"pi":1.14},{"op":"line","r":58.0,"w":3.0},{"op":"strip"},{"op":"mark","t":140,"x":2.47},{"op":"dmg","m":3.24},{"op":"self"},{"op":"buff","e":"resist","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.shinra_legend.stage1","ops":[{"op":"fx","p":"crit","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"sonic","v":1.05,"pi":1.0},{"op":"fx","p":"crit","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":15},{"op":"fx","p":"crit","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"sonic","n":32,"at":"line","r":30},{"op":"sound","s":"sonic","v":1.15,"pi":0.95},{"op":"area","r":22.0,"n":18},{"op":"strip"},{"op":"eff","e":"weakness","t":115,"a":3},{"op":"dmg","m":3.335},{"op":"area","r":16.0,"n":10},{"op":"eff","e":"weakness","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.shinra_legend.stage2","ops":[{"op":"fx","p":"crit","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"sonic","v":1.25,"pi":0.75},{"op":"fx","p":"crit","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"end_rod","n":10,"at":"line","r":20},{"op":"fx","p":"soul","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"crit","n":48,"at":"line","r":48},{"op":"fx","p":"sonic","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"sonic","v":1.5,"pi":0.75},{"op":"line","r":74.0,"w":5.0},{"op":"dmg","m":10.206},{"op":"strip"},{"op":"mark","t":190,"x":2.86},{"op":"self"},{"op":"cleanse"},{"op":"guard","t":140},{"op":"fx","p":"sonic","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"crit","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"line","r":72.0,"w":4.0},{"op":"dmg","m":3.2},{"op":"strip"},{"op":"mark","t":200,"x":2.5},{"op":"self"},{"op":"cleanse"},{"op":"line","r":44.0,"w":4.0},{"op":"dmg","m":1.0},{"op":"eff","e":"weakness","t":160,"a":2},{"op":"self"},{"op":"buff","e":"resist","t":240,"a":4},{"op":"area","r":20,"n":10},{"op":"strip"},{"op":"fx","p":"crit","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"sonic","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"self"},{"op":"cleanse"},{"op":"guard","t":105},{"op":"area","r":17,"n":8},{"op":"strip"}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.shinra_legend.stage0","ops":[{"op":"fx","p":"crit","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"sonic","v":0.9,"pi":1.2},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"crit","n":6,"at":"line","r":10},{"op":"fx","p":"soul","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"crit","n":36,"at":"line","r":24},{"op":"sound","s":"sonic","v":1.05,"pi":1.14},{"op":"line","r":58.0,"w":3.0},{"op":"strip"},{"op":"mark","t":140,"x":2.47},{"op":"dmg","m":3.24},{"op":"self"},{"op":"buff","e":"resist","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.shinra_legend.stage1","ops":[{"op":"fx","p":"crit","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"sonic","v":1.05,"pi":1.0},{"op":"fx","p":"crit","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":15},{"op":"fx","p":"crit","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"sonic","n":32,"at":"line","r":30},{"op":"sound","s":"sonic","v":1.15,"pi":0.95},{"op":"area","r":22.0,"n":18},{"op":"strip"},{"op":"eff","e":"weakness","t":115,"a":3},{"op":"dmg","m":3.335},{"op":"area","r":16.0,"n":10},{"op":"eff","e":"weakness","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.shinra_legend.stage2","ops":[{"op":"fx","p":"crit","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"sonic","v":1.25,"pi":0.75},{"op":"fx","p":"crit","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"end_rod","n":10,"at":"line","r":20},{"op":"fx","p":"soul","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"crit","n":48,"at":"line","r":48},{"op":"fx","p":"sonic","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"sonic","v":1.5,"pi":0.75},{"op":"line","r":74.0,"w":5.0},{"op":"dmg","m":10.206},{"op":"strip"},{"op":"mark","t":190,"x":2.86},{"op":"self"},{"op":"cleanse"},{"op":"guard","t":140},{"op":"fx","p":"sonic","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"crit","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"line","r":72.0,"w":4.0},{"op":"dmg","m":3.2},{"op":"strip"},{"op":"mark","t":200,"x":2.5},{"op":"self"},{"op":"cleanse"},{"op":"line","r":44.0,"w":4.0},{"op":"dmg","m":1.0},{"op":"eff","e":"weakness","t":160,"a":2},{"op":"self"},{"op":"buff","e":"resist","t":240,"a":4},{"op":"area","r":20,"n":10},{"op":"strip"},{"op":"fx","p":"crit","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"sonic","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"self"},{"op":"cleanse"},{"op":"guard","t":105},{"op":"area","r":17,"n":8},{"op":"strip"}]}]〕
23. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
24. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 29. 全界支配 アインソフオウル

**モブ側の動きの方向性**：自分の分岐残像と別世界の軍勢を幾重にも重ねる。。

### 分岐確定の王剣 — 討伐武器（メイン／武器欄） (`ain_sof_aur_weapon`)

**現行パラメータ**：rank=1、damage登録値=298.66667、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:sweeping_edge:25。

**装備中の常時命令（4命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"luck","t":40,"a":3}` — 強化〔e="luck", t=40, a=3〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（7命令）**：

01. `{"op":"chance","p":0.5,"ops":[{"op":"victim"},{"op":"dmg","m":0.4}]}` — 抽選〔p=0.5, ops=[{"op":"victim"},{"op":"dmg","m":0.4}]〕
02. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"glow","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"glow","t":90,"a":0}]〕
03. `{"op":"chance","p":0.535,"ops":[{"op":"victim"},{"op":"fx","p":"portal","n":15,"at":"t","s":0.24},{"op":"mark","t":180,"x":2.07},{"op":"eff","e":"slow","t":103,"a":0}]}` — 抽選〔p=0.535, ops=[{"op":"victim"},{"op":"fx","p":"portal","n":15,"at":"t","s":0.24},{"op":"mark","t":180,"x":2.07},{"op":"eff","e":"slow","t":103,"a":0}]〕
04. `{"op":"chance","p":0.231,"ops":[{"op":"victim"},{"op":"dmg","m":0.305}]}` — 抽選〔p=0.231, ops=[{"op":"victim"},{"op":"dmg","m":0.305}]〕
05. `{"op":"chance","p":0.085,"ops":[{"op":"victim"},{"op":"fx","p":"portal","n":8,"at":"t","s":0.25},{"op":"dmg","m":0.28}]}` — 抽選〔p=0.085, ops=[{"op":"victim"},{"op":"fx","p":"portal","n":8,"at":"t","s":0.25},{"op":"dmg","m":0.28}]〕
06. `{"op":"chance","p":0.24,"ops":[{"op":"victim"},{"op":"fx","p":"portal","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.24, ops=[{"op":"victim"},{"op":"fx","p":"portal","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]〕
07. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"portal","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"portal","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]〕

**権能発動時の命令（23命令）**：

01. `{"op":"fx","p":"portal","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="portal", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"portal","n":4,"at":"self","s":0.7}` — 粒子演出〔p="portal", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":40,"at":"self","s":1.4}` — 粒子演出〔p="end_rod", n=40, at="self", s=1.4〕
04. `{"op":"fx","p":"portal","n":40,"at":"self"}` — 粒子演出〔p="portal", n=40, at="self"〕
05. `{"op":"sound","s":"mirror","v":1.0,"pi":1.6}` — 効果音〔s="mirror", v=1.0, pi=1.6〕
06. `{"op":"chance","p":0.5,"ops":[{"op":"area","r":24,"n":36},{"op":"dmg","m":2.0},{"op":"stun","t":65}],"else":[{"op":"area","r":24,"n":36},{"op":"dmg","m":1.0},{"op":"strip"},{"op":"self"},{"op":"healpct","v":0.25}]}` — 抽選〔p=0.5, ops=[{"op":"area","r":24,"n":36},{"op":"dmg","m":2.0},{"op":"stun","t":65}], else=[{"op":"area","r":24,"n":36},{"op":"dmg","m":1.0},{"op":"strip"},{"op":"self"},{"op":"healpct","v":0.25}]〕
07. `{"op":"summon","k":"golem","n":2}` — 召喚〔k="golem", n=2〕
08. `{"op":"blink","d":8}` — blink〔d=8〕
09. `{"op":"fx","p":"end_rod","n":12,"at":"t","s":0.5}` — 粒子演出〔p="end_rod", n=12, at="t", s=0.5〕
10. `{"op":"fx","p":"portal","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="portal", n=46, at="ring", r=5.5, y=0.25〕
11. `{"op":"fx","p":"rportal","n":36,"at":"line","r":24}` — 粒子演出〔p="rportal", n=36, at="line", r=24〕
12. `{"op":"summon","k":"golem","n":4}` — 召喚〔k="golem", n=4〕
13. `{"op":"area","r":25.0,"n":20}` — 円形対象の取得〔r=25.0, n=20〕
14. `{"op":"dmg","m":2.4}` — 追加攻撃〔m=2.4〕
15. `{"op":"fx","p":"portal","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="portal", n=16, at="ring", r=5.0〕
16. `{"op":"sound","s":"spell","v":0.75,"pi":1.15}` — 効果音〔s="spell", v=0.75, pi=1.15〕
17. `{"op":"area","r":9,"n":8}` — 円形対象の取得〔r=9, n=8〕
18. `{"op":"dmg","m":0.9}` — 追加攻撃〔m=0.9〕
19. `{"op":"eff","e":"slow","t":65,"a":0}` — 敵への状態異常〔e="slow", t=65, a=0〕
20. `{"op":"fx","p":"portal","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="portal", n=24, at="ring", r=4.5, y=0.6〕
21. `{"op":"sound","s":"mirror","v":0.8,"pi":0.8}` — 効果音〔s="mirror", v=0.8, pi=0.8〕
22. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
23. `{"op":"eff","e":"slow","t":32,"a":124}` — 敵への状態異常〔e="slow", t=32, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 並行世界の星鏡 — 神威触媒（Curios relic_focus） (`ain_sof_aur_focus`)

**現行パラメータ**：rank=2、damage登録値=69.6762、relics側CD=160tick、art側CD=160tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"reflect","t":25,"r":6}` — 反射〔t=25, r=6〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"luck","t":45,"a":0}` — 強化〔e="luck", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"luck","t":45,"a":2}` — 強化〔e="luck", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"luck","t":42,"a":2}` — 強化〔e="luck", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（41命令）**：

01. `{"op":"fx","p":"portal","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="portal", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"portal","n":6,"at":"self","s":0.7}` — 粒子演出〔p="portal", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":40,"at":"self","s":1.4}` — 粒子演出〔p="end_rod", n=40, at="self", s=1.4〕
04. `{"op":"fx","p":"portal","n":40,"at":"self"}` — 粒子演出〔p="portal", n=40, at="self"〕
05. `{"op":"sound","s":"mirror","v":1.0,"pi":1.6}` — 効果音〔s="mirror", v=1.0, pi=1.6〕
06. `{"op":"summon","k":"golem","n":4}` — 召喚〔k="golem", n=4〕
07. `{"op":"reflect","t":200,"r":24}` — 反射〔t=200, r=24〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"guard","t":60}` — 防御〔t=60〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"luck","t":150,"a":1}` — 強化〔e="luck", t=150, a=1〕
13. `{"op":"fx","p":"rportal","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="rportal", n=50, at="ring", r=8.0, y=0.6〕
14. `{"op":"fx","p":"end_rod","n":32,"at":"line","r":30}` — 粒子演出〔p="end_rod", n=32, at="line", r=30〕
15. `{"op":"sound","s":"teleport","v":1.15,"pi":0.95}` — 効果音〔s="teleport", v=1.15, pi=0.95〕
16. `{"op":"chain","n":6,"r":20.0}` — chain〔n=6, r=20.0〕
17. `{"op":"dmg","m":3.0}` — 追加攻撃〔m=3.0〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"guard","t":105}` — 防御〔t=105〕
20. `{"op":"self"}` — 対象を自分へ〔〕
21. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
22. `{"op":"buff","e":"luck","t":150,"a":3}` — 強化〔e="luck", t=150, a=3〕
23. `{"op":"fx","p":"portal","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="portal", n=24, at="ring", r=12, y=0.5〕
24. `{"op":"sound","s":"mirror","v":0.85,"pi":1.11}` — 効果音〔s="mirror", v=0.85, pi=1.11〕
25. `{"op":"area","r":16.0,"n":12}` — 円形対象の取得〔r=16.0, n=12〕
26. `{"op":"dmg","m":0.8}` — 追加攻撃〔m=0.8〕
27. `{"op":"eff","e":"slow","t":100,"a":1}` — 敵への状態異常〔e="slow", t=100, a=1〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"buff","e":"luck","t":220,"a":3}` — 強化〔e="luck", t=220, a=3〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"summon","k":"golem","n":1}` — 召喚〔k="golem", n=1〕
32. `{"op":"fx","p":"portal","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="portal", n=24, at="ring", r=5.5, y=0.7〕
33. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
34. `{"op":"eff","e":"slow","t":43,"a":123}` — 敵への状態異常〔e="slow", t=43, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"buff","e":"luck","t":100,"a":123}` — 強化〔e="luck", t=100, a=123〕
37. `{"op":"fx","p":"portal","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="portal", n=16, at="ring", r=3.7, y=0.55〕
38. `{"op":"self"}` — 対象を自分へ〔〕
39. `{"op":"cleanse"}` — 状態異常解除〔〕
40. `{"op":"guard","t":100}` — 防御〔t=100〕
41. `{"op":"reflect","t":100,"r":9}` — 反射〔t=100, r=9〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 選択王権の冠 — 神格装飾品（Curios relic_charm） (`ain_sof_aur_charm`)

**現行パラメータ**：rank=1、damage登録値=69.6762、relics側CD=190tick、art側CD=190tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（13命令）**：

01. `{"op":"snapshot"}` — 状態保存〔〕
02. `{"op":"self"}` — 対象を自分へ〔〕
03. `{"op":"buff","e":"luck","t":40,"a":2}` — 強化〔e="luck", t=40, a=2〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"luck","t":45,"a":0}` — 強化〔e="luck", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
09. `{"op":"buff","e":"luck","t":45,"a":1}` — 強化〔e="luck", t=45, a=1〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"luck","t":42,"a":2}` — 強化〔e="luck", t=42, a=2〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"resist","t":48,"a":3}` — 強化〔e="resist", t=48, a=3〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（36命令）**：

01. `{"op":"fx","p":"portal","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="portal", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"portal","n":4,"at":"self","s":0.7}` — 粒子演出〔p="portal", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":40,"at":"self","s":1.4}` — 粒子演出〔p="end_rod", n=40, at="self", s=1.4〕
04. `{"op":"fx","p":"portal","n":40,"at":"self"}` — 粒子演出〔p="portal", n=40, at="self"〕
05. `{"op":"sound","s":"mirror","v":1.0,"pi":1.6}` — 効果音〔s="mirror", v=1.0, pi=1.6〕
06. `{"op":"rewind"}` — 復元〔〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"undying","t":100}` — 死亡防護〔t=100〕
09. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"luck","t":210,"a":1}` — 強化〔e="luck", t=210, a=1〕
12. `{"op":"fx","p":"portal","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="portal", n=46, at="ring", r=5.5, y=0.25〕
13. `{"op":"fx","p":"rportal","n":36,"at":"line","r":24}` — 粒子演出〔p="rportal", n=36, at="line", r=24〕
14. `{"op":"sound","s":"teleport","v":1.05,"pi":1.14}` — 効果音〔s="teleport", v=1.05, pi=1.14〕
15. `{"op":"self"}` — 対象を自分へ〔〕
16. `{"op":"guard","t":95}` — 防御〔t=95〕
17. `{"op":"self"}` — 対象を自分へ〔〕
18. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
19. `{"op":"cleanse"}` — 状態異常解除〔〕
20. `{"op":"buff","e":"luck","t":180,"a":3}` — 強化〔e="luck", t=180, a=3〕
21. `{"op":"guard","t":95}` — 防御〔t=95〕
22. `{"op":"fx","p":"portal","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="portal", n=30, at="ring", r=4.0, y=0.7〕
23. `{"op":"sound","s":"mirror","v":0.8,"pi":1.1}` — 効果音〔s="mirror", v=0.8, pi=1.1〕
24. `{"op":"self"}` — 対象を自分へ〔〕
25. `{"op":"buff","e":"luck","t":280,"a":4}` — 強化〔e="luck", t=280, a=4〕
26. `{"op":"guard","t":125}` — 防御〔t=125〕
27. `{"op":"self"}` — 対象を自分へ〔〕
28. `{"op":"reflect","t":80,"r":14}` — 反射〔t=80, r=14〕
29. `{"op":"fx","p":"portal","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="portal", n=20, at="ring", r=4, y=0.4〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"luck","t":160,"a":123}` — 強化〔e="luck", t=160, a=123〕
32. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
33. `{"op":"eff","e":"slow","t":32,"a":123}` — 敵への状態異常〔e="slow", t=32, a=123〕
34. `{"op":"self"}` — 対象を自分へ〔〕
35. `{"op":"guard","t":95}` — 防御〔t=95〕
36. `{"op":"cleanse"}` — 状態異常解除〔〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 全界選択・無限分岐の玉座 — 超越神器（武器欄） (`ain_sof_aur_legend`)

**現行パラメータ**：rank=3、damage登録値=479.75、relics側CD=345tick、art側CD=345tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:sweeping_edge:25。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"snapshot"}` — 状態保存〔〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
08. `{"op":"buff","e":"luck","t":45,"a":3}` — 強化〔e="luck", t=45, a=3〕
09. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（7命令）**：

01. `{"op":"chance","p":0.5,"ops":[{"op":"victim"},{"op":"dmg","m":1.0}]}` — 抽選〔p=0.5, ops=[{"op":"victim"},{"op":"dmg","m":1.0}]〕
02. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"glow","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"glow","t":160,"a":1}]〕
03. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"portal","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"portal","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
04. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"glow","t":135,"a":2},{"op":"fx","p":"portal","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"glow","t":135,"a":2},{"op":"fx","p":"portal","n":10,"at":"t","s":0.35}]〕
05. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
06. `{"op":"chance","p":0.375,"ops":[{"op":"victim"},{"op":"fx","p":"portal","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.375, ops=[{"op":"victim"},{"op":"fx","p":"portal","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]〕
07. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"portal","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"portal","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]〕

**権能発動時の命令（26命令）**：

01. `{"op":"fx","p":"portal","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="portal", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"portal","n":4,"at":"self","s":0.7}` — 粒子演出〔p="portal", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":40,"at":"self","s":1.4}` — 粒子演出〔p="end_rod", n=40, at="self", s=1.4〕
04. `{"op":"fx","p":"portal","n":40,"at":"self"}` — 粒子演出〔p="portal", n=40, at="self"〕
05. `{"op":"sound","s":"mirror","v":1.0,"pi":1.6}` — 効果音〔s="mirror", v=1.0, pi=1.6〕
06. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
07. `{"op":"dmg","m":3.36}` — 追加攻撃〔m=3.36〕
08. `{"op":"stun","t":105}` — 行動停止〔t=105〕
09. `{"op":"strip"}` — 強化解除〔〕
10. `{"op":"dmg","m":5.6,"magic":1}` — 追加攻撃〔m=5.6, magic=1〕
11. `{"op":"summon","k":"golem","n":5}` — 召喚〔k="golem", n=5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"undying","t":180}` — 死亡防護〔t=180〕
14. `{"op":"guard","t":100}` — 防御〔t=100〕
15. `{"op":"healpct","v":0.6}` — 最大HP割合回復〔v=0.6〕
16. `{"op":"reflect","t":400,"r":48}` — 反射〔t=400, r=48〕
17. `{"op":"fx","p":"end_rod","n":12,"at":"t","s":0.5}` — 粒子演出〔p="end_rod", n=12, at="t", s=0.5〕
18. `{"op":"area","r":26,"n":24}` — 円形対象の取得〔r=26, n=24〕
19. `{"op":"dmg","m":1.3}` — 追加攻撃〔m=1.3〕
20. `{"op":"eff","e":"nausea","t":95,"a":0}` — 敵への状態異常〔e="nausea", t=95, a=0〕
21. `{"op":"fx","p":"rportal","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="rportal", n=50, at="ring", r=8.0, y=0.6〕
22. `{"op":"fx","p":"end_rod","n":32,"at":"line","r":30}` — 粒子演出〔p="end_rod", n=32, at="line", r=30〕
23. `{"op":"sound","s":"teleport","v":1.15,"pi":0.95}` — 効果音〔s="teleport", v=1.15, pi=0.95〕
24. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.ain_sof_aur_legend.stage0","ops":[{"op":"fx","p":"portal","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"mirror","v":0.9,"pi":1.2},{"op":"fx","p":"portal","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":10},{"op":"fx","p":"portal","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"rportal","n":36,"at":"line","r":24},{"op":"sound","s":"teleport","v":1.05,"pi":1.14},{"op":"summon","k":"golem","n":4},{"op":"area","r":25.0,"n":20},{"op":"dmg","m":3.24},{"op":"self"},{"op":"buff","e":"luck","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.ain_sof_aur_legend.stage1","ops":[{"op":"fx","p":"portal","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"mirror","v":1.05,"pi":1.0},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"portal","n":6,"at":"line","r":15},{"op":"fx","p":"rportal","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"end_rod","n":32,"at":"line","r":30},{"op":"sound","s":"teleport","v":1.15,"pi":0.95},{"op":"chain","n":6,"r":20.0},{"op":"dmg","m":4.35},{"op":"self"},{"op":"guard","t":105},{"op":"area","r":18.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.ain_sof_aur_legend.stage2","ops":[{"op":"fx","p":"portal","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"mirror","v":1.25,"pi":0.75},{"op":"fx","p":"end_rod","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"portal","n":10,"at":"line","r":20},{"op":"fx","p":"portal","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"rportal","n":48,"at":"line","r":48},{"op":"fx","p":"end_rod","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"teleport","v":1.5,"pi":0.75},{"op":"area","r":38.0,"n":30},{"op":"dmg","m":10.044},{"op":"summon","k":"golem","n":5},{"op":"strip"},{"op":"self"},{"op":"healpct","v":0.45},{"op":"fx","p":"end_rod","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"portal","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":36.0,"n":32},{"op":"dmg","m":2.9},{"op":"summon","k":"golem","n":4},{"op":"self"},{"op":"healpct","v":0.45},{"op":"area","r":27.0,"n":16},{"op":"dmg","m":1.1},{"op":"eff","e":"slow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"luck","t":240,"a":4},{"op":"self"},{"op":"summon","k":"golem","n":2},{"op":"fx","p":"portal","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"mirror","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"self"},{"op":"cleanse"},{"op":"guard","t":105},{"op":"area","r":17,"n":8},{"op":"strip"}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.ain_sof_aur_legend.stage0","ops":[{"op":"fx","p":"portal","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"mirror","v":0.9,"pi":1.2},{"op":"fx","p":"portal","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":10},{"op":"fx","p":"portal","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"rportal","n":36,"at":"line","r":24},{"op":"sound","s":"teleport","v":1.05,"pi":1.14},{"op":"summon","k":"golem","n":4},{"op":"area","r":25.0,"n":20},{"op":"dmg","m":3.24},{"op":"self"},{"op":"buff","e":"luck","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.ain_sof_aur_legend.stage1","ops":[{"op":"fx","p":"portal","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"mirror","v":1.05,"pi":1.0},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"portal","n":6,"at":"line","r":15},{"op":"fx","p":"rportal","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"end_rod","n":32,"at":"line","r":30},{"op":"sound","s":"teleport","v":1.15,"pi":0.95},{"op":"chain","n":6,"r":20.0},{"op":"dmg","m":4.35},{"op":"self"},{"op":"guard","t":105},{"op":"area","r":18.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.ain_sof_aur_legend.stage2","ops":[{"op":"fx","p":"portal","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"mirror","v":1.25,"pi":0.75},{"op":"fx","p":"end_rod","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"portal","n":10,"at":"line","r":20},{"op":"fx","p":"portal","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"rportal","n":48,"at":"line","r":48},{"op":"fx","p":"end_rod","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"teleport","v":1.5,"pi":0.75},{"op":"area","r":38.0,"n":30},{"op":"dmg","m":10.044},{"op":"summon","k":"golem","n":5},{"op":"strip"},{"op":"self"},{"op":"healpct","v":0.45},{"op":"fx","p":"end_rod","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"portal","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":36.0,"n":32},{"op":"dmg","m":2.9},{"op":"summon","k":"golem","n":4},{"op":"self"},{"op":"healpct","v":0.45},{"op":"area","r":27.0,"n":16},{"op":"dmg","m":1.1},{"op":"eff","e":"slow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"luck","t":240,"a":4},{"op":"self"},{"op":"summon","k":"golem","n":2},{"op":"fx","p":"portal","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"mirror","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"self"},{"op":"cleanse"},{"op":"guard","t":105},{"op":"area","r":17,"n":8},{"op":"strip"}]}]〕
25. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
26. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 30. 全害惡徳 アンラマンユ

**モブ側の動きの方向性**：黒い罪業を吸い取り、影の翼と鎖へ変えて仲間を庇う。。

### 全害惡徳の影鎖鎌 — 討伐武器（メイン／武器欄） (`angra_mainyu_weapon`)

**現行パラメータ**：rank=1、damage登録値=328.5、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12。

**装備中の常時命令（5命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"night","t":300,"a":0}` — 強化〔e="night", t=300, a=0〕
03. `{"op":"buff","e":"regen","t":40,"a":0}` — 強化〔e="regen", t=40, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（10命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"eff","e":"wither","t":80,"a":2}` — 敵への状態異常〔e="wither", t=80, a=2〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"heal","v":4}` — heal〔v=4〕
05. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"wither","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"wither","t":90,"a":0}]〕
06. `{"op":"chance","p":0.5,"ops":[{"op":"victim"},{"op":"fx","p":"soul","n":17,"at":"t","s":0.24},{"op":"mark","t":200,"x":2.21},{"op":"eff","e":"wither","t":115,"a":0}]}` — 抽選〔p=0.5, ops=[{"op":"victim"},{"op":"fx","p":"soul","n":17,"at":"t","s":0.24},{"op":"mark","t":200,"x":2.21},{"op":"eff","e":"wither","t":115,"a":0}]〕
07. `{"op":"chance","p":0.258,"ops":[{"op":"victim"},{"op":"dmg","m":0.34}]}` — 抽選〔p=0.258, ops=[{"op":"victim"},{"op":"dmg","m":0.34}]〕
08. `{"op":"chance","p":0.104,"ops":[{"op":"victim"},{"op":"fx","p":"soul","n":8,"at":"t","s":0.25},{"op":"self"},{"op":"healpct","v":0.045}]}` — 抽選〔p=0.104, ops=[{"op":"victim"},{"op":"fx","p":"soul","n":8,"at":"t","s":0.25},{"op":"self"},{"op":"healpct","v":0.045}]〕
09. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"fx","p":"soul","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"fx","p":"soul","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]〕
10. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"soul","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"soul","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]〕

**権能発動時の命令（27命令）**：

01. `{"op":"fx","p":"soul","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="soul", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"soul","n":4,"at":"self","s":0.7}` — 粒子演出〔p="soul", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"sculk","n":40,"at":"self"}` — 粒子演出〔p="sculk", n=40, at="self"〕
04. `{"op":"fx","p":"bigsmoke","n":20,"at":"self"}` — 粒子演出〔p="bigsmoke", n=20, at="self"〕
05. `{"op":"sound","s":"wither","v":0.8,"pi":0.6}` — 効果音〔s="wither", v=0.8, pi=0.6〕
06. `{"op":"chain","n":8,"r":12}` — chain〔n=8, r=12〕
07. `{"op":"pull","f":2.0}` — pull〔f=2.0〕
08. `{"op":"dmg","m":1.44}` — 追加攻撃〔m=1.44〕
09. `{"op":"eff","e":"wither","t":300,"a":4}` — 敵への状態異常〔e="wither", t=300, a=4〕
10. `{"op":"eff","e":"weakness","t":300,"a":4}` — 敵への状態異常〔e="weakness", t=300, a=4〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"healpct","v":0.25}` — 最大HP割合回復〔v=0.25〕
13. `{"op":"fx","p":"sculk","n":12,"at":"t","s":0.5}` — 粒子演出〔p="sculk", n=12, at="t", s=0.5〕
14. `{"op":"fx","p":"soul","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="soul", n=46, at="ring", r=5.5, y=0.25〕
15. `{"op":"fx","p":"witch","n":36,"at":"line","r":24}` — 粒子演出〔p="witch", n=36, at="line", r=24〕
16. `{"op":"area","r":25.0,"n":20}` — 円形対象の取得〔r=25.0, n=20〕
17. `{"op":"eff","e":"wither","t":125,"a":2}` — 敵への状態異常〔e="wither", t=125, a=2〕
18. `{"op":"dmg","m":2.6}` — 追加攻撃〔m=2.6〕
19. `{"op":"fx","p":"soul","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="soul", n=16, at="ring", r=5.0〕
20. `{"op":"sound","s":"spell","v":0.75,"pi":1.15}` — 効果音〔s="spell", v=0.75, pi=1.15〕
21. `{"op":"chain","n":4,"r":12}` — chain〔n=4, r=12〕
22. `{"op":"dmg","m":1.0}` — 追加攻撃〔m=1.0〕
23. `{"op":"eff","e":"wither","t":65,"a":0}` — 敵への状態異常〔e="wither", t=65, a=0〕
24. `{"op":"fx","p":"soul","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="soul", n=24, at="ring", r=4.5, y=0.6〕
25. `{"op":"sound","s":"wither","v":0.8,"pi":0.8}` — 効果音〔s="wither", v=0.8, pi=0.8〕
26. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
27. `{"op":"eff","e":"weakness","t":100,"a":124}` — 敵への状態異常〔e="weakness", t=100, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 悪意結晶の黒杯 — 神威触媒（Curios relic_focus） (`angra_mainyu_focus`)

**現行パラメータ**：rank=2、damage登録値=69.6762、relics側CD=155tick、art側CD=155tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"area","r":6,"n":36}` — 円形対象の取得〔r=6, n=36〕
02. `{"op":"eff","e":"weakness","t":40,"a":0}` — 敵への状態異常〔e="weakness", t=40, a=0〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"resist","t":45,"a":0}` — 強化〔e="resist", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"regen","t":42,"a":2}` — 強化〔e="regen", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（45命令）**：

01. `{"op":"fx","p":"soul","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="soul", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"soul","n":6,"at":"self","s":0.7}` — 粒子演出〔p="soul", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"sculk","n":40,"at":"self"}` — 粒子演出〔p="sculk", n=40, at="self"〕
04. `{"op":"fx","p":"bigsmoke","n":20,"at":"self"}` — 粒子演出〔p="bigsmoke", n=20, at="self"〕
05. `{"op":"sound","s":"wither","v":0.8,"pi":0.6}` — 効果音〔s="wither", v=0.8, pi=0.6〕
06. `{"op":"area","r":24,"n":36}` — 円形対象の取得〔r=24, n=36〕
07. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
08. `{"op":"eff","e":"weakness","t":600,"a":6}` — 敵への状態異常〔e="weakness", t=600, a=6〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"healpct","v":0.4}` — 最大HP割合回復〔v=0.4〕
11. `{"op":"buff","e":"absorb","t":600,"a":6}` — 強化〔e="absorb", t=600, a=6〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"resist","t":150,"a":1}` — 強化〔e="resist", t=150, a=1〕
15. `{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="witch", n=50, at="ring", r=8.0, y=0.6〕
16. `{"op":"fx","p":"ash","n":32,"at":"line","r":30}` — 粒子演出〔p="ash", n=32, at="line", r=30〕
17. `{"op":"sound","s":"wither","v":1.15,"pi":0.95}` — 効果音〔s="wither", v=1.15, pi=0.95〕
18. `{"op":"area","r":26.0,"n":20}` — 円形対象の取得〔r=26.0, n=20〕
19. `{"op":"strip"}` — 強化解除〔〕
20. `{"op":"pull","f":1.9}` — pull〔f=1.9〕
21. `{"op":"dmg","m":2.7}` — 追加攻撃〔m=2.7〕
22. `{"op":"allies","r":24.0}` — 味方対象〔r=24.0〕
23. `{"op":"cleanse"}` — 状態異常解除〔〕
24. `{"op":"self"}` — 対象を自分へ〔〕
25. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
26. `{"op":"buff","e":"regen","t":150,"a":3}` — 強化〔e="regen", t=150, a=3〕
27. `{"op":"fx","p":"soul","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="soul", n=24, at="ring", r=12, y=0.5〕
28. `{"op":"sound","s":"wither","v":0.85,"pi":1.18}` — 効果音〔s="wither", v=0.85, pi=1.18〕
29. `{"op":"allies","r":26.0}` — 味方対象〔r=26.0〕
30. `{"op":"healpct","v":0.14,"to":1}` — 最大HP割合回復〔v=0.14, to=1〕
31. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"buff","e":"regen","t":240,"a":3}` — 強化〔e="regen", t=240, a=3〕
34. `{"op":"self"}` — 対象を自分へ〔〕
35. `{"op":"buff","e":"resist","t":240,"a":2}` — 強化〔e="resist", t=240, a=2〕
36. `{"op":"fx","p":"soul","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="soul", n=24, at="ring", r=5.5, y=0.7〕
37. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
38. `{"op":"eff","e":"weakness","t":135,"a":123}` — 敵への状態異常〔e="weakness", t=135, a=123〕
39. `{"op":"self"}` — 対象を自分へ〔〕
40. `{"op":"buff","e":"regen","t":140,"a":7}` — 強化〔e="regen", t=140, a=7〕
41. `{"op":"fx","p":"soul","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="soul", n=16, at="ring", r=3.7, y=0.55〕
42. `{"op":"allies","r":18.0}` — 味方対象〔r=18.0〕
43. `{"op":"healpct","v":0.24}` — 最大HP割合回復〔v=0.24〕
44. `{"op":"cleanse"}` — 状態異常解除〔〕
45. `{"op":"buff","e":"regen","t":130,"a":3}` — 強化〔e="regen", t=130, a=3〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 闇を抱く王環 — 神格装飾品（Curios relic_charm） (`angra_mainyu_charm`)

**現行パラメータ**：rank=1、damage登録値=69.6762、relics側CD=185tick、art側CD=185tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（12命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"night","t":300,"a":0}` — 強化〔e="night", t=300, a=0〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"resist","t":45,"a":0}` — 強化〔e="resist", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"regen","t":42,"a":2}` — 強化〔e="regen", t=42, a=2〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"regen","t":48,"a":5}` — 強化〔e="regen", t=48, a=5〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（40命令）**：

01. `{"op":"fx","p":"soul","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="soul", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"soul","n":4,"at":"self","s":0.7}` — 粒子演出〔p="soul", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"sculk","n":40,"at":"self"}` — 粒子演出〔p="sculk", n=40, at="self"〕
04. `{"op":"fx","p":"bigsmoke","n":20,"at":"self"}` — 粒子演出〔p="bigsmoke", n=20, at="self"〕
05. `{"op":"sound","s":"wither","v":0.8,"pi":0.6}` — 効果音〔s="wither", v=0.8, pi=0.6〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"invis","t":300,"a":0}` — 強化〔e="invis", t=300, a=0〕
08. `{"op":"guard","t":40}` — 防御〔t=40〕
09. `{"op":"cleanse"}` — 状態異常解除〔〕
10. `{"op":"area","r":16,"n":36}` — 円形対象の取得〔r=16, n=36〕
11. `{"op":"eff","e":"dark","t":300,"a":0}` — 敵への状態異常〔e="dark", t=300, a=0〕
12. `{"op":"eff","e":"blind","t":200,"a":0}` — 敵への状態異常〔e="blind", t=200, a=0〕
13. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
14. `{"op":"self"}` — 対象を自分へ〔〕
15. `{"op":"buff","e":"resist","t":210,"a":1}` — 強化〔e="resist", t=210, a=1〕
16. `{"op":"fx","p":"soul","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="soul", n=46, at="ring", r=5.5, y=0.25〕
17. `{"op":"fx","p":"witch","n":36,"at":"line","r":24}` — 粒子演出〔p="witch", n=36, at="line", r=24〕
18. `{"op":"sound","s":"wither","v":1.05,"pi":1.14}` — 効果音〔s="wither", v=1.05, pi=1.14〕
19. `{"op":"self"}` — 対象を自分へ〔〕
20. `{"op":"guard","t":95}` — 防御〔t=95〕
21. `{"op":"self"}` — 対象を自分へ〔〕
22. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
23. `{"op":"cleanse"}` — 状態異常解除〔〕
24. `{"op":"buff","e":"regen","t":180,"a":3}` — 強化〔e="regen", t=180, a=3〕
25. `{"op":"guard","t":95}` — 防御〔t=95〕
26. `{"op":"fx","p":"soul","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="soul", n=30, at="ring", r=4.0, y=0.7〕
27. `{"op":"sound","s":"wither","v":0.8,"pi":1.1}` — 効果音〔s="wither", v=0.8, pi=1.1〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"buff","e":"regen","t":300,"a":4}` — 強化〔e="regen", t=300, a=4〕
30. `{"op":"guard","t":140}` — 防御〔t=140〕
31. `{"op":"allies","r":24.0}` — 味方対象〔r=24.0〕
32. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
33. `{"op":"fx","p":"soul","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="soul", n=20, at="ring", r=4, y=0.4〕
34. `{"op":"self"}` — 対象を自分へ〔〕
35. `{"op":"buff","e":"regen","t":140,"a":7}` — 強化〔e="regen", t=140, a=7〕
36. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
37. `{"op":"eff","e":"weakness","t":100,"a":123}` — 敵への状態異常〔e="weakness", t=100, a=123〕
38. `{"op":"allies","r":16}` — 味方対象〔r=16〕
39. `{"op":"healpct","v":0.18}` — 最大HP割合回復〔v=0.18〕
40. `{"op":"cleanse"}` — 状態異常解除〔〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 世界悪核・全害の王権 — 超越神器（武器欄） (`angra_mainyu_legend`)

**現行パラメータ**：rank=3、damage登録値=578.1875、relics側CD=340tick、art側CD=340tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"area","r":8,"n":36}` — 円形対象の取得〔r=8, n=36〕
06. `{"op":"eff","e":"wither","t":40,"a":2}` — 敵への状態異常〔e="wither", t=40, a=2〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
09. `{"op":"buff","e":"regen","t":45,"a":3}` — 強化〔e="regen", t=45, a=3〕
10. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（10命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"eff","e":"wither","t":200,"a":4}` — 敵への状態異常〔e="wither", t=200, a=4〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"heal","v":10}` — heal〔v=10〕
05. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"wither","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"wither","t":160,"a":1}]〕
06. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"soul","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"soul","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
07. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"wither","t":135,"a":2},{"op":"fx","p":"soul","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"wither","t":135,"a":2},{"op":"fx","p":"soul","n":10,"at":"t","s":0.35}]〕
08. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
09. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"fx","p":"soul","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"fx","p":"soul","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]〕
10. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"soul","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"soul","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]〕

**権能発動時の命令（26命令）**：

01. `{"op":"fx","p":"soul","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="soul", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"soul","n":4,"at":"self","s":0.7}` — 粒子演出〔p="soul", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"sculk","n":40,"at":"self"}` — 粒子演出〔p="sculk", n=40, at="self"〕
04. `{"op":"fx","p":"bigsmoke","n":20,"at":"self"}` — 粒子演出〔p="bigsmoke", n=20, at="self"〕
05. `{"op":"sound","s":"wither","v":0.8,"pi":0.6}` — 効果音〔s="wither", v=0.8, pi=0.6〕
06. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
07. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
08. `{"op":"eff","e":"wither","t":1200,"a":9}` — 敵への状態異常〔e="wither", t=1200, a=9〕
09. `{"op":"eff","e":"weakness","t":1200,"a":9}` — 敵への状態異常〔e="weakness", t=1200, a=9〕
10. `{"op":"eff","e":"dark","t":600,"a":0}` — 敵への状態異常〔e="dark", t=600, a=0〕
11. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
12. `{"op":"dmg","m":5.6,"magic":1}` — 追加攻撃〔m=5.6, magic=1〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"healpct","v":0.6}` — 最大HP割合回復〔v=0.6〕
15. `{"op":"buff","e":"absorb","t":1200,"a":9}` — 強化〔e="absorb", t=1200, a=9〕
16. `{"op":"fx","p":"sculk","n":12,"at":"t","s":0.5}` — 粒子演出〔p="sculk", n=12, at="t", s=0.5〕
17. `{"op":"area","r":30,"n":24}` — 円形対象の取得〔r=30, n=24〕
18. `{"op":"strip"}` — 強化解除〔〕
19. `{"op":"eff","e":"wither","t":160,"a":1}` — 敵への状態異常〔e="wither", t=160, a=1〕
20. `{"op":"dmg","m":1.2}` — 追加攻撃〔m=1.2〕
21. `{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="witch", n=50, at="ring", r=8.0, y=0.6〕
22. `{"op":"fx","p":"ash","n":32,"at":"line","r":30}` — 粒子演出〔p="ash", n=32, at="line", r=30〕
23. `{"op":"sound","s":"wither","v":1.15,"pi":0.95}` — 効果音〔s="wither", v=1.15, pi=0.95〕
24. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.angra_mainyu_legend.stage0","ops":[{"op":"fx","p":"soul","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"wither","v":0.9,"pi":1.2},{"op":"fx","p":"soul","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"sculk","n":6,"at":"line","r":10},{"op":"fx","p":"soul","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"witch","n":36,"at":"line","r":24},{"op":"sound","s":"wither","v":1.05,"pi":1.14},{"op":"area","r":25.0,"n":20},{"op":"eff","e":"wither","t":125,"a":2},{"op":"dmg","m":3.51},{"op":"self"},{"op":"buff","e":"regen","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.angra_mainyu_legend.stage1","ops":[{"op":"fx","p":"soul","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"wither","v":1.05,"pi":1.0},{"op":"fx","p":"sculk","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"soul","n":6,"at":"line","r":15},{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"ash","n":32,"at":"line","r":30},{"op":"sound","s":"wither","v":1.15,"pi":0.95},{"op":"area","r":26.0,"n":20},{"op":"strip"},{"op":"pull","f":1.9},{"op":"dmg","m":3.915},{"op":"allies","r":24.0},{"op":"cleanse"},{"op":"area","r":20.0,"n":10},{"op":"eff","e":"weakness","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.angra_mainyu_legend.stage2","ops":[{"op":"fx","p":"soul","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"wither","v":1.25,"pi":0.75},{"op":"fx","p":"sculk","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"soul","n":10,"at":"line","r":20},{"op":"fx","p":"soul","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"witch","n":48,"at":"line","r":48},{"op":"fx","p":"ash","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"wither","v":1.5,"pi":0.75},{"op":"area","r":36.0,"n":28},{"op":"dmg","m":9.72},{"op":"eff","e":"wither","t":155,"a":3},{"op":"allies","r":30.0},{"op":"healpct","v":0.4},{"op":"cleanse"},{"op":"fx","p":"ash","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"soul","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":32.0,"n":28},{"op":"dmg","m":2.8},{"op":"eff","e":"wither","t":180,"a":3},{"op":"allies","r":30.0},{"op":"cleanse"},{"op":"self"},{"op":"healpct","v":0.45},{"op":"allies","r":40.0},{"op":"healpct","v":0.28,"to":1},{"op":"cleanse","to":1},{"op":"self"},{"op":"guard","t":180},{"op":"allies","r":26.0},{"op":"healpct","v":0.14,"to":1},{"op":"fx","p":"soul","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"wither","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"allies","r":22},{"op":"healpct","v":0.24},{"op":"cleanse"},{"op":"guard","t":110}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.angra_mainyu_legend.stage0","ops":[{"op":"fx","p":"soul","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"wither","v":0.9,"pi":1.2},{"op":"fx","p":"soul","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"sculk","n":6,"at":"line","r":10},{"op":"fx","p":"soul","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"witch","n":36,"at":"line","r":24},{"op":"sound","s":"wither","v":1.05,"pi":1.14},{"op":"area","r":25.0,"n":20},{"op":"eff","e":"wither","t":125,"a":2},{"op":"dmg","m":3.51},{"op":"self"},{"op":"buff","e":"regen","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.angra_mainyu_legend.stage1","ops":[{"op":"fx","p":"soul","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"wither","v":1.05,"pi":1.0},{"op":"fx","p":"sculk","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"soul","n":6,"at":"line","r":15},{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"ash","n":32,"at":"line","r":30},{"op":"sound","s":"wither","v":1.15,"pi":0.95},{"op":"area","r":26.0,"n":20},{"op":"strip"},{"op":"pull","f":1.9},{"op":"dmg","m":3.915},{"op":"allies","r":24.0},{"op":"cleanse"},{"op":"area","r":20.0,"n":10},{"op":"eff","e":"weakness","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.angra_mainyu_legend.stage2","ops":[{"op":"fx","p":"soul","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"wither","v":1.25,"pi":0.75},{"op":"fx","p":"sculk","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"soul","n":10,"at":"line","r":20},{"op":"fx","p":"soul","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"witch","n":48,"at":"line","r":48},{"op":"fx","p":"ash","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"wither","v":1.5,"pi":0.75},{"op":"area","r":36.0,"n":28},{"op":"dmg","m":9.72},{"op":"eff","e":"wither","t":155,"a":3},{"op":"allies","r":30.0},{"op":"healpct","v":0.4},{"op":"cleanse"},{"op":"fx","p":"ash","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"soul","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":32.0,"n":28},{"op":"dmg","m":2.8},{"op":"eff","e":"wither","t":180,"a":3},{"op":"allies","r":30.0},{"op":"cleanse"},{"op":"self"},{"op":"healpct","v":0.45},{"op":"allies","r":40.0},{"op":"healpct","v":0.28,"to":1},{"op":"cleanse","to":1},{"op":"self"},{"op":"guard","t":180},{"op":"allies","r":26.0},{"op":"healpct","v":0.14,"to":1},{"op":"fx","p":"soul","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"wither","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"allies","r":22},{"op":"healpct","v":0.24},{"op":"cleanse"},{"op":"guard","t":110}]}]〕
25. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
26. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 31. 始源母胎 マグナ・マーテル

**モブ側の動きの方向性**：生命の脈動、組織の成長、繭からの誕生を段階的に描く。。

### 命を継ぐ蔓鞭 — 討伐武器（メイン／武器欄） (`magna_mater_weapon`)

**現行パラメータ**：rank=1、damage登録値=313.91667、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12。

**装備中の常時命令（4命令）**：

01. `{"op":"allies","r":10}` — 味方対象〔r=10〕
02. `{"op":"buff","e":"regen","t":40,"a":0,"to":1}` — 強化〔e="regen", t=40, a=0, to=1〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（9命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"stun","t":20}` — 行動停止〔t=20〕
03. `{"op":"eff","e":"slow","t":60,"a":2}` — 敵への状態異常〔e="slow", t=60, a=2〕
04. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"poison","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"poison","t":90,"a":0}]〕
05. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"fx","p":"happy","n":9,"at":"t","s":0.24},{"op":"mark","t":120,"x":1.65},{"op":"eff","e":"slow","t":55,"a":0}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"fx","p":"happy","n":9,"at":"t","s":0.24},{"op":"mark","t":120,"x":1.65},{"op":"eff","e":"slow","t":55,"a":0}]〕
06. `{"op":"chance","p":0.15,"ops":[{"op":"victim"},{"op":"dmg","m":0.2}]}` — 抽選〔p=0.15, ops=[{"op":"victim"},{"op":"dmg","m":0.2}]〕
07. `{"op":"chance","p":0.123,"ops":[{"op":"victim"},{"op":"fx","p":"happy","n":8,"at":"t","s":0.25},{"op":"self"},{"op":"healpct","v":0.04}]}` — 抽選〔p=0.123, ops=[{"op":"victim"},{"op":"fx","p":"happy","n":8,"at":"t","s":0.25},{"op":"self"},{"op":"healpct","v":0.04}]〕
08. `{"op":"chance","p":0.18,"ops":[{"op":"victim"},{"op":"fx","p":"happy","n":14,"at":"t","s":0.28},{"op":"eff","e":"poison","t":38,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.18, ops=[{"op":"victim"},{"op":"fx","p":"happy","n":14,"at":"t","s":0.28},{"op":"eff","e":"poison","t":38,"a":124},{"op":"mark","t":100,"x":2.15}]〕
09. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"compost","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"compost","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]〕

**権能発動時の命令（27命令）**：

01. `{"op":"fx","p":"heart","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="heart", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"heart","n":4,"at":"self","s":0.7}` — 粒子演出〔p="heart", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"happy","n":50,"at":"self","s":1.6}` — 粒子演出〔p="happy", n=50, at="self", s=1.6〕
04. `{"op":"fx","p":"compost","n":30,"at":"self"}` — 粒子演出〔p="compost", n=30, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":1.0}` — 効果音〔s="chime", v=1.0, pi=1.0〕
06. `{"op":"line","r":20,"w":3}` — 線分対象の取得〔r=20, w=3〕
07. `{"op":"pull","f":2.5}` — pull〔f=2.5〕
08. `{"op":"stun","t":65}` — 行動停止〔t=65〕
09. `{"op":"dmg","m":1.44}` — 追加攻撃〔m=1.44〕
10. `{"op":"allies","r":20}` — 味方対象〔r=20〕
11. `{"op":"healpct","v":0.25,"to":1}` — 最大HP割合回復〔v=0.25, to=1〕
12. `{"op":"summon","k":"wolf","n":2}` — 召喚〔k="wolf", n=2〕
13. `{"op":"fx","p":"happy","n":12,"at":"t","s":0.5}` — 粒子演出〔p="happy", n=12, at="t", s=0.5〕
14. `{"op":"fx","p":"heart","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="heart", n=46, at="ring", r=5.5, y=0.25〕
15. `{"op":"fx","p":"compost","n":36,"at":"line","r":24}` — 粒子演出〔p="compost", n=36, at="line", r=24〕
16. `{"op":"line","r":58.0,"w":5.0}` — 線分対象の取得〔r=58.0, w=5.0〕
17. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
18. `{"op":"eff","e":"poison","t":100,"a":1}` — 敵への状態異常〔e="poison", t=100, a=1〕
19. `{"op":"fx","p":"happy","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="happy", n=16, at="ring", r=5.0〕
20. `{"op":"sound","s":"sonic","v":0.75,"pi":1.15}` — 効果音〔s="sonic", v=0.75, pi=1.15〕
21. `{"op":"line","r":18,"w":2}` — 線分対象の取得〔r=18, w=2〕
22. `{"op":"dmg","m":1.05}` — 追加攻撃〔m=1.05〕
23. `{"op":"eff","e":"slow","t":65,"a":0}` — 敵への状態異常〔e="slow", t=65, a=0〕
24. `{"op":"fx","p":"happy","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="happy", n=24, at="ring", r=4.5, y=0.6〕
25. `{"op":"sound","s":"totem","v":0.8,"pi":0.8}` — 効果音〔s="totem", v=0.8, pi=0.8〕
26. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
27. `{"op":"eff","e":"poison","t":38,"a":124}` — 敵への状態異常〔e="poison", t=38, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 始源生命の種杖 — 神威触媒（Curios relic_focus） (`magna_mater_focus`)

**現行パラメータ**：rank=2、damage登録値=68.31、relics側CD=150tick、art側CD=150tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"allies","r":16}` — 味方対象〔r=16〕
02. `{"op":"buff","e":"regen","t":40,"a":0,"to":1}` — 強化〔e="regen", t=40, a=0, to=1〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"regen","t":45,"a":0}` — 強化〔e="regen", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"regen","t":42,"a":2}` — 強化〔e="regen", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（42命令）**：

01. `{"op":"fx","p":"heart","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="heart", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"heart","n":6,"at":"self","s":0.7}` — 粒子演出〔p="heart", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"happy","n":50,"at":"self","s":1.6}` — 粒子演出〔p="happy", n=50, at="self", s=1.6〕
04. `{"op":"fx","p":"compost","n":30,"at":"self"}` — 粒子演出〔p="compost", n=30, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":1.0}` — 効果音〔s="chime", v=1.0, pi=1.0〕
06. `{"op":"summon","k":"wolf","n":4}` — 召喚〔k="wolf", n=4〕
07. `{"op":"summon","k":"golem","n":2}` — 召喚〔k="golem", n=2〕
08. `{"op":"allies","r":32}` — 味方対象〔r=32〕
09. `{"op":"healpct","v":0.4,"to":1}` — 最大HP割合回復〔v=0.4, to=1〕
10. `{"op":"buff","e":"regen","t":600,"a":3,"to":1}` — 強化〔e="regen", t=600, a=3, to=1〕
11. `{"op":"buff","e":"health","t":1200,"a":3,"to":1}` — 強化〔e="health", t=1200, a=3, to=1〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"regen","t":150,"a":1}` — 強化〔e="regen", t=150, a=1〕
15. `{"op":"fx","p":"compost","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="compost", n=50, at="ring", r=8.0, y=0.6〕
16. `{"op":"fx","p":"happy","n":32,"at":"line","r":30}` — 粒子演出〔p="happy", n=32, at="line", r=30〕
17. `{"op":"sound","s":"summon","v":1.15,"pi":0.95}` — 効果音〔s="summon", v=1.15, pi=0.95〕
18. `{"op":"summon","k":"golem","n":4}` — 召喚〔k="golem", n=4〕
19. `{"op":"allies","r":25.0}` — 味方対象〔r=25.0〕
20. `{"op":"healpct","v":0.35}` — 最大HP割合回復〔v=0.35〕
21. `{"op":"self"}` — 対象を自分へ〔〕
22. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
23. `{"op":"buff","e":"regen","t":150,"a":3}` — 強化〔e="regen", t=150, a=3〕
24. `{"op":"fx","p":"happy","n":24,"at":"ring","r":10,"y":0.5}` — 粒子演出〔p="happy", n=24, at="ring", r=10, y=0.5〕
25. `{"op":"sound","s":"totem","v":0.85,"pi":0.9}` — 効果音〔s="totem", v=0.85, pi=0.9〕
26. `{"op":"allies","r":18.0}` — 味方対象〔r=18.0〕
27. `{"op":"healpct","v":0.14,"to":1}` — 最大HP割合回復〔v=0.14, to=1〕
28. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
29. `{"op":"self"}` — 対象を自分へ〔〕
30. `{"op":"buff","e":"regen","t":200,"a":3}` — 強化〔e="regen", t=200, a=3〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"summon","k":"wolf","n":2}` — 召喚〔k="wolf", n=2〕
33. `{"op":"fx","p":"happy","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="happy", n=24, at="ring", r=5.5, y=0.7〕
34. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
35. `{"op":"eff","e":"poison","t":51,"a":123}` — 敵への状態異常〔e="poison", t=51, a=123〕
36. `{"op":"self"}` — 対象を自分へ〔〕
37. `{"op":"buff","e":"regen","t":140,"a":7}` — 強化〔e="regen", t=140, a=7〕
38. `{"op":"fx","p":"compost","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="compost", n=16, at="ring", r=3.7, y=0.55〕
39. `{"op":"allies","r":18.0}` — 味方対象〔r=18.0〕
40. `{"op":"healpct","v":0.24}` — 最大HP割合回復〔v=0.24〕
41. `{"op":"cleanse"}` — 状態異常解除〔〕
42. `{"op":"buff","e":"regen","t":130,"a":3}` — 強化〔e="regen", t=130, a=3〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 万命慈愛の母環 — 神格装飾品（Curios relic_charm） (`magna_mater_charm`)

**現行パラメータ**：rank=1、damage登録値=68.31、relics側CD=180tick、art側CD=180tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（13命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
03. `{"op":"buff","e":"saturation","t":40,"a":0}` — 強化〔e="saturation", t=40, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"regen","t":45,"a":0}` — 強化〔e="regen", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
09. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"regen","t":42,"a":2}` — 強化〔e="regen", t=42, a=2〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"regen","t":48,"a":5}` — 強化〔e="regen", t=48, a=5〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（39命令）**：

01. `{"op":"fx","p":"heart","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="heart", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"heart","n":4,"at":"self","s":0.7}` — 粒子演出〔p="heart", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"happy","n":50,"at":"self","s":1.6}` — 粒子演出〔p="happy", n=50, at="self", s=1.6〕
04. `{"op":"fx","p":"compost","n":30,"at":"self"}` — 粒子演出〔p="compost", n=30, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":1.0}` — 効果音〔s="chime", v=1.0, pi=1.0〕
06. `{"op":"allies","r":24}` — 味方対象〔r=24〕
07. `{"op":"healpct","v":0.25,"to":1}` — 最大HP割合回復〔v=0.25, to=1〕
08. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
09. `{"op":"guard","t":60,"to":1}` — 防御〔t=60, to=1〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"food"}` — food〔〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"regen","t":210,"a":1}` — 強化〔e="regen", t=210, a=1〕
15. `{"op":"fx","p":"heart","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="heart", n=46, at="ring", r=5.5, y=0.25〕
16. `{"op":"fx","p":"compost","n":36,"at":"line","r":24}` — 粒子演出〔p="compost", n=36, at="line", r=24〕
17. `{"op":"sound","s":"summon","v":1.05,"pi":1.14}` — 効果音〔s="summon", v=1.05, pi=1.14〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"guard","t":95}` — 防御〔t=95〕
20. `{"op":"self"}` — 対象を自分へ〔〕
21. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
22. `{"op":"cleanse"}` — 状態異常解除〔〕
23. `{"op":"buff","e":"regen","t":180,"a":3}` — 強化〔e="regen", t=180, a=3〕
24. `{"op":"guard","t":95}` — 防御〔t=95〕
25. `{"op":"fx","p":"happy","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="happy", n=30, at="ring", r=4.0, y=0.7〕
26. `{"op":"sound","s":"totem","v":0.8,"pi":1.1}` — 効果音〔s="totem", v=0.8, pi=1.1〕
27. `{"op":"self"}` — 対象を自分へ〔〕
28. `{"op":"buff","e":"regen","t":260,"a":4}` — 強化〔e="regen", t=260, a=4〕
29. `{"op":"guard","t":155}` — 防御〔t=155〕
30. `{"op":"allies","r":28.0}` — 味方対象〔r=28.0〕
31. `{"op":"healpct","v":0.14,"to":1}` — 最大HP割合回復〔v=0.14, to=1〕
32. `{"op":"fx","p":"happy","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="happy", n=20, at="ring", r=4, y=0.4〕
33. `{"op":"self"}` — 対象を自分へ〔〕
34. `{"op":"buff","e":"regen","t":140,"a":7}` — 強化〔e="regen", t=140, a=7〕
35. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
36. `{"op":"eff","e":"poison","t":38,"a":123}` — 敵への状態異常〔e="poison", t=38, a=123〕
37. `{"op":"allies","r":16}` — 味方対象〔r=16〕
38. `{"op":"healpct","v":0.18}` — 最大HP割合回復〔v=0.18〕
39. `{"op":"cleanse"}` — 状態異常解除〔〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 始源創命・無窮の母胎 — 超越神器（武器欄） (`magna_mater_legend`)

**現行パラメータ**：rank=3、damage登録値=578.1875、relics側CD=335tick、art側CD=335tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"allies","r":16}` — 味方対象〔r=16〕
06. `{"op":"buff","e":"regen","t":40,"a":1,"to":1}` — 強化〔e="regen", t=40, a=1, to=1〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
09. `{"op":"buff","e":"regen","t":45,"a":3}` — 強化〔e="regen", t=45, a=3〕
10. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（8命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"stun","t":30}` — 行動停止〔t=30〕
03. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"poison","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"poison","t":160,"a":1}]〕
04. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"heart","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"heart","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
05. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"poison","t":135,"a":2},{"op":"fx","p":"compost","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"poison","t":135,"a":2},{"op":"fx","p":"compost","n":10,"at":"t","s":0.35}]〕
06. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
07. `{"op":"chance","p":0.3,"ops":[{"op":"victim"},{"op":"fx","p":"happy","n":20,"at":"t","s":0.33},{"op":"eff","e":"poison","t":51,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.3, ops=[{"op":"victim"},{"op":"fx","p":"happy","n":20,"at":"t","s":0.33},{"op":"eff","e":"poison","t":51,"a":124},{"op":"mark","t":160,"x":2.5}]〕
08. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"compost","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"compost","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]〕

**権能発動時の命令（27命令）**：

01. `{"op":"fx","p":"heart","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="heart", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"heart","n":4,"at":"self","s":0.7}` — 粒子演出〔p="heart", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"happy","n":50,"at":"self","s":1.6}` — 粒子演出〔p="happy", n=50, at="self", s=1.6〕
04. `{"op":"fx","p":"compost","n":30,"at":"self"}` — 粒子演出〔p="compost", n=30, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":1.0}` — 効果音〔s="chime", v=1.0, pi=1.0〕
06. `{"op":"summon","k":"wolf","n":5}` — 召喚〔k="wolf", n=5〕
07. `{"op":"allies","r":48}` — 味方対象〔r=48〕
08. `{"op":"healpct","v":0.6,"to":1}` — 最大HP割合回復〔v=0.6, to=1〕
09. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
10. `{"op":"buff","e":"regen","t":1200,"a":4,"to":1}` — 強化〔e="regen", t=1200, a=4, to=1〕
11. `{"op":"undying","t":180,"to":1}` — 死亡防護〔t=180, to=1〕
12. `{"op":"buff","e":"health","t":2400,"a":5,"to":1}` — 強化〔e="health", t=2400, a=5, to=1〕
13. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
14. `{"op":"stun","t":105}` — 行動停止〔t=105〕
15. `{"op":"pull","f":2.0}` — pull〔f=2.0〕
16. `{"op":"fx","p":"happy","n":12,"at":"t","s":0.5}` — 粒子演出〔p="happy", n=12, at="t", s=0.5〕
17. `{"op":"allies","r":26}` — 味方対象〔r=26〕
18. `{"op":"healpct","v":0.35}` — 最大HP割合回復〔v=0.35〕
19. `{"op":"cleanse"}` — 状態異常解除〔〕
20. `{"op":"self"}` — 対象を自分へ〔〕
21. `{"op":"buff","e":"regen","t":200,"a":2}` — 強化〔e="regen", t=200, a=2〕
22. `{"op":"fx","p":"compost","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="compost", n=50, at="ring", r=8.0, y=0.6〕
23. `{"op":"fx","p":"happy","n":32,"at":"line","r":30}` — 粒子演出〔p="happy", n=32, at="line", r=30〕
24. `{"op":"sound","s":"summon","v":1.15,"pi":0.95}` — 効果音〔s="summon", v=1.15, pi=0.95〕
25. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.magna_mater_legend.stage0","ops":[{"op":"fx","p":"happy","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"totem","v":0.9,"pi":1.2},{"op":"fx","p":"compost","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"heart","n":6,"at":"line","r":10},{"op":"fx","p":"heart","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"compost","n":36,"at":"line","r":24},{"op":"sound","s":"summon","v":1.05,"pi":1.14},{"op":"line","r":58.0,"w":5.0},{"op":"dmg","m":3.78},{"op":"eff","e":"poison","t":100,"a":1},{"op":"self"},{"op":"buff","e":"regen","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.magna_mater_legend.stage1","ops":[{"op":"fx","p":"happy","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"totem","v":1.05,"pi":1.0},{"op":"fx","p":"heart","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"compost","n":6,"at":"line","r":15},{"op":"fx","p":"compost","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"happy","n":32,"at":"line","r":30},{"op":"sound","s":"summon","v":1.15,"pi":0.95},{"op":"summon","k":"golem","n":4},{"op":"allies","r":25.0},{"op":"healpct","v":0.35},{"op":"area","r":12.0,"n":10},{"op":"eff","e":"poison","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.magna_mater_legend.stage2","ops":[{"op":"fx","p":"happy","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"totem","v":1.25,"pi":0.75},{"op":"fx","p":"heart","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"compost","n":10,"at":"line","r":20},{"op":"fx","p":"heart","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"compost","n":48,"at":"line","r":48},{"op":"fx","p":"happy","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"summon","v":1.5,"pi":0.75},{"op":"area","r":34.0,"n":28},{"op":"dmg","m":9.72},{"op":"summon","k":"golem","n":5},{"op":"allies","r":31.0},{"op":"healpct","v":0.5},{"op":"self"},{"op":"buff","e":"regen","t":180,"a":3},{"op":"fx","p":"happy","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"compost","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":30.0,"n":27},{"op":"dmg","m":3.1},{"op":"summon","k":"golem","n":4},{"op":"allies","r":30.0},{"op":"healpct","v":0.5},{"op":"allies","r":25.0},{"op":"healpct","v":0.28,"to":1},{"op":"cleanse","to":1},{"op":"self"},{"op":"guard","t":180},{"op":"self"},{"op":"summon","k":"wolf","n":3},{"op":"fx","p":"happy","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"totem","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"poison","t":51,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"allies","r":22},{"op":"healpct","v":0.24},{"op":"cleanse"},{"op":"guard","t":110}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.magna_mater_legend.stage0","ops":[{"op":"fx","p":"happy","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"totem","v":0.9,"pi":1.2},{"op":"fx","p":"compost","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"heart","n":6,"at":"line","r":10},{"op":"fx","p":"heart","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"compost","n":36,"at":"line","r":24},{"op":"sound","s":"summon","v":1.05,"pi":1.14},{"op":"line","r":58.0,"w":5.0},{"op":"dmg","m":3.78},{"op":"eff","e":"poison","t":100,"a":1},{"op":"self"},{"op":"buff","e":"regen","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.magna_mater_legend.stage1","ops":[{"op":"fx","p":"happy","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"totem","v":1.05,"pi":1.0},{"op":"fx","p":"heart","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"compost","n":6,"at":"line","r":15},{"op":"fx","p":"compost","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"happy","n":32,"at":"line","r":30},{"op":"sound","s":"summon","v":1.15,"pi":0.95},{"op":"summon","k":"golem","n":4},{"op":"allies","r":25.0},{"op":"healpct","v":0.35},{"op":"area","r":12.0,"n":10},{"op":"eff","e":"poison","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.magna_mater_legend.stage2","ops":[{"op":"fx","p":"happy","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"totem","v":1.25,"pi":0.75},{"op":"fx","p":"heart","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"compost","n":10,"at":"line","r":20},{"op":"fx","p":"heart","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"compost","n":48,"at":"line","r":48},{"op":"fx","p":"happy","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"summon","v":1.5,"pi":0.75},{"op":"area","r":34.0,"n":28},{"op":"dmg","m":9.72},{"op":"summon","k":"golem","n":5},{"op":"allies","r":31.0},{"op":"healpct","v":0.5},{"op":"self"},{"op":"buff","e":"regen","t":180,"a":3},{"op":"fx","p":"happy","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"compost","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":30.0,"n":27},{"op":"dmg","m":3.1},{"op":"summon","k":"golem","n":4},{"op":"allies","r":30.0},{"op":"healpct","v":0.5},{"op":"allies","r":25.0},{"op":"healpct","v":0.28,"to":1},{"op":"cleanse","to":1},{"op":"self"},{"op":"guard","t":180},{"op":"self"},{"op":"summon","k":"wolf","n":3},{"op":"fx","p":"happy","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"totem","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"poison","t":51,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"allies","r":22},{"op":"healpct","v":0.24},{"op":"cleanse"},{"op":"guard","t":110}]}]〕
26. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
27. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 32. 無限円環 ウロボロス

**モブ側の動きの方向性**：尾を環へ閉じる姿と周回する光輪を時間演出に同期させる。。

### 無限円環の輪刃 — 討伐武器（メイン／武器欄） (`ouroboros_weapon`)

**現行パラメータ**：rank=1、damage登録値=305.25926、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:sweeping_edge:25。

**装備中の常時命令（3命令）**：

01. `{"op":"snapshot"}` — 状態保存〔〕
02. `{"op":"self"}` — 対象を自分へ〔〕
03. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（9命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"stun","t":15}` — 行動停止〔t=15〕
03. `{"op":"chance","p":0.3,"ops":[{"op":"victim"},{"op":"dmg","m":0.3}]}` — 抽選〔p=0.3, ops=[{"op":"victim"},{"op":"dmg","m":0.3}]〕
04. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"slow","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"slow","t":90,"a":0}]〕
05. `{"op":"chance","p":0.465,"ops":[{"op":"victim"},{"op":"fx","p":"rportal","n":11,"at":"t","s":0.24},{"op":"mark","t":140,"x":1.79},{"op":"eff","e":"slow","t":67,"a":0}]}` — 抽選〔p=0.465, ops=[{"op":"victim"},{"op":"fx","p":"rportal","n":11,"at":"t","s":0.24},{"op":"mark","t":140,"x":1.79},{"op":"eff","e":"slow","t":67,"a":0}]〕
06. `{"op":"chance","p":0.177,"ops":[{"op":"victim"},{"op":"dmg","m":0.235}]}` — 抽選〔p=0.177, ops=[{"op":"victim"},{"op":"dmg","m":0.235}]〕
07. `{"op":"chance","p":0.142,"ops":[{"op":"victim"},{"op":"fx","p":"rportal","n":8,"at":"t","s":0.25},{"op":"stun","t":7}]}` — 抽選〔p=0.142, ops=[{"op":"victim"},{"op":"fx","p":"rportal","n":8,"at":"t","s":0.25},{"op":"stun","t":7}]〕
08. `{"op":"chance","p":0.2,"ops":[{"op":"victim"},{"op":"fx","p":"portal","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.2, ops=[{"op":"victim"},{"op":"fx","p":"portal","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]〕
09. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"rportal","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"rportal","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]〕

**権能発動時の命令（24命令）**：

01. `{"op":"fx","p":"rportal","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="rportal", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"rportal","n":4,"at":"self","s":0.7}` — 粒子演出〔p="rportal", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"enchant","n":50,"at":"ring","r":3}` — 粒子演出〔p="enchant", n=50, at="ring", r=3〕
04. `{"op":"fx","p":"portal","n":30,"at":"self"}` — 粒子演出〔p="portal", n=30, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":0.7}` — 効果音〔s="chime", v=1.0, pi=0.7〕
06. `{"op":"rewind"}` — 復元〔〕
07. `{"op":"area","r":16,"n":36}` — 円形対象の取得〔r=16, n=36〕
08. `{"op":"dmg","m":1.68}` — 追加攻撃〔m=1.68〕
09. `{"op":"stun","t":65}` — 行動停止〔t=65〕
10. `{"op":"fx","p":"enchant","n":12,"at":"t","s":0.5}` — 粒子演出〔p="enchant", n=12, at="t", s=0.5〕
11. `{"op":"fx","p":"rportal","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="rportal", n=46, at="ring", r=5.5, y=0.25〕
12. `{"op":"fx","p":"enchant","n":36,"at":"line","r":24}` — 粒子演出〔p="enchant", n=36, at="line", r=24〕
13. `{"op":"chain","n":5,"r":19.0}` — chain〔n=5, r=19.0〕
14. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
15. `{"op":"eff","e":"slow","t":100,"a":2}` — 敵への状態異常〔e="slow", t=100, a=2〕
16. `{"op":"fx","p":"portal","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="portal", n=16, at="ring", r=5.0〕
17. `{"op":"sound","s":"spell","v":0.75,"pi":1.15}` — 効果音〔s="spell", v=0.75, pi=1.15〕
18. `{"op":"area","r":9,"n":8}` — 円形対象の取得〔r=9, n=8〕
19. `{"op":"dmg","m":0.9}` — 追加攻撃〔m=0.9〕
20. `{"op":"eff","e":"slow","t":65,"a":0}` — 敵への状態異常〔e="slow", t=65, a=0〕
21. `{"op":"fx","p":"portal","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="portal", n=24, at="ring", r=4.5, y=0.6〕
22. `{"op":"sound","s":"mirror","v":0.8,"pi":0.8}` — 効果音〔s="mirror", v=0.8, pi=0.8〕
23. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
24. `{"op":"eff","e":"slow","t":32,"a":124}` — 敵への状態異常〔e="slow", t=32, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 輪廻記憶の砂時計 — 神威触媒（Curios relic_focus） (`ouroboros_focus`)

**現行パラメータ**：rank=2、damage登録値=68.31、relics側CD=145tick、art側CD=145tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（10命令）**：

01. `{"op":"snapshot"}` — 状態保存〔〕
02. `{"op":"self"}` — 対象を自分へ〔〕
03. `{"op":"buff","e":"regen","t":40,"a":0}` — 強化〔e="regen", t=40, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"regen","t":45,"a":0}` — 強化〔e="regen", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"resist","t":42,"a":2}` — 強化〔e="resist", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（43命令）**：

01. `{"op":"fx","p":"rportal","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="rportal", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"rportal","n":6,"at":"self","s":0.7}` — 粒子演出〔p="rportal", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"enchant","n":50,"at":"ring","r":3}` — 粒子演出〔p="enchant", n=50, at="ring", r=3〕
04. `{"op":"fx","p":"portal","n":30,"at":"self"}` — 粒子演出〔p="portal", n=30, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":0.7}` — 効果音〔s="chime", v=1.0, pi=0.7〕
06. `{"op":"area","r":32,"n":36}` — 円形対象の取得〔r=32, n=36〕
07. `{"op":"stun","t":90}` — 行動停止〔t=90〕
08. `{"op":"freeze","t":200}` — freeze〔t=200〕
09. `{"op":"erase","r":32}` — erase〔r=32〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"healpct","v":0.4}` — 最大HP割合回復〔v=0.4〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"regen","t":150,"a":1}` — 強化〔e="regen", t=150, a=1〕
15. `{"op":"fx","p":"enchant","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="enchant", n=50, at="ring", r=8.0, y=0.6〕
16. `{"op":"fx","p":"end_rod","n":32,"at":"line","r":30}` — 粒子演出〔p="end_rod", n=32, at="line", r=30〕
17. `{"op":"sound","s":"mirror","v":1.15,"pi":0.95}` — 効果音〔s="mirror", v=1.15, pi=0.95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"snapshot"}` — 状態保存〔〕
20. `{"op":"guard","t":120}` — 防御〔t=120〕
21. `{"op":"area","r":22.0,"n":16}` — 円形対象の取得〔r=22.0, n=16〕
22. `{"op":"dmg","m":2.6}` — 追加攻撃〔m=2.6〕
23. `{"op":"self"}` — 対象を自分へ〔〕
24. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
25. `{"op":"buff","e":"resist","t":150,"a":3}` — 強化〔e="resist", t=150, a=3〕
26. `{"op":"fx","p":"portal","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="portal", n=24, at="ring", r=12, y=0.5〕
27. `{"op":"sound","s":"mirror","v":0.85,"pi":0.97}` — 効果音〔s="mirror", v=0.85, pi=0.97〕
28. `{"op":"line","r":30.0,"w":2.5}` — 線分対象の取得〔r=30.0, w=2.5〕
29. `{"op":"dmg","m":0.85}` — 追加攻撃〔m=0.85〕
30. `{"op":"eff","e":"slow","t":160,"a":1}` — 敵への状態異常〔e="slow", t=160, a=1〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"resist","t":220,"a":3}` — 強化〔e="resist", t=220, a=3〕
33. `{"op":"self"}` — 対象を自分へ〔〕
34. `{"op":"snapshot"}` — 状態保存〔〕
35. `{"op":"fx","p":"portal","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="portal", n=24, at="ring", r=5.5, y=0.7〕
36. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
37. `{"op":"eff","e":"slow","t":43,"a":123}` — 敵への状態異常〔e="slow", t=43, a=123〕
38. `{"op":"self"}` — 対象を自分へ〔〕
39. `{"op":"buff","e":"resist","t":140,"a":2}` — 強化〔e="resist", t=140, a=2〕
40. `{"op":"fx","p":"rportal","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="rportal", n=16, at="ring", r=3.7, y=0.55〕
41. `{"op":"self"}` — 対象を自分へ〔〕
42. `{"op":"guard","t":90}` — 防御〔t=90〕
43. `{"op":"buff","e":"luck","t":160,"a":5}` — 強化〔e="luck", t=160, a=5〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 無傷回帰の環 — 神格装飾品（Curios relic_charm） (`ouroboros_charm`)

**現行パラメータ**：rank=1、damage登録値=68.31、relics側CD=175tick、art側CD=175tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（11命令）**：

01. `{"op":"snapshot"}` — 状態保存〔〕
02. `{"op":"self"}` — 対象を自分へ〔〕
03. `{"op":"buff","e":"regen","t":45,"a":0}` — 強化〔e="regen", t=45, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
06. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
07. `{"op":"buff","e":"resist","t":45,"a":1}` — 強化〔e="resist", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"resist","t":42,"a":2}` — 強化〔e="resist", t=42, a=2〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"luck","t":48,"a":8}` — 強化〔e="luck", t=48, a=8〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（36命令）**：

01. `{"op":"fx","p":"rportal","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="rportal", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"rportal","n":4,"at":"self","s":0.7}` — 粒子演出〔p="rportal", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"enchant","n":50,"at":"ring","r":3}` — 粒子演出〔p="enchant", n=50, at="ring", r=3〕
04. `{"op":"fx","p":"portal","n":30,"at":"self"}` — 粒子演出〔p="portal", n=30, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":0.7}` — 効果音〔s="chime", v=1.0, pi=0.7〕
06. `{"op":"rewind"}` — 復元〔〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"cleanse"}` — 状態異常解除〔〕
09. `{"op":"guard","t":40}` — 防御〔t=40〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"regen","t":210,"a":1}` — 強化〔e="regen", t=210, a=1〕
13. `{"op":"fx","p":"rportal","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="rportal", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"enchant","n":36,"at":"line","r":24}` — 粒子演出〔p="enchant", n=36, at="line", r=24〕
15. `{"op":"sound","s":"mirror","v":1.05,"pi":1.14}` — 効果音〔s="mirror", v=1.05, pi=1.14〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"guard","t":95}` — 防御〔t=95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
20. `{"op":"cleanse"}` — 状態異常解除〔〕
21. `{"op":"buff","e":"resist","t":180,"a":3}` — 強化〔e="resist", t=180, a=3〕
22. `{"op":"guard","t":95}` — 防御〔t=95〕
23. `{"op":"fx","p":"portal","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="portal", n=30, at="ring", r=4.0, y=0.7〕
24. `{"op":"sound","s":"mirror","v":0.8,"pi":1.1}` — 効果音〔s="mirror", v=0.8, pi=1.1〕
25. `{"op":"self"}` — 対象を自分へ〔〕
26. `{"op":"buff","e":"resist","t":280,"a":4}` — 強化〔e="resist", t=280, a=4〕
27. `{"op":"guard","t":170}` — 防御〔t=170〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"reflect","t":80,"r":18}` — 反射〔t=80, r=18〕
30. `{"op":"fx","p":"portal","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="portal", n=20, at="ring", r=4, y=0.4〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"resist","t":140,"a":2}` — 強化〔e="resist", t=140, a=2〕
33. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
34. `{"op":"eff","e":"slow","t":32,"a":123}` — 敵への状態異常〔e="slow", t=32, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 宇宙継続・無限円環 — 超越神器（武器欄） (`ouroboros_legend`)

**現行パラメータ**：rank=3、damage登録値=524.33333、relics側CD=330tick、art側CD=330tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:sweeping_edge:25。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"snapshot"}` — 状態保存〔〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
08. `{"op":"buff","e":"resist","t":45,"a":3}` — 強化〔e="resist", t=45, a=3〕
09. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（8命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"stun","t":30}` — 行動停止〔t=30〕
03. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"slow","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"slow","t":160,"a":1}]〕
04. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"rportal","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"rportal","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
05. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"enchant","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"enchant","n":10,"at":"t","s":0.35}]〕
06. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
07. `{"op":"chance","p":0.325,"ops":[{"op":"victim"},{"op":"fx","p":"portal","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.325, ops=[{"op":"victim"},{"op":"fx","p":"portal","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]〕
08. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"rportal","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"rportal","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]〕

**権能発動時の命令（25命令）**：

01. `{"op":"fx","p":"rportal","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="rportal", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"rportal","n":4,"at":"self","s":0.7}` — 粒子演出〔p="rportal", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"enchant","n":50,"at":"ring","r":3}` — 粒子演出〔p="enchant", n=50, at="ring", r=3〕
04. `{"op":"fx","p":"portal","n":30,"at":"self"}` — 粒子演出〔p="portal", n=30, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":0.7}` — 効果音〔s="chime", v=1.0, pi=0.7〕
06. `{"op":"rewind"}` — 復元〔〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"undying","t":180}` — 死亡防護〔t=180〕
09. `{"op":"healpct","v":0.6}` — 最大HP割合回復〔v=0.6〕
10. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
11. `{"op":"stun","t":105}` — 行動停止〔t=105〕
12. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
13. `{"op":"eff","e":"slow","t":600,"a":6}` — 敵への状態異常〔e="slow", t=600, a=6〕
14. `{"op":"erase","r":64}` — erase〔r=64〕
15. `{"op":"fx","p":"enchant","n":12,"at":"t","s":0.5}` — 粒子演出〔p="enchant", n=12, at="t", s=0.5〕
16. `{"op":"snapshot"}` — 状態保存〔〕
17. `{"op":"self"}` — 対象を自分へ〔〕
18. `{"op":"guard","t":100}` — 防御〔t=100〕
19. `{"op":"buff","e":"regen","a":2,"t":180}` — 強化〔e="regen", a=2, t=180〕
20. `{"op":"fx","p":"enchant","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="enchant", n=50, at="ring", r=8.0, y=0.6〕
21. `{"op":"fx","p":"end_rod","n":32,"at":"line","r":30}` — 粒子演出〔p="end_rod", n=32, at="line", r=30〕
22. `{"op":"sound","s":"mirror","v":1.15,"pi":0.95}` — 効果音〔s="mirror", v=1.15, pi=0.95〕
23. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.ouroboros_legend.stage0","ops":[{"op":"fx","p":"portal","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"mirror","v":0.9,"pi":1.2},{"op":"fx","p":"rportal","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"enchant","n":6,"at":"line","r":10},{"op":"fx","p":"rportal","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"enchant","n":36,"at":"line","r":24},{"op":"sound","s":"mirror","v":1.05,"pi":1.14},{"op":"chain","n":5,"r":19.0},{"op":"dmg","m":3.78},{"op":"eff","e":"slow","t":100,"a":2},{"op":"self"},{"op":"buff","e":"resist","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.ouroboros_legend.stage1","ops":[{"op":"fx","p":"portal","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"mirror","v":1.05,"pi":1.0},{"op":"fx","p":"enchant","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"rportal","n":6,"at":"line","r":15},{"op":"fx","p":"enchant","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"end_rod","n":32,"at":"line","r":30},{"op":"sound","s":"mirror","v":1.15,"pi":0.95},{"op":"self"},{"op":"snapshot"},{"op":"guard","t":120},{"op":"area","r":22.0,"n":16},{"op":"dmg","m":3.77},{"op":"area","r":14.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.ouroboros_legend.stage2","ops":[{"op":"fx","p":"portal","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"mirror","v":1.25,"pi":0.75},{"op":"fx","p":"enchant","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"rportal","n":10,"at":"line","r":20},{"op":"fx","p":"rportal","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"enchant","n":48,"at":"line","r":48},{"op":"fx","p":"end_rod","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"mirror","v":1.5,"pi":0.75},{"op":"area","r":32.0,"n":26},{"op":"dmg","m":10.206},{"op":"stun","t":50},{"op":"self"},{"op":"rewind"},{"op":"guard","t":170},{"op":"fx","p":"end_rod","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"enchant","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":27.0,"n":24},{"op":"dmg","m":3.0},{"op":"self"},{"op":"rewind"},{"op":"guard","t":120},{"op":"line","r":38.0,"w":4.0},{"op":"dmg","m":0.9},{"op":"eff","e":"slow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"resist","t":240,"a":4},{"op":"self"},{"op":"guard","t":130},{"op":"fx","p":"portal","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"mirror","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"slow","t":65,"a":15},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.ouroboros_legend.stage0","ops":[{"op":"fx","p":"portal","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"mirror","v":0.9,"pi":1.2},{"op":"fx","p":"rportal","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"enchant","n":6,"at":"line","r":10},{"op":"fx","p":"rportal","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"enchant","n":36,"at":"line","r":24},{"op":"sound","s":"mirror","v":1.05,"pi":1.14},{"op":"chain","n":5,"r":19.0},{"op":"dmg","m":3.78},{"op":"eff","e":"slow","t":100,"a":2},{"op":"self"},{"op":"buff","e":"resist","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.ouroboros_legend.stage1","ops":[{"op":"fx","p":"portal","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"mirror","v":1.05,"pi":1.0},{"op":"fx","p":"enchant","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"rportal","n":6,"at":"line","r":15},{"op":"fx","p":"enchant","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"end_rod","n":32,"at":"line","r":30},{"op":"sound","s":"mirror","v":1.15,"pi":0.95},{"op":"self"},{"op":"snapshot"},{"op":"guard","t":120},{"op":"area","r":22.0,"n":16},{"op":"dmg","m":3.77},{"op":"area","r":14.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.ouroboros_legend.stage2","ops":[{"op":"fx","p":"portal","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"mirror","v":1.25,"pi":0.75},{"op":"fx","p":"enchant","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"rportal","n":10,"at":"line","r":20},{"op":"fx","p":"rportal","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"enchant","n":48,"at":"line","r":48},{"op":"fx","p":"end_rod","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"mirror","v":1.5,"pi":0.75},{"op":"area","r":32.0,"n":26},{"op":"dmg","m":10.206},{"op":"stun","t":50},{"op":"self"},{"op":"rewind"},{"op":"guard","t":170},{"op":"fx","p":"end_rod","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"enchant","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":27.0,"n":24},{"op":"dmg","m":3.0},{"op":"self"},{"op":"rewind"},{"op":"guard","t":120},{"op":"line","r":38.0,"w":4.0},{"op":"dmg","m":0.9},{"op":"eff","e":"slow","t":160,"a":2},{"op":"self"},{"op":"buff","e":"resist","t":240,"a":4},{"op":"self"},{"op":"guard","t":130},{"op":"fx","p":"portal","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"mirror","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"slow","t":65,"a":15},{"op":"mark","t":135,"x":1.8}]}]〕
24. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
25. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 33. 玖天神樹 イグドラシル

**モブ側の動きの方向性**：少女分体の軽い動作と巨大な樹木本体の根・枝葉を別制御する。。

### 玖天神樹の若枝 — 討伐武器（メイン／武器欄） (`yggdrasil_weapon`)

**現行パラメータ**：rank=1、damage登録値=578.5、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（6命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"regen","t":40,"a":0}` — 強化〔e="regen", t=40, a=0〕
03. `{"op":"allies","r":8}` — 味方対象〔r=8〕
04. `{"op":"buff","e":"regen","t":40,"a":0,"to":1}` — 強化〔e="regen", t=40, a=0, to=1〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（8命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"stun","t":15}` — 行動停止〔t=15〕
03. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"slow","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"slow","t":90,"a":0}]〕
04. `{"op":"chance","p":0.45,"ops":[{"op":"victim"},{"op":"fx","p":"happy","n":13,"at":"t","s":0.24},{"op":"mark","t":160,"x":1.93},{"op":"eff","e":"slow","t":79,"a":0}]}` — 抽選〔p=0.45, ops=[{"op":"victim"},{"op":"fx","p":"happy","n":13,"at":"t","s":0.24},{"op":"mark","t":160,"x":1.93},{"op":"eff","e":"slow","t":79,"a":0}]〕
05. `{"op":"chance","p":0.204,"ops":[{"op":"victim"},{"op":"dmg","m":0.27}]}` — 抽選〔p=0.204, ops=[{"op":"victim"},{"op":"dmg","m":0.27}]〕
06. `{"op":"chance","p":0.085,"ops":[{"op":"victim"},{"op":"fx","p":"happy","n":8,"at":"t","s":0.25},{"op":"self"},{"op":"healpct","v":0.04}]}` — 抽選〔p=0.085, ops=[{"op":"victim"},{"op":"fx","p":"happy","n":8,"at":"t","s":0.25},{"op":"self"},{"op":"healpct","v":0.04}]〕
07. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"compost","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"compost","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]〕
08. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"compost","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"compost","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]〕

**権能発動時の命令（29命令）**：

01. `{"op":"fx","p":"compost","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="compost", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"compost","n":4,"at":"self","s":0.7}` — 粒子演出〔p="compost", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"happy","n":50,"at":"self","s":1.6}` — 粒子演出〔p="happy", n=50, at="self", s=1.6〕
04. `{"op":"fx","p":"compost","n":40,"at":"self"}` — 粒子演出〔p="compost", n=40, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":1.1}` — 効果音〔s="chime", v=1.0, pi=1.1〕
06. `{"op":"area","r":20,"n":36}` — 円形対象の取得〔r=20, n=36〕
07. `{"op":"slam","f":2.0}` — slam〔f=2.0〕
08. `{"op":"stun","t":65}` — 行動停止〔t=65〕
09. `{"op":"dmg","m":1.44}` — 追加攻撃〔m=1.44〕
10. `{"op":"allies","r":20}` — 味方対象〔r=20〕
11. `{"op":"healpct","v":0.25,"to":1}` — 最大HP割合回復〔v=0.25, to=1〕
12. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
13. `{"op":"summon","k":"wolf","n":2}` — 召喚〔k="wolf", n=2〕
14. `{"op":"fx","p":"happy","n":12,"at":"t","s":0.5}` — 粒子演出〔p="happy", n=12, at="t", s=0.5〕
15. `{"op":"fx","p":"happy","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="happy", n=46, at="ring", r=5.5, y=0.25〕
16. `{"op":"fx","p":"compost","n":36,"at":"line","r":24}` — 粒子演出〔p="compost", n=36, at="line", r=24〕
17. `{"op":"area","r":25.0,"n":20}` — 円形対象の取得〔r=25.0, n=20〕
18. `{"op":"pull","f":1.6}` — pull〔f=1.6〕
19. `{"op":"eff","e":"slow","t":100,"a":2}` — 敵への状態異常〔e="slow", t=100, a=2〕
20. `{"op":"dmg","m":2.1}` — 追加攻撃〔m=2.1〕
21. `{"op":"fx","p":"happy","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="happy", n=16, at="ring", r=5.0〕
22. `{"op":"sound","s":"spell","v":0.75,"pi":1.15}` — 効果音〔s="spell", v=0.75, pi=1.15〕
23. `{"op":"area","r":9,"n":8}` — 円形対象の取得〔r=9, n=8〕
24. `{"op":"dmg","m":0.9}` — 追加攻撃〔m=0.9〕
25. `{"op":"eff","e":"slow","t":65,"a":0}` — 敵への状態異常〔e="slow", t=65, a=0〕
26. `{"op":"fx","p":"compost","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="compost", n=24, at="ring", r=4.5, y=0.6〕
27. `{"op":"sound","s":"chime","v":0.8,"pi":0.8}` — 効果音〔s="chime", v=0.8, pi=0.8〕
28. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
29. `{"op":"eff","e":"slow","t":32,"a":124}` — 敵への状態異常〔e="slow", t=32, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 九界魔流の神実 — 神威触媒（Curios relic_focus） (`yggdrasil_focus`)

**現行パラメータ**：rank=2、damage登録値=68.31、relics側CD=160tick、art側CD=160tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（12命令）**：

01. `{"op":"allies","r":16}` — 味方対象〔r=16〕
02. `{"op":"buff","e":"regen","t":40,"a":0,"to":1}` — 強化〔e="regen", t=40, a=0, to=1〕
03. `{"op":"buff","e":"haste","t":40,"a":0,"to":1}` — 強化〔e="haste", t=40, a=0, to=1〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"regen","t":45,"a":0}` — 強化〔e="regen", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"fx","p":"compost","n":10,"at":"self","s":0.12}` — 粒子演出〔p="compost", n=10, at="self", s=0.12〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
10. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"regen","t":42,"a":2}` — 強化〔e="regen", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（45命令）**：

01. `{"op":"fx","p":"compost","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="compost", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"compost","n":6,"at":"self","s":0.7}` — 粒子演出〔p="compost", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"happy","n":50,"at":"self","s":1.6}` — 粒子演出〔p="happy", n=50, at="self", s=1.6〕
04. `{"op":"fx","p":"compost","n":40,"at":"self"}` — 粒子演出〔p="compost", n=40, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":1.1}` — 効果音〔s="chime", v=1.0, pi=1.1〕
06. `{"op":"allies","r":32}` — 味方対象〔r=32〕
07. `{"op":"healpct","v":0.4,"to":1}` — 最大HP割合回復〔v=0.4, to=1〕
08. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
09. `{"op":"buff","e":"regen","t":600,"a":3,"to":1}` — 強化〔e="regen", t=600, a=3, to=1〕
10. `{"op":"buff","e":"health","t":1200,"a":2,"to":1}` — 強化〔e="health", t=1200, a=2, to=1〕
11. `{"op":"buff","e":"absorb","t":600,"a":4,"to":1}` — 強化〔e="absorb", t=600, a=4, to=1〕
12. `{"op":"xp","v":100}` — xp〔v=100〕
13. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
14. `{"op":"self"}` — 対象を自分へ〔〕
15. `{"op":"buff","e":"regen","t":150,"a":1}` — 強化〔e="regen", t=150, a=1〕
16. `{"op":"fx","p":"compost","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="compost", n=50, at="ring", r=8.0, y=0.6〕
17. `{"op":"fx","p":"heart","n":32,"at":"line","r":30}` — 粒子演出〔p="heart", n=32, at="line", r=30〕
18. `{"op":"sound","s":"totem","v":1.15,"pi":0.95}` — 効果音〔s="totem", v=1.15, pi=0.95〕
19. `{"op":"allies","r":31.0}` — 味方対象〔r=31.0〕
20. `{"op":"healpct","v":0.55}` — 最大HP割合回復〔v=0.55〕
21. `{"op":"cleanse"}` — 状態異常解除〔〕
22. `{"op":"self"}` — 対象を自分へ〔〕
23. `{"op":"buff","e":"regen","t":170,"a":3}` — 強化〔e="regen", t=170, a=3〕
24. `{"op":"self"}` — 対象を自分へ〔〕
25. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
26. `{"op":"buff","e":"regen","t":150,"a":3}` — 強化〔e="regen", t=150, a=3〕
27. `{"op":"fx","p":"compost","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="compost", n=24, at="ring", r=12, y=0.5〕
28. `{"op":"sound","s":"chime","v":0.85,"pi":1.04}` — 効果音〔s="chime", v=0.85, pi=1.04〕
29. `{"op":"allies","r":22.0}` — 味方対象〔r=22.0〕
30. `{"op":"healpct","v":0.14,"to":1}` — 最大HP割合回復〔v=0.14, to=1〕
31. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"buff","e":"regen","t":240,"a":3}` — 強化〔e="regen", t=240, a=3〕
34. `{"op":"allies","r":24.0}` — 味方対象〔r=24.0〕
35. `{"op":"healpct","v":0.14,"to":1}` — 最大HP割合回復〔v=0.14, to=1〕
36. `{"op":"fx","p":"compost","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="compost", n=24, at="ring", r=5.5, y=0.7〕
37. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
38. `{"op":"eff","e":"slow","t":43,"a":123}` — 敵への状態異常〔e="slow", t=43, a=123〕
39. `{"op":"self"}` — 対象を自分へ〔〕
40. `{"op":"buff","e":"regen","t":140,"a":7}` — 強化〔e="regen", t=140, a=7〕
41. `{"op":"fx","p":"compost","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="compost", n=16, at="ring", r=3.7, y=0.55〕
42. `{"op":"allies","r":18.0}` — 味方対象〔r=18.0〕
43. `{"op":"healpct","v":0.24}` — 最大HP割合回復〔v=0.24〕
44. `{"op":"cleanse"}` — 状態異常解除〔〕
45. `{"op":"buff","e":"regen","t":130,"a":3}` — 強化〔e="regen", t=130, a=3〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 世界樹の若葉冠 — 神格装飾品（Curios relic_charm） (`yggdrasil_charm`)

**現行パラメータ**：rank=1、damage登録値=68.31、relics側CD=190tick、art側CD=190tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（13命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
03. `{"op":"buff","e":"saturation","t":40,"a":0}` — 強化〔e="saturation", t=40, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"regen","t":45,"a":0}` — 強化〔e="regen", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
09. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"regen","t":42,"a":2}` — 強化〔e="regen", t=42, a=2〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"regen","t":48,"a":5}` — 強化〔e="regen", t=48, a=5〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（38命令）**：

01. `{"op":"fx","p":"compost","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="compost", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"compost","n":4,"at":"self","s":0.7}` — 粒子演出〔p="compost", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"happy","n":50,"at":"self","s":1.6}` — 粒子演出〔p="happy", n=50, at="self", s=1.6〕
04. `{"op":"fx","p":"compost","n":40,"at":"self"}` — 粒子演出〔p="compost", n=40, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":1.1}` — 効果音〔s="chime", v=1.0, pi=1.1〕
06. `{"op":"allies","r":24}` — 味方対象〔r=24〕
07. `{"op":"healpct","v":0.25,"to":1}` — 最大HP割合回復〔v=0.25, to=1〕
08. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"food"}` — food〔〕
11. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"regen","t":210,"a":1}` — 強化〔e="regen", t=210, a=1〕
14. `{"op":"fx","p":"happy","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="happy", n=46, at="ring", r=5.5, y=0.25〕
15. `{"op":"fx","p":"compost","n":36,"at":"line","r":24}` — 粒子演出〔p="compost", n=36, at="line", r=24〕
16. `{"op":"sound","s":"totem","v":1.05,"pi":1.14}` — 効果音〔s="totem", v=1.05, pi=1.14〕
17. `{"op":"self"}` — 対象を自分へ〔〕
18. `{"op":"guard","t":95}` — 防御〔t=95〕
19. `{"op":"self"}` — 対象を自分へ〔〕
20. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
21. `{"op":"cleanse"}` — 状態異常解除〔〕
22. `{"op":"buff","e":"regen","t":180,"a":3}` — 強化〔e="regen", t=180, a=3〕
23. `{"op":"guard","t":95}` — 防御〔t=95〕
24. `{"op":"fx","p":"compost","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="compost", n=30, at="ring", r=4.0, y=0.7〕
25. `{"op":"sound","s":"chime","v":0.8,"pi":1.1}` — 効果音〔s="chime", v=0.8, pi=1.1〕
26. `{"op":"self"}` — 対象を自分へ〔〕
27. `{"op":"buff","e":"regen","t":300,"a":4}` — 強化〔e="regen", t=300, a=4〕
28. `{"op":"guard","t":125}` — 防御〔t=125〕
29. `{"op":"allies","r":24.0}` — 味方対象〔r=24.0〕
30. `{"op":"healpct","v":0.14,"to":1}` — 最大HP割合回復〔v=0.14, to=1〕
31. `{"op":"fx","p":"compost","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="compost", n=20, at="ring", r=4, y=0.4〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"buff","e":"regen","t":140,"a":7}` — 強化〔e="regen", t=140, a=7〕
34. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
35. `{"op":"eff","e":"slow","t":32,"a":123}` — 敵への状態異常〔e="slow", t=32, a=123〕
36. `{"op":"allies","r":16}` — 味方対象〔r=16〕
37. `{"op":"healpct","v":0.18}` — 最大HP割合回復〔v=0.18〕
38. `{"op":"cleanse"}` — 状態異常解除〔〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 玖界循環・神樹の心葉 — 超越神器（武器欄） (`yggdrasil_legend`)

**現行パラメータ**：rank=3、damage登録値=1157.875、relics側CD=345tick、art側CD=345tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"allies","r":16}` — 味方対象〔r=16〕
06. `{"op":"buff","e":"regen","t":40,"a":1,"to":1}` — 強化〔e="regen", t=40, a=1, to=1〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
09. `{"op":"buff","e":"regen","t":45,"a":3}` — 強化〔e="regen", t=45, a=3〕
10. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（8命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"stun","t":20}` — 行動停止〔t=20〕
03. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"slow","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"slow","t":160,"a":1}]〕
04. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"happy","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"happy","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
05. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"happy","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"happy","n":10,"at":"t","s":0.35}]〕
06. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
07. `{"op":"chance","p":0.35,"ops":[{"op":"victim"},{"op":"fx","p":"compost","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.35, ops=[{"op":"victim"},{"op":"fx","p":"compost","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]〕
08. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"compost","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"compost","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]〕

**権能発動時の命令（27命令）**：

01. `{"op":"fx","p":"compost","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="compost", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"compost","n":4,"at":"self","s":0.7}` — 粒子演出〔p="compost", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"happy","n":50,"at":"self","s":1.6}` — 粒子演出〔p="happy", n=50, at="self", s=1.6〕
04. `{"op":"fx","p":"compost","n":40,"at":"self"}` — 粒子演出〔p="compost", n=40, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":1.1}` — 効果音〔s="chime", v=1.0, pi=1.1〕
06. `{"op":"allies","r":48}` — 味方対象〔r=48〕
07. `{"op":"healpct","v":0.6,"to":1}` — 最大HP割合回復〔v=0.6, to=1〕
08. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
09. `{"op":"buff","e":"regen","t":1200,"a":5,"to":1}` — 強化〔e="regen", t=1200, a=5, to=1〕
10. `{"op":"undying","t":180,"to":1}` — 死亡防護〔t=180, to=1〕
11. `{"op":"fx","p":"end_rod","n":44,"at":"ring","r":10}` — 粒子演出〔p="end_rod", n=44, at="ring", r=10〕
12. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
13. `{"op":"stun","t":105}` — 行動停止〔t=105〕
14. `{"op":"lightning"}` — lightning〔〕
15. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
16. `{"op":"fx","p":"happy","n":12,"at":"t","s":0.5}` — 粒子演出〔p="happy", n=12, at="t", s=0.5〕
17. `{"op":"allies","r":26}` — 味方対象〔r=26〕
18. `{"op":"healpct","v":0.35}` — 最大HP割合回復〔v=0.35〕
19. `{"op":"cleanse"}` — 状態異常解除〔〕
20. `{"op":"self"}` — 対象を自分へ〔〕
21. `{"op":"buff","e":"regen","t":200,"a":2}` — 強化〔e="regen", t=200, a=2〕
22. `{"op":"fx","p":"compost","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="compost", n=50, at="ring", r=8.0, y=0.6〕
23. `{"op":"fx","p":"heart","n":32,"at":"line","r":30}` — 粒子演出〔p="heart", n=32, at="line", r=30〕
24. `{"op":"sound","s":"totem","v":1.15,"pi":0.95}` — 効果音〔s="totem", v=1.15, pi=0.95〕
25. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.yggdrasil_legend.stage0","ops":[{"op":"fx","p":"compost","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"chime","v":0.9,"pi":1.2},{"op":"fx","p":"compost","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"heart","n":6,"at":"line","r":10},{"op":"fx","p":"happy","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"compost","n":36,"at":"line","r":24},{"op":"sound","s":"totem","v":1.05,"pi":1.14},{"op":"area","r":25.0,"n":20},{"op":"pull","f":1.6},{"op":"eff","e":"slow","t":100,"a":2},{"op":"dmg","m":2.835},{"op":"self"},{"op":"buff","e":"regen","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.yggdrasil_legend.stage1","ops":[{"op":"fx","p":"compost","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"chime","v":1.05,"pi":1.0},{"op":"fx","p":"heart","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"compost","n":6,"at":"line","r":15},{"op":"fx","p":"compost","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"heart","n":32,"at":"line","r":30},{"op":"sound","s":"totem","v":1.15,"pi":0.95},{"op":"allies","r":31.0},{"op":"healpct","v":0.55},{"op":"cleanse"},{"op":"self"},{"op":"buff","e":"regen","t":170,"a":3},{"op":"area","r":16.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.yggdrasil_legend.stage2","ops":[{"op":"fx","p":"compost","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"chime","v":1.25,"pi":0.75},{"op":"fx","p":"heart","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"compost","n":10,"at":"line","r":20},{"op":"fx","p":"happy","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"compost","n":48,"at":"line","r":48},{"op":"fx","p":"heart","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"totem","v":1.5,"pi":0.75},{"op":"area","r":33.0,"n":25},{"op":"dmg","m":8.262},{"op":"stun","t":46},{"op":"allies","r":36.0},{"op":"healpct","v":0.6},{"op":"cleanse"},{"op":"self"},{"op":"guard","t":170},{"op":"fx","p":"heart","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"happy","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":30.0,"n":27},{"op":"dmg","m":2.6},{"op":"allies","r":36.0},{"op":"healpct","v":0.75},{"op":"cleanse"},{"op":"self"},{"op":"buff","e":"regen","t":180,"a":3},{"op":"allies","r":31.0},{"op":"healpct","v":0.28,"to":1},{"op":"cleanse","to":1},{"op":"self"},{"op":"guard","t":180},{"op":"allies","r":24.0},{"op":"healpct","v":0.14,"to":1},{"op":"fx","p":"compost","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"chime","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"allies","r":22},{"op":"healpct","v":0.24},{"op":"cleanse"},{"op":"guard","t":110}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.yggdrasil_legend.stage0","ops":[{"op":"fx","p":"compost","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"chime","v":0.9,"pi":1.2},{"op":"fx","p":"compost","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"heart","n":6,"at":"line","r":10},{"op":"fx","p":"happy","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"compost","n":36,"at":"line","r":24},{"op":"sound","s":"totem","v":1.05,"pi":1.14},{"op":"area","r":25.0,"n":20},{"op":"pull","f":1.6},{"op":"eff","e":"slow","t":100,"a":2},{"op":"dmg","m":2.835},{"op":"self"},{"op":"buff","e":"regen","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.yggdrasil_legend.stage1","ops":[{"op":"fx","p":"compost","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"chime","v":1.05,"pi":1.0},{"op":"fx","p":"heart","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"compost","n":6,"at":"line","r":15},{"op":"fx","p":"compost","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"heart","n":32,"at":"line","r":30},{"op":"sound","s":"totem","v":1.15,"pi":0.95},{"op":"allies","r":31.0},{"op":"healpct","v":0.55},{"op":"cleanse"},{"op":"self"},{"op":"buff","e":"regen","t":170,"a":3},{"op":"area","r":16.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.yggdrasil_legend.stage2","ops":[{"op":"fx","p":"compost","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"chime","v":1.25,"pi":0.75},{"op":"fx","p":"heart","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"compost","n":10,"at":"line","r":20},{"op":"fx","p":"happy","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"compost","n":48,"at":"line","r":48},{"op":"fx","p":"heart","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"totem","v":1.5,"pi":0.75},{"op":"area","r":33.0,"n":25},{"op":"dmg","m":8.262},{"op":"stun","t":46},{"op":"allies","r":36.0},{"op":"healpct","v":0.6},{"op":"cleanse"},{"op":"self"},{"op":"guard","t":170},{"op":"fx","p":"heart","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"happy","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":30.0,"n":27},{"op":"dmg","m":2.6},{"op":"allies","r":36.0},{"op":"healpct","v":0.75},{"op":"cleanse"},{"op":"self"},{"op":"buff","e":"regen","t":180,"a":3},{"op":"allies","r":31.0},{"op":"healpct","v":0.28,"to":1},{"op":"cleanse","to":1},{"op":"self"},{"op":"guard","t":180},{"op":"allies","r":24.0},{"op":"healpct","v":0.14,"to":1},{"op":"fx","p":"compost","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"chime","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"allies","r":22},{"op":"healpct","v":0.24},{"op":"cleanse"},{"op":"guard","t":110}]}]〕
26. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
27. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 34. 万律自在神 御世姫命

**モブ側の動きの方向性**：光輪へ腰掛ける、逆さに浮く、絵を描くなどの小さな遊戯動作。。

### 万律自在の神楽鈴 — 討伐武器（メイン／武器欄） (`miyohime_weapon`)

**現行パラメータ**：rank=1、damage登録値=578.5、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（5命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"cleanse"}` — 状態異常解除〔〕
03. `{"op":"adapt","t":40}` — adapt〔t=40〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（7命令）**：

01. `{"op":"chance","p":0.35,"ops":[{"op":"victim"},{"op":"each","ops":[{"op":"launch","f":2.0},{"op":"freeze","t":200},{"op":"stun","t":60}]}]}` — 抽選〔p=0.35, ops=[{"op":"victim"},{"op":"each","ops":[{"op":"launch","f":2.0},{"op":"freeze","t":200},{"op":"stun","t":60}]}]〕
02. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"nausea","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"nausea","t":90,"a":0}]〕
03. `{"op":"chance","p":0.515,"ops":[{"op":"victim"},{"op":"fx","p":"firework","n":15,"at":"t","s":0.24},{"op":"mark","t":180,"x":2.07},{"op":"eff","e":"levitate","t":28,"a":0}]}` — 抽選〔p=0.515, ops=[{"op":"victim"},{"op":"fx","p":"firework","n":15,"at":"t","s":0.24},{"op":"mark","t":180,"x":2.07},{"op":"eff","e":"levitate","t":28,"a":0}]〕
04. `{"op":"chance","p":0.231,"ops":[{"op":"victim"},{"op":"dmg","m":0.305}]}` — 抽選〔p=0.231, ops=[{"op":"victim"},{"op":"dmg","m":0.305}]〕
05. `{"op":"chance","p":0.104,"ops":[{"op":"victim"},{"op":"fx","p":"firework","n":8,"at":"t","s":0.25},{"op":"eff","e":"nausea","t":60,"a":0}]}` — 抽選〔p=0.104, ops=[{"op":"victim"},{"op":"fx","p":"firework","n":8,"at":"t","s":0.25},{"op":"eff","e":"nausea","t":60,"a":0}]〕
06. `{"op":"chance","p":0.24,"ops":[{"op":"victim"},{"op":"fx","p":"firework","n":14,"at":"t","s":0.28},{"op":"eff","e":"fatigue","t":110,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.24, ops=[{"op":"victim"},{"op":"fx","p":"firework","n":14,"at":"t","s":0.28},{"op":"eff","e":"fatigue","t":110,"a":124},{"op":"mark","t":100,"x":2.15}]〕
07. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"firework","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"firework","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":65,"a":14}]〕

**権能発動時の命令（26命令）**：

01. `{"op":"fx","p":"firework","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="firework", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"firework","n":4,"at":"self","s":0.7}` — 粒子演出〔p="firework", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"firework","n":40,"at":"self","s":1.5}` — 粒子演出〔p="firework", n=40, at="self", s=1.5〕
04. `{"op":"fx","p":"end_rod","n":30,"at":"self"}` — 粒子演出〔p="end_rod", n=30, at="self"〕
05. `{"op":"sound","s":"spell","v":1.0,"pi":0.8}` — 効果音〔s="spell", v=1.0, pi=0.8〕
06. `{"op":"area","r":24,"n":36}` — 円形対象の取得〔r=24, n=36〕
07. `{"op":"each","ops":[{"op":"launch","f":3.0},{"op":"slam","f":4.0},{"op":"freeze","t":400},{"op":"stun","t":65},{"op":"eff","e":"slow","t":600,"a":9},{"op":"eff","e":"levitate","t":200,"a":4}]}` — each〔ops=[{"op":"launch","f":3.0},{"op":"slam","f":4.0},{"op":"freeze","t":400},{"op":"stun","t":65},{"op":"eff","e":"slow","t":600,"a":9},{"op":"eff","e":"levitate","t":200,"a":4}]〕
08. `{"op":"dmg","m":1.2}` — 追加攻撃〔m=1.2〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"cleanse"}` — 状態異常解除〔〕
11. `{"op":"adapt","t":600}` — adapt〔t=600〕
12. `{"op":"fx","p":"firework","n":12,"at":"t","s":0.5}` — 粒子演出〔p="firework", n=12, at="t", s=0.5〕
13. `{"op":"fx","p":"firework","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="firework", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"end_rod","n":36,"at":"line","r":24}` — 粒子演出〔p="end_rod", n=36, at="line", r=24〕
15. `{"op":"area","r":24.0,"n":18}` — 円形対象の取得〔r=24.0, n=18〕
16. `{"op":"eff","e":"levitate","t":70,"a":1}` — 敵への状態異常〔e="levitate", t=70, a=1〕
17. `{"op":"stun","t":30}` — 行動停止〔t=30〕
18. `{"op":"fx","p":"end_rod","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="end_rod", n=16, at="ring", r=5.0〕
19. `{"op":"sound","s":"spell","v":0.75,"pi":1.15}` — 効果音〔s="spell", v=0.75, pi=1.15〕
20. `{"op":"area","r":9,"n":8}` — 円形対象の取得〔r=9, n=8〕
21. `{"op":"dmg","m":0.9}` — 追加攻撃〔m=0.9〕
22. `{"op":"eff","e":"levitate","t":65,"a":0}` — 敵への状態異常〔e="levitate", t=65, a=0〕
23. `{"op":"fx","p":"firework","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="firework", n=24, at="ring", r=4.5, y=0.6〕
24. `{"op":"sound","s":"chime","v":0.8,"pi":0.8}` — 効果音〔s="chime", v=0.8, pi=0.8〕
25. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
26. `{"op":"eff","e":"fatigue","t":110,"a":124}` — 敵への状態異常〔e="fatigue", t=110, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 極彩法則の結晶杖 — 神威触媒（Curios relic_focus） (`miyohime_focus`)

**現行パラメータ**：rank=2、damage登録値=77.8734、relics側CD=155tick、art側CD=155tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"night","t":300,"a":0}` — 強化〔e="night", t=300, a=0〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"luck","t":45,"a":0}` — 強化〔e="luck", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"luck","t":45,"a":2}` — 強化〔e="luck", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"luck","t":42,"a":2}` — 強化〔e="luck", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（41命令）**：

01. `{"op":"fx","p":"firework","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="firework", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"firework","n":6,"at":"self","s":0.7}` — 粒子演出〔p="firework", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"firework","n":40,"at":"self","s":1.5}` — 粒子演出〔p="firework", n=40, at="self", s=1.5〕
04. `{"op":"fx","p":"end_rod","n":30,"at":"self"}` — 粒子演出〔p="end_rod", n=30, at="self"〕
05. `{"op":"sound","s":"spell","v":1.0,"pi":0.8}` — 効果音〔s="spell", v=1.0, pi=0.8〕
06. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.miyohime_focus.say0","ops":[{"op":"fx","p":"firework","n":18,"at":"ring","r":6}]},{"say":"relic_art.oror_supreme_bosses.miyohime_focus.say1","ops":[{"op":"fx","p":"firework","n":18,"at":"ring","r":6}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.miyohime_focus.say0","ops":[{"op":"fx","p":"firework","n":18,"at":"ring","r":6}]},{"say":"relic_art.oror_supreme_bosses.miyohime_focus.say1","ops":[{"op":"fx","p":"firework","n":18,"at":"ring","r":6}]}]〕
07. `{"op":"area","r":32,"n":36}` — 円形対象の取得〔r=32, n=36〕
08. `{"op":"eff","e":"levitate","t":200,"a":4}` — 敵への状態異常〔e="levitate", t=200, a=4〕
09. `{"op":"stun","t":90}` — 行動停止〔t=90〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"luck","t":150,"a":1}` — 強化〔e="luck", t=150, a=1〕
13. `{"op":"fx","p":"end_rod","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="end_rod", n=50, at="ring", r=8.0, y=0.6〕
14. `{"op":"fx","p":"happy","n":32,"at":"line","r":30}` — 粒子演出〔p="happy", n=32, at="line", r=30〕
15. `{"op":"sound","s":"totem","v":1.15,"pi":0.95}` — 効果音〔s="totem", v=1.15, pi=0.95〕
16. `{"op":"area","r":26.0,"n":20}` — 円形対象の取得〔r=26.0, n=20〕
17. `{"op":"strip"}` — 強化解除〔〕
18. `{"op":"dmg","m":2.5}` — 追加攻撃〔m=2.5〕
19. `{"op":"eff","e":"slow","t":110,"a":2}` — 敵への状態異常〔e="slow", t=110, a=2〕
20. `{"op":"self"}` — 対象を自分へ〔〕
21. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
22. `{"op":"buff","e":"luck","t":150,"a":3}` — 強化〔e="luck", t=150, a=3〕
23. `{"op":"fx","p":"firework","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="firework", n=24, at="ring", r=12, y=0.5〕
24. `{"op":"sound","s":"chime","v":0.85,"pi":1.11}` — 効果音〔s="chime", v=0.85, pi=1.11〕
25. `{"op":"area","r":16.0,"n":12}` — 円形対象の取得〔r=16.0, n=12〕
26. `{"op":"dmg","m":0.8}` — 追加攻撃〔m=0.8〕
27. `{"op":"eff","e":"levitate","t":120,"a":1}` — 敵への状態異常〔e="levitate", t=120, a=1〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"buff","e":"luck","t":200,"a":3}` — 強化〔e="luck", t=200, a=3〕
30. `{"op":"area","r":16,"n":8}` — 円形対象の取得〔r=16, n=8〕
31. `{"op":"eff","e":"levitate","t":100,"a":1}` — 敵への状態異常〔e="levitate", t=100, a=1〕
32. `{"op":"fx","p":"firework","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="firework", n=24, at="ring", r=5.5, y=0.7〕
33. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
34. `{"op":"eff","e":"fatigue","t":148,"a":123}` — 敵への状態異常〔e="fatigue", t=148, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"buff","e":"luck","t":100,"a":123}` — 強化〔e="luck", t=100, a=123〕
37. `{"op":"fx","p":"firework","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="firework", n=16, at="ring", r=3.7, y=0.55〕
38. `{"op":"self"}` — 対象を自分へ〔〕
39. `{"op":"cleanse"}` — 状態異常解除〔〕
40. `{"op":"guard","t":100}` — 防御〔t=100〕
41. `{"op":"reflect","t":100,"r":9}` — 反射〔t=100, r=9〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 干渉不成立の神冠 — 神格装飾品（Curios relic_charm） (`miyohime_charm`)

**現行パラメータ**：rank=1、damage登録値=77.8734、relics側CD=185tick、art側CD=185tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（13命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"cleanse"}` — 状態異常解除〔〕
03. `{"op":"reflect","t":25,"r":6}` — 反射〔t=25, r=6〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"luck","t":45,"a":0}` — 強化〔e="luck", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
09. `{"op":"buff","e":"luck","t":45,"a":1}` — 強化〔e="luck", t=45, a=1〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"luck","t":42,"a":2}` — 強化〔e="luck", t=42, a=2〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"resist","t":48,"a":3}` — 強化〔e="resist", t=48, a=3〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（38命令）**：

01. `{"op":"fx","p":"firework","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="firework", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"firework","n":4,"at":"self","s":0.7}` — 粒子演出〔p="firework", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"firework","n":40,"at":"self","s":1.5}` — 粒子演出〔p="firework", n=40, at="self", s=1.5〕
04. `{"op":"fx","p":"end_rod","n":30,"at":"self"}` — 粒子演出〔p="end_rod", n=30, at="self"〕
05. `{"op":"sound","s":"spell","v":1.0,"pi":0.8}` — 効果音〔s="spell", v=1.0, pi=0.8〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"guard","t":180}` — 防御〔t=180〕
08. `{"op":"cleanse"}` — 状態異常解除〔〕
09. `{"op":"erase","r":32}` — erase〔r=32〕
10. `{"op":"reflect","t":200,"r":16}` — 反射〔t=200, r=16〕
11. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"luck","t":210,"a":1}` — 強化〔e="luck", t=210, a=1〕
14. `{"op":"fx","p":"firework","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="firework", n=46, at="ring", r=5.5, y=0.25〕
15. `{"op":"fx","p":"end_rod","n":36,"at":"line","r":24}` — 粒子演出〔p="end_rod", n=36, at="line", r=24〕
16. `{"op":"sound","s":"totem","v":1.05,"pi":1.14}` — 効果音〔s="totem", v=1.05, pi=1.14〕
17. `{"op":"self"}` — 対象を自分へ〔〕
18. `{"op":"guard","t":95}` — 防御〔t=95〕
19. `{"op":"self"}` — 対象を自分へ〔〕
20. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
21. `{"op":"cleanse"}` — 状態異常解除〔〕
22. `{"op":"buff","e":"luck","t":180,"a":3}` — 強化〔e="luck", t=180, a=3〕
23. `{"op":"guard","t":95}` — 防御〔t=95〕
24. `{"op":"fx","p":"firework","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="firework", n=30, at="ring", r=4.0, y=0.7〕
25. `{"op":"sound","s":"chime","v":0.8,"pi":1.1}` — 効果音〔s="chime", v=0.8, pi=1.1〕
26. `{"op":"self"}` — 対象を自分へ〔〕
27. `{"op":"buff","e":"luck","t":260,"a":4}` — 強化〔e="luck", t=260, a=4〕
28. `{"op":"guard","t":140}` — 防御〔t=140〕
29. `{"op":"self"}` — 対象を自分へ〔〕
30. `{"op":"buff","e":"resist","t":240,"a":2}` — 強化〔e="resist", t=240, a=2〕
31. `{"op":"fx","p":"firework","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="firework", n=20, at="ring", r=4, y=0.4〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"buff","e":"luck","t":160,"a":123}` — 強化〔e="luck", t=160, a=123〕
34. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
35. `{"op":"eff","e":"fatigue","t":110,"a":123}` — 敵への状態異常〔e="fatigue", t=110, a=123〕
36. `{"op":"self"}` — 対象を自分へ〔〕
37. `{"op":"guard","t":95}` — 防御〔t=95〕
38. `{"op":"cleanse"}` — 状態異常解除〔〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 理外自由・万律自在神璽 — 超越神器（武器欄） (`miyohime_legend`)

**現行パラメータ**：rank=3、damage登録値=1157.875、relics側CD=340tick、art側CD=340tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10、minecraft:luck_of_the_sea:25。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"cleanse"}` — 状態異常解除〔〕
06. `{"op":"reflect","t":25,"r":8}` — 反射〔t=25, r=8〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
09. `{"op":"buff","e":"luck","t":45,"a":3}` — 強化〔e="luck", t=45, a=3〕
10. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（8命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"each","ops":[{"op":"launch","f":3.0},{"op":"slam","f":4.0},{"op":"freeze","t":400},{"op":"stun","t":105},{"op":"eff","e":"slow","t":600,"a":9},{"op":"eff","e":"levitate","t":200,"a":4}]}` — each〔ops=[{"op":"launch","f":3.0},{"op":"slam","f":4.0},{"op":"freeze","t":400},{"op":"stun","t":105},{"op":"eff","e":"slow","t":600,"a":9},{"op":"eff","e":"levitate","t":200,"a":4}]〕
03. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"nausea","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"nausea","t":160,"a":1}]〕
04. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"firework","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"firework","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
05. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"levitate","t":135,"a":2},{"op":"fx","p":"firework","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"levitate","t":135,"a":2},{"op":"fx","p":"firework","n":10,"at":"t","s":0.35}]〕
06. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
07. `{"op":"chance","p":0.375,"ops":[{"op":"victim"},{"op":"fx","p":"firework","n":20,"at":"t","s":0.33},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.375, ops=[{"op":"victim"},{"op":"fx","p":"firework","n":20,"at":"t","s":0.33},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":160,"x":2.5}]〕
08. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"firework","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"firework","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]〕

**権能発動時の命令（25命令）**：

01. `{"op":"fx","p":"firework","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="firework", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"firework","n":4,"at":"self","s":0.7}` — 粒子演出〔p="firework", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"firework","n":40,"at":"self","s":1.5}` — 粒子演出〔p="firework", n=40, at="self", s=1.5〕
04. `{"op":"fx","p":"end_rod","n":30,"at":"self"}` — 粒子演出〔p="end_rod", n=30, at="self"〕
05. `{"op":"sound","s":"spell","v":1.0,"pi":0.8}` — 効果音〔s="spell", v=1.0, pi=0.8〕
06. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
07. `{"op":"each","ops":[{"op":"launch","f":3.0},{"op":"slam","f":4.0},{"op":"freeze","t":400},{"op":"stun","t":105},{"op":"eff","e":"slow","t":600,"a":9},{"op":"eff","e":"levitate","t":200,"a":4}]}` — each〔ops=[{"op":"launch","f":3.0},{"op":"slam","f":4.0},{"op":"freeze","t":400},{"op":"stun","t":105},{"op":"eff","e":"slow","t":600,"a":9},{"op":"eff","e":"levitate","t":200,"a":4}]〕
08. `{"op":"dmg","m":3.36}` — 追加攻撃〔m=3.36〕
09. `{"op":"stun","t":105}` — 行動停止〔t=105〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"undying","t":180}` — 死亡防護〔t=180〕
12. `{"op":"guard","t":100}` — 防御〔t=100〕
13. `{"op":"adapt","t":2400}` — adapt〔t=2400〕
14. `{"op":"buff","e":"strength","t":1200,"a":12}` — 強化〔e="strength", t=1200, a=12〕
15. `{"op":"erase","r":64}` — erase〔r=64〕
16. `{"op":"fx","p":"firework","n":12,"at":"t","s":0.5}` — 粒子演出〔p="firework", n=12, at="t", s=0.5〕
17. `{"op":"area","r":26,"n":24}` — 円形対象の取得〔r=26, n=24〕
18. `{"op":"stun","t":45}` — 行動停止〔t=45〕
19. `{"op":"fx","p":"end_rod","n":35,"at":"ring","r":9}` — 粒子演出〔p="end_rod", n=35, at="ring", r=9〕
20. `{"op":"fx","p":"end_rod","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="end_rod", n=50, at="ring", r=8.0, y=0.6〕
21. `{"op":"fx","p":"happy","n":32,"at":"line","r":30}` — 粒子演出〔p="happy", n=32, at="line", r=30〕
22. `{"op":"sound","s":"totem","v":1.15,"pi":0.95}` — 効果音〔s="totem", v=1.15, pi=0.95〕
23. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.miyohime_legend.stage0","ops":[{"op":"fx","p":"firework","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"chime","v":0.9,"pi":1.2},{"op":"fx","p":"firework","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"enchant","n":6,"at":"line","r":10},{"op":"fx","p":"firework","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"end_rod","n":36,"at":"line","r":24},{"op":"sound","s":"totem","v":1.05,"pi":1.14},{"op":"area","r":24.0,"n":18},{"op":"eff","e":"levitate","t":70,"a":1},{"op":"stun","t":30},{"op":"self"},{"op":"buff","e":"luck","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.miyohime_legend.stage1","ops":[{"op":"fx","p":"firework","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"chime","v":1.05,"pi":1.0},{"op":"fx","p":"enchant","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"firework","n":6,"at":"line","r":15},{"op":"fx","p":"end_rod","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"happy","n":32,"at":"line","r":30},{"op":"sound","s":"totem","v":1.15,"pi":0.95},{"op":"area","r":26.0,"n":20},{"op":"strip"},{"op":"dmg","m":3.625},{"op":"eff","e":"slow","t":110,"a":2},{"op":"area","r":18.0,"n":10},{"op":"eff","e":"levitate","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.miyohime_legend.stage2","ops":[{"op":"fx","p":"firework","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"chime","v":1.25,"pi":0.75},{"op":"fx","p":"enchant","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"firework","n":10,"at":"line","r":20},{"op":"fx","p":"firework","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"end_rod","n":48,"at":"line","r":48},{"op":"fx","p":"happy","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"totem","v":1.5,"pi":0.75},{"op":"area","r":35.0,"n":28},{"op":"dmg","m":9.072},{"op":"strip"},{"op":"stun","t":65},{"op":"self"},{"op":"guard","t":150},{"op":"fx","p":"happy","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"firework","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":30.0,"n":26},{"op":"dmg","m":2.7},{"op":"strip"},{"op":"stun","t":45},{"op":"self"},{"op":"buff","e":"luck","t":180,"a":4},{"op":"area","r":24.0,"n":16},{"op":"dmg","m":1.1},{"op":"eff","e":"levitate","t":160,"a":2},{"op":"self"},{"op":"buff","e":"luck","t":240,"a":4},{"op":"area","r":16,"n":8},{"op":"eff","e":"levitate","t":100,"a":1},{"op":"fx","p":"firework","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"chime","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"self"},{"op":"cleanse"},{"op":"guard","t":105},{"op":"area","r":17,"n":8},{"op":"strip"}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.miyohime_legend.stage0","ops":[{"op":"fx","p":"firework","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"chime","v":0.9,"pi":1.2},{"op":"fx","p":"firework","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"enchant","n":6,"at":"line","r":10},{"op":"fx","p":"firework","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"end_rod","n":36,"at":"line","r":24},{"op":"sound","s":"totem","v":1.05,"pi":1.14},{"op":"area","r":24.0,"n":18},{"op":"eff","e":"levitate","t":70,"a":1},{"op":"stun","t":30},{"op":"self"},{"op":"buff","e":"luck","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.miyohime_legend.stage1","ops":[{"op":"fx","p":"firework","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"chime","v":1.05,"pi":1.0},{"op":"fx","p":"enchant","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"firework","n":6,"at":"line","r":15},{"op":"fx","p":"end_rod","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"happy","n":32,"at":"line","r":30},{"op":"sound","s":"totem","v":1.15,"pi":0.95},{"op":"area","r":26.0,"n":20},{"op":"strip"},{"op":"dmg","m":3.625},{"op":"eff","e":"slow","t":110,"a":2},{"op":"area","r":18.0,"n":10},{"op":"eff","e":"levitate","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.miyohime_legend.stage2","ops":[{"op":"fx","p":"firework","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"chime","v":1.25,"pi":0.75},{"op":"fx","p":"enchant","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"firework","n":10,"at":"line","r":20},{"op":"fx","p":"firework","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"end_rod","n":48,"at":"line","r":48},{"op":"fx","p":"happy","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"totem","v":1.5,"pi":0.75},{"op":"area","r":35.0,"n":28},{"op":"dmg","m":9.072},{"op":"strip"},{"op":"stun","t":65},{"op":"self"},{"op":"guard","t":150},{"op":"fx","p":"happy","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"firework","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":30.0,"n":26},{"op":"dmg","m":2.7},{"op":"strip"},{"op":"stun","t":45},{"op":"self"},{"op":"buff","e":"luck","t":180,"a":4},{"op":"area","r":24.0,"n":16},{"op":"dmg","m":1.1},{"op":"eff","e":"levitate","t":160,"a":2},{"op":"self"},{"op":"buff","e":"luck","t":240,"a":4},{"op":"area","r":16,"n":8},{"op":"eff","e":"levitate","t":100,"a":1},{"op":"fx","p":"firework","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"chime","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"self"},{"op":"cleanse"},{"op":"guard","t":105},{"op":"area","r":17,"n":8},{"op":"strip"}]}]〕
24. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
25. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 35. 無垢なる全能

**モブ側の動きの方向性**：幼い手遊びだけで他者の姿や行動を変える。。

### 無垢なる全能のぬいぐるみ — 討伐武器（メイン／武器欄） (`innocence_weapon`)

**現行パラメータ**：rank=1、damage登録値=578.5、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（5命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"slowfall","t":40,"a":0}` — 強化〔e="slowfall", t=40, a=0〕
03. `{"op":"buff","e":"luck","t":40,"a":2}` — 強化〔e="luck", t=40, a=2〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（7命令）**：

01. `{"op":"chance","p":0.3,"ops":[{"op":"victim"},{"op":"transmute"}]}` — 抽選〔p=0.3, ops=[{"op":"victim"},{"op":"transmute"}]〕
02. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"slow","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"slow","t":90,"a":0}]〕
03. `{"op":"chance","p":0.54,"ops":[{"op":"victim"},{"op":"fx","p":"heart","n":17,"at":"t","s":0.24},{"op":"mark","t":200,"x":2.21},{"op":"eff","e":"slow","t":103,"a":0}]}` — 抽選〔p=0.54, ops=[{"op":"victim"},{"op":"fx","p":"heart","n":17,"at":"t","s":0.24},{"op":"mark","t":200,"x":2.21},{"op":"eff","e":"slow","t":103,"a":0}]〕
04. `{"op":"chance","p":0.258,"ops":[{"op":"victim"},{"op":"dmg","m":0.34}]}` — 抽選〔p=0.258, ops=[{"op":"victim"},{"op":"dmg","m":0.34}]〕
05. `{"op":"chance","p":0.123,"ops":[{"op":"victim"},{"op":"fx","p":"heart","n":8,"at":"t","s":0.25},{"op":"eff","e":"levitate","t":18,"a":0}]}` — 抽選〔p=0.123, ops=[{"op":"victim"},{"op":"fx","p":"heart","n":8,"at":"t","s":0.25},{"op":"eff","e":"levitate","t":18,"a":0}]〕
06. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"fx","p":"happy","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"fx","p":"happy","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]〕
07. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"happy","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"wither","t":48,"a":5}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"happy","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"wither","t":48,"a":5}]〕

**権能発動時の命令（27命令）**：

01. `{"op":"fx","p":"happy","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="happy", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"happy","n":4,"at":"self","s":0.7}` — 粒子演出〔p="happy", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"heart","n":10,"at":"self"}` — 粒子演出〔p="heart", n=10, at="self"〕
04. `{"op":"fx","p":"firework","n":30,"at":"self"}` — 粒子演出〔p="firework", n=30, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":2.0}` — 効果音〔s="chime", v=1.0, pi=2.0〕
06. `{"op":"area","r":24,"n":36}` — 円形対象の取得〔r=24, n=36〕
07. `{"op":"transmute"}` — transmute〔〕
08. `{"op":"area","r":24,"n":36}` — 円形対象の取得〔r=24, n=36〕
09. `{"op":"eff","e":"levitate","t":200,"a":2}` — 敵への状態異常〔e="levitate", t=200, a=2〕
10. `{"op":"stun","t":65}` — 行動停止〔t=65〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"cleanse"}` — 状態異常解除〔〕
13. `{"op":"fx","p":"heart","n":12,"at":"t","s":0.5}` — 粒子演出〔p="heart", n=12, at="t", s=0.5〕
14. `{"op":"fx","p":"happy","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="happy", n=46, at="ring", r=5.5, y=0.25〕
15. `{"op":"fx","p":"heart","n":36,"at":"line","r":24}` — 粒子演出〔p="heart", n=36, at="line", r=24〕
16. `{"op":"area","r":21.0,"n":18}` — 円形対象の取得〔r=21.0, n=18〕
17. `{"op":"stun","t":43}` — 行動停止〔t=43〕
18. `{"op":"eff","e":"glow","t":120,"a":0}` — 敵への状態異常〔e="glow", t=120, a=0〕
19. `{"op":"fx","p":"happy","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="happy", n=16, at="ring", r=5.0〕
20. `{"op":"sound","s":"spell","v":0.75,"pi":1.15}` — 効果音〔s="spell", v=0.75, pi=1.15〕
21. `{"op":"area","r":9,"n":8}` — 円形対象の取得〔r=9, n=8〕
22. `{"op":"dmg","m":0.9}` — 追加攻撃〔m=0.9〕
23. `{"op":"eff","e":"slow","t":65,"a":0}` — 敵への状態異常〔e="slow", t=65, a=0〕
24. `{"op":"fx","p":"happy","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="happy", n=24, at="ring", r=4.5, y=0.6〕
25. `{"op":"sound","s":"chime","v":0.8,"pi":0.8}` — 効果音〔s="chime", v=0.8, pi=0.8〕
26. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
27. `{"op":"eff","e":"weakness","t":100,"a":124}` — 敵への状態異常〔e="weakness", t=100, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 虹眼全能の玩具箱 — 神威触媒（Curios relic_focus） (`innocence_focus`)

**現行パラメータ**：rank=2、damage登録値=81.972、relics側CD=150tick、art側CD=150tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"slowfall","t":40,"a":0}` — 強化〔e="slowfall", t=40, a=0〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"jump","t":45,"a":0}` — 強化〔e="jump", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"luck","t":45,"a":2}` — 強化〔e="luck", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"absorb","t":42,"a":2}` — 強化〔e="absorb", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（42命令）**：

01. `{"op":"fx","p":"happy","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="happy", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"happy","n":6,"at":"self","s":0.7}` — 粒子演出〔p="happy", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"heart","n":10,"at":"self"}` — 粒子演出〔p="heart", n=10, at="self"〕
04. `{"op":"fx","p":"firework","n":30,"at":"self"}` — 粒子演出〔p="firework", n=30, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":2.0}` — 効果音〔s="chime", v=1.0, pi=2.0〕
06. `{"op":"area","r":32,"n":36}` — 円形対象の取得〔r=32, n=36〕
07. `{"op":"eff","e":"levitate","t":300,"a":3}` — 敵への状態異常〔e="levitate", t=300, a=3〕
08. `{"op":"stun","t":90}` — 行動停止〔t=90〕
09. `{"op":"dmg","m":1.5}` — 追加攻撃〔m=1.5〕
10. `{"op":"allies","r":24}` — 味方対象〔r=24〕
11. `{"op":"healpct","v":0.4,"to":1}` — 最大HP割合回復〔v=0.4, to=1〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"jump","t":150,"a":1}` — 強化〔e="jump", t=150, a=1〕
15. `{"op":"fx","p":"heart","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="heart", n=50, at="ring", r=8.0, y=0.6〕
16. `{"op":"fx","p":"firework","n":32,"at":"line","r":30}` — 粒子演出〔p="firework", n=32, at="line", r=30〕
17. `{"op":"sound","s":"totem","v":1.15,"pi":0.95}` — 効果音〔s="totem", v=1.15, pi=0.95〕
18. `{"op":"area","r":24.0,"n":20}` — 円形対象の取得〔r=24.0, n=20〕
19. `{"op":"eff","e":"levitate","t":80,"a":1}` — 敵への状態異常〔e="levitate", t=80, a=1〕
20. `{"op":"dmg","m":2.6}` — 追加攻撃〔m=2.6〕
21. `{"op":"self"}` — 対象を自分へ〔〕
22. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
23. `{"op":"buff","e":"luck","t":150,"a":3}` — 強化〔e="luck", t=150, a=3〕
24. `{"op":"fx","p":"happy","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="happy", n=24, at="ring", r=12, y=0.5〕
25. `{"op":"sound","s":"chime","v":0.85,"pi":1.18}` — 効果音〔s="chime", v=0.85, pi=1.18〕
26. `{"op":"area","r":18.0,"n":12}` — 円形対象の取得〔r=18.0, n=12〕
27. `{"op":"dmg","m":0.8}` — 追加攻撃〔m=0.8〕
28. `{"op":"eff","e":"nausea","t":140,"a":1}` — 敵への状態異常〔e="nausea", t=140, a=1〕
29. `{"op":"self"}` — 対象を自分へ〔〕
30. `{"op":"buff","e":"absorb","t":220,"a":3}` — 強化〔e="absorb", t=220, a=3〕
31. `{"op":"area","r":18,"n":8}` — 円形対象の取得〔r=18, n=8〕
32. `{"op":"eff","e":"nausea","t":100,"a":1}` — 敵への状態異常〔e="nausea", t=100, a=1〕
33. `{"op":"fx","p":"happy","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="happy", n=24, at="ring", r=5.5, y=0.7〕
34. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
35. `{"op":"eff","e":"weakness","t":135,"a":123}` — 敵への状態異常〔e="weakness", t=135, a=123〕
36. `{"op":"self"}` — 対象を自分へ〔〕
37. `{"op":"buff","e":"absorb","t":200,"a":15}` — 強化〔e="absorb", t=200, a=15〕
38. `{"op":"fx","p":"happy","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="happy", n=16, at="ring", r=3.7, y=0.55〕
39. `{"op":"self"}` — 対象を自分へ〔〕
40. `{"op":"cleanse"}` — 状態異常解除〔〕
41. `{"op":"guard","t":100}` — 防御〔t=100〕
42. `{"op":"reflect","t":100,"r":9}` — 反射〔t=100, r=9〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 死の取消の髪飾り — 神格装飾品（Curios relic_charm） (`innocence_charm`)

**現行パラメータ**：rank=1、damage登録値=81.972、relics側CD=180tick、art側CD=180tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（11命令）**：

01. `{"op":"low","pct":0.3,"ops":[{"op":"self"},{"op":"undying","t":40},{"op":"healpct","v":0.25}]}` — low〔pct=0.3, ops=[{"op":"self"},{"op":"undying","t":40},{"op":"healpct","v":0.25}]〕
02. `{"op":"self"}` — 対象を自分へ〔〕
03. `{"op":"buff","e":"jump","t":45,"a":0}` — 強化〔e="jump", t=45, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
06. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
07. `{"op":"buff","e":"luck","t":45,"a":1}` — 強化〔e="luck", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"absorb","t":42,"a":2}` — 強化〔e="absorb", t=42, a=2〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"resist","t":48,"a":3}` — 強化〔e="resist", t=48, a=3〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（39命令）**：

01. `{"op":"fx","p":"happy","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="happy", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"happy","n":4,"at":"self","s":0.7}` — 粒子演出〔p="happy", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"heart","n":10,"at":"self"}` — 粒子演出〔p="heart", n=10, at="self"〕
04. `{"op":"fx","p":"firework","n":30,"at":"self"}` — 粒子演出〔p="firework", n=30, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":2.0}` — 効果音〔s="chime", v=1.0, pi=2.0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"undying","t":100}` — 死亡防護〔t=100〕
08. `{"op":"healpct","v":0.25}` — 最大HP割合回復〔v=0.25〕
09. `{"op":"cleanse"}` — 状態異常解除〔〕
10. `{"op":"allies","r":16}` — 味方対象〔r=16〕
11. `{"op":"healpct","v":0.25,"to":1}` — 最大HP割合回復〔v=0.25, to=1〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"jump","t":210,"a":1}` — 強化〔e="jump", t=210, a=1〕
15. `{"op":"fx","p":"happy","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="happy", n=46, at="ring", r=5.5, y=0.25〕
16. `{"op":"fx","p":"heart","n":36,"at":"line","r":24}` — 粒子演出〔p="heart", n=36, at="line", r=24〕
17. `{"op":"sound","s":"totem","v":1.05,"pi":1.14}` — 効果音〔s="totem", v=1.05, pi=1.14〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"guard","t":95}` — 防御〔t=95〕
20. `{"op":"self"}` — 対象を自分へ〔〕
21. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
22. `{"op":"cleanse"}` — 状態異常解除〔〕
23. `{"op":"buff","e":"luck","t":180,"a":3}` — 強化〔e="luck", t=180, a=3〕
24. `{"op":"guard","t":95}` — 防御〔t=95〕
25. `{"op":"fx","p":"happy","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="happy", n=30, at="ring", r=4.0, y=0.7〕
26. `{"op":"sound","s":"chime","v":0.8,"pi":1.1}` — 効果音〔s="chime", v=0.8, pi=1.1〕
27. `{"op":"self"}` — 対象を自分へ〔〕
28. `{"op":"buff","e":"absorb","t":280,"a":4}` — 強化〔e="absorb", t=280, a=4〕
29. `{"op":"guard","t":155}` — 防御〔t=155〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"absorb","t":240,"a":3}` — 強化〔e="absorb", t=240, a=3〕
32. `{"op":"fx","p":"happy","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="happy", n=20, at="ring", r=4, y=0.4〕
33. `{"op":"self"}` — 対象を自分へ〔〕
34. `{"op":"buff","e":"absorb","t":200,"a":15}` — 強化〔e="absorb", t=200, a=15〕
35. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
36. `{"op":"eff","e":"weakness","t":100,"a":123}` — 敵への状態異常〔e="weakness", t=100, a=123〕
37. `{"op":"self"}` — 対象を自分へ〔〕
38. `{"op":"guard","t":95}` — 防御〔t=95〕
39. `{"op":"cleanse"}` — 状態異常解除〔〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 無垢創世・全能の遊び場 — 超越神器（武器欄） (`innocence_legend`)

**現行パラメータ**：rank=3、damage登録値=1157.875、relics側CD=335tick、art側CD=335tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"cleanse"}` — 状態異常解除〔〕
06. `{"op":"low","pct":0.4,"ops":[{"op":"self"},{"op":"undying","t":40}]}` — low〔pct=0.4, ops=[{"op":"self"},{"op":"undying","t":40}]〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
09. `{"op":"buff","e":"luck","t":45,"a":3}` — 強化〔e="luck", t=45, a=3〕
10. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（7命令）**：

01. `{"op":"chance","p":0.5,"ops":[{"op":"victim"},{"op":"transmute"}]}` — 抽選〔p=0.5, ops=[{"op":"victim"},{"op":"transmute"}]〕
02. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"slow","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"slow","t":160,"a":1}]〕
03. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"happy","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"happy","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
04. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"levitate","t":135,"a":2},{"op":"fx","p":"happy","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"levitate","t":135,"a":2},{"op":"fx","p":"happy","n":10,"at":"t","s":0.35}]〕
05. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
06. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"fx","p":"happy","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"fx","p":"happy","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]〕
07. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"happy","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"wither","t":78,"a":7}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"happy","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"wither","t":78,"a":7}]〕

**権能発動時の命令（26命令）**：

01. `{"op":"fx","p":"happy","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="happy", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"happy","n":4,"at":"self","s":0.7}` — 粒子演出〔p="happy", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"heart","n":10,"at":"self"}` — 粒子演出〔p="heart", n=10, at="self"〕
04. `{"op":"fx","p":"firework","n":30,"at":"self"}` — 粒子演出〔p="firework", n=30, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":2.0}` — 効果音〔s="chime", v=1.0, pi=2.0〕
06. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
07. `{"op":"transmute"}` — transmute〔〕
08. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
09. `{"op":"eff","e":"levitate","t":400,"a":5}` — 敵への状態異常〔e="levitate", t=400, a=5〕
10. `{"op":"stun","t":105}` — 行動停止〔t=105〕
11. `{"op":"dmg","m":3.36}` — 追加攻撃〔m=3.36〕
12. `{"op":"allies","r":48}` — 味方対象〔r=48〕
13. `{"op":"undying","t":180,"to":1}` — 死亡防護〔t=180, to=1〕
14. `{"op":"healpct","v":0.6,"to":1}` — 最大HP割合回復〔v=0.6, to=1〕
15. `{"op":"self"}` — 対象を自分へ〔〕
16. `{"op":"guard","t":180}` — 防御〔t=180〕
17. `{"op":"fx","p":"heart","n":12,"at":"t","s":0.5}` — 粒子演出〔p="heart", n=12, at="t", s=0.5〕
18. `{"op":"area","r":26,"n":24}` — 円形対象の取得〔r=26, n=24〕
19. `{"op":"stun","t":45}` — 行動停止〔t=45〕
20. `{"op":"fx","p":"end_rod","n":35,"at":"ring","r":9}` — 粒子演出〔p="end_rod", n=35, at="ring", r=9〕
21. `{"op":"fx","p":"heart","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="heart", n=50, at="ring", r=8.0, y=0.6〕
22. `{"op":"fx","p":"firework","n":32,"at":"line","r":30}` — 粒子演出〔p="firework", n=32, at="line", r=30〕
23. `{"op":"sound","s":"totem","v":1.15,"pi":0.95}` — 効果音〔s="totem", v=1.15, pi=0.95〕
24. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.innocence_legend.stage0","ops":[{"op":"fx","p":"happy","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"chime","v":0.9,"pi":1.2},{"op":"fx","p":"happy","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"firework","n":6,"at":"line","r":10},{"op":"fx","p":"happy","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"heart","n":36,"at":"line","r":24},{"op":"sound","s":"totem","v":1.05,"pi":1.14},{"op":"area","r":21.0,"n":18},{"op":"stun","t":43},{"op":"eff","e":"glow","t":120,"a":0},{"op":"self"},{"op":"buff","e":"absorb","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.innocence_legend.stage1","ops":[{"op":"fx","p":"happy","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"chime","v":1.05,"pi":1.0},{"op":"fx","p":"firework","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"happy","n":6,"at":"line","r":15},{"op":"fx","p":"heart","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"firework","n":32,"at":"line","r":30},{"op":"sound","s":"totem","v":1.15,"pi":0.95},{"op":"area","r":24.0,"n":20},{"op":"eff","e":"levitate","t":80,"a":1},{"op":"dmg","m":3.77},{"op":"area","r":20.0,"n":10},{"op":"eff","e":"nausea","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.innocence_legend.stage2","ops":[{"op":"fx","p":"happy","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"chime","v":1.25,"pi":0.75},{"op":"fx","p":"firework","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"happy","n":10,"at":"line","r":20},{"op":"fx","p":"happy","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"heart","n":48,"at":"line","r":48},{"op":"fx","p":"firework","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"totem","v":1.5,"pi":0.75},{"op":"area","r":32.0,"n":28},{"op":"dmg","m":8.91},{"op":"stun","t":65},{"op":"knock","f":3.0},{"op":"self"},{"op":"buff","e":"luck","t":155,"a":3},{"op":"fx","p":"firework","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"happy","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":28.0,"n":26},{"op":"dmg","m":2.5},{"op":"stun","t":45},{"op":"self"},{"op":"buff","e":"absorb","t":175,"a":5},{"op":"area","r":27.0,"n":16},{"op":"dmg","m":1.2},{"op":"eff","e":"nausea","t":160,"a":2},{"op":"self"},{"op":"buff","e":"absorb","t":240,"a":4},{"op":"area","r":18,"n":8},{"op":"eff","e":"levitate","t":100,"a":1},{"op":"fx","p":"happy","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"chime","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"self"},{"op":"cleanse"},{"op":"guard","t":105},{"op":"area","r":17,"n":8},{"op":"strip"}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.innocence_legend.stage0","ops":[{"op":"fx","p":"happy","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"chime","v":0.9,"pi":1.2},{"op":"fx","p":"happy","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"firework","n":6,"at":"line","r":10},{"op":"fx","p":"happy","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"heart","n":36,"at":"line","r":24},{"op":"sound","s":"totem","v":1.05,"pi":1.14},{"op":"area","r":21.0,"n":18},{"op":"stun","t":43},{"op":"eff","e":"glow","t":120,"a":0},{"op":"self"},{"op":"buff","e":"absorb","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.innocence_legend.stage1","ops":[{"op":"fx","p":"happy","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"chime","v":1.05,"pi":1.0},{"op":"fx","p":"firework","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"happy","n":6,"at":"line","r":15},{"op":"fx","p":"heart","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"firework","n":32,"at":"line","r":30},{"op":"sound","s":"totem","v":1.15,"pi":0.95},{"op":"area","r":24.0,"n":20},{"op":"eff","e":"levitate","t":80,"a":1},{"op":"dmg","m":3.77},{"op":"area","r":20.0,"n":10},{"op":"eff","e":"nausea","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.innocence_legend.stage2","ops":[{"op":"fx","p":"happy","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"chime","v":1.25,"pi":0.75},{"op":"fx","p":"firework","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"happy","n":10,"at":"line","r":20},{"op":"fx","p":"happy","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"heart","n":48,"at":"line","r":48},{"op":"fx","p":"firework","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"totem","v":1.5,"pi":0.75},{"op":"area","r":32.0,"n":28},{"op":"dmg","m":8.91},{"op":"stun","t":65},{"op":"knock","f":3.0},{"op":"self"},{"op":"buff","e":"luck","t":155,"a":3},{"op":"fx","p":"firework","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"happy","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":28.0,"n":26},{"op":"dmg","m":2.5},{"op":"stun","t":45},{"op":"self"},{"op":"buff","e":"absorb","t":175,"a":5},{"op":"area","r":27.0,"n":16},{"op":"dmg","m":1.2},{"op":"eff","e":"nausea","t":160,"a":2},{"op":"self"},{"op":"buff","e":"absorb","t":240,"a":4},{"op":"area","r":18,"n":8},{"op":"eff","e":"levitate","t":100,"a":1},{"op":"fx","p":"happy","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"chime","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"self"},{"op":"cleanse"},{"op":"guard","t":105},{"op":"area","r":17,"n":8},{"op":"strip"}]}]〕
25. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
26. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 36. 凄惨たる暴虐

**モブ側の動きの方向性**：全身の体重移動と肉体の反動。魔法らしい発光は極小化する。。

### 凄惨暴虐の鬼金棒 — 討伐武器（メイン／武器欄） (`brutality_weapon`)

**現行パラメータ**：rank=1、damage登録値=303.81609、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:knockback:5。

**装備中の常時命令（5命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"strength","t":40,"a":2}` — 強化〔e="strength", t=40, a=2〕
03. `{"op":"buff","e":"speed","t":40,"a":0}` — 強化〔e="speed", t=40, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（10命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"strip"}` — 強化解除〔〕
03. `{"op":"dmg","m":0.4}` — 追加攻撃〔m=0.4〕
04. `{"op":"knock","f":3.0}` — knock〔f=3.0〕
05. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"weakness","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"weakness","t":90,"a":0}]〕
06. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":9,"at":"t","s":0.24},{"op":"mark","t":120,"x":1.65},{"op":"eff","e":"weakness","t":115,"a":1}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":9,"at":"t","s":0.24},{"op":"mark","t":120,"x":1.65},{"op":"eff","e":"weakness","t":115,"a":1}]〕
07. `{"op":"chance","p":0.15,"ops":[{"op":"victim"},{"op":"dmg","m":0.2}]}` — 抽選〔p=0.15, ops=[{"op":"victim"},{"op":"dmg","m":0.2}]〕
08. `{"op":"chance","p":0.142,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":8,"at":"t","s":0.25},{"op":"knock","f":0.8}]}` — 抽選〔p=0.142, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":8,"at":"t","s":0.25},{"op":"knock","f":0.8}]〕
09. `{"op":"chance","p":0.18,"ops":[{"op":"victim"},{"op":"fx","p":"bigsmoke","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.18, ops=[{"op":"victim"},{"op":"fx","p":"bigsmoke","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]〕
10. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]〕

**権能発動時の命令（31命令）**：

01. `{"op":"fx","p":"smoke","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="smoke", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"smoke","n":4,"at":"self","s":0.7}` — 粒子演出〔p="smoke", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"explosion","n":8,"at":"self","s":1.2}` — 粒子演出〔p="explosion", n=8, at="self", s=1.2〕
04. `{"op":"fx","p":"crit","n":50,"at":"self"}` — 粒子演出〔p="crit", n=50, at="self"〕
05. `{"op":"sound","s":"anvil","v":1.0,"pi":0.6}` — 効果音〔s="anvil", v=1.0, pi=0.6〕
06. `{"op":"near","r":16,"n":3}` — near〔r=16, n=3〕
07. `{"op":"strip"}` — 強化解除〔〕
08. `{"op":"dmg","m":1.2}` — 追加攻撃〔m=1.2〕
09. `{"op":"dmg","m":1.2}` — 追加攻撃〔m=1.2〕
10. `{"op":"dmg","m":1.2}` — 追加攻撃〔m=1.2〕
11. `{"op":"dmg","m":1.2}` — 追加攻撃〔m=1.2〕
12. `{"op":"mark","t":300,"x":2.0}` — 刻印〔t=300, x=2.0〕
13. `{"op":"knock","f":5.0}` — knock〔f=5.0〕
14. `{"op":"self"}` — 対象を自分へ〔〕
15. `{"op":"buff","e":"strength","t":300,"a":8}` — 強化〔e="strength", t=300, a=8〕
16. `{"op":"cleanse"}` — 状態異常解除〔〕
17. `{"op":"fx","p":"explosion","n":12,"at":"t","s":0.5}` — 粒子演出〔p="explosion", n=12, at="t", s=0.5〕
18. `{"op":"fx","p":"crit","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="crit", n=46, at="ring", r=5.5, y=0.25〕
19. `{"op":"fx","p":"bigsmoke","n":36,"at":"line","r":24}` — 粒子演出〔p="bigsmoke", n=36, at="line", r=24〕
20. `{"op":"cone","r":14.0,"a":145.0}` — 扇形対象の取得〔r=14.0, a=145.0〕
21. `{"op":"dmg","m":4.1}` — 追加攻撃〔m=4.1〕
22. `{"op":"slam"}` — slam〔〕
23. `{"op":"fx","p":"crit","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="crit", n=16, at="ring", r=5.0〕
24. `{"op":"sound","s":"sonic","v":0.75,"pi":1.15}` — 効果音〔s="sonic", v=0.75, pi=1.15〕
25. `{"op":"cone","r":11,"a":85}` — 扇形対象の取得〔r=11, a=85〕
26. `{"op":"dmg","m":1.0}` — 追加攻撃〔m=1.0〕
27. `{"op":"eff","e":"weakness","t":65,"a":0}` — 敵への状態異常〔e="weakness", t=65, a=0〕
28. `{"op":"fx","p":"bigsmoke","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="bigsmoke", n=24, at="ring", r=4.5, y=0.6〕
29. `{"op":"sound","s":"stone","v":0.8,"pi":0.8}` — 効果音〔s="stone", v=0.8, pi=0.8〕
30. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
31. `{"op":"eff","e":"weakness","t":100,"a":124}` — 敵への状態異常〔e="weakness", t=100, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 抗理粉砕の鋼手甲 — 神威触媒（Curios relic_focus） (`brutality_focus`)

**現行パラメータ**：rank=2、damage登録値=90.1692、relics側CD=145tick、art側CD=145tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"haste","t":40,"a":2}` — 強化〔e="haste", t=40, a=2〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"strength","t":45,"a":0}` — 強化〔e="strength", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"strength","t":45,"a":2}` — 強化〔e="strength", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"strength","t":42,"a":2}` — 強化〔e="strength", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（42命令）**：

01. `{"op":"fx","p":"smoke","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="smoke", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"smoke","n":6,"at":"self","s":0.7}` — 粒子演出〔p="smoke", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"explosion","n":8,"at":"self","s":1.2}` — 粒子演出〔p="explosion", n=8, at="self", s=1.2〕
04. `{"op":"fx","p":"crit","n":50,"at":"self"}` — 粒子演出〔p="crit", n=50, at="self"〕
05. `{"op":"sound","s":"anvil","v":1.0,"pi":0.6}` — 効果音〔s="anvil", v=1.0, pi=0.6〕
06. `{"op":"area","r":20,"n":36}` — 円形対象の取得〔r=20, n=36〕
07. `{"op":"strip"}` — 強化解除〔〕
08. `{"op":"dmg","m":1.6}` — 追加攻撃〔m=1.6〕
09. `{"op":"slam","f":4.0}` — slam〔f=4.0〕
10. `{"op":"stun","t":90}` — 行動停止〔t=90〕
11. `{"op":"erase","r":24}` — erase〔r=24〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"strength","t":150,"a":1}` — 強化〔e="strength", t=150, a=1〕
15. `{"op":"fx","p":"bigsmoke","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="bigsmoke", n=50, at="ring", r=8.0, y=0.6〕
16. `{"op":"fx","p":"explosion","n":32,"at":"line","r":30}` — 粒子演出〔p="explosion", n=32, at="line", r=30〕
17. `{"op":"sound","s":"stone","v":1.15,"pi":0.95}` — 効果音〔s="stone", v=1.15, pi=0.95〕
18. `{"op":"area","r":17.0,"n":18}` — 円形対象の取得〔r=17.0, n=18〕
19. `{"op":"strip"}` — 強化解除〔〕
20. `{"op":"dmg","m":3.5}` — 追加攻撃〔m=3.5〕
21. `{"op":"knock","f":3.4}` — knock〔f=3.4〕
22. `{"op":"self"}` — 対象を自分へ〔〕
23. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
24. `{"op":"buff","e":"strength","t":150,"a":3}` — 強化〔e="strength", t=150, a=3〕
25. `{"op":"fx","p":"bigsmoke","n":24,"at":"ring","r":10,"y":0.5}` — 粒子演出〔p="bigsmoke", n=24, at="ring", r=10, y=0.5〕
26. `{"op":"sound","s":"stone","v":0.85,"pi":0.9}` — 効果音〔s="stone", v=0.85, pi=0.9〕
27. `{"op":"cone","r":10.0,"a":95.0}` — 扇形対象の取得〔r=10.0, a=95.0〕
28. `{"op":"dmg","m":0.95}` — 追加攻撃〔m=0.95〕
29. `{"op":"eff","e":"weakness","t":160,"a":1}` — 敵への状態異常〔e="weakness", t=160, a=1〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"strength","t":240,"a":3}` — 強化〔e="strength", t=240, a=3〕
32. `{"op":"cone","r":20.0,"a":110.0}` — 扇形対象の取得〔r=20.0, a=110.0〕
33. `{"op":"knock","f":2.8}` — knock〔f=2.8〕
34. `{"op":"fx","p":"bigsmoke","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="bigsmoke", n=24, at="ring", r=5.5, y=0.7〕
35. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
36. `{"op":"eff","e":"weakness","t":135,"a":123}` — 敵への状態異常〔e="weakness", t=135, a=123〕
37. `{"op":"self"}` — 対象を自分へ〔〕
38. `{"op":"buff","e":"strength","t":80,"a":19}` — 強化〔e="strength", t=80, a=19〕
39. `{"op":"fx","p":"crit","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="crit", n=16, at="ring", r=3.7, y=0.55〕
40. `{"op":"cone","r":12,"a":100}` — 扇形対象の取得〔r=12, a=100〕
41. `{"op":"eff","e":"weakness","t":75,"a":22}` — 敵への状態異常〔e="weakness", t=75, a=22〕
42. `{"op":"knock","f":2.1}` — knock〔f=2.1〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 不敗暴力の骨環 — 神格装飾品（Curios relic_charm） (`brutality_charm`)

**現行パラメータ**：rank=1、damage登録値=90.1692、relics側CD=175tick、art側CD=175tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（11命令）**：

01. `{"op":"low","pct":0.4,"ops":[{"op":"self"},{"op":"buff","e":"strength","t":40,"a":10}]}` — low〔pct=0.4, ops=[{"op":"self"},{"op":"buff","e":"strength","t":40,"a":10}]〕
02. `{"op":"self"}` — 対象を自分へ〔〕
03. `{"op":"buff","e":"strength","t":45,"a":0}` — 強化〔e="strength", t=45, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
06. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
07. `{"op":"buff","e":"strength","t":45,"a":1}` — 強化〔e="strength", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"strength","t":42,"a":2}` — 強化〔e="strength", t=42, a=2〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"resist","t":48,"a":4}` — 強化〔e="resist", t=48, a=4〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（37命令）**：

01. `{"op":"fx","p":"smoke","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="smoke", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"smoke","n":4,"at":"self","s":0.7}` — 粒子演出〔p="smoke", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"explosion","n":8,"at":"self","s":1.2}` — 粒子演出〔p="explosion", n=8, at="self", s=1.2〕
04. `{"op":"fx","p":"crit","n":50,"at":"self"}` — 粒子演出〔p="crit", n=50, at="self"〕
05. `{"op":"sound","s":"anvil","v":1.0,"pi":0.6}` — 効果音〔s="anvil", v=1.0, pi=0.6〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"guard","t":60}` — 防御〔t=60〕
08. `{"op":"buff","e":"strength","t":600,"a":8}` — 強化〔e="strength", t=600, a=8〕
09. `{"op":"buff","e":"resist","t":600,"a":3}` — 強化〔e="resist", t=600, a=3〕
10. `{"op":"cleanse"}` — 状態異常解除〔〕
11. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"strength","t":210,"a":1}` — 強化〔e="strength", t=210, a=1〕
14. `{"op":"fx","p":"crit","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="crit", n=46, at="ring", r=5.5, y=0.25〕
15. `{"op":"fx","p":"bigsmoke","n":36,"at":"line","r":24}` — 粒子演出〔p="bigsmoke", n=36, at="line", r=24〕
16. `{"op":"sound","s":"stone","v":1.05,"pi":1.14}` — 効果音〔s="stone", v=1.05, pi=1.14〕
17. `{"op":"self"}` — 対象を自分へ〔〕
18. `{"op":"guard","t":95}` — 防御〔t=95〕
19. `{"op":"self"}` — 対象を自分へ〔〕
20. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
21. `{"op":"cleanse"}` — 状態異常解除〔〕
22. `{"op":"buff","e":"strength","t":180,"a":3}` — 強化〔e="strength", t=180, a=3〕
23. `{"op":"guard","t":95}` — 防御〔t=95〕
24. `{"op":"fx","p":"bigsmoke","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="bigsmoke", n=30, at="ring", r=4.0, y=0.7〕
25. `{"op":"sound","s":"stone","v":0.8,"pi":1.1}` — 効果音〔s="stone", v=0.8, pi=1.1〕
26. `{"op":"self"}` — 対象を自分へ〔〕
27. `{"op":"buff","e":"strength","t":300,"a":4}` — 強化〔e="strength", t=300, a=4〕
28. `{"op":"guard","t":170}` — 防御〔t=170〕
29. `{"op":"self"}` — 対象を自分へ〔〕
30. `{"op":"buff","e":"strength","t":240,"a":3}` — 強化〔e="strength", t=240, a=3〕
31. `{"op":"fx","p":"bigsmoke","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="bigsmoke", n=20, at="ring", r=4, y=0.4〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"buff","e":"strength","t":110,"a":31}` — 強化〔e="strength", t=110, a=31〕
34. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
35. `{"op":"eff","e":"weakness","t":100,"a":123}` — 敵への状態異常〔e="weakness", t=100, a=123〕
36. `{"op":"self"}` — 対象を自分へ〔〕
37. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 絶対暴力・凄惨の覇拳 — 超越神器（武器欄） (`brutality_legend`)

**現行パラメータ**：rank=3、damage登録値=339.27586、relics側CD=330tick、art側CD=330tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:knockback:6。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"buff","e":"strength","t":40,"a":4}` — 強化〔e="strength", t=40, a=4〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
08. `{"op":"buff","e":"strength","t":45,"a":3}` — 強化〔e="strength", t=45, a=3〕
09. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（11命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"strip"}` — 強化解除〔〕
03. `{"op":"dmg","m":0.6}` — 追加攻撃〔m=0.6〕
04. `{"op":"dmg","m":0.6}` — 追加攻撃〔m=0.6〕
05. `{"op":"knock","f":4.0}` — knock〔f=4.0〕
06. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"weakness","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"weakness","t":160,"a":1}]〕
07. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
08. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"bigsmoke","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"bigsmoke","n":10,"at":"t","s":0.35}]〕
09. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
10. `{"op":"chance","p":0.3,"ops":[{"op":"victim"},{"op":"fx","p":"bigsmoke","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.3, ops=[{"op":"victim"},{"op":"fx","p":"bigsmoke","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]〕
11. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"crit","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"crit","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]〕

**権能発動時の命令（29命令）**：

01. `{"op":"fx","p":"smoke","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="smoke", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"smoke","n":4,"at":"self","s":0.7}` — 粒子演出〔p="smoke", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"explosion","n":8,"at":"self","s":1.2}` — 粒子演出〔p="explosion", n=8, at="self", s=1.2〕
04. `{"op":"fx","p":"crit","n":50,"at":"self"}` — 粒子演出〔p="crit", n=50, at="self"〕
05. `{"op":"sound","s":"anvil","v":1.0,"pi":0.6}` — 効果音〔s="anvil", v=1.0, pi=0.6〕
06. `{"op":"area","r":40,"n":36}` — 円形対象の取得〔r=40, n=36〕
07. `{"op":"strip"}` — 強化解除〔〕
08. `{"op":"dmg","m":1.68}` — 追加攻撃〔m=1.68〕
09. `{"op":"dmg","m":1.68}` — 追加攻撃〔m=1.68〕
10. `{"op":"dmg","m":1.68}` — 追加攻撃〔m=1.68〕
11. `{"op":"dmg","m":1.68}` — 追加攻撃〔m=1.68〕
12. `{"op":"launch","f":3.0}` — launch〔f=3.0〕
13. `{"op":"knock","f":6.0}` — knock〔f=6.0〕
14. `{"op":"stun","t":105}` — 行動停止〔t=105〕
15. `{"op":"dmg","m":5.6,"magic":1}` — 追加攻撃〔m=5.6, magic=1〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"buff","e":"strength","t":1200,"a":20}` — 強化〔e="strength", t=1200, a=20〕
18. `{"op":"undying","t":180}` — 死亡防護〔t=180〕
19. `{"op":"cleanse"}` — 状態異常解除〔〕
20. `{"op":"fx","p":"explosion","n":12,"at":"t","s":0.5}` — 粒子演出〔p="explosion", n=12, at="t", s=0.5〕
21. `{"op":"cone","r":12,"a":120}` — 扇形対象の取得〔r=12, a=120〕
22. `{"op":"dmg","m":2.5}` — 追加攻撃〔m=2.5〕
23. `{"op":"slam"}` — slam〔〕
24. `{"op":"fx","p":"bigsmoke","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="bigsmoke", n=50, at="ring", r=8.0, y=0.6〕
25. `{"op":"fx","p":"explosion","n":32,"at":"line","r":30}` — 粒子演出〔p="explosion", n=32, at="line", r=30〕
26. `{"op":"sound","s":"stone","v":1.15,"pi":0.95}` — 効果音〔s="stone", v=1.15, pi=0.95〕
27. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.brutality_legend.stage0","ops":[{"op":"fx","p":"bigsmoke","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"stone","v":0.9,"pi":1.2},{"op":"fx","p":"crit","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"bigsmoke","n":6,"at":"line","r":10},{"op":"fx","p":"crit","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"bigsmoke","n":36,"at":"line","r":24},{"op":"sound","s":"stone","v":1.05,"pi":1.14},{"op":"cone","r":14.0,"a":145.0},{"op":"dmg","m":5.535},{"op":"slam"},{"op":"self"},{"op":"buff","e":"strength","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.brutality_legend.stage1","ops":[{"op":"fx","p":"bigsmoke","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"stone","v":1.05,"pi":1.0},{"op":"fx","p":"bigsmoke","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"crit","n":6,"at":"line","r":15},{"op":"fx","p":"bigsmoke","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"explosion","n":32,"at":"line","r":30},{"op":"sound","s":"stone","v":1.15,"pi":0.95},{"op":"area","r":17.0,"n":18},{"op":"strip"},{"op":"dmg","m":5.075},{"op":"knock","f":3.4},{"op":"area","r":12.0,"n":10},{"op":"eff","e":"weakness","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.brutality_legend.stage2","ops":[{"op":"fx","p":"bigsmoke","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"stone","v":1.25,"pi":0.75},{"op":"fx","p":"bigsmoke","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"crit","n":10,"at":"line","r":20},{"op":"fx","p":"crit","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"bigsmoke","n":48,"at":"line","r":48},{"op":"fx","p":"explosion","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"stone","v":1.5,"pi":0.75},{"op":"cone","r":24.0,"a":155.0},{"op":"dmg","m":11.9},{"op":"strip"},{"op":"slam"},{"op":"area","r":18.0,"n":20},{"op":"dmg","m":5.67},{"op":"self"},{"op":"buff","e":"strength","t":200,"a":5},{"op":"fx","p":"explosion","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"bigsmoke","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"cone","r":24.0,"a":155.0},{"op":"dmg","m":3.8},{"op":"slam"},{"op":"area","r":18.0,"n":20},{"op":"dmg","m":1.4},{"op":"self"},{"op":"buff","e":"strength","t":195,"a":5},{"op":"cone","r":30.0,"a":110.0},{"op":"dmg","m":0.8},{"op":"eff","e":"weakness","t":160,"a":2},{"op":"self"},{"op":"buff","e":"strength","t":240,"a":4},{"op":"area","r":20,"n":10},{"op":"slam","f":3.2},{"op":"fx","p":"bigsmoke","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"stone","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"weakness","t":75,"a":22},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.brutality_legend.stage0","ops":[{"op":"fx","p":"bigsmoke","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"stone","v":0.9,"pi":1.2},{"op":"fx","p":"crit","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"bigsmoke","n":6,"at":"line","r":10},{"op":"fx","p":"crit","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"bigsmoke","n":36,"at":"line","r":24},{"op":"sound","s":"stone","v":1.05,"pi":1.14},{"op":"cone","r":14.0,"a":145.0},{"op":"dmg","m":5.535},{"op":"slam"},{"op":"self"},{"op":"buff","e":"strength","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.brutality_legend.stage1","ops":[{"op":"fx","p":"bigsmoke","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"stone","v":1.05,"pi":1.0},{"op":"fx","p":"bigsmoke","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"crit","n":6,"at":"line","r":15},{"op":"fx","p":"bigsmoke","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"explosion","n":32,"at":"line","r":30},{"op":"sound","s":"stone","v":1.15,"pi":0.95},{"op":"area","r":17.0,"n":18},{"op":"strip"},{"op":"dmg","m":5.075},{"op":"knock","f":3.4},{"op":"area","r":12.0,"n":10},{"op":"eff","e":"weakness","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.brutality_legend.stage2","ops":[{"op":"fx","p":"bigsmoke","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"stone","v":1.25,"pi":0.75},{"op":"fx","p":"bigsmoke","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"crit","n":10,"at":"line","r":20},{"op":"fx","p":"crit","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"bigsmoke","n":48,"at":"line","r":48},{"op":"fx","p":"explosion","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"stone","v":1.5,"pi":0.75},{"op":"cone","r":24.0,"a":155.0},{"op":"dmg","m":11.9},{"op":"strip"},{"op":"slam"},{"op":"area","r":18.0,"n":20},{"op":"dmg","m":5.67},{"op":"self"},{"op":"buff","e":"strength","t":200,"a":5},{"op":"fx","p":"explosion","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"bigsmoke","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"cone","r":24.0,"a":155.0},{"op":"dmg","m":3.8},{"op":"slam"},{"op":"area","r":18.0,"n":20},{"op":"dmg","m":1.4},{"op":"self"},{"op":"buff","e":"strength","t":195,"a":5},{"op":"cone","r":30.0,"a":110.0},{"op":"dmg","m":0.8},{"op":"eff","e":"weakness","t":160,"a":2},{"op":"self"},{"op":"buff","e":"strength","t":240,"a":4},{"op":"area","r":20,"n":10},{"op":"slam","f":3.2},{"op":"fx","p":"bigsmoke","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"stone","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"weakness","t":75,"a":22},{"op":"mark","t":135,"x":1.8}]}]〕
28. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
29. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 37. 邪沌の呪詛

**モブ側の動きの方向性**：優しい手の動きと、白薔薇が黒花へ変わる変調を使う。。

### 悲劇の操り人形 — 討伐武器（メイン／武器欄） (`cursed_love_weapon`)

**現行パラメータ**：rank=1、damage登録値=578.5、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10、minecraft:fire_aspect:10。

**装備中の常時命令（4命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"regen","t":40,"a":0}` — 強化〔e="regen", t=40, a=0〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（9命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"eff","e":"wither","t":100,"a":3}` — 敵への状態異常〔e="wither", t=100, a=3〕
03. `{"op":"eff","e":"nausea","t":60,"a":0}` — 敵への状態異常〔e="nausea", t=60, a=0〕
04. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"wither","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"wither","t":90,"a":0}]〕
05. `{"op":"chance","p":0.485,"ops":[{"op":"victim"},{"op":"fx","p":"witch","n":11,"at":"t","s":0.24},{"op":"mark","t":140,"x":1.79},{"op":"eff","e":"wither","t":55,"a":0}]}` — 抽選〔p=0.485, ops=[{"op":"victim"},{"op":"fx","p":"witch","n":11,"at":"t","s":0.24},{"op":"mark","t":140,"x":1.79},{"op":"eff","e":"wither","t":55,"a":0}]〕
06. `{"op":"chance","p":0.177,"ops":[{"op":"victim"},{"op":"dmg","m":0.235}]}` — 抽選〔p=0.177, ops=[{"op":"victim"},{"op":"dmg","m":0.235}]〕
07. `{"op":"chance","p":0.085,"ops":[{"op":"victim"},{"op":"fx","p":"witch","n":8,"at":"t","s":0.25},{"op":"eff","e":"weakness","t":65,"a":0}]}` — 抽選〔p=0.085, ops=[{"op":"victim"},{"op":"fx","p":"witch","n":8,"at":"t","s":0.25},{"op":"eff","e":"weakness","t":65,"a":0}]〕
08. `{"op":"chance","p":0.2,"ops":[{"op":"victim"},{"op":"fx","p":"witch","n":14,"at":"t","s":0.28},{"op":"eff","e":"wither","t":22,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.2, ops=[{"op":"victim"},{"op":"fx","p":"witch","n":14,"at":"t","s":0.28},{"op":"eff","e":"wither","t":22,"a":124},{"op":"mark","t":100,"x":2.15}]〕
09. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"witch","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"witch","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]〕

**権能発動時の命令（28命令）**：

01. `{"op":"fx","p":"witch","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="witch", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"witch","n":4,"at":"self","s":0.7}` — 粒子演出〔p="witch", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"dragon","n":30,"at":"self"}` — 粒子演出〔p="dragon", n=30, at="self"〕
04. `{"op":"fx","p":"sculk","n":20,"at":"self"}` — 粒子演出〔p="sculk", n=20, at="self"〕
05. `{"op":"sound","s":"mirror","v":0.8,"pi":0.5}` — 効果音〔s="mirror", v=0.8, pi=0.5〕
06. `{"op":"chain","n":6,"r":12}` — chain〔n=6, r=12〕
07. `{"op":"pull","f":2.0}` — pull〔f=2.0〕
08. `{"op":"stun","t":65}` — 行動停止〔t=65〕
09. `{"op":"eff","e":"wither","t":400,"a":5}` — 敵への状態異常〔e="wither", t=400, a=5〕
10. `{"op":"eff","e":"nausea","t":300,"a":0}` — 敵への状態異常〔e="nausea", t=300, a=0〕
11. `{"op":"mark","t":400,"x":2.5}` — 刻印〔t=400, x=2.5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"healpct","v":0.25}` — 最大HP割合回復〔v=0.25〕
14. `{"op":"fx","p":"dragon","n":12,"at":"t","s":0.5}` — 粒子演出〔p="dragon", n=12, at="t", s=0.5〕
15. `{"op":"fx","p":"heart","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="heart", n=46, at="ring", r=5.5, y=0.25〕
16. `{"op":"fx","p":"witch","n":36,"at":"line","r":24}` — 粒子演出〔p="witch", n=36, at="line", r=24〕
17. `{"op":"area","r":25.0,"n":18}` — 円形対象の取得〔r=25.0, n=18〕
18. `{"op":"eff","e":"wither","t":135,"a":2}` — 敵への状態異常〔e="wither", t=135, a=2〕
19. `{"op":"mark","t":130,"x":1.5}` — 刻印〔t=130, x=1.5〕
20. `{"op":"fx","p":"witch","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="witch", n=16, at="ring", r=5.0〕
21. `{"op":"sound","s":"spell","v":0.75,"pi":1.15}` — 効果音〔s="spell", v=0.75, pi=1.15〕
22. `{"op":"chain","n":4,"r":12}` — chain〔n=4, r=12〕
23. `{"op":"dmg","m":1.0}` — 追加攻撃〔m=1.0〕
24. `{"op":"eff","e":"wither","t":65,"a":0}` — 敵への状態異常〔e="wither", t=65, a=0〕
25. `{"op":"fx","p":"witch","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="witch", n=24, at="ring", r=4.5, y=0.6〕
26. `{"op":"sound","s":"wither","v":0.8,"pi":0.8}` — 効果音〔s="wither", v=0.8, pi=0.8〕
27. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
28. `{"op":"eff","e":"wither","t":22,"a":124}` — 敵への状態異常〔e="wither", t=22, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 邪沌の愛液瓶 — 神威触媒（Curios relic_focus） (`cursed_love_focus`)

**現行パラメータ**：rank=2、damage登録値=73.7748、relics側CD=160tick、art側CD=160tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"night","t":300,"a":0}` — 強化〔e="night", t=300, a=0〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"regen","t":45,"a":0}` — 強化〔e="regen", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"regen","t":42,"a":2}` — 強化〔e="regen", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（41命令）**：

01. `{"op":"fx","p":"witch","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="witch", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"witch","n":6,"at":"self","s":0.7}` — 粒子演出〔p="witch", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"dragon","n":30,"at":"self"}` — 粒子演出〔p="dragon", n=30, at="self"〕
04. `{"op":"fx","p":"sculk","n":20,"at":"self"}` — 粒子演出〔p="sculk", n=20, at="self"〕
05. `{"op":"sound","s":"mirror","v":0.8,"pi":0.5}` — 効果音〔s="mirror", v=0.8, pi=0.5〕
06. `{"op":"area","r":24,"n":36}` — 円形対象の取得〔r=24, n=36〕
07. `{"op":"eff","e":"wither","t":800,"a":7}` — 敵への状態異常〔e="wither", t=800, a=7〕
08. `{"op":"eff","e":"weakness","t":800,"a":5}` — 敵への状態異常〔e="weakness", t=800, a=5〕
09. `{"op":"eff","e":"blind","t":200,"a":0}` — 敵への状態異常〔e="blind", t=200, a=0〕
10. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
11. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"regen","t":150,"a":1}` — 強化〔e="regen", t=150, a=1〕
14. `{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="witch", n=50, at="ring", r=8.0, y=0.6〕
15. `{"op":"fx","p":"ash","n":32,"at":"line","r":30}` — 粒子演出〔p="ash", n=32, at="line", r=30〕
16. `{"op":"sound","s":"wither","v":1.15,"pi":0.95}` — 効果音〔s="wither", v=1.15, pi=0.95〕
17. `{"op":"area","r":26.0,"n":22}` — 円形対象の取得〔r=26.0, n=22〕
18. `{"op":"strip"}` — 強化解除〔〕
19. `{"op":"dmg","m":2.7}` — 追加攻撃〔m=2.7〕
20. `{"op":"eff","e":"weakness","t":125,"a":2}` — 敵への状態異常〔e="weakness", t=125, a=2〕
21. `{"op":"self"}` — 対象を自分へ〔〕
22. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
23. `{"op":"buff","e":"regen","t":150,"a":3}` — 強化〔e="regen", t=150, a=3〕
24. `{"op":"fx","p":"witch","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="witch", n=24, at="ring", r=12, y=0.5〕
25. `{"op":"sound","s":"wither","v":0.85,"pi":0.97}` — 効果音〔s="wither", v=0.85, pi=0.97〕
26. `{"op":"area","r":12.0,"n":12}` — 円形対象の取得〔r=12.0, n=12〕
27. `{"op":"dmg","m":0.8}` — 追加攻撃〔m=0.8〕
28. `{"op":"eff","e":"wither","t":100,"a":1}` — 敵への状態異常〔e="wither", t=100, a=1〕
29. `{"op":"self"}` — 対象を自分へ〔〕
30. `{"op":"buff","e":"regen","t":200,"a":3}` — 強化〔e="regen", t=200, a=3〕
31. `{"op":"area","r":14,"n":8}` — 円形対象の取得〔r=14, n=8〕
32. `{"op":"eff","e":"wither","t":100,"a":1}` — 敵への状態異常〔e="wither", t=100, a=1〕
33. `{"op":"fx","p":"witch","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="witch", n=24, at="ring", r=5.5, y=0.7〕
34. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
35. `{"op":"eff","e":"wither","t":30,"a":123}` — 敵への状態異常〔e="wither", t=30, a=123〕
36. `{"op":"self"}` — 対象を自分へ〔〕
37. `{"op":"buff","e":"regen","t":140,"a":7}` — 強化〔e="regen", t=140, a=7〕
38. `{"op":"fx","p":"witch","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="witch", n=16, at="ring", r=3.7, y=0.55〕
39. `{"op":"area","r":14,"n":7}` — 円形対象の取得〔r=14, n=7〕
40. `{"op":"eff","e":"wither","t":65,"a":6}` — 敵への状態異常〔e="wither", t=65, a=6〕
41. `{"op":"mark","t":115,"x":1.8}` — 刻印〔t=115, x=1.8〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 幸福反転の黒花飾り — 神格装飾品（Curios relic_charm） (`cursed_love_charm`)

**現行パラメータ**：rank=1、damage登録値=73.7748、relics側CD=190tick、art側CD=190tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（12命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"regen","t":45,"a":0}` — 強化〔e="regen", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"regen","t":42,"a":2}` — 強化〔e="regen", t=42, a=2〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"regen","t":48,"a":4}` — 強化〔e="regen", t=48, a=4〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（37命令）**：

01. `{"op":"fx","p":"witch","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="witch", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"witch","n":4,"at":"self","s":0.7}` — 粒子演出〔p="witch", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"dragon","n":30,"at":"self"}` — 粒子演出〔p="dragon", n=30, at="self"〕
04. `{"op":"fx","p":"sculk","n":20,"at":"self"}` — 粒子演出〔p="sculk", n=20, at="self"〕
05. `{"op":"sound","s":"mirror","v":0.8,"pi":0.5}` — 効果音〔s="mirror", v=0.8, pi=0.5〕
06. `{"op":"area","r":20,"n":36}` — 円形対象の取得〔r=20, n=36〕
07. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
08. `{"op":"eff","e":"hunger","t":600,"a":5}` — 敵への状態異常〔e="hunger", t=600, a=5〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"healpct","v":0.25}` — 最大HP割合回復〔v=0.25〕
11. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"regen","t":210,"a":1}` — 強化〔e="regen", t=210, a=1〕
14. `{"op":"fx","p":"heart","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="heart", n=46, at="ring", r=5.5, y=0.25〕
15. `{"op":"fx","p":"witch","n":36,"at":"line","r":24}` — 粒子演出〔p="witch", n=36, at="line", r=24〕
16. `{"op":"sound","s":"wither","v":1.05,"pi":1.14}` — 効果音〔s="wither", v=1.05, pi=1.14〕
17. `{"op":"self"}` — 対象を自分へ〔〕
18. `{"op":"guard","t":95}` — 防御〔t=95〕
19. `{"op":"self"}` — 対象を自分へ〔〕
20. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
21. `{"op":"cleanse"}` — 状態異常解除〔〕
22. `{"op":"buff","e":"regen","t":180,"a":3}` — 強化〔e="regen", t=180, a=3〕
23. `{"op":"guard","t":95}` — 防御〔t=95〕
24. `{"op":"fx","p":"witch","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="witch", n=30, at="ring", r=4.0, y=0.7〕
25. `{"op":"sound","s":"wither","v":0.8,"pi":1.1}` — 効果音〔s="wither", v=0.8, pi=1.1〕
26. `{"op":"self"}` — 対象を自分へ〔〕
27. `{"op":"buff","e":"regen","t":260,"a":4}` — 強化〔e="regen", t=260, a=4〕
28. `{"op":"guard","t":125}` — 防御〔t=125〕
29. `{"op":"self"}` — 対象を自分へ〔〕
30. `{"op":"cleanse"}` — 状態異常解除〔〕
31. `{"op":"fx","p":"witch","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="witch", n=20, at="ring", r=4, y=0.4〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"buff","e":"regen","t":140,"a":7}` — 強化〔e="regen", t=140, a=7〕
34. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
35. `{"op":"eff","e":"wither","t":22,"a":123}` — 敵への状態異常〔e="wither", t=22, a=123〕
36. `{"op":"self"}` — 対象を自分へ〔〕
37. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 終わらぬ悲劇・呪愛の心臓 — 超越神器（武器欄） (`cursed_love_legend`)

**現行パラメータ**：rank=3、damage登録値=1157.875、relics側CD=345tick、art側CD=345tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10、minecraft:fire_aspect:10。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"area","r":8,"n":36}` — 円形対象の取得〔r=8, n=36〕
06. `{"op":"eff","e":"wither","t":40,"a":2}` — 敵への状態異常〔e="wither", t=40, a=2〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
09. `{"op":"buff","e":"regen","t":45,"a":3}` — 強化〔e="regen", t=45, a=3〕
10. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（9命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"eff","e":"wither","t":200,"a":5}` — 敵への状態異常〔e="wither", t=200, a=5〕
03. `{"op":"mark","t":200,"x":2.0}` — 刻印〔t=200, x=2.0〕
04. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"wither","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"wither","t":160,"a":1}]〕
05. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"heart","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"heart","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
06. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"wither","t":135,"a":2},{"op":"fx","p":"heart","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"wither","t":135,"a":2},{"op":"fx","p":"heart","n":10,"at":"t","s":0.35}]〕
07. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
08. `{"op":"chance","p":0.325,"ops":[{"op":"victim"},{"op":"fx","p":"witch","n":20,"at":"t","s":0.33},{"op":"eff","e":"wither","t":30,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.325, ops=[{"op":"victim"},{"op":"fx","p":"witch","n":20,"at":"t","s":0.33},{"op":"eff","e":"wither","t":30,"a":124},{"op":"mark","t":160,"x":2.5}]〕
09. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"witch","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"witch","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"weakness","t":95,"a":16}]〕

**権能発動時の命令（27命令）**：

01. `{"op":"fx","p":"witch","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="witch", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"witch","n":4,"at":"self","s":0.7}` — 粒子演出〔p="witch", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"dragon","n":30,"at":"self"}` — 粒子演出〔p="dragon", n=30, at="self"〕
04. `{"op":"fx","p":"sculk","n":20,"at":"self"}` — 粒子演出〔p="sculk", n=20, at="self"〕
05. `{"op":"sound","s":"mirror","v":0.8,"pi":0.5}` — 効果音〔s="mirror", v=0.8, pi=0.5〕
06. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
07. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
08. `{"op":"eff","e":"wither","t":1200,"a":9}` — 敵への状態異常〔e="wither", t=1200, a=9〕
09. `{"op":"eff","e":"nausea","t":600,"a":0}` — 敵への状態異常〔e="nausea", t=600, a=0〕
10. `{"op":"eff","e":"blind","t":300,"a":0}` — 敵への状態異常〔e="blind", t=300, a=0〕
11. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
12. `{"op":"dmg","m":5.6,"magic":1}` — 追加攻撃〔m=5.6, magic=1〕
13. `{"op":"mark","t":600,"x":3.0}` — 刻印〔t=600, x=3.0〕
14. `{"op":"self"}` — 対象を自分へ〔〕
15. `{"op":"healpct","v":0.6}` — 最大HP割合回復〔v=0.6〕
16. `{"op":"undying","t":180}` — 死亡防護〔t=180〕
17. `{"op":"fx","p":"dragon","n":12,"at":"t","s":0.5}` — 粒子演出〔p="dragon", n=12, at="t", s=0.5〕
18. `{"op":"area","r":30,"n":24}` — 円形対象の取得〔r=30, n=24〕
19. `{"op":"strip"}` — 強化解除〔〕
20. `{"op":"eff","e":"wither","t":160,"a":1}` — 敵への状態異常〔e="wither", t=160, a=1〕
21. `{"op":"dmg","m":1.2}` — 追加攻撃〔m=1.2〕
22. `{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="witch", n=50, at="ring", r=8.0, y=0.6〕
23. `{"op":"fx","p":"ash","n":32,"at":"line","r":30}` — 粒子演出〔p="ash", n=32, at="line", r=30〕
24. `{"op":"sound","s":"wither","v":1.15,"pi":0.95}` — 効果音〔s="wither", v=1.15, pi=0.95〕
25. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.cursed_love_legend.stage0","ops":[{"op":"fx","p":"witch","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"wither","v":0.9,"pi":1.2},{"op":"fx","p":"witch","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"heart","n":6,"at":"line","r":10},{"op":"fx","p":"heart","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"witch","n":36,"at":"line","r":24},{"op":"sound","s":"wither","v":1.05,"pi":1.14},{"op":"area","r":25.0,"n":18},{"op":"eff","e":"wither","t":135,"a":2},{"op":"mark","t":130,"x":1.95},{"op":"self"},{"op":"buff","e":"regen","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.cursed_love_legend.stage1","ops":[{"op":"fx","p":"witch","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"wither","v":1.05,"pi":1.0},{"op":"fx","p":"heart","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"witch","n":6,"at":"line","r":15},{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"ash","n":32,"at":"line","r":30},{"op":"sound","s":"wither","v":1.15,"pi":0.95},{"op":"area","r":26.0,"n":22},{"op":"strip"},{"op":"dmg","m":3.915},{"op":"eff","e":"weakness","t":125,"a":2},{"op":"area","r":14.0,"n":10},{"op":"eff","e":"wither","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.cursed_love_legend.stage2","ops":[{"op":"fx","p":"witch","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"wither","v":1.25,"pi":0.75},{"op":"fx","p":"heart","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"witch","n":10,"at":"line","r":20},{"op":"fx","p":"heart","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"witch","n":48,"at":"line","r":48},{"op":"fx","p":"ash","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"wither","v":1.5,"pi":0.75},{"op":"area","r":34.0,"n":29},{"op":"dmg","m":9.072},{"op":"eff","e":"wither","t":170,"a":3},{"op":"strip"},{"op":"stun","t":46},{"op":"fx","p":"ash","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"heart","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":30.0,"n":27},{"op":"dmg","m":3.0},{"op":"eff","e":"wither","t":175,"a":3},{"op":"strip"},{"op":"area","r":15.0,"n":16},{"op":"dmg","m":0.9},{"op":"eff","e":"wither","t":160,"a":2},{"op":"self"},{"op":"buff","e":"regen","t":240,"a":4},{"op":"area","r":14,"n":8},{"op":"eff","e":"wither","t":100,"a":1},{"op":"fx","p":"witch","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"wither","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"wither","t":30,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"wither","t":65,"a":6},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.cursed_love_legend.stage0","ops":[{"op":"fx","p":"witch","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"wither","v":0.9,"pi":1.2},{"op":"fx","p":"witch","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"heart","n":6,"at":"line","r":10},{"op":"fx","p":"heart","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"witch","n":36,"at":"line","r":24},{"op":"sound","s":"wither","v":1.05,"pi":1.14},{"op":"area","r":25.0,"n":18},{"op":"eff","e":"wither","t":135,"a":2},{"op":"mark","t":130,"x":1.95},{"op":"self"},{"op":"buff","e":"regen","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.cursed_love_legend.stage1","ops":[{"op":"fx","p":"witch","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"wither","v":1.05,"pi":1.0},{"op":"fx","p":"heart","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"witch","n":6,"at":"line","r":15},{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"ash","n":32,"at":"line","r":30},{"op":"sound","s":"wither","v":1.15,"pi":0.95},{"op":"area","r":26.0,"n":22},{"op":"strip"},{"op":"dmg","m":3.915},{"op":"eff","e":"weakness","t":125,"a":2},{"op":"area","r":14.0,"n":10},{"op":"eff","e":"wither","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.cursed_love_legend.stage2","ops":[{"op":"fx","p":"witch","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"wither","v":1.25,"pi":0.75},{"op":"fx","p":"heart","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"witch","n":10,"at":"line","r":20},{"op":"fx","p":"heart","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"witch","n":48,"at":"line","r":48},{"op":"fx","p":"ash","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"wither","v":1.5,"pi":0.75},{"op":"area","r":34.0,"n":29},{"op":"dmg","m":9.072},{"op":"eff","e":"wither","t":170,"a":3},{"op":"strip"},{"op":"stun","t":46},{"op":"fx","p":"ash","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"heart","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":30.0,"n":27},{"op":"dmg","m":3.0},{"op":"eff","e":"wither","t":175,"a":3},{"op":"strip"},{"op":"area","r":15.0,"n":16},{"op":"dmg","m":0.9},{"op":"eff","e":"wither","t":160,"a":2},{"op":"self"},{"op":"buff","e":"regen","t":240,"a":4},{"op":"area","r":14,"n":8},{"op":"eff","e":"wither","t":100,"a":1},{"op":"fx","p":"witch","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"wither","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"wither","t":30,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"wither","t":65,"a":6},{"op":"mark","t":135,"x":1.8}]}]〕
26. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
27. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 38. 戒進の研究

**モブ側の動きの方向性**：医療装置、機械腕、分析視線と培養生命の成長を重ねる。。

### 救済実験の大注射器 — 討伐武器（メイン／武器欄） (`relentless_research_weapon`)

**現行パラメータ**：rank=1、damage登録値=328.5、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12。

**装備中の常時命令（4命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"regen","t":40,"a":0}` — 強化〔e="regen", t=40, a=0〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（8命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"eff","e":"poison","t":100,"a":4}` — 敵への状態異常〔e="poison", t=100, a=4〕
03. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"poison","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"poison","t":90,"a":0}]〕
04. `{"op":"chance","p":0.51,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":13,"at":"t","s":0.24},{"op":"mark","t":160,"x":1.93},{"op":"eff","e":"fatigue","t":67,"a":0}]}` — 抽選〔p=0.51, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":13,"at":"t","s":0.24},{"op":"mark","t":160,"x":1.93},{"op":"eff","e":"fatigue","t":67,"a":0}]〕
05. `{"op":"chance","p":0.204,"ops":[{"op":"victim"},{"op":"dmg","m":0.27}]}` — 抽選〔p=0.204, ops=[{"op":"victim"},{"op":"dmg","m":0.27}]〕
06. `{"op":"chance","p":0.104,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":8,"at":"t","s":0.25},{"op":"eff","e":"poison","t":55,"a":1}]}` — 抽選〔p=0.104, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":8,"at":"t","s":0.25},{"op":"eff","e":"poison","t":55,"a":1}]〕
07. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":14,"at":"t","s":0.28},{"op":"eff","e":"fatigue","t":110,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":14,"at":"t","s":0.28},{"op":"eff","e":"fatigue","t":110,"a":124},{"op":"mark","t":100,"x":2.15}]〕
08. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"wax","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"wax","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]〕

**権能発動時の命令（27命令）**：

01. `{"op":"fx","p":"sculk","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="sculk", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"sculk","n":4,"at":"self","s":0.7}` — 粒子演出〔p="sculk", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"happy","n":20,"at":"self"}` — 粒子演出〔p="happy", n=20, at="self"〕
04. `{"op":"fx","p":"witch","n":30,"at":"self"}` — 粒子演出〔p="witch", n=30, at="self"〕
05. `{"op":"sound","s":"spell","v":0.8,"pi":1.6}` — 効果音〔s="spell", v=0.8, pi=1.6〕
06. `{"op":"line","r":24,"w":2.5}` — 線分対象の取得〔r=24, w=2.5〕
07. `{"op":"dmg","m":1.8}` — 追加攻撃〔m=1.8〕
08. `{"op":"eff","e":"poison","t":400,"a":6}` — 敵への状態異常〔e="poison", t=400, a=6〕
09. `{"op":"stun","t":65}` — 行動停止〔t=65〕
10. `{"op":"chance","p":0.3,"ops":[{"op":"transmute"}]}` — 抽選〔p=0.3, ops=[{"op":"transmute"}]〕
11. `{"op":"allies","r":16}` — 味方対象〔r=16〕
12. `{"op":"healpct","v":0.25,"to":1}` — 最大HP割合回復〔v=0.25, to=1〕
13. `{"op":"fx","p":"witch","n":12,"at":"t","s":0.5}` — 粒子演出〔p="witch", n=12, at="t", s=0.5〕
14. `{"op":"fx","p":"witch","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="witch", n=46, at="ring", r=5.5, y=0.25〕
15. `{"op":"fx","p":"spark","n":36,"at":"line","r":24}` — 粒子演出〔p="spark", n=36, at="line", r=24〕
16. `{"op":"line","r":56.0,"w":4.0}` — 線分対象の取得〔r=56.0, w=4.0〕
17. `{"op":"dmg","m":2.7}` — 追加攻撃〔m=2.7〕
18. `{"op":"eff","e":"poison","t":105,"a":1}` — 敵への状態異常〔e="poison", t=105, a=1〕
19. `{"op":"fx","p":"enchant","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="enchant", n=16, at="ring", r=5.0〕
20. `{"op":"sound","s":"sonic","v":0.75,"pi":1.15}` — 効果音〔s="sonic", v=0.75, pi=1.15〕
21. `{"op":"line","r":18,"w":2}` — 線分対象の取得〔r=18, w=2〕
22. `{"op":"dmg","m":1.05}` — 追加攻撃〔m=1.05〕
23. `{"op":"eff","e":"fatigue","t":65,"a":0}` — 敵への状態異常〔e="fatigue", t=65, a=0〕
24. `{"op":"fx","p":"spark","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="spark", n=24, at="ring", r=4.5, y=0.6〕
25. `{"op":"sound","s":"anvil","v":0.8,"pi":0.8}` — 効果音〔s="anvil", v=0.8, pi=0.8〕
26. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
27. `{"op":"eff","e":"fatigue","t":110,"a":124}` — 敵への状態異常〔e="fatigue", t=110, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 戒進治療の研究炉 — 神威触媒（Curios relic_focus） (`relentless_research_focus`)

**現行パラメータ**：rank=2、damage登録値=68.31、relics側CD=155tick、art側CD=155tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"allies","r":16}` — 味方対象〔r=16〕
02. `{"op":"buff","e":"regen","t":40,"a":0,"to":1}` — 強化〔e="regen", t=40, a=0, to=1〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"regen","t":45,"a":0}` — 強化〔e="regen", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"haste","t":42,"a":2}` — 強化〔e="haste", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（42命令）**：

01. `{"op":"fx","p":"sculk","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="sculk", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"sculk","n":6,"at":"self","s":0.7}` — 粒子演出〔p="sculk", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"happy","n":20,"at":"self"}` — 粒子演出〔p="happy", n=20, at="self"〕
04. `{"op":"fx","p":"witch","n":30,"at":"self"}` — 粒子演出〔p="witch", n=30, at="self"〕
05. `{"op":"sound","s":"spell","v":0.8,"pi":1.6}` — 効果音〔s="spell", v=0.8, pi=1.6〕
06. `{"op":"allies","r":32}` — 味方対象〔r=32〕
07. `{"op":"healpct","v":0.4,"to":1}` — 最大HP割合回復〔v=0.4, to=1〕
08. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
09. `{"op":"buff","e":"regen","t":600,"a":4,"to":1}` — 強化〔e="regen", t=600, a=4, to=1〕
10. `{"op":"buff","e":"health","t":1200,"a":4,"to":1}` — 強化〔e="health", t=1200, a=4, to=1〕
11. `{"op":"summon","k":"wolf","n":2}` — 召喚〔k="wolf", n=2〕
12. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
13. `{"op":"self"}` — 対象を自分へ〔〕
14. `{"op":"buff","e":"regen","t":150,"a":1}` — 強化〔e="regen", t=150, a=1〕
15. `{"op":"fx","p":"spark","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="spark", n=50, at="ring", r=8.0, y=0.6〕
16. `{"op":"fx","p":"compost","n":32,"at":"line","r":30}` — 粒子演出〔p="compost", n=32, at="line", r=30〕
17. `{"op":"sound","s":"spell","v":1.15,"pi":0.95}` — 効果音〔s="spell", v=1.15, pi=0.95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"adapt"}` — adapt〔〕
20. `{"op":"healpct","v":0.35}` — 最大HP割合回復〔v=0.35〕
21. `{"op":"summon","k":"golem","n":3}` — 召喚〔k="golem", n=3〕
22. `{"op":"self"}` — 対象を自分へ〔〕
23. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
24. `{"op":"buff","e":"regen","t":150,"a":3}` — 強化〔e="regen", t=150, a=3〕
25. `{"op":"fx","p":"spark","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="spark", n=24, at="ring", r=12, y=0.5〕
26. `{"op":"sound","s":"anvil","v":0.85,"pi":1.04}` — 効果音〔s="anvil", v=0.85, pi=1.04〕
27. `{"op":"area","r":14.0,"n":12}` — 円形対象の取得〔r=14.0, n=12〕
28. `{"op":"dmg","m":0.8}` — 追加攻撃〔m=0.8〕
29. `{"op":"eff","e":"fatigue","t":120,"a":1}` — 敵への状態異常〔e="fatigue", t=120, a=1〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"haste","t":220,"a":3}` — 強化〔e="haste", t=220, a=3〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"adapt","t":160}` — adapt〔t=160〕
34. `{"op":"fx","p":"spark","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="spark", n=24, at="ring", r=5.5, y=0.7〕
35. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
36. `{"op":"eff","e":"fatigue","t":148,"a":123}` — 敵への状態異常〔e="fatigue", t=148, a=123〕
37. `{"op":"self"}` — 対象を自分へ〔〕
38. `{"op":"buff","e":"haste","t":100,"a":123}` — 強化〔e="haste", t=100, a=123〕
39. `{"op":"fx","p":"wax","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="wax", n=16, at="ring", r=3.7, y=0.55〕
40. `{"op":"self"}` — 対象を自分へ〔〕
41. `{"op":"repair","v":180}` — 修理〔v=180〕
42. `{"op":"buff","e":"haste","t":170,"a":6}` — 強化〔e="haste", t=170, a=6〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 分散保存の記憶鏡 — 神格装飾品（Curios relic_charm） (`relentless_research_charm`)

**現行パラメータ**：rank=1、damage登録値=68.31、relics側CD=185tick、art側CD=185tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（11命令）**：

01. `{"op":"snapshot"}` — 状態保存〔〕
02. `{"op":"self"}` — 対象を自分へ〔〕
03. `{"op":"buff","e":"regen","t":45,"a":0}` — 強化〔e="regen", t=45, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
06. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"haste","t":42,"a":2}` — 強化〔e="haste", t=42, a=2〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"haste","t":48,"a":7}` — 強化〔e="haste", t=48, a=7〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（36命令）**：

01. `{"op":"fx","p":"sculk","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="sculk", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"sculk","n":4,"at":"self","s":0.7}` — 粒子演出〔p="sculk", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"happy","n":20,"at":"self"}` — 粒子演出〔p="happy", n=20, at="self"〕
04. `{"op":"fx","p":"witch","n":30,"at":"self"}` — 粒子演出〔p="witch", n=30, at="self"〕
05. `{"op":"sound","s":"spell","v":0.8,"pi":1.6}` — 効果音〔s="spell", v=0.8, pi=1.6〕
06. `{"op":"rewind"}` — 復元〔〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"undying","t":100}` — 死亡防護〔t=100〕
09. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"regen","t":210,"a":1}` — 強化〔e="regen", t=210, a=1〕
12. `{"op":"fx","p":"witch","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="witch", n=46, at="ring", r=5.5, y=0.25〕
13. `{"op":"fx","p":"spark","n":36,"at":"line","r":24}` — 粒子演出〔p="spark", n=36, at="line", r=24〕
14. `{"op":"sound","s":"spell","v":1.05,"pi":1.14}` — 効果音〔s="spell", v=1.05, pi=1.14〕
15. `{"op":"self"}` — 対象を自分へ〔〕
16. `{"op":"guard","t":95}` — 防御〔t=95〕
17. `{"op":"self"}` — 対象を自分へ〔〕
18. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
19. `{"op":"cleanse"}` — 状態異常解除〔〕
20. `{"op":"buff","e":"regen","t":180,"a":3}` — 強化〔e="regen", t=180, a=3〕
21. `{"op":"guard","t":95}` — 防御〔t=95〕
22. `{"op":"fx","p":"spark","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="spark", n=30, at="ring", r=4.0, y=0.7〕
23. `{"op":"sound","s":"anvil","v":0.8,"pi":1.1}` — 効果音〔s="anvil", v=0.8, pi=1.1〕
24. `{"op":"self"}` — 対象を自分へ〔〕
25. `{"op":"buff","e":"haste","t":280,"a":4}` — 強化〔e="haste", t=280, a=4〕
26. `{"op":"guard","t":140}` — 防御〔t=140〕
27. `{"op":"self"}` — 対象を自分へ〔〕
28. `{"op":"repair","v":180}` — 修理〔v=180〕
29. `{"op":"fx","p":"spark","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="spark", n=20, at="ring", r=4, y=0.4〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"haste","t":160,"a":123}` — 強化〔e="haste", t=160, a=123〕
32. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
33. `{"op":"eff","e":"fatigue","t":110,"a":123}` — 敵への状態異常〔e="fatigue", t=110, a=123〕
34. `{"op":"self"}` — 対象を自分へ〔〕
35. `{"op":"repair","v":220}` — 修理〔v=220〕
36. `{"op":"guard","t":80}` — 防御〔t=80〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 全救済実験・戒進の原理 — 超越神器（武器欄） (`relentless_research_legend`)

**現行パラメータ**：rank=3、damage登録値=578.1875、relics側CD=340tick、art側CD=340tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"allies","r":16}` — 味方対象〔r=16〕
06. `{"op":"buff","e":"regen","t":40,"a":1,"to":1}` — 強化〔e="regen", t=40, a=1, to=1〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
09. `{"op":"buff","e":"regen","t":45,"a":3}` — 強化〔e="regen", t=45, a=3〕
10. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（9命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"eff","e":"poison","t":200,"a":6}` — 敵への状態異常〔e="poison", t=200, a=6〕
03. `{"op":"dmg","m":5.0,"magic":1}` — 追加攻撃〔m=5.0, magic=1〕
04. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"poison","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"poison","t":160,"a":1}]〕
05. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"witch","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"witch","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
06. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"poison","t":135,"a":2},{"op":"fx","p":"witch","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"poison","t":135,"a":2},{"op":"fx","p":"witch","n":10,"at":"t","s":0.35}]〕
07. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
08. `{"op":"chance","p":0.35,"ops":[{"op":"victim"},{"op":"fx","p":"spark","n":20,"at":"t","s":0.33},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.35, ops=[{"op":"victim"},{"op":"fx","p":"spark","n":20,"at":"t","s":0.33},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":160,"x":2.5}]〕
09. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"wax","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"wax","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]〕

**権能発動時の命令（28命令）**：

01. `{"op":"fx","p":"sculk","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="sculk", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"sculk","n":4,"at":"self","s":0.7}` — 粒子演出〔p="sculk", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"happy","n":20,"at":"self"}` — 粒子演出〔p="happy", n=20, at="self"〕
04. `{"op":"fx","p":"witch","n":30,"at":"self"}` — 粒子演出〔p="witch", n=30, at="self"〕
05. `{"op":"sound","s":"spell","v":0.8,"pi":1.6}` — 効果音〔s="spell", v=0.8, pi=1.6〕
06. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
07. `{"op":"eff","e":"poison","t":1200,"a":9}` — 敵への状態異常〔e="poison", t=1200, a=9〕
08. `{"op":"stun","t":105}` — 行動停止〔t=105〕
09. `{"op":"transmute"}` — transmute〔〕
10. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
11. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
12. `{"op":"allies","r":48}` — 味方対象〔r=48〕
13. `{"op":"healpct","v":0.6,"to":1}` — 最大HP割合回復〔v=0.6, to=1〕
14. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
15. `{"op":"undying","t":180,"to":1}` — 死亡防護〔t=180, to=1〕
16. `{"op":"summon","k":"wolf","n":5}` — 召喚〔k="wolf", n=5〕
17. `{"op":"fx","p":"witch","n":12,"at":"t","s":0.5}` — 粒子演出〔p="witch", n=12, at="t", s=0.5〕
18. `{"op":"allies","r":26}` — 味方対象〔r=26〕
19. `{"op":"healpct","v":0.35}` — 最大HP割合回復〔v=0.35〕
20. `{"op":"cleanse"}` — 状態異常解除〔〕
21. `{"op":"self"}` — 対象を自分へ〔〕
22. `{"op":"buff","e":"regen","t":200,"a":2}` — 強化〔e="regen", t=200, a=2〕
23. `{"op":"fx","p":"spark","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="spark", n=50, at="ring", r=8.0, y=0.6〕
24. `{"op":"fx","p":"compost","n":32,"at":"line","r":30}` — 粒子演出〔p="compost", n=32, at="line", r=30〕
25. `{"op":"sound","s":"spell","v":1.15,"pi":0.95}` — 効果音〔s="spell", v=1.15, pi=0.95〕
26. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.relentless_research_legend.stage0","ops":[{"op":"fx","p":"spark","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"anvil","v":0.9,"pi":1.2},{"op":"fx","p":"wax","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"spark","n":6,"at":"line","r":10},{"op":"fx","p":"witch","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"spark","n":36,"at":"line","r":24},{"op":"sound","s":"spell","v":1.05,"pi":1.14},{"op":"line","r":56.0,"w":4.0},{"op":"dmg","m":3.645},{"op":"eff","e":"poison","t":105,"a":1},{"op":"self"},{"op":"buff","e":"haste","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.relentless_research_legend.stage1","ops":[{"op":"fx","p":"spark","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"anvil","v":1.05,"pi":1.0},{"op":"fx","p":"spark","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"wax","n":6,"at":"line","r":15},{"op":"fx","p":"spark","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"compost","n":32,"at":"line","r":30},{"op":"sound","s":"spell","v":1.15,"pi":0.95},{"op":"self"},{"op":"adapt"},{"op":"healpct","v":0.35},{"op":"summon","k":"golem","n":3},{"op":"area","r":16.0,"n":10},{"op":"eff","e":"fatigue","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.relentless_research_legend.stage2","ops":[{"op":"fx","p":"spark","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"anvil","v":1.25,"pi":0.75},{"op":"fx","p":"spark","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"wax","n":10,"at":"line","r":20},{"op":"fx","p":"witch","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"spark","n":48,"at":"line","r":48},{"op":"fx","p":"compost","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"spell","v":1.5,"pi":0.75},{"op":"area","r":32.0,"n":28},{"op":"dmg","m":9.558},{"op":"eff","e":"poison","t":150,"a":3},{"op":"summon","k":"golem","n":4},{"op":"self"},{"op":"buff","e":"regen","t":170,"a":3},{"op":"fx","p":"compost","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"witch","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":28.0,"n":25},{"op":"dmg","m":2.8},{"op":"summon","k":"golem","n":3},{"op":"self"},{"op":"adapt"},{"op":"healpct","v":0.4},{"op":"area","r":18.0,"n":16},{"op":"dmg","m":1.0},{"op":"eff","e":"fatigue","t":160,"a":2},{"op":"self"},{"op":"buff","e":"haste","t":240,"a":4},{"op":"self"},{"op":"summon","k":"golem","n":2},{"op":"fx","p":"spark","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"anvil","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"self"},{"op":"repair","v":260},{"op":"area","r":17,"n":9},{"op":"eff","e":"poison","t":65,"a":9}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.relentless_research_legend.stage0","ops":[{"op":"fx","p":"spark","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"anvil","v":0.9,"pi":1.2},{"op":"fx","p":"wax","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"spark","n":6,"at":"line","r":10},{"op":"fx","p":"witch","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"spark","n":36,"at":"line","r":24},{"op":"sound","s":"spell","v":1.05,"pi":1.14},{"op":"line","r":56.0,"w":4.0},{"op":"dmg","m":3.645},{"op":"eff","e":"poison","t":105,"a":1},{"op":"self"},{"op":"buff","e":"haste","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.relentless_research_legend.stage1","ops":[{"op":"fx","p":"spark","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"anvil","v":1.05,"pi":1.0},{"op":"fx","p":"spark","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"wax","n":6,"at":"line","r":15},{"op":"fx","p":"spark","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"compost","n":32,"at":"line","r":30},{"op":"sound","s":"spell","v":1.15,"pi":0.95},{"op":"self"},{"op":"adapt"},{"op":"healpct","v":0.35},{"op":"summon","k":"golem","n":3},{"op":"area","r":16.0,"n":10},{"op":"eff","e":"fatigue","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.relentless_research_legend.stage2","ops":[{"op":"fx","p":"spark","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"anvil","v":1.25,"pi":0.75},{"op":"fx","p":"spark","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"wax","n":10,"at":"line","r":20},{"op":"fx","p":"witch","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"spark","n":48,"at":"line","r":48},{"op":"fx","p":"compost","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"spell","v":1.5,"pi":0.75},{"op":"area","r":32.0,"n":28},{"op":"dmg","m":9.558},{"op":"eff","e":"poison","t":150,"a":3},{"op":"summon","k":"golem","n":4},{"op":"self"},{"op":"buff","e":"regen","t":170,"a":3},{"op":"fx","p":"compost","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"witch","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":28.0,"n":25},{"op":"dmg","m":2.8},{"op":"summon","k":"golem","n":3},{"op":"self"},{"op":"adapt"},{"op":"healpct","v":0.4},{"op":"area","r":18.0,"n":16},{"op":"dmg","m":1.0},{"op":"eff","e":"fatigue","t":160,"a":2},{"op":"self"},{"op":"buff","e":"haste","t":240,"a":4},{"op":"self"},{"op":"summon","k":"golem","n":2},{"op":"fx","p":"spark","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"anvil","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"fatigue","t":148,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"self"},{"op":"repair","v":260},{"op":"area","r":17,"n":9},{"op":"eff","e":"poison","t":65,"a":9}]}]〕
27. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
28. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 39. 外悪の魔導

**モブ側の動きの方向性**：人型の動作を最小化し、魔法陣と魔導書が独立運動する。。

### 禁理術式の鎖刃 — 討伐武器（メイン／武器欄） (`forbidden_arcana_weapon`)

**現行パラメータ**：rank=1、damage登録値=351.83333、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12。

**装備中の常時命令（5命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"adapt","t":40}` — adapt〔t=40〕
03. `{"op":"reflect","t":25,"r":6}` — 反射〔t=25, r=6〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（9命令）**：

01. `{"op":"chain","n":3,"r":8}` — chain〔n=3, r=8〕
02. `{"op":"dmg","m":0.3}` — 追加攻撃〔m=0.3〕
03. `{"op":"stun","t":10}` — 行動停止〔t=10〕
04. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"fatigue","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"fatigue","t":90,"a":0}]〕
05. `{"op":"chance","p":0.535,"ops":[{"op":"victim"},{"op":"fx","p":"portal","n":15,"at":"t","s":0.24},{"op":"mark","t":180,"x":2.07},{"op":"eff","e":"wither","t":79,"a":0}]}` — 抽選〔p=0.535, ops=[{"op":"victim"},{"op":"fx","p":"portal","n":15,"at":"t","s":0.24},{"op":"mark","t":180,"x":2.07},{"op":"eff","e":"wither","t":79,"a":0}]〕
06. `{"op":"chance","p":0.231,"ops":[{"op":"victim"},{"op":"dmg","m":0.305}]}` — 抽選〔p=0.231, ops=[{"op":"victim"},{"op":"dmg","m":0.305}]〕
07. `{"op":"chance","p":0.123,"ops":[{"op":"victim"},{"op":"fx","p":"portal","n":8,"at":"t","s":0.25},{"op":"strip"}]}` — 抽選〔p=0.123, ops=[{"op":"victim"},{"op":"fx","p":"portal","n":8,"at":"t","s":0.25},{"op":"strip"}]〕
08. `{"op":"chance","p":0.24,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":14,"at":"t","s":0.28},{"op":"eff","e":"wither","t":22,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.24, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":14,"at":"t","s":0.28},{"op":"eff","e":"wither","t":22,"a":124},{"op":"mark","t":100,"x":2.15}]〕
09. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":32,"a":3}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":32,"a":3}]〕

**権能発動時の命令（27命令）**：

01. `{"op":"fx","p":"witch","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="witch", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"witch","n":4,"at":"self","s":0.7}` — 粒子演出〔p="witch", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"portal","n":60,"at":"self"}` — 粒子演出〔p="portal", n=60, at="self"〕
04. `{"op":"fx","p":"sculk","n":30,"at":"self"}` — 粒子演出〔p="sculk", n=30, at="self"〕
05. `{"op":"sound","s":"spell","v":1.0,"pi":0.6}` — 効果音〔s="spell", v=1.0, pi=0.6〕
06. `{"op":"line","r":32,"w":3}` — 線分対象の取得〔r=32, w=3〕
07. `{"op":"dmg","m":1.92}` — 追加攻撃〔m=1.92〕
08. `{"op":"stun","t":65}` — 行動停止〔t=65〕
09. `{"op":"strip"}` — 強化解除〔〕
10. `{"op":"reflect","t":200,"r":16}` — 反射〔t=200, r=16〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"adapt","t":600}` — adapt〔t=600〕
13. `{"op":"fx","p":"portal","n":12,"at":"t","s":0.5}` — 粒子演出〔p="portal", n=12, at="t", s=0.5〕
14. `{"op":"fx","p":"enchant","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="enchant", n=46, at="ring", r=5.5, y=0.25〕
15. `{"op":"fx","p":"witch","n":36,"at":"line","r":24}` — 粒子演出〔p="witch", n=36, at="line", r=24〕
16. `{"op":"chain","n":6,"r":18.0}` — chain〔n=6, r=18.0〕
17. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
18. `{"op":"eff","e":"weakness","t":95,"a":2}` — 敵への状態異常〔e="weakness", t=95, a=2〕
19. `{"op":"fx","p":"enchant","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="enchant", n=16, at="ring", r=5.0〕
20. `{"op":"sound","s":"spell","v":0.75,"pi":1.15}` — 効果音〔s="spell", v=0.75, pi=1.15〕
21. `{"op":"chain","n":4,"r":12}` — chain〔n=4, r=12〕
22. `{"op":"dmg","m":1.0}` — 追加攻撃〔m=1.0〕
23. `{"op":"eff","e":"wither","t":65,"a":0}` — 敵への状態異常〔e="wither", t=65, a=0〕
24. `{"op":"fx","p":"enchant","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="enchant", n=24, at="ring", r=4.5, y=0.6〕
25. `{"op":"sound","s":"spell","v":0.8,"pi":0.8}` — 効果音〔s="spell", v=0.8, pi=0.8〕
26. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
27. `{"op":"eff","e":"wither","t":22,"a":124}` — 敵への状態異常〔e="wither", t=22, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 外悪魔導の寄生書 — 神威触媒（Curios relic_focus） (`forbidden_arcana_focus`)

**現行パラメータ**：rank=2、damage登録値=79.9227、relics側CD=150tick、art側CD=150tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"night","t":300,"a":0}` — 強化〔e="night", t=300, a=0〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"haste","t":45,"a":0}` — 強化〔e="haste", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"haste","t":42,"a":2}` — 強化〔e="haste", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（41命令）**：

01. `{"op":"fx","p":"witch","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="witch", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"witch","n":6,"at":"self","s":0.7}` — 粒子演出〔p="witch", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"portal","n":60,"at":"self"}` — 粒子演出〔p="portal", n=60, at="self"〕
04. `{"op":"fx","p":"sculk","n":30,"at":"self"}` — 粒子演出〔p="sculk", n=30, at="self"〕
05. `{"op":"sound","s":"spell","v":1.0,"pi":0.6}` — 効果音〔s="spell", v=1.0, pi=0.6〕
06. `{"op":"area","r":24,"n":36}` — 円形対象の取得〔r=24, n=36〕
07. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
08. `{"op":"stun","t":90}` — 行動停止〔t=90〕
09. `{"op":"eff","e":"wither","t":400,"a":4}` — 敵への状態異常〔e="wither", t=400, a=4〕
10. `{"op":"erase","r":32}` — erase〔r=32〕
11. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"haste","t":150,"a":1}` — 強化〔e="haste", t=150, a=1〕
14. `{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="witch", n=50, at="ring", r=8.0, y=0.6〕
15. `{"op":"fx","p":"sculk","n":32,"at":"line","r":30}` — 粒子演出〔p="sculk", n=32, at="line", r=30〕
16. `{"op":"sound","s":"spell","v":1.15,"pi":0.95}` — 効果音〔s="spell", v=1.15, pi=0.95〕
17. `{"op":"summon","k":"golem","n":3}` — 召喚〔k="golem", n=3〕
18. `{"op":"area","r":24.0,"n":19}` — 円形対象の取得〔r=24.0, n=19〕
19. `{"op":"dmg","m":2.6}` — 追加攻撃〔m=2.6〕
20. `{"op":"mark","t":125,"x":1.7}` — 刻印〔t=125, x=1.7〕
21. `{"op":"self"}` — 対象を自分へ〔〕
22. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
23. `{"op":"buff","e":"haste","t":150,"a":3}` — 強化〔e="haste", t=150, a=3〕
24. `{"op":"fx","p":"enchant","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="enchant", n=24, at="ring", r=12, y=0.5〕
25. `{"op":"sound","s":"spell","v":0.85,"pi":1.11}` — 効果音〔s="spell", v=0.85, pi=1.11〕
26. `{"op":"area","r":16.0,"n":12}` — 円形対象の取得〔r=16.0, n=12〕
27. `{"op":"dmg","m":0.8}` — 追加攻撃〔m=0.8〕
28. `{"op":"eff","e":"wither","t":140,"a":1}` — 敵への状態異常〔e="wither", t=140, a=1〕
29. `{"op":"self"}` — 対象を自分へ〔〕
30. `{"op":"buff","e":"haste","t":240,"a":3}` — 強化〔e="haste", t=240, a=3〕
31. `{"op":"chain","n":6,"r":24.0}` — chain〔n=6, r=24.0〕
32. `{"op":"dmg","m":0.45}` — 追加攻撃〔m=0.45〕
33. `{"op":"fx","p":"enchant","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="enchant", n=24, at="ring", r=5.5, y=0.7〕
34. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
35. `{"op":"eff","e":"wither","t":30,"a":123}` — 敵への状態異常〔e="wither", t=30, a=123〕
36. `{"op":"self"}` — 対象を自分へ〔〕
37. `{"op":"buff","e":"haste","t":100,"a":123}` — 強化〔e="haste", t=100, a=123〕
38. `{"op":"fx","p":"enchant","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="enchant", n=16, at="ring", r=3.7, y=0.55〕
39. `{"op":"area","r":16,"n":9}` — 円形対象の取得〔r=16, n=9〕
40. `{"op":"eff","e":"fatigue","t":75,"a":55}` — 敵への状態異常〔e="fatigue", t=75, a=55〕
41. `{"op":"mark","t":135,"x":1.8}` — 刻印〔t=135, x=1.8〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 自己破棄の術環 — 神格装飾品（Curios relic_charm） (`forbidden_arcana_charm`)

**現行パラメータ**：rank=1、damage登録値=79.9227、relics側CD=180tick、art側CD=180tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（12命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"adapt","t":40}` — adapt〔t=40〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"haste","t":45,"a":0}` — 強化〔e="haste", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
08. `{"op":"buff","e":"haste","t":45,"a":1}` — 強化〔e="haste", t=45, a=1〕
09. `{"op":"self"}` — 対象を自分へ〔〕
10. `{"op":"buff","e":"haste","t":42,"a":2}` — 強化〔e="haste", t=42, a=2〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"absorb","t":48,"a":4}` — 強化〔e="absorb", t=48, a=4〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（36命令）**：

01. `{"op":"fx","p":"witch","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="witch", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"witch","n":4,"at":"self","s":0.7}` — 粒子演出〔p="witch", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"portal","n":60,"at":"self"}` — 粒子演出〔p="portal", n=60, at="self"〕
04. `{"op":"fx","p":"sculk","n":30,"at":"self"}` — 粒子演出〔p="sculk", n=30, at="self"〕
05. `{"op":"sound","s":"spell","v":1.0,"pi":0.6}` — 効果音〔s="spell", v=1.0, pi=0.6〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"cleanse"}` — 状態異常解除〔〕
08. `{"op":"guard","t":100}` — 防御〔t=100〕
09. `{"op":"adapt","t":1200}` — adapt〔t=1200〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"haste","t":210,"a":1}` — 強化〔e="haste", t=210, a=1〕
13. `{"op":"fx","p":"enchant","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="enchant", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"witch","n":36,"at":"line","r":24}` — 粒子演出〔p="witch", n=36, at="line", r=24〕
15. `{"op":"sound","s":"spell","v":1.05,"pi":1.14}` — 効果音〔s="spell", v=1.05, pi=1.14〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"guard","t":95}` — 防御〔t=95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
20. `{"op":"cleanse"}` — 状態異常解除〔〕
21. `{"op":"buff","e":"haste","t":180,"a":3}` — 強化〔e="haste", t=180, a=3〕
22. `{"op":"guard","t":95}` — 防御〔t=95〕
23. `{"op":"fx","p":"enchant","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="enchant", n=30, at="ring", r=4.0, y=0.7〕
24. `{"op":"sound","s":"spell","v":0.8,"pi":1.1}` — 効果音〔s="spell", v=0.8, pi=1.1〕
25. `{"op":"self"}` — 対象を自分へ〔〕
26. `{"op":"buff","e":"haste","t":300,"a":4}` — 強化〔e="haste", t=300, a=4〕
27. `{"op":"guard","t":155}` — 防御〔t=155〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"reflect","t":80,"r":18}` — 反射〔t=80, r=18〕
30. `{"op":"fx","p":"enchant","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="enchant", n=20, at="ring", r=4, y=0.4〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"haste","t":160,"a":123}` — 強化〔e="haste", t=160, a=123〕
33. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
34. `{"op":"eff","e":"wither","t":22,"a":123}` — 敵への状態異常〔e="wither", t=22, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 魔導自己研究・外悪の深淵 — 超越神器（武器欄） (`forbidden_arcana_legend`)

**現行パラメータ**：rank=3、damage登録値=578.1875、relics側CD=335tick、art側CD=335tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12。

**装備中の常時命令（10命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"adapt","t":40}` — adapt〔t=40〕
06. `{"op":"reflect","t":25,"r":10}` — 反射〔t=25, r=10〕
07. `{"op":"self"}` — 対象を自分へ〔〕
08. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
09. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕
10. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（8命令）**：

01. `{"op":"chain","n":6,"r":12}` — chain〔n=6, r=12〕
02. `{"op":"dmg","m":0.5}` — 追加攻撃〔m=0.5〕
03. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"fatigue","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"fatigue","t":160,"a":1}]〕
04. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
05. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"sculk","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"sculk","n":10,"at":"t","s":0.35}]〕
06. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
07. `{"op":"chance","p":0.375,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":20,"at":"t","s":0.33},{"op":"eff","e":"wither","t":30,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.375, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":20,"at":"t","s":0.33},{"op":"eff","e":"wither","t":30,"a":124},{"op":"mark","t":160,"x":2.5}]〕
08. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"enchant","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":62,"a":5}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"enchant","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"levitate","t":62,"a":5}]〕

**権能発動時の命令（25命令）**：

01. `{"op":"fx","p":"witch","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="witch", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"witch","n":4,"at":"self","s":0.7}` — 粒子演出〔p="witch", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"portal","n":60,"at":"self"}` — 粒子演出〔p="portal", n=60, at="self"〕
04. `{"op":"fx","p":"sculk","n":30,"at":"self"}` — 粒子演出〔p="sculk", n=30, at="self"〕
05. `{"op":"sound","s":"spell","v":1.0,"pi":0.6}` — 効果音〔s="spell", v=1.0, pi=0.6〕
06. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
07. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
08. `{"op":"stun","t":105}` — 行動停止〔t=105〕
09. `{"op":"dmg","m":3.36}` — 追加攻撃〔m=3.36〕
10. `{"op":"dmg","m":5.6,"magic":1}` — 追加攻撃〔m=5.6, magic=1〕
11. `{"op":"reflect","t":600,"r":48}` — 反射〔t=600, r=48〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"adapt","t":2400}` — adapt〔t=2400〕
14. `{"op":"undying","t":180}` — 死亡防護〔t=180〕
15. `{"op":"erase","r":64}` — erase〔r=64〕
16. `{"op":"fx","p":"portal","n":12,"at":"t","s":0.5}` — 粒子演出〔p="portal", n=12, at="t", s=0.5〕
17. `{"op":"chain","n":5,"r":16}` — chain〔n=5, r=16〕
18. `{"op":"dmg","m":1.7}` — 追加攻撃〔m=1.7〕
19. `{"op":"mark","t":100,"x":1.4}` — 刻印〔t=100, x=1.4〕
20. `{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="witch", n=50, at="ring", r=8.0, y=0.6〕
21. `{"op":"fx","p":"sculk","n":32,"at":"line","r":30}` — 粒子演出〔p="sculk", n=32, at="line", r=30〕
22. `{"op":"sound","s":"spell","v":1.15,"pi":0.95}` — 効果音〔s="spell", v=1.15, pi=0.95〕
23. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.forbidden_arcana_legend.stage0","ops":[{"op":"fx","p":"enchant","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"spell","v":0.9,"pi":1.2},{"op":"fx","p":"enchant","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"witch","n":6,"at":"line","r":10},{"op":"fx","p":"enchant","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"witch","n":36,"at":"line","r":24},{"op":"sound","s":"spell","v":1.05,"pi":1.14},{"op":"chain","n":6,"r":18.0},{"op":"dmg","m":3.78},{"op":"eff","e":"weakness","t":95,"a":2},{"op":"self"},{"op":"buff","e":"haste","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.forbidden_arcana_legend.stage1","ops":[{"op":"fx","p":"enchant","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"spell","v":1.05,"pi":1.0},{"op":"fx","p":"witch","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"enchant","n":6,"at":"line","r":15},{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"sculk","n":32,"at":"line","r":30},{"op":"sound","s":"spell","v":1.15,"pi":0.95},{"op":"summon","k":"golem","n":3},{"op":"area","r":24.0,"n":19},{"op":"dmg","m":3.77},{"op":"mark","t":125,"x":2.21},{"op":"area","r":18.0,"n":10},{"op":"eff","e":"wither","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.forbidden_arcana_legend.stage2","ops":[{"op":"fx","p":"enchant","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"spell","v":1.25,"pi":0.75},{"op":"fx","p":"witch","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"enchant","n":10,"at":"line","r":20},{"op":"fx","p":"enchant","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"witch","n":48,"at":"line","r":48},{"op":"fx","p":"sculk","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"spell","v":1.5,"pi":0.75},{"op":"area","r":36.0,"n":29},{"op":"dmg","m":10.044},{"op":"strip"},{"op":"stun","t":55},{"op":"self"},{"op":"buff","e":"haste","t":170,"a":4},{"op":"fx","p":"sculk","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"sculk","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":32.0,"n":27},{"op":"dmg","m":3.1},{"op":"summon","k":"golem","n":3},{"op":"self"},{"op":"buff","e":"haste","t":180,"a":5},{"op":"area","r":21.0,"n":16},{"op":"dmg","m":1.1},{"op":"eff","e":"wither","t":160,"a":2},{"op":"self"},{"op":"buff","e":"haste","t":240,"a":4},{"op":"chain","n":6,"r":24.0},{"op":"dmg","m":0.45},{"op":"fx","p":"enchant","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"spell","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"wither","t":30,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"fatigue","t":75,"a":55},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.forbidden_arcana_legend.stage0","ops":[{"op":"fx","p":"enchant","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"spell","v":0.9,"pi":1.2},{"op":"fx","p":"enchant","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"witch","n":6,"at":"line","r":10},{"op":"fx","p":"enchant","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"witch","n":36,"at":"line","r":24},{"op":"sound","s":"spell","v":1.05,"pi":1.14},{"op":"chain","n":6,"r":18.0},{"op":"dmg","m":3.78},{"op":"eff","e":"weakness","t":95,"a":2},{"op":"self"},{"op":"buff","e":"haste","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.forbidden_arcana_legend.stage1","ops":[{"op":"fx","p":"enchant","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"spell","v":1.05,"pi":1.0},{"op":"fx","p":"witch","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"enchant","n":6,"at":"line","r":15},{"op":"fx","p":"witch","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"sculk","n":32,"at":"line","r":30},{"op":"sound","s":"spell","v":1.15,"pi":0.95},{"op":"summon","k":"golem","n":3},{"op":"area","r":24.0,"n":19},{"op":"dmg","m":3.77},{"op":"mark","t":125,"x":2.21},{"op":"area","r":18.0,"n":10},{"op":"eff","e":"wither","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.forbidden_arcana_legend.stage2","ops":[{"op":"fx","p":"enchant","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"spell","v":1.25,"pi":0.75},{"op":"fx","p":"witch","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"enchant","n":10,"at":"line","r":20},{"op":"fx","p":"enchant","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"witch","n":48,"at":"line","r":48},{"op":"fx","p":"sculk","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"spell","v":1.5,"pi":0.75},{"op":"area","r":36.0,"n":29},{"op":"dmg","m":10.044},{"op":"strip"},{"op":"stun","t":55},{"op":"self"},{"op":"buff","e":"haste","t":170,"a":4},{"op":"fx","p":"sculk","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"sculk","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":32.0,"n":27},{"op":"dmg","m":3.1},{"op":"summon","k":"golem","n":3},{"op":"self"},{"op":"buff","e":"haste","t":180,"a":5},{"op":"area","r":21.0,"n":16},{"op":"dmg","m":1.1},{"op":"eff","e":"wither","t":160,"a":2},{"op":"self"},{"op":"buff","e":"haste","t":240,"a":4},{"op":"chain","n":6,"r":24.0},{"op":"dmg","m":0.45},{"op":"fx","p":"enchant","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"spell","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"wither","t":30,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"fatigue","t":75,"a":55},{"op":"mark","t":135,"x":1.8}]}]〕
24. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
25. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 40. 救堕せし勇者

**モブ側の動きの方向性**：聖剣の型、祈り、ためらいと涙を別の演技レイヤーで表す。。

### 救堕の古聖剣 — 討伐武器（メイン／武器欄） (`fallen_savior_weapon`)

**現行パラメータ**：rank=1、damage登録値=341.33333、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:sweeping_edge:25。

**装備中の常時命令（5命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"regen","t":40,"a":0}` — 強化〔e="regen", t=40, a=0〕
03. `{"op":"buff","e":"resist","t":40,"a":0}` — 強化〔e="resist", t=40, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（9命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"burn","s":4}` — burn〔s=4〕
03. `{"op":"dmg","m":1.8,"magic":1}` — 追加攻撃〔m=1.8, magic=1〕
04. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"wither","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"wither","t":90,"a":0}]〕
05. `{"op":"chance","p":0.58,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":17,"at":"t","s":0.24},{"op":"mark","t":200,"x":2.21},{"op":"eff","e":"weakness","t":91,"a":1}]}` — 抽選〔p=0.58, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":17,"at":"t","s":0.24},{"op":"mark","t":200,"x":2.21},{"op":"eff","e":"weakness","t":91,"a":1}]〕
06. `{"op":"chance","p":0.258,"ops":[{"op":"victim"},{"op":"dmg","m":0.34}]}` — 抽選〔p=0.258, ops=[{"op":"victim"},{"op":"dmg","m":0.34}]〕
07. `{"op":"chance","p":0.142,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":8,"at":"t","s":0.25},{"op":"strip"}]}` — 抽選〔p=0.142, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":8,"at":"t","s":0.25},{"op":"strip"}]〕
08. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":14,"at":"t","s":0.28},{"op":"eff","e":"weakness","t":100,"a":124},{"op":"mark","t":100,"x":2.15}]〕
09. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":55,"a":12}]〕

**権能発動時の命令（29命令）**：

01. `{"op":"fx","p":"end_rod","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="end_rod", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"end_rod","n":4,"at":"self","s":0.7}` — 粒子演出〔p="end_rod", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":40,"at":"self"}` — 粒子演出〔p="end_rod", n=40, at="self"〕
04. `{"op":"fx","p":"ash","n":30,"at":"self"}` — 粒子演出〔p="ash", n=30, at="self"〕
05. `{"op":"sound","s":"totem","v":0.6,"pi":0.8}` — 効果音〔s="totem", v=0.6, pi=0.8〕
06. `{"op":"fx","p":"end_rod","n":60,"at":"line","r":40}` — 粒子演出〔p="end_rod", n=60, at="line", r=40〕
07. `{"op":"line","r":40,"w":3}` — 線分対象の取得〔r=40, w=3〕
08. `{"op":"dmg","m":2.4}` — 追加攻撃〔m=2.4〕
09. `{"op":"burn","s":8}` — burn〔s=8〕
10. `{"op":"dmg","m":2.16,"magic":1}` — 追加攻撃〔m=2.16, magic=1〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"cleanse"}` — 状態異常解除〔〕
13. `{"op":"healpct","v":0.25}` — 最大HP割合回復〔v=0.25〕
14. `{"op":"fx","p":"end_rod","n":12,"at":"t","s":0.5}` — 粒子演出〔p="end_rod", n=12, at="t", s=0.5〕
15. `{"op":"fx","p":"end_rod","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="end_rod", n=46, at="ring", r=5.5, y=0.25〕
16. `{"op":"fx","p":"soul","n":36,"at":"line","r":24}` — 粒子演出〔p="soul", n=36, at="line", r=24〕
17. `{"op":"line","r":57.0,"w":4.0}` — 線分対象の取得〔r=57.0, w=4.0〕
18. `{"op":"dmg","m":3.1}` — 追加攻撃〔m=3.1〕
19. `{"op":"strip"}` — 強化解除〔〕
20. `{"op":"mark","t":140,"x":1.7}` — 刻印〔t=140, x=1.7〕
21. `{"op":"fx","p":"end_rod","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="end_rod", n=16, at="ring", r=5.0〕
22. `{"op":"sound","s":"sonic","v":0.75,"pi":1.15}` — 効果音〔s="sonic", v=0.75, pi=1.15〕
23. `{"op":"line","r":18,"w":2}` — 線分対象の取得〔r=18, w=2〕
24. `{"op":"dmg","m":1.05}` — 追加攻撃〔m=1.05〕
25. `{"op":"eff","e":"weakness","t":65,"a":0}` — 敵への状態異常〔e="weakness", t=65, a=0〕
26. `{"op":"fx","p":"end_rod","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="end_rod", n=24, at="ring", r=4.5, y=0.6〕
27. `{"op":"sound","s":"totem","v":0.8,"pi":0.8}` — 効果音〔s="totem", v=0.8, pi=0.8〕
28. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
29. `{"op":"eff","e":"weakness","t":100,"a":124}` — 敵への状態異常〔e="weakness", t=100, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 悪の未来を断つ聖印 — 神威触媒（Curios relic_focus） (`fallen_savior_focus`)

**現行パラメータ**：rank=2、damage登録値=86.0706、relics側CD=145tick、art側CD=145tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"night","t":300,"a":0}` — 強化〔e="night", t=300, a=0〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"strength","t":45,"a":0}` — 強化〔e="strength", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"strength","t":45,"a":2}` — 強化〔e="strength", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"resist","t":42,"a":2}` — 強化〔e="resist", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（42命令）**：

01. `{"op":"fx","p":"end_rod","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="end_rod", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"end_rod","n":6,"at":"self","s":0.7}` — 粒子演出〔p="end_rod", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":40,"at":"self"}` — 粒子演出〔p="end_rod", n=40, at="self"〕
04. `{"op":"fx","p":"ash","n":30,"at":"self"}` — 粒子演出〔p="ash", n=30, at="self"〕
05. `{"op":"sound","s":"totem","v":0.6,"pi":0.8}` — 効果音〔s="totem", v=0.6, pi=0.8〕
06. `{"op":"area","r":32,"n":36}` — 円形対象の取得〔r=32, n=36〕
07. `{"op":"eff","e":"glow","t":600,"a":0}` — 敵への状態異常〔e="glow", t=600, a=0〕
08. `{"op":"mark","t":600,"x":3.0}` — 刻印〔t=600, x=3.0〕
09. `{"op":"lightning"}` — lightning〔〕
10. `{"op":"dmg","m":1.5}` — 追加攻撃〔m=1.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"cleanse"}` — 状態異常解除〔〕
13. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
14. `{"op":"self"}` — 対象を自分へ〔〕
15. `{"op":"buff","e":"strength","t":150,"a":1}` — 強化〔e="strength", t=150, a=1〕
16. `{"op":"fx","p":"soul","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="soul", n=50, at="ring", r=8.0, y=0.6〕
17. `{"op":"fx","p":"crit","n":32,"at":"line","r":30}` — 粒子演出〔p="crit", n=32, at="line", r=30〕
18. `{"op":"sound","s":"wither","v":1.15,"pi":0.95}` — 効果音〔s="wither", v=1.15, pi=0.95〕
19. `{"op":"area","r":24.0,"n":18}` — 円形対象の取得〔r=24.0, n=18〕
20. `{"op":"stun","t":48}` — 行動停止〔t=48〕
21. `{"op":"eff","e":"weakness","t":105,"a":2}` — 敵への状態異常〔e="weakness", t=105, a=2〕
22. `{"op":"self"}` — 対象を自分へ〔〕
23. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
24. `{"op":"buff","e":"strength","t":150,"a":3}` — 強化〔e="strength", t=150, a=3〕
25. `{"op":"fx","p":"end_rod","n":24,"at":"ring","r":12,"y":0.5}` — 粒子演出〔p="end_rod", n=24, at="ring", r=12, y=0.5〕
26. `{"op":"sound","s":"totem","v":0.85,"pi":1.18}` — 効果音〔s="totem", v=0.85, pi=1.18〕
27. `{"op":"line","r":36.0,"w":2.5}` — 線分対象の取得〔r=36.0, w=2.5〕
28. `{"op":"dmg","m":0.85}` — 追加攻撃〔m=0.85〕
29. `{"op":"eff","e":"weakness","t":160,"a":1}` — 敵への状態異常〔e="weakness", t=160, a=1〕
30. `{"op":"self"}` — 対象を自分へ〔〕
31. `{"op":"buff","e":"resist","t":200,"a":3}` — 強化〔e="resist", t=200, a=3〕
32. `{"op":"area","r":20,"n":10}` — 円形対象の取得〔r=20, n=10〕
33. `{"op":"strip"}` — 強化解除〔〕
34. `{"op":"fx","p":"end_rod","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="end_rod", n=24, at="ring", r=5.5, y=0.7〕
35. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
36. `{"op":"eff","e":"weakness","t":135,"a":123}` — 敵への状態異常〔e="weakness", t=135, a=123〕
37. `{"op":"self"}` — 対象を自分へ〔〕
38. `{"op":"buff","e":"resist","t":140,"a":2}` — 強化〔e="resist", t=140, a=2〕
39. `{"op":"fx","p":"end_rod","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="end_rod", n=16, at="ring", r=3.7, y=0.55〕
40. `{"op":"area","r":14,"n":7}` — 円形対象の取得〔r=14, n=7〕
41. `{"op":"eff","e":"weakness","t":85,"a":20}` — 敵への状態異常〔e="weakness", t=85, a=20〕
42. `{"op":"mark","t":115,"x":1.8}` — 刻印〔t=115, x=1.8〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 不滅祝福の胸章 — 神格装飾品（Curios relic_charm） (`fallen_savior_charm`)

**現行パラメータ**：rank=1、damage登録値=86.0706、relics側CD=175tick、art側CD=175tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（11命令）**：

01. `{"op":"low","pct":0.3,"ops":[{"op":"self"},{"op":"undying","t":40},{"op":"buff","e":"regen","t":40,"a":4}]}` — low〔pct=0.3, ops=[{"op":"self"},{"op":"undying","t":40},{"op":"buff","e":"regen","t":40,"a":4}]〕
02. `{"op":"self"}` — 対象を自分へ〔〕
03. `{"op":"buff","e":"strength","t":45,"a":0}` — 強化〔e="strength", t=45, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
06. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
07. `{"op":"buff","e":"strength","t":45,"a":1}` — 強化〔e="strength", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"resist","t":42,"a":2}` — 強化〔e="resist", t=42, a=2〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"regen","t":48,"a":4}` — 強化〔e="regen", t=48, a=4〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（36命令）**：

01. `{"op":"fx","p":"end_rod","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="end_rod", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"end_rod","n":4,"at":"self","s":0.7}` — 粒子演出〔p="end_rod", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":40,"at":"self"}` — 粒子演出〔p="end_rod", n=40, at="self"〕
04. `{"op":"fx","p":"ash","n":30,"at":"self"}` — 粒子演出〔p="ash", n=30, at="self"〕
05. `{"op":"sound","s":"totem","v":0.6,"pi":0.8}` — 効果音〔s="totem", v=0.6, pi=0.8〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"undying","t":100}` — 死亡防護〔t=100〕
08. `{"op":"healpct","v":0.25}` — 最大HP割合回復〔v=0.25〕
09. `{"op":"cleanse"}` — 状態異常解除〔〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"strength","t":210,"a":1}` — 強化〔e="strength", t=210, a=1〕
13. `{"op":"fx","p":"end_rod","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="end_rod", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"soul","n":36,"at":"line","r":24}` — 粒子演出〔p="soul", n=36, at="line", r=24〕
15. `{"op":"sound","s":"wither","v":1.05,"pi":1.14}` — 効果音〔s="wither", v=1.05, pi=1.14〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"guard","t":95}` — 防御〔t=95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
20. `{"op":"cleanse"}` — 状態異常解除〔〕
21. `{"op":"buff","e":"strength","t":180,"a":3}` — 強化〔e="strength", t=180, a=3〕
22. `{"op":"guard","t":95}` — 防御〔t=95〕
23. `{"op":"fx","p":"end_rod","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="end_rod", n=30, at="ring", r=4.0, y=0.7〕
24. `{"op":"sound","s":"totem","v":0.8,"pi":1.1}` — 効果音〔s="totem", v=0.8, pi=1.1〕
25. `{"op":"self"}` — 対象を自分へ〔〕
26. `{"op":"buff","e":"resist","t":260,"a":4}` — 強化〔e="resist", t=260, a=4〕
27. `{"op":"guard","t":170}` — 防御〔t=170〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"buff","e":"resist","t":240,"a":2}` — 強化〔e="resist", t=240, a=2〕
30. `{"op":"fx","p":"end_rod","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="end_rod", n=20, at="ring", r=4, y=0.4〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"resist","t":140,"a":2}` — 強化〔e="resist", t=140, a=2〕
33. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
34. `{"op":"eff","e":"weakness","t":100,"a":123}` — 敵への状態異常〔e="weakness", t=100, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 全悪救滅・神殺しの聖剣 — 超越神器（武器欄） (`fallen_savior_legend`)

**現行パラメータ**：rank=3、damage登録値=479.75、relics側CD=330tick、art側CD=330tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:12、minecraft:sweeping_edge:25。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"low","pct":0.4,"ops":[{"op":"self"},{"op":"undying","t":40}]}` — low〔pct=0.4, ops=[{"op":"self"},{"op":"undying","t":40}]〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
08. `{"op":"buff","e":"strength","t":45,"a":3}` — 強化〔e="strength", t=45, a=3〕
09. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（9命令）**：

01. `{"op":"victim"}` — 対象を敵へ〔〕
02. `{"op":"dmg","m":5.0,"magic":1}` — 追加攻撃〔m=5.0, magic=1〕
03. `{"op":"burn","s":6}` — burn〔s=6〕
04. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"wither","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"wither","t":160,"a":1}]〕
05. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
06. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"end_rod","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"weakness","t":135,"a":2},{"op":"fx","p":"end_rod","n":10,"at":"t","s":0.35}]〕
07. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
08. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":20,"at":"t","s":0.33},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":160,"x":2.5}]〕
09. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"slow","t":85,"a":14}]〕

**権能発動時の命令（29命令）**：

01. `{"op":"fx","p":"end_rod","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="end_rod", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"end_rod","n":4,"at":"self","s":0.7}` — 粒子演出〔p="end_rod", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"end_rod","n":40,"at":"self"}` — 粒子演出〔p="end_rod", n=40, at="self"〕
04. `{"op":"fx","p":"ash","n":30,"at":"self"}` — 粒子演出〔p="ash", n=30, at="self"〕
05. `{"op":"sound","s":"totem","v":0.6,"pi":0.8}` — 効果音〔s="totem", v=0.6, pi=0.8〕
06. `{"op":"fx","p":"end_rod","n":72,"at":"line","r":96}` — 粒子演出〔p="end_rod", n=72, at="line", r=96〕
07. `{"op":"line","r":96,"w":5}` — 線分対象の取得〔r=96, w=5〕
08. `{"op":"dmg","m":3.36}` — 追加攻撃〔m=3.36〕
09. `{"op":"dmg","m":5.6,"magic":1}` — 追加攻撃〔m=5.6, magic=1〕
10. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
11. `{"op":"lightning"}` — lightning〔〕
12. `{"op":"dmg","m":2.24}` — 追加攻撃〔m=2.24〕
13. `{"op":"stun","t":105}` — 行動停止〔t=105〕
14. `{"op":"self"}` — 対象を自分へ〔〕
15. `{"op":"undying","t":180}` — 死亡防護〔t=180〕
16. `{"op":"healpct","v":0.6}` — 最大HP割合回復〔v=0.6〕
17. `{"op":"cleanse"}` — 状態異常解除〔〕
18. `{"op":"buff","e":"strength","t":1200,"a":10}` — 強化〔e="strength", t=1200, a=10〕
19. `{"op":"fx","p":"end_rod","n":12,"at":"t","s":0.5}` — 粒子演出〔p="end_rod", n=12, at="t", s=0.5〕
20. `{"op":"line","r":64,"w":3}` — 線分対象の取得〔r=64, w=3〕
21. `{"op":"dmg","m":1.8}` — 追加攻撃〔m=1.8〕
22. `{"op":"strip"}` — 強化解除〔〕
23. `{"op":"mark","t":120,"x":1.6}` — 刻印〔t=120, x=1.6〕
24. `{"op":"fx","p":"soul","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="soul", n=50, at="ring", r=8.0, y=0.6〕
25. `{"op":"fx","p":"crit","n":32,"at":"line","r":30}` — 粒子演出〔p="crit", n=32, at="line", r=30〕
26. `{"op":"sound","s":"wither","v":1.15,"pi":0.95}` — 効果音〔s="wither", v=1.15, pi=0.95〕
27. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.fallen_savior_legend.stage0","ops":[{"op":"fx","p":"end_rod","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"totem","v":0.9,"pi":1.2},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"ash","n":6,"at":"line","r":10},{"op":"fx","p":"end_rod","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"soul","n":36,"at":"line","r":24},{"op":"sound","s":"wither","v":1.05,"pi":1.14},{"op":"line","r":57.0,"w":4.0},{"op":"dmg","m":4.185},{"op":"strip"},{"op":"mark","t":140,"x":2.21},{"op":"self"},{"op":"buff","e":"resist","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.fallen_savior_legend.stage1","ops":[{"op":"fx","p":"end_rod","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"totem","v":1.05,"pi":1.0},{"op":"fx","p":"ash","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":15},{"op":"fx","p":"soul","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"crit","n":32,"at":"line","r":30},{"op":"sound","s":"wither","v":1.15,"pi":0.95},{"op":"area","r":24.0,"n":18},{"op":"stun","t":48},{"op":"eff","e":"weakness","t":105,"a":2},{"op":"area","r":20.0,"n":10},{"op":"eff","e":"weakness","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.fallen_savior_legend.stage2","ops":[{"op":"fx","p":"end_rod","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"totem","v":1.25,"pi":0.75},{"op":"fx","p":"ash","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"end_rod","n":10,"at":"line","r":20},{"op":"fx","p":"end_rod","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"soul","n":48,"at":"line","r":48},{"op":"fx","p":"crit","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"wither","v":1.5,"pi":0.75},{"op":"line","r":76.0,"w":5.0},{"op":"dmg","m":11.178},{"op":"strip"},{"op":"area","r":25.0,"n":20},{"op":"dmg","m":4.86},{"op":"self"},{"op":"buff","e":"strength","t":175,"a":3},{"op":"fx","p":"crit","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"end_rod","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"line","r":76.0,"w":4.0},{"op":"dmg","m":3.5},{"op":"strip"},{"op":"area","r":21.0,"n":20},{"op":"dmg","m":1.7},{"op":"self"},{"op":"buff","e":"strength","t":175,"a":4},{"op":"line","r":44.0,"w":4.0},{"op":"dmg","m":1.2},{"op":"eff","e":"weakness","t":160,"a":2},{"op":"self"},{"op":"buff","e":"resist","t":240,"a":4},{"op":"area","r":20,"n":10},{"op":"strip"},{"op":"fx","p":"end_rod","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"totem","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"weakness","t":85,"a":20},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.fallen_savior_legend.stage0","ops":[{"op":"fx","p":"end_rod","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"totem","v":0.9,"pi":1.2},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"ash","n":6,"at":"line","r":10},{"op":"fx","p":"end_rod","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"soul","n":36,"at":"line","r":24},{"op":"sound","s":"wither","v":1.05,"pi":1.14},{"op":"line","r":57.0,"w":4.0},{"op":"dmg","m":4.185},{"op":"strip"},{"op":"mark","t":140,"x":2.21},{"op":"self"},{"op":"buff","e":"resist","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.fallen_savior_legend.stage1","ops":[{"op":"fx","p":"end_rod","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"totem","v":1.05,"pi":1.0},{"op":"fx","p":"ash","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":15},{"op":"fx","p":"soul","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"crit","n":32,"at":"line","r":30},{"op":"sound","s":"wither","v":1.15,"pi":0.95},{"op":"area","r":24.0,"n":18},{"op":"stun","t":48},{"op":"eff","e":"weakness","t":105,"a":2},{"op":"area","r":20.0,"n":10},{"op":"eff","e":"weakness","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.fallen_savior_legend.stage2","ops":[{"op":"fx","p":"end_rod","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"totem","v":1.25,"pi":0.75},{"op":"fx","p":"ash","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"end_rod","n":10,"at":"line","r":20},{"op":"fx","p":"end_rod","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"soul","n":48,"at":"line","r":48},{"op":"fx","p":"crit","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"wither","v":1.5,"pi":0.75},{"op":"line","r":76.0,"w":5.0},{"op":"dmg","m":11.178},{"op":"strip"},{"op":"area","r":25.0,"n":20},{"op":"dmg","m":4.86},{"op":"self"},{"op":"buff","e":"strength","t":175,"a":3},{"op":"fx","p":"crit","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"end_rod","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"line","r":76.0,"w":4.0},{"op":"dmg","m":3.5},{"op":"strip"},{"op":"area","r":21.0,"n":20},{"op":"dmg","m":1.7},{"op":"self"},{"op":"buff","e":"strength","t":175,"a":4},{"op":"line","r":44.0,"w":4.0},{"op":"dmg","m":1.2},{"op":"eff","e":"weakness","t":160,"a":2},{"op":"self"},{"op":"buff","e":"resist","t":240,"a":4},{"op":"area","r":20,"n":10},{"op":"strip"},{"op":"fx","p":"end_rod","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"totem","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"weakness","t":135,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"weakness","t":85,"a":20},{"op":"mark","t":135,"x":1.8}]}]〕
28. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
29. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

## 41. 甘契の未怪

**モブ側の動きの方向性**：手を差し伸べ契約書を開く、金貨を弾く、羽根ペンで署名を促す。。

### 未来債権の天秤 — 討伐武器（メイン／武器欄） (`sweet_pact_weapon`)

**現行パラメータ**：rank=1、damage登録値=578.5、relics側CD=110tick、art側CD=110tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（4命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"luck","t":40,"a":2}` — 強化〔e="luck", t=40, a=2〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"haste","t":45,"a":2}` — 強化〔e="haste", t=45, a=2〕

**命中したときの命令（7命令）**：

01. `{"op":"chance","p":0.25,"ops":[{"op":"give","item":"emerald","n":1}]}` — 抽選〔p=0.25, ops=[{"op":"give","item":"emerald","n":1}]〕
02. `{"op":"chance","p":0.25,"ops":[{"op":"victim"},{"op":"eff","e":"weakness","t":90,"a":0}]}` — 抽選〔p=0.25, ops=[{"op":"victim"},{"op":"eff","e":"weakness","t":90,"a":0}]〕
03. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"fx","p":"wax","n":9,"at":"t","s":0.24},{"op":"mark","t":120,"x":1.65},{"op":"eff","e":"slow","t":103,"a":0}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"fx","p":"wax","n":9,"at":"t","s":0.24},{"op":"mark","t":120,"x":1.65},{"op":"eff","e":"slow","t":103,"a":0}]〕
04. `{"op":"chance","p":0.15,"ops":[{"op":"victim"},{"op":"dmg","m":0.2}]}` — 抽選〔p=0.15, ops=[{"op":"victim"},{"op":"dmg","m":0.2}]〕
05. `{"op":"chance","p":0.085,"ops":[{"op":"victim"},{"op":"fx","p":"wax","n":8,"at":"t","s":0.25},{"op":"eff","e":"glow","t":85,"a":0}]}` — 抽選〔p=0.085, ops=[{"op":"victim"},{"op":"fx","p":"wax","n":8,"at":"t","s":0.25},{"op":"eff","e":"glow","t":85,"a":0}]〕
06. `{"op":"chance","p":0.18,"ops":[{"op":"victim"},{"op":"fx","p":"wax","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]}` — 抽選〔p=0.18, ops=[{"op":"victim"},{"op":"fx","p":"wax","n":14,"at":"t","s":0.28},{"op":"eff","e":"slow","t":32,"a":124},{"op":"mark","t":100,"x":2.15}]〕
07. `{"op":"chance","p":0.16,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"wither","t":48,"a":5}]}` — 抽選〔p=0.16, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"wither","t":48,"a":5}]〕

**権能発動時の命令（31命令）**：

01. `{"op":"fx","p":"enchant","n":8,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="enchant", n=8, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"enchant","n":4,"at":"self","s":0.7}` — 粒子演出〔p="enchant", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"wax","n":40,"at":"self"}` — 粒子演出〔p="wax", n=40, at="self"〕
04. `{"op":"fx","p":"happy","n":20,"at":"self"}` — 粒子演出〔p="happy", n=20, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":0.9}` — 効果音〔s="chime", v=1.0, pi=0.9〕
06. `{"op":"area","r":20,"n":36}` — 円形対象の取得〔r=20, n=36〕
07. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
08. `{"op":"stun","t":65}` — 行動停止〔t=65〕
09. `{"op":"dmg","m":1.44}` — 追加攻撃〔m=1.44〕
10. `{"op":"give","item":"emerald","n":6}` — give〔item="emerald", n=6〕
11. `{"op":"give","item":"gold","n":4}` — give〔item="gold", n=4〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"healpct","v":0.25}` — 最大HP割合回復〔v=0.25〕
14. `{"op":"food"}` — food〔〕
15. `{"op":"fx","p":"wax","n":12,"at":"t","s":0.5}` — 粒子演出〔p="wax", n=12, at="t", s=0.5〕
16. `{"op":"fx","p":"happy","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="happy", n=46, at="ring", r=5.5, y=0.25〕
17. `{"op":"fx","p":"enchant","n":36,"at":"line","r":24}` — 粒子演出〔p="enchant", n=36, at="line", r=24〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"guard","t":100}` — 防御〔t=100〕
20. `{"op":"buff","e":"luck","t":140,"a":3}` — 強化〔e="luck", t=140, a=3〕
21. `{"op":"allies","r":18.0}` — 味方対象〔r=18.0〕
22. `{"op":"healpct","v":0.25}` — 最大HP割合回復〔v=0.25〕
23. `{"op":"fx","p":"end_rod","n":16,"at":"ring","r":5.0}` — 粒子演出〔p="end_rod", n=16, at="ring", r=5.0〕
24. `{"op":"sound","s":"spell","v":0.75,"pi":1.15}` — 効果音〔s="spell", v=0.75, pi=1.15〕
25. `{"op":"area","r":9,"n":8}` — 円形対象の取得〔r=9, n=8〕
26. `{"op":"dmg","m":0.9}` — 追加攻撃〔m=0.9〕
27. `{"op":"eff","e":"slow","t":65,"a":0}` — 敵への状態異常〔e="slow", t=65, a=0〕
28. `{"op":"fx","p":"wax","n":24,"at":"ring","r":4.5,"y":0.6}` — 粒子演出〔p="wax", n=24, at="ring", r=4.5, y=0.6〕
29. `{"op":"sound","s":"chime","v":0.8,"pi":0.8}` — 効果音〔s="chime", v=0.8, pi=0.8〕
30. `{"op":"cone","r":12,"a":85}` — 扇形対象の取得〔r=12, a=85〕
31. `{"op":"eff","e":"slow","t":32,"a":124}` — 敵への状態異常〔e="slow", t=32, a=124〕

**戦闘動作の監修**：通常攻撃のコンボと武器固有の追加権能を区別する。2特殊技＋必殺技の独立123技はV15設計にあり、現行JARの完全実装とは区別。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 甘蜜の契約書 — 神威触媒（Curios relic_focus） (`sweet_pact_focus`)

**現行パラメータ**：rank=2、damage登録値=68.31、relics側CD=160tick、art側CD=160tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"saturation","t":40,"a":0}` — 強化〔e="saturation", t=40, a=0〕
03. `{"op":"self"}` — 対象を自分へ〔〕
04. `{"op":"buff","e":"luck","t":45,"a":0}` — 強化〔e="luck", t=45, a=0〕
05. `{"op":"self"}` — 対象を自分へ〔〕
06. `{"op":"buff","e":"luck","t":45,"a":2}` — 強化〔e="luck", t=45, a=2〕
07. `{"op":"buff","e":"regen","t":45,"a":1}` — 強化〔e="regen", t=45, a=1〕
08. `{"op":"self"}` — 対象を自分へ〔〕
09. `{"op":"buff","e":"luck","t":42,"a":2}` — 強化〔e="luck", t=42, a=2〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（44命令）**：

01. `{"op":"fx","p":"enchant","n":12,"at":"ring","r":3.4,"y":0.75}` — 粒子演出〔p="enchant", n=12, at="ring", r=3.4, y=0.75〕
02. `{"op":"fx","p":"enchant","n":6,"at":"self","s":0.7}` — 粒子演出〔p="enchant", n=6, at="self", s=0.7〕
03. `{"op":"fx","p":"wax","n":40,"at":"self"}` — 粒子演出〔p="wax", n=40, at="self"〕
04. `{"op":"fx","p":"happy","n":20,"at":"self"}` — 粒子演出〔p="happy", n=20, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":0.9}` — 効果音〔s="chime", v=1.0, pi=0.9〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.4}` — 最大HP割合回復〔v=0.4〕
08. `{"op":"food"}` — food〔〕
09. `{"op":"buff","e":"absorb","t":600,"a":6}` — 強化〔e="absorb", t=600, a=6〕
10. `{"op":"buff","e":"strength","t":600,"a":4}` — 強化〔e="strength", t=600, a=4〕
11. `{"op":"give","item":"emerald","n":8}` — give〔item="emerald", n=8〕
12. `{"op":"give","item":"diamond","n":2}` — give〔item="diamond", n=2〕
13. `{"op":"xp","v":120}` — xp〔v=120〕
14. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
15. `{"op":"self"}` — 対象を自分へ〔〕
16. `{"op":"buff","e":"luck","t":150,"a":1}` — 強化〔e="luck", t=150, a=1〕
17. `{"op":"fx","p":"enchant","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="enchant", n=50, at="ring", r=8.0, y=0.6〕
18. `{"op":"fx","p":"ash","n":32,"at":"line","r":30}` — 粒子演出〔p="ash", n=32, at="line", r=30〕
19. `{"op":"sound","s":"totem","v":1.15,"pi":0.95}` — 効果音〔s="totem", v=1.15, pi=0.95〕
20. `{"op":"area","r":24.0,"n":18}` — 円形対象の取得〔r=24.0, n=18〕
21. `{"op":"mark","t":135,"x":1.5}` — 刻印〔t=135, x=1.5〕
22. `{"op":"eff","e":"slow","t":100,"a":2}` — 敵への状態異常〔e="slow", t=100, a=2〕
23. `{"op":"dmg","m":2.2}` — 追加攻撃〔m=2.2〕
24. `{"op":"self"}` — 対象を自分へ〔〕
25. `{"op":"healpct","v":0.22}` — 最大HP割合回復〔v=0.22〕
26. `{"op":"buff","e":"luck","t":150,"a":3}` — 強化〔e="luck", t=150, a=3〕
27. `{"op":"fx","p":"wax","n":24,"at":"ring","r":10,"y":0.5}` — 粒子演出〔p="wax", n=24, at="ring", r=10, y=0.5〕
28. `{"op":"sound","s":"chime","v":0.85,"pi":0.9}` — 効果音〔s="chime", v=0.85, pi=0.9〕
29. `{"op":"allies","r":18.0}` — 味方対象〔r=18.0〕
30. `{"op":"healpct","v":0.14,"to":1}` — 最大HP割合回復〔v=0.14, to=1〕
31. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
32. `{"op":"self"}` — 対象を自分へ〔〕
33. `{"op":"buff","e":"luck","t":220,"a":3}` — 強化〔e="luck", t=220, a=3〕
34. `{"op":"allies","r":24.0}` — 味方対象〔r=24.0〕
35. `{"op":"healpct","v":0.14,"to":1}` — 最大HP割合回復〔v=0.14, to=1〕
36. `{"op":"fx","p":"wax","n":24,"at":"ring","r":5.5,"y":0.7}` — 粒子演出〔p="wax", n=24, at="ring", r=5.5, y=0.7〕
37. `{"op":"cone","r":14,"a":95}` — 扇形対象の取得〔r=14, a=95〕
38. `{"op":"eff","e":"slow","t":43,"a":123}` — 敵への状態異常〔e="slow", t=43, a=123〕
39. `{"op":"self"}` — 対象を自分へ〔〕
40. `{"op":"buff","e":"luck","t":100,"a":123}` — 強化〔e="luck", t=100, a=123〕
41. `{"op":"fx","p":"end_rod","n":16,"at":"ring","r":3.7,"y":0.55}` — 粒子演出〔p="end_rod", n=16, at="ring", r=3.7, y=0.55〕
42. `{"op":"area","r":14,"n":7}` — 円形対象の取得〔r=14, n=7〕
43. `{"op":"eff","e":"slow","t":90,"a":14}` — 敵への状態異常〔e="slow", t=90, a=14〕
44. `{"op":"mark","t":115,"x":1.8}` — 刻印〔t=115, x=1.8〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 依存救済の旅環 — 神格装飾品（Curios relic_charm） (`sweet_pact_charm`)

**現行パラメータ**：rank=1、damage登録値=68.31、relics側CD=190tick、art側CD=190tick。エンチャント付与命令：付与データなし。

**装備中の常時命令（13命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"luck","t":40,"a":1}` — 強化〔e="luck", t=40, a=1〕
03. `{"op":"buff","e":"regen","t":40,"a":0}` — 強化〔e="regen", t=40, a=0〕
04. `{"op":"self"}` — 対象を自分へ〔〕
05. `{"op":"buff","e":"luck","t":45,"a":0}` — 強化〔e="luck", t=45, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"buff","e":"resist","t":45,"a":2}` — 強化〔e="resist", t=45, a=2〕
08. `{"op":"buff","e":"regen","t":45,"a":2}` — 強化〔e="regen", t=45, a=2〕
09. `{"op":"buff","e":"luck","t":45,"a":1}` — 強化〔e="luck", t=45, a=1〕
10. `{"op":"self"}` — 対象を自分へ〔〕
11. `{"op":"buff","e":"luck","t":42,"a":2}` — 強化〔e="luck", t=42, a=2〕
12. `{"op":"self"}` — 対象を自分へ〔〕
13. `{"op":"buff","e":"regen","t":48,"a":4}` — 強化〔e="regen", t=48, a=4〕

**命中したときの命令（0命令）**：

登録なし。

**権能発動時の命令（36命令）**：

01. `{"op":"fx","p":"enchant","n":6,"at":"ring","r":2.4,"y":0.75}` — 粒子演出〔p="enchant", n=6, at="ring", r=2.4, y=0.75〕
02. `{"op":"fx","p":"enchant","n":4,"at":"self","s":0.7}` — 粒子演出〔p="enchant", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"wax","n":40,"at":"self"}` — 粒子演出〔p="wax", n=40, at="self"〕
04. `{"op":"fx","p":"happy","n":20,"at":"self"}` — 粒子演出〔p="happy", n=20, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":0.9}` — 効果音〔s="chime", v=1.0, pi=0.9〕
06. `{"op":"allies","r":24}` — 味方対象〔r=24〕
07. `{"op":"healpct","v":0.25,"to":1}` — 最大HP割合回復〔v=0.25, to=1〕
08. `{"op":"cleanse","to":1}` — 状態異常解除〔to=1〕
09. `{"op":"give","item":"bread","n":8}` — give〔item="bread", n=8〕
10. `{"op":"fx","p":"crit","n":12,"at":"t","s":0.5}` — 粒子演出〔p="crit", n=12, at="t", s=0.5〕
11. `{"op":"self"}` — 対象を自分へ〔〕
12. `{"op":"buff","e":"luck","t":210,"a":1}` — 強化〔e="luck", t=210, a=1〕
13. `{"op":"fx","p":"happy","n":46,"at":"ring","r":5.5,"y":0.25}` — 粒子演出〔p="happy", n=46, at="ring", r=5.5, y=0.25〕
14. `{"op":"fx","p":"enchant","n":36,"at":"line","r":24}` — 粒子演出〔p="enchant", n=36, at="line", r=24〕
15. `{"op":"sound","s":"totem","v":1.05,"pi":1.14}` — 効果音〔s="totem", v=1.05, pi=1.14〕
16. `{"op":"self"}` — 対象を自分へ〔〕
17. `{"op":"guard","t":95}` — 防御〔t=95〕
18. `{"op":"self"}` — 対象を自分へ〔〕
19. `{"op":"healpct","v":0.3}` — 最大HP割合回復〔v=0.3〕
20. `{"op":"cleanse"}` — 状態異常解除〔〕
21. `{"op":"buff","e":"luck","t":180,"a":3}` — 強化〔e="luck", t=180, a=3〕
22. `{"op":"guard","t":95}` — 防御〔t=95〕
23. `{"op":"fx","p":"wax","n":30,"at":"ring","r":4.0,"y":0.7}` — 粒子演出〔p="wax", n=30, at="ring", r=4.0, y=0.7〕
24. `{"op":"sound","s":"chime","v":0.8,"pi":1.1}` — 効果音〔s="chime", v=0.8, pi=1.1〕
25. `{"op":"self"}` — 対象を自分へ〔〕
26. `{"op":"buff","e":"luck","t":280,"a":4}` — 強化〔e="luck", t=280, a=4〕
27. `{"op":"guard","t":125}` — 防御〔t=125〕
28. `{"op":"self"}` — 対象を自分へ〔〕
29. `{"op":"guard","t":130}` — 防御〔t=130〕
30. `{"op":"fx","p":"wax","n":20,"at":"ring","r":4,"y":0.4}` — 粒子演出〔p="wax", n=20, at="ring", r=4, y=0.4〕
31. `{"op":"self"}` — 対象を自分へ〔〕
32. `{"op":"buff","e":"luck","t":160,"a":123}` — 強化〔e="luck", t=160, a=123〕
33. `{"op":"cone","r":10,"a":100}` — 扇形対象の取得〔r=10, a=100〕
34. `{"op":"eff","e":"slow","t":32,"a":123}` — 敵への状態異常〔e="slow", t=32, a=123〕
35. `{"op":"self"}` — 対象を自分へ〔〕
36. `{"op":"guard","t":85}` — 防御〔t=85〕

**装備動作の監修**：装着したアクセサリーは装備欄に固定。触媒なら発動点は装着位置から投影、装飾品なら被弾・回復・状態変化などの条件で反応させる。召喚する砲塔や足場は別の設置物であり、アクセサリー本体は設置しない。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。

### 未来総有・未怪の債権冠 — 超越神器（武器欄） (`sweet_pact_legend`)

**現行パラメータ**：rank=3、damage登録値=1157.875、relics側CD=345tick、art側CD=345tick。エンチャント付与命令：minecraft:unbreaking:125、minecraft:mending:1、minecraft:sharpness:125、minecraft:looting:10。

**装備中の常時命令（9命令）**：

01. `{"op":"self"}` — 対象を自分へ〔〕
02. `{"op":"buff","e":"resist","t":40,"a":3}` — 強化〔e="resist", t=40, a=3〕
03. `{"op":"buff","e":"strength","t":40,"a":6}` — 強化〔e="strength", t=40, a=6〕
04. `{"op":"buff","e":"regen","t":40,"a":1}` — 強化〔e="regen", t=40, a=1〕
05. `{"op":"buff","e":"saturation","t":40,"a":0}` — 強化〔e="saturation", t=40, a=0〕
06. `{"op":"self"}` — 対象を自分へ〔〕
07. `{"op":"healpct","v":0.012}` — 最大HP割合回復〔v=0.012〕
08. `{"op":"buff","e":"luck","t":45,"a":3}` — 強化〔e="luck", t=45, a=3〕
09. `{"op":"buff","e":"haste","t":45,"a":3}` — 強化〔e="haste", t=45, a=3〕

**命中したときの命令（7命令）**：

01. `{"op":"chance","p":0.35,"ops":[{"op":"give","item":"emerald","n":2}]}` — 抽選〔p=0.35, ops=[{"op":"give","item":"emerald","n":2}]〕
02. `{"op":"chance","p":0.4,"ops":[{"op":"victim"},{"op":"eff","e":"weakness","t":160,"a":1}]}` — 抽選〔p=0.4, ops=[{"op":"victim"},{"op":"eff","e":"weakness","t":160,"a":1}]〕
03. `{"op":"chance","p":0.48,"ops":[{"op":"victim"},{"op":"fx","p":"happy","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]}` — 抽選〔p=0.48, ops=[{"op":"victim"},{"op":"fx","p":"happy","n":12,"at":"t","s":0.3},{"op":"mark","t":120,"x":1.5}]〕
04. `{"op":"chance","p":0.75,"ops":[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"enchant","n":10,"at":"t","s":0.35}]}` — 抽選〔p=0.75, ops=[{"op":"victim"},{"op":"mark","t":175,"x":2.6},{"op":"eff","e":"slow","t":135,"a":2},{"op":"fx","p":"enchant","n":10,"at":"t","s":0.35}]〕
05. `{"op":"chance","p":0.26,"ops":[{"op":"victim"},{"op":"dmg","m":0.075}]}` — 抽選〔p=0.26, ops=[{"op":"victim"},{"op":"dmg","m":0.075}]〕
06. `{"op":"chance","p":0.3,"ops":[{"op":"victim"},{"op":"fx","p":"wax","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]}` — 抽選〔p=0.3, ops=[{"op":"victim"},{"op":"fx","p":"wax","n":20,"at":"t","s":0.33},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":160,"x":2.5}]〕
07. `{"op":"chance","p":0.22,"ops":[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"wither","t":78,"a":7}]}` — 抽選〔p=0.22, ops=[{"op":"victim"},{"op":"fx","p":"end_rod","n":7,"at":"t","s":0.28},{"op":"victim"},{"op":"eff","e":"wither","t":78,"a":7}]〕

**権能発動時の命令（28命令）**：

01. `{"op":"fx","p":"enchant","n":9,"at":"ring","r":4.5,"y":0.75}` — 粒子演出〔p="enchant", n=9, at="ring", r=4.5, y=0.75〕
02. `{"op":"fx","p":"enchant","n":4,"at":"self","s":0.7}` — 粒子演出〔p="enchant", n=4, at="self", s=0.7〕
03. `{"op":"fx","p":"wax","n":40,"at":"self"}` — 粒子演出〔p="wax", n=40, at="self"〕
04. `{"op":"fx","p":"happy","n":20,"at":"self"}` — 粒子演出〔p="happy", n=20, at="self"〕
05. `{"op":"sound","s":"chime","v":1.0,"pi":0.9}` — 効果音〔s="chime", v=1.0, pi=0.9〕
06. `{"op":"area","r":48,"n":36}` — 円形対象の取得〔r=48, n=36〕
07. `{"op":"strip","steal":1}` — 強化解除〔steal=1〕
08. `{"op":"stun","t":105}` — 行動停止〔t=105〕
09. `{"op":"dmg","m":2.8}` — 追加攻撃〔m=2.8〕
10. `{"op":"dmg","m":5.6,"magic":1}` — 追加攻撃〔m=5.6, magic=1〕
11. `{"op":"give","item":"diamond","n":8}` — give〔item="diamond", n=8〕
12. `{"op":"give","item":"emerald","n":8}` — give〔item="emerald", n=8〕
13. `{"op":"give","item":"netherite","n":1}` — give〔item="netherite", n=1〕
14. `{"op":"self"}` — 対象を自分へ〔〕
15. `{"op":"healpct","v":0.6}` — 最大HP割合回復〔v=0.6〕
16. `{"op":"undying","t":180}` — 死亡防護〔t=180〕
17. `{"op":"buff","e":"absorb","t":1200,"a":9}` — 強化〔e="absorb", t=1200, a=9〕
18. `{"op":"fx","p":"wax","n":12,"at":"t","s":0.5}` — 粒子演出〔p="wax", n=12, at="t", s=0.5〕
19. `{"op":"area","r":30,"n":24}` — 円形対象の取得〔r=30, n=24〕
20. `{"op":"strip"}` — 強化解除〔〕
21. `{"op":"eff","e":"wither","t":160,"a":1}` — 敵への状態異常〔e="wither", t=160, a=1〕
22. `{"op":"dmg","m":1.2}` — 追加攻撃〔m=1.2〕
23. `{"op":"fx","p":"enchant","n":50,"at":"ring","r":8.0,"y":0.6}` — 粒子演出〔p="enchant", n=50, at="ring", r=8.0, y=0.6〕
24. `{"op":"fx","p":"ash","n":32,"at":"line","r":30}` — 粒子演出〔p="ash", n=32, at="line", r=30〕
25. `{"op":"sound","s":"totem","v":1.15,"pi":0.95}` — 効果音〔s="totem", v=1.15, pi=0.95〕
26. `{"op":"cycle","steps":[{"say":"relic_art.oror_supreme_bosses.sweet_pact_legend.stage0","ops":[{"op":"fx","p":"wax","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"chime","v":0.9,"pi":1.2},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"enchant","n":6,"at":"line","r":10},{"op":"fx","p":"happy","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"enchant","n":36,"at":"line","r":24},{"op":"sound","s":"totem","v":1.05,"pi":1.14},{"op":"self"},{"op":"guard","t":100},{"op":"buff","e":"luck","t":140,"a":3},{"op":"allies","r":18.0},{"op":"healpct","v":0.25},{"op":"self"},{"op":"buff","e":"luck","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.sweet_pact_legend.stage1","ops":[{"op":"fx","p":"wax","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"chime","v":1.05,"pi":1.0},{"op":"fx","p":"enchant","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":15},{"op":"fx","p":"enchant","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"ash","n":32,"at":"line","r":30},{"op":"sound","s":"totem","v":1.15,"pi":0.95},{"op":"area","r":24.0,"n":18},{"op":"mark","t":135,"x":1.95},{"op":"eff","e":"slow","t":100,"a":2},{"op":"dmg","m":3.19},{"op":"area","r":12.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.sweet_pact_legend.stage2","ops":[{"op":"fx","p":"wax","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"chime","v":1.25,"pi":0.75},{"op":"fx","p":"enchant","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"end_rod","n":10,"at":"line","r":20},{"op":"fx","p":"happy","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"enchant","n":48,"at":"line","r":48},{"op":"fx","p":"ash","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"totem","v":1.5,"pi":0.75},{"op":"area","r":31.0,"n":25},{"op":"dmg","m":9.072},{"op":"strip"},{"op":"stun","t":55},{"op":"self"},{"op":"buff","e":"luck","t":200,"a":4},{"op":"fx","p":"ash","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"enchant","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":30.0,"n":28},{"op":"dmg","m":2.9},{"op":"mark","t":185,"x":2.2},{"op":"self"},{"op":"buff","e":"luck","t":200,"a":4},{"op":"allies","r":37.0},{"op":"healpct","v":0.28,"to":1},{"op":"cleanse","to":1},{"op":"self"},{"op":"guard","t":180},{"op":"self"},{"op":"buff","e":"luck","t":240,"a":2},{"op":"fx","p":"wax","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"chime","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"slow","t":90,"a":14},{"op":"mark","t":135,"x":1.8}]}]}` — 段階権能切替〔steps=[{"say":"relic_art.oror_supreme_bosses.sweet_pact_legend.stage0","ops":[{"op":"fx","p":"wax","n":26,"at":"ring","r":5.0,"y":0.9},{"op":"sound","s":"chime","v":0.9,"pi":1.2},{"op":"fx","p":"end_rod","n":10,"at":"ring","r":4.5,"y":0.7},{"op":"fx","p":"enchant","n":6,"at":"line","r":10},{"op":"fx","p":"happy","n":46,"at":"ring","r":5.5,"y":0.25},{"op":"fx","p":"enchant","n":36,"at":"line","r":24},{"op":"sound","s":"totem","v":1.05,"pi":1.14},{"op":"self"},{"op":"guard","t":100},{"op":"buff","e":"luck","t":140,"a":3},{"op":"allies","r":18.0},{"op":"healpct","v":0.25},{"op":"self"},{"op":"buff","e":"luck","t":120,"a":3}]},{"say":"relic_art.oror_supreme_bosses.sweet_pact_legend.stage1","ops":[{"op":"fx","p":"wax","n":34,"at":"ring","r":8.0,"y":0.9},{"op":"sound","s":"chime","v":1.05,"pi":1.0},{"op":"fx","p":"enchant","n":10,"at":"ring","r":6.0,"y":0.7},{"op":"fx","p":"end_rod","n":6,"at":"line","r":15},{"op":"fx","p":"enchant","n":50,"at":"ring","r":8.0,"y":0.6},{"op":"fx","p":"ash","n":32,"at":"line","r":30},{"op":"sound","s":"totem","v":1.15,"pi":0.95},{"op":"area","r":24.0,"n":18},{"op":"mark","t":135,"x":1.95},{"op":"eff","e":"slow","t":100,"a":2},{"op":"dmg","m":3.19},{"op":"area","r":12.0,"n":10},{"op":"eff","e":"slow","t":120,"a":2},{"op":"self"},{"op":"guard","t":90}]},{"say":"relic_art.oror_supreme_bosses.sweet_pact_legend.stage2","ops":[{"op":"fx","p":"wax","n":58,"at":"ring","r":11.0,"y":0.9},{"op":"sound","s":"chime","v":1.25,"pi":0.75},{"op":"fx","p":"enchant","n":16,"at":"ring","r":7.5,"y":0.7},{"op":"fx","p":"end_rod","n":10,"at":"line","r":20},{"op":"fx","p":"happy","n":64,"at":"ring","r":11,"y":0.2},{"op":"fx","p":"enchant","n":48,"at":"line","r":48},{"op":"fx","p":"ash","n":36,"at":"ring","r":6,"y":1.0},{"op":"sound","s":"totem","v":1.5,"pi":0.75},{"op":"area","r":31.0,"n":25},{"op":"dmg","m":9.072},{"op":"strip"},{"op":"stun","t":55},{"op":"self"},{"op":"buff","e":"luck","t":200,"a":4},{"op":"fx","p":"ash","n":8,"at":"pillar","s":0.22},{"op":"fx","p":"enchant","n":54,"at":"ring","r":13.0,"y":1.0},{"op":"area","r":30.0,"n":28},{"op":"dmg","m":2.9},{"op":"mark","t":185,"x":2.2},{"op":"self"},{"op":"buff","e":"luck","t":200,"a":4},{"op":"allies","r":37.0},{"op":"healpct","v":0.28,"to":1},{"op":"cleanse","to":1},{"op":"self"},{"op":"guard","t":180},{"op":"self"},{"op":"buff","e":"luck","t":240,"a":2},{"op":"fx","p":"wax","n":44,"at":"ring","r":11.0,"y":0.55},{"op":"sound","s":"chime","v":1.2,"pi":0.7},{"op":"area","r":14,"n":14},{"op":"eff","e":"slow","t":43,"a":124},{"op":"mark","t":190,"x":3.1},{"op":"dmg","m":1.25},{"op":"area","r":16,"n":10},{"op":"eff","e":"slow","t":90,"a":14},{"op":"mark","t":135,"x":1.8}]}]〕
27. `{"op":"area","r":16,"n":16}` — 円形対象の取得〔r=16, n=16〕
28. `{"op":"dmg","m":1.1}` — 追加攻撃〔m=1.1〕

**神器段階の登録**：1個のcycle命令。段階の内側データは上記cast命令と元JSONを照合する。通常討伐武器の特殊技3件とは別システム。

**状態**：ここまでの数値・命令はJARの登録値。装着操作・描画・コンボの実プレイは未検証。
