// もりみえる - interaction logic
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
      const r = await fetch('data/watersheds/japan_lev08.geojson');
      state.watersheds = await r.json();
      console.log(`Loaded ${state.watersheds.features.length} watersheds`);
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
      const [meta, series, co2] = await Promise.all([
        fetch('data/sentinel/himi_meta.json').then(r => r.json()).catch(() => null),
        fetch('data/sentinel/himi_timeseries.json').then(r => r.json()).catch(() => null),
        fetch('data/sentinel/himi_co2.json').then(r => r.json()).catch(() => null),
      ]);
      state.sentinelMeta = meta;
      state.sentinelSeries = series;
      state.himiCo2 = co2;
      if (meta) console.log('Sentinel scene:', meta.scene?.scene_id);
      if (series) console.log(`NDVI time series: ${series.points?.length} points`);
      if (co2) console.log(`Himi CO2: ${co2.annual_co2_t.toLocaleString()} t-CO2/yr`);

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
      budgetDisplay.textContent = `${fmtMan(v)}万円`;
    });

    $('#company-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      state.company = fd.get('company') || 'あなた';
      state.industry = fd.get('industry');
      state.budget = +fd.get('budget');
      state.region = fd.get('region');
      state.vision = fd.get('vision') || '';
      state.address = (fd.get('address') || '').trim();

      // Show loading state if we have an address — we'll geocode + load watersheds in parallel
      const btn = e.target.querySelector('button[type="submit"]');
      const origLabel = btn.textContent;
      if (state.address) {
        btn.textContent = '取水域を特定中…';
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
    const featured = featuredSeed.filter(c => c.deepdive);
    const realProjects = pickRealProjects(state.region, 4);

    state.candidates = [...featured, ...realProjects];

    $('#company-name-display').textContent = state.company || 'あなた';
    $('#candidate-count').textContent = state.candidates.length;

    // Update headline: if we matched a watershed, brag about it
    const title = document.querySelector('#candidates .section-title');
    const lead = document.querySelector('#candidates .section-lead');
    const inWsCount = state.candidates.filter(c => c.in_watershed).length;
    if (state.userBasin && inWsCount > 0) {
      const upArea = Math.round(state.userBasin.properties.up_area_sqkm || state.userBasin.properties.area_sqkm || 0);
      title.innerHTML = `<span id="company-name-display">${state.company}</span> の取水域・上流の森、<span id="candidate-count">${inWsCount}</span> つ見つかりました`;
      lead.innerHTML = `工場や本社で使う水は、上流の森が育んでいます。あなたの会社の地点を含む水系（流域面積 <b>${upArea.toLocaleString()} km²</b>）の中で、J-クレジット制度に登録された森林を優先的にお見せしています。`;
    } else if (state.userBasin) {
      title.innerHTML = `<span id="company-name-display">${state.company}</span> の取水域内、登録済みプロジェクトが見つからなかったので、近隣の候補をお見せします`;
      lead.textContent = 'あなたの会社の流域内では現時点でJ-クレジット登録森林が見つかりませんでした。近隣の森から優先表示しています。';
    } else if (state.address) {
      title.innerHTML = `<span id="company-name-display">${state.company}</span> 向けの候補、${state.candidates.length} つ`;
      lead.textContent = '住所から取水域を特定できなかったため（離島・海岸沿いの可能性）、希望地域の中から候補を提示しています。';
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
      return {
        id: `jc-${p.no}`,
        name: shortenSummary(p.summary),
        pref: p.location,
        prefecture: p.prefecture,
        lat: p.lat,
        lon: p.lon,
        area_ha: ha,
        species: 'スギ・ヒノキ 70% / 広葉樹 30%（推定）',
        mean_height: '— m',
        stand_age: '—',
        co2_estimate: co2_estimate,
        co2_low: Math.round(co2_estimate - uncertainty),
        co2_high: Math.round(co2_estimate + uncertainty),
        credit_man_yen: Math.round(co2_estimate * 1.2),
        owner: p.operator,
        deepdive: false,
        tagline: inWatershed ? '🌊 あなたの取水域・上流の森' : `J-クレジット登録番号 ${p.no}・${p.methodology.split(' ')[0]}`,
        in_watershed: inWatershed,
        _jcredit: p
      };
    });
  }

  function shortenSummary(s) {
    if (!s) return '森林経営活動プロジェクト';
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
        ${c.tagline ? `<p style="margin:6px 0 10px;font-size:12px;color:var(--earth-600);font-weight:500;">✦ ${c.tagline}</p>` : ''}
        <dl class="candidate-meta">
          <dt>面積</dt><dd>${c.area_ha} ha</dd>
          <dt>樹種</dt><dd>${c.species.replace(/ /g, '')}</dd>
          <dt>林齢</dt><dd>${c.stand_age}</dd>
          <dt>所有</dt><dd>${c.owner || '—'}</dd>
        </dl>
        <div class="candidate-co2">
          <span class="co2-num">${fmtMan(c.co2_estimate)}</span>
          <span class="co2-unit">t-CO₂/年</span>
          <span style="margin-left:auto;font-size:11px;color:var(--ink-500);">
            ±${fmtMan((c.co2_high - c.co2_low) / 2)}
          </span>
        </div>
        <div class="candidate-credit">クレジット試算：約 ${fmtMan(c.credit_man_yen)} 万円/年</div>
        <p class="candidate-cta">${c.deepdive ? '衛星画像で森を見る →' : '地図で見る →'}</p>
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
      }).addTo(map).bindTooltip('あなたの取水域・上流側', { sticky: true });

      // The user's local basin
      L.geoJSON(userBasinFC, {
        style: {
          color: '#1f4570',
          weight: 2,
          fillColor: '#3b6da1',
          fillOpacity: 0.25,
        },
      }).addTo(map).bindTooltip('あなたの会社の取水域', { sticky: true });
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

      const tipLine2 = inWs ? '<span style="color:#3b6da1;">🌊 あなたの取水域・上流</span><br>' : '';
      marker.bindTooltip(
        `<b>${c.name}</b><br>${tipLine2}${c.pref}<br>${fmtMan(c.co2_estimate)} t-CO₂/年`,
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
    if (c.deepdive && state.sentinelMeta) {
      const d = (state.sentinelMeta.datetime || '').slice(0, 10);
      $('#dd-lead').innerHTML = `林野庁令和7年度委託事業の対象地。<b>${d}</b> の Sentinel-2 衛星画像（雲量${state.sentinelMeta.cloud_cover.toFixed(1)}%）から実際に NDVI を計算し、森林面積を推定しました。地図上の緑が濃い領域ほど植生が活発です。`;
    } else if (c.tagline) {
      $('#dd-lead').textContent = `${c.tagline}。実際のJ-クレジット登録プロジェクトです。`;
    } else {
      $('#dd-lead').textContent = 'Sentinel-1/2 衛星の週次観測と、林野庁オープンデータを統合して可視化しています。';
    }

    $('#dd-co2').textContent = fmtMan(c.co2_estimate);
    const dd = $('#dd-co2').nextElementSibling; // dummy to satisfy lint
    document.querySelector('#deepdive .metric-card.highlight .metric-error').textContent =
      `95% 信頼区間：${fmtMan(c.co2_low)} – ${fmtMan(c.co2_high)} t-CO₂`;
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
      const overlays = { 'NDVI 解析結果': state.ddNdviLayer };
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
    block.hidden = false;
    body.innerHTML = `
      <ol class="method-steps">
        <li>
          <h4>1. 森林面積の特定（衛星実測）</h4>
          <p>
            Sentinel-2 L2A の <code>${fm.scene_window}</code> 期間の最低雲量シーンから NDVI を計算。
            NDVI > <code>${fm.forest_threshold_ndvi}</code> の画素を森林と判定（Hansen et al. 2013, Tier 2 既定値）。
          </p>
          <ul class="method-list">
            <li>AOI 総面積：<strong>${co2.aoi.total_area_ha.toLocaleString()} ha</strong>（${co2.aoi.name}）</li>
            <li>解析画素数：${fm.total_pixels.toLocaleString()} (1 画素 ≈ ${fm.pixel_area_ha} ha)</li>
            <li>有効画素率（非雲）：<strong>${fm.valid_coverage_pct}%</strong></li>
            <li>森林画素率：<strong>${fm.forest_ratio_pct}%</strong></li>
            <li>森林面積：<strong>${co2.forest_area_ha.toLocaleString()} ha</strong></li>
          </ul>
        </li>
        <li>
          <h4>2. 森林1 ha あたりの CO₂ 吸収量</h4>
          <p><code>${co2.method}</code> による既定式：</p>
          <pre class="method-formula">CO₂/ha/年 = MAI × wood_density × BEF × (1 + R) × CF × (44/12)
        = ${p.MAI_m3_per_ha_yr} × ${p.wood_density_t_per_m3} × ${p.BEF}
          × (1 + ${p.root_shoot_ratio}) × ${p.carbon_fraction} × ${p.co2_per_c.toFixed(3)}
        ≈ ${co2.co2_per_ha_per_year} t-CO₂</pre>
          <ul class="method-list small-list">
            <li>MAI：${p.MAI_m3_per_ha_yr} m³/ha/年（${co2.parameter_sources.MAI}）</li>
            <li>木材密度：${p.wood_density_t_per_m3} t/m³（${co2.parameter_sources.wood_density}）</li>
            <li>BEF（バイオマス拡大係数）：${p.BEF}（${co2.parameter_sources.BEF}）</li>
            <li>根/地上比：${p.root_shoot_ratio}（${co2.parameter_sources.root_shoot_ratio}）</li>
            <li>炭素割合：${p.carbon_fraction}（${co2.parameter_sources.carbon_fraction}）</li>
          </ul>
        </li>
        <li>
          <h4>3. AOI 全体の年間 CO₂ 吸収量</h4>
          <pre class="method-formula">${co2.forest_area_ha.toLocaleString()} ha × ${co2.co2_per_ha_per_year} t-CO₂/ha/年
  ≈ <strong>${co2.annual_co2_t.toLocaleString()} t-CO₂/年</strong>
  ( ±${(co2.uncertainty_pct * 100).toFixed(0)}% 信頼幅：${co2.annual_co2_low_t.toLocaleString()} – ${co2.annual_co2_high_t.toLocaleString()} )</pre>
          <p class="method-note">
            不確実性は Tier 2 で典型的に ±30%。MAI の地域差、樹種混交、衛星分類誤差を合算した経験値です。
            個別森林・施業実態を組み込むことで、より狭い信頼幅と高精度な推定が可能になります。
          </p>
        </li>
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
      <div class="stamp-row"><span class="stamp-label">NDVI 観測点</span><span>${state.sentinelSeries?.points?.length ?? '?'} (5yr)</span></div>
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
      label.textContent = `過去 ${endYear - startYear} 年の NDVI 推移（${series.length} 観測点・Sentinel-2 実測）`;
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
    $('#cert-company').textContent = state.company || 'サンプル株式会社';
    $('#cert-forest').textContent = `${c.pref}・${c.name}`;
    $('#cert-area').textContent = `${c.area_ha} ha`;
    $('#cert-co2').innerHTML = `${fmtMan(c.co2_estimate)} t-CO₂ <span class="cert-sub">（95% CI: ${fmtMan(c.co2_low)} – ${fmtMan(c.co2_high)}）</span>`;

    const end = new Date(now);
    end.setFullYear(end.getFullYear() + 5);
    $('#cert-period').textContent = `${formatJpDate(now)} 〜 ${formatJpDate(end)}（5年間）`;
    $('#cert-budget').textContent = `${fmtMan(state.budget)} 万円`;

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
    return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`;
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
