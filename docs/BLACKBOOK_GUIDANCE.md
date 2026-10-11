# Blackbook Guidance — Suggested Methodology

## Problem statement

Farmers must compare crop choices under budget, water, soil, season, local crop availability and buyer-demand uncertainty. A crop already available in large quantities relative to buyer demand may face surplus/competition risk; a crop with lower supply than recorded demand may represent an opportunity, subject to agronomic suitability and cost. A single market-price signal is insufficient. FasalSense demonstrates a multi-factor decision-support workflow that ranks crops using local supply/demand balance and connects produce listings to buyers.

## Objective

Develop a web-based prototype that accepts farmer-specific information, ranks multiple crop options using transparent rules, communicates the assumptions and risks behind indicative financial estimates, and provides a simple farmer-retailer marketplace.

## Proposed system modules

1. User and role management (farmer / retailer).
2. Farm profile and input validation.
3. Crop catalogue with source/evidence fields.
4. Multi-factor scoring / ranking and estimated financial calculations.
5. Weather adapter and data-status labels.
6. Soil photo preview and manual soil-test inputs (not lab-grade image prediction).
7. Market-insight display, with live source adapter only when real data is available.
8. Farmer produce listings and retailer inquiry workflow.
9. Dashboard, scenario comparison, and reports.

## Baseline recommendation method

For a student demonstrator, begin with a transparent weighted scoring model. For each candidate, evaluate:

- season compatibility;
- soil and tested pH compatibility (only when reliable crop ranges exist);
- water requirement versus reported availability;
- affordability (estimated cost versus available budget);
- local supply quantity versus retailer/buyer demand quantity over a stated window, the resulting balance category, and source/data-quality label;
- market-price signal with source/date quality, if available;
- margin range and risk.

Return a score and reasons, not a prediction of certain success. Avoid using score values as probabilities. Show the assumptions used. If using any trained model, document the dataset, licensing, target variable, training/test split, metrics, baseline, and limitations separately from rule-based scoring.

## Financial formulas

For consistent units:

- `Total estimated cultivation cost = estimated cost per acre × area in acres`
- `Estimated gross revenue = estimated yield per acre × area in acres × expected sale price per yield unit`
- `Estimated operating margin = estimated gross revenue − listed operating costs`

The result should state which costs are omitted. Use sensitivity/range analysis where input costs, yield or selling price are uncertain. A displayed margin is not a guaranteed profit.

## Testing approach

Test typical inputs, boundary values, missing/unknown soil values, very low and high budget, no/limited/reliable water, all seasons, and several land sizes. Verify authorization on protected farmer/retailer workflows. Verify API outage states for weather/market integrations. Do not report a model accuracy number without evaluating a genuinely trained model against withheld data.

## Limitations and future scope

- Chharoli-specific validated crop records may not be publicly available; use district evidence as regional context and label the distinction.
- Sample costs, yields and market prices are illustrative until dated/local sources are verified. The included 30-day supply/demand quantities are synthetic demo values, not estimates verified for Chharoli.
- Soil photos cannot reliably quantify pH/NPK without a validated data/model pipeline; lab tests remain the correct source.
- Weather station/gridded forecast and groundwater data are not equivalent to farm-specific water availability.
- Farmer-reported/app database counts are not an official survey.
- Future extension: voluntary crop/harvest survey in the village, retailer-demand surveys, verified mandi-arrival data, market API, calibrated crop-economic ranges, local agronomist review, model training/evaluation if suitable data is available, Marathi language and inclusive UX.
