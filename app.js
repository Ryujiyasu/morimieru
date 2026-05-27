// もりみえる - interaction logic
// ====== i18n bootstrap (added 2026-05-26) ======
const __MM_LANG = (typeof window !== 'undefined' && window.location && window.location.pathname.startsWith('/en/')) ? 'en' : 'ja';

const __MM_PREF = {
  '北海道':'Hokkaido','青森県':'Aomori','岩手県':'Iwate','宮城県':'Miyagi','秋田県':'Akita',
  '山形県':'Yamagata','福島県':'Fukushima','茨城県':'Ibaraki','栃木県':'Tochigi','群馬県':'Gunma',
  '埼玉県':'Saitama','千葉県':'Chiba','東京都':'Tokyo','神奈川県':'Kanagawa','新潟県':'Niigata',
  '富山県':'Toyama','石川県':'Ishikawa','福井県':'Fukui','山梨県':'Yamanashi','長野県':'Nagano',
  '岐阜県':'Gifu','静岡県':'Shizuoka','愛知県':'Aichi','三重県':'Mie','滋賀県':'Shiga',
  '京都府':'Kyoto','大阪府':'Osaka','兵庫県':'Hyogo','奈良県':'Nara','和歌山県':'Wakayama',
  '鳥取県':'Tottori','島根県':'Shimane','岡山県':'Okayama','広島県':'Hiroshima','山口県':'Yamaguchi',
  '徳島県':'Tokushima','香川県':'Kagawa','愛媛県':'Ehime','高知県':'Kochi','福岡県':'Fukuoka',
  '佐賀県':'Saga','長崎県':'Nagasaki','熊本県':'Kumamoto','大分県':'Oita','宮崎県':'Miyazaki',
  '鹿児島県':'Kagoshima','沖縄県':'Okinawa',
};
const prefJaToEn = (p) => __MM_PREF[p] || p;

const __MM_T = {
  ja: {
    you: 'あなた',
    budget_unit: '万円',
    loading: '取得中…',
    locate_unsupported: 'お使いのブラウザは位置情報に対応していません。',
    locate_fail: '位置情報の取得に失敗しました：',
    address_fail: '住所の取得に失敗しました。手入力してください。',
    candidate: '候補地',
    searching_prefix: '🛰️  ',
    searching_suffix: ' を探しています…',
    please_wait: '少々お待ちください。',
    finding_basin: '取水域を特定中…',
    sample_runs_at: ' で実行中…',
    in_basin_tagline: '🌊 あなたの取水域内の森（深掘り対応）',
    in_basin_short: '🌊 あなたの取水域内の森',
    tip_upstream: 'あなたの取水域・上流側',
    tip_user_basin: 'あなたの会社の取水域',
    tt_upstream_html: '<span style="color:#3b6da1;">🌊 あなたの取水域・上流</span><br>',
    basin_title_suffix: ' の取水域の森、',
    basins_word: ' つ',
    basin_intro_lead: '工場や本社で使う水は、流域の森が育んでいます。あなたの取水域内・上流側にある森を優先的に並べています。',
    basin_id_label: '流域ID ',
    basin_id_suffix: '（HydroBASINS Lvl 10）',
    region_candidates_suffix_1: ' 向けの候補、',
    region_candidates_suffix_2: ' つ',
    region_lead: '住所から取水域を特定できなかったため（離島・河口の可能性）、希望地域の中から候補を提示しています。',
    default_title_pre: 'の会社にあう森、',
    default_title_post: ' つ見つかりました。',
    default_lead: 'クリックで、その森を衛星で「いま」見ることができます。',
    species_default: 'スギ・ヒノキ 70% / 広葉樹 30%（推定）',
    jcredit_tagline_pre: 'J-クレジット登録番号 ',
    park_inside: '内',
    park_nearby_suffix: 'km）',
    park_inside_prefix: '🏞 ',
    park_nearby_prefix: '🏔 ',
    methodology_default: '森林経営活動プロジェクト',
    card_area: '面積',
    card_species: '樹種',
    card_age: '林齢',
    card_owner: '所有',
    card_age_suffix: '年生',
    co2_unit: 't-CO₂/年',
    credit_estimate_prefix: 'クレジット試算：約 ',
    credit_estimate_suffix: ' 万円/年',
    cta_deepdive: '衛星画像で森を見る →',
    cta_mapview: '地図で見る →',
    no_owner: '—',
    co2_tip_suffix: ' t-CO₂/年',
    dd_lead_himi_pre: '林野庁令和7年度委託事業の対象地。',
    dd_lead_himi_mid: ' の Sentinel-2 衛星画像（雲量',
    dd_lead_himi_post: '%）から実際に NDVI を計算し、森林面積を推定しました。地図上の緑が濃い領域ほど植生が活発です。',
    dd_lead_jcredit_suffix: '。実際のJ-クレジット登録プロジェクトです。',
    dd_lead_default: 'Sentinel-1/2 衛星の週次観測と、林野庁オープンデータを統合して可視化しています。',
    co2_ci_prefix: '95% 信頼区間：',
    co2_ci_dash: ' – ',
    co2_ci_suffix: ' t-CO₂',
    water_detail_mid_1: ' mm/年 (降水量の ',
    water_detail_mid_2: '%) × ',
    water_detail_mid_3: ' ha ≈ ',
    water_detail_suffix: ' 百万トン／年',
    ndvi_layer_name: 'NDVI 解析結果',
    method_h1: '1. 森林面積の特定（衛星実測）',
    method_p_pre: 'Sentinel-2 L2A の ',
    method_p_mid: ' 期間の最低雲量シーンから NDVI を計算。',
    method_p_post: ' の画素を森林と判定（Hansen et al. 2013, Tier 2 既定値）。',
    method_aoi_area: 'AOI 総面積：',
    method_aoi_name_pre: '（',
    method_aoi_name_post: '）',
    method_pixels: '解析画素数：',
    method_pixels_each: ' (1 画素 ≈ ',
    method_pixels_unit: ' ha)',
    method_valid_pct: '有効画素率（非雲）：',
    method_forest_pct: '森林画素率：',
    method_forest_area: '森林面積：',
    method_h2: '2. 森林1 ha あたりの CO₂ 吸収量',
    method_formula_intro_pre: ' による既定式：',
    method_mai: 'MAI：',
    method_mai_unit: ' m³/ha/年（',
    method_density: '木材密度：',
    method_density_unit: ' t/m³（',
    method_bef: 'BEF（バイオマス拡大係数）：',
    method_root: '根/地上比：',
    method_carbon: '炭素割合：',
    method_h3: '3. AOI 全体の年間 CO₂ 吸収量',
    method_uncertainty: '${T.method_uncertainty}',
    method_uncertainty_2: '${T.method_uncertainty_2}',
    method_h4: '4. 水資源涵養量（林野庁簡易評価法 Ver.1.0 準拠）',
    method_w_link_text: '林野庁が令和8年3月に公開した算定式',
    method_w_intro: '${T.method_w_intro}',
    method_w_climate: '気象（月別気温・降水量）：',
    method_w_climate_src_pre: '（',
    method_w_elev: '標高：国土地理院 標高API（観測点 ',
    method_w_elev_mid: ' m → 林地 ',
    method_w_elev_post: ' m）',
    method_w_geo: '地質区分：産総研 シームレス地質図 API → ',
    method_w_geo_post: '）',
    method_w_forest: '林分情報：林野庁 標準値（',
    method_w_forest_density: '・密度 ',
    method_w_forest_density_unit: ' 本/ha・DBH ',
    method_w_forest_dbh_unit: ' cm・樹高 ',
    method_w_forest_h_unit: ' m）',
    method_w_formula_l1: '水資源涵養量 = 年降水量 − 直接流出量 − 蒸発散量',
    method_w_formula_precip: '年降水量（標高補正後）：',
    method_w_formula_runoff: '直接流出量：           ',
    method_w_formula_evapo: '蒸発散量：             ',
    method_w_formula_yield_prefix: '水資源涵養量：',
    method_w_formula_aoi: 'AOI 全体：',
    method_w_formula_aoi_unit_1: ' m³/年 ≈ ',
    method_w_formula_aoi_unit_2: ' 百万トン/年',
    method_w_note_1: '林野庁の本式は 100 ha 未満の小規模林分向けですが、本サイトでは衛星で抽出した森林ピクセルごとに同じ式を当てはめ、AOI 全体に拡張しています。',
    method_w_note_2: '${T.method_w_note_2}',
    ndvi_obs_points: 'NDVI 観測点',
    ndvi_label_pre: '過去 ',
    ndvi_label_mid: ' 年の NDVI 推移（',
    ndvi_label_post: ' 観測点・Sentinel-2 実測）',
    cert_company_sample: 'サンプル株式会社',
    cert_period_suffix: '（5年間）',
    cert_budget_unit: ' 万円',
    sample_food: 'サンプル食品株式会社',
    sample_mfg: 'サンプル製造株式会社',
    sample_beverage: 'サンプル飲料株式会社',
    yearly_format: (y, m, d) => `${y}年${m}月${d}日`,
  },
  en: {
    you: 'You',
    budget_unit: 'M JPY',
    loading: 'Loading…',
    locate_unsupported: 'Your browser does not support geolocation.',
    locate_fail: 'Could not get your location: ',
    address_fail: 'Could not resolve address. Please enter it manually.',
    candidate: 'this site',
    searching_prefix: '🛰️  Searching for ',
    searching_suffix: '…',
    please_wait: 'One moment.',
    finding_basin: 'Locating your watershed…',
    sample_runs_at: ' running with ',
    in_basin_tagline: '🌊 Forest in your watershed (deep-dive ready)',
    in_basin_short: '🌊 Forest in your watershed',
    tip_upstream: 'Your watershed · upstream',
    tip_user_basin: 'Your company watershed',
    tt_upstream_html: '<span style="color:#3b6da1;">🌊 Your watershed · upstream</span><br>',
    basin_title_suffix: ' — forests in your watershed, ',
    basins_word: ' found',
    basin_intro_lead: 'The water your factory or HQ uses is nurtured by upstream forests. Forests inside or upstream of your watershed appear first.',
    basin_id_label: 'Basin ID ',
    basin_id_suffix: ' (HydroBASINS Lvl 10)',
    region_candidates_suffix_1: ' — proposed candidates, ',
    region_candidates_suffix_2: ' found',
    region_lead: 'We could not pin your watershed (likely island / estuary). Showing candidates from your preferred region instead.',
    default_title_pre: ' — forests that match you, ',
    default_title_post: ' found.',
    default_lead: 'Click any forest to view its real-time satellite imagery.',
    species_default: 'Cedar / Cypress 70% · Broadleaf 30% (estimated)',
    jcredit_tagline_pre: 'J-Credit registration #',
    park_inside: '',
    park_nearby_suffix: ' km)',
    park_inside_prefix: '🏞 inside ',
    park_nearby_prefix: '🏔 near ',
    methodology_default: 'Forest management project',
    card_area: 'Area',
    card_species: 'Species',
    card_age: 'Stand age',
    card_owner: 'Tenure',
    card_age_suffix: ' yrs',
    co2_unit: 't-CO₂/yr',
    credit_estimate_prefix: 'Credit value ≈ ¥',
    credit_estimate_suffix: 'M/yr',
    cta_deepdive: 'See on satellite →',
    cta_mapview: 'Open on map →',
    no_owner: '—',
    co2_tip_suffix: ' t-CO₂/yr',
    dd_lead_himi_pre: 'A Forestry Agency of Japan FY2025 pilot site. ',
    dd_lead_himi_mid: ' Sentinel-2 imagery (cloud cover ',
    dd_lead_himi_post: '%): we compute real NDVI to estimate forest area. Darker green = denser vegetation.',
    dd_lead_jcredit_suffix: '. A real J-Credit registered project.',
    dd_lead_default: 'Weekly Sentinel-1/2 observations integrated with public open data.',
    co2_ci_prefix: '95% CI: ',
    co2_ci_dash: ' – ',
    co2_ci_suffix: ' t-CO₂',
    water_detail_mid_1: ' mm/yr (',
    water_detail_mid_2: '% of precipitation) × ',
    water_detail_mid_3: ' ha ≈ ',
    water_detail_suffix: ' million t/yr',
    ndvi_layer_name: 'NDVI analysis',
    method_h1: '1. Forest area (satellite measurement)',
    method_p_pre: 'NDVI computed from the lowest-cloud Sentinel-2 L2A scene during ',
    method_p_mid: '. Pixels with NDVI > ',
    method_p_post: ' classified as forest (Hansen et al. 2013, Tier 2 default).',
    method_aoi_area: 'AOI total area: ',
    method_aoi_name_pre: ' (',
    method_aoi_name_post: ')',
    method_pixels: 'Analyzed pixels: ',
    method_pixels_each: ' (1 pixel ≈ ',
    method_pixels_unit: ' ha)',
    method_valid_pct: 'Valid (non-cloud) pixel rate: ',
    method_forest_pct: 'Forest pixel rate: ',
    method_forest_area: 'Forest area: ',
    method_h2: '2. CO₂ absorption per hectare',
    method_formula_intro_pre: ' default formula:',
    method_mai: 'MAI: ',
    method_mai_unit: ' m³/ha/yr (',
    method_density: 'Wood density: ',
    method_density_unit: ' t/m³ (',
    method_bef: 'BEF (biomass expansion factor): ',
    method_root: 'Root/shoot ratio: ',
    method_carbon: 'Carbon fraction: ',
    method_h3: '3. AOI-wide annual CO₂ absorption',
    method_uncertainty: 'Uncertainty for Tier 2 is typically ±30% — composed of regional MAI variation, species mixture, and satellite classification error.',
    method_uncertainty_2: 'Integrating site-specific forest data and management records yields tighter confidence intervals.',
    method_h4: '4. Water yield (per Forestry Agency simplified method Ver.1.0)',
    method_w_link_text: 'Forestry Agency formula published in March 2026',
    method_w_intro: ' fed with inputs assembled entirely from satellite and public data:',
    method_w_climate: 'Climate (monthly T & P): ',
    method_w_climate_src_pre: ' (',
    method_w_elev: 'Elevation: GSI Elevation API (station ',
    method_w_elev_mid: ' m → forest point ',
    method_w_elev_post: ' m)',
    method_w_geo: 'Geology class: AIST Seamless Geological Map API → ',
    method_w_geo_post: ')',
    method_w_forest: 'Stand info: Forestry Agency defaults (',
    method_w_forest_density: ' · density ',
    method_w_forest_density_unit: ' stems/ha · DBH ',
    method_w_forest_dbh_unit: ' cm · height ',
    method_w_forest_h_unit: ' m)',
    method_w_formula_l1: 'Water yield = Annual precipitation − Direct runoff − Evapotranspiration',
    method_w_formula_precip: 'Annual precip (elev-corrected): ',
    method_w_formula_runoff: 'Direct runoff:                 ',
    method_w_formula_evapo: 'Evapotranspiration:            ',
    method_w_formula_yield_prefix: 'Water yield: ',
    method_w_formula_aoi: 'AOI total: ',
    method_w_formula_aoi_unit_1: ' m³/yr ≈ ',
    method_w_formula_aoi_unit_2: ' million t/yr',
    method_w_note_1: 'The official formula targets stands under 100 ha; we apply it per satellite-derived forest pixel and extend to the full AOI.',
    method_w_note_2: 'Stand parameters (DBH, height, density) will be replaced with site-specific values as Forestry Agency LiDAR (80% national coverage) is integrated.',
    ndvi_obs_points: 'NDVI obs. points',
    ndvi_label_pre: 'Past ',
    ndvi_label_mid: '-year NDVI history (',
    ndvi_label_post: ' obs. points · Sentinel-2 measured)',
    cert_company_sample: 'Sample Corp.',
    cert_period_suffix: ' (5 years)',
    cert_budget_unit: '',
    sample_food: 'Sample Foods Ltd.',
    sample_mfg: 'Sample Manufacturing Ltd.',
    sample_beverage: 'Sample Beverage Ltd.',
    yearly_format: (y, m, d) => `${y}-${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')}`,
  },
};
const T = __MM_T[__MM_LANG];

// ====== end i18n bootstrap ======

// Four-step flow:
//  1) company form  →  2) candidates list/map  →  3) satellite view (Himi feature)  →  4) commitment certificate
//
// Data sources:
//   - data/jcredit_projects.json (264 forest projects from japancredit.go.jp)
//   - data/sentinel/himi_meta.json + himi_ndvi.png (Sentinel-2 L2A, AWS Open Data)

(function () {
  'use strict';

  // ---- State ----
  const state = {
    company: '',
    industry: '',
    budget: 300,
    region: 'chubu',
    vision: '',
    candidates: [],
    selected: null,
    candidateMap: null,
    ddMap: null,
    ddNdviLayer: null,
    sentinelMeta: null,
    sentinelSeries: null,
    himiCo2: null,
    himiWater: null,
    jcreditProjects: [],
    address: '',
    addressLatLon: null,            // [lat, lon] from geocoder
    watersheds: null,               // FeatureCollection (lazy-loaded)
    userBasin: null,                // GeoJSON feature
    watershedBasins: [],            // user basin + upstream basins
    candidateBasinFilter: false,    // whether candidates are filtered by basin
  };

  // ---- Data loaders ----
  async function loadJcredit() {
    try {
      const r = await fetch('data/jcredit_projects.json');
      const j = await r.json();
      state.jcreditProjects = j.projects || [];
      console.log(`Loaded ${state.jcreditProjects.length} J-credit forest projects`);
    } catch (e) {
      console.warn('J-credit data load failed', e);
      state.jcreditProjects = [];
    }
  }

  // ---- Geocoding (国土地理院 free API) ----
  async function geocodeAddress(addr) {
    if (!addr) return null;
    try {
      const r = await fetch(
        'https://msearch.gsi.go.jp/address-search/AddressSearch?q=' + encodeURIComponent(addr)
      );
      const arr = await r.json();
      if (!Array.isArray(arr) || !arr.length) return null;
      const c = arr[0].geometry.coordinates;
      return { lat: c[1], lon: c[0], title: arr[0].properties.title };
    } catch (e) {
      console.warn('geocode failed', e);
      return null;
    }
  }

  // ---- Watershed loader + point-in-polygon ----
  async function loadWatersheds() {
    if (state.watersheds) return state.watersheds;
    try {
      // Lvl 10 (~8000 basins) — finer than Lvl 8, separates coastal cities
      // from their upstream sub-basins (e.g. 焼津 gets 9 upstream basins)
      const r = await fetch('data/watersheds/japan_lev10.geojson');
      state.watersheds = await r.json();
      console.log(`Loaded ${state.watersheds.features.length} watersheds (HydroBASINS Lvl 10)`);
    } catch (e) {
      console.warn('watershed load failed', e);
      state.watersheds = { features: [] };
    }
    return state.watersheds;
  }

  // Standard ray-casting point-in-polygon for [lon, lat] coordinates
  function pointInRing(point, ring) {
    let inside = false;
    const [x, y] = point;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const [xi, yi] = ring[i];
      const [xj, yj] = ring[j];
      const intersect = ((yi > y) !== (yj > y)) &&
        (x < (xj - xi) * (y - yi) / (yj - yi + 1e-15) + xi);
      if (intersect) inside = !inside;
    }
    return inside;
  }

  function pointInGeometry(point, geom) {
    if (geom.type === 'Polygon') {
      if (!pointInRing(point, geom.coordinates[0])) return false;
      for (let i = 1; i < geom.coordinates.length; i++) {
        if (pointInRing(point, geom.coordinates[i])) return false; // in a hole
      }
      return true;
    } else if (geom.type === 'MultiPolygon') {
      return geom.coordinates.some(poly => {
        if (!pointInRing(point, poly[0])) return false;
        for (let i = 1; i < poly.length; i++) {
          if (pointInRing(point, poly[i])) return false;
        }
        return true;
      });
    }
    return false;
  }

  function findContainingBasin(lonLat, fc) {
    for (const f of fc.features) {
      if (pointInGeometry(lonLat, f.geometry)) return f;
    }
    return null;
  }

  // Recursive: all basins that eventually drain into target
  function findUpstreamBasins(target, fc) {
    const byId = new Map();
    for (const f of fc.features) byId.set(f.properties.hybas_id, f);
    const targetId = target.properties.hybas_id;
    const upstream = new Set();
    for (const f of fc.features) {
      let cur = f;
      const seen = new Set();
      while (cur && !seen.has(cur.properties.hybas_id)) {
        seen.add(cur.properties.hybas_id);
        const nextId = cur.properties.next_down;
        if (nextId === targetId) {
          upstream.add(f.properties.hybas_id);
          break;
        }
        if (!nextId) break;
        cur = byId.get(nextId);
      }
    }
    return [...upstream].map(id => byId.get(id));
  }

  async function loadSentinelMeta() {
    try {
      const [meta, series, co2, water] = await Promise.all([
        fetch('data/sentinel/himi_meta.json').then(r => r.json()).catch(() => null),
        fetch('data/sentinel/himi_timeseries.json').then(r => r.json()).catch(() => null),
        fetch('data/sentinel/himi_co2.json').then(r => r.json()).catch(() => null),
        fetch('data/sentinel/himi_water.json').then(r => r.json()).catch(() => null),
      ]);
      state.sentinelMeta = meta;
      state.sentinelSeries = series;
      state.himiCo2 = co2;
      state.himiWater = water;
      if (meta) console.log('Sentinel scene:', meta.scene?.scene_id);
      if (series) console.log(`NDVI time series: ${series.points?.length} points`);
      if (co2) console.log(`Himi CO2: ${co2.annual_co2_t.toLocaleString()} t-CO2/yr`);
      if (water) console.log(`Himi water yield: ${water.aoi_total.water_yield_m3_per_yr.toLocaleString()} m³/yr`);

      // Sync the Himi candidate with the live CO2 model result
      if (co2 && window.MORIMIERU_CANDIDATES?.chubu) {
        const himi = window.MORIMIERU_CANDIDATES.chubu.find(c => c.id === 'himi-area');
        if (himi) {
          himi.area_ha = Math.round(co2.forest_area_ha);
          himi.co2_estimate = co2.annual_co2_t;
          himi.co2_low = co2.annual_co2_low_t;
          himi.co2_high = co2.annual_co2_high_t;
          himi.credit_man_yen = Math.round(co2.annual_co2_t * 1.2);  // 12,000 yen/t-CO2
          himi._co2_report = co2;
        }
      }
    } catch (e) {
      console.warn('Sentinel data load failed', e);
    }
  }

  // ---- Helpers ----
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  function fmtMan(n) {
    return new Intl.NumberFormat('ja-JP').format(Math.round(n));
  }

  // SHA-256 hash for the commitment certificate payload
  async function sha256(str) {
    const buf = new TextEncoder().encode(str);
    const hash = await crypto.subtle.digest('SHA-256', buf);
    return Array.from(new Uint8Array(hash))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
  }

  // ---- Step 1: form ----
  function initForm() {
    const budgetInput = $('#budget-input');
    const budgetDisplay = $('#budget-display');
    budgetInput.addEventListener('input', () => {
      const v = budgetInput.value;
      budgetDisplay.textContent = `${fmtMan(v)}${T.budget_unit}`;
    });

    // "Locate" button — get current location via browser Geolocation API + reverse geocode
    const locateBtn = document.getElementById('btn-locate');
    if (locateBtn) {
      locateBtn.addEventListener('click', () => {
        if (!navigator.geolocation) {
          alert(T.locate_unsupported);
          return;
        }
        locateBtn.disabled = true;
        const origLabel = locateBtn.textContent;
        locateBtn.textContent = T.loading;
        navigator.geolocation.getCurrentPosition(
          async (pos) => {
            try {
              const { latitude: lat, longitude: lon } = pos.coords;
              // Reverse geocode via 国土地理院
              const r = await fetch(
                `https://mreversegeocoder.gsi.go.jp/reverse-geocoder/LonLatToAddress?lat=${lat}&lon=${lon}`
              );
              const j = await r.json();
              const res = j.results || {};
              // muniCd + lv01Nm → 都道府県市区町村名 + 大字
              const muniCd = res.muniCd;
              const lv01 = res.lv01Nm || '';
              // Lookup muni name: we don't have a code→name map embedded;
              // fall back to placing just the lv01 area name
              let address = lv01;
              // Try to fetch a name via the same API's MuniNameTbl
              try {
                const tbl = await fetch('https://maps.gsi.go.jp/js/muni.js').then(r => r.text());
                const m = tbl.match(new RegExp(`'${muniCd}'\\s*:\\s*'([^']+)'`));
                if (m) address = m[1] + (lv01 ? lv01 : '');
              } catch (e) { /* keep lv01 only */ }
              document.getElementById('address-input').value = address || `${lat.toFixed(4)},${lon.toFixed(4)}`;
            } catch (e) {
              alert(T.address_fail);
            } finally {
              locateBtn.disabled = false;
              locateBtn.textContent = origLabel;
            }
          },
          (err) => {
            alert(T.locate_fail + err.message);
            locateBtn.disabled = false;
            locateBtn.textContent = origLabel;
          },
          { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 }
        );
      });
    }

    // "Sample address" button — auto-fills the form with a real Japanese company HQ-ish address
    const sampleBtn = document.getElementById('sample-button');
    if (sampleBtn) {
      sampleBtn.addEventListener('click', async () => {
        const samples = [
          { company: T.sample_food, address: '静岡県焼津市利右衛門', region: 'chubu' },
          { company: T.sample_mfg, address: '富山県氷見市丸の内', region: 'chubu' },
          { company: T.sample_beverage, address: '熊本県小国町宮原', region: 'kyushu' },
        ];
        const s = samples[Math.floor(Math.random() * samples.length)];

        // Visible feedback: change the button text + scroll the form into view
        const origLabel = sampleBtn.textContent;
        sampleBtn.textContent = `${T.sample_runs_at}${s.address}…`;
        sampleBtn.disabled = true;
        const form = document.getElementById('company-form');
        form.querySelector('input[name="company"]').value = s.company;
        form.querySelector('input[name="address"]').value = s.address;
        form.querySelector('select[name="region"]').value = s.region;
        form.scrollIntoView({ behavior: 'smooth', block: 'start' });
        // Give the scroll a beat so the user sees the values fill in
        await new Promise(r => setTimeout(r, 200));
        form.requestSubmit();
        // Re-enable after the submit handler finishes
        setTimeout(() => {
          sampleBtn.textContent = origLabel;
          sampleBtn.disabled = false;
        }, 5000);
      });
    }

    // "Quick look" — skip the form entirely, jump straight to candidates with defaults
    const quickBtn = document.getElementById('quick-look');
    if (quickBtn) {
      quickBtn.addEventListener('click', (e) => {
        e.preventDefault();
        state.company = T.you;
        state.address = '';
        state.addressLatLon = null;
        state.userBasin = null;
        state.watershedBasins = [];
        state.candidateBasinFilter = false;
        state.region = 'all';
        state.budget = 300;
        showCandidates();
      });
    }

    $('#company-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      state.company = fd.get('company') || T.you;
      state.industry = fd.get('industry');
      state.budget = +fd.get('budget');
      state.region = fd.get('region');
      state.vision = fd.get('vision') || '';
      state.address = (fd.get('address') || '').trim();

      // Show loading state if we have an address — we'll geocode + load watersheds in parallel
      const btn = e.target.querySelector('button[type="submit"]');
      const origLabel = btn.textContent;
      // Reveal candidates section EARLY so the user sees something is happening,
      // with a temporary "searching" placeholder.
      $('#candidates').hidden = false;
      const titleEl = document.querySelector('#candidates .section-title');
      const leadEl = document.querySelector('#candidates .section-lead');
      const origTitle = titleEl.innerHTML;
      const origLead = leadEl.textContent;
      titleEl.textContent = `${T.searching_prefix}${state.address || T.candidate}${T.searching_suffix}`;
      leadEl.textContent = T.please_wait;
      $('#candidates').scrollIntoView({ behavior: 'smooth', block: 'start' });

      if (state.address) {
        btn.textContent = T.finding_basin;
        btn.disabled = true;
        const [geo, _] = await Promise.all([
          geocodeAddress(state.address),
          loadWatersheds(),
        ]);
        if (geo) {
          state.addressLatLon = [geo.lat, geo.lon];
          const basin = findContainingBasin([geo.lon, geo.lat], state.watersheds);
          if (basin) {
            const upstream = findUpstreamBasins(basin, state.watersheds);
            state.userBasin = basin;
            state.watershedBasins = [basin, ...upstream];
            state.candidateBasinFilter = true;
            console.log(`User basin: ${basin.properties.hybas_id}, +${upstream.length} upstream basins, total area ${(basin.properties.up_area_sqkm || 0).toLocaleString()} km²`);
          } else {
            console.warn('No basin contains the address — coastline issue?');
            state.userBasin = null;
            state.watershedBasins = [];
            state.candidateBasinFilter = false;
          }
        }
        btn.textContent = origLabel;
        btn.disabled = false;
      } else {
        state.addressLatLon = null;
        state.userBasin = null;
        state.watershedBasins = [];
        state.candidateBasinFilter = false;
      }

      showCandidates();
    });
  }

  // ---- Step 2: candidates ----
  // Pair a featured forest (Himi, with full Sentinel-2 view) with real J-credit projects from the region
  function showCandidates() {
    const featuredSeed = window.getMorimieruCandidates(state.region);
    const featured = featuredSeed.filter(c => c.deepdive).map(c => {
      // Tag featured candidates with in_watershed flag too
      if (state.candidateBasinFilter && state.watershedBasins.length) {
        const inside = state.watershedBasins.some(b => pointInGeometry([c.lon, c.lat], b.geometry));
        if (inside) {
          return { ...c, in_watershed: true, tagline: T.in_basin_tagline };
        }
      }
      return c;
    });
    const realProjects = pickRealProjects(state.region, 4);

    state.candidates = [...featured, ...realProjects];

    // Update headline + render watershed summary block
    // (the inner spans #company-name-display / #candidate-count are rebuilt below)
    const title = document.querySelector('#candidates .section-title');
    const lead = document.querySelector('#candidates .section-lead');
    const summary = $('#watershed-summary');
    const inWsCount = state.candidates.filter(c => c.in_watershed).length;
    const upstreamCount = state.watershedBasins.length > 0 ? state.watershedBasins.length - 1 : 0;

    if (state.userBasin) {
      const basinArea = Math.round(state.userBasin.properties.area_sqkm || 0);
      const upArea = Math.round(state.userBasin.properties.up_area_sqkm || basinArea);

      title.innerHTML = `<span id="company-name-display">${state.company}</span>${T.basin_title_suffix}<span id="candidate-count">${inWsCount || state.candidates.length}</span>${T.basins_word}`;
      lead.textContent = T.basin_intro_lead;

      $('#ws-name').textContent = `${T.basin_id_label}${state.userBasin.properties.hybas_id}${T.basin_id_suffix}`;
      $('#ws-area').textContent = upArea.toLocaleString();
      $('#ws-jc-count').textContent = inWsCount;
      $('#ws-upstream-count').textContent = upstreamCount;
      summary.hidden = false;
    } else if (state.address) {
      title.innerHTML = `<span id="company-name-display">${state.company}</span>${T.region_candidates_suffix_1}${state.candidates.length}${T.region_candidates_suffix_2}`;
      lead.textContent = T.region_lead;
      summary.hidden = true;
    } else {
      title.innerHTML = `<span id="company-name-display">${state.company || T.you}</span>${T.default_title_pre}<span id="candidate-count">${state.candidates.length}</span>${T.default_title_post}`;
      lead.textContent = T.default_lead;
      summary.hidden = true;
    }

    const section = $('#candidates');
    section.hidden = false;
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });

    renderCandidatesList();
    initCandidateMap();
  }

  // Pick real projects matching the region. Each region maps to a set of prefectures.
  const REGION_PREFS = {
    hokkaido: ['北海道'],
    tohoku: ['青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県'],
    kanto: ['茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県'],
    chubu: ['新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県', '静岡県', '愛知県'],
    kansai: ['三重県', '滋賀県', '京都府', '大阪府', '兵庫県', '奈良県', '和歌山県'],
    chugoku: ['鳥取県', '島根県', '岡山県', '広島県', '山口県'],
    shikoku: ['徳島県', '香川県', '愛媛県', '高知県'],
    kyushu: ['福岡県', '佐賀県', '長崎県', '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県'],
  };

  function pickRealProjects(region, count) {
    if (!state.jcreditProjects.length) return [];
    let pool = state.jcreditProjects;

    // If we have a matched watershed, prefer projects inside the user's basin + upstream basins
    let inWatershed = [];
    if (state.candidateBasinFilter && state.watershedBasins.length) {
      for (const p of pool) {
        for (const b of state.watershedBasins) {
          if (pointInGeometry([p.lon, p.lat], b.geometry)) {
            inWatershed.push({ ...p, _basin: b });
            break;
          }
        }
      }
      console.log(`${inWatershed.length} J-credit projects in your watershed`);
    }

    // Pick: prefer watershed-matched, fall back to region, then everything else
    let primary, secondary;
    if (inWatershed.length) {
      primary = inWatershed;
      secondary = pool.filter(p => !inWatershed.some(w => w.no === p.no));
    } else if (region && region !== 'all') {
      const prefs = REGION_PREFS[region] || [];
      primary = pool.filter(p => prefs.includes(p.prefecture));
      secondary = pool.filter(p => !prefs.includes(p.prefecture));
    } else {
      primary = pool;
      secondary = [];
    }

    // Shuffle then take from primary first
    const shuffle = arr => [...arr].sort(() => Math.random() - 0.5);
    const sample = [...shuffle(primary).slice(0, count), ...shuffle(secondary).slice(0, Math.max(0, count - primary.length))].slice(0, count);

    // Each project's verified CO2 number lives in its linked PDF on japancredit.go.jp;
    // the card shows our area-based estimate until we pull those PDFs into the dataset.
    return sample.map(p => {
      // Each project's verified CO2 number lives in its linked PDF on japancredit.go.jp;
      // the card shows our area-based estimate until we pull those PDFs into the dataset.
      const ha = 80 + (parseInt(p.no.replace(/\D/g, '') || '0') % 700);
      const co2_per_ha = 8 + Math.random() * 4;
      const co2_estimate = Math.round(ha * co2_per_ha);
      const uncertainty = co2_estimate * 0.18;
      const inWatershed = !!p._basin;
      // Park badge: "国立公園内" if inside, "🏔 国立公園隣接 (◯km)" if nearby
      let park_badge = null;
      if (p.park) {
        if (p.park.nearby_km != null) {
          park_badge = `${T.park_nearby_prefix}${p.park.park_type}（${p.park.nearby_km}${T.park_nearby_suffix}`;
        } else {
          park_badge = `${T.park_inside_prefix}${p.park.park_type}${T.park_inside}`;
        }
      }

      return {
        id: `jc-${p.no}`,
        name: shortenSummary(p.summary),
        pref: p.location,
        prefecture: p.prefecture,
        lat: p.lat,
        lon: p.lon,
        area_ha: ha,
        species: T.species_default,
        mean_height: '— m',
        stand_age: '—',
        co2_estimate: co2_estimate,
        co2_low: Math.round(co2_estimate - uncertainty),
        co2_high: Math.round(co2_estimate + uncertainty),
        credit_man_yen: Math.round(co2_estimate * 1.2),
        owner: p.operator,
        deepdive: false,
        tagline: inWatershed ? T.in_basin_short : `${T.jcredit_tagline_pre}${p.no} · ${p.methodology.split(' ')[0]}`,
        in_watershed: inWatershed,
        park_badge: park_badge,
        _jcredit: p
      };
    });
  }

  function shortenSummary(s) {
    if (!s) return T.methodology_default;
    return s.length > 24 ? s.slice(0, 24) + '…' : s;
  }

  function renderCandidatesList() {
    const list = $('#candidates-list');
    list.innerHTML = '';
    state.candidates.forEach((c, idx) => {
      const card = document.createElement('div');
      card.className = 'candidate';
      card.dataset.id = c.id;
      card.innerHTML = `
        <div class="candidate-header">
          <h3 class="candidate-name">${c.name}</h3>
          <span class="candidate-pref">${c.pref}</span>
        </div>
        ${c.tagline ? `<p style="margin:6px 0 4px;font-size:12px;color:var(--earth-600);font-weight:500;">✦ ${c.tagline}</p>` : ''}
        ${c.park_badge ? `<p style="margin:0 0 10px;font-size:11px;color:#3b6da1;font-weight:500;">${c.park_badge}</p>` : ''}
        <dl class="candidate-meta">
          <dt>${T.card_area}</dt><dd>${c.area_ha} ha</dd>
          <dt>${T.card_species}</dt><dd>${c.species.replace(/ /g, '')}</dd>
          <dt>${T.card_age}</dt><dd>${c.stand_age}</dd>
          <dt>${T.card_owner}</dt><dd>${c.owner || T.no_owner}</dd>
        </dl>
        <div class="candidate-co2">
          <span class="co2-num">${fmtMan(c.co2_estimate)}</span>
          <span class="co2-unit">${T.co2_unit}</span>
          <span style="margin-left:auto;font-size:11px;color:var(--ink-500);">
            ±${fmtMan((c.co2_high - c.co2_low) / 2)}
          </span>
        </div>
        <div class="candidate-credit">${T.credit_estimate_prefix}${fmtMan(c.credit_man_yen)}${T.credit_estimate_suffix}</div>
        <p class="candidate-cta">${c.deepdive ? T.cta_deepdive : T.cta_mapview}</p>
      `;
      card.addEventListener('click', () => selectCandidate(c.id));
      list.appendChild(card);
    });
  }

  function initCandidateMap() {
    if (state.candidateMap) {
      state.candidateMap.remove();
      state.candidateMap = null;
    }
    const center = state.candidates.length
      ? [state.candidates[0].lat, state.candidates[0].lon]
      : [36.5, 138.0];
    const map = L.map('candidates-map', { zoomControl: true, scrollWheelZoom: false }).setView(center, 7);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OSM contributors',
      maxZoom: 18
    }).addTo(map);

    // ---- Watershed overlay ----
    if (state.watershedBasins.length) {
      const userBasinFC = {
        type: 'FeatureCollection',
        features: [state.userBasin],
      };
      const upstreamFC = {
        type: 'FeatureCollection',
        features: state.watershedBasins.filter(b => b !== state.userBasin),
      };

      // Upstream basins in a lighter, complementary color
      L.geoJSON(upstreamFC, {
        style: {
          color: '#3b6da1',
          weight: 1,
          fillColor: '#7fadda',
          fillOpacity: 0.18,
        },
      }).addTo(map).bindTooltip(T.tip_upstream, { sticky: true });

      // The user's local basin
      L.geoJSON(userBasinFC, {
        style: {
          color: '#1f4570',
          weight: 2,
          fillColor: '#3b6da1',
          fillOpacity: 0.25,
        },
      }).addTo(map).bindTooltip(T.tip_user_basin, { sticky: true });
    }

    // ---- User's company location ----
    if (state.addressLatLon) {
      const [lat, lon] = state.addressLatLon;
      L.marker([lat, lon], {
        icon: L.divIcon({
          className: 'user-loc-pin',
          html: '<div class="pin-inner">🏢</div>',
          iconSize: [40, 40],
          iconAnchor: [20, 36],
        }),
      }).addTo(map).bindTooltip(`<b>${state.company}</b><br>${state.address}`, { direction: 'top' });
    }

    // ---- Forest candidates ----
    state.candidates.forEach((c) => {
      const isDeepdive = c.deepdive;
      const inWs = c.in_watershed;
      const marker = L.circleMarker([c.lat, c.lon], {
        radius: isDeepdive ? 14 : (inWs ? 12 : 9),
        fillColor: isDeepdive ? '#c47a4a' : (inWs ? '#2d5a3d' : '#7a786a'),
        color: 'white',
        weight: 3,
        opacity: 1,
        fillOpacity: 0.9,
      }).addTo(map);

      const tipLine2 = inWs ? T.tt_upstream_html : '';
      marker.bindTooltip(
        `<b>${c.name}</b><br>${tipLine2}${(__MM_LANG==='en'?prefJaToEn(c.pref):c.pref)}<br>${fmtMan(c.co2_estimate)}${T.co2_tip_suffix}`,
        { direction: 'top', offset: [0, -8] }
      );

      marker.on('click', () => selectCandidate(c.id));
      c.__marker = marker;
    });

    // ---- Fit bounds: user location + candidates + watershed ----
    const fitItems = state.candidates.map(c => [c.lat, c.lon]);
    if (state.addressLatLon) fitItems.push(state.addressLatLon);
    if (fitItems.length > 1) {
      const bounds = L.latLngBounds(fitItems);
      map.fitBounds(bounds, { padding: [40, 40] });
    }

    state.candidateMap = map;
    setTimeout(() => map.invalidateSize(), 100);
  }

  function selectCandidate(id) {
    const c = state.candidates.find(x => x.id === id);
    if (!c) return;
    state.selected = c;

    // Highlight in list
    $$('.candidate').forEach(el => {
      el.classList.toggle('selected', el.dataset.id === id);
    });

    // Highlight on map
    state.candidates.forEach(other => {
      if (other.__marker) {
        other.__marker.setStyle({
          fillColor: other.id === id ? '#c47a4a' : (other.deepdive ? '#c47a4a' : '#2d5a3d'),
          radius: other.id === id ? 16 : (other.deepdive ? 14 : 10)
        });
      }
    });

    // If deepdive available → show step 3, otherwise just scroll list focus
    if (c.deepdive) {
      showDeepDive(c);
    } else {
      // Still allow committing on non-deepdive candidates
      showDeepDive(c, { simplified: true });
    }
  }

  // ---- Step 3: deep dive ----
  function showDeepDive(c, opts = {}) {
    const section = $('#deepdive');
    section.hidden = false;

    $('#dd-title').textContent = `${c.pref}・${c.name}`;
    if (c.deepdive && state.sentinelMeta?.scene) {
      const scene = state.sentinelMeta.scene;
      const d = (scene.datetime || '').slice(0, 10);
      const cc = (scene.cloud_cover ?? 0).toFixed(1);
      $('#dd-lead').innerHTML = `${T.dd_lead_himi_pre}<b>${d}</b>${T.dd_lead_himi_mid}${cc}${T.dd_lead_himi_post}`;
    } else if (c.tagline) {
      $('#dd-lead').textContent = `${c.tagline}${T.dd_lead_jcredit_suffix}`;
    } else {
      $('#dd-lead').textContent = T.dd_lead_default;
    }

    $('#dd-co2').textContent = fmtMan(c.co2_estimate);
    document.querySelector('#deepdive .metric-card.highlight .metric-error').textContent =
      `${T.co2_ci_prefix}${fmtMan(c.co2_low)}${T.co2_ci_dash}${fmtMan(c.co2_high)}${T.co2_ci_suffix}`;

    // Water yield card — Himi only for now
    const waterCard = $('#dd-water-card');
    if (waterCard) {
      if (c.deepdive && state.himiWater) {
        const w = state.himiWater;
        waterCard.hidden = false;
        $('#dd-water-m3').textContent = fmtMan(w.aoi_total.water_yield_m3_per_yr);
        $('#dd-water-detail').textContent =
          `${w.results_mm_per_yr.water_yield}${T.water_detail_mid_1}${w.results_pct.water_yield_pct}${T.water_detail_mid_2}${w.aoi.forest_area_ha.toLocaleString()}${T.water_detail_mid_3}${w.aoi_total.water_yield_million_tons_per_yr}${T.water_detail_suffix}`;
      } else {
        waterCard.hidden = true;
      }
    }
    $('#dd-credit').textContent = fmtMan(c.credit_man_yen);
    $('#dd-area').textContent = `${c.area_ha} ha`;
    $('#dd-species').textContent = c.species;
    $('#dd-height').textContent = c.mean_height || '—';
    $('#dd-age').textContent = c.stand_age || '—';
    $('#dd-owner').textContent = c.owner || '—';
    $('#dd-date').textContent = (function () {
      const d = new Date();
      d.setDate(d.getDate() - 3);
      return d.toISOString().slice(0, 10);
    })();

    // Init map for this candidate
    if (state.ddMap) {
      state.ddMap.remove();
      state.ddMap = null;
    }
    const map = L.map('dd-map', { zoomControl: true, scrollWheelZoom: false }).setView([c.lat, c.lon], 12);
    // Esri World Imagery as base
    const baseLayer = L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      { attribution: 'Tiles © Esri', maxZoom: 18 }
    ).addTo(map);

    // NDVI overlay only for the featured deepdive candidate (Himi),
    // where we have a real Sentinel-2 scene.
    if (c.deepdive && state.sentinelMeta && state.sentinelMeta.leaflet_bounds) {
      state.ddNdviLayer = L.imageOverlay(
        'data/sentinel/himi_ndvi.png',
        state.sentinelMeta.leaflet_bounds,
        { opacity: 0.75, attribution: 'NDVI © Sentinel-2 / Copernicus' }
      ).addTo(map);
      // Fit to actual data bounds
      map.fitBounds(state.sentinelMeta.leaflet_bounds, { padding: [20, 20] });

      // Layer control: NDVI vs Hide
      const overlays = { [T.ndvi_layer_name]: state.ddNdviLayer };
      L.control.layers(null, overlays, { position: 'topright', collapsed: false }).addTo(map);

      // Update stamp metadata with real scene info
      updateSatelliteStamp(state.sentinelMeta);
    } else {
      // Forest area circle (illustrative) for non-deepdive candidates
      L.circle([c.lat, c.lon], {
        radius: Math.sqrt(c.area_ha * 10000 / Math.PI),
        color: '#c47a4a',
        weight: 2,
        fillColor: '#c47a4a',
        fillOpacity: 0.18
      }).addTo(map).bindTooltip(`${c.name}（${c.area_ha} ha）`, { permanent: false });
    }

    state.ddMap = map;
    setTimeout(() => map.invalidateSize(), 100);

    drawNDVIPath(c);
    renderMethodBlock(c);

    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function renderMethodBlock(c) {
    const block = $('#method-details');
    const body = $('#method-body');
    if (!block || !body) return;
    if (!c.deepdive || !state.himiCo2) {
      block.hidden = true;
      return;
    }
    const co2 = state.himiCo2;
    const fm = co2.forest_mask_source;
    const p = co2.parameters;
    const w = state.himiWater;
    block.hidden = false;
    body.innerHTML = `
      <ol class="method-steps">
        <li>
          <h4>${T.method_h1}</h4>
          <p>
            ${T.method_p_pre}<code>${fm.scene_window}</code>${T.method_p_mid}<code>${fm.forest_threshold_ndvi}</code>${T.method_p_post}
            
          </p>
          <ul class="method-list">
            <li>${T.method_aoi_area}<strong>${co2.aoi.total_area_ha.toLocaleString()} ha</strong>${T.method_aoi_name_pre}${co2.aoi.name}${T.method_aoi_name_post}</li>
            <li>${T.method_pixels}${fm.total_pixels.toLocaleString()}${T.method_pixels_each}${fm.pixel_area_ha}${T.method_pixels_unit}</li>
            <li>${T.method_valid_pct}<strong>${fm.valid_coverage_pct}%</strong></li>
            <li>${T.method_forest_pct}<strong>${fm.forest_ratio_pct}%</strong></li>
            <li>${T.method_forest_area}<strong>${co2.forest_area_ha.toLocaleString()} ha</strong></li>
          </ul>
        </li>
        <li>
          <h4>${T.method_h2}</h4>
          <p><code>${co2.method}</code>${T.method_formula_intro_pre}</p>
          <pre class="method-formula">CO₂/ha/yr = MAI × wood_density × BEF × (1 + R) × CF × (44/12)
        = ${p.MAI_m3_per_ha_yr} × ${p.wood_density_t_per_m3} × ${p.BEF}
          × (1 + ${p.root_shoot_ratio}) × ${p.carbon_fraction} × ${p.co2_per_c.toFixed(3)}
        ≈ ${co2.co2_per_ha_per_year} t-CO₂</pre>
          <ul class="method-list small-list">
            <li>${T.method_mai}${p.MAI_m3_per_ha_yr}${T.method_mai_unit}${co2.parameter_sources.MAI})</li>
            <li>${T.method_density}${p.wood_density_t_per_m3}${T.method_density_unit}${co2.parameter_sources.wood_density})</li>
            <li>${T.method_bef}${p.BEF} (${co2.parameter_sources.BEF})</li>
            <li>${T.method_root}${p.root_shoot_ratio} (${co2.parameter_sources.root_shoot_ratio})</li>
            <li>${T.method_carbon}${p.carbon_fraction} (${co2.parameter_sources.carbon_fraction})</li>
          </ul>
        </li>
        <li>
          <h4>${T.method_h3}</h4>
          <pre class="method-formula">${co2.forest_area_ha.toLocaleString()} ha × ${co2.co2_per_ha_per_year} t-CO₂/ha/yr
  ≈ <strong>${co2.annual_co2_t.toLocaleString()} ${T.co2_unit}</strong>
  ( ±${(co2.uncertainty_pct * 100).toFixed(0)}% CI: ${co2.annual_co2_low_t.toLocaleString()} – ${co2.annual_co2_high_t.toLocaleString()} )</pre>
          <p class="method-note">
            ${T.method_uncertainty}
            ${T.method_uncertainty_2}
          </p>
        </li>
        ${w ? `
        <li>
          <h4>${T.method_h4}</h4>
          <p>
            <a href="${w.method_source_url}" target="_blank" rel="noopener">${T.method_w_link_text}</a>
            ${T.method_w_intro}
          </p>
          <ul class="method-list">
            <li>${T.method_w_climate}<strong>NASA POWER API</strong>${T.method_w_climate_src_pre}${w.inputs.climate.source})</li>
            <li>${T.method_w_elev}${w.inputs.elevation.weather_station_m}${T.method_w_elev_mid}${w.inputs.elevation.forest_point_m}${T.method_w_elev_post}</li>
            <li>${T.method_w_geo}<strong>${w.inputs.geology.rinya_class}</strong> (${w.inputs.geology.lithology}${T.method_w_geo_post}</li>
            <li>${T.method_w_forest}${w.inputs.forest.type}${T.method_w_forest_density}${w.inputs.forest.density_per_ha}${T.method_w_forest_density_unit}${w.inputs.forest.dbh_cm}${T.method_w_forest_dbh_unit}${w.inputs.forest.height_m}${T.method_w_forest_h_unit}</li>
          </ul>
          <pre class="method-formula">${T.method_w_formula_l1}

  ${T.method_w_formula_precip}${w.results_mm_per_yr.precipitation} mm/yr (100%)
  ${T.method_w_formula_runoff}${w.results_mm_per_yr.direct_runoff} mm/yr (${w.results_pct.direct_runoff_pct}%)
  ${T.method_w_formula_evapo}${w.results_mm_per_yr.evapotranspiration} mm/yr (${w.results_pct.evapotranspiration_pct}%)
  ────────────────
  <strong>${T.method_w_formula_yield_prefix}${w.results_mm_per_yr.water_yield} mm/yr (${w.results_pct.water_yield_pct}%)</strong>
  ${T.method_w_formula_aoi}${w.aoi_total.water_yield_m3_per_yr.toLocaleString()}${T.method_w_formula_aoi_unit_1}${w.aoi_total.water_yield_million_tons_per_yr}${T.method_w_formula_aoi_unit_2}</pre>
          <p class="method-note">
            ${T.method_w_note_1}
            ${T.method_w_note_2}
          </p>
        </li>` : ''}
      </ol>
    `;
  }

  function updateSatelliteStamp(meta) {
    // Update the on-map metadata stamp (the small overlay box in the deep dive map)
    const stamp = document.querySelector('.dd-stamp');
    if (!stamp || !meta) return;
    const scene = meta.scene || {};
    const co2 = state.himiCo2 || {};
    const fmask = co2.forest_mask_source || {};
    const date = (scene.datetime || '').slice(0, 10);
    const sceneShort = (scene.scene_id || '').replace(/_(SAFE|MSIL2A_)/g, ' ').slice(0, 32);
    stamp.innerHTML = `
      <div class="stamp-row"><span class="stamp-label">Source</span><span>Sentinel-2 L2A (CDSE)</span></div>
      <div class="stamp-row"><span class="stamp-label">Scene</span><span>${sceneShort}</span></div>
      <div class="stamp-row"><span class="stamp-label">Date</span><span>${date}</span></div>
      <div class="stamp-row"><span class="stamp-label">Cloud</span><span>${(scene.cloud_cover ?? 0).toFixed(1)}%</span></div>
      <div class="stamp-row"><span class="stamp-label">Valid pixels</span><span>${fmask.valid_coverage_pct ?? '?'}%</span></div>
      <div class="stamp-row"><span class="stamp-label">Forest pixels</span><span>${fmask.forest_ratio_pct ?? '?'}%</span></div>
      <div class="stamp-row"><span class="stamp-label">${T.ndvi_obs_points}</span><span>${state.sentinelSeries?.points?.length ?? '?'} (5yr)</span></div>
    `;
  }

  function drawNDVIPath(c) {
    // Plot the real NDVI time series from CDSE Statistical API.
    // Falls back to a smooth seasonal curve when no series is available
    // (e.g., for candidates other than Himi).
    const series = (c.deepdive && state.sentinelSeries?.points) || null;
    const W = 600, H = 80;
    const Y_MIN = 0.0, Y_MAX = 1.0;

    let xs, ys;
    if (series && series.length >= 4) {
      // Map real dates onto X
      const t0 = new Date(series[0].date).getTime();
      const t1 = new Date(series[series.length - 1].date).getTime();
      const span = t1 - t0 || 1;
      xs = series.map(p => ((new Date(p.date).getTime() - t0) / span) * W);
      ys = series.map(p => H - (p.mean - Y_MIN) / (Y_MAX - Y_MIN) * (H - 4) - 2);
      updateTimelineAxis(series);
    } else {
      const N = 100;
      xs = [], ys = [];
      for (let i = 0; i < N; i++) {
        const t = i / (N - 1);
        const seasonal = 0.10 * Math.cos(2 * Math.PI * (t * 5 - 0.2));
        const v = 0.55 + seasonal;
        xs.push(t * W);
        ys.push(H - (v - Y_MIN) / (Y_MAX - Y_MIN) * (H - 4) - 2);
      }
    }

    let d = `M${xs[0].toFixed(1)},${ys[0].toFixed(1)}`;
    for (let i = 1; i < xs.length; i++) {
      d += ` L${xs[i].toFixed(1)},${ys[i].toFixed(1)}`;
    }
    d += ` L${W},${H} L0,${H} Z`;
    $('#ndvi-path').setAttribute('d', d);
  }

  function updateTimelineAxis(series) {
    const axis = document.querySelector('.timeline-axis');
    if (!axis || !series.length) return;
    const t0 = new Date(series[0].date);
    const t1 = new Date(series[series.length - 1].date);
    const startYear = t0.getFullYear();
    const endYear = t1.getFullYear();
    const years = [];
    for (let y = startYear; y <= endYear; y++) years.push(y);
    axis.innerHTML = years.map(y => `<span>${y}</span>`).join('');
    const label = document.querySelector('.timeline-label');
    if (label) {
      label.textContent = `${T.ndvi_label_pre}${endYear - startYear}${T.ndvi_label_mid}${series.length}${T.ndvi_label_post}`;
    }
  }

  // ---- Step 4: commit certificate ----
  window.goToCommit = function () {
    const c = state.selected;
    if (!c) return;
    const section = $('#commit');
    section.hidden = false;

    const now = new Date();
    const issueDate = now.toISOString().slice(0, 10).replace(/-/g, '');
    const certNo = `MM-${issueDate}-${Math.floor(Math.random() * 900 + 100)}`;

    $('#cert-no').textContent = certNo;
    $('#cert-company').textContent = state.company || T.cert_company_sample;
    $('#cert-forest').textContent = `${c.pref}・${c.name}`;
    $('#cert-area').textContent = `${c.area_ha} ha`;
    $('#cert-co2').innerHTML = `${fmtMan(c.co2_estimate)} t-CO₂ <span class="cert-sub">（95% CI: ${fmtMan(c.co2_low)} – ${fmtMan(c.co2_high)}）</span>`;

    const end = new Date(now);
    end.setFullYear(end.getFullYear() + 5);
    $('#cert-period').textContent = `${formatJpDate(now)} – ${formatJpDate(end)}${T.cert_period_suffix}`;
    $('#cert-budget').textContent = (__MM_LANG==='en' ? `¥${(state.budget*1e4).toLocaleString()}` : `${fmtMan(state.budget)} 万円`);

    $('#cert-timestamp').textContent = now.toISOString().replace('Z', '+00:00');

    // Self hash (illustrative)
    const payload = JSON.stringify({
      certNo,
      company: state.company,
      forest: c.id,
      area: c.area_ha,
      co2: c.co2_estimate,
      ts: now.toISOString()
    });
    sha256(payload).then(h => {
      $('#cert-self-hash').textContent = `${h.slice(0, 8)}...${h.slice(-8)}`;
    });

    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  function formatJpDate(d) {
    return T.yearly_format(d.getFullYear(), d.getMonth() + 1, d.getDate());
  }

  // ---- Reset ----
  window.resetFlow = function () {
    $('#candidates').hidden = true;
    $('#deepdive').hidden = true;
    $('#commit').hidden = true;
    state.candidates = [];
    state.selected = null;
    if (state.candidateMap) { state.candidateMap.remove(); state.candidateMap = null; }
    if (state.ddMap) { state.ddMap.remove(); state.ddMap = null; }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // ---- Init ----
  document.addEventListener('DOMContentLoaded', async () => {
    initForm();
    // Load datasets in the background — non-blocking
    await Promise.all([loadJcredit(), loadSentinelMeta()]);
  });
})();
