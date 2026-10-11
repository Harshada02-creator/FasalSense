const API = "";
let token = localStorage.getItem("fasal_token") || "";
let currentUser = JSON.parse(localStorage.getItem("fasal_user") || "null");
let currentFarm = null;
let allScenarios = [];
let activeScenarioId = null;

const fmt = n => "₹" + Number(n || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 });
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// ---------------------------------------------------------------------------
// API Helper
// ---------------------------------------------------------------------------
async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (token) headers.Authorization = "Bearer " + token;
  const res = await fetch(API + path, { ...options, headers });
  const data = await res.json().catch(() => ({ detail: "Unexpected server response" }));
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

function toast(msg) {
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(window._toastTimer);
  window._toastTimer = setTimeout(() => el.classList.remove("show"), 3500);
}

// ---------------------------------------------------------------------------
// Navigation & Role State
// ---------------------------------------------------------------------------
function updateNavState() {
  const loginBtn = document.getElementById("nav-login-btn");
  const regBtn = document.getElementById("nav-register-btn");
  const dashBtn = document.getElementById("nav-dash-btn");
  const postListBtn = document.getElementById("post-listing-btn");

  if (currentUser) {
    if (loginBtn) loginBtn.style.display = "none";
    if (regBtn) regBtn.style.display = "none";
    if (dashBtn) {
      dashBtn.style.display = "inline-flex";
      dashBtn.textContent = `Workspace (${currentUser.role}) →`;
    }
    if (postListBtn) postListBtn.style.display = (currentUser.role === "farmer") ? "inline-flex" : "none";
  } else {
    if (loginBtn) loginBtn.style.display = "inline-flex";
    if (regBtn) regBtn.style.display = "inline-flex";
    if (dashBtn) dashBtn.style.display = "none";
    if (postListBtn) postListBtn.style.display = "none";
  }
}

function showPage(name) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  const el = document.getElementById("page-" + name);
  if (el) el.classList.add("active");
  window.scrollTo({ top: 0, behavior: "smooth" });

  if (name === "community") loadCommunity(true);
  if (name === "market") loadListings();
  if (name === "analyzer") renderPublicOrUserAnalyzer();
  if (name === "scenarios") loadScenariosLab();
  if (name === "dashboard" && currentUser) openDashboard();
}

function logout() {
  token = "";
  currentUser = null;
  currentFarm = null;
  localStorage.removeItem("fasal_token");
  localStorage.removeItem("fasal_user");
  updateNavState();
  showPage("home");
  toast("You have logged out.");
}

function authSuccess(data) {
  token = data.token;
  currentUser = data.user;
  localStorage.setItem("fasal_token", token);
  localStorage.setItem("fasal_user", JSON.stringify(currentUser));
  updateNavState();
  showPage("dashboard");
  openDashboard();
  toast(`Welcome to FasalSense, ${currentUser.name}.`);
}

function fillDemoLogin(role) {
  const form = document.getElementById("login-form");
  if (!form) return;
  if (role === "farmer") {
    form.querySelector('input[name="email"]').value = "farmer.demo@example.com";
    form.querySelector('input[name="password"]').value = "DemoFarm123!";
  } else {
    form.querySelector('input[name="email"]').value = "retailer.demo@example.com";
    form.querySelector('input[name="password"]').value = "DemoRetail123!";
  }
}

document.getElementById("login-form")?.addEventListener("submit", async e => {
  e.preventDefault();
  const f = new FormData(e.target);
  const msg = document.getElementById("login-msg");
  msg.textContent = "Authenticating…";
  try {
    const data = await api("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email: f.get("email"), password: f.get("password") })
    });
    authSuccess(data);
    msg.textContent = "";
  } catch (err) {
    msg.textContent = err.message;
  }
});

document.getElementById("register-form")?.addEventListener("submit", async e => {
  e.preventDefault();
  const f = new FormData(e.target);
  const msg = document.getElementById("register-msg");
  msg.textContent = "Creating your account…";
  try {
    const data = await api("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({
        name: f.get("name"),
        email: f.get("email"),
        password: f.get("password"),
        role: f.get("role"),
        locality: "Chharoli Budruk"
      })
    });
    authSuccess(data);
    msg.textContent = "";
  } catch (err) {
    msg.textContent = err.message;
  }
});

// ---------------------------------------------------------------------------
// 7 Pedagogical Demonstration Scenarios
// ---------------------------------------------------------------------------
async function fetchScenarios() {
  if (allScenarios.length > 0) return allScenarios;
  try {
    const d = await api("/api/scenarios");
    allScenarios = d.scenarios || [];
    return allScenarios;
  } catch (e) {
    console.error("Could not fetch scenarios", e);
    return [];
  }
}

async function renderScenarioChipsContainers() {
  const scenarios = await fetchScenarios();
  const containers = [
    document.getElementById("home-scenario-chips"),
    document.getElementById("lab-scenario-chips"),
    document.getElementById("analyzer-scenario-chips")
  ];

  const html = scenarios.map(sc => `
    <button type="button" class="scenario-chip ${activeScenarioId === sc.id ? 'active' : ''}" onclick="selectScenario('${sc.id}')">
      <b>${esc(sc.title)}</b>
      <small>${esc(sc.badge)}</small>
    </button>
  `).join("");

  containers.forEach(c => {
    if (c) c.innerHTML = html;
  });
}

async function selectScenario(scId) {
  activeScenarioId = scId;
  const scenarios = await fetchScenarios();
  const sc = scenarios.find(x => x.id === scId);
  if (!sc) return;

  renderScenarioChipsContainers();

  // If on scenarios lab page:
  const detailEl = document.getElementById("active-scenario-detail");
  if (detailEl) {
    detailEl.innerHTML = `
      <div class="scenario-focus-card">
        <div class="scenario-focus-icon">🧪</div>
        <div class="scenario-focus-body">
          <span class="scenario-focus-badge">${esc(sc.badge)}</span>
          <b>${esc(sc.title)}</b>
          <p>${esc(sc.description)}</p>
          <div style="margin-top:8px; font-size:12px; color:var(--maroon); background:#fcf2ea; padding:8px 12px; border-radius:6px; border:1px solid #eecfbc;">
            <b>Pedagogical Focus for Evaluation:</b> ${esc(sc.pedagogical_focus)}
          </div>
        </div>
      </div>
    `;
  }

  // Populate Analyzer form fields if rendered
  populateAnalyzerWithProfile(sc.profile);

  // Trigger analysis for the scenario
  try {
    const resultsContainer = document.getElementById("scenario-analysis-results") || document.getElementById("analysis-results");
    if (resultsContainer) {
      resultsContainer.innerHTML = '<div class="panel">Recalculating 16 crops for this scenario…</div>';
      const payload = { ...sc.profile, scenario_id: sc.id };
      const d = await api("/api/analyze", { method: "POST", body: JSON.stringify(payload) });
      renderAnalysisCards(d, resultsContainer);
    }
  } catch (err) {
    toast("Scenario analysis failed: " + err.message);
  }
}

function populateAnalyzerWithProfile(p) {
  const form = document.getElementById("analyze-form");
  if (!form) return;
  if (p.area_acres !== undefined) form.querySelector('input[name="area_acres"]').value = p.area_acres;
  if (p.budget_inr !== undefined) form.querySelector('input[name="budget_inr"]').value = p.budget_inr;
  if (p.soil_type !== undefined) form.querySelector('select[name="soil_type"]').value = p.soil_type;
  if (p.soil_ph !== undefined) form.querySelector('input[name="soil_ph"]').value = p.soil_ph ?? "";
  if (p.irrigation !== undefined) form.querySelector('select[name="irrigation"]').value = p.irrigation;
  if (p.water_availability !== undefined) form.querySelector('select[name="water_availability"]').value = p.water_availability;
  if (p.season !== undefined) form.querySelector('select[name="season"]').value = p.season;
}

async function loadScenariosLab() {
  await renderScenarioChipsContainers();
  if (!activeScenarioId && allScenarios.length > 0) {
    selectScenario(allScenarios[0].id);
  }
}

// ---------------------------------------------------------------------------
// Side-by-Side Scenario Comparer
// ---------------------------------------------------------------------------
async function openCompareModal() {
  const modal = document.getElementById("compare-modal");
  const selA = document.getElementById("compare-select-a");
  const selB = document.getElementById("compare-select-b");
  if (!modal || !selA || !selB) return;

  const scenarios = await fetchScenarios();
  const options = scenarios.map((s, idx) => `<option value="${s.id}">${s.title}</option>`).join("");
  selA.innerHTML = options;
  selB.innerHTML = options;

  if (scenarios.length >= 2) {
    selA.value = scenarios[0].id;
    selB.value = scenarios[1].id;
  }

  modal.classList.add("show");
  runSideBySideComparison();
}

function closeCompareModal() {
  document.getElementById("compare-modal")?.classList.remove("show");
}

async function runSideBySideComparison() {
  const selA = document.getElementById("compare-select-a");
  const selB = document.getElementById("compare-select-b");
  const out = document.getElementById("compare-results-wrap");
  if (!selA || !selB || !out) return;

  const scenarios = await fetchScenarios();
  const scA = scenarios.find(x => x.id === selA.value);
  const scB = scenarios.find(x => x.id === selB.value);
  if (!scA || !scB) return;

  out.innerHTML = '<p class="muted">Calculating comparison…</p>';
  try {
    const [resA, resB] = await Promise.all([
      api("/api/analyze", { method: "POST", body: JSON.stringify({ ...scA.profile, scenario_id: scA.id }) }),
      api("/api/analyze", { method: "POST", body: JSON.stringify({ ...scB.profile, scenario_id: scB.id }) })
    ]);

    const mapB = {};
    (resB.recommendations || []).forEach((c, idx) => { mapB[c.name] = { rank: idx + 1, ...c }; });

    const rows = (resA.recommendations || []).slice(0, 8).map((cA, idxA) => {
      const rankA = idxA + 1;
      const cB = mapB[cA.name] || { rank: "—", score: "—", market_balance: "—" };
      const scoreDiff = typeof cB.score === "number" ? (cB.score - cA.score) : 0;
      const diffLabel = scoreDiff > 0 ? `+${scoreDiff}` : `${scoreDiff}`;
      const diffColor = scoreDiff > 0 ? "var(--green)" : scoreDiff < 0 ? "#a84e27" : "var(--muted)";

      return `
        <tr>
          <td><b>${esc(cA.name)}</b><br><small class="muted">${esc(cA.category)}</small></td>
          <td><b>#${rankA}</b> (${cA.score}/100)<br><small class="muted">${esc(cA.market_balance)}</small></td>
          <td><b>#${cB.rank}</b> (${cB.score}/100)<br><small class="muted">${esc(cB.market_balance)}</small></td>
          <td style="color:${diffColor}; font-weight:700;">${diffLabel} pts</td>
        </tr>
      `;
    }).join("");

    out.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Candidate Crop</th>
            <th>Scenario A (# Rank &amp; Score)</th>
            <th>Scenario B (# Rank &amp; Score)</th>
            <th>Score Shift</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
      <div style="padding:14px; background:#faf5ee; border-top:1px solid var(--line); font-size:11px; color:var(--brown);">
        <b>Key Difference:</b> Scenario A tests <i>${esc(scA.badge)}</i> vs Scenario B <i>${esc(scB.badge)}</i>. Notice how suitability and budget constraints re-balance candidate crops.
      </div>
    `;
  } catch (e) {
    out.innerHTML = `<p class="risk">Comparison failed: ${esc(e.message)}</p>`;
  }
}

// ---------------------------------------------------------------------------
// Crop Analyzer & Soil Visual Tone
// ---------------------------------------------------------------------------
function renderPublicOrUserAnalyzer() {
  const container = document.getElementById("analyzer-container");
  if (!container) return;
  renderScenarioChipsContainers();
  renderAnalyzer(container);
}

function renderAnalyzer(container) {
  if (!container) return;
  const f = currentFarm || {};

  container.innerHTML = `
    <form id="analyze-form" class="panel">
      <div class="panel-head">
        <div>
          <div class="eyebrow">YOUR FARM CONDITIONS</div>
          <h3>Input Farm &amp; Soil Parameters</h3>
          <p class="muted">Inputs recalculate in real-time. Economics scale automatically for entered land area.</p>
        </div>
        <button type="submit" class="btn btn-primary">Recalculate Analysis ↗</button>
      </div>

      <div class="form-two" style="margin-top:16px;">
        <label>Land Area (Acres)
          <input name="area_acres" type="number" min="0.05" max="1000" step="0.05" value="${f.area_acres ?? 1.0}" required>
        </label>
        <label>Cultivation Budget (₹ Total)
          <input name="budget_inr" type="number" min="0" step="500" value="${f.budget_inr ?? 25000}" required>
        </label>
        <label>Soil Type
          <select name="soil_type">
            ${["Unknown", "Black soil", "Sandy loam", "Loamy", "Clay loam", "Red soil"].map(x => `<option ${(f.soil_type === x) ? "selected" : ""}>${x}</option>`).join("")}
          </select>
        </label>
        <label>Soil pH (Tested Lab Value)
          <input name="soil_ph" type="number" min="0" max="14" step="0.1" value="${f.soil_ph ?? ""}" placeholder="e.g. 6.8 (leave blank if unknown)">
        </label>
        <label>Irrigation Access
          <select name="irrigation">
            ${["Rain-fed", "Borewell", "Canal", "Drip", "Sprinkler", "None"].map(x => `<option ${(f.irrigation === x) ? "selected" : ""}>${x}</option>`).join("")}
          </select>
        </label>
        <label>Water Availability
          <select name="water_availability">
            ${["Reliable", "Seasonal / uncertain", "Limited", "No irrigation"].map(x => `<option ${(f.water_availability === x) ? "selected" : ""}>${x}</option>`).join("")}
          </select>
        </label>
        <label>Target Growing Season
          <select name="season">
            ${["Kharif", "Rabi", "Summer"].map(x => `<option ${(f.season === x) ? "selected" : ""}>${x}</option>`).join("")}
          </select>
        </label>
        <label>Market Analysis Mode
          <select name="market_mode">
            <option value="hybrid" selected>Hybrid (Platform + Demo Fallback)</option>
            <option value="platform_only">Strict Platform-Only (FasalSense Records)</option>
          </select>
        </label>
      </div>

      <!-- Soil Photo Preview & Visual Tone Analysis -->
      <div style="background:#faf5ee; border:1px solid var(--line); border-radius:12px; padding:18px; margin:20px 0;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <b style="font-size:13px; color:var(--maroon-dark);">📷 Soil Photo Upload (Experimental Visual Analysis)</b>
          <span style="font-size:10px; background:#ede0d0; color:var(--brown); padding:3px 8px; border-radius:12px;">Experimental Visual Inspection Only</span>
        </div>
        <input id="soil-photo" type="file" accept="image/*" style="margin-top:10px;">
        <div id="soil-photo-preview" class="field-help" style="margin-top:10px;">
          This is an <b>experimental visual analysis aid only</b>. A smartphone photograph can inspect surface color tone and texture, but <b>does not and cannot measure exact chemical pH, Nitrogen (N), Phosphorus (P), or Potassium (K)</b>. Please enter verified laboratory measurements from your official government Soil Health Card in the fields above.
        </div>
      </div>

      <div style="display:flex; gap:12px; align-items:center;">
        <button class="btn btn-primary" type="submit">Run 5-Factor Analysis ↗</button>
        <button class="btn btn-outline" type="button" onclick="saveAsFarmProfile()">Save Inputs to Farm Profile</button>
      </div>
    </form>

    <div id="analysis-results"></div>
  `;

  setupSoilPhotoPreview();
  setupLiveFormRecalculate();

  // Run initial analysis
  document.getElementById("analyze-form")?.requestSubmit();
}

function setupSoilPhotoPreview() {
  const photoInput = document.getElementById("soil-photo");
  const preview = document.getElementById("soil-photo-preview");
  if (!photoInput || !preview) return;

  photoInput.addEventListener("change", () => {
    const file = photoInput.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      preview.textContent = "Please select a valid image file.";
      return;
    }

    const reader = new FileReader();
    reader.onload = e => {
      const img = new Image();
      img.onload = () => {
        // Off-screen canvas to extract average color tone
        const canvas = document.createElement("canvas");
        canvas.width = 40;
        canvas.height = 40;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0, 40, 40);
        const data = ctx.getImageData(0, 0, 40, 40).data;
        let r = 0, g = 0, b = 0;
        for (let i = 0; i < data.length; i += 4) {
          r += data[i]; g += data[i + 1]; b += data[i + 2];
        }
        const count = data.length / 4;
        r = Math.round(r / count);
        g = Math.round(g / count);
        b = Math.round(b / count);

        // Classify visual tone
        let toneLabel = "Neutral loam tone";
        if (r < 90 && g < 80 && b < 70) {
          toneLabel = "Deep dark brown/black tone — visually consistent with Black cotton soil (Vertisols) common in Pune.";
        } else if (r > 130 && r > g * 1.2) {
          toneLabel = "Reddish tint — visually consistent with Alfisols / Red gravelly loams.";
        } else if (r > 140 && g > 130) {
          toneLabel = "Pale light tone — visually consistent with Sandy or alluvial soil.";
        }

        preview.innerHTML = `
          <div style="display:flex; gap:16px; align-items:center; margin-top:10px;">
            <img src="${e.target.result}" alt="Soil specimen" style="width:110px; height:85px; object-fit:cover; border-radius:8px; border:1px solid var(--line);">
            <div>
              <div style="display:flex; align-items:center; gap:8px;">
                <span style="display:inline-block; width:14px; height:14px; border-radius:3px; background:rgb(${r},${g},${b}); border:1px solid #999;"></span>
                <b>Visual Tone:</b> ${esc(toneLabel)}
              </div>
              <small class="muted" style="display:block; margin-top:4px;">
                <b>Academic Honesty Boundary:</b> Visual inspection cannot replace chemical soil testing. Tested pH &amp; NPK values must be entered manually from laboratory Soil Health Cards.
              </small>
            </div>
          </div>
        `;
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  });
}

function setupLiveFormRecalculate() {
  const form = document.getElementById("analyze-form");
  if (!form) return;
  let timer;
  form.querySelectorAll('input:not([type="file"]), select').forEach(el => {
    el.addEventListener(el.tagName === "SELECT" ? "change" : "input", () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        form.requestSubmit();
      }, 500);
    });
  });

  form.addEventListener("submit", async e => {
    e.preventDefault();
    const f = new FormData(form);
    const obj = {
      area_acres: Number(f.get("area_acres")),
      budget_inr: Number(f.get("budget_inr")),
      soil_ph: f.get("soil_ph") === "" ? null : Number(f.get("soil_ph")),
      soil_type: f.get("soil_type"),
      irrigation: f.get("irrigation"),
      water_availability: f.get("water_availability"),
      season: f.get("season"),
      market_mode: f.get("market_mode") || "hybrid",
      scenario_id: activeScenarioId
    };

    const out = document.getElementById("analysis-results");
    if (!out) return;
    out.innerHTML = '<div class="panel">Recalculating multi-factor crop recommendations…</div>';

    try {
      const data = await api("/api/analyze", { method: "POST", body: JSON.stringify(obj) });
      renderAnalysisCards(data, out);
    } catch (err) {
      out.innerHTML = `<div class="panel form-msg">${esc(err.message)}</div>`;
    }
  });
}

async function saveAsFarmProfile() {
  if (!currentUser || currentUser.role !== "farmer") {
    toast("Please log in as a farmer to save your farm profile.");
    return showPage("login");
  }
  const form = document.getElementById("analyze-form");
  if (!form) return;
  const f = new FormData(form);
  const payload = {
    area_acres: Number(f.get("area_acres")),
    budget_inr: Number(f.get("budget_inr")),
    soil_ph: f.get("soil_ph") === "" ? null : Number(f.get("soil_ph")),
    soil_type: f.get("soil_type"),
    irrigation: f.get("irrigation"),
    water_availability: f.get("water_availability"),
    season: f.get("season"),
    current_crop: currentFarm?.current_crop || "Not entered",
    nitrogen: currentFarm?.nitrogen || null,
    phosphorus: currentFarm?.phosphorus || null,
    potassium: currentFarm?.potassium || null
  };
  try {
    currentFarm = await api("/api/farm", { method: "PUT", body: JSON.stringify(payload) });
    toast("Farm profile updated.");
  } catch (e) {
    toast("Failed to save farm: " + e.message);
  }
}

// ---------------------------------------------------------------------------
// Render Analysis Cards with 5-Factor Score Breakdown
// ---------------------------------------------------------------------------
function renderAnalysisCards(data, container) {
  const items = data.recommendations || [];
  if (!items.length) {
    container.innerHTML = '<div class="panel"><p class="muted">No candidate crops found.</p></div>';
    return;
  }

  const scenarioBanner = data.scenario_applied ? `
    <div class="scenario-focus-card" style="margin:20px 0;">
      <div class="scenario-focus-icon">🧪</div>
      <div class="scenario-focus-body">
        <span class="scenario-focus-badge">ACTIVE TEST SCENARIO</span>
        <b>${esc(data.scenario_applied)}</b>
        <p>${esc(data.scenario_pedagogical_focus || "")}</p>
      </div>
    </div>
  ` : '';

  const isZeroBudget = items.length > 0 && items.every(c => (c.score_breakdown?.budget_score === 0 && !c.suitability_flags?.affordable && (c.risks || []).some(r => r.includes("ZERO WORKING CAPITAL"))));

  const zeroBudgetBanner = isZeroBudget ? `
    <div class="notice" style="margin:20px 0; background:#fdf0e6; border:1px solid #f0c3a8; color:#a84e27;">
      <span>⚠️</span>
      <div>
        <b>Zero Working Capital Specified:</b>
        <p>You entered a working capital budget of ₹0. All crops require capital investment and are marked unaffordable. Please enter your estimated working capital to see tailored budget scores.</p>
      </div>
    </div>
  ` : '';

  const headerNotice = `
    <div class="notice" style="margin:20px 0;">
      <span>ⓘ</span>
      <div>
        <b>Transparent 5-Factor Prototype Scoring:</b>
        <p>${esc(data.method)} Local crop supply vs retailer demand carries a bounded 15-point component to detect gluts without overriding agronomic suitability.</p>
        <p style="margin-top:6px; font-size:11px; color:var(--muted);"><b>Feature Boundaries:</b> Open-Meteo 7-day weather forecast and soil N/P/K nutrient fields are contextual advisories and official Soil Health Card records; they are not currently factored into the 5-factor ranking. Soil photo upload is strictly an experimental visual tone aid.</p>
      </div>
    </div>
  `;

  const cardsHtml = items.map((c, idx) => {
    const bd = c.score_breakdown || { season_score: 20, water_score: 15, soil_score: 15, budget_score: 15, market_score: 10, total: c.score };
    const market = c;

    // Market status pill class
    let pillClass = "balance-unknown";
    if (c.market_balance === "Low supply relative to demand") pillClass = "balance-gap";
    else if (c.market_balance === "High supply relative to demand") pillClass = "balance-surplus";
    else if (c.market_balance === "Supply and demand broadly balanced") pillClass = "balance-balanced";

    // Affordability badge
    let budgetPillHtml = '<span class="balance-pill balance-gap" style="font-size:10px; padding:2px 8px;">Within Budget</span>';
    if (!c.suitability_flags?.affordable) {
      if (c.suitability_flags?.budget_stretch) {
        budgetPillHtml = '<span class="balance-pill" style="font-size:10px; padding:2px 8px; background:#fff3e0; color:#b26a1b; border:1px solid #f0c58e;">Over Budget (Stretch)</span>';
      } else {
        budgetPillHtml = '<span class="balance-pill balance-surplus" style="font-size:10px; padding:2px 8px;">Unaffordable</span>';
      }
    }

    // Score badge style
    const scoreColorClass = c.score >= 75 ? "" : (c.score >= 50 ? "amber" : "amber");

    return `
      <div class="crop-result">
        <div class="crop-result-head">
          <div>
            <div class="eyebrow">OPTION ${idx + 1} · ${esc(c.category)} · ${esc(c.season)}</div>
            <h3>${esc(c.name)}</h3>
            <p class="muted" style="margin-bottom:0;">${esc(c.note)}</p>
          </div>
          <div class="score-badge ${scoreColorClass}">
            <b>${c.score}</b> / 100 prototype score
          </div>
        </div>

        <!-- 5-Factor Score Breakdown Bar -->
        <div class="score-breakdown-card">
          <div class="score-breakdown-title">
            <span>SUITABILITY BREAKDOWN (OUT OF 100 POINTS)</span>
            <span>Total: <b>${c.score}/100</b></span>
          </div>
          <div class="score-multi-bar">
            <div class="score-bar-segment seg-season" style="width:${(bd.season_score / 100) * 100}%" title="Season: ${bd.season_score}/25"></div>
            <div class="score-bar-segment seg-water" style="width:${(bd.water_score / 100) * 100}%" title="Water: ${bd.water_score}/20"></div>
            <div class="score-bar-segment seg-soil" style="width:${(bd.soil_score / 100) * 100}%" title="Soil & pH: ${bd.soil_score}/20"></div>
            <div class="score-bar-segment seg-budget" style="width:${(bd.budget_score / 100) * 100}%" title="Budget: ${bd.budget_score}/20"></div>
            <div class="score-bar-segment seg-market" style="width:${(bd.market_score / 100) * 100}%" title="Market: ${bd.market_score}/15"></div>
          </div>
          <div class="score-legend">
            <div class="legend-item"><span class="legend-dot" style="background:#3b7a57;"></span><div><b>Season:</b> ${bd.season_score}/25</div></div>
            <div class="legend-item"><span class="legend-dot" style="background:#3c78a0;"></span><div><b>Water:</b> ${bd.water_score}/20</div></div>
            <div class="legend-item"><span class="legend-dot" style="background:#8a6240;"></span><div><b>Soil/pH:</b> ${bd.soil_score}/20</div></div>
            <div class="legend-item"><span class="legend-dot" style="background:#b05c2d;"></span><div><b>Budget:</b> ${bd.budget_score}/20</div></div>
            <div class="legend-item"><span class="legend-dot" style="background:#7c2d82;"></span><div><b>Market:</b> ${bd.market_score}/15</div></div>
          </div>
        </div>

        <!-- Economics Metric Row -->
        <div class="metric-row">
          <div class="metric">
            <small>Estimated Cultivation Cost</small>
            <b>${fmt(c.cost_inr)}</b>
            <div style="margin-top:4px;">${budgetPillHtml}</div>
          </div>
          <div class="metric">
            <small>Illustrative Gross Revenue</small>
            <b>${fmt(c.revenue_inr)}</b>
            <small style="margin-top:4px; font-weight:normal; text-transform:none; color:var(--muted);">${esc(c.price_assumption_note || 'Static baseline benchmark rate')}</small>
          </div>
          <div class="metric">
            <small>Net Operating Margin</small>
            <b>${fmt(c.profit_inr)}</b>
            <small style="margin-top:4px; font-weight:normal; text-transform:none;">Range: ${fmt(c.conservative_profit_inr)} to ${fmt(c.optimistic_profit_inr)}</small>
          </div>
        </div>

        <div class="metric-row">
          <div class="metric">
            <small>Reference Yield</small>
            <b>${c.yield_quintal} q</b>
          </div>
          <div class="metric">
            <small>Wholesale Benchmark Price</small>
            <b>${fmt(c.price_per_quintal)}/q <small style="display:inline; font-size:11px;">(${fmt(c.price_per_kg)}/kg)</small></b>
          </div>
          <div class="metric">
            <small>Water &amp; Duration</small>
            <b>${esc(c.water_need)} · ${c.duration_days} days</b>
          </div>
        </div>

        <!-- Local Supply vs Buyer Demand Balance Card -->
        <div class="market-balance-panel">
          <div class="eyebrow">LOCAL CROP SUPPLY VS RETAILER DEMAND (30-DAY WINDOW)</div>
          <div class="metric-row" style="margin:10px 0;">
            <div class="metric">
              <small>${c.market_source_type === "platform_activity" ? "FasalSense Listed Supply" : "Available Local Supply"}</small>
              <b>${c.market_supply_kg == null ? "—" : Number(c.market_supply_kg).toLocaleString("en-IN") + " kg"}</b>
            </div>
            <div class="metric">
              <small>${c.market_source_type === "platform_activity" ? "Retailer Inquiry Volume" : "Recorded Buyer Demand"}</small>
              <b>${c.market_demand_kg == null ? "—" : Number(c.market_demand_kg).toLocaleString("en-IN") + " kg"}</b>
            </div>
            <div class="metric">
              <small>Market Balance Status</small>
              <div style="margin-top:4px;">
                <span class="balance-pill ${pillClass}">${esc(c.market_balance || "Unknown")}</span>
              </div>
            </div>
          </div>
          <p class="field-help" style="margin-top:8px;">
            <b>Market Evidence Status:</b> ${esc(c.market_data_status)}. Wholesale price trends benchmarked from ${esc(c.market_benchmark_market || "Pune APMC")} (${esc(c.market_benchmark_historical_range || "N/A")}).
          </p>
        </div>

        <p class="good"><b>Why this crop scores:</b> ${c.reasons.map(esc).join("; ")}.</p>
        <p class="risk"><b>Risks &amp; Constraints:</b> ${c.risks.map(esc).join("; ")}.</p>

        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:14px; padding-top:10px; border-top:1px solid var(--line-light); font-size:11px; color:var(--muted);">
          <span><b>Evidence Scope:</b> ${esc(c.evidence_scope)}</span>
          ${currentUser?.role === "farmer" ? `<button class="btn btn-outline btn-sm" onclick="quickListCrop('${esc(c.name)}', ${c.price_per_kg})">List ${esc(c.name)} in Marketplace →</button>` : ''}
        </div>
      </div>
    `;
  }).join("");

  container.innerHTML = scenarioBanner + zeroBudgetBanner + headerNotice + cardsHtml;
}

// ---------------------------------------------------------------------------
// Marketplace & Listings
// ---------------------------------------------------------------------------
async function loadListings() {
  const grid = document.getElementById("listing-grid");
  if (!grid) return;
  const search = document.getElementById("market-search")?.value || "";
  const max = document.getElementById("market-max")?.value || "";
  let url = "/api/listings?q=" + encodeURIComponent(search);
  if (max) url += "&max_price=" + encodeURIComponent(max);

  try {
    const rows = await api(url);
    if (!rows.length) {
      grid.innerHTML = '<div class="panel" style="grid-column:1/-1;"><h3>No matching listings found</h3><p class="muted">As farmers publish produce in Chharoli, available listings will appear here.</p></div>';
      return;
    }
    grid.innerHTML = rows.map(x => `
      <div class="listing-card">
        ${x.is_demo ? '<span class="demo-label">DEMO LISTING · NOT VERIFIED OFFER</span>' : ''}
        <div class="listing-art">${cropEmoji(x.crop_name)}</div>
        <h3>${esc(x.crop_name)} ${x.variety ? `<small style="font-size:12px; font-weight:normal; color:var(--muted);">(${esc(x.variety)})</small>` : ''}</h3>
        <div class="price">${fmt(x.price_per_kg)} <small>/ kg</small></div>
        <div class="listing-meta">
          <span><b>${Number(x.quantity_kg).toLocaleString("en-IN")} kg</b> available</span>
          <span>⌖ Chharoli Budruk</span>
        </div>
        <p class="muted">${esc(x.description || "Farm-fresh produce listed by local farmer.")}</p>
        <p class="field-help" style="margin-bottom:14px;">Listed by <b>${esc(x.farmer_name)}</b> · Grade: ${esc(x.quality)}</p>
        ${currentUser?.role === "retailer"
          ? `<button class="btn btn-primary full" onclick="openInquiryModal(${x.id}, '${esc(x.crop_name)}', ${x.quantity_kg}, ${x.price_per_kg}, '${esc(x.farmer_name)}')">Submit Purchase Inquiry →</button>`
          : (currentUser?.role === "farmer"
            ? `<button class="btn btn-outline full" disabled>Your Farmer Workspace</button>`
            : `<button class="btn btn-outline full" onclick="showPage('login')">Log in as Retailer to Inquire</button>`
          )}
      </div>
    `).join("");
  } catch (e) {
    grid.innerHTML = '<div class="panel" style="grid-column:1/-1;">Could not load listings. Please try again.</div>';
  }
}

function cropEmoji(n) {
  n = (n || "").toLowerCase();
  if (n.includes("bajra") || n.includes("millet")) return "🌾";
  if (n.includes("onion")) return "🧅";
  if (n.includes("maize")) return "🌽";
  if (n.includes("chickpea") || n.includes("gram") || n.includes("harbhara")) return "🌱";
  if (n.includes("paddy") || n.includes("rice")) return "🌾";
  if (n.includes("tomato")) return "🍅";
  if (n.includes("potato")) return "🥔";
  if (n.includes("soybean")) return "🫘";
  if (n.includes("sugarcane")) return "🎋";
  if (n.includes("cotton")) return "☁️";
  return "🥬";
}

// ---------------------------------------------------------------------------
// Interactive Inquiry Modal
// ---------------------------------------------------------------------------
function openInquiryModal(listingId, cropName, maxQty, pricePerKg, farmerName) {
  const modal = document.getElementById("inquiry-modal");
  if (!modal) return;
  document.getElementById("modal-listing-id").value = listingId;
  document.getElementById("modal-listing-title").textContent = `${cropName} (₹${pricePerKg}/kg)`;
  document.getElementById("modal-listing-meta").textContent = `Offered by ${farmerName} · Max available: ${Number(maxQty).toLocaleString("en-IN")} kg`;

  const qtyInput = document.getElementById("modal-quantity");
  qtyInput.max = maxQty;
  qtyInput.value = Math.min(100, maxQty);

  const calcEl = document.getElementById("modal-price-calc");
  const updateCalc = () => {
    const q = Number(qtyInput.value || 0);
    calcEl.innerHTML = `Estimated Purchase Value: <b>₹${Number(q * pricePerKg).toLocaleString("en-IN")}</b> (${q} kg @ ₹${pricePerKg}/kg)`;
  };
  qtyInput.oninput = updateCalc;
  updateCalc();

  modal.classList.add("show");
}

function closeInquiryModal() {
  document.getElementById("inquiry-modal")?.classList.remove("show");
}

document.getElementById("inquiry-modal-form")?.addEventListener("submit", async e => {
  e.preventDefault();
  const listingId = Number(document.getElementById("modal-listing-id").value);
  const qty = Number(document.getElementById("modal-quantity").value);
  const msg = document.getElementById("modal-message").value;

  try {
    const res = await api("/api/inquiries", {
      method: "POST",
      body: JSON.stringify({ listing_id: listingId, quantity_kg: qty, message: msg })
    });
    closeInquiryModal();
    toast(res.message || "Purchase inquiry sent to the farmer.");
    if (currentUser?.role === "retailer") dashView("inquiries");
  } catch (err) {
    toast("Error: " + err.message);
  }
});

// ---------------------------------------------------------------------------
// Produce Listing Creation Modal
// ---------------------------------------------------------------------------
function showListingFormModal() {
  document.getElementById("listing-modal")?.classList.add("show");
}
function closeListingModal() {
  document.getElementById("listing-modal")?.classList.remove("show");
}

document.getElementById("listing-modal-form")?.addEventListener("submit", async e => {
  e.preventDefault();
  const f = new FormData(e.target);
  const payload = {
    crop_name: f.get("crop_name"),
    variety: f.get("variety") || "",
    quantity_kg: Number(f.get("quantity_kg")),
    price_per_kg: Number(f.get("price_per_kg")),
    available_date: f.get("available_date") || "Ready now",
    quality: f.get("quality") || "Standard quality",
    description: f.get("description") || ""
  };
  try {
    await api("/api/listings", { method: "POST", body: JSON.stringify(payload) });
    closeListingModal();
    e.target.reset();
    toast("Produce listing published successfully.");
    loadListings();
    if (currentUser?.role === "farmer") dashView("listings");
  } catch (err) {
    toast("Listing failed: " + err.message);
  }
});

function quickListCrop(cropName, pricePerKg) {
  showListingFormModal();
  const form = document.getElementById("listing-modal-form");
  if (form) {
    form.querySelector('input[name="crop_name"]').value = cropName;
    form.querySelector('input[name="price_per_kg"]').value = pricePerKg;
  }
}

// ---------------------------------------------------------------------------
// Community & Supply/Demand Tables
// ---------------------------------------------------------------------------
async function loadCommunity(detail = false) {
  try {
    const d = await api("/api/community");
    const types = d.current_crops.length;
    const statsHtml = `
      <div class="stat-card"><span>Registered Farmers</span><b>${d.farmers_registered}</b><small>FasalSense accounts</small></div>
      <div class="stat-card"><span>Farms Profiled</span><b>${d.farms_profiled}</b><small>With saved soil/budget</small></div>
      <div class="stat-card"><span>Active Listings</span><b>${d.active_listings}</b><small>Available produce offers</small></div>
      <div class="stat-card"><span>Crop Types Reported</span><b>${types}</b><small>Distinct farm crops</small></div>
    `;
    const a = document.getElementById("community-stats");
    if (a) a.innerHTML = statsHtml;

    const bars = document.getElementById("crop-community");
    if (bars) {
      if (!d.current_crops.length) {
        bars.innerHTML = '<p class="muted">No current crop records entered yet.</p>';
      } else {
        const max = Math.max(...d.current_crops.map(x => x.farmers_reporting));
        bars.innerHTML = d.current_crops.map(x => `
          <div class="crop-bar-row">
            <b>${esc(x.crop)}</b>
            <div class="bar-track"><div class="bar-fill" style="width:${(x.farmers_reporting / max) * 100}%"></div></div>
            <span>${x.farmers_reporting} farmer(s)</span>
          </div>
        `).join("");
      }
    }

    loadMarketBalance();
    loadApmcBenchmarks();
  } catch (e) {
    console.warn(e);
  }
}

async function loadMarketBalance() {
  const el = document.getElementById("market-balance-table");
  if (!el) return;
  const mode = document.getElementById("market-mode-select")?.value || "hybrid";

  try {
    const d = await api("/api/market/supply-demand?mode=" + encodeURIComponent(mode));
    const rows = d.signals || [];
    el.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Candidate Crop</th>
            <th>Available Supply</th>
            <th>Retailer Demand</th>
            <th>Supply/Demand Ratio</th>
            <th>Balance Assessment</th>
            <th>Evidence Scope</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(x => {
            let pillClass = "balance-unknown";
            if (x.balance_label === "Low supply relative to demand") pillClass = "balance-gap";
            else if (x.balance_label === "High supply relative to demand") pillClass = "balance-surplus";
            else if (x.balance_label === "Supply and demand broadly balanced") pillClass = "balance-balanced";

            const isDemo = x.source_type === "illustrative_demo";
            const isPlatform = x.source_type === "platform_activity";
            const evidenceLabel = isPlatform ? "FasalSense Platform Records (30d)" : (isDemo ? "Illustrative Simulation" : "Insufficient Data");

            return `
              <tr>
                <td><b>${esc(x.crop_name)}</b></td>
                <td>${x.supply_kg == null ? "—" : Number(x.supply_kg).toLocaleString("en-IN") + " kg"}<br><small class="muted">${x.platform_supply_listings || 0} listings</small></td>
                <td>${x.demand_kg == null ? "—" : Number(x.demand_kg).toLocaleString("en-IN") + " kg"}<br><small class="muted">${x.platform_demand_inquiries || 0} inquiries</small></td>
                <td>${x.supply_demand_ratio ? Number(x.supply_demand_ratio).toFixed(2) : "—"}</td>
                <td><span class="balance-pill ${pillClass}">${esc(x.balance_label)}</span></td>
                <td><small>${esc(evidenceLabel)}</small></td>
              </tr>
            `;
          }).join("")}
        </tbody>
      </table>
      <div style="padding:12px; background:#faf5ee; font-size:11px; color:var(--brown); border-top:1px solid var(--line);">
        <b>Methodology:</b> Window: ${d.window_days || 30} days. ${esc(d.note || "")}
      </div>
    `;
  } catch (e) {
    el.innerHTML = '<p class="risk">Market balance data temporarily unavailable.</p>';
  }
}

async function loadApmcBenchmarks() {
  const el = document.getElementById("apmc-benchmarks-table");
  if (!el) return;
  try {
    const d = await api("/api/market/benchmarks");
    const rows = d.benchmarks || [];
    el.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Commodity</th>
            <th>Benchmark APMC Market</th>
            <th>Modal Price (₹/q)</th>
            <th>12-Month Volatility Range</th>
            <th>Primary Sowing/Arrival Season</th>
            <th>Price Trend / Dynamics</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(x => `
            <tr>
              <td><b>${esc(x.crop_name)}</b></td>
              <td>${esc(x.market)}</td>
              <td><b>₹${Number(x.benchmark_price_q).toLocaleString("en-IN")}</b> / q<br><small class="muted">(₹${Number(x.benchmark_price_kg).toFixed(1)}/kg)</small></td>
              <td>₹${x.historical_min_q} – ₹${x.historical_max_q} / q</td>
              <td>${esc(x.arrival_season)}</td>
              <td><small>${esc(x.price_trend_label)}</small></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
      <div style="padding:12px; background:#faf5ee; font-size:11px; color:var(--brown); border-top:1px solid var(--line);">
        <b>Source:</b> ${esc(d.source)}. Wholesale modal auctions in Pune district APMCs; not village-gate farm purchases.
      </div>
    `;
  } catch (e) {
    el.innerHTML = '<p class="muted">APMC benchmarks loading…</p>';
  }
}

// ---------------------------------------------------------------------------
// Dashboard Views & Workspace
// ---------------------------------------------------------------------------
async function openDashboard() {
  if (!currentUser) return showPage("login");
  document.getElementById("side-name").textContent = currentUser.name;
  document.getElementById("side-role").textContent = currentUser.role === "farmer" ? "Farmer Workspace" : "Retailer Workspace";
  document.getElementById("user-avatar").textContent = currentUser.name.slice(0, 1).toUpperCase();

  // Role permissions UI
  const farmBtn = document.getElementById("side-farm-btn");
  const analyzerBtn = document.getElementById("side-analyzer-btn");
  const listBtn = document.getElementById("side-listings-btn");
  const histBtn = document.getElementById("side-history-btn");

  if (currentUser.role === "retailer") {
    if (farmBtn) farmBtn.style.display = "none";
    if (analyzerBtn) analyzerBtn.style.display = "none";
    if (listBtn) listBtn.style.display = "none";
    if (histBtn) histBtn.style.display = "none";
  } else {
    if (farmBtn) farmBtn.style.display = "flex";
    if (analyzerBtn) analyzerBtn.style.display = "flex";
    if (listBtn) listBtn.style.display = "flex";
    if (histBtn) histBtn.style.display = "flex";
  }

  try {
    const d = await api("/api/auth/me");
    currentFarm = d.farm;
  } catch (e) {
    logout();
    return;
  }

  showPage("dashboard");
  dashView("overview");
}

async function dashView(view) {
  if (!currentUser) return showPage("login");
  if (currentUser.role === "retailer" && ["farm", "analyzer", "listings", "history"].includes(view)) {
    view = "market";
  }

  document.querySelectorAll(".side-link[data-view]").forEach(b => {
    b.classList.toggle("active", b.dataset.view === view);
  });

  if (view === "overview") {
    const isFarmer = currentUser.role === "farmer";
    document.getElementById("dash-title").textContent = `Namaste, ${currentUser.name.split(" ")[0]}`;
    document.getElementById("dash-subtitle").textContent = isFarmer
      ? "Welcome to your Chharoli farm management and decision workspace."
      : "Discover local farmer produce, compare prices, and manage purchase inquiries.";

    document.getElementById("dash-content").innerHTML = `
      <div class="dash-grid">
        <div class="weather-card">
          <div class="eyebrow" style="color:#e5b89e;">LOCAL WEATHER FORECAST · CHHAROLI</div>
          <h3>7-Day Agronomic Weather</h3>
          <div id="weather-main" class="weather-loading">Fetching current weather…</div>
          <div id="weather-days"></div>
          <div class="weather-metrics" id="weather-metrics"></div>
        </div>
        <div class="panel">
          <div class="panel-head">
            <div>
              <h3>Community Snapshot</h3>
              <p class="muted">Active prototype statistics</p>
            </div>
            <span class="status-badge">App Data</span>
          </div>
          <div id="dash-community" class="mini-list">Loading…</div>
          <button class="btn btn-outline full" style="margin-top:14px;" onclick="dashView('community')">Inspect Supply &amp; Demand →</button>
        </div>
      </div>

      <div class="panel" style="margin-top:22px;">
        <div class="panel-head">
          <div>
            <h3>${isFarmer ? "My Farm Quick Actions" : "Retailer Quick Actions"}</h3>
            <p class="muted">${isFarmer ? "Evaluate multi-crop options or publish newly harvested produce." : "Explore available produce listings from farmers in Chharoli."}</p>
          </div>
        </div>
        <div style="display:flex; gap:12px; flex-wrap:wrap; margin-top:14px;">
          ${isFarmer ? `
            <button class="btn btn-primary" onclick="dashView('analyzer')">Launch Crop Analyzer ↗</button>
            <button class="btn btn-outline" onclick="dashView('farm')">Edit Farm Profile ♧</button>
            <button class="btn btn-outline" onclick="showListingFormModal()">+ List New Produce 🧺</button>
          ` : `
            <button class="btn btn-primary" onclick="dashView('market')">Browse Marketplace 🧺</button>
            <button class="btn btn-outline" onclick="dashView('inquiries')">View My Inquiries ✉</button>
          `}
        </div>
      </div>
    `;
    loadWeather();
    loadCommunityForDash();
  } else if (view === "farm") {
    renderFarmForm();
  } else if (view === "analyzer") {
    document.getElementById("dash-title").textContent = "Crop Suitability Analyzer";
    document.getElementById("dash-subtitle").textContent = "Compare candidate crops using farm affordability, water constraints, soil pH, and local market balance.";
    renderAnalyzer(document.getElementById("dash-content"));
  } else if (view === "scenarios") {
    document.getElementById("dash-title").textContent = "Scenarios Laboratory";
    document.getElementById("dash-subtitle").textContent = "Test the 7 required evaluation situations and inspect live ranking recalculations.";
    document.getElementById("dash-content").innerHTML = `
      <div class="scenario-bar">
        <div class="scenario-bar-title" style="margin-bottom:12px;"><b>Select a Test Situation:</b></div>
        <div class="scenario-chips" id="dash-scenario-chips"></div>
      </div>
      <div id="dash-scenario-focus"></div>
      <div id="dash-scenario-results" style="margin-top:20px;"></div>
    `;
    renderScenarioChipsContainers();
    // Re-bind to dash containers
    document.getElementById("dash-scenario-chips").innerHTML = (await fetchScenarios()).map(sc => `
      <button type="button" class="scenario-chip ${activeScenarioId === sc.id ? 'active' : ''}" onclick="selectDashScenario('${sc.id}')">
        <b>${esc(sc.title)}</b>
        <small>${esc(sc.badge)}</small>
      </button>
    `).join("");
    if (allScenarios.length > 0) selectDashScenario(allScenarios[0].id);
  } else if (view === "community") {
    document.getElementById("dash-title").textContent = "Crop Supply vs Retailer Demand";
    document.getElementById("dash-subtitle").textContent = "Examine how local availability balances with buyer demand across candidate crops.";
    document.getElementById("dash-content").innerHTML = `
      <div class="panel">
        <div class="panel-head">
          <div>
            <h3>Crop Availability vs Buyer Requests</h3>
            <p class="muted">Ratios &lt; 0.75 indicate supply gaps; &gt; 1.25 indicate potential surplus competition.</p>
          </div>
          <select id="market-mode-select" onchange="loadMarketBalance()" style="width:auto; padding:6px 10px;">
            <option value="hybrid" selected>Hybrid (Demo Simulation Fallback)</option>
            <option value="platform_only">Platform-Only (FasalSense Records)</option>
          </select>
        </div>
        <div id="market-balance-table" class="table-wrap">Loading market balance…</div>
      </div>
      <div class="panel" style="margin-top:25px;">
        <div class="panel-head">
          <div><h3>Pune District Mandi Wholesale Benchmarks</h3><p class="muted">MSAMB &amp; AGMARKNET Pune APMC data</p></div>
        </div>
        <div id="apmc-benchmarks-table" class="table-wrap">Loading APMC benchmarks…</div>
      </div>
    `;
    loadMarketBalance();
    loadApmcBenchmarks();
  } else if (view === "market") {
    document.getElementById("dash-title").textContent = "Produce Marketplace";
    document.getElementById("dash-subtitle").textContent = "Browse active listings from Chharoli farmers.";
    document.getElementById("dash-content").innerHTML = `
      <div class="market-tools">
        <input id="market-search" placeholder="Search crop or variety…" oninput="loadListings()">
        <label>Max ₹/kg <input id="market-max" type="number" min="0" placeholder="Any" oninput="loadListings()"></label>
        ${currentUser.role === "farmer" ? '<button class="btn btn-primary" onclick="showListingFormModal()">+ List Produce</button>' : ''}
      </div>
      <div id="listing-grid" class="listing-grid"></div>
    `;
    loadListings();
  } else if (view === "listings") {
    document.getElementById("dash-title").textContent = "My Produce Listings";
    document.getElementById("dash-subtitle").textContent = "Manage harvest listings you have published in the Chharoli marketplace.";
    document.getElementById("dash-content").innerHTML = '<div id="my-listings" class="panel">Loading your listings…</div>';
    loadMyListings();
  } else if (view === "inquiries") {
    document.getElementById("dash-title").textContent = "Purchase Inquiries";
    document.getElementById("dash-subtitle").textContent = currentUser.role === "farmer"
      ? "Respond to retailer purchase inquiries received for your produce."
      : "Track the status of inquiries you have submitted to local farmers.";
    document.getElementById("dash-content").innerHTML = '<div id="inquiries-list" class="panel">Loading inquiries…</div>';
    loadInquiries();
  } else if (view === "history") {
    document.getElementById("dash-title").textContent = "My Analysis History";
    document.getElementById("dash-subtitle").textContent = "Review previous crop analysis runs saved for your farm.";
    document.getElementById("dash-content").innerHTML = '<div id="history-list" class="panel">Loading analysis history…</div>';
    loadAnalysisHistory();
  }
}

async function selectDashScenario(scId) {
  activeScenarioId = scId;
  const scenarios = await fetchScenarios();
  const sc = scenarios.find(x => x.id === scId);
  if (!sc) return;

  const focusEl = document.getElementById("dash-scenario-focus");
  if (focusEl) {
    focusEl.innerHTML = `
      <div class="scenario-focus-card">
        <div class="scenario-focus-icon">🧪</div>
        <div class="scenario-focus-body">
          <span class="scenario-focus-badge">${esc(sc.badge)}</span>
          <b>${esc(sc.title)}</b>
          <p>${esc(sc.description)}</p>
          <div style="margin-top:6px; font-size:11px; color:var(--maroon);"><b>Evaluation Focus:</b> ${esc(sc.pedagogical_focus)}</div>
        </div>
      </div>
    `;
  }
  const out = document.getElementById("dash-scenario-results");
  if (out) {
    out.innerHTML = '<div class="panel">Calculating scenario outputs…</div>';
    try {
      const d = await api("/api/analyze", { method: "POST", body: JSON.stringify({ ...sc.profile, scenario_id: sc.id }) });
      renderAnalysisCards(d, out);
    } catch (e) {
      out.innerHTML = `<p class="risk">Error: ${esc(e.message)}</p>`;
    }
  }
}

// ---------------------------------------------------------------------------
// Farmer Farm Profile Form
// ---------------------------------------------------------------------------
function renderFarmForm() {
  const f = currentFarm || {};
  document.getElementById("dash-title").textContent = "Farm Profile";
  document.getElementById("dash-subtitle").textContent = "Update farm land, soil test chemistry, and irrigation access.";

  document.getElementById("dash-content").innerHTML = `
    <form id="farm-form" class="panel">
      <div class="form-two">
        <label>Land Area (Acres)
          <input name="area_acres" type="number" min="0.05" step="0.05" value="${f.area_acres ?? 1.0}" required>
        </label>
        <label>Available Cultivation Budget (₹)
          <input name="budget_inr" type="number" min="0" step="500" value="${f.budget_inr ?? 25000}" required>
        </label>
        <label>Soil Texture Category
          <select name="soil_type">
            ${["Unknown", "Black soil", "Sandy loam", "Loamy", "Clay loam", "Red soil"].map(x => `<option ${(f.soil_type === x) ? "selected" : ""}>${x}</option>`).join("")}
          </select>
        </label>
        <label>Soil pH (Laboratory Tested)
          <input name="soil_ph" type="number" min="0" max="14" step="0.1" value="${f.soil_ph ?? ""}" placeholder="e.g. 7.2 (leave blank if unknown)">
        </label>
        <label>Nitrogen - N (kg/ha, optional)
          <input name="nitrogen" type="number" min="0" value="${f.nitrogen ?? ""}" placeholder="From Soil Health Card">
        </label>
        <label>Phosphorus - P (kg/ha, optional)
          <input name="phosphorus" type="number" min="0" value="${f.phosphorus ?? ""}" placeholder="From Soil Health Card">
        </label>
        <label>Potassium - K (kg/ha, optional)
          <input name="potassium" type="number" min="0" value="${f.potassium ?? ""}" placeholder="From Soil Health Card">
        </label>
        <label>Irrigation Infrastructure
          <select name="irrigation">
            ${["Rain-fed", "Borewell", "Canal", "Drip", "Sprinkler", "None"].map(x => `<option ${(f.irrigation === x) ? "selected" : ""}>${x}</option>`).join("")}
          </select>
        </label>
        <label>Water Availability
          <select name="water_availability">
            ${["Reliable", "Seasonal / uncertain", "Limited", "No irrigation"].map(x => `<option ${(f.water_availability === x) ? "selected" : ""}>${x}</option>`).join("")}
          </select>
        </label>
        <label>Current Crop Being Grown
          <input name="current_crop" value="${esc(f.current_crop ?? "Not entered")}" placeholder="e.g. Bajra, onion">
        </label>
        <label>Planned Sowing Season
          <select name="season">
            ${["Kharif", "Rabi", "Summer"].map(x => `<option ${(f.season === x) ? "selected" : ""}>${x}</option>`).join("")}
          </select>
        </label>
      </div>

      <p class="field-help" style="margin-top:16px;">
        <b>Laboratory Soil Testing Guidance:</b> Values for pH, N, P, and K should derive from physical Soil Health Card testing at the nearest Krishi Vigyan Kendra (KVK) or Taluka Agriculture Office in Pune.
      </p>

      <button class="btn btn-primary" type="submit" style="margin-top:14px;">Save Farm Profile →</button>
      <div id="farm-msg" class="form-msg"></div>
    </form>
  `;

  document.getElementById("farm-form").addEventListener("submit", async e => {
    e.preventDefault();
    const form = e.target;
    const fData = new FormData(form);
    const obj = {
      area_acres: Number(fData.get("area_acres")),
      budget_inr: Number(fData.get("budget_inr")),
      soil_ph: fData.get("soil_ph") === "" ? null : Number(fData.get("soil_ph")),
      nitrogen: fData.get("nitrogen") === "" ? null : Number(fData.get("nitrogen")),
      phosphorus: fData.get("phosphorus") === "" ? null : Number(fData.get("phosphorus")),
      potassium: fData.get("potassium") === "" ? null : Number(fData.get("potassium")),
      soil_type: fData.get("soil_type"),
      irrigation: fData.get("irrigation"),
      water_availability: fData.get("water_availability"),
      current_crop: fData.get("current_crop") || "Not entered",
      season: fData.get("season")
    };
    try {
      currentFarm = await api("/api/farm", { method: "PUT", body: JSON.stringify(obj) });
      document.getElementById("farm-msg").textContent = "Farm profile successfully saved.";
      toast("Farm profile saved.");
    } catch (err) {
      document.getElementById("farm-msg").textContent = err.message;
    }
  });
}

// ---------------------------------------------------------------------------
// Farmer Produce Listings Management
// ---------------------------------------------------------------------------
async function loadMyListings() {
  const el = document.getElementById("my-listings");
  if (!el) return;
  try {
    const rows = await api("/api/my-listings");
    if (!rows.length) {
      el.innerHTML = `
        <h3>No produce listings yet</h3>
        <p class="muted">Publish produce you have harvested to make it discoverable to nearby buyers.</p>
        <button class="btn btn-primary" style="margin-top:12px;" onclick="showListingFormModal()">+ Create First Listing</button>
      `;
      return;
    }
    el.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
        <span class="muted">${rows.length} total listing(s) posted</span>
        <button class="btn btn-primary btn-sm" onclick="showListingFormModal()">+ Post New Listing</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Produce</th>
              <th>Variety</th>
              <th>Quantity Available</th>
              <th>Asking Price</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            ${rows.map(x => `
              <tr>
                <td><b>${esc(x.crop_name)}</b></td>
                <td>${esc(x.variety || "—")}</td>
                <td><b>${Number(x.quantity_kg).toLocaleString("en-IN")} kg</b></td>
                <td><b>${fmt(x.price_per_kg)}</b> / kg</td>
                <td>
                  <span class="status-badge" style="${x.status === 'Active' ? '' : 'background:#eee; color:#666;'}">
                    ${esc(x.status)}
                  </span>
                </td>
                <td>
                  <select onchange="updateListingStatus(${x.id}, this.value)" style="width:auto; padding:4px 8px; font-size:11px;">
                    <option ${x.status === "Active" ? "selected" : ""}>Active</option>
                    <option ${x.status === "Paused" ? "selected" : ""}>Paused</option>
                    <option ${x.status === "Sold out" ? "selected" : ""}>Sold out</option>
                    <option ${x.status === "Archived" ? "selected" : ""}>Archived</option>
                  </select>
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  } catch (e) {
    el.innerHTML = `<p class="risk">Error: ${esc(e.message)}</p>`;
  }
}

async function updateListingStatus(id, newStatus) {
  try {
    await api(`/api/listings/${id}/status?status=${encodeURIComponent(newStatus)}`, { method: "PATCH" });
    toast("Listing status updated to " + newStatus);
    loadMyListings();
  } catch (e) {
    toast("Status update failed: " + e.message);
  }
}

// ---------------------------------------------------------------------------
// Inquiries (Farmer & Retailer Workflows)
// ---------------------------------------------------------------------------
async function loadInquiries() {
  const el = document.getElementById("inquiries-list");
  if (!el) return;
  try {
    const rows = await api("/api/inquiries");
    const badge = document.getElementById("inquiry-count-badge");
    if (badge) {
      const pendingCount = rows.filter(x => x.status === "Pending").length;
      if (pendingCount > 0) {
        badge.textContent = pendingCount;
        badge.style.display = "inline-block";
      } else {
        badge.style.display = "none";
      }
    }

    if (!rows.length) {
      el.innerHTML = `
        <h3>No inquiries recorded yet</h3>
        <p class="muted">${currentUser.role === "farmer" ? "Inquiries from retailers will appear here when buyers express purchase interest." : "Inquiries you submit for farmer listings will appear here with live response tracking."}</p>
      `;
      return;
    }

    const isFarmer = currentUser.role === "farmer";
    el.innerHTML = rows.map(x => {
      let statusStyle = "background:var(--amber-light); color:var(--amber); border:1px solid var(--amber-border);";
      if (x.status === "Accepted") statusStyle = "background:var(--green-light); color:var(--green); border:1px solid var(--green-border);";
      else if (x.status === "Declined") statusStyle = "background:#fde8e8; color:#9c2727; border:1px solid #f3bcbc;";
      else if (x.status === "Completed") statusStyle = "background:#e8f0fe; color:#1a56db; border:1px solid #bcd0f7;";
      else if (x.status === "Cancelled") statusStyle = "background:#eee; color:#666;";

      return `
        <div class="mini-row" style="padding:16px 0;">
          <div>
            <div style="display:flex; align-items:center; gap:8px;">
              <b style="font-size:15px; color:var(--maroon-dark);">${esc(x.crop_name)}</b>
              <span class="status-badge" style="${statusStyle}">${esc(x.status)}</span>
            </div>
            <small class="muted" style="margin:4px 0;">
              ${isFarmer ? `Inquiry from <b>${esc(x.other_party)}</b>` : `Sent to farmer <b>${esc(x.other_party)}</b>`}
              · Quantity: <b>${Number(x.quantity_kg).toLocaleString("en-IN")} kg</b> · Date: ${new Date(x.created_at).toLocaleDateString()}
            </small>
            ${x.message ? `<div style="background:#faf5ee; padding:8px 12px; border-radius:6px; margin-top:6px; font-size:12px; border:1px solid var(--line-light);">"${esc(x.message)}"</div>` : ''}
          </div>
          <div style="display:flex; gap:8px; align-items:center;">
            ${isFarmer && x.status === "Pending" ? `
              <button class="btn btn-primary btn-sm" onclick="setInquiryStatus(${x.id}, 'Accepted')">Accept</button>
              <button class="btn btn-outline btn-sm" onclick="setInquiryStatus(${x.id}, 'Declined')">Decline</button>
            ` : ''}
            ${isFarmer && x.status === "Accepted" ? `
              <button class="btn btn-primary btn-sm" onclick="setInquiryStatus(${x.id}, 'Completed')">Mark Completed</button>
            ` : ''}
            ${!isFarmer && x.status === "Pending" ? `
              <button class="btn btn-outline btn-sm" onclick="setInquiryStatus(${x.id}, 'Cancelled')">Cancel Inquiry</button>
            ` : ''}
          </div>
        </div>
      `;
    }).join("");
  } catch (e) {
    el.innerHTML = `<p class="risk">Error: ${esc(e.message)}</p>`;
  }
}

async function setInquiryStatus(id, newStatus) {
  try {
    await api(`/api/inquiries/${id}?status=${encodeURIComponent(newStatus)}`, { method: "PATCH" });
    toast(`Inquiry status updated to ${newStatus}.`);
    loadInquiries();
  } catch (e) {
    toast("Status update failed: " + e.message);
  }
}

// ---------------------------------------------------------------------------
// Weather Widget & Community Dashboard
// ---------------------------------------------------------------------------
async function loadWeather() {
  const main = document.getElementById("weather-main");
  if (!main) return;
  try {
    const d = await api("/api/weather");
    const c = d.current;
    main.innerHTML = `
      <div class="weather-temp">${Math.round(c.temperature_2m)}°C</div>
      <div class="weather-sub">Relative Humidity: ${c.relative_humidity_2m}% · Precipitation: ${c.precipitation} mm</div>
      <div class="weather-sub" style="margin-top:6px;">Updated ${new Date(d.fetched_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })} · Provider: Open-Meteo</div>
    `;
    document.getElementById("weather-metrics").innerHTML = `
      <div><b>${c.wind_speed_10m} km/h</b><small>Wind Speed</small></div>
      <div><b>${d.daily.precipitation_probability_max[0] ?? 0}%</b><small>Rain Chance Today</small></div>
      <div><b>${d.daily.precipitation_sum[0] ?? 0} mm</b><small>Precipitation</small></div>
    `;
    document.getElementById("weather-days").innerHTML = `
      <div class="weather-sub" style="margin-top:14px; background:rgba(255,255,255,0.08); padding:8px 12px; border-radius:8px;">
        Tomorrow: ${d.daily.time[1] || ""} · ${d.daily.temperature_2m_min[1] ?? "—"}–${d.daily.temperature_2m_max[1] ?? "—"}°C · Rain chance ${d.daily.precipitation_probability_max[1] ?? 0}%
      </div>
    `;
  } catch (e) {
    main.innerHTML = '<p class="weather-sub">Live weather service unavailable. Please check internet connection.</p>';
  }
}

async function loadCommunityForDash() {
  const el = document.getElementById("dash-community");
  if (!el) return;
  try {
    const d = await api("/api/community");
    el.innerHTML = `
      <div class="mini-row"><div>Registered Farmers<small>Chharoli accounts</small></div><b>${d.farmers_registered}</b></div>
      <div class="mini-row"><div>Registered Retailers<small>Wholesale/local buyers</small></div><b>${d.retailers_registered}</b></div>
      <div class="mini-row"><div>Active Harvest Listings<small>Current offers</small></div><b>${d.active_listings}</b></div>
    `;
  } catch (e) {}
}

async function loadAnalysisHistory() {
  const el = document.getElementById("history-list");
  if (!el) return;
  try {
    const rows = await api("/api/analysis-history");
    if (!rows.length) {
      el.innerHTML = '<p class="muted">No saved analysis runs yet. Analysis history logs automatically when you run the Crop Analyzer.</p>';
      return;
    }
    el.innerHTML = `
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Area</th>
              <th>Budget</th>
              <th>Season</th>
              <th>Soil / pH</th>
              <th>Top Recommended Crop</th>
              <th>Score</th>
            </tr>
          </thead>
          <tbody>
            ${rows.map(x => `
              <tr>
                <td>${new Date(x.created_at).toLocaleDateString()}</td>
                <td>${x.area_acres} ac</td>
                <td>${fmt(x.budget_inr)}</td>
                <td>${esc(x.season)}</td>
                <td>${esc(x.soil_type)} ${x.soil_ph ? `(pH ${x.soil_ph})` : ''}</td>
                <td><b>${esc(x.top_crop)}</b></td>
                <td><span class="status-badge">${x.top_score}/100</span></td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  } catch (e) {
    el.innerHTML = `<p class="risk">Error: ${esc(e.message)}</p>`;
  }
}

// ---------------------------------------------------------------------------
// Initialization on Page Load
// ---------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", async () => {
  updateNavState();
  await fetchScenarios();
  renderScenarioChipsContainers();

  if (token && currentUser) {
    showPage("dashboard");
    openDashboard();
  } else {
    loadCommunity();
    loadListings();
  }
});
