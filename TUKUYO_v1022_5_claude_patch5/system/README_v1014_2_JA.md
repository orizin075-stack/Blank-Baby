# TUKUYO v1014.2 — Atomic Crash Recovery

v1014.1の署名鍵継続性・独立意味検証・検索索引修復を維持しながら、process death中の部分書込とmulti-file commitを復旧可能にする修復版。

- atomic file replace: target fileを直接途中書込せず、同一directoryの一時fileをfsync後にreplaceする。
- verified reasoning mutation marker: 回答結果とWhole State同期の間で停止した場合、次processがWhole Stateを再同期する。
- checkpoint WAL: checkpoint本体とLATEST pointerの間で停止しても、次processが有効checkpointを検証してpointerを修復する。
- restore transaction: staged audit合格後のrestoreをpersistent stage + transaction markerでcommitし、途中停止後は次processがidempotentに完遂する。
- realtime pending event: realtime event / head / run stateのmulti-file更新をpending recordで束縛し、途中停止を次processで完遂または安全に破棄する。
- orphan temp cleanup: SIGKILLで残ったatomic temporary fileはstartup recoveryが除去する。

## claim boundary

今回のfault injectionは指定commit点での強制killを対象とする。任意のCPU命令位置、filesystem/controller故障、電源断でのhardware durability、24h/72hの実時間完走を証明するものではない。
