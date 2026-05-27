# もりみえる（morimieru）プロジェクト概要

最終更新：2026-05-19

---

## 1. 一行で言うと

> **無料公開の衛星データ × オープンデータを統合し、日本の森林の「見えない価値」（水源涵養・CO₂吸収・流域つながり・生物多様性）を、誰でも・無料で・透明な計算式で可視化する公益基盤。**

公開URL：**https://mori-mieru.jp/**

---

## 2. 解決したい問題

森林には「市場価格に現れない多面的機能」が大量にある。
- 水を貯える（水源涵養）
- CO₂を吸収・固定する
- 土砂崩れを防ぐ
- 生物多様性を支える
- 木材を供給する

これらは個別の研究や受託案件では数値化されているが、**「日本全国・市町村・流域・林班単位で誰でも引ける形」**で整備されていない。
結果として、TNFD 開示・カーボンクレジット購入・自治体の森林整備・市民の森林理解、すべてで「数字で示す根拠」が不足している。

もりみえるは、ここを **無料・透明・全国** で埋める基盤を目指している。

---

## 3. 立ち位置（戦略）

| 軸 | 大手・受託SI | もりみえる |
|---|---|---|
| 顧客 | 大企業・自治体（受託） | 誰でも（無料Web） |
| 精度 | 受託毎にチューニング・高 | 標準データ・中（±10〜30%） |
| 対応エリア | 案件毎 | **日本全国 pre-integrated** |
| 透明性 | レポート提出 | **全式・全インプット公開** |
| 強み | 精度・サポート | **検証可能性 × 普及可能性** |

> 「精度競争」ではなく **「検証可能性 × 普及可能性」** で価値を出す。
> 受託の大手連合では届かない、個人・小規模団体・自治体・教育機関のための **オープン公益基盤**。

---

## 4. 機能（実装済み）

### 4.1 流域マッチング v1
住所を入れると、その地点の **取水域 → 上流の森林** を自動特定。
- HydroBASINS Lvl 10（CC-BY、商用OK）
- ジオコーディング：国土地理院
- 平均集水面積：約100km²

### 4.2 水源涵養量の定量算定
林野庁「林地における水資源涵養量の簡易評価手法 Ver.1.0」（令和8年3月公開）準拠。
- 水収支法：降水量 − 蒸発散 − 直接流出
- 入力：NASA POWER 気象 / 産総研シームレス地質図 / 国土数値情報 森林
- 実例：氷見市 **年間 約1.19億トン**（一般家庭160万世帯相当）

### 4.3 CO₂吸収量推定
IPCC AFOLU **Tier 2** 手法。
- Sentinel-2 NDVI → 森林マスク（10mピクセル）
- 林班単位（中央値100ha）で集計
- 静岡県 1,102林班（161,182ha）実装済 → 年間 約130万 t-CO₂

### 4.4 衛星 NDVI 時系列モニタリング
- Copernicus Sentinel-2 L2A、5年時系列
- 氷見市 71観測点・10mグリッド
- 施業前後の差分から「整備効果」を量化（衛星MRV）

### 4.5 J-クレジット 264件マップ
J-クレジット制度事務局から取得した森林由来プロジェクト全264件を地理情報付きで可視化。
2026年5月時点で、2025年中盤に¥10,000を突破した相場感も統合。

### 4.6 3D水循環シミュレータ（PoC 段階）
- エンジン：**ParFlow 3.15.0**（LLNL/ボン大、LGPL、3D Richards + Shallow Water + CLM）
- 同サーバ上で **Little Washita 12日シミュレーション 18秒**、**氷見市 10km×10km 6時間シミュレーション 5秒** で動作確認済
- 詳細：[SIMULATOR_ROADMAP.md](SIMULATOR_ROADMAP.md)

### 4.7 暗号学的検証可能性（モニタリング報告書）
- TPM 2.0 attestation + Merkle hash + RFC 3161 timestamp
- レポートPDFに改ざん不可な署名を付与（hyde）

---

## 5. データソース（すべて無料・公開）

| データ | 出所 | ライセンス |
|---|---|---|
| Sentinel-1 / Sentinel-2 L2A | 欧州 Copernicus / CDSE | 無料・商用OK |
| Landsat 8/9 | NASA / USGS | 無料・商用OK |
| NASA POWER（気象） | NASA | 無料・商用OK |
| AMeDAS（気象） | 気象庁 | 無料・無認証 |
| シームレス地質図 V2 | 産総研 | CC-BY |
| HydroBASINS Lvl 10 | WWF HydroSHEDS | CC-BY |
| 国土数値情報 A13 / W05 / W07 | 国土地理院 | 非商用（要確認） |
| 静岡県森林クラウド 1,102林班 | 静岡県 | オープンデータ |
| 林野庁 LiDAR（栃木・兵庫・高知） | 林野庁／G空間情報センター | 「らしんばん」MIERUNE×日本森林技術協会、商用OK |
| 森林生態系多様性基礎調査 | 林野庁 | 公開 |
| 自然環境保全基礎調査（植生図） | 環境省 | 公開 |
| 自然公園データ A10 | 国土数値情報 | CC-BY |
| J-クレジット 264件 | J-クレジット制度事務局 | 公開 |

---

## 6. 技術スタック

### フロントエンド
- 素の HTML / CSS / JavaScript（ビルドステップなし）
- 地図：Leaflet + Esri World Imagery タイル
- フォント：Noto Sans JP / M PLUS Rounded 1c / Josefin Sans

### バックエンド・データ処理
- Python：rasterio / pystac-client / numpy / pandas / Pillow / scipy
- 数値解析：ParFlow（C/Fortran/MPI、Hypre PFMG プリコンディショナ）

### インフラ
- AWS EC2（ap-northeast-1）
- Ubuntu 24.04 / nginx / Let's Encrypt
- ディスク 19GB EBS

---

## 7. リポジトリ構成

```
/var/www/morimieru/
├── README.md                          # 公開README
├── OVERVIEW.md                        # ←本ファイル
├── ROADMAP.md                         # 機能ロードマップ
├── SIMULATOR_ROADMAP.md               # 3D水循環シミュレータ計画
├── COMPETITORS.md                     # 競合マトリックス
├── CONTRIBUTING.md                    # コントリビューションガイド
├── NAGANO_MTG_AGENDA.md               # 長野さんMTGアジェンダ
├── NAGANO_MTG_BUSINESS_PLANS.md       # みちびき実証事業 5案
├── NAGANO_MTG_BUSINESS_PLANS.pdf      # 同 PDF版
├── NAGANO_MTG_BUSINESS_PLANS.docx     # 同 DOCX版
├── GEMINI3_IMAGE_PROMPTS.md           # サイトビジュアル用Geminiプロンプト
├── GEMINI3_IMAGE_PROMPTS_ARTICLES.md  # 記事用 17枚プロンプト
│
├── index.html                         # トップ
├── map.html                           # データマップ
├── watershed.html                     # 流域マップ
├── reports.html                       # レポート一覧
├── sitemap.xml / robots.txt
├── style.css / app.js / config.js
│
├── report/                            # 個別レポート（3本）
│   ├── himi-water.html                # 氷見市水資源涵養量
│   ├── himi-monitoring.html           # 氷見市時系列モニタリング
│   └── shizuoka-forests.html          # 静岡県森林公益機能
│
├── article/                           # 解説記事（5本）
│   ├── index.html                     # 記事一覧ハブ
│   ├── water-yield-guide.html         # 水源涵養量ガイド
│   ├── tnfd-forest-disclosure.html    # TNFD森林開示の実務
│   ├── jcredit-forest-map-2026.html   # J-クレジット264件 2026年版
│   ├── satellite-co2-tier2.html       # 衛星×CO2 IPCC Tier 2
│   ├── gx-ets-forest-credit-2026.html # GX-ETS 2026年版
│   └── img/                           # 記事画像21枚（Gemini生成17 + PoC実画像4）
│
├── data/                              # データセット
│   ├── candidates.js                  # 主要森林候補
│   ├── jcredit_projects.json          # J-クレジット264件
│   ├── reports.json                   # レポート一覧
│   ├── sentinel/                      # Sentinel-2 NDVI ラスタ
│   ├── co2/ / watersheds/ / rinpan/   # 算定結果
│   └── mountains/
│
├── scripts/                           # データ更新Pythonスクリプト群
│   ├── parse_jcredit.py
│   ├── fetch_sentinel2_himi.py
│   ├── estimate_water_himi.py
│   ├── estimate_co2_himi.py
│   ├── compute_rinpan_water.py
│   ├── compute_timeseries_diff.py
│   ├── extract_japan_watersheds.py
│   └── ... (約20本)
│
└── assets/                            # ロゴ・OG画像など
```

---

## 8. 公開URL構造

| URL | 内容 |
|---|---|
| `/` | トップ。4ステップフロー（会社情報→候補森林→衛星NDVI→意思表明書） |
| `/map.html` | 全国データマップ（市町村別森林公益機能） |
| `/watershed.html` | 流域マップ（HydroBASINS Lvl 10、3モード切替） |
| `/reports.html` | レポート一覧ハブ |
| `/article/` | 解説記事一覧 |
| `/article/<slug>.html` | 個別記事（計5本） |
| `/report/<slug>.html` | 個別レポート（計3本） |
| `/sitemap.xml` | サイトマップ（13 URL） |

---

## 9. 解説記事（5本）

| ID | タイトル | キーワードクラスタ |
|---|---|---|
| 1 | [水源涵養量とは？林野庁簡易評価法 Ver.1.0 ガイド](article/water-yield-guide.html) | 水源涵養量、簡易評価法 |
| 2 | [TNFD森林開示の実務ガイド](article/tnfd-forest-disclosure.html) | TNFD、自然関連財務情報開示、LEAP |
| 3 | [森林由来J-クレジット 全264件マップ 2026年版](article/jcredit-forest-map-2026.html) | J-クレジット 価格、購入、選び方 |
| 4 | [衛星×森林CO2吸収量 IPCC Tier 2 解説](article/satellite-co2-tier2.html) | IPCC AFOLU、Sentinel-2、NDVI |
| 5 | [GX-ETS と森林由来J-クレジット 2026年版](article/gx-ets-forest-credit-2026.html) | GX-ETS、排出量取引、カーボンプライシング |

各記事 4,000〜6,000字、Schema.org Article 構造化データ、FAQ、参考文献付き。

---

## 10. ステークホルダー

### コア
- **ryuji**：開発（フロントエンド・バックエンド・データ処理・記事執筆）
- **株式会社エムスクエア・ラボ**（加藤百合子代表）：パブリッシャー、衛星データノウハウ提供（農地ナビ＋）

### パートナー候補
- **株式会社モリアゲ**（長野麻子代表、元林野庁木材利用課長）：営業ネットワーク、制度知識、「一社一山」コンセプト
- **今井聡さん**：紹介者、共同推進者
- **春山慶彦さん**（YAMAP 社長）：流域図ライセンス・コラボ可能性

### 想定ユーザー（=支払い側）
✗ 森林所有者・森林組合・地方自治体（与信力・予算なし、長野さんの方針）
✓ 消費者、林材加工業者、林材流通業者、住宅メーカー、金融機関、水/森林を使う事業会社

### 競合（受託系・大手）
森かち（住林×NTT）、woodinfo、日立 FSDX、アジア航測、DeepForest Tech、精密林業計測（PreFore）、ヤマハ UMS、mapry、地圏環境テクノロジー（GETFLOWS）等

詳細：[COMPETITORS.md](COMPETITORS.md)

---

## 11. 進行中の重要プロジェクト

### 11.1 みちびき実証事業 共同応募（締切 2026-05-28）
- **代表応募者**：株式会社エムスクエア・ラボ
- **共同応募者**：株式会社モリアゲ
- **技術提供**：もりみえる
- **協力者**：森林組合・林材1次業者
- 5つの事業計画案を提示中 → [NAGANO_MTG_BUSINESS_PLANS.md](NAGANO_MTG_BUSINESS_PLANS.md)

### 11.2 3D水循環シミュレータ Phase 0 完了
- ParFlow 3.15.0 を現サーバでビルド・動作確認済
- Little Washita（米国OK、12日、CLM結合）：18秒で完走
- 氷見市（日本、6時間、SRTM実DEM）：5秒で完走
- 詳細：[SIMULATOR_ROADMAP.md](SIMULATOR_ROADMAP.md)

### 11.3 SEO 立ち上げ
- Google Analytics：過去28日でアクティブユーザー17名（立ち上げ初期）
- 解説記事5本投入、内部リンク強化、sitemap.xml 13URL
- Search Console 経由のクロール待ち（1〜4週間）

---

## 12. ロードマップ抜粋（短期）

| 優先度 | 項目 |
|---|---|
| ⭐⭐⭐ | みちびき応募書類最終化（5/28） |
| ⭐⭐⭐ | 林班 × 森林簿 × 計画図統合（静岡から開始） |
| ⭐⭐⭐ | 時系列差分による施業効果モニタリング |
| ⭐⭐ | ParFlow Phase 1（AMeDAS実気象 × 氷見1年シミュ） |
| ⭐⭐ | 林野庁 LiDAR 取り込み（栃木・兵庫・高知 20mメッシュ） |
| ⭐⭐ | 環境省 生物多様性レイヤー統合 |
| ⭐⭐ | Google Search Console 再クロール・記事流入測定 |
| ⭐ | YAMAP流域図ライセンス交渉 |
| ⭐ | オープンソース化（GitHub公開） |

詳細：[ROADMAP.md](ROADMAP.md)

---

## 13. メッセージング軸（広報用）

- ✅ **「精度競争じゃなく、検証可能性 × 普及可能性」**
- ✅ **「すべて無料の公開データから」**
- ✅ **「負動産じゃなく、価値ある森を引き受ける人をつなぐ」**（長野さん引用）
- ✅ **「林野庁の20年蓄積を統合した上で、新しい層を追加」**
- ✅ **「日本全国・常時計算済の森林インフラ」**

---

## 14. デプロイ

```bash
ssh ubuntu@mori-mieru.jp 'cd /var/www/morimieru && sudo git pull && sudo chown -R www-data:www-data .'
```

データ更新：

```bash
.venv/bin/python scripts/parse_jcredit.py        # J-credit 一覧の取り直し
.venv/bin/python scripts/fetch_sentinel2_himi.py # Sentinel-2 シーンの更新
```

---

## 15. 連絡先・関連リソース

- 公開URL：https://mori-mieru.jp/
- パブリッシャー：株式会社エムスクエア・ラボ（https://m2-labo.jp/）
- パートナー：株式会社モリアゲ（https://mori-age.jp/）

---

最終更新：2026-05-19。本ドキュメントはプロジェクトの全体像を1ファイルにまとめたもので、詳細は各ファイルへのリンクを参照してください。
