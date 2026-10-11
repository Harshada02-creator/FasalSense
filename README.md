# FasalSense — Farming Intelligence & Local Market Balance Prototype

**Target Locality:** Chharoli Budruk, Haveli Taluka, Pune, Maharashtra, India  
**Project Type:** Final-Year Diploma Computer Engineering Project / Blackbook Implementation  
**Core Innovation:** Multi-factor crop decision support integrating **Local Crop Supply vs. Retailer Demand balance** with farm affordability, water constraints, soil chemistry, and a farmer-to-retailer produce marketplace.

---

## 1. Project Overview

FasalSense addresses a critical gap in smallholder agriculture: **farming decisions made without knowing local market availability or buyer demand often lead to harvest gluts, extreme price discounting, and distress sales.**

Rather than merely recommending whichever crop currently has the highest market price, FasalSense evaluates:
1. **Growing Season Match (25 points)**: Sowing window compatibility (Kharif, Rabi, Summer).
2. **Water & Irrigation Fit (20 points)**: Available farm water supply vs. crop requirement (penalizing high-water crops during rain-fed conditions).
3. **Soil & pH Chemistry (20 points)**: Soil texture suitability and laboratory-tested pH ranges (5.5–8.2).
4. **Cultivation Budget & Affordability (20 points)**: Area-scaled input expenses vs. available farmer capital.
5. **Local Crop Supply vs. Buyer Demand Balance (15 points)**:
   - **Potential Supply Gap** (Ratio < 0.75): Retailer demand exceeds local supply (+5 bonus; sales opportunity signal).
   - **Broadly Balanced** (0.75 ≤ Ratio ≤ 1.25): Normal market condition (+2 baseline).
   - **Potential Surplus Glut** (Ratio > 1.25): Local supply exceeds buyer demand (-7 penalty; high competition risk).
   - **Insufficient Records**: Missing supply/demand is labeled as unknown (not assumed as zero demand).

---

## 2. Completed Features

### A. Core Innovation: Local Supply vs. Retailer Demand
- Per-crop local supply (kg), retailer demand (kg), supply/demand ratio, and balance status.
- Source transparency: Distinguishes dynamic FasalSense platform activity (trailing 30 days) from the labelled synthetic baseline.
- Real historical wholesale benchmarks from **Pune APMC (Gultekdi), Haveli APMC, and Junnar APMC** (MSAMB & AGMARKNET bulletins 2022–2024), including 12-month volatility ranges.

### B. Interactive 7-Scenario Teacher Demonstration Laboratory
Pre-configured interactive scenarios accessible via 1-click test chips and a side-by-side comparison modal:
1. **Scenario 1: Low Budget & Limited Water** — Resource-constrained: favors drought-tolerant Bajra/Moong; severely penalizes Sugarcane and Paddy.
2. **Scenario 2: High Budget & Reliable Water** — Capital-enabled: unlocks higher-input crops while monitoring water sustainability.
3. **Scenario 3: Soil Type & pH Variation** — Demonstrates how pH changes (acidic 5.2 vs neutral 7.0 vs alkaline 7.8) trigger suitability adjustments.
4. **Scenario 4: Growing Season Shift** — Switches to Rabi; Kharif crops (Bajra, Soybean) drop to 0 season points, promoting Wheat, Harbhara, and Onion.
5. **Scenario 5: High Existing Supply / Low Demand** — Simulates local market tomato glut; market score drops to 3/15.
6. **Scenario 6: Low Existing Supply / High Buyer Demand** — Simulates strong unmet demand for leafy vegetables and Moong; market score rises to 15/15.
7. **Scenario 7: Strong Demand but Unaffordable Cost** — Proves that strong market demand **never overrides** budget constraints.

### C. Complete Role-Based Workflows
- **Farmer Workflow**:
  - Registration/Login → Farm Profile (Acres, soil texture, tested pH, tested NPK, irrigation, water, budget, season).
  - Soil photo upload with visual tone classification (Vertisol / Alfisol / Alluvial indicator) and laboratory testing guidance.
  - Multi-crop suitability analysis with 5-factor breakdown and sensitivity ranges (conservative / base / optimistic returns).
  - Produce listing publication, editing, status management (Active, Paused, Sold out, Archived).
  - Received retailer inquiries management (Accept, Decline, Complete).
  - Analysis history tracking.
- **Retailer Workflow**:
  - Registration/Login → Marketplace exploration with crop/variety search and price filtering.
  - In-page purchase inquiry modal with quantity verification, price calculation, and notes.
  - Inquiries dashboard tracking response status (Pending, Accepted, Declined, Completed, Cancelled).

---

## 3. Technology Stack

- **Backend**: FastAPI (Python 3.11+ / 3.12), SQLAlchemy 2.0, Pydantic v2.
- **Database**: SQLite (default local development, anchored to project root) / PostgreSQL (production via `DATABASE_URL`).
- **Security**: PBKDF2-HMAC-SHA256 password hashing (240,000 rounds), HMAC-SHA256 bearer tokens, role authorization (`require_role`).
- **Frontend**: Responsive Vanilla HTML5/CSS3/JavaScript (mobile-first, warm Indian agricultural palette, glassmorphism, no external framework lock-in).
- **APIs**: Open-Meteo Weather API for Chharoli Budruk coordinates (18.637° N, 73.881° E).

---

## 4. How to Run Locally

### Prerequisites
Python 3.11 or 3.12 installed.

### Setup Steps
```bash
# Clone or navigate to the directory
cd FasalSense_MD_Files

# Create a virtual environment (optional but recommended)
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the local server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Windows Helper Wrappers
This package includes `python.cmd` and `uvicorn.cmd` pre-configured for the environment. You can run:
```cmd
python.cmd -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` in your web browser.
- Interactive Web App: `http://127.0.0.1:8000/`
- API Documentation (Swagger): `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/api/health`

### Demo Login Credentials
- **Farmer Demo**: `farmer.demo@example.com` / `DemoFarm123!` (or click "Fill Farmer" on login)
- **Retailer Demo**: `retailer.demo@example.com` / `DemoRetail123!` (or click "Fill Retailer" on login)

---

## 5. Running Verification Tests

Run the full automated test suite (35 tests across 5 modules):
```bash
python scripts/verify_project.py
python -m unittest discover -s tests -p "test_*.py" -v
```

All 35 tests pass:
- `tests/test_full_application_smoke.py` (11 tests): End-to-end smoke verification of landing page HTML, static CSS & JS assets, farmer & retailer authentication/registration, budget sensitivity, water availability differentiation, soil pH response, season disqualification, acreage-scaled financial modeling, supply-demand surplus/gap badges, demand-vs-budget protection, and complete 16-crop APMC benchmark audit with portal URLs.
- `tests/test_api_workflows.py` (7 tests): Health endpoint, Farmer/Retailer demo logins on fresh database, 403 role enforcement, farm profile updates, produce listings CRUD, retailer purchase inquiries lifecycle, authenticated analysis history growth, and zero-budget protection.
- `tests/test_crop_engine.py` (5 tests): pH evaluation, season mismatch gating, budget penalty, high demand vs budget constraint, water deficit penalty.
- `tests/test_scenarios.py` (6 tests): Validates all 7 pedagogical demonstration scenarios.
- `tests/test_recommendation_scenarios.py` (6 tests): Multi-crop catalogue, water differentiation, area financial scaling, budget fit, supply-demand delta, simulation labelling.

---

## 6. Deploying to Render

The repository includes a ready `render.yaml` blueprint:
1. Push this project repository to GitHub or GitLab.
2. In the [Render Dashboard](https://dashboard.render.com/), click **New → Blueprint**.
3. Connect your repository. Render will automatically detect `render.yaml`, set up:
   - Web Service: `fasalsense-chharoli` (Python runtime, `uvicorn app.main:app --host 0.0.0.0 --port $PORT`).
   - Managed PostgreSQL Database: `fasalsense-db`.
4. Environment variables configured automatically:
   - `DATABASE_URL` (connected to PostgreSQL database).
   - `SECRET_KEY` (generated securely).
   - `DEMO_MODE=true` (initializes demo accounts and sample listings).
5. Once deployed, verify `/api/health` returns `{"status":"ok"}`.

---

## 7. Data Provenance & Academic Disclosures

| Data Stream | Source / Agency | Geography & Coverage | Evidence Status |
| :--- | :--- | :--- | :--- |
| **7-Day Weather Forecast** | Open-Meteo API | Chharoli coordinates (18.637° N, 73.881° E) | Live Sourced Forecast |
| **Crop Catalogue (16 Crops)** | NABARD Pune District PLP (2022-23) scale of finance | Pune District Level | District-Level Reference |
| **Wholesale Mandi Prices** | MSAMB & AGMARKNET Pune / Haveli / Junnar APMC | Pune District APMCs (2022-2024) | Historical Wholesale Benchmark |
| **Platform Produce Supply** | FasalSense Active Crop Listings | Chharoli prototype registered users | Prototype Platform Activity |
| **Platform Retailer Demand** | FasalSense Retailer Purchase Inquiries | Chharoli prototype registered users | Prototype Platform Activity |
| **Demonstration Supply/Demand** | `data/local_supply_demand_demo.csv` | Synthetic demonstration baseline | Explicitly Simulated Demo Data |
| **Soil Chemistry (pH, N, P, K)** | Farmer self-reported from Soil Health Card | Individual farm plot | Farmer Laboratory Self-Report |

### Blackbook Disclosure Checklist
- **No Village Census Claimed**: FasalSense does not represent a census of all produce harvested in Chharoli. Platform numbers reflect prototype users only.
- **No AI Camera pH Measurement**: Smartphone camera photos cannot measure chemical pH or NPK. Honest visual tone inspection is provided, with explicit guidance to use laboratory Soil Health Cards.
- **No Guaranteed Profit**: Cultivation costs, gross revenues, and margins are illustrative projections with conservative and optimistic bounds. Land lease, transport, and extreme weather risks are clearly stated.
