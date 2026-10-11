# Data, Crop Evidence and Source Policy

## Non-negotiable rule: distinguish locality levels

A crop appearing in a Pune district-level report does not prove that it is commonly grown in **Chharoli Budruk specifically**. In the UI, README, blackbook and presentation, use these evidence labels consistently:

- `Village-verified`: only when a trustworthy source or voluntary local survey actually supports the specific village claim.
- `District-level reference`: a source covers Pune district or its financing/agriculture context but not Chharoli village cultivation.
- `General agronomic candidate`: a plausible crop option to evaluate, not a claim about local prevalence.
- `Farmer-reported`: supplied voluntarily by a registered prototype farmer; not a community-wide statistic.
- `Illustrative/demo`: synthetic/example figures used for demonstrations.
- `Live sourced`: current data returned from an identified working source with source name and retrieval/update time.

Do not label all 16 starter crops “commonly grown in Chharoli.” The current catalogue is a flexible candidate set for demonstrating multi-factor ranking.

## Public sources to evaluate

1. **NABARD, Pune District Potential Linked Credit Plan (PLP), 2022–23** — historical district-level crop/scale-of-finance reference, with its listed financing crops referring to FY 2021–22. It includes examples such as sugarcane, jowar, bajra, ragi, paddy, onion, maize, sesame, sunflower, soybean, groundnut, moong, urad, tur, wheat, gram, fodder crops, vegetables, guava and fig. This is not a Chharoli village census and not a current mandi-price feed.
   - Source: https://www.nabard.org/auth/writereaddata/tender/1012212259Pune.pdf
2. **National Water Data Portal — Maharashtra Surface Water Department, Rainfall (Manual - Daily)** — public dataset page describes daily station rainfall, with a 2021–2025 CSV/API resource. Check station/geographic hierarchy and dates before assuming a station represents Chharoli.
   - Source: https://nwdp.nwic.gov.in/en/dataset/rainfall-maharashtra-surface-water-manual-daily
3. **IMD / Mausam** — weather and official rainfall products can provide regional context. Station/district/forecast values should not be described as farm-specific water supply.
   - https://mausam.imd.gov.in/
4. **AGMARKNET** — candidate source to evaluate for dated mandi arrivals/prices and commodity/market mapping. Confirm access, granularity, update timing and allowed usage before integration.
   - https://agmarknet.gov.in/
5. **Open Government Data Platform India** — search for relevant dated district crop/rainfall datasets and document the specific dataset URL and schema used.
   - https://data.gov.in/
6. **Soil Health Card / soil testing** — helps explain that pH and nutrient results come from a physical soil test and lab workflow, rather than a normal phone photo.
   - https://soilhealth.dac.gov.in/
   - Background on the portal: https://www.nic.gov.in/project/soil-health-card-portal/
7. **Central Ground Water Board (CGWB)** — consider regional/yearbook groundwater context only after identifying the actual well, period and geographic coverage. Groundwater observations are not equivalent to a particular farm's available water.
   - https://cgwb.gov.in/
8. **Open-Meteo** — weather forecast integration in the current starter. Verify coordinates, response fields, attribution requirements, terms and service availability before deployment.
   - https://open-meteo.com/

## Data integration requirements

For every imported source, record:

- dataset title and publisher;
- exact source URL and access date;
- original observation period and geographic granularity;
- field names, units, missing value conventions and any transformations;
- licence/terms or access limitations where applicable;
- last refresh time and “not available” behaviour;
- whether it is an observed value, forecast, district average, farmer self-report, model estimate or demonstration assumption.

Keep source references close to the display. Do not silently fill missing values with invented numbers. Any default/sample should include a visible `Demo / illustrative` label.

## Crop economics

The current seed catalogue's per-acre costs, yield estimates and per-quintal prices are placeholders for arithmetic and UI demonstration. They should be replaced or calibrated from credible, time-stamped, region/season-appropriate evidence before being described as reliable. Where evidence is unavailable, present low/base/high scenarios, disclose assumptions, and allow the user to edit assumptions during a demonstration.

Use consistent units:

- land area: acres or hectares, explicitly shown;
- cultivation cost: INR per acre (or INR per hectare if clearly converted);
- yield: quintals per acre / hectare;
- sale price: INR per quintal or INR per kg;
- revenue: yield × price × area using consistent units;
- estimated margin: gross revenue minus explicitly listed operating costs. Clarify excluded costs (land rent, financing, family labour, equipment depreciation, post-harvest loss, transport etc.) if excluded.

A positive illustrative margin is not a promise of profit.

## Soil imagery

A normal photo can show coarse visual appearance but cannot reliably identify pH, NPK and full soil health. Do not train or imply a model without a labelled, licensed dataset and meaningful evaluation. Safe prototype approach: photo upload and preview + optional manually entered lab result + guidance to get tested. If a vision model is added, disclose limitations and return uncertainty rather than an exact unsupported measurement.

## Local crop supply versus buyer demand (core recommendation feature)

The recommendation engine must not just display crop price or a generic market trend. For every candidate crop, it should compare estimated available supply with recorded/estimated buyer demand over a clearly stated period and show a balance label:

- **Potential supply gap:** supply is materially lower than demand in the selected comparable dataset.
- **Broadly balanced:** supply and demand are of similar scale.
- **Potential surplus / competition:** supply is materially higher than demand.
- **Insufficient records:** one or both sides cannot be compared. Do not interpret missing values as zero supply/demand.

### Evidence priority

1. Verified dated public market arrival/quantity data and buyer-demand data with compatible crop/variety, unit, geography and period, if available.
2. Farmer listings / harvest availability and retailer inquiry quantities captured inside FasalSense. These are a useful *platform activity proxy*, but they are not a census of Chharoli or the whole local market. For ranking, compare these as an observed balance only when both sides have meaningful records.
3. A synthetic per-crop supply/demand table for teacher demonstrations only. Every screen must say **“Illustrative simulation — not measured in Chharoli”** and show the time window. It must never be presented as a real village statistic.

The supplied `data/local_supply_demand_demo.csv` is deliberately synthetic. Its numbers exist only so the prototype can demonstrate the logic of surplus/low-availability scenarios before verified local records are accessible. Replace them with sourced values when appropriate, and retain provenance fields. Do not fabricate a shortage or surplus claim about actual Chharoli.

In the starter implementation, actual app-side active listing supply (kg) and retailer inquiry quantity (kg) use a rolling 30-day window. Demo listings must not be counted as genuine supply. Cancelled inquiries must not count as demand. If one side is missing, fall back to the labelled demo signal when enabled; otherwise return `Insufficient supply/demand records`. Keep both app-activity counts visible where helpful.

The balance is one component of a broader recommendation score. It must not cause an agronomically unsuitable crop to win. A “potential supply gap” is only a possible sales opportunity; it is not a price forecast or guarantee that a retailer will buy the crop.

## Market trends

- A price change must have a source, commodity/variety, market, unit, observation dates, and update time.
- Do not hard-code “prices are rising” without dated observations.
- If current data is unavailable, show a sample trend chart and visibly label it “Illustrative demo data—not live prices”.
- A rising price signal is never sufficient alone to recommend a crop.
