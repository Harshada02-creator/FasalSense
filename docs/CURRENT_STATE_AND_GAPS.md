# Current State and Implementation Status (Updated Prototype)

This document provides a candid evaluation of the completed FasalSense prototype after addressing the foundational starter gaps.

## What Was Implemented and Verified

1. **Local Crop Supply vs Retailer Demand Balance (Core Innovation)**:
   - Quantified per-crop supply and demand snapshot calculation.
   - Evaluates Supply/Demand ratio (< 0.75 for potential market gap opportunity, > 1.25 for potential surplus competition, 0.75–1.25 for balanced).
   - Core 15-point bounded scoring component integrated into recommendation engine.
   - Integrated Pune APMC historical wholesale modal price benchmarks (MSAMB & AGMARKNET 2022–2024), 12-month volatility ranges, and arrival seasons.
   - Clean distinction between dynamic FasalSense platform activity and synthetic demonstration baselines.

2. **Multi-Factor Scoring Calibration**:
   - Transparent 5-factor scoring model summing to 100 points max:
     * Season Match: 25 pts (out-of-season = 0 pts)
     * Water & Irrigation Fit: 20 pts (penalizes high-water crops during rain-fed conditions)
     * Soil Texture & pH Chemistry: 20 pts (texture 12 pts, tested pH 8 pts)
     * Cultivation Budget & Affordability: 20 pts (scaled by land area)
     * Market Supply vs Demand: 15 pts (glut warning vs market gap opportunity)
   - Tested pH input is actively evaluated against documented agronomic ranges (`ph_min`, `ph_max`).
   - Area-scaled economics with conservative (-15%) and optimistic (+15%) sensitivity bounds.

3. **Interactive 7-Scenario Teacher Demonstration Laboratory**:
   - 1-click preset scenario selector chips on Home, Scenarios Lab, and Analyzer.
   - Live debounced recalculation when parameters are edited.
   - Pedagogical focus banner on every scenario explaining the exact software behavior.
   - Side-by-side scenario comparison modal comparing Scenario A vs Scenario B with rank/score diffs.

4. **Complete Role-Based Workflows**:
   - **Farmer**: Registration/login, farm profile persistence, soil photo preview with visual color tone analysis and laboratory guidance, crop analysis, listing creation/editing/status management, received inquiry handling (Accept, Decline, Complete), and analysis history.
   - **Retailer**: Registration/login, marketplace search and price filtering, in-page inquiry submission modal with price calculator, and inquiry status tracking (Pending, Accepted, Declined, Completed, Cancelled).
   - Strict 403 authorization enforcement on cross-role endpoints.

5. **Path Robustness & Data-Driven Catalogue**:
   - Static files and SQLite database paths anchored to project root using `Path(__file__)`.
   - Data-driven crop catalogue loaded dynamically from `data/crop_catalogue_seed.json`.

6. **Comprehensive Test Suite (35 Tests Passed)**:
   - `test_full_application_smoke.py` (11 tests): End-to-end smoke verification of HTML landing page, static CSS & JS, farmer & retailer authentication/registration, budget sensitivity, water availability differentiation, soil pH response, season disqualification, acreage-scaled financial modeling, supply-demand surplus/gap badges, demand-vs-budget protection, and complete 16-crop APMC benchmark audit.
   - `test_api_workflows.py` (7 tests): Health endpoint, Farmer & Retailer demo logins on fresh database, 403 role enforcement, farm profile updates, produce listings CRUD, retailer purchase inquiries lifecycle, authenticated analysis history growth, and zero-budget protection.
   - `test_crop_engine.py` (5 tests): pH evaluation, season mismatch gating, budget penalty, high demand vs budget constraint, water deficit penalty.
   - `test_scenarios.py` (6 tests): Validates all 7 pedagogical demonstration scenarios.
   - `test_recommendation_scenarios.py` (6 tests): Multi-crop catalogue, water differentiation, area financial scaling, budget fit, supply-demand delta, simulation labelling.

---

## Known Limitations to Disclose in Diploma Blackbook

1. **Not a Village-Wide Census**:
   - FasalSense captures listings and inquiries inside this prototype only. It does not represent an exhaustive census of all crops grown in Chharoli Budruk.
2. **Honest Soil Testing Boundaries**:
   - Smartphone camera imagery cannot determine chemical pH, Nitrogen, Phosphorus, or Potassium. Physical laboratory testing (Soil Health Card) remains necessary.
3. **Illustrative Operating Margins vs. Guaranteed Profits**:
   - Economic models estimate operational gross margins based on benchmark costs and modal yields. They exclude land rent, debt financing, family labour valuation, transport logistics, and catastrophic climate/pest shocks.
4. **Demonstration Baseline Fallback**:
   - When active platform listings and inquiries for a candidate crop are insufficient, the system uses labelled synthetic values for demonstration purposes, preventing misleading zero-demand outputs.
5. **Future Scope for Production**:
   - Automated AGMARKNET live API scraper integration.
   - Multi-lingual Marathi localization (मराठी भाषांतर).
   - Micro-climate sensor integration (IoT soil moisture probes).
   - Cooperative bulk procurement and logistics pooling.
