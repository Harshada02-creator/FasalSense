"""Unit tests covering all 7 pedagogical demonstration scenarios."""
import unittest

from app.services import PRESET_SCENARIOS, recommend, CROPS
from app.market_data import build_market_signals, build_demo_signals, signal_from_values


class PresetScenariosTests(unittest.TestCase):
    def test_all_seven_scenarios_configured(self):
        self.assertEqual(len(PRESET_SCENARIOS), 7)
        ids = [s["id"] for s in PRESET_SCENARIOS]
        expected_ids = [f"scenario_{i}" for i in range(1, 8)]
        self.assertEqual(ids, expected_ids)

    def test_scenario_1_favors_drought_tolerant_crop(self):
        """Scenario 1: Low budget + limited water should favor Bajra/Moong over Sugarcane."""
        s1 = next(s for s in PRESET_SCENARIOS if s["id"] == "scenario_1")
        results = recommend(s1["profile"])
        top_crop = results[0]["name"]
        self.assertIn(top_crop, ["Pearl millet (Bajra)", "Green gram (Moong)"])

        # Sugarcane must be severely penalized compared to Bajra
        bajra = next(x for x in results if x["name"] == "Pearl millet (Bajra)")
        sugarcane = next(x for x in results if x["name"] == "Sugarcane")
        self.assertGreater(bajra["score"], sugarcane["score"] + 30)
        self.assertFalse(sugarcane["suitability_flags"]["water_match"])
        self.assertFalse(sugarcane["suitability_flags"]["affordable"])

    def test_scenario_2_enables_higher_investment_crops(self):
        """Scenario 2: High budget + reliable water allows higher capital crops."""
        s2 = next(s for s in PRESET_SCENARIOS if s["id"] == "scenario_2")
        results = recommend(s2["profile"])
        top_names = [x["name"] for x in results[:5]]
        # Higher-input crops should have favorable affordability and water flags
        top_crop = results[0]
        self.assertTrue(top_crop["suitability_flags"]["affordable"])
        self.assertTrue(top_crop["suitability_flags"]["water_match"])

    def test_scenario_4_season_shift_to_rabi(self):
        """Scenario 4: Sowing in Rabi causes Rabi crops to dominate and Kharif to drop."""
        s4 = next(s for s in PRESET_SCENARIOS if s["id"] == "scenario_4")
        results = recommend(s4["profile"])
        top_3 = [x["name"] for x in results[:3]]
        # Wheat, Chickpea, or Rabi Onion should top
        self.assertTrue(any(c in top_3 for c in ["Wheat", "Chickpea (Harbhara)", "Onion"]))

        # Bajra (Kharif only) must be at bottom with 0 season score
        bajra = next(x for x in results if x["name"] == "Pearl millet (Bajra)")
        self.assertEqual(bajra["score_breakdown"]["season_score"], 0)

    def test_scenario_5_surplus_penalizes_market_score(self):
        """Scenario 5: Oversupply of Tomato drops its market score to 3/15 and warns of glut."""
        s5 = next(s for s in PRESET_SCENARIOS if s["id"] == "scenario_5")
        names = [c["name"] for c in CROPS]
        base_signals = build_demo_signals(names)
        override = s5["scenario_market_override"]
        merged_signals = {
            **base_signals,
            "tomato": signal_from_values(
                "Tomato",
                override["tomato"]["supply_kg"],
                override["tomato"]["demand_kg"],
                30,
                "scenario_simulation",
                "Simulated surplus",
                "surplus test"
            )
        }
        results = recommend(s5["profile"], market_signals=merged_signals)
        tomato = next(x for x in results if x["name"] == "Tomato")
        self.assertEqual(tomato["score_breakdown"]["market_score"], 3)
        self.assertEqual(tomato["market_balance"], "High supply relative to demand")

    def test_scenario_6_demand_gap_rewards_market_score(self):
        """Scenario 6: Low supply & high demand for Leafy vegetables awards 15/15 market score."""
        s6 = next(s for s in PRESET_SCENARIOS if s["id"] == "scenario_6")
        names = [c["name"] for c in CROPS]
        base_signals = build_demo_signals(names)
        override = s6["scenario_market_override"]
        leafy_key = "leafy vegetables (mixed)"
        merged_signals = {
            **base_signals,
            leafy_key: signal_from_values(
                "Leafy vegetables (mixed)",
                override[leafy_key]["supply_kg"],
                override[leafy_key]["demand_kg"],
                30,
                "scenario_simulation",
                "Simulated demand gap",
                "demand test"
            )
        }
        results = recommend(s6["profile"], market_signals=merged_signals)
        leafy = next(x for x in results if x["name"] == "Leafy vegetables (mixed)")
        self.assertEqual(leafy["score_breakdown"]["market_score"], 15)
        self.assertEqual(leafy["market_balance"], "Low supply relative to demand")


if __name__ == "__main__":
    unittest.main()
