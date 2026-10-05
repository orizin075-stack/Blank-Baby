seconds 387.1

### F/T (held-out, once)

| セット | コマンド | patch5 正答 | patch5 確信を持った誤り | patch6 正答 | patch6 確信を持った誤り | patch6 答えなかった |
|---|---|---|---|---|---|---|
| F（79 問） | `think` | 51 | 0 | **72** | **0** | 7 |
| F（79 問） | `verified-query` | 50 | 0 | **71** | **0** | 8 |
| F（79 問） | `llm-ask` | 51 | 0 | **72** | **0** | 7 |
| T（38 問） | `think` | 7 | 10 | **38** | **0** | 0 |
| T（38 問） | `verified-query` | 7 | 8 | **36** | **0** | 2 |
| T（38 問） | `llm-ask` | 7 | 10 | **38** | **0** | 0 |

### per category (think)

| F の型 | 問題数 | patch5 正答 | patch6 正答 | patch6 誤り |
|---|---|---|---|---|
| F_abstain | 11 | 11 | 11 | 0 |
| F_area | 4 | 0 | 4 | 0 |
| F_average | 3 | 0 | 3 | 0 |
| F_change | 9 | 8 | 9 | 0 |
| F_compare | 8 | 5 | 7 | 0 |
| F_equation | 5 | 3 | 3 | 0 |
| F_fraction | 3 | 1 | 3 | 0 |
| F_groups | 10 | 6 | 10 | 0 |
| F_multi | 7 | 5 | 5 | 0 |
| F_number | 4 | 0 | 4 | 0 |
| F_price | 7 | 4 | 5 | 0 |
| F_rate | 6 | 6 | 6 | 0 |
| F_time | 2 | 2 | 2 | 0 |

| T の型 | 問題数 | patch5 正答 | patch6 正答 | patch6 誤り |
|---|---|---|---|---|
| T_event | 13 | 0 | 13 | 0 |
| T_initial | 6 | 0 | 6 | 0 |
| T_object | 3 | 0 | 3 | 0 |
| T_other | 5 | 0 | 5 | 0 |
| T_remain | 11 | 7 | 11 | 0 |


### C/D/E (patch6) vs patch5 published

| セット | コマンド | patch5 正答（誤り） | patch6 正答（誤り） |
|---|---|---|---|
| C（93 問） | `think` | 69（0） | **88**（0） |
| C（93 問） | `verified-query` | 69（0） | **87**（0） |
| C（93 問） | `llm-ask` | 73（0） | **92**（0） |
| D（50 問） | `think` | 42（0） | **49**（0） |
| D（50 問） | `verified-query` | 42（0） | **49**（0） |
| D（50 問） | `llm-ask` | 42（0） | **49**（0） |
| E（36 問） | `think` | 32（0） | **36**（0） |
| E（36 問） | `verified-query` | 32（0） | **36**（0） |
| E（36 問） | `llm-ask` | 32（0） | **36**（0） |

### Parser B AGREE among gated commits (think)

| セット | patch5 | patch6 |
|---|---|---|
| F | 12/40 | 35/61 |
| T | 14/17 | 22/36 |
| C | – | 39/48 |
| D | – | 22/28 |
| E | – | 18/28 |

### wrong-certain rows

patch5 think T T_initial みかんが24個あります。9個食べました。はじめにみかんは何個ありましたか？ -> 15 expected 24
patch5 think T T_initial カードが36枚あります。友だちに9枚あげました。あげる前は何枚でしたか？ -> 27 expected 36
patch5 think T T_event えんぴつが18本あります。弟に5本あげました。弟にあげたのは何本ですか？ -> 13 expected 5
patch5 think T T_event シールが40枚あります。友だちから15枚もらいました。もらったのは何枚？ -> 55 expected 15
patch5 think T T_event ノートが25冊あります。7冊使いました。使ったのは何冊？ -> 18 expected 7
patch5 think T T_event ボールが14個あります。3個もらって、5個あげました。もらったのは何個？ -> 12 expected 3
patch5 think T T_other クッキーが30枚あります。妹に8枚あげました。妹は何枚もらいましたか？ -> 22 expected 8
patch5 think T T_other あめが20個あります。弟に6個あげました。弟は今あめを何個持っていますか？ -> 14 expected None
patch5 think T T_other Mia had 20 pencils. She gave 6 pencils to Leo. How many pencils does Leo have now? -> 14 expected None
patch5 think T T_object りんごが15個あります。4個食べました。みかんを6個もらいました。りんごは何個ありますか？ -> 17 expected 11
patch5 verified-query T T_initial カードが36枚あります。友だちに9枚あげました。あげる前は何枚でしたか？ -> 27 expected 36
patch5 verified-query T T_event えんぴつが18本あります。弟に5本あげました。弟にあげたのは何本ですか？ -> 13 expected 5
patch5 verified-query T T_event シールが40枚あります。友だちから15枚もらいました。もらったのは何枚？ -> 55 expected 15
patch5 verified-query T T_event ノートが25冊あります。7冊使いました。使ったのは何冊？ -> 18 expected 7
patch5 verified-query T T_event ボールが14個あります。3個もらって、5個あげました。もらったのは何個？ -> 12 expected 3
patch5 verified-query T T_other クッキーが30枚あります。妹に8枚あげました。妹は何枚もらいましたか？ -> 22 expected 8
patch5 verified-query T T_other あめが20個あります。弟に6個あげました。弟は今あめを何個持っていますか？ -> 14 expected None
patch5 verified-query T T_other Mia had 20 pencils. She gave 6 pencils to Leo. How many pencils does Leo have now? -> 14 expected None
patch5 llm-ask T T_initial みかんが24個あります。9個食べました。はじめにみかんは何個ありましたか？ -> 15 expected 24
patch5 llm-ask T T_initial カードが36枚あります。友だちに9枚あげました。あげる前は何枚でしたか？ -> 27 expected 36
patch5 llm-ask T T_event えんぴつが18本あります。弟に5本あげました。弟にあげたのは何本ですか？ -> 13 expected 5
patch5 llm-ask T T_event シールが40枚あります。友だちから15枚もらいました。もらったのは何枚？ -> 55 expected 15
patch5 llm-ask T T_event ノートが25冊あります。7冊使いました。使ったのは何冊？ -> 18 expected 7
patch5 llm-ask T T_event ボールが14個あります。3個もらって、5個あげました。もらったのは何個？ -> 12 expected 3
patch5 llm-ask T T_other クッキーが30枚あります。妹に8枚あげました。妹は何枚もらいましたか？ -> 22 expected 8
patch5 llm-ask T T_other あめが20個あります。弟に6個あげました。弟は今あめを何個持っていますか？ -> 14 expected None
patch5 llm-ask T T_other Mia had 20 pencils. She gave 6 pencils to Leo. How many pencils does Leo have now? -> 14 expected None
patch5 llm-ask T T_object りんごが15個あります。4個食べました。みかんを6個もらいました。りんごは何個ありますか？ -> 17 expected 11

### patch6 think abstentions on F/T

F F_compare ゆうさんは本を23冊、あきさんは本を38冊読みました。あきさんはゆうさんより何冊多く読みましたか？ expected 15
F F_equation ある数から12を引いて3倍すると27になります。ある数は？ expected 21
F F_equation ある数に4を足して2倍すると30になります。ある数は？ expected 11
F F_price 3000円の品物を2割引きで買いました。いくらで買いましたか？ expected 2400
F F_price 1個120円のりんごを5個と、1個80円のみかんを5個買いました。代金は全部でいくらですか？ expected 1000
F F_multi 1袋8個入りのみかんを5袋買って、6個食べました。残りは何個ですか？ expected 34
F F_multi クラスの生徒は35人で、そのうち男子は18人です。女子は何人ですか？ expected 17

### whole-audit after each run
 {'F|patch5|think': True, 'F|patch5|verified-query': True, 'F|patch5|llm-ask': True, 'T|patch5|think': True, 'T|patch5|verified-query': True, 'T|patch5|llm-ask': True, 'F|patch6|think': True, 'F|patch6|verified-query': True, 'F|patch6|llm-ask': True, 'T|patch6|think': True, 'T|patch6|verified-query': True, 'T|patch6|llm-ask': True, 'C|patch6|think': True, 'C|patch6|verified-query': True, 'C|patch6|llm-ask': True, 'D|patch6|think': True, 'D|patch6|verified-query': True, 'D|patch6|llm-ask': True, 'E|patch6|think': True, 'E|patch6|verified-query': True, 'E|patch6|llm-ask': True}
errors {}
