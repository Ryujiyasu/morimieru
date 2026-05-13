// Featured forests for もりみえる
// These are the curated locations shown alongside real J-credit projects.
// CO2 absorption numbers reflect typical Japanese planted forest carbon
// stocks (5-15 t-CO2/ha/year for mature sugi/hinoki plantations).

window.MORIMIERU_CANDIDATES = {
  // Region-keyed list (Step 2 filters by user's region selection)
  chubu: [
    {
      id: 'himi-asahi',
      name: '朝日山系の森',
      pref: '富山県 氷見市',
      lat: 36.857,
      lon: 136.987,
      area_ha: 182,
      species: 'スギ・ヒノキ 73% / 広葉樹 27%',
      mean_height: '18.4 m',
      stand_age: '55年生',
      co2_estimate: 1420,
      co2_low: 1180,
      co2_high: 1690,
      credit_man_yen: 1705,
      owner: '森林組合・私有林',
      deepdive: true,
      tagline: '林野庁令和7年度委託事業の対象地',
      lidar: 'R6 高密度実施',
      ndvi_path: [0.62, 0.58, 0.71, 0.74, 0.65, 0.72, 0.78, 0.81, 0.76, 0.68, 0.71, 0.79, 0.82, 0.77]
    },
    {
      id: 'midori-watarase',
      name: '渡良瀬源流の森',
      pref: '群馬県 みどり市',
      lat: 36.520,
      lon: 139.288,
      area_ha: 96,
      species: 'スギ 55% / 広葉樹 45%',
      mean_height: '16.1 m',
      stand_age: '48年生',
      co2_estimate: 720,
      co2_low: 580,
      co2_high: 860,
      credit_man_yen: 864,
      owner: '東京農工大学演習林・市有林',
      tagline: '令和7年度委託事業の対岸検証地',
      lidar: 'R6 高密度実施'
    },
    {
      id: 'minamishinano-akiyama',
      name: '秋山郷の広葉樹林',
      pref: '長野県 栄村',
      lat: 36.948,
      lon: 138.602,
      area_ha: 245,
      species: 'ブナ・ミズナラ 88% / カラマツ 12%',
      mean_height: '22.7 m',
      stand_age: '75年生（天然林）',
      co2_estimate: 1960,
      co2_low: 1500,
      co2_high: 2410,
      credit_man_yen: 2352,
      owner: '集落共有林（区有林）',
      tagline: '世界的にも貴重なブナ天然林'
    },
    {
      id: 'okuetsu-katsuyama',
      name: '奥越前の混交林',
      pref: '福井県 勝山市',
      lat: 36.060,
      lon: 136.501,
      area_ha: 134,
      species: 'スギ 40% / 広葉樹 60%',
      mean_height: '17.8 m',
      stand_age: '60年生',
      co2_estimate: 1010,
      co2_low: 800,
      co2_high: 1230,
      credit_man_yen: 1212,
      owner: '森林組合・私有林',
      tagline: '小規模分散所有・中間支援組織が窓口'
    }
  ],
  tohoku: [
    {
      id: 'akita-mori',
      name: '森吉山系の天然林',
      pref: '秋田県 北秋田市',
      lat: 39.978,
      lon: 140.541,
      area_ha: 312,
      species: 'ブナ 92% / その他 8%',
      mean_height: '24.5 m',
      stand_age: '90年生',
      co2_estimate: 2230,
      co2_low: 1810,
      co2_high: 2680,
      credit_man_yen: 2676
    },
    {
      id: 'iwate-kunimi',
      name: '国見山の杉林',
      pref: '岩手県 一関市',
      lat: 38.943,
      lon: 141.105,
      area_ha: 89,
      species: 'スギ 100%',
      mean_height: '19.8 m',
      stand_age: '52年生',
      co2_estimate: 645,
      co2_low: 510,
      co2_high: 790,
      credit_man_yen: 774
    }
  ],
  kanto: [
    {
      id: 'tochigi-kofu',
      name: '古峰ヶ原の混交林',
      pref: '栃木県 鹿沼市',
      lat: 36.677,
      lon: 139.575,
      area_ha: 158,
      species: 'スギ・ヒノキ 65% / 広葉樹 35%',
      mean_height: '17.2 m',
      stand_age: '58年生',
      co2_estimate: 1135,
      co2_low: 920,
      co2_high: 1370,
      credit_man_yen: 1362,
      tagline: '林野庁オープンデータ整備済み県'
    }
  ],
  kansai: [
    {
      id: 'wakayama-koya',
      name: '高野山参道沿いの森',
      pref: '和歌山県 高野町',
      lat: 34.215,
      lon: 135.583,
      area_ha: 142,
      species: 'スギ・ヒノキ 80% / 広葉樹 20%',
      mean_height: '20.3 m',
      stand_age: '70年生',
      co2_estimate: 1280,
      co2_low: 1040,
      co2_high: 1540,
      credit_man_yen: 1536
    }
  ],
  chugoku: [
    {
      id: 'okayama-yataka',
      name: '弥高山の森',
      pref: '岡山県 高梁市',
      lat: 34.846,
      lon: 133.510,
      area_ha: 108,
      species: 'スギ・ヒノキ 70% / 広葉樹 30%',
      mean_height: '17.5 m',
      stand_age: '55年生',
      co2_estimate: 815,
      co2_low: 660,
      co2_high: 980,
      credit_man_yen: 978
    }
  ],
  shikoku: [
    {
      id: 'kochi-shimanto',
      name: '四万十源流の森',
      pref: '高知県 津野町',
      lat: 33.490,
      lon: 132.948,
      area_ha: 195,
      species: '広葉樹 70% / スギ 30%',
      mean_height: '21.0 m',
      stand_age: '65年生',
      co2_estimate: 1430,
      co2_low: 1180,
      co2_high: 1710,
      credit_man_yen: 1716,
      tagline: '林野庁オープンデータ整備済み県'
    }
  ],
  kyushu: [
    {
      id: 'kumamoto-oguni',
      name: '小国杉の森',
      pref: '熊本県 小国町',
      lat: 33.114,
      lon: 131.085,
      area_ha: 165,
      species: '小国杉 95% / 広葉樹 5%',
      mean_height: '22.8 m',
      stand_age: '78年生',
      co2_estimate: 1320,
      co2_low: 1080,
      co2_high: 1580,
      credit_man_yen: 1584,
      tagline: '銘木の里・小国杉のブランド林'
    }
  ],
  hokkaido: [
    {
      id: 'hokkaido-shiretoko',
      name: '知床麓のトドマツ林',
      pref: '北海道 斜里町',
      lat: 44.080,
      lon: 144.945,
      area_ha: 420,
      species: 'トドマツ・エゾマツ 85% / 広葉樹 15%',
      mean_height: '19.5 m',
      stand_age: '60年生',
      co2_estimate: 2520,
      co2_low: 2080,
      co2_high: 2980,
      credit_man_yen: 3024
    }
  ]
};

// Region label map
window.MORIMIERU_REGION_LABELS = {
  all: '全国',
  hokkaido: '北海道',
  tohoku: '東北',
  kanto: '関東',
  chubu: '中部・北陸',
  kansai: '関西',
  chugoku: '中国',
  shikoku: '四国',
  kyushu: '九州・沖縄'
};

// Get candidates by region (or all)
window.getMorimieruCandidates = function(region) {
  const all = window.MORIMIERU_CANDIDATES;
  if (region === 'all' || !region) {
    return Object.values(all).flat();
  }
  return all[region] || [];
};
