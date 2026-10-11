# FasalSense — Master Build Brief for Antigravity

You are continuing an existing student-project codebase. **Read this file and `README.md`, then read every file under `docs/` before making changes.** Treat the supplied code as the starting point, not proof that every feature is complete. Audit the app, preserve working features, improve the project end-to-end, and run tests before finishing.

## 1. Product vision

Build **FasalSense**, a polished, responsive, multi-crop farm decision-support prototype for **Chharoli Budruk, Pune, Maharashtra, India**. This is a final-year diploma / blackbook demonstration, not a government-grade or agronomist-certified production system. It must clearly show how recommendations change when a farmer changes their budget, land size, soil details, water availability, irrigation access, season, and market assumptions. **The core differentiator is local crop supply versus buyer demand**: show which crops already appear in bulk supply, which are relatively less available, what retailers are asking for, and how this can signal surplus/competition or a possible market gap. Do not reduce market analysis to price trends alone.

**Do not build the product around rice/paddy alone.** Paddy is one candidate among multiple cereals, pulses, oilseeds, vegetables, and longer-duration crops. The existing list of 16 is a starter catalogue, not a scientifically verified list of the only crops grown in Chharoli. Do not claim the list is village-verified. Review `data/crop_catalogue_seed.csv` and `docs/DATA_AND_SOURCE_POLICY.md`; design the crop catalogue to be extensible. Add additional candidates only with clear source/provenance or explicit `candidate / needs local validation` status.

## 2. Main audience and roles

### Farmer
- Register and log in as a farmer.
- Set a farm profile: area in acres, approximate locality (avoid collecting exact GPS unless necessary), budget in INR, soil category, optional soil-test pH/N/P/K, season, irrigation method, and water availability.
- Upload a soil photo and view a preview. Unless a real model with a documented dataset and defensible evaluation is integrated, label this as a photo preview / preliminary visual aid only. **Never infer exact pH or NPK from a photo and present it as measured.** Allow manual entry of a tested pH or soil-test result.
- Run a multi-factor crop analysis that ranks several alternatives (not just one crop).
- See why each crop ranked as it did, the main risk factors, approximate cultivation cost, likely gross revenue, estimated net return, duration, water requirement, season, and confidence/data-quality labels.
- Compare top candidates side by side.
- Save/update farm details, view analysis history if feasible, and publish produce listings.

### Retailer / buyer
- Separate retailer registration/login and role-aware dashboard.
- Browse farmer produce listings; search/filter by crop, quantity, asking price, availability, locality, and quality.
- View clearly marked demo listings and send inquiries to farmers.
- Do not fabricate real retailer demand or orders. Use app records and labelled sample records only.

## 3. CORE DEMONSTRATION REQUIREMENT — LOCAL SUPPLY/DEMAND BALANCE

The most important market concept is **how much of each crop is already available in the local market context versus how much buyers want**. The teacher must be able to see per-crop available-supply quantity, recorded buyer-demand quantity, a comparison period, the resulting balance and the evidence/source label. The app must distinguish: (a) potential surplus / high competition if supply is materially above demand, (b) broadly balanced supply/demand, (c) a possible supply gap when demand is higher than supply, and (d) insufficient comparable records.

This supply/demand balance must contribute to crop ranking and be displayed directly inside each crop recommendation. It is not a decorative market dashboard and not optional. The farmer should see why an already plentiful crop may carry higher competition risk, or why a lower-availability crop may present a market opportunity. That opportunity must never override unsuitable soil, season, water or unaffordable cost, and it must not be described as a guaranteed higher price or sale.

The teacher must be able to change a control and immediately see meaningful changes. Make analysis refresh on explicit “Analyze” action and, where appropriate, show a “Recalculate” control or a debounced preview. Always avoid stale outputs being mistaken for outputs from current inputs.

Include at least these preset scenarios (values are examples for software testing, not agricultural advice):
1. Low budget + rain-fed/no irrigation.
2. Moderate budget + limited or seasonal water.
3. Higher budget + reliable irrigation / abundant water.
4. Same farm details but different soil category or measured pH.
5. Same profile but season changes (Kharif / Rabi / Summer).
6. Same profile but land area changes, so total cost/revenue scale proportionately.

7. Same farm conditions but market supply changes from high-surplus to demand-gap for a crop.
8. Use a crop where supply/demand records are missing and show “insufficient data,” not zero demand.

Show how the crop ranking and cost estimates change across scenarios. Do not imply a higher budget or abundant water automatically means a crop is best. Penalize water-intensive crops when water is limited; penalize candidates that are not affordable; account for season and soil suitability; expose trade-offs and uncertainty.

## 4. Crop recommendation engine

The existing `app/services.py` is a transparent rules-based prototype and contains illustrative crop economics. Audit it and improve it. Recommended approach:

1. Make crop catalogue data-driven (JSON or CSV under `data/`, loaded by backend) rather than defining everything only inside a Python list. Keep fields for season(s), soil compatibility, pH range if supported by a source, water need, duration, input cost basis, plausible yield range, price basis, risk notes, source, source date, and evidence status.
2. Calculate separate explainable components: season fit, soil/pH fit, water fit, budget fit, local supply-versus-buyer-demand balance, and estimated return/risk. Market balance is a bounded but meaningful score component. Display the crop's comparable supply and demand quantities, period, status, evidence scope, and score effect.
3. Use sensible penalties / suitability gates for out-of-season or clearly unaffordable options. Avoid saturating every result at a score of 95; scores should meaningfully distinguish candidates and be labelled “prototype suitability score”, not a probability of success.
4. Calculate totals consistently: cultivation cost, gross revenue, estimated operating margin, and range/uncertainty. State units clearly (INR per acre, INR per quintal/kg, quintals per acre, etc.). Confirm unit conversions.
5. Do not use a commodity price increase by itself as the crop recommendation. Use crop availability/supply vs buyer-demand balance as a core market input, along with dated prices/market arrivals when verified. Market opportunity remains one input alongside suitability, water, budget, season, input cost, yield uncertainty, transport/storage, and risk.
6. Show top 3–5 candidates, including why a crop is recommended and why other options may be risky. Keep a “not enough information” state when inputs are missing.
7. Mark every unverified numeric assumption as `illustrative`, `estimated`, or `not connected to live market data`. Never fabricate source citations, live prices, historical trends, crop production, or ML accuracy.
8. If a real ML component is added, use a documented, licensed dataset and add preprocessing, reproducible training/evaluation code, a saved model only if valid, a baseline comparison, and honest metrics. Do not call a hand-written scoring formula “trained ML”. If no suitable public local dataset exists, keep the transparent scoring model and describe ML as future work in the blackbook rather than inventing a trained model.

## 5. Market, weather, soil, water data

- Supply/demand is a core feature. Evaluate supply as comparable market arrivals or stated available quantity, and demand as comparable buyer inquiries/orders/demand records, for the same crop definition, unit, place and period. Do not compare unmatched units/periods silently. Use `data/local_supply_demand_demo.csv` only as a labelled simulation for presentations, never as real Chharoli facts.
- FasalSense active non-demo listings and retailer inquiries can provide a live **platform-activity proxy** over the trailing 30 days when both sides have records. It is not a whole-village census. If one side is missing, show insufficient data (or use the clearly labelled synthetic fallback only when demo mode is enabled).
- Keep Chharoli Budruk as the target area, but label coordinates as approximate until verified.
- Weather integration may use Open-Meteo. Show source, retrieval time, and API failure state. Do not silently substitute fake live weather.
- For market prices, prefer a verified official or reputable source (e.g. AGMARKNET / data.gov.in / Maharashtra market sources) where terms and usable data are available. If integration is not practical, create a small static demonstration dataset with explicit sample/demo labels and dates; clearly separate it from live price data.
- Public district rainfall data is not the same as exact farm water supply. Farmer-reported water availability should be represented separately from station rainfall / public groundwater records.
- The soil photo should not return a made-up exact pH. Prefer lab-result input and guidance on getting a soil test. Any image classifier must be separately documented, tested, and carefully limited.
- Do not scrape restricted government or private records, bypass access controls, or expose farmer-identifiable data. Use public datasets, voluntary demo entries, and labelled synthetic records only.

## 6. UX and visual design

Build a premium but accessible Indian agriculture dashboard, mobile-first and responsive:
- Palette: warm ivory / cream backgrounds, earthy maroon or soil-brown, terracotta accents, muted leaf green, dark readable text. Subtle local/folk-art inspired details only; avoid busy decoration.
- Clear typography, strong hierarchy, generous spacing, data cards, charts, comparison tables, empty states, validation, loading and error feedback.
- Farmer experience should be simple and accessible; plain language, INR formatting, acres/hectares clearly labelled, icons with text labels, responsive layout.
- Retailer experience should feel like a functional marketplace, not an unrelated generic template.
- Do not hard-code only one crop as the hero/result. Showcase diverse crop options and explain how inputs influence ranking.
- Make demo data labels visible near every demonstration statistic, price, yield, and market chart.

## 7. Technical requirements

The current code uses FastAPI, SQLAlchemy, SQLite locally / PostgreSQL via `DATABASE_URL`, and a static HTML/CSS/JS frontend. Prefer improving this stack instead of doing a wholesale rewrite unless there is a clear technical reason.

- Keep clear module boundaries: API/routes, data models, recommendation service, source adapters, crop catalogue, static frontend, tests, docs.
- Keep role-based authorization on APIs and validate input server-side.
- Use safe secrets via environment variables; never commit `.env`, databases, passwords, tokens, or user records.
- Fix path issues so static assets and templates load independent of current working directory.
- Check demo-mode behavior; demo credentials and listings must be labelled and disabled for public use when appropriate.
- Add tests for recommendation scenario changes, area-scaled financial calculations, invalid inputs, role checks / key API workflows, and graceful weather failure.
- Ensure `requirements.txt`, environment example, and Render Blueprint agree. The app must start with documented commands, respond to `/api/health`, and not rely on shipping a local SQLite database.
- Add friendly error states for missing weather/market data and for empty farmer/retailer accounts.
- Do not claim full production readiness; include a limitations/security checklist.

## 8. Acceptance criteria

The task is not complete until all of the following hold:
- Fresh checkout can install dependencies and start using the documented steps.
- `/api/health` returns healthy status and the homepage/static assets load.
- Farmer and retailer registration/login work, and role boundaries hold.
- Farmer can save a profile, analyze crops, and see meaningful explanations and economic calculations.
- Every recommendation displays crop-specific supply quantity vs buyer-demand quantity, period and evidence label; surplus/low-availability balance meaningfully changes the market score without overriding agronomic constraints.
- Supply/demand overview table clearly separates synthetic demonstration quantities from platform-observed activity and never presents either as a full village census.
- Low-budget/no-water and high-budget/reliable-water scenarios produce visibly different, sensible rankings; seasonal and soil changes also alter suitability where relevant.
- Costs scale with area; units are consistent; no negative/positive results are framed as guaranteed.
- Retailers can filter listings and create inquiries; farmer listing management works.
- The UI identifies prototype/illustrative values honestly and does not fake precise pH, exact village statistics, live prices, or trained-model metrics.
- Tests and syntax checks run; any failing test or incomplete feature is reported honestly.
- Update the README, technical notes, data provenance, and a brief blackbook methodology/limitations document after implementation.

## 9. Work order

1. Audit the current code and documentation; make a short implementation checklist.
2. Fix app startup, security/configuration, data model issues, and the recommendation engine's logic/units.
2a. Validate the supply/demand component, evidence labels and missing-data behaviour first; this is the core differentiator of FasalSense.
3. Make the crop catalogue data-driven with provenance fields and transparent sample economics.
4. Improve multi-scenario farmer analysis and comparisons.
5. Improve farmer/retailer flows and responsive visual polish.
6. Add tests and run them.
7. Update docs and summarize what is genuinely implemented, what uses demo data, and how to run/deploy.

**Do not stop after rewriting the prompt or generating a mock-up. Work in the actual files in this repository and deliver the improved runnable project.**
