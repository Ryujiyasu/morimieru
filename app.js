// もりみえる - prototype interaction logic
// Pure vanilla JS. Three steps:
//  1) company form  →  2) candidates list/map  →  3) deep dive Himi  →  4) commit certificate

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
    ddMap: null
  };

  // ---- Helpers ----
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  function fmtMan(n) {
    return new Intl.NumberFormat('ja-JP').format(Math.round(n));
  }

  // Cheap deterministic-ish hash for the demo certificate
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

    $('#company-form').addEventListener('submit', (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      state.company = fd.get('company') || 'あなた';
      state.industry = fd.get('industry');
      state.budget = +fd.get('budget');
      state.region = fd.get('region');
      state.vision = fd.get('vision') || '';
      showCandidates();
    });
  }

  // ---- Step 2: candidates ----
  function showCandidates() {
    state.candidates = window.getMorimieruCandidates(state.region);
    if (state.region === 'all') {
      state.candidates = state.candidates.slice(0, 5);
    }

    $('#company-name-display').textContent = state.company || 'あなた';
    $('#candidate-count').textContent = state.candidates.length;

    const section = $('#candidates');
    section.hidden = false;
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });

    renderCandidatesList();
    initCandidateMap();
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
        <p class="candidate-cta">${c.deepdive ? '詳細を見る（深掘りデモ） →' : '地図で見る →'}</p>
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

    state.candidates.forEach((c, idx) => {
      const isDeepdive = c.deepdive;
      const marker = L.circleMarker([c.lat, c.lon], {
        radius: isDeepdive ? 14 : 10,
        fillColor: isDeepdive ? '#c47a4a' : '#2d5a3d',
        color: 'white',
        weight: 3,
        opacity: 1,
        fillOpacity: 0.85
      }).addTo(map);

      marker.bindTooltip(
        `<b>${c.name}</b><br>${c.pref}<br>${fmtMan(c.co2_estimate)} t-CO₂/年`,
        { direction: 'top', offset: [0, -8] }
      );

      marker.on('click', () => selectCandidate(c.id));
      c.__marker = marker;
    });

    if (state.candidates.length > 1) {
      const bounds = L.latLngBounds(state.candidates.map(c => [c.lat, c.lon]));
      map.fitBounds(bounds, { padding: [40, 40] });
    }

    state.candidateMap = map;

    // workaround for Leaflet inside hidden section
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
    $('#dd-lead').textContent = c.tagline
      ? `${c.tagline}。Sentinel-2 の週次観測で「いま」を捉えています。`
      : 'Sentinel-1/2 衛星の週次観測と、林野庁オープンデータを統合して可視化しています。';

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
    // Use satellite-like Esri tiles (free, no key)
    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      { attribution: 'Tiles © Esri', maxZoom: 18 }
    ).addTo(map);

    // Forest area circle (illustrative)
    L.circle([c.lat, c.lon], {
      radius: Math.sqrt(c.area_ha * 10000 / Math.PI), // m
      color: '#c47a4a',
      weight: 2,
      fillColor: '#c47a4a',
      fillOpacity: 0.18
    }).addTo(map).bindTooltip(`${c.name}（${c.area_ha} ha）`, { permanent: false });

    state.ddMap = map;
    setTimeout(() => map.invalidateSize(), 100);

    drawNDVIPath(c);

    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function drawNDVIPath(c) {
    // Generate a plausible weekly NDVI series for 5 years (~260 points)
    // Seasonal cosine + smooth random walk + slight upward trend
    const N = 260;
    const points = [];
    let drift = 0;
    for (let i = 0; i < N; i++) {
      const t = i / N;
      const seasonal = 0.10 * Math.cos(2 * Math.PI * (i / 52 - 0.2)); // peak around late spring
      drift += (Math.random() - 0.49) * 0.012;
      drift *= 0.98;
      const trend = 0.04 * t;
      const v = Math.min(0.95, Math.max(0.25, 0.65 + seasonal + drift + trend));
      points.push(v);
    }
    // Build SVG path
    const W = 600, H = 80;
    const xs = points.map((_, i) => (i / (N - 1)) * W);
    const ys = points.map(v => H - (v - 0.20) / (0.95 - 0.20) * (H - 4) - 2);
    let d = `M${xs[0].toFixed(1)},${ys[0].toFixed(1)}`;
    for (let i = 1; i < N; i++) {
      d += ` L${xs[i].toFixed(1)},${ys[i].toFixed(1)}`;
    }
    // close to baseline
    d += ` L${W},${H} L0,${H} Z`;
    $('#ndvi-path').setAttribute('d', d);
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
  document.addEventListener('DOMContentLoaded', initForm);
})();
