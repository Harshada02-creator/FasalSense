# Product Specification — FasalSense

## Purpose

FasalSense is a student prototype for Chharoli Budruk that helps farmers compare crop choices using farm constraints AND a crop-by-crop supply-versus-buyer-demand signal. The system should identify whether a crop appears plentiful relative to recorded demand, broadly balanced, or less available than demand. This market balance is a core recommendation component, not merely a sidebar or optional insight. It must be combined with soil/season/water suitability, affordability, estimated cost/yield/returns and risk.

## Intended flow

1. **Landing page:** explain the value proposition and offer clear Farmer and Retailer entry points.
2. **Registration/login:** role is explicit (`farmer` or `retailer`). The page/dashboard content and protected API routes respect the role.
3. **Farmer profile:** land area, budget, season, soil type, optional lab-tested pH/NPK, irrigation method, self-reported water availability, optional current crop and experience/preferences.
4. **Soil step:** upload an image for preview and explain visual analysis limits. A photo must not be presented as reliable pH/NPK measurement. Soil-test values are optional and labelled with their source.
5. **Local supply-vs-demand analysis (CORE FEATURE):** for each crop, estimate how much is already available in the local market context, how much buyers are asking for, and whether the balance suggests likely surplus/competition, approximate balance, or a possible supply gap. Use crop-level quantities and source/evidence labels, not just a generic “demand is high” tag or price chart.
6. **Recommendation:** combine local supply/demand balance with soil/season/water suitability, budget fit, cultivation cost, estimated yield/returns, crop duration and risk. Explain how a crop's availability/demand balance affected its ranking.
7. **Scenario comparison:** allow changes to budget, water, season, soil and area; recalculate and compare rankings. Also let the demo compare market scenarios such as “large existing supply” versus “higher buyer demand”.
8. **Market/insights:** present a crop-by-crop supply/demand table or chart, and separate actual app activity, verified public market data and static demonstration data. Source, period, location and update labels must be visible.
8. **Farmer marketplace:** create and manage produce listings with quantity, price, quality, availability and description.
9. **Retailer marketplace:** search and filter active listings, view whether a listing is demo data, and send inquiries.
10. **Method/limitations:** include an accessible explanation of how the recommendation is calculated and what is not yet validated.

## Main inputs

- Budget: Indian rupees (INR), total available for cultivation on the selected area.
- Area: acres (make it clear whether any fields or sources use hectares).
- Season: Kharif, Rabi, Summer / local equivalent. Validate planting windows from reliable sources before treating a season as a rule.
- Soil: soil texture/category; optional lab-tested pH and N/P/K.
- Water: no irrigation/rain-fed, limited, seasonal/uncertain, or reliable; irrigation method separately recorded.
- Weather: sourced forecast if available, with source/fetched time.
- Market context is a key input: local crop supply/availability quantity, recorded buyer demand quantity, supply-demand balance status, and where possible dated prices/market arrivals. Use actual dated data where connected, or explicitly labelled static demonstration values. Missing demand observations must be marked unknown, not silently treated as zero.
- Optional preferences: crop duration, risk tolerance, preferred crop families, buyer access, and storage/transport ability if relevant.

## Recommended result structure

For each candidate crop return/display:

- Name, category and candidate status.
- Prototype suitability score and component breakdown, including the market-balance component.
- Season compatibility and known conflicts.
- Soil/pH compatibility status (`fits`, `needs confirmation`, or `potential mismatch`).
- Water needs and relationship to the farmer's reported supply.
- Local availability / supply quantity and buyer demand quantity, their period, the balance category (possible surplus / balanced / possible supply gap), evidence status and market-score effect.
- Estimated cultivation cost and unit basis.
- Estimated yield and price basis/range, source and date.
- Estimated gross revenue, estimated expenses and net operating margin.
- Duration, risk summary, and reasons for/against.
- Data provenance status: verified/source-backed, district-level reference, farmer-reported, or illustrative.

## User interface principles

- Use a warm, modern Indian agriculture visual identity (ivory, earth-brown/maroon, terracotta, muted leaf green); keep the layout clean and not cluttered.
- Make charts meaningful and accessible, with labels as well as colour.
- Provide responsive cards, input sliders where useful, validation messages, loading states, empty states and API error states.
- Preserve readable language: “estimated return” not “guaranteed profit”; “soil photo preview” not “AI pH detection” unless truly implemented and validated.
- Clearly identify app-registration counts as FasalSense-only statistics, not a census of Chharoli.

## Out of scope for this prototype

- Guaranteed crop profitability or guaranteed yield.
- Official census of all farmers/crops in Chharoli.
- Farm-specific groundwater levels or sensor data without a verified connection.
- Automatic lab-grade soil chemistry from a regular photo.
- Real purchasing/payment transactions, unless separately scoped and safely implemented.
- Any claim of validated local model accuracy without an evaluation dataset and measured results.
