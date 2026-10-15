# 造形リファレンス調査（凝ったMOD）

実際のモデルファイル（Bedrock geo / Tabula / Java）を読み込み、ゲームと同じ箱UV・ライティングで描画して比較した。
描画ツールは `tools/study/`（geoview / tblview / acview / ldview / refmix）。

## 調べたMODとモデル
- Cobblemon（MPL-2.0, GitLab）: torterra, garchomp, gyarados, wailord, lapras, rayquaza, charizard, dragonite, xerneas, arcanine, metagross, lugia, gardevoir, mewtwo, primarina, tinkaton, milotic
- Alex's Caves（GitHub）: Hullbreaker, Tremorzilla, Subterranodon, Gloomoth, Vallumraptor, Candicorn, Deep One, Forsaken, Licowitch, Underzealot
- Ice and Fire（GitHub, Tabula）: 火竜（104パーツ）, 海竜
- Bosses of Mass Destruction（GitHub, GeckoLib）: Lich（233パーツ）, Gauntlet, Obsidilith, Void Blossom
- Iron's Spells 'n Spellbooks（GitHub, GeckoLib）: Dead King, Tyros, Archevoker, 3D防具（pyromancer / cryomancer / priest / cultist / shadowwalker / plagued / wizard / electromancer / paladin）
- Ars Nouveau（GitHub, GeckoLib）: Wilden Chimera, Wilden Hunter, Starbuncle, Amethyst Golem
- Twilight Forest / Goety / Deeper and Darker（GitHub, Java）: Lich, Snow Queen, Necromancer, Redstone Golem, Stalker
- Touhou Little Maid: 霊夢・天子（355パーツ）・勇儀
- Dungeons and Combat: MCreator製・GeckoLib・Curios依存、4勢力（Eldrichの信徒 / 血の教団 / 太陽の子 / 炎の存在）とミニボス（Gravewatcher, Pyroknight, Lady Blaze, Kamath）、20種以上の3D防具。ソース非公開で、この環境からはCurseForge/Modrinthに接続できずJARを取得できなかった。

## 数値（中央値）
| | パーツ数 | 平面の割合 | 回転した骨の割合 | inflate層 |
|---|---:|---:|---:|---:|
| 参考MOD | 83 | 37% | 35% | 約30%（Cobblemon） |
| 現行の自作モデル | 46 | 24% | — | 10% |

## 共通する作り方
1. 姿勢で形を作る: 胴を傾け、首を上げ、尾を下げてから反らす。脚は太腿・脛・足で曲げる。箱を水平に並べない。
2. 平面の切り抜きで輪郭を作る: 背びれ・棘・羽根・鰭・髪束・裾・炎を、透過で形を描いた板で作る（Hullbreakerは巨大な鰭板で大半の輪郭を作る）。
3. 節を多く: 尾・首は6〜12節、各節に棘やひれを付ける（火竜・海竜・レックウザ）。
4. 重ね着: inflateした箱で外套・装甲・毛皮・甲羅の縁を重ねる（Cobblemonは約3割がinflate）。
5. 小物の密度: 冠・宝飾・爪・牙・ベルト・鋲・ページ・鎖など1〜2単位の小パーツを要所に集中（BoMDのLichは66個）。
6. 誇張した特徴: 武器・帽子・翼・角・髪など、キャラを示す部位を体より大きくしてよい（Tinkatonのハンマー、Xerneasの角、天子の帽子）。
7. テクスチャ: 128〜512pxで、平面の色分けだけでなく柔らかい陰影・ハイライト・縁取りを描く。目は大きなハイライト付き。
8. 3D防具（Iron's / Dungeons and Combat系）: 体は通常の比率のまま、フード・襟・肩当て・前垂れ・マントを別パーツで重ね、金縁や紋章で格を出す。
