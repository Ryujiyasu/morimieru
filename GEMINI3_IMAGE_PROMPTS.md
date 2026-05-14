# Gemini 3 画像生成 指示書（もりみえる用）

## 使い方
- 各プロンプトは Gemini 3（image generation）にそのまま貼って実行できる形にしてあります
- 推奨アスペクト比は項目ごとに記載
- 生成された画像は `assets/` 配下に下記ファイル名で保存してください
- 全画像の共通トーン：**温かい・柔らかい・写実的だがほんの少しイラスト寄り・モリアゲのブランドカラー（深い森緑＋クリーム＋アクセント土色）と調和**

---

## 1. ヒーロー背景画像（最重要）

**保存先**: `assets/hero-forest.jpg`
**アスペクト比**: 16:9（横長）
**用途**: トップページ Hero セクションの背景

### プロンプト（英語版・推奨）
```
A serene aerial view of a Japanese mountain forest in late spring, photographed from a low-flying drone at golden hour. Mix of cedar (sugi) plantation rows curving along the contours and patches of deciduous broadleaf trees. Soft morning mist drifting between the ridges. Gentle warm light from the upper right, long soft shadows. Mostly forest greens (deep emerald to soft sage), with a cream-colored sky and subtle terracotta/earth tones in the exposed soil and tree trunks. Painterly photography style, slightly desaturated, very calm and contemplative mood. No people, no buildings, no text. Highly detailed but soft, like a high-end documentary shot.
```

### プロンプト（日本語版）
```
日本の山岳森林を低空ドローンから捉えた静謐な空撮。晩春の朝。等高線に沿って弧を描くスギ人工林の列と、点在する広葉樹のパッチ。尾根の間に流れる柔らかな朝霧。右上から差し込む暖かい光と長く柔らかい影。深いエメラルドから優しい青磁色までの森緑を主体に、クリーム色の空、露出した土壌や樹皮の控えめなテラコッタ・大地色をアクセントに。やや彩度を落とした絵画的な写真表現。瞑想的で穏やかな雰囲気。人物・建造物・文字なし。高精細だが柔らかい、高級ドキュメンタリーフォトの質感。
```

### ネガティブ要素（避けたいもの）
- 鮮やかすぎる色、青空ピーカン
- 都市・建物・人物・車・道路標識・電柱
- テキストやロゴ
- ファンタジー要素（光のオーラ、虹、フレア）
- 季節違い（紅葉や雪）— あくまで「これから育っていく春」

---

## 2. OG画像（SNSシェア・LINE等のリッチカード）

**保存先**: `assets/og-image.jpg`
**アスペクト比**: 1.91:1（1200 × 630 推奨）
**用途**: SNSシェア時のサムネ。文字は CSS で重ねるので、画像自体は背景のみ

### プロンプト
```
A textured paper background in cream color (#faf6ef), with a subtle abstract Japanese forest motif rendered in deep forest green (#2d5a3d) ink wash style. Suggest tree silhouettes — a few simple cedar trees on the lower left and right edges — but leave the center mostly clean and empty for text overlay. Very minimal, very calm, traditional washi paper texture, suitable as a hero background for a forestry sustainability platform. No actual text in the image.
```

---

## 3. 候補森林カードのデフォルトサムネ（任意・後回しでOK）

**保存先**: `assets/forest-thumbnail.jpg`
**アスペクト比**: 4:3
**用途**: 候補リストの各カードに添えるサムネ画像

### プロンプト
```
A close-up photograph of a Japanese cedar (sugi) and broadleaf mixed forest interior. Soft, diffused light filtering through the canopy. Moss on the ground. Tree trunks rising tall. Quiet, contemplative atmosphere. Photorealistic, slightly painterly, warm tones, no people. Color palette: forest greens, warm browns, and soft cream highlights.
```

---

## 4. 「衛星 → 森 → 会社」のコンセプトイラスト（任意）

**保存先**: `assets/concept-diagram.png`
**アスペクト比**: 4:3 or 16:9
**用途**: About セクションや Technology セクションの補助ビジュアル

### プロンプト
```
A minimalist, flat-style editorial illustration showing the connection between a satellite orbiting Earth, a Japanese forest landscape below with cedar trees, and a small company building in the distance. Drawn in the style of a Japanese magazine infographic — soft pastel palette (deep forest green, cream, warm terracotta), gentle hand-drawn quality with M PLUS Rounded 1c-like roundness, no harsh edges. Show data flowing from the satellite down to the forest as soft dotted lines, and from the forest to the building as a gentle warm arc representing CO2 absorption. No text. Calm, hopeful mood.
```

---

## 5. 仮証書の装飾用エンブレム（任意）

**保存先**: `assets/cert-emblem.svg`（SVG生成依頼でなければ PNG でも可）
**アスペクト比**: 1:1
**用途**: コミットメント証明書の装飾

### プロンプト
```
A circular emblem in the style of a traditional Japanese seal (hanko / inkan), but very modern and minimalist. The emblem shows a stylized cedar tree silhouette in the center, surrounded by a thin circular border with subtle radial lines suggesting sunlight. Color: deep forest green (#2d5a3d) on cream. Should feel official but warm, like a craftsman's signature, not a corporate logo. Flat design, no shading. Transparent background.
```

---

## 追加（2026-05-14）：レポート用ヘッダー画像 3 枚

各レポートのトップに敷くヘッダー背景画像。すべてアスペクト比 21:9（横長・パノラマ）、
解像度 2400 × 1029 程度。

### A. 水資源涵養レポート用

**保存先**: `assets/report-water-hero.jpg`

```
A serene Japanese mountain forest landscape with a clear stream winding through
cedar and broadleaf trees. Morning mist hovering between the ridges. Soft warm
light from the upper right. Dominant colors: deep forest greens, soft sage, cool
blue water tones reflecting the trees. Painterly photography style, slightly
desaturated, contemplative mood. No people or buildings. Panoramic 21:9 aspect
ratio for a report header banner. Very high resolution.
```

### B. CO₂ 吸収レポート用（氷見市周辺森林レポート）

**保存先**: `assets/report-co2-hero.jpg`

```
A wide panoramic view of a Japanese mountain forest in late summer, photographed
from a high vantage point at golden hour. Dense canopy of cedar (sugi) and
broadleaf trees stretching to the horizon. Soft warm light, very subtle haze
suggesting CO2 absorption. Mostly deep forest greens with warm amber highlights.
Documentary photography style, slightly painterly. Panoramic 21:9 ratio for a
report header banner. No people, no buildings, no text.
```

### C. 時系列差分（モニタリング）レポート用

**保存先**: `assets/report-monitoring-hero.jpg`

```
A panoramic Japanese forest landscape showing subtle seasonal variation: a few
patches of younger growth, mature canopy, and slightly different shades indicating
forest vigor over time. Photographed at the edge of golden hour, with a hint of
mist. Dominant colors: a layered palette of forest greens (younger lighter green,
mature deep green, mature dark cedar green). Slightly painterly editorial photo
style. Panoramic 21:9 ratio for a report header banner. No people, no buildings,
no text.
```

---

## 共通ガイドライン

### カラーパレット（生成画像に含めたい色）
- **メイン**：深い森緑 `#2d5a3d` / 中間森緑 `#5a8a3a` / 淡い緑 `#a7c498`
- **背景**：クリーム `#faf6ef` / 紙色 `#fffaf0`
- **アクセント**：土色テラコッタ `#c47a4a` / 暖かい茶 `#8c5a3a`
- **NGカラー**：原色青、原色赤、純黒、ネオン

### 雰囲気のキーワード
- ✅ 穏やか / 瞑想的 / 温かい / 高級ドキュメンタリー / 和の余白
- ✅ ほんのり絵画的、photorealistic but slightly painterly
- ✅ 朝霧、低彩度、柔らかい光
- ❌ 派手 / ファンタジー / 商業バナー風 / ストック写真感

### 参考スタイル
- 写真家：星野道夫、今森光彦、川田喜久治の森林カット
- 雑誌：『ソトコト』『Discover Japan』の森林特集のトーン
- イラストレーター：植田真、塩川いづみ（雑誌『nice things.』『暮しの手帖』系統）

---

## 生成後の作業

1. 画像を `/home/ubuntu/agrimap/morimieru/assets/` に保存
2. `index.html` の hero セクション CSS の `.hero-bg` に画像URLを追加：
   ```css
   .hero-bg {
     background-image: url('assets/hero-forest.jpg'),
       radial-gradient(...) /* 既存のグラデーション */;
     background-size: cover;
     background-position: center;
   }
   ```
3. OG画像は `<head>` の `<meta property="og:image" content="...">` に登録
4. 生成画像にチラ見せ的に文字（©, ロゴ）を入れたくなったら CSS で別途オーバーレイ
