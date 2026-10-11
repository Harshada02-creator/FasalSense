# Reference Links for Further Verification

These links are starting points for Antigravity to review and cite. A link existing does not mean a dataset has already been downloaded, parsed, integrated, or validated against Chharoli.

| Topic | Source | What it can support | Important limitation |
|---|---|---|---|
| Pune district crop context | NABARD Pune District PLP 2022–23: https://www.nabard.org/auth/writereaddata/tender/1012212259Pune.pdf | Historical district-level crop/scale-of-finance references | Uses FY 2021–22 scale-of-finance table; not a village census or current price feed |
| Maharashtra daily rainfall | National Water Data Portal: https://nwdp.nwic.gov.in/en/dataset/rainfall-maharashtra-surface-water-manual-daily | Rainfall station records and CSV/API catalogue | Must check station location/time coverage; not farm's actual available water |
| Soil Health Card | https://soilhealth.dac.gov.in/ | Context for tested soil properties / soil-health workflows | Does not let a regular photo reveal exact soil pH/NPK |
| Soil Health Card background | https://www.nic.gov.in/project/soil-health-card-portal/ | Explains sample collection and laboratory workflow | General portal information, not Chharoli-specific soil results |
| Mandi prices | https://agmarknet.gov.in/ | Candidate source for crop/market/date commodity price data | Confirm the exact access method, units, data period and update time before coding integration |
| Government open data | https://data.gov.in/ | Dataset catalogue and APIs | Record the exact dataset/schema/source date used |
| Weather | https://open-meteo.com/ | Current starter forecast integration | Exact coordinate and terms/attribution should be checked |
| Groundwater | https://cgwb.gov.in/ | Published groundwater reports / station context | Only appropriate if a relevant location, well and observation period are identified |


## Supply/demand implementation note

The starter currently uses `data/local_supply_demand_demo.csv` for a clearly labelled synthetic scenario signal, plus observed FasalSense active listings and buyer inquiries when both sides have records. This local app data is not an external public source and must not be cited as actual Chharoli production or demand. External official mandi-arrival or other compatible supply/demand datasets are still to be investigated and verified before any village-/area-wide claims are made.
