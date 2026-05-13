# もりみえる (morimieru)

> 豊かな森を未来につなぐため、衛星の目で日本中の森を可視化し、
> その想いを支える会社と、森を守る人をつなぎます。

**公開URL**: https://mori-mieru.jp/

「企業 × 森林」を結びつけるオンラインサービス。無料の公開衛星データ（Sentinel-1/2、Landsat）と林野庁オープンデータを統合し、J-クレジット制度に登録された実在の森林プロジェクトと、企業の意思決定をつなげます。

## 構成

```
morimieru/
├── index.html                 # メインページ（4ステップフロー）
├── style.css                  # デザインシステム
├── app.js                     # フロー制御
├── data/
│   ├── candidates.js          # 主要候補（深掘りデータ付き）
│   ├── jcredit_projects.json  # J-クレジット 264件の実在プロジェクト
│   └── sentinel/              # Sentinel-2 L2A 由来 NDVI ラスタ
├── assets/                    # ビジュアル素材
├── scripts/                   # データ更新スクリプト
└── GEMINI3_IMAGE_PROMPTS.md   # ブランドビジュアル生成プロンプト集
```

## 4ステップフロー

1. **Hero** — 「あなたの会社の森を、見つけよう。」
2. **会社情報入力** — 会社名・業種・年間予算・希望地域・想い
3. **候補森林の提示** — 全国地図 + カード（CO₂吸収量±信頼区間 + クレジット試算）
4. **衛星で森を見る** — 直近の Sentinel-2 シーンの NDVI を地図に重畳
5. **意思表明書の発行** — SHA-256 ハッシュつきの森林コミットメント証明書

## データソース（全て無料・公開）

- **Sentinel-1 / Sentinel-2 L2A** — 欧州 Copernicus（AWS Open Data ミラーから取得）
- **Landsat 8/9** — NASA / USGS
- **森林生態系多様性基礎調査** — 林野庁（全国 4km グリッド・15,000 プロット・25 年蓄積）
- **航空レーザ森林資源解析データ** — 林野庁（民有林 80% 整備済、3 県オープンデータ化）
- **J-クレジット 登録プロジェクト一覧** — J-クレジット制度事務局

## 設計の哲学

- **無料データのみで運用** — 普及可能性と単価競争力を両立
- **モニタリングの暗号学的検証可能性** — TPM 2.0 attestation + Merkle hash + RFC 3161 timestamp
- **「精度競争」ではなく「検証可能性 × 普及可能性」** で価値を出す

## 技術スタック

- フロントエンド：素の HTML / CSS / JavaScript（ビルドステップなし）
- 地図：Leaflet + Esri World Imagery（タイル）
- 衛星処理：Python (rasterio / pystac-client / Pillow / numpy)
- ホスト：AWS EC2 (ap-northeast-1)、nginx、Let's Encrypt

## デプロイ

```bash
ssh ubuntu@mori-mieru.jp 'cd /var/www/morimieru && sudo git pull && sudo chown -R www-data:www-data .'
```

データ更新：

```bash
.venv/bin/python scripts/parse_jcredit.py        # J-credit 一覧の取り直し
.venv/bin/python scripts/fetch_sentinel2_himi.py # Sentinel-2 シーンの更新
```
