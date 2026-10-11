"""Baseline behavioural tests for the current rules-based prototype."""
import unittest

from app.services import CROPS, recommend
from app.market_data import build_demo_signals, signal_from_values


class RecommendationScenarioTests(unittest.TestCase):
    def test_catalogue_is_multi_crop(self):
        self.assertGreaterEqual(len(CROPS), 16)
        self.assertGreaterEqual(len({crop["name"] for crop in CROPS}), 16)

    def test_low_water_and_reliable_water_profiles_can_rank_differently(self):
        low_water = {
            "area_acres": 1,
            "budget_inr": 10000,
            "soil_type": "Sandy loam",
            "season": "Kharif",
            "water_availability": "No irrigation",
            "irrigation": "Rain-fed",
        }
        reliable_water = {
            "area_acres": 2,
            "budget_inr": 150000,
            "soil_type": "Clay loam",
            "season": "Kharif",
            "water_availability": "Reliable",
            "irrigation": "Borewell",
        }
        low_top = recommend(low_water)[0]["name"]
        high_top = recommend(reliable_water)[0]["name"]
        self.assertNotEqual(low_top, high_top)

    def test_cost_and_revenue_scale_with_area(self):
        profile = {
            "area_acres": 1,
            "budget_inr": 100000,
            "soil_type": "Loamy",
            "season": "Rabi",
            "water_availability": "Reliable",
            "irrigation": "Drip",
        }
        one_acre = {item["name"]: item for item in recommend(profile)}
        profile["area_acres"] = 2
        two_acres = {item["name"]: item for item in recommend(profile)}
        for crop in CROPS:
            name = crop["name"]
            self.assertEqual(two_acres[name]["cost_inr"], 2 * one_acre[name]["cost_inr"])
            self.assertEqual(two_acres[name]["revenue_inr"], 2 * one_acre[name]["revenue_inr"])

    def test_budget_changes_affordability_score_component(self):
        low_budget = {
            "area_acres": 1,
            "budget_inr": 1,
            "soil_type": "Loamy",
            "season": "Rabi",
            "water_availability": "Reliable",
            "irrigation": "Drip",
        }
        higher_budget = dict(low_budget, budget_inr=100000)
        low_result = {item["name"]: item for item in recommend(low_budget)}
        high_result = {item["name"]: item for item in recommend(higher_budget)}
        self.assertGreater(high_result["Wheat"]["score"], low_result["Wheat"]["score"])

    def test_supply_demand_balance_changes_market_component(self):
        profile = {
            "area_acres": 1, "budget_inr": 100000, "soil_type": "Loamy",
            "season": "Kharif", "water_availability": "Reliable", "irrigation": "Drip",
        }
        names = [crop["name"] for crop in CROPS]
        signals = build_demo_signals(names)
        key = "tomato"
        high_demand = signal_from_values(
            "Tomato", 1000, 5000, 30, "illustrative_demo", "SIMULATED TEST DATA", "test only"
        )
        surplus = signal_from_values(
            "Tomato", 8000, 1000, 30, "illustrative_demo", "SIMULATED TEST DATA", "test only"
        )
        demand_scores = {x["name"]: x["score"] for x in recommend(profile, market_signals={**signals, key: high_demand})}
        surplus_scores = {x["name"]: x["score"] for x in recommend(profile, market_signals={**signals, key: surplus})}
        self.assertGreater(demand_scores["Tomato"], surplus_scores["Tomato"])

    def test_demo_market_signals_are_explicitly_labelled(self):
        signals = build_demo_signals([crop["name"] for crop in CROPS])
        self.assertEqual(signals["tomato"]["source_type"], "illustrative_demo")
        self.assertIn("not measured in Chharoli", signals["tomato"]["data_status"])
        self.assertNotEqual(signals["tomato"]["balance_label"], "Insufficient supply/demand records")


if __name__ == "__main__":
    unittest.main()
