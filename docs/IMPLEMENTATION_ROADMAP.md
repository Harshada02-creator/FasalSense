# Implementation Roadmap

This is a delivery order, not a claim that the work is already done.

## P0 — Make the starter safe and reproducible

- Confirm clean local installation and start-up.
- Use paths anchored to the Python module/project directory.
- Ensure no SQLite DB, secrets, personal data or cache is distributed.
- Require a strong environment secret in deployed environments; keep demo mode clearly separated.
- Validate account roles and protected routes.
- Add smoke/API tests.

## P1 — Recommendation engine and LOCAL SUPPLY/DEMAND (core differentiator)

- Build a per-crop supply-vs-buyer-demand signal: local available supply, buyer inquiry/demand volume, comparison period, source, confidence and a clear potential-surplus / balanced / possible-supply-gap label.
- Use that balance as a meaningful, bounded ranking component. A crop already in bulk supply relative to buyer demand should incur a competition/surplus risk; a crop with lower supply than recorded demand may gain a market-opportunity signal, but must still pass agronomic and budget checks.
- Add a dedicated supply/demand view so a teacher can compare the supported crops and understand why the market signal changes a recommendation.
- Separate app-only active listings and retailer inquiries from a complete village/market estimate. Treat missing records as unknown, not zero demand.
- Provide synthetic supply/demand quantities only for demonstrations, conspicuously labelled as simulated and not measured in Chharoli.
- Move the crop catalogue to structured configuration and load provenance fields.
- Audit every unit and financial formula.
- Replace maximum-score saturation with normalized component scoring.
- Make affordability a meaningful decision factor; flag costs above budget instead of merely hiding the issue.
- Make water, season and soil compatibility transparent.
- Add crop comparison, cost ranges, risk warnings and a scenario comparison feature.
- Avoid using price trends or supply-gap signals as the dominant deciding variable; market balance is important but must not override season, soil, water, budget and risk.

## P2 — Data provenance and integrations

- Weather: show current source, provider timestamp and unavailable state.
- Market: implement only a verified source adapter; otherwise make the demo/sample dataset visibly illustrative.
- Rainfall/water: distinguish regional rainfall from farm's reported access to water.
- Crop catalogue: keep village-level, district-level and unverified candidate statuses.
- Soil: show image preview plus optional test values; don't invent soil chemistry from an image.

## P3 — User workflows and UI

- Farmer profile create/read/update workflow.
- Farmer analyze/recommendation/compare/previous analysis flow.
- Farmer produce listing create/edit/pause/sold workflow.
- Retailer search/filter/listing detail/inquiry flow.
- Loading/error/empty/success states and responsive layout.
- Demo labels in every widget that uses static example data.

## P4 — Academic documentation and release

- Include architecture diagram and data flow.
- Describe ranking logic and financial calculations.
- Add scenario test tables and observed results.
- Describe sources, geographic scope and update frequency.
- List limitations and ethics/privacy considerations.
- Update Render instructions and verify a clean deployment if possible.
