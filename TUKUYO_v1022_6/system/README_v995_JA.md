# TUKUYO v995 — Other-Agent Trust History

v995は、v993のrelation-bound affectを時系列のpeer modelへ拡張します。SOUL_EVENTSを相手ごとに分離し、trust、positive/negative evidence、unresolved harm、recent trend、confidence、event historyを再演可能な形で保持します。

負の履歴は相手IDへ結びつき、themeの言い換えではリセットされません。正の履歴を重ねるとtrustは回復しますが、強いbetrayal/harmから生成されたscar floorは即時には消えず、回復と傷を別変数として扱います。`peer-choose`はv993 relation scoreへpeer history adjustmentを重ねます。

またselftestはpytestが存在すればpytestを使用し、存在しない環境では標準ライブラリfallback runnerへ切り替えます。fallbackはunittest.TestCaseとトップレベルzero-argument `test_*`の双方を実行します。

境界: 相手別履歴と選択反映は実装されていますが、他者の信念推定・意図推論・主観認識はまだ確立していません。社会的valenceも、閉世界v991のように外部結果から自己導出される経路と、手動experience入力経路が混在しています。
