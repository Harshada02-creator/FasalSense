# Presentation Demo Scenarios

These are software behaviour tests for showing that inputs drive different outputs. Values below are sample inputs only; they are not farm recommendations.

## Scenario A — Low budget, water uncertain

- Area: 1 acre
- Budget: ₹10,000
- Soil: Sandy loam (reported; not laboratory-confirmed)
- Season: Kharif
- Water: No irrigation / rain-fed
- Expected behaviour: favour candidates with lower water needs and costs near the budget; penalise very expensive and high-water options; explain uncertainty and show alternatives instead of guaranteeing profit.

## Scenario B — Higher budget, reliable water

- Area: 2 acres
- Budget: ₹1,50,000
- Soil: Clay loam (reported)
- Season: Kharif
- Water: Reliable supply / borewell
- Expected behaviour: more candidates may pass affordability; high-water candidates may become eligible only if season/soil and sustainable supply also make sense. Never recommend sugarcane or paddy solely because budget/water is high.

## Scenario C — Limited seasonal water

- Area: 1.5 acres
- Budget: ₹35,000
- Soil: Black soil
- Season: Rabi
- Water: Seasonal / uncertain
- Expected behaviour: rank candidates considering season and limited water; clearly label any crop whose water, temperature or local planting window needs confirmation.

## Scenario D — Same budget, different area

Use the same crop assumptions and change land area from 0.5 acre to 1 acre. Total cultivation cost, expected gross revenue and expected total margin should scale consistently if the per-acre assumptions are unchanged. Per-acre values themselves should not double.

## Scenario E — Soil change

Keep all inputs constant, then change soil texture or enter a sample soil-test pH. Recommendation explanations should update only where the catalogue has justified compatibility ranges. If no validated pH range exists for a crop, show `needs confirmation` rather than fabricating one.

## Scenario F — Season change

Switch between Kharif, Rabi and Summer. Crop suitability should change only according to documented season rules, local crop calendars or clearly labelled placeholder rules. The app should identify the selected season and explain season mismatches.

## Scenario G — Retailer discovers supply

1. Register/log in as a farmer and add a listing with crop, quantity, price, date and quality.
2. Log out; log in as a retailer.
3. Search/filter listings.
4. Open a listing and send an inquiry for a quantity.
5. Confirm data ownership, inquiry record and any status display work correctly.

## What to record during testing

For each run, record input profile, top 3 results, score components, assumed values, cost/revenue units, warnings, and whether the outcome changed for a reasonable reason. Do not evaluate success solely by one crop being ranked first.


## Scenario H — Oversupplied crop vs. demand gap

- Keep farmer budget, soil, area, season and water fixed.
- Compare two market inputs/signals: (a) crop supply materially exceeds recorded buyer demand; (b) recorded buyer demand exceeds supply.
- Expected behaviour: the first candidate receives a potential surplus/competition warning and lower market component; the second receives a possible market-gap signal and a bounded positive component. The top overall crop must still respect soil, season, water and affordability.
- Use the shipped `data/local_supply_demand_demo.csv` only for this labelled demonstration. It is synthetic, not measured in Chharoli.

## Scenario I — Missing buyer records

- Disable `MARKET_DEMO_MODE`, then use a crop with active listings but no retailer inquiries.
- Expected behaviour: demand is labelled “Insufficient supply/demand records”; it must not claim that demand is zero or that the crop is oversupplied.

## Scenario J — Actual prototype marketplace activity

- Create a non-demo active listing for a crop, then create retailer inquiries for that crop.
- Expected behaviour: the supply/demand endpoint uses app-observed listed supply and inquiry demand for that crop when both sides have usable records, labels the result as FasalSense-only activity, and does not describe it as a whole-village census.
