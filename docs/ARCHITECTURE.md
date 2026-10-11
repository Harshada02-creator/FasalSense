# Starter Architecture and Intended Data Flow

## Current stack

- Frontend: plain HTML, CSS and JavaScript under `static/`.
- API: FastAPI under `app/main.py`.
- Data models and persistence: SQLAlchemy (`app/models.py`, `app/database.py`).
- Business logic: `app/services.py` (weather request and current rules-based crop recommendations).
- Local DB: SQLite by default; deployment can use PostgreSQL through `DATABASE_URL`.
- Hosting start: `render.yaml`.

## Intended request flow

```text
Farmer / Retailer browser
        |
        v
Responsive UI (static/index.html, styles.css, app.js)
        |
        v
FastAPI API routes (app/main.py)
        |-----------------------|
        v                       v
Auth / role checks         Domain services
        |                    |       |
        v                    v       v
SQLAlchemy models     Crop engine  External source adapters
        |                    |       |
        v                    v       v
SQLite/PostgreSQL     Ranked crop comparison + sources/assumptions
```

## Intended extension points

- `data/crop_catalogue_seed.json`: initial crop definitions and evidence metadata. Antigravity should migrate the runtime logic to load structured data only after tests verify the migration.
- `app/services.py` or a new `app/recommendation/` package: scoring, cost equations, risk, unit conversion.
- `app/providers/`: weather and (if genuinely implemented) market data adapters.
- `tests/`: service-level, API, auth/role and scenario tests.

Keep data lineage attached to returned values so the frontend can indicate `live`, `district-level`, `farmer-reported`, `illustrative`, or `unavailable`.


## Supply/demand component (core recommendation input)

`app/market_data.py` builds a crop-level market signal over a rolling 30-day window. It prefers a comparable signal derived from non-demo active listings and retailer inquiries inside FasalSense when both sides have records; otherwise it uses the explicitly synthetic `data/local_supply_demand_demo.csv` if demo market mode is enabled. The `/api/market/supply-demand` endpoint exposes per-crop quantity, balance label, source status, and the observed platform-side counts. `/api/analyze` passes the same per-crop signals to the ranking function.

Important boundary: platform activity is not a village-wide market census, and the bundled simulated quantities are not real Chharoli observations. No production or demand claim should be presented as locally verified without external evidence.
