# TUKUYO v1021 起動

新しい実個体接続は、新規データディレクトリで README_V1021.md のコマンドから起動してください。外部公開鍵は TUKUYO_v1021_TRUST_ANCHOR.txt、再構築した開発順と進級条件は ROUTE_V1021.md を参照してください。以下のランチャーは従来の対話起動用です。

Python 3.10+ を用意し、`pip install -r requirements.txt` を実行してください。

## 推奨起動

- Linux/macOS: `./START_TUKUYO.sh`
- Windows: `START_TUKUYO.bat`

個体データは署名済み配布フォルダの外、既定では `~/.tukuyo/v999_data`（Windowsでは `%USERPROFILE%\.tukuyo\v999_data`）へ保存されます。
`TUKUYO_DATA_DIR` で変更できます。

外部runtime trust anchorを使ってpublisher pinまで検証する場合は、`run_tukuyo.py --runtime-trust-file <anchor> ...` を使用してください。
