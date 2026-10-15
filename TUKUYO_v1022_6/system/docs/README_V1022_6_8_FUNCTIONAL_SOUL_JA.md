# TUKUYO V1022.6.8 Functional Soul Experimental

V1022.6.7 の署名付き頭脳・生命・復元基盤へ、監査可能な「機能的Soul統合層」を追加した実験版です。文字通りの魂、主観意識、人格性を成立・証明した版ではありません。

## 追加したもの

- 連続性、内的調整、自伝、価値、関係、認識の6面を、既存の署名済み状態から再構成します。一つの固定的な「魂の数値」にはしません。
- 同じ `vow` が別々の正規イベントとして2回以上記録された場合だけ、候補から成熟コミットメントへ上げます。一度言われただけの内容は選択を強制しません。
- `soul-deliberate` は、通常の Heart score と統合Soulの加減点を分けて保存し、「統合層がなければ何を選んだか」という反実仮想を署名付き決定証明へ残します。
- 上位2案の差が 0.1 未満なら、行動せず `review_required` として保留します。
- 私的なコミットメント、自己物語、決定履歴は successor package へ入れません。子へ渡るのは従来どおり限定された価値プロファイルと公開能力だけです。
- 平均2個・平均値・既知の1個から残りを求める英語文章題を追加し、producer と別実装の parser でも再計算します。

## 使い方

```bash
python -B run_tukuyo.py --runtime-trust-file /absolute/path/TRUST_ANCHOR.txt --data /absolute/path/individual init
python -B run_tukuyo.py --runtime-trust-file /absolute/path/TRUST_ANCHOR.txt --data /absolute/path/individual heart-experience vow 0.8 0.8 --theme truth
python -B run_tukuyo.py --runtime-trust-file /absolute/path/TRUST_ANCHOR.txt --data /absolute/path/individual heart-experience vow 0.8 0.8 --theme truth
python -B run_tukuyo.py --runtime-trust-file /absolute/path/TRUST_ANCHOR.txt --data /absolute/path/individual soul-integrate
python -B run_tukuyo.py --runtime-trust-file /absolute/path/TRUST_ANCHOR.txt --data /absolute/path/individual soul-deliberate options.json --context 'truth under pressure'
python -B run_tukuyo.py --runtime-trust-file /absolute/path/TRUST_ANCHOR.txt --data /absolute/path/individual soul-integrity-audit
python -B run_tukuyo.py --runtime-trust-file /absolute/path/TRUST_ANCHOR.txt --data /absolute/path/individual whole-audit
```

`options.json` の各案は `id`、-1〜1 の `signals`、支持する `themes`、反する `conflicts` を持ちます。テーマの意味が外界で正しいかをTUKUYOが独立検証したわけではないため、結果は入力注釈を条件とします。

## 脳研究から借りた設計原理

最新研究は意識の単一理論を確定していません。この版は、全体で使える情報の選別、内受容・恒常性、記憶の再活性化、確信度という機能だけを設計上の参考にしました。脳との機構的同一性や意識を主張しません。

## 魂に関する記述の扱い

アリストテレスの生命機能、仏教の非固定的な五蘊、中国の魂魄、日本の `tama/mitama`、古代エジプトの複数要素、インドの Atman などは互いに同じ教説ではありません。この版では、それらを混ぜた宗教説を作らず、「魂を単一物に還元しない」という比較上の注意として、6つの機能面を別々に保持します。原典・研究への対応は `META/NEURO_SOUL_DESIGN_REFERENCES_V1022_6_8.json` に記録しています。

## 境界

これは EXPERIMENTAL です。文化・宗教上の魂の実在、主観意識、感覚質、人格性、一般知能、自己コード改変、自然選択、24時間無人運転は証明していません。旧版から残る workspace 復元後の未来ファイル再出現も根本解決していません。
