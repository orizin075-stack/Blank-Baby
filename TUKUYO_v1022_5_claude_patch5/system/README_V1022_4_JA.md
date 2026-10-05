# TUKUYO V1022.4 Recovery Completeness Experimental

V1022.3を基に、実個体群の復元と有限推論の確定条件を修正した実験版。LLM接続や新たな教師会話は追加していない。既存の公開技能・代謝・独立したSoul/Heart/鍵・署名付き継承を保持する。

## 変更

- 壊れた子個体の現在状態で復元を止めず、署名済みcheckpointを独立したstageで監査してから復元する。
- 復元用の準備記録とファイルhashをrecovery鍵で署名する。全rootの置換画像を構成し、root外の認証済みsidecarを保持してディレクトリを切り替える。二つのrenameの間に停止してdata pathが一時的に消えても、次回起動が復元を完了する。SIGKILL後もstageの全byteを照合し、改変・欠落時には準備記録を残して停止する。欠落を「rollback成功」と扱わない。
- 現役rootが署名済みの全置換画像と完全一致している場合は、復元済みとして署名付き完了記録を残す。その後に古い準備記録が再出現しても、同じ操作の完了署名を検証して再適用を止め、正当な後続操作を維持する。完了署名の改変は拒否する。
- checkpointより未来のprivate WALと`.lineage_transaction/PREPARED.json`を破棄する。通常起動は復元を完了してから他のredo・cache修復を行う。
- checkpoint後に生まれた実個体の残存秘密鍵は、`v1014/private/retired_runtimes`へ退避する。現役runtimeのpathから除き、同じ番号で次の子を作る時に古い鍵を再使用させない。checkpoint内の個体の鍵は変更しない。
- ownerのcopy-on-write処理中も、子の学習headを子自身の署名済みWholeへ照合する。commit後も実個体群を再監査し、確認が済むまでPREPAREDを保持する。
- meta reasonerと独立checkerは、候補数・深さ・探索量の上限に達した場合に棄権する。最初の8件や32件だけを見た「全戦略一致」を返さない。
- v1021実個体への直接操作もownerと同じ階層lockを取得する。

## fresh実行

コードの`system`外にdataを置く。配布物の新しい外部anchorを明示する。

```bash
python3 -B system/tools/verify_release.py system --trusted-pubkey-file TUKUYO_v1022_4_TRUST_ANCHOR.txt
python3 -B system/run_tukuyo.py --runtime-trust-file TUKUYO_v1022_4_TRUST_ANCHOR.txt --data ./individual init
python3 -B system/run_tukuyo.py --runtime-trust-file TUKUYO_v1022_4_TRUST_ANCHOR.txt --data ./individual metabolism-init --families 4 --reservoir 160000 --regeneration 1800 --max-age 4
python3 -B system/run_tukuyo.py --runtime-trust-file TUKUYO_v1022_4_TRUST_ANCHOR.txt --data ./individual metabolism-step --ticks 12
```

## 別process反復復元ゲート

全操作が別CLI process。4家系・第3世代・16個体の同一checkpointを反復復元する。途中に次世代の誕生、未来realtimeイベント、復元のSIGKILL、未来lineageのPREPARED、死亡中のSIGKILLを入れる。毎回、checkpointの全公開ファイル・全対象byte・既存秘密鍵のhash・資源会計・Whole・realtimeを確認し、最後に新processで運転を再開する。

```bash
python3 -B system/tools/recovery_stress.py --data ./recovery_gate --runtime-trust-file TUKUYO_v1022_4_TRUST_ANCHOR.txt --report ./recovery_report.json --cycles 100
```

外部reportが完成したcycleを記録する。同じ設定・同じ署名済みコードなら、同じreportとdataで再実行して続けられる。失敗はreportに保存し、未完走を成功に数えない。退避した未来個体の秘密鍵は公開証拠へ含めない。

## 既存個体のruntime anchor更新

新しい配布署名鍵は旧鍵と相互署名されていない。`META/PATCH_LINEAGE_v1022_4.json`に親archive・manifestのhashと両公開鍵を記録しているが、publisher継続性の暗号的証明ではない。新anchorへの信頼は利用者が別途決める必要がある。

既存data内の子process起動用anchorを更新する場合だけ、旧anchorと新anchorを明示して次を実行する。個体の秘密鍵、学習、energy、継承stateは再初期化しない。既存checkpointのruntime pinは当時のものなので、そのcheckpointを復元した後には再度この手順が必要になる。

```bash
python3 -B system/run_tukuyo.py --runtime-trust-file TUKUYO_v1022_4_TRUST_ANCHOR.txt --data ./existing_individual runtime-trust-rebind --previous-trust-file ./previous_runtime_anchor.txt
```

旧版で未完了の復元markerがある場合、先に旧版で完了させる。署名済み準備記録を持たない旧markerをこの版が自動承認することはない。準備stageを失った場合も、秘密鍵backupとcheckpoint/blobを保全して停止原因を調査する。

## 合格の境界

実測結果は外部検証報告を参照。このゲートは有限条件の工学試験であり、24h実時間、電源断、別OS、一般自然言語知能、自然選択、自己コード改変、意識や文字通りの生命の証明ではない。復元は明示的な履歴巻き戻しであり、通常運転中の不可逆死亡とは別の管理操作である。
