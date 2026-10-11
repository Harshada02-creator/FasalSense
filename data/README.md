# Data directory

`crop_catalogue_seed.json` and `crop_catalogue_seed.csv` are copies of the current hard-coded prototype crop catalogue extracted from `app/services.py`. They are provided for review and migration to a data-driven configuration. The `app/services.py` file is still the current runtime source of truth until Antigravity implements and tests catalogue loading.

All numeric crop-economics values are illustrative placeholders. The source column indicates evidence context, not a claim that a crop is widely grown in Chharoli.

`district_crop_candidates.csv` includes additional named crops from a Pune district-level NABARD planning document. They are expansion candidates to assess, not a required or village-verified list.

`local_supply_demand_demo.csv` contains synthetic crop supply/demand quantities over a 30-day example window. They are deliberately fake demonstration inputs used to make the recommender show surplus/balanced/possible-gap scenarios. They are **not observations or estimates verified in Chharoli**. Do not quote these numbers as actual local supply/demand in a report.
