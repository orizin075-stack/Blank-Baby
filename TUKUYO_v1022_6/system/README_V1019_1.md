# TUKUYO v1019.1 — Evolution Integrity / Crash Recovery Closure

本修正版の基盤は HARDENED_COMPACT（元ZIP SHA-256: 9bb314226143ab9969ebffeb54898f3214eab639dab9a1dd7ad32b7d04f8b3b2）。REINTEGRATION版とは異なる系統です。

互換性のため version と既存状態schemaは v1019 を維持し、CLIの release_revision と新しい配布名で v1019.1 を識別します。進化package/capsule/selectionは /2 schemaです。選択証明が不足する旧 /1 進化packageの取り込みは拒否します。既存個体を上書きせず、新しいデータディレクトリで検証してください。既存個体の自動移行・全履歴の書換えはこの修正版では提供しません。

## 実装変更

- 受信側で変異幅、fitness、gain、budgetを計算。seed digestから候補集合を再生成し、選抜候補とcommitmentを検査。
- 選択のbaselineを直前世代の署名付きheritable profileまたは創始値へ束縛。Soulの経験は遺伝profileに混ぜない。
- 証明のfamily、親子ID、世代、隣接鍵、減衰値、死亡宣言を照合。未知フィールド・非有限値・bool数値を拒否。
- 継承/進化の更新は一時コピーで実行。ライブ更新前にredo記録を永続化し、次回起動で同一バイト列を完了する。prepare前の停止は変更前へ戻る。prepare後の停止はコミット完了へ進む。
- 進化状態を署名付きcommit履歴から再構築。拒否した操作でイベントや使用済みマーカーを残さない。
- 継承鍵を両方失った既存個体は新鍵で継続しない。
- 死亡後のCLI経験・学習・会話・新規選択を拒否。主要なSoul/Heart/会話APIにも同じ制約を適用。監査と死亡後の署名付き出力は維持。
- 箱/袋/ケース/束と中身の消費を区別。箱を開けるだけでは中身を減らさない。消費超過は棄権。
- 相手別選択の引数、独立検証器の版/schema判定、v1017テストの現行API追従を修正。

## 起動

個体データは配布ディレクトリ外へ置きます。Python 3.10+ と requirements.txt の依存関係を用意してください。

```sh
python -B run_tukuyo.py --runtime-trust-file /path/to/TUKUYO_v1019_1_TRUST_ANCHOR.txt --data /path/to/new-individual init --individual-id TUKUYO-v1019-1-001
python -B run_tukuyo.py --runtime-trust-file /path/to/TUKUYO_v1019_1_TRUST_ANCHOR.txt --data /path/to/new-individual evolution-select research
python -B run_tukuyo.py --runtime-trust-file /path/to/TUKUYO_v1019_1_TRUST_ANCHOR.txt --data /path/to/new-individual whole-audit
```

同梱STARTスクリプトは従来のデータ既定値を保持します。既存データを誤って使わないよう、TUKUYO_DATA_DIR を新規ディレクトリへ設定してください。新しいtrust anchorはこの修正版の署名鍵です。旧publisher鍵によるcross-signatureはありません。

## 成立範囲と限界

5trait、budget=3.15、4環境の固定fitnessを使う限定モデルです。自然選択・open-ended evolution・population ecology・主観的意識・literal soul・一般L5・24時間稼働は成立を主張しません。

トランザクションはデータの一時コピーを使用するため、個体のデータ量に応じてディスクと時間が必要です。系譜writerのロックは実装しましたが、全ての旧機能を含む複数同時writerの一貫性は未検証です。試験はLinux上のSIGKILLで実施し、実停電・Windows/macOSでの動作は未検証です。

公開鍵pinは署名者を束縛しますが、署名者が主張する世界外の本当の個体ID・本当の死亡やfitnessの現実的有用性を外部観測なしで証明するものではありません。許可された文字列フィールドを利用した秘密情報の隠蔽、データ全体の悪意ある巻戻し、ハードウェア故障は今回の防御成立範囲に含めません。

全検証結果は配布と同時に提供する実測報告を参照してください。META内の旧版報告は履歴資料であり、この修正版の新規実測ではありません。
