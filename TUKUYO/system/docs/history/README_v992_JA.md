# TUKUYO v992 — Fresh Holdout Transfer Assay

v992は、TRAIN_A / TRAIN_Bで得た環境介入結果から「観測context × action」の経験的成績を学び、配置・サイズ・hazard/resource条件を変えたHOLDOUT_A / HOLDOUT_Bへ持ち込むfresh holdout評価です。

訓練では各観測状態を複製した介入試験で実際に一手を実行し、行動別の固定報酬ではなくv991のgrounded utilityを観測します。holdoutでは学習済みpolicyと固定MOVE_FORWARD baselineを同条件で比較します。

この評価が示すのは、同一閉世界family内の抽象観測contextを介した限定的転移です。観測カテゴリと行動集合は事前定義されており、cross-domain generalizationや現実世界一般化を主張しません。
