"""Comprehensive unit tests for the FasalSense Crop Recommendation Engine."""
import unittest

from app.services import CROPS, recommend
from app.market_data import build_demo_signals, signal_from_values


class CropEngineUnitTests(unittest.TestCase):
    def test_ph_evaluation_changes_soil_score(self):
        """Test that soil pH within optimal range scores higher than severe mismatch."""
        optimal_profile = {
            "area_acres": 1.0,
            "budget_inr": 50000,
            "soil_type": "Loamy",
            "soil_ph": 6.8,  # Optimal for Wheat (6.0-7.8)
            "season": "Rabi",
            "water_availability": "Reliable",
            "irrigation": "Canal"
        }
        acidic_mismatch_profile = dict(optimal_profile, soil_ph=4.5)  # Severe acid mismatch for Wheat

        optimal_res = {x["name"]: x for x in recommend(optimal_profile)}
        mismatch_res = {x["name"]: x for x in recommend(acidic_mismatch_profile)}

        # Wheat soil score should be strictly higher when pH is optimal
        self.assertGreater(
            optimal_res["Wheat"]["score_breakdown"]["soil_score"],
            mismatch_res["Wheat"]["score_breakdown"]["soil_score"]
        )
        self.assertEqual(optimal_res["Wheat"]["suitability_flags"]["ph_status"], "Optimal")
        self.assertEqual(mismatch_res["Wheat"]["suitability_flags"]["ph_status"], "Mismatched")

    def test_season_mismatch_zeroes_season_score(self):
        """Test that out-of-season crops receive 0 for season score."""
        kharif_profile = {
            "area_acres": 1.0,
            "budget_inr": 50000,
            "soil_type": "Loamy",
            "season": "Kharif",
            "water_availability": "Reliable",
            "irrigation": "Drip"
        }
        res = {x["name"]: x for x in recommend(kharif_profile)}
        # Wheat is Rabi only
        self.assertEqual(res["Wheat"]["score_breakdown"]["season_score"], 0)
        self.assertFalse(res["Wheat"]["suitability_flags"]["season_match"])

        # Bajra is Kharif
        self.assertEqual(res["Pearl millet (Bajra)"]["score_breakdown"]["season_score"], 25)
        self.assertTrue(res["Pearl millet (Bajra)"]["suitability_flags"]["season_match"])

    def test_unaffordable_crop_heavily_penalized(self):
        """Test that when cultivation cost significantly exceeds budget, budget score drops to 0."""
        shoestring_budget = {
            "area_acres": 1.0,
            "budget_inr": 12000,  # Sugarcane costs 65,000; Bajra costs 12,500
            "soil_type": "Loamy",
            "season": "Kharif",
            "water_availability": "Reliable",
            "irrigation": "Drip"
        }
        res = {x["name"]: x for x in recommend(shoestring_budget)}
        self.assertEqual(res["Sugarcane"]["score_breakdown"]["budget_score"], 0)
        self.assertFalse(res["Sugarcane"]["suitability_flags"]["affordable"])

        # Bajra is slightly near budget, should score much higher on budget
        self.assertGreater(
            res["Pearl millet (Bajra)"]["score_breakdown"]["budget_score"],
            res["Sugarcane"]["score_breakdown"]["budget_score"]
        )

    def test_high_demand_does_not_override_unaffordable_cost(self):
        """Crucial test: High market demand cannot force an unaffordable crop to rank #1."""
        profile = {
            "area_acres": 1.0,
            "budget_inr": 15000,  # Tomato costs 45,000
            "soil_type": "Sandy loam",
            "season": "Kharif",
            "water_availability": "Reliable",
            "irrigation": "Drip"
        }
        names = [c["name"] for c in CROPS]
        signals = build_demo_signals(names)

        # Force massive retailer demand for Tomato
        huge_tomato_demand = signal_from_values(
            "Tomato", 500, 10000, 30, "scenario_simulation", "Huge demand signal", "testing"
        )
        signals["tomato"] = huge_tomato_demand

        results = recommend(profile, market_signals=signals)
        top_crop = results[0]

        # Tomato should NOT be rank #1 because it costs 45,000 vs 15,000 budget
        self.assertNotEqual(top_crop["name"], "Tomato")
        self.assertFalse(results[[x["name"] for x in results].index("Tomato")]["suitability_flags"]["affordable"])

    def test_water_constraints_penalize_sugarcane_under_drought(self):
        """Test that water-intensive crops fail when water availability is limited."""
        drought_profile = {
            "area_acres": 1.0,
            "budget_inr": 100000,
            "soil_type": "Clay loam",
            "season": "Kharif",
            "water_availability": "No irrigation",
            "irrigation": "Rain-fed"
        }
        res = {x["name"]: x for x in recommend(drought_profile)}
        self.assertEqual(res["Sugarcane"]["score_breakdown"]["water_score"], 2)
        self.assertFalse(res["Sugarcane"]["suitability_flags"]["water_match"])

        # Drought tolerant Bajra should receive maximum water score
        self.assertEqual(res["Pearl millet (Bajra)"]["score_breakdown"]["water_score"], 20)


if __name__ == "__main__":
    unittest.main()
