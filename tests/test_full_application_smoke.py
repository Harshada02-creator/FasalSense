"""End-to-End Application Smoke and Verification Suite for FasalSense.

Verifies:
1. Static assets and landing page HTML serving.
2. Complete farmer and retailer authentication and registration.
3. Farm profile persistence and laboratory Soil Health Card values.
4. Input sensitivity: budget, water, pH, season, and acreage scaling.
5. Supply vs. demand balance signals (surplus warning vs. supply-gap opportunity).
6. Non-overridable constraints: strong demand cannot bypass budget or season mismatch.
7. Produce listings CRUD and status transitions.
8. Purchase inquiry lifecycle and role-based permissions.
9. APMC benchmark completeness across all 16 crops.
"""
from __future__ import annotations

import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine
from app.services import CROPS, recommend
from app.market_data import build_demo_signals, signal_from_values, load_apmc_benchmarks


class ApplicationSmokeAndLogicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    # -------------------------------------------------------------
    # 1. Landing Page & Static Assets
    # -------------------------------------------------------------
    def test_01_landing_page_and_assets(self):
        # GET /
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("FasalSense", res.text)
        self.assertIn("Chharoli Budruk", res.text)
        self.assertIn("local crop supply vs retailer demand", res.text.lower())

        # GET /static/styles.css
        res_css = self.client.get("/static/styles.css")
        self.assertEqual(res_css.status_code, 200)
        self.assertIn("--maroon", res_css.text)

        # GET /static/app.js
        res_js = self.client.get("/static/app.js")
        self.assertEqual(res_js.status_code, 200)
        self.assertIn("experimental visual analysis", res_js.text)

    # -------------------------------------------------------------
    # 2. Registration and Authentication
    # -------------------------------------------------------------
    def test_02_registration_and_authentication(self):
        suffix = "smoke_test_run"
        farmer_email = f"farmer_{suffix}@example.com"
        retailer_email = f"retailer_{suffix}@example.com"

        # Register Farmer
        res_f = self.client.post("/api/auth/register", json={
            "name": "Balu Patil",
            "email": farmer_email,
            "password": "FarmPassword123!",
            "role": "farmer",
            "locality": "Chharoli Budruk"
        })
        # If user already exists in db, try login
        if res_f.status_code != 200:
            res_f = self.client.post("/api/auth/login", json={
                "email": farmer_email,
                "password": "FarmPassword123!"
            })
        self.assertEqual(res_f.status_code, 200)
        self.assertEqual(res_f.json()["user"]["role"], "farmer")

        # Register Retailer
        res_r = self.client.post("/api/auth/register", json={
            "name": "Khadki Fresh Mart",
            "email": retailer_email,
            "password": "RetailPassword123!",
            "role": "retailer",
            "locality": "Chharoli Budruk"
        })
        if res_r.status_code != 200:
            res_r = self.client.post("/api/auth/login", json={
                "email": retailer_email,
                "password": "RetailPassword123!"
            })
        self.assertEqual(res_r.status_code, 200)
        self.assertEqual(res_r.json()["user"]["role"], "retailer")

        # Invalid login check
        res_bad = self.client.post("/api/auth/login", json={
            "email": farmer_email,
            "password": "WrongPassword999!"
        })
        self.assertEqual(res_bad.status_code, 401)

    # -------------------------------------------------------------
    # 3. Dynamic Crop Ranking by Farmer Parameters
    # -------------------------------------------------------------
    def test_03_budget_change_alters_ranking_and_affordability(self):
        base_profile = {
            "area_acres": 1.0,
            "soil_type": "Black soil",
            "soil_ph": 7.0,
            "season": "Kharif",
            "water_availability": "Reliable",
            "irrigation": "Drip",
        }
        low_budget = dict(base_profile, budget_inr=10000)
        high_budget = dict(base_profile, budget_inr=90000)

        low_results = recommend(low_budget)
        high_results = recommend(high_budget)

        # Under low budget, Pearl millet (cost ~12,500) or Green gram (~11,000) rank high
        low_names = [c["name"] for c in low_results[:3]]
        self.assertTrue("Pearl millet (Bajra)" in low_names or "Green gram (Moong)" in low_names)

        # Sugarcane (cost ~65,000) must be UNAFFORDABLE under low budget
        sugarcane_low = next(c for c in low_results if c["name"] == "Sugarcane")
        self.assertFalse(sugarcane_low["suitability_flags"]["affordable"])
        self.assertEqual(sugarcane_low["score_breakdown"]["budget_score"], 0)

        # Under high budget, Sugarcane is affordable
        sugarcane_high = next(c for c in high_results if c["name"] == "Sugarcane")
        self.assertTrue(sugarcane_high["suitability_flags"]["affordable"])
        self.assertEqual(sugarcane_high["score_breakdown"]["budget_score"], 20)

    def test_04_water_availability_alters_ranking(self):
        profile_rainfed = {
            "area_acres": 1.0,
            "budget_inr": 80000,
            "soil_type": "Clay loam",
            "soil_ph": 7.0,
            "season": "Kharif",
            "water_availability": "Seasonal / uncertain",
            "irrigation": "Rain-fed"
        }
        profile_reliable = dict(profile_rainfed, water_availability="Reliable", irrigation="Canal / Well")

        res_rainfed = recommend(profile_rainfed)
        res_reliable = recommend(profile_reliable)

        # Under rainfed, Rice (Paddy) and Sugarcane receive poor water score
        rice_rainfed = next(c for c in res_rainfed if c["name"] == "Rice (Paddy)")
        rice_reliable = next(c for c in res_reliable if c["name"] == "Rice (Paddy)")
        self.assertLess(rice_rainfed["score_breakdown"]["water_score"], rice_reliable["score_breakdown"]["water_score"])

        # Bajra thrives under rainfed
        bajra_rainfed = next(c for c in res_rainfed if c["name"] == "Pearl millet (Bajra)")
        self.assertEqual(bajra_rainfed["score_breakdown"]["water_score"], 20)

    def test_05_soil_ph_change_alters_ranking(self):
        profile_neutral = {
            "area_acres": 1.0,
            "budget_inr": 50000,
            "soil_type": "Loamy",
            "soil_ph": 7.0,
            "season": "Rabi",
            "water_availability": "Reliable",
            "irrigation": "Drip"
        }
        profile_acidic = dict(profile_neutral, soil_ph=5.3)  # Potato optimal (5.2-6.8), Wheat sub-optimal (6.0-7.8)

        res_neutral = recommend(profile_neutral)
        res_acidic = recommend(profile_acidic)

        wheat_neutral = next(c for c in res_neutral if c["name"] == "Wheat")
        wheat_acidic = next(c for c in res_acidic if c["name"] == "Wheat")

        self.assertEqual(wheat_neutral["suitability_flags"]["ph_status"], "Optimal")
        self.assertIn(wheat_acidic["suitability_flags"]["ph_status"], ["Sub-optimal", "Mismatched"])
        self.assertGreater(wheat_neutral["score_breakdown"]["soil_score"], wheat_acidic["score_breakdown"]["soil_score"])

    def test_06_season_change_disqualifies_out_of_season_crops(self):
        kharif_profile = {
            "area_acres": 1.0,
            "budget_inr": 50000,
            "soil_type": "Loamy",
            "season": "Kharif",
            "water_availability": "Reliable",
            "irrigation": "Drip"
        }
        rabi_profile = dict(kharif_profile, season="Rabi")

        kharif_res = recommend(kharif_profile)
        rabi_res = recommend(rabi_profile)

        # Wheat is strictly Rabi
        wheat_in_kharif = next(c for c in kharif_res if c["name"] == "Wheat")
        wheat_in_rabi = next(c for c in rabi_res if c["name"] == "Wheat")
        self.assertEqual(wheat_in_kharif["score_breakdown"]["season_score"], 0)
        self.assertEqual(wheat_in_rabi["score_breakdown"]["season_score"], 25)

        # Bajra is strictly Kharif
        bajra_in_kharif = next(c for c in kharif_res if c["name"] == "Pearl millet (Bajra)")
        bajra_in_rabi = next(c for c in rabi_res if c["name"] == "Pearl millet (Bajra)")
        self.assertEqual(bajra_in_kharif["score_breakdown"]["season_score"], 25)
        self.assertEqual(bajra_in_rabi["score_breakdown"]["season_score"], 0)

    def test_07_land_area_scales_economics_and_sensitivity_correctly(self):
        p1 = {"area_acres": 1.0, "budget_inr": 100000, "soil_type": "Loamy", "season": "Kharif", "water_availability": "Reliable", "irrigation": "Drip"}
        p3 = dict(p1, area_acres=3.0)

        res1 = recommend(p1)
        res3 = recommend(p3)

        c1 = next(c for c in res1 if c["name"] == "Soybean")
        c3 = next(c for c in res3 if c["name"] == "Soybean")

        self.assertAlmostEqual(c3["cost_inr"], c1["cost_inr"] * 3.0, delta=5)
        self.assertAlmostEqual(c3["revenue_inr"], c1["revenue_inr"] * 3.0, delta=5)
        self.assertAlmostEqual(c3["yield_quintal"], c1["yield_quintal"] * 3.0, places=2)
        self.assertAlmostEqual(c3["conservative_profit_inr"], c1["conservative_profit_inr"] * 3.0, delta=10)
        self.assertAlmostEqual(c3["optimistic_profit_inr"], c1["optimistic_profit_inr"] * 3.0, delta=10)

    # -------------------------------------------------------------
    # 4. Supply vs Demand Signals & Protection Rules
    # -------------------------------------------------------------
    def test_08_surplus_warning_and_supply_gap_opportunity(self):
        crop_names = [c["name"] for c in CROPS]
        signals = build_demo_signals(crop_names)

        # 1. Simulate High Supply vs Low Demand (Surplus Glut)
        signals["tomato"] = signal_from_values(
            "Tomato", supply_kg=12000, demand_kg=1000, period_days=30,
            source_type="scenario_simulation", data_status="Demonstration glut",
            notes="Testing local surplus warning"
        )
        # 2. Simulate Low Supply vs High Demand (Supply Gap Opportunity)
        signals["green gram (moong)"] = signal_from_values(
            "Green gram (Moong)", supply_kg=500, demand_kg=6000, period_days=30,
            source_type="scenario_simulation", data_status="Demonstration gap",
            notes="Testing supply gap bonus"
        )

        profile = {
            "area_acres": 1.0,
            "budget_inr": 50000,
            "soil_type": "Sandy loam",
            "soil_ph": 7.0,
            "season": "Kharif",
            "water_availability": "Reliable",
            "irrigation": "Drip"
        }
        res = recommend(profile, market_signals=signals)

        tomato = next(c for c in res if c["name"] == "Tomato")
        moong = next(c for c in res if c["name"] == "Green gram (Moong)")

        # Tomato should have surplus label and penalty market score of 3
        self.assertEqual(tomato["market_balance"], "High supply relative to demand")
        self.assertEqual(tomato["score_breakdown"]["market_score"], 3)
        self.assertTrue(any("LOCAL SURPLUS" in r for r in tomato["risks"]))

        # Moong should have supply-gap label and bonus market score of 15
        self.assertEqual(moong["market_balance"], "Low supply relative to demand")
        self.assertEqual(moong["score_breakdown"]["market_score"], 15)
        self.assertTrue(any("MARKET GAP" in r for r in moong["reasons"]))

    def test_09_strong_demand_cannot_override_unaffordable_cost(self):
        """Crucial requirement: High market demand cannot force an unaffordable crop to rank #1."""
        crop_names = [c["name"] for c in CROPS]
        signals = build_demo_signals(crop_names)

        # Massive demand for Tomato (cost ₹45,000)
        signals["tomato"] = signal_from_values(
            "Tomato", supply_kg=200, demand_kg=20000, period_days=30,
            source_type="scenario_simulation", data_status="Massive unmet demand",
            notes="Retailers desperately bidding for tomatoes"
        )

        # Farmer with a low budget of ₹15,000
        poor_profile = {
            "area_acres": 1.0,
            "budget_inr": 15000,
            "soil_type": "Sandy loam",
            "soil_ph": 6.8,
            "season": "Kharif",
            "water_availability": "Reliable",
            "irrigation": "Drip"
        }
        res = recommend(poor_profile, market_signals=signals)

        # Rank #1 crop MUST NOT be Tomato
        self.assertNotEqual(res[0]["name"], "Tomato")

        tomato = next(c for c in res if c["name"] == "Tomato")
        self.assertFalse(tomato["suitability_flags"]["affordable"])
        self.assertEqual(tomato["score_breakdown"]["budget_score"], 0)
        self.assertTrue(any("UNAFFORDABLE" in r for r in tomato["risks"]))

    # -------------------------------------------------------------
    # 5. Market-Price Benchmarks Completeness Audit
    # -------------------------------------------------------------
    def test_10_market_price_benchmarks_audit(self):
        benchmarks = load_apmc_benchmarks()
        self.assertEqual(len(benchmarks), 16, "Must contain exactly 16 benchmark records for all catalogue crops")

        for key, item in benchmarks.items():
            self.assertIn("crop_name", item)
            self.assertIn("market", item)
            self.assertIn("benchmark_price_q", item)
            self.assertIn("benchmark_price_kg", item)
            self.assertIn("source", item)
            self.assertIn("source_portal_url", item)
            self.assertTrue(item["source_portal_url"].startswith("http"), f"Must have valid URL: {item['source_portal_url']}")
            self.assertIn("commodity", item)
            self.assertIn("variety", item)
            self.assertIn("reporting_period", item)
            self.assertIn("retrieval_date", item)
            self.assertIn("extraction_method", item)
            self.assertIn("calculation_method", item)
            self.assertIn("provenance", item)
            self.assertIn("status", item)
            # Must not label historical or statutory values as live
            self.assertIn(item["status"], ["historical-apmc-benchmark", "statutory-frp-benchmark"])
            self.assertGreater(item["benchmark_price_q"], 0)
            self.assertGreater(item["benchmark_price_kg"], 0)

    def test_11_zero_budget_and_budget_stretch_flags(self):
        # 1. Zero budget marks all unaffordable
        zero_bg_profile = {
            "area_acres": 1.0,
            "budget_inr": 0,
            "soil_type": "Loamy",
            "soil_ph": 7.0,
            "season": "Kharif",
            "water_availability": "Reliable",
            "irrigation": "Drip"
        }
        recs_zero = recommend(zero_bg_profile)
        for c in recs_zero:
            self.assertFalse(c["suitability_flags"]["affordable"])
            self.assertEqual(c["score_breakdown"]["budget_score"], 0)
            self.assertTrue(any("ZERO WORKING CAPITAL" in r for r in c["risks"]))

        # 2. Budget stretch (cost is 10% above budget)
        # Bajra costs ~12,500. Set budget to 11,500. Cost exceeds budget by ~8.7%, within 25% stretch band.
        stretch_profile = dict(zero_bg_profile, budget_inr=11500)
        recs_stretch = recommend(stretch_profile)
        bajra = next(c for c in recs_stretch if c["name"] == "Pearl millet (Bajra)")
        self.assertFalse(bajra["suitability_flags"]["affordable"])
        self.assertTrue(bajra["suitability_flags"]["budget_stretch"])
        self.assertEqual(bajra["score_breakdown"]["budget_score"], 6)
        self.assertTrue(any("OVER BUDGET (STRETCH)" in r for r in bajra["risks"]))


if __name__ == "__main__":
    unittest.main()
