# TUKUYO 第4世代（開発中）— 引き継ぎメモ

このメモは、第4世代の作業を別のセッションで続けるためのものです。第4世代は、3 つの LLM（Claude・ChatGPT・Gemini）を親にして育つ子です。親の API キーを使う測定は、キーを入れたあとの**新しいセッション**でしかできません。

## 0. v1022.7.7 との統合（2026-10-12、`v1022.7.7+gen4-r6`）

`system/` は、渡された v1022.7.7（経験による魂の系統。v1022.6.5 でこちらの 2026-10-08 の版を取り込み、6.6〜7.7 まで進んだもの）と、第4世代の第6回（成長の実験まで）を一つにしたものです。何をどちらから取り、どこで何を決めたかは `FUSION_V1022_7_7_2026-10-12.md` にあります。続ける人が知っておくこと：

- 学んだ読み方は、生きた個体では相手の署名つきコミットの鎖（`src/tukuyo_g4/runtime_store.py`、`g4/commits`・`g4/STATE.json`、部品名 `g4_learning`）に入ります。`g4/learned.json` はその写しです。手で書き換えると、どのコマンドも止まります（`G4_LEARNING_CACHE_MISMATCH`）。前の版で子が署名した `learned.json` は読み、次のコミットに引き継ぎます（`runtime_store._own_signed`）。署名のないものは受け取りません。
- ほかの第4世代の記録（`own.py`）：署名に、書いたときに全体の状態が記録していた版（`base`）を入れます。古い版に戻されたものは `<KIND>_ROLLED_BACK` で断ります。署名のないものは、全体の状態がそのファイルを記録しているときだけ受け取ります。
- 入力の関所（`src/tukuyo_g4/api.py` の `_input_coverage`）：親だけの読みには相手の関所（`tukuyo_v1022.input_audit`）をすべてかけます。自分の読みには、文の形で一律に断る 3 つ（`NOT_FOR_OWN_READINGS`）を脇に置いてかけます。測り直しは `python3 -B tools/fusion_gates.py DATA --work WORK`（費用 0）。
- `think` は、parser B（`tukuyo_v1022.semantic_gate.parser_b`）が決めた答えと違うと控えます（相手の関所）。parser B の「K 個ずつ…何袋」の誤りは直しました（`_b_groups_en`）。parser B の誤りは `think` の正しい答えを止めるので、`fusion_gates.py` の `think` で見張ってください。
- 読み取り器：問いに大きさ・新旧の言葉（big・small・new・old など、`KIND_MODS`）が付いた物は、話の中にその言い方がなければ読みません（`ASKED_KIND_NOT_TOLD`）。
- 相手の試験の一部（ChatGPT のログイン）には `PyJWT[crypto]` が要ります（`system/requirements-chatgpt.txt`）。
- 相手の経験による魂の実験は `python3 -B tools/v1022_7_7_soul_experiment.py --data FRESH --trust ANCHOR --out out.json` と、`python3 -B tools/v1022_7_7_experience_verifier.py --data FRESH` で、いつでもやり直せます（記録した結果だけ、費用 0）。
- 統合した版の最後の確かめ（署名した写し、費用 0）：全体テスト 1031/1031、魂らしさ 12/12、汚染 6/6、成長の実験 3/3、親を使わない計測は例外 0・型の食い違い 0、ASDiv 開発用は `g4-solve` 501・`think` 502（誤りはどちらも 3）。結果は `evidence_gen4/*fusion_2026-10-12.json`。

**道筋の残りを進めた版（2026-10-13、`v1022.7.9+gen4-r9`）。** 外部の検証が示した 7.9〜9.0 を同時に進めました（`ROADMAP_2026-10-13.md`）。続ける人が知っておくこと：

- 経験の出どころ（`src/tukuyo_v1022/provenance.py`）：魂の出来事の `origin`（と実観測だけ `evidence`）は、書き込む道筋が決めます。新しく経験を書く道を足すときは、`process_experience(..., origin=...)` を必ず渡すこと（渡さなければ「出どころの記録なし」）。observed は `observe_experience` だけ、checked は第4世代の生活だけ。監査は `whole_state._audit_once` から呼ばれ、実観測の証拠を観測の記録から作り直して比べます。合格の実験は `tools/experience_authenticity_experiment.py`。
- 目標（`src/tukuyo_v1022/goals.py`）：記録から決まりで作る。決まりを変えたら、台帳の監査（記録から作り直して比べる）が前の台帳を通さなくなるので、決まりの版を分けること。合格の実験は `tools/goal_formation_experiment.py`。
- 日本語の読み手（`src/tukuyo_g4/reader_ja.py`）と英語の補助の形（`src/tukuyo_g4/forms_story_en.py`）：直すときは `tools/private_eval.py --set dev` と自分の確認用の問題で誤りを見ること。**本番用（`HELD_OUT_SHA256`）は今回 1 回使ったので、次に改善を測るときは新しい本番用を書くこと**。英語の補助の形は開発用の言い回しに合わせすぎで、本番用では効きませんでした。読み手には、どの形よりも先に効く歯止めがあります：日本語は `NOT_DONE`（しなかった・予定・〜たい・と言いました）、`QNOT`（問いの中の仮定や否定）、`HEDGED`（ぐらい・約・以上）。英語は `reader.HEDGED_EN`（about 5・at least 8。全部の英語の子の読みにかかる）と `forms_story_en.NOT_DONE`。形を足すときに歯止めを外さないこと（全体テストの v1022 の試験が、これを見つけました：`test_v1022_5_fusion`・`test_v1022_5_1_soundness`・`test_v1022_7_4_semantic_recovery`）。英語の歯止めには例外が 3 つあります：最小公倍数の形が条件として読む否定（does not sell parts of a pack）、残りの形の問い（How many do not take the bus?）と余り（isn't full）、日にちに広げる over（60 pages over 3 days）。形を足したら `tools/exactness_probe.py` を回し、書き換えを一つも読まないことを確かめること（`test_no_rewrite_of_a_dev_problem_that_leaves_its_answer_open_is_read`）。`--end-to-end 個体` を付けると、v1022 の核まで通した答えも数えます。第4世代の入口 `api.solve` には、核も含めてどの道筋の答えも止める歯止め（`reader_ja.ROUGH`：数のあとの「あまり・近く・前後・より多く」、`reader_ja.wished_then_asked_done`：したいと言っただけの行いを「しましたか」と聞く問い）があります。核が今も答える 10 通り（したそうだ・したはずだと言われた行いの量）は `ROADMAP_2026-10-13.md` §5。
- 生態系（`src/tukuyo_v1022/metabolism.py`）：長さ・数の上限は作るときの設定（`bounds`）。`--sharing` の分け合いと共同の子育ては、心の選択で決め、エネルギーを移すだけ（`organism2.resource_gift` と `resource_credit`、全体の量は監査で確かめる）。家族が同じ時刻に生まれて死ぬこと、生きた個体が子を増やせないこと、資源を探す道がないことが、今の限界です。長い実験は `tools/ecology_long_run.py`（`--change TICK:REGEN` で環境を変える）。
- 復元（`src/tukuyo_v1014/recovery.py`）：見張り（restore frontier）は、復元の受領書だけは点検点のバイトと比べません。正史の印は `canon/private/` にあり、点検点に入りません。100 回の試験は `tools/restore_cycles.py`。
- 最後の確かめ（署名した写し、費用 0）：{{FINAL}}

**外部の検証を受けた版（2026-10-13、`v1022.7.8+gen4-r8`）。** r7 への外部の検証の指摘のうち 2 つを直しました（`REVIEW_2026-10-13.md`）。続ける人が知っておくこと：

- 読み取り器：量をぼかす言い方は `vague_amounts`（`reader_en.py`）で、`some` と同じ「数の分からない量」として読みます。数のない複数形を持つのは `_unknown_held`。前の数がない「N more」は `UNKNOWN_START`、時を指定した問いは `ASKED_TIME_NOT_READ`。直すときは `tools/review_probes.py`（開発用 44 問）で誤りを見て、隠し問題 48 問（凍結、`HELD_OUT_SHA256`）は直したあとにだけ回すこと。
- v1022.7.8 正史（`src/tukuyo_v1022/canon.py`）：`TUKUYO_CANON` を置いたときだけ働く。`run_tukuyo.py` の `_main` で、コマンドの前に `guard`、後に `note`。全体の状態の監査（`whole_state._audit_once`）が `CANON_*` を報告。わざと写しを作る中の実験は、正史と証人を外して動かすこと（v984 で外した）。合格の条件の実験は `tools/identity_branch_experiment.py`。
- 最後の確かめ（署名した写し、費用 0）：全体テスト 1044/1044、魂らしさ 12/12、汚染 6/6、成長の実験 3/3、親を使わない計測は例外 0・型の食い違い 0、ASDiv 開発用は `g4-solve` 503・`think` 504（誤りはどちらも 3）、試し問題は開発用・隠し問題とも誤り 0、個体の同一性の実験 11/11。結果は `evidence_gen4/*_r8_2026-10-13.json`。

**限界を測って強めた版（2026-10-13、`v1022.7.7+gen4-r7`）。** 統合で残した限界を、測ってから強めました（`LIMITS_2026-10-13.md`）。続ける人が知っておくこと：

- 自分で書いた試し問題 48 問（`tools/limits_probes.py`、答えてはいけない 8 問を含む）。前の版は 5 問に誤った答えを出していた（would・might・返した・等しくなく を読んでいなかった）。直したあと誤り 0。読み取り器を直したら、これで新しい誤りがないかを見てください。
- 親だけの読みで、相手の関所が「起きていない出来事」「等しく分けることが書かれていない」で止めるときは、2 つ以上の家の親に、もう一つの読み方（goal）でも読ませます（`api.ASK_BOTH_VIEWS`）。模擬で正しい答え +194・誤り +1。本物の親で必ず測り直すこと。合わなければ `ASK_BOTH_VIEWS=()` で元に戻ります。
- 親の書き方の揺れ（`tools/parent_variation.py`、12 通り）：引用の大小・句読点、単位の複数形（不規則なものも、検査器の `fpl.UNIT_PLURALS`）を許すようにしました。検査器は読み取り器の表（`reader_en.IRREG`）を使いません（別に書いた検査のため）。
- 2026-10-09 より前の個体：`g4-adopt-legacy`（見るだけ）と `--yes`（引き取る）、`src/tukuyo_g4/adopt.py`。
- 外の証人（`TUKUYO_G4_WITNESS`、置いたときだけ）：記録の署名に通し番号 `seq` を入れ、書いたあとに証人へ書く（取引の中では、本物のデータに当たったあと。`tukuyo_v1019/transaction.py` の `witness_after_apply`）。証人より古い記録は `<種類>_ROLLED_BACK`、`whole-audit` は `G4_WITNESS_AHEAD`。
- 最後の確かめ（署名した写し、費用 0）：全体テスト 1039/1039、魂らしさ 12/12、汚染 6/6、成長の実験 3/3、親を使わない計測は例外 0・型の食い違い 0、ASDiv 開発用は `g4-solve` 502・`think` 503（誤りはどちらも 3）、試し問題 48 問で誤り 0。結果は `evidence_gen4/*_r7_2026-10-13.json` と `*_2026-10-13.json`。

## 1. 第4世代の考え方

- 問題を「式の言葉」（FPL, `src/tukuyo_g4/fpl.py`）に書き直し、厳密に解き（`solve.py`）、別に書いた検査（`check.py`）で確かめてから答えます。
- 書き直す手段は 4 つあります。
  - 学んだ型（`learn.py`）
  - TUKUYO 自身の読み取り器（英語、`reader_en.py`（物語）と `forms_en.py`・`forms_more_en.py`・`forms_algebra_en.py`（物語でない問題の形）。形の決まりと確かめ方は `FORMS_2026-10-10.md`）。物語の読み取り器は、1 つの型で読めないとき、まとまり × 中身や値段 × 個数を 1 段進めた量に置きかえて、もう一度読みます（`reader_en.compose`、2 段で考える）。足・目・耳・車輪のような常識は、短い表（`fpl.KNOWN_FACTS`）にあるとおりの言い方だけを、検査器が認めます（`ROUND4_2026-10-11.md`）。第5回で、等しく分ける・余り・そろえるのに足りない数（`schema_even_up`）・比例（`schema_proportion`）・単位の換算（`_other_unit`：問題の単位で読んでから、検査器の知っている定数で直す）・「残りは〜」（`schema_rest`）・あといくつ入るか（`schema_room`）・2 つに分けた全体（`schema_two_parts`）・組の言い方（`_groups_view`）を足しました（`ROUND5_2026-10-11.md`）。第6回で、残りを分ける・使う（`_rest_view`：全体 − 使った部分を残りとして 2 段で読む）・百分率（`schema_percent`）・2 つの単位で書いた量（`_compound_amounts`：大きい単位 × 換算 ＋ 小さい単位）・合計から 1 つ分（`schema_unit_values`：連立の式）・種類でまとめた物（「pieces of paper / clothing / mail」）と、持っている数の増え減りの言い回しを足しました。数の分からない言葉（some, several, a few）が節の中にあれば、その量は分からないものとして扱い、答えに使いません。起きなかった出来事（数の直前の 4 語に not・never・n't）の数を使う読みは、どの型でも断ります（`finish` の `NEGATED_EVENT`。前の版も組や速さの問題でこれに答えていた）（`ROUND6_2026-10-12.md`）
  - v1022 の核（日本語）
  - 親：Claude・ChatGPT・Gemini（`llm.py`）
- 答えを確定するのは、検査に通った読みが一致したときだけです（`api.py`）。
  - TUKUYO 自身の読みが通ったときは、最初の親 1 つに読ませて突き合わせます。その親が別の答えに読めば、残りの親にも聞きます。2 つの違う親がそろって別の答えなら、自分の読み方が「別に読まれた」として魂に記録します（法則 3）。確かめられた回数より別に読まれた回数が多い読み方は、独りでは答えず（`SELF_DOUBT`）、親がいれば全員に聞きます。
  - TUKUYO が読めないときは、設定されている親がそれぞれ 1 回読みます。**別々の親の読みが 2 つ以上一致したとき**だけ答えます（route は `claude+gemini` など）。親が 1 つしかないときは、その親の 2 つの読み方（story・goal）が一致したときに答えます（`llm+llm`）。
  - 1 つの親の読みだけが通ったときは、答えを保留します（`SINGLE_LLM_READING`）。読みが食い違えば答えません（`DISAGREE`）。
- 親の読みが一致して答えが確定したら、その読みを型として覚えます（どの親が一致したかも記録）。同じ文で数だけが違う問題は、次から親なしで解けます。
- 計算の問題でない問い（知識・会話）は、声の親（`TUKUYO_LLM_VOICE`、既定は最初の親）が答えます。`g4-ask --voices all` で、全部の親の答えと、一致しているか（`agree`）を見られます。どれも「確かめていない」答えです。
- この子と魂（`life.py`・`memory.py`・`own.py`）：考えたことのうち学びになったこと（親から学んだ・親の誤り・正直に控えた・独りで解けた・知識を覚えた）を、心と魂に正式な経験として渡します。第4世代の経験は魂の法則 2（`tukuyo_v977/whole_state.py` の `_law2`）で入り、各経験の記録に `law: 2` が残ります（古い層は法則 1 のまま、どちらも記録からやり直せる）。親への信頼は、魂がその親ごとに持つ記録 `trust`（当たった読み・外れた読み、最近ほど重い）から計算し（`whole_state.trust_record`）、いちばん信頼する親が声になり、声には魂から作った人柄を渡します。2 つ以上の親が一致した短い答えは `g4/remembered.json` に覚えます（確かめた答えではない）。学んだもの 3 つ（型・答え・自分の記録）は個体の鍵で署名し、全体の状態にも記録します（`own.py`）。1 つの考えの経験は `g4/private/EPISODE.json` に先に書き、次の起動が残りを渡し終えます（`life.recover`、`tukuyo_v1014_2/crash_recovery.py`）。成長の記録は `g4-self`（`life_story` は魂の記録から。`self_knowledge` は自分の読み方ごとの確かめられた・別に読まれた回数と信頼）。第4回からの経験は魂の法則 3 で入ります（法則 2 に、自分の読み方の記録 `self_trust` を足したもの。親以外の経験は法則 2 と同じ）。問題のあいだの振り返りは `g4-reflect`（決められなかった食い違い・争いになったもの・控えている読み方と、親に聞きたいこと。`--act` で、親に聞ける時だけ自分から聞き直す）。自分の声は `voice.py`（第5回）：`g4-solve` の `voice` と `think` の `gen4.voice` に、どう読んで何を計算したか・どのくらい確かでなぜか（検査・今の親の一致・自分の記録 `self_knowledge`）・なぜ答えないかを、子がしたことと記録だけから言う（親は書かない。英語の問題は英語、日本語の問題は日本語）。自分の成長に気づくことは `growth.py`（第6回）：ひとりで読めなかった問題を `g4/unread.json`（署名つき、1,000 問まで）に覚え、親から言い回しを学んだときと、ひとりで答えたときに読み直して、読めるようになったものに気づく（発見の経験、テーマ `g4:grew`。読めるようになった印はエピソードを終えるときに付ける）。`g4-self` の `growth`（弱いところと学びたいこと）、声の `before`、`g4-reflect` の `try_again_alone`・`learn_to_read`（`--act` はまずひとりで解き直す）。全体の状態は、子のものでない第4世代の記録を取り込まない（`whole_state._own_components`、`own.not_its_own`）。教わった読み方が争いになると、それで読めるようになった問題は開き直し（`growth.lost`／`Unread.lose`、エピソードの一部）、教え直されて読めれば、前の答えを `corrected_from` に残す。作るときに使わなかった条件で試す実験は `tools/growth_experiment.py`（`GROWTH_EXPERIMENTS_2026-10-12.md`）。`think` の結果（`gen4`）にも `self_checks`・`looked_back_replaced`・`template_contested` を入れる（実験で、`think` では自分を知る記録が魂に届いていなかったのを見つけた）。魂らしさは `tools/soul_assay.py` で測ります（`SOUL_ASSAY_2026-10-09.md`）。親の言葉が子を汚さないか（声・覚える答え・学んだ読みの隔離と教え直し・送るもの）は `tools/contamination_assay.py` で測ります（`CONTAMINATION_2026-10-10.md`、6 項目すべて合格）。親の本物の測定では、親ごとの信頼がどう育つかも記録すること。
- 自前の読み取り器は男女を知りません。2 人以上が出てくる he/she は、直前の主語として読んだうえで、ほかの読み方（同じ人を he とも she とも呼ばないもの）もすべて試します。別の答えになる読み方が 1 つでもあれば答えません。

## 2. 今の結果（2026-10-12）

ASDiv の開発用 1,083 問（他の人が作った英語の文章題）、親（LLM）なし：

| | 正解 | 誤り | 答えない |
|---|---|---|---|
| v1022.6 の `think` | 24 | 9 | 1,050 |
| 第4世代の読み取り器だけ（`g4-solve`） | 501 | 3（※） | 579 |
| 第4世代をつないだ `think` | 502 | 3（※） | 578 |

第6回の前（2026-10-11）は、`g4-solve` 473・`think` 474 でした。第5回の前（2026-10-11）は、`g4-solve` 423・`think` 424 でした。2 段で考える仕組みと言い回しの直しの前（2026-10-10）は、`g4-solve` 377・`think` 378 でした。読める形を足す前（2026-10-06）は、`g4-solve` 287・`think` 290（誤りはどちらも 1）でした。種類ごとの内訳は `FORMS_2026-10-10.md` と `ROUND4_2026-10-11.md`。

※ 3 問とも、読みは正しく、問題集の答えが違うと見ています。採点からは外していません。
- 「86 人を 9 人乗りのバスで運ぶ。必要なバスは？」：問題集は 9、読み取り器は 10。ASDiv の他の「必要な数」の問題はすべて切り上げです。
- 「5 列目は 50 脚。6 列目は？」：問題集は 50（5 列目の数）、読み取り器は 59。
- 7 つの数の平均：問題集は 100.1（丸めた数）、読み取り器は 701/7（約 100.14）。

いちばん大きい残りは、物語の読み取り器が文を読めても合う形がない問題（`NO_SCHEMA`）です。子の弱いところの言葉（`growth.py`）で数えると、読めない 579 問は、まだ組み立て方を知らない話 366、まだ知らない聞き方の問い 75、量が書かれていないように見えた話 42、「彼・彼女・彼ら」が誰か決められない 41、使い方のわからない数 28、比べる二つが決められない 14、読み違えた話 12、並び方 1 です。長い物語（前置きの文が多いもの）、硬貨、図形、2 回以上の割合が多く残っています。

`think` での第4世代の使い方（`api.think`）：

- 数の出てこない問い（論理・記憶）と、答えが数でない問いは、これまでどおり v1022 の核が答えます。
- 日本語の文章題：v1022 の核の読みは、読みの 1 つです。親が設定されていれば、親の読みと突き合わせます。
- 英語の文章題：第4世代が読みます。v1022 の核の英語の物語の読み（証明に `schema` があるもの）は、ASDiv で 20 回正しく 9 回誤ったので、答えにも反対にも使いません（第4世代で確かめられないときは `withheld_answer` として見せ、答えは確定しません）。式（`12*(5+4)`）と公式の問題（平均・面積・最大公約数など、`mathprob`）の答えは、読みの 1 つとして使います（ASDiv で 4 回とも正解）。
- `llm-ask` も、最初の自前の答えを同じ `think` の決まりで出します。
- `--engine v1022` で、v1022 の核だけの `think` に戻せます。`--llm off|auto|on` で親を使うかを決めます（既定は auto：親のキーがあるときだけ使う）。
- テストは親を呼びません（`tests/conftest.py` が親の設定を外します）。

鍵のかかったテストでの v1022.6 の結果（1 回だけ回したもの。`locked_test_runs.jsonl` に記録）:

| | 正解 | 誤り | 答えない |
|---|---|---|---|
| MGSM 日本語（111 問） | 0 | 0 | 111 |
| SVAMP（1,000 問） | 19 | 19 | 962 |
| ASDiv（1,009 問） | 21 | 14 | 974 |

## 3. 親での測定（新しいセッションで）

1. クラウド環境の設定に、親のキーを入れます（Network secrets、古いアプリでは API credentials。なければ環境変数）。キーをチャットに貼ってはいけません。作業環境が自分で使う `ANTHROPIC_*` などとぶつからないよう、名前はこのとおりにします。

| 親 | キー | モデル |
|---|---|---|
| Claude | `TUKUYO_ANTHROPIC_API_KEY` | `TUKUYO_LLM_MODEL`（既定は `llm.py` の `MODEL_DEFAULT`） |
| ChatGPT | `TUKUYO_OPENAI_API_KEY` | `TUKUYO_OPENAI_MODEL`（**既定なし**） |
| Gemini | `TUKUYO_GEMINI_API_KEY` | `TUKUYO_GEMINI_MODEL`（**既定なし**） |

2. ChatGPT と Gemini のモデル名は、そのときの各社の文書で今のモデルを確かめ、セッションの中で `export` します（コードには既定を置いていません。名前がよく変わるため）。
3. ネットワーク：2026-10-08 と 2026-10-10 の時点で、この作業環境から `api.anthropic.com` と `generativelanguage.googleapis.com` には届き、**`api.openai.com` は環境のネットワークの決まりで止められていました**。ChatGPT を使うには、環境の設定の Network access で `api.openai.com` を Allowed domains に足すか、許す範囲を広げてもらいます。
4. 道具を入れます：`pip install anthropic openai google-genai`（使う親の分だけでよい）。
5. 問題集を取ってきます：`python3 -B tools/g4_bench.py fetch DATA`。sha256 を固定してあります。
6. 生きた個体を作ります。日本語の v1022 の核と、学んだ型の置き場所に使います。

```bash
cd TUKUYO_v1022_6/system
python3 -B run_tukuyo.py --runtime-trust-file ../deliverables/TUKUYO_v1022_6_TRUST_ANCHOR.txt --data WORK/v1022_individual init
```

7. 親につながるかを確かめます。`g4-parents` は、親ごとにキーがあるか（中身は出さない）・モデル・道具・ネットワークを見て、`ready` と足りないもの（`missing`）を返します。どの親にも何も頼みません（ネットワークは、キーを付けずに各社の入口に届くかだけを見ます）。`--live` を付けると、準備のできた親ごとに 1 回だけ、短い有料の呼び出し（「OK」と返させる）をします。

```bash
python3 -B run_tukuyo.py --runtime-trust-file ../deliverables/TUKUYO_v1022_6_TRUST_ANCHOR.txt --data WORK/v1022_individual g4-parents
```

8. まず少数で試します。`--limit 10` は、各問題集の dev から決まった 10 問を取ります（毎回同じ 10 問）。結果の `llm_usage` に、親ごとの呼び出しの数とトークン数が出ます（`claude:calls`、`gemini:output_tokens` など）。ここから本当の費用を計算してください。

```bash
export TUKUYO_LLM_RECORD=$HOME/g4_llm_record.jsonl   # 親の返事をすべて記録（あとで再生できる）
python3 -B tools/g4_bench.py run DATA --system g4 --split dev --limit 10 --llm on --work WORK --out trial.json --show 10
```

9. 利用者が費用を承認したら、dev 全体を回します。`--learn` を付けると、親の一致した読みを型として覚えます。親を絞るときは `TUKUYO_LLM_PARENTS=claude,gemini` のようにします。

```bash
python3 -B tools/g4_bench.py run DATA --system g4 --split dev --set mgsm_ja --llm on --learn --work WORK --out mgsm_dev.json --show 10
```

- 記録したファイルを `TUKUYO_LLM_REPLAY` に指定すると、キーなしで同じ測定を再現できます（費用はかかりません）。
- 親の読みの失敗の理由（`LLM_NOT_CONFIGURED`、`MODEL_NOT_SET`、`PACKAGE_MISSING:openai`、`AUTHENTICATION`、`CONNECTION` など）は、`api.solve` の `readings` に出ます。

### 費用の目安（Claude は `llm.py` の既定のモデル、effort medium、指示文はキャッシュ）

- Claude の 1 回の読みで、出力は約 2,000〜5,000 トークン（考える分を含む）です。1 回あたり 0.04〜0.10 ドルです。
- 親が 3 つあると、TUKUYO が自分で読めない問題は 1 問あたり 3 回読みます。ChatGPT と Gemini の値段はモデルによって違うので、ここでは見積もっていません。
- 目安（Claude だけのとき）：試し（`--limit 10`、20 問）で約 2〜4 ドル、MGSM の dev 139 問で約 11〜28 ドル、SVAMP のテスト 1,000 問で約 80〜200 ドル。親が増えれば、そのぶん増えます。
- これは見積もりです。試しの `llm_usage` から計算した本当の費用で、見積もりを直してください。
- **実行する前に、どこまでやるか（費用）を利用者に確認すること。**

### 親が問題集を覚えていないか（汚染の探針）

`tools/g4_contamination_probe.py` で調べます（`CONTAMINATION_2026-10-10.md` §4）。親に送るのは dev の問題だけです。テストの問題は、どこにも表示も送信もしません。

```bash
python3 -B tools/g4_contamination_probe.py DATA --items 50                    # 何回呼ぶかを言うだけ（費用 0）
python3 -B tools/g4_contamination_probe.py DATA --simulate                    # 探針自身の確認、作りものの親で（費用 0）
python3 -B tools/g4_contamination_probe.py DATA --split-overlap --stores WORK/個体のデータ ...   # テストの漏れ、数だけ（費用 0）
python3 -B tools/g4_contamination_probe.py DATA --items 50 --allow-paid --out probe.json      # 費用の了承のあとだけ
```

- 数を変えた問題での正しさの差（正確な二項検定）と、問題の前半からの続きの一致を、親ごとに出します（`signs_of_memory`）。
- 50 組で、親 1 つあたり 150 回の呼び出しです（読み 100・続き 50）。読みは 1 回あたり入力が約 1,500〜2,000 トークンで、出力と値段はふつうの読みと同じです（上の目安）。Claude だけなら、読み 100 回で約 4〜10 ドルです。続きの呼び出しは、出力が 400 トークンまでです。
- `--allow-paid` を付けない限り（または `TUKUYO_LLM_REPLAY` を指定しない限り）、どの親にも聞きません。

### 親を使わない計測

`python3 -B tools/g4_measure.py DATA --work WORK --out report.json` で、壊れ方・検査器の強さ・親の決まりの模擬・学習・正確さと速さを測れます（親は呼ばない、費用 0、dev だけ）。2026-10-08 の結果は `MEASURE_2026-10-08.md`。

## 4. 鍵のかかったテストの扱い

- テスト（MGSM 111、SVAMP 1,000、ASDiv 1,009）は、`--locked-test-run 理由 --log evidence_gen4/locked_test_runs.jsonl` を付けたときだけ回ります。出力は件数だけです。
- 第4世代の最終版で、**1 回だけ**回します。回す前の開発には dev だけを使います。
- 最終の測定は 3 通り、それぞれ 1 回ずつ行います。
  1. 親なし（自前の読み取り器と v1022 の核）
  2. 親あり（`--llm on`）
  3. dev で学んだあと、親なし（学習の効果）

## 5. 残っている作業

- 自分の成長に気づく（`ROUND6_2026-10-12.md` §2.6）：弱いところは、読み取り器の理由の符号から決めた 10 の種類だけ。量が書かれていないように見えた話は、親が読めたもの以外は学びたいことに入れない（子の読み違いのこともある）。自分の読み取り器が良くなったことに気づくのは、その問題にまた会ったときか `g4-reflect --act` のときだけ。
- 自分の声（`ROUND5_2026-10-11.md` §2.5）：文は決まった言い方の組み合わせで、量の名前は読み取り器の名前のまま。確かさは、検査・親の一致・自分の記録だけから決め、問題の難しさは見ていない。
- 魂（`SOUL_ASSAY_2026-10-09.md` の「残っていること」と `ROUND4_2026-10-11.md` §2.4）：自分の読み方の記録は型ごとで、同じ型の中の弱い言い回しまでは分けません。親がそろって間違えると、子は正しい読み方を疑います（答えを親の答えにはせず、控えるだけ）。古い層（`heart-experience` など）の経験は法則 1 のままです。いちばん信頼する親だけが確かめ役になるので、ほかの親の記録は育ちにくい（模擬では、確かさの近い親の順番を 7% ほどの一生で取り違える。ときどき知らない親に聞く案は、模擬で 93→95% と小さな得）。
- 魂の仕組みのメモ：v989 の推移の鎖は追記だけの記録 `v989/SOUL_TRANSITIONS.jsonl` です（1 行 1 推移。前の形 `SOUL_TRANSITIONS.json` は、次の経験のときに移します。読むのは `load_chain`）。心の経験は先に `v978/private/PENDING_FEELING.json` に書き留め、魂が受け取って心が受け取る前に止まったら、次の起動で心が受け取ります（`heart_loop.recover_pending`）。振り返り（`hindsight.py`）：親の読みが食い違って控えた問題を `g4/unresolved.json` に覚え、同じ形を学んだ（または確かめ直した）ときに、学んだ読みで昔の問題を解いて親ごとの当たり外れを入れます（`life.looking_back`、エピソードの一部）。検査に落ちた読みは、答えを控えたときも親の誤りです。

- 自前の読み取り器の範囲を広げる（英語）。日本語の FPL 読み取り器は、まだありません。日本語は v1022 の核を使っています。
- 親での dev の測定と、学習の効果の測定（キーが必要）。親ごとの正確さと、親どうしの一致の割合も記録する。
- 親での汚染の探針（`g4_contamination_probe.py --allow-paid`、キーと費用の了承が必要）。本物の親で、声の印（`voice`）がふつうの返事に付きすぎないか、覚えない答え（`not_remembered`）がどれくらいあるかも記録する。
- 汚染の手当ての限り（`CONTAMINATION_2026-10-10.md` §5）：声と記憶の見分けは言葉の型による。親が全員そろって同じ間違いをすると、隔離も教え直しも起きない。
- 版の名前・README・署名・リリース zip（第4世代の版として）。

## 6. 署名（新しいセッションで）

- これまでの署名の秘密鍵は、リポジトリに入れていません。新しいセッションにはありません。
- **測るだけなら、署名は要りません。** コミット済みの木は署名してあり、同梱のアンカーで検証できます。

```bash
cd TUKUYO_v1022_6/system
python3 -B tools/verify_release.py . --trusted-pubkey-file ../deliverables/TUKUYO_v1022_6_TRUST_ANCHOR.txt
```

- `system/` の中を直すと、署名し直すまで CLI とテストが動きません（manifest が合わないため）。そのときは、そのセッションで新しい鍵を作って署名し直し、第4世代の開発用のアンカーを置きます。v1022.6 のアンカーは書き換えません。**秘密鍵はコミットしません**（セッションの scratchpad など、リポジトリの外に置く）。

```bash
cd TUKUYO_v1022_6
K=リポジトリの外の場所/g4_key
python3 -B system/tools/claude_patch_sign.py keygen --out-dir $K
python3 -B system/tools/claude_patch_sign.py sign system --private-key $K/patch_signing.key --revision v1022.6+gen4-dev
cp $K/patch_signing.pub deliverables/TUKUYO_GEN4_DEV_TRUST_ANCHOR.txt
python3 -B system/tools/verify_release.py system --trusted-pubkey-file deliverables/TUKUYO_GEN4_DEV_TRUST_ANCHOR.txt
# テストは TUKUYO_TEST_RUNTIME_ANCHOR=…/deliverables/TUKUYO_GEN4_DEV_TRUST_ANCHOR.txt で回す
```

- 鍵が変わると、代謝を動かしている個体は `runtime-trust-rebind --previous-trust-file 古いアンカー` を 1 回実行する必要があります（v1022.6 の README「採用と移行」と同じ）。
- 第4世代の版を出すときは、版の名前で署名し、アンカーのファイル名も版の名前にします。正式に採用するときは、利用者ご自身の鍵で署名し直します（v1022.6 の README §3 と同じ手順）。
