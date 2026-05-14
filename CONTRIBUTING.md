# Contributing to もりみえる

もりみえる（morimieru）は **公益基盤プロジェクト** です。
誰でも、どんな立場でも歓迎します。

---

## 私たちの考えていること

- **林業の未来のために、無料・オープン・透明な基盤を作る**
- 既存大手の高コスト B2B 受託モデルでは、自治体・小規模森林組合・住民に届かない
- 衛星・公開データ・AI で「森の見えない価値」を誰でも触れる形にする
- 事業モデルは決めない。基盤がしっかり育つ過程で「何ができるか」が見えてくる

---

## 貢献の仕方

### コード

1. Fork してブランチを切る
2. 変更を加える
3. ローカルで動作確認（`python -m http.server 8765` で開く）
4. Pull Request を出す（説明には「なぜこの変更か」を1〜2文で）

### データ

新しい公開データを統合するアイデア（自治体オープンデータ、衛星、林野庁等）は
GitHub Issue で提案してください。
ライセンス・出典明示が必須です。

### ドキュメント

レポート構成・計算根拠・用語説明の改善は大歓迎です。
特に：
- IPCC 整合性のレビュー
- 林野庁簡易評価法 Ver.1.0 の解釈確認
- 自治体・林業者・住民の声を反映した UI 改善

### 不具合報告

- スマホ表示で崩れる
- データが間違っている
- 計算根拠の不一致

→ GitHub Issue でお知らせください。

---

## 開発環境

```bash
git clone https://github.com/Ryujiyasu/morimieru.git
cd morimieru
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # 必要なら作る
python -m http.server 8765
# → http://localhost:8765/
```

---

## データ・スクリプト

`scripts/` には外部 API からデータを取得・処理するスクリプトがあります：

- `fetch_himi_cdse.py`: Sentinel-2 NDVI (CDSE)
- `estimate_co2_himi.py`: IPCC Tier 2 CO2 算定
- `estimate_water_himi.py`: 林野庁簡易評価法 水資源涵養量
- `fetch_shizuoka_rinpan.py`: 静岡県森林クラウド林班ポリゴン
- `compute_rinpan_water.py`: 林班ごとの水収支計算
- `parse_jcredit.py`: J-クレジット 264件 登録一覧

各スクリプトは独立に動きます。`-h` か冒頭の docstring で目的を確認してください。

---

## CDSE Sentinel Hub の認証情報

`/etc/morimieru/sentinel-hub.env` (root 600) に保存：

```
SH_CLIENT_ID=sh-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
SH_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

クライアント情報は環境変数 `SH_CREDS_FILE` で上書き可能。

---

## 行動規範

- 林業の未来を一緒に作る気持ちで関わる
- 商業的な囲い込みを目的とした提案は受け入れない
- 全データ・全式・全プロセスをトランスペアレントに保つ
- 営利では届かないユーザー（自治体・住民・教育機関・小規模団体）の声を最優先

---

## 連絡先

- Maintainer: 安河内竜二（株式会社エムスクエア・ラボ）
- Email: r.yasukouchi@m2-labo.jp
- GitHub Issues: https://github.com/Ryujiyasu/morimieru/issues
