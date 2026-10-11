"""Crop recommendation engine and weather services for FasalSense.

Implements a transparent, multi-factor agronomic & economic decision-support model
tailored for Chharoli Budruk, Pune, Maharashtra.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import httpx

from .market_data import build_demo_signals, crop_key

ROOT = Path(__file__).resolve().parent.parent
CATALOGUE_PATH = ROOT / "data" / "crop_catalogue_seed.json"

LAT = float(os.getenv("CHHAROLI_LAT", "18.637"))
LON = float(os.getenv("CHHAROLI_LON", "73.881"))


def load_crops() -> list[dict]:
    if CATALOGUE_PATH.exists():
        try:
            with open(CATALOGUE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Built-in fallback in case JSON file is inaccessible
    return [
        {"name":"Rice (Paddy)","category":"Cereal","season":["Kharif"],"soil":["Clay loam","Loamy","Black soil","Unknown"],"water":"High","ph_min":5.5,"ph_max":7.0,"days":125,"cost_acre":26000,"yield_q_acre":20.0,"price_q":2300,"demand":"Variable — verify latest mandi rates","note":"Consider only with suitable season, reliable water, drainage and local suitability.","market_trend":"Illustrative demo signal — verify current mandi prices"},
        {"name":"Pearl millet (Bajra)","category":"Millet / Cereal","season":["Kharif"],"soil":["Sandy loam","Loamy","Black soil","Unknown"],"water":"Low","ph_min":6.5,"ph_max":8.2,"days":85,"cost_acre":12500,"yield_q_acre":4.5,"price_q":2400,"demand":"Variable","note":"Drought-tolerant cereal candidate; check local variety and sowing window.","market_trend":"Illustrative demo signal"},
        {"name":"Sorghum (Jowar)","category":"Cereal","season":["Kharif","Rabi"],"soil":["Black soil","Loamy","Clay loam","Unknown"],"water":"Low to moderate","ph_min":6.0,"ph_max":8.0,"days":105,"cost_acre":13500,"yield_q_acre":5.0,"price_q":3200,"demand":"Variable","note":"Can suit drier conditions; season and grain/fodder market matter.","market_trend":"Illustrative demo signal"},
        {"name":"Pigeon pea (Tur/Arhar)","category":"Pulse","season":["Kharif"],"soil":["Loamy","Clay loam","Black soil","Unknown"],"water":"Low to moderate","ph_min":6.5,"ph_max":7.8,"days":160,"cost_acre":16500,"yield_q_acre":3.2,"price_q":7200,"demand":"Moderate","note":"Longer-duration pulse; needs suitable season and good drainage.","market_trend":"Illustrative demo signal"},
        {"name":"Green gram (Moong)","category":"Pulse","season":["Kharif","Summer"],"soil":["Sandy loam","Loamy","Unknown"],"water":"Low to moderate","ph_min":6.2,"ph_max":7.6,"days":65,"cost_acre":11000,"yield_q_acre":2.4,"price_q":7600,"demand":"Variable","note":"Short-duration pulse; local variety, heat and sowing timing matter.","market_trend":"Illustrative demo signal"},
        {"name":"Chickpea (Harbhara)","category":"Pulse","season":["Rabi"],"soil":["Black soil","Loamy","Clay loam","Unknown"],"water":"Low to moderate","ph_min":6.0,"ph_max":8.0,"days":110,"cost_acre":14500,"yield_q_acre":3.5,"price_q":5600,"demand":"Variable","note":"Rabi pulse; residual soil moisture and temperature are important.","market_trend":"Illustrative demo signal"},
        {"name":"Wheat","category":"Cereal","season":["Rabi"],"soil":["Loamy","Clay loam","Black soil","Unknown"],"water":"Moderate","ph_min":6.0,"ph_max":7.8,"days":120,"cost_acre":19000,"yield_q_acre":8.0,"price_q":2500,"demand":"Variable","note":"Needs a suitable cool-season window and planned irrigation.","market_trend":"Illustrative demo signal"},
        {"name":"Maize","category":"Cereal","season":["Kharif","Rabi"],"soil":["Loamy","Clay loam","Unknown"],"water":"Moderate","ph_min":6.0,"ph_max":7.5,"days":100,"cost_acre":18500,"yield_q_acre":6.0,"price_q":2200,"demand":"Variable","note":"Moisture is especially important around flowering; verify buyer demand.","market_trend":"Illustrative demo signal"},
        {"name":"Soybean","category":"Oilseed / Legume","season":["Kharif"],"soil":["Black soil","Loamy","Clay loam","Unknown"],"water":"Moderate","ph_min":6.0,"ph_max":7.5,"days":100,"cost_acre":17500,"yield_q_acre":5.0,"price_q":4600,"demand":"Variable","note":"Common regional crop candidate; waterlogging and disease risk need attention.","market_trend":"Illustrative demo signal"},
        {"name":"Groundnut","category":"Oilseed","season":["Kharif","Summer"],"soil":["Sandy loam","Loamy","Unknown"],"water":"Moderate","ph_min":6.0,"ph_max":7.2,"days":115,"cost_acre":22000,"yield_q_acre":5.0,"price_q":6000,"demand":"Variable","note":"Needs suitable loose soil and moisture management; avoid waterlogging.","market_trend":"Illustrative demo signal"},
        {"name":"Onion","category":"Vegetable / Cash","season":["Rabi"],"soil":["Sandy loam","Loamy","Unknown"],"water":"Moderate","ph_min":6.2,"ph_max":7.5,"days":120,"cost_acre":38000,"yield_q_acre":65.0,"price_q":1800,"demand":"Highly variable","note":"Higher input and price risk; storage, disease and market timing matter.","market_trend":"Illustrative demo signal"},
        {"name":"Tomato","category":"Vegetable / Perishable","season":["Kharif","Rabi","Summer"],"soil":["Sandy loam","Loamy","Unknown"],"water":"Moderate","ph_min":6.0,"ph_max":7.0,"days":100,"cost_acre":45000,"yield_q_acre":100.0,"price_q":1200,"demand":"Highly variable","note":"Potentially high returns but substantial price, pest, labour and perishability risk.","market_trend":"Illustrative demo signal"},
        {"name":"Potato","category":"Vegetable / Tuber","season":["Rabi"],"soil":["Sandy loam","Loamy","Unknown"],"water":"Moderate","ph_min":5.2,"ph_max":6.8,"days":100,"cost_acre":42000,"yield_q_acre":80.0,"price_q":1400,"demand":"Variable","note":"Requires suitable temperatures, seed quality and a buyer/storage plan.","market_trend":"Illustrative demo signal"},
        {"name":"Cotton","category":"Commercial Fiber","season":["Kharif"],"soil":["Black soil","Loamy","Clay loam","Unknown"],"water":"Moderate","ph_min":6.5,"ph_max":8.0,"days":170,"cost_acre":24000,"yield_q_acre":5.0,"price_q":7000,"demand":"Variable","note":"Longer-duration crop with pest and input-cost risks; suitability must be checked.","market_trend":"Illustrative demo signal"},
        {"name":"Sugarcane","category":"Cash Crop","season":["Kharif","Rabi","Summer"],"soil":["Black soil","Loamy","Clay loam","Unknown"],"water":"High","ph_min":6.5,"ph_max":8.0,"days":300,"cost_acre":65000,"yield_q_acre":350.0,"price_q":350,"demand":"Depends on mill/buyer access","note":"Long-duration, water-intensive crop; check water sustainability, planting window and mill access.","market_trend":"Illustrative demo signal"},
        {"name":"Leafy vegetables (mixed)","category":"Vegetable / Perishable","season":["Kharif","Rabi","Summer"],"soil":["Sandy loam","Loamy","Unknown"],"water":"Moderate","ph_min":6.0,"ph_max":7.2,"days":45,"cost_acre":18000,"yield_q_acre":35.0,"price_q":1800,"demand":"Local demand dependent","note":"Short-cycle option when nearby buyers and frequent harvesting/transport are available.","market_trend":"Illustrative demo signal"}
    ]

CROPS = load_crops()


async def get_weather():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT, "longitude": LON, "timezone": "Asia/Kolkata",
        "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum",
        "forecast_days": 7
    }
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    data["location_label"] = "Chharoli Budruk, Pune (approximate center)"
    data["source"] = "Open-Meteo"
    data["fetched_at"] = datetime.now().astimezone().isoformat()
    return data


def recommend(profile: dict, weather: dict | None = None, market_signals: dict | None = None):
    """Multi-factor crop recommendation engine for FasalSense.

    Scoring is strictly structured into 5 explainable components (Max 100):
    1. Season Suitability (25 pts)
    2. Water & Irrigation Fit (20 pts)
    3. Soil & pH Compatibility (20 pts)
    4. Cultivation Budget & Affordability (20 pts)
    5. Local Supply vs Buyer Demand Balance (15 pts)

    Agronomic constraints and financial budget strictly bound rankings,
    preventing high market demand from promoting unsuitable crops.
    """
    crops_list = CROPS if CROPS else load_crops()
    if market_signals is None:
        market_signals = build_demo_signals([c["name"] for c in crops_list])

    area = max(float(profile.get("area_acres") or 1.0), 0.05)
    budget = max(float(profile.get("budget_inr") or 0.0), 0.0)
    soil = profile.get("soil_type", "Unknown")
    soil_ph = profile.get("soil_ph")
    try:
        soil_ph = float(soil_ph) if soil_ph is not None and soil_ph != "" else None
    except (ValueError, TypeError):
        soil_ph = None

    season = profile.get("season", "Kharif")
    water = profile.get("water_availability", "Seasonal / uncertain")
    irrigation = profile.get("irrigation", "Rain-fed")

    results = []
    for c in crops_list:
        reasons = []
        risks = []

        # ---------------------------------------------------------
        # 1. Season Suitability Component (Max 25 points)
        # ---------------------------------------------------------
        if season in c["season"]:
            score_season = 25
            reasons.append(f"Optimal growing window: listed for the {season} season")
            is_season_match = True
        else:
            score_season = 0
            risks.append(f"Season mismatch: {c['name']} is typically not recommended for {season} in Pune district")
            is_season_match = False

        # ---------------------------------------------------------
        # 2. Water & Irrigation Fit Component (Max 20 points)
        # ---------------------------------------------------------
        water_need = c["water"]
        water_reliable = ("Reliable" in water) or (irrigation in ["Borewell", "Canal", "Drip", "Sprinkler"])
        water_limited = ("Limited" in water) or ("No irrigation" in water) or (irrigation in ["Rain-fed", "None"])

        if water_need == "Low":
            if water_limited:
                score_water = 20
                reasons.append(f"Low water requirement: highly resilient under rain-fed / limited water")
            else:
                score_water = 18
                reasons.append(f"Low water requirement fits your available water supply")
            is_water_match = True
        elif water_need in ["Low to moderate", "Moderate"]:
            if water_reliable:
                score_water = 20
                reasons.append(f"Moderate water need aligns well with your reported irrigation access ({irrigation})")
                is_water_match = True
            elif water_limited:
                score_water = 7
                risks.append(f"Moderate water requirement poses stress risk with limited / rain-fed water")
                is_water_match = False
            else:  # seasonal / uncertain
                score_water = 14
                reasons.append("Moderate water requirement manageable with typical seasonal rainfall")
                is_water_match = True
        else:  # High water need (Paddy, Sugarcane)
            if water_reliable:
                score_water = 17
                reasons.append(f"High water requirement can be supported by {irrigation}, subject to sustainable supply")
                risks.append("Heavy water consumption: monitor local aquifer and power costs")
                is_water_match = True
            elif water_limited:
                score_water = 2
                risks.append(f"CRITICAL WATER DEFICIT: High water need is incompatible with limited/rain-fed water")
                is_water_match = False
            else:  # seasonal
                score_water = 8
                risks.append(f"Uncertain seasonal water poses severe risk for high-water crop")
                is_water_match = False

        # ---------------------------------------------------------
        # 3. Soil Texture & pH Compatibility (Max 20 points)
        # Texture: 12 pts | pH: 8 pts
        # ---------------------------------------------------------
        # Soil Texture (12 pts)
        if soil == "Unknown" or soil in c["soil"]:
            score_soil_texture = 12
            reasons.append(f"Soil type '{soil}' is compatible with agronomic requirements")
            is_soil_match = True
        else:
            score_soil_texture = 4
            risks.append(f"Soil type mismatch: '{soil}' is sub-optimal; requires soil conditioning or variety selection")
            is_soil_match = False

        # Soil pH (8 pts)
        ph_min = c.get("ph_min", 6.0)
        ph_max = c.get("ph_max", 7.5)
        if soil_ph is None:
            score_ph = 5
            ph_status = "Not tested"
            reasons.append(f"Soil pH not entered; optimal range is {ph_min}–{ph_max}")
        elif ph_min <= soil_ph <= ph_max:
            score_ph = 8
            ph_status = "Optimal"
            reasons.append(f"Tested soil pH ({soil_ph:.1f}) is within optimal range ({ph_min}–{ph_max})")
        elif (ph_min - 0.5) <= soil_ph <= (ph_max + 0.5):
            score_ph = 4
            ph_status = "Slight deviation"
            risks.append(f"Soil pH ({soil_ph:.1f}) slightly outside preferred range ({ph_min}–{ph_max}); minor yield impact possible")
        else:
            score_ph = 0
            ph_status = "Mismatched"
            risks.append(f"Soil pH ({soil_ph:.1f}) significantly deviates from suitable range ({ph_min}–{ph_max}); risk of nutrient lockout")

        score_soil = score_soil_texture + score_ph

        # ---------------------------------------------------------
        # 4. Local Supply vs Buyer Demand Balance (Max 15 points)
        # Core Innovation Differentiator
        # ---------------------------------------------------------
        signal = market_signals.get(crop_key(c["name"])) if market_signals else None
        if not signal:
            signal = {
                "supply_kg": None, "demand_kg": None, "period_days": 30,
                "source_type": "unknown", "data_status": "Not enough comparable supply and demand data",
                "balance_label": "Insufficient supply/demand records", "supply_demand_ratio": None,
                "score_delta": 0, "notes": "Missing records are unknown, not zero supply or demand."
            }

        balance_label = signal.get("balance_label", "Insufficient supply/demand records")
        source_type = signal.get("source_type", "unknown")
        market_delta = int(signal.get("score_delta", 0) or 0)

        if balance_label == "Low supply relative to demand":
            # Buyer demand exceeds local availability: Potential market gap opportunity
            score_market = 15
            reasons.append("MARKET GAP: Recorded buyer demand exceeds local available supply; potential direct selling opportunity")
        elif balance_label == "High supply relative to demand":
            # Local availability materially exceeds buyer demand: Potential surplus / high competition
            score_market = 3
            risks.append("LOCAL SURPLUS / HIGH COMPETITION: Local supply materially exceeds recorded buyer demand; risk of unsold stock or price discounting")
        elif balance_label == "Supply and demand broadly balanced":
            score_market = 10
            reasons.append("Market balance: supply and buyer demand are broadly balanced")
        else:
            # Insufficient records: neutral baseline, neither awarded nor punished
            score_market = 8
            risks.append("Insufficient local supply/demand records; market balance is unknown (not zero demand)")

        if source_type == "illustrative_demo":
            risks.append("Market quantities are synthetic demo values, not an official census of Chharoli")
        elif source_type == "platform_activity":
            reasons.append("Market signal reflects verified FasalSense app listings and retailer inquiries (trailing 30 days)")

        # ---------------------------------------------------------
        # 5. Cultivation Cost & Affordability (Max 20 points)
        # ---------------------------------------------------------
        cost = c["cost_acre"] * area
        effective_price_q = signal.get("benchmark_price_q") if (signal and signal.get("benchmark_price_q")) else c["price_q"]
        revenue = c["yield_q_acre"] * effective_price_q * area
        profit = revenue - cost

        if budget <= 0:
            score_budget = 0
            risks.append(f"ZERO WORKING CAPITAL SPECIFIED: Cultivation of {c['name']} requires an estimated ₹{round(cost):,} for {area} acre(s); crop is marked unaffordable")
            is_affordable = False
            is_budget_stretch = False
        elif cost <= budget * 0.75:
            score_budget = 20
            reasons.append(f"Estimated cost (₹{round(cost):,}) is well within your budget (₹{round(budget):,})")
            is_affordable = True
            is_budget_stretch = False
        elif cost <= budget:
            score_budget = 16
            reasons.append(f"Estimated cost (₹{round(cost):,}) fits within your budget (₹{round(budget):,})")
            is_affordable = True
            is_budget_stretch = False
        elif cost <= budget * 1.25:
            score_budget = 6
            risks.append(f"OVER BUDGET (STRETCH): estimated cost (₹{round(cost):,}) exceeds budget (₹{round(budget):,}) by ~{round((cost-budget)/budget*100)}%")
            is_affordable = False
            is_budget_stretch = True
        else:
            score_budget = 0
            risks.append(f"UNAFFORDABLE: estimated cost (₹{round(cost):,}) substantially exceeds budget (₹{round(budget):,})")
            is_affordable = False
            is_budget_stretch = False

        if profit <= 0:
            risks.append("Estimated gross revenue under benchmark assumptions does not cover operating costs")

        # ---------------------------------------------------------
        # Total Score Aggregation (Clamped 5 - 100)
        # ---------------------------------------------------------
        raw_total = score_season + score_water + score_soil + score_budget + score_market
        final_score = max(5, min(95, raw_total))

        # Financial Sensitivity Ranges (-15% / +15% yield & price)
        conservative_rev = (c["yield_q_acre"] * 0.85) * (effective_price_q * 0.90) * area
        optimistic_rev = (c["yield_q_acre"] * 1.15) * (effective_price_q * 1.10) * area

        results.append({
            "name": c["name"],
            "category": c.get("category", "General Crop"),
            "score": final_score,
            "score_breakdown": {
                "season_score": score_season,
                "water_score": score_water,
                "soil_score": score_soil,
                "budget_score": score_budget,
                "market_score": score_market,
                "total": final_score
            },
            "suitability_flags": {
                "season_match": is_season_match,
                "water_match": is_water_match,
                "soil_match": is_soil_match,
                "affordable": is_affordable,
                "budget_stretch": is_budget_stretch,
                "ph_status": ph_status
            },
            "season": ", ".join(c["season"]),
            "water_need": c["water"],
            "duration_days": c["days"],
            "optimal_ph_range": f"{ph_min} – {ph_max}",
            "tested_soil_ph": soil_ph,
            "cost_inr": round(cost),
            "revenue_inr": round(revenue),
            "profit_inr": round(profit),
            "profit_margin_pct": round(profit / revenue * 100, 1) if revenue else 0.0,
            "conservative_profit_inr": round(conservative_rev - cost),
            "optimistic_profit_inr": round(optimistic_rev - cost),
            "yield_quintal": round(c["yield_q_acre"] * area, 2),
            "price_per_quintal": effective_price_q,
            "price_per_kg": round(effective_price_q / 100, 2),
            "price_assumption_note": "Calculations use static illustrative baseline prices derived from APMC modal benchmarks (or statutory FRP for sugarcane), not live streaming auction quotes.",
            "cost_breakdown": {k: round(v * area) for k, v in c.get("cost_breakdown", {}).items()},
            "demand": c["demand"],
            "reasons": reasons,
            "risks": risks,
            "note": c["note"],
            "market_trend": signal.get("benchmark_price_trend") or c.get("market_trend", "No verified price trend connected"),
            "market_supply_kg": signal.get("supply_kg"),
            "market_demand_kg": signal.get("demand_kg"),
            "market_period_days": signal.get("period_days", 30),
            "market_balance": balance_label,
            "market_source_type": source_type,
            "market_data_status": signal.get("data_status", "Not enough comparable supply and demand data"),
            "market_ratio": signal.get("supply_demand_ratio"),
            "market_score_delta": market_delta,
            "market_notes": signal.get("notes", ""),
            "market_benchmark_price_q": signal.get("benchmark_price_q", c["price_q"]),
            "market_benchmark_historical_range": signal.get("benchmark_historical_range", "Not available"),
            "market_benchmark_market": signal.get("benchmark_market", "Pune district benchmark"),
            "market_platform_supply_kg": signal.get("platform_supply_kg", 0),
            "market_platform_supply_listings": signal.get("platform_supply_listings", 0),
            "market_platform_demand_kg": signal.get("platform_demand_kg", 0),
            "market_platform_demand_inquiries": signal.get("platform_demand_inquiries", 0),
            "evidence_status": c.get("evidence_status", "district-level-reference"),
            "evidence_source": c.get("evidence_source", "NABARD Pune District PLP 2022-23"),
            "evidence_scope": c.get("evidence_scope", "Pune district; not village-specific census"),
            "data_status": "ILLUSTRATIVE CROP COST/YIELD/PRICE REFERENCES — NOT LIVE GUARANTEED DATA"
        })

    return sorted(results, key=lambda x: x["score"], reverse=True)


PRESET_SCENARIOS = [
    {
        "id": "scenario_1",
        "title": "Scenario 1: Low Budget & Limited Water",
        "badge": "Resource-Constrained",
        "description": "Tests how the engine prioritizes drought-tolerant, low-investment crops (e.g. Bajra, Moong) and heavily penalizes water-intensive or high-cost crops (Sugarcane, Paddy).",
        "profile": {
            "area_acres": 1.0,
            "budget_inr": 12000,
            "soil_type": "Sandy loam",
            "soil_ph": 7.0,
            "season": "Kharif",
            "irrigation": "Rain-fed",
            "water_availability": "Limited"
        },
        "pedagogical_focus": "Validates that high-water crops (Paddy/Sugarcane) cannot rank first despite high market prices, while affordable drought-tolerant crops rise."
    },
    {
        "id": "scenario_2",
        "title": "Scenario 2: High Budget & Reliable Water",
        "badge": "High Capital & Assured Water",
        "description": "Tests how reliable borewell water and capital allow evaluating crops with higher operating costs (Soybean, Tur, Tomato, Paddy) while noting water sustainability trade-offs.",
        "profile": {
            "area_acres": 2.0,
            "budget_inr": 150000,
            "soil_type": "Clay loam",
            "soil_ph": 6.8,
            "season": "Kharif",
            "irrigation": "Borewell",
            "water_availability": "Reliable"
        },
        "pedagogical_focus": "Shows that removing budget/water bottlenecks unlocks higher-input crops, but long duration and water risk remain explicit."
    },
    {
        "id": "scenario_3",
        "title": "Scenario 3: Soil Type & pH Variation",
        "badge": "Agronomic Soil Fit",
        "description": "Demonstrates how changing soil texture (Black soil vs Sandy loam) or tested pH (Acidic 5.4 vs Neutral 7.0 vs Alkaline 8.3) alters rankings and triggers pH mismatch warnings.",
        "profile": {
            "area_acres": 1.5,
            "budget_inr": 35000,
            "soil_type": "Black soil",
            "soil_ph": 7.8,
            "season": "Rabi",
            "irrigation": "Drip",
            "water_availability": "Seasonal / uncertain"
        },
        "pedagogical_focus": "Proves that soil chemistry is actively computed, penalizing crops outside their optimal pH window."
    },
    {
        "id": "scenario_4",
        "title": "Scenario 4: Growing Season Shift (Rabi / Summer)",
        "badge": "Crop Calendar Window",
        "description": "Switches the target season to Rabi. Watch Kharif-only crops (Bajra, Soybean, Tur) drop to 0 for season fit, while Rabi crops (Wheat, Harbhara, Rabi Onion) take top positions.",
        "profile": {
            "area_acres": 1.0,
            "budget_inr": 30000,
            "soil_type": "Loamy",
            "soil_ph": 6.8,
            "season": "Rabi",
            "irrigation": "Canal",
            "water_availability": "Reliable"
        },
        "pedagogical_focus": "Demonstrates that season mismatch is an absolute suitability gate (0/25 pts)."
    },
    {
        "id": "scenario_5",
        "title": "Scenario 5: High Existing Supply / Low Demand",
        "badge": "Local Market Surplus Glut",
        "description": "Simulates a local market surplus for Tomato (Supply 12,000 kg vs Demand 2,000 kg). Market score drops to 3/15 and warns of seller competition and price risk.",
        "profile": {
            "area_acres": 1.0,
            "budget_inr": 60000,
            "soil_type": "Loamy",
            "soil_ph": 6.5,
            "season": "Kharif",
            "irrigation": "Drip",
            "water_availability": "Reliable"
        },
        "scenario_market_override": {
            "tomato": {
                "crop_name": "Tomato",
                "supply_kg": 12000.0,
                "demand_kg": 2000.0,
                "period_days": 30,
                "source_type": "scenario_simulation",
                "data_status": "SIMULATED SURPLUS SCENARIO — High local tomato supply vs low retailer requests",
                "notes": "Testing surplus warning penalty"
            }
        },
        "pedagogical_focus": "Highlights the core differentiator: high local supply penalizes the market score due to glut risk."
    },
    {
        "id": "scenario_6",
        "title": "Scenario 6: Low Existing Supply / High Buyer Demand",
        "badge": "Market Gap Opportunity",
        "description": "Simulates strong unmet buyer demand for Leafy Vegetables & Moong (Retailer inquiries 4,500 kg vs listed supply 900 kg). Market score jumps to 15/15.",
        "profile": {
            "area_acres": 1.0,
            "budget_inr": 25000,
            "soil_type": "Sandy loam",
            "soil_ph": 6.8,
            "season": "Summer",
            "irrigation": "Sprinkler",
            "water_availability": "Reliable"
        },
        "scenario_market_override": {
            "leafy vegetables (mixed)": {
                "crop_name": "Leafy vegetables (mixed)",
                "supply_kg": 900.0,
                "demand_kg": 4500.0,
                "period_days": 30,
                "source_type": "scenario_simulation",
                "data_status": "SIMULATED DEMAND GAP — Strong retailer inquiry volume relative to farmer listings",
                "notes": "Testing demand gap incentive"
            }
        },
        "pedagogical_focus": "Shows how buyer demand signals identify market opportunities without guaranteeing sales."
    },
    {
        "id": "scenario_7",
        "title": "Scenario 7: Strong Demand but Unaffordable Cost",
        "badge": "Budget Gate Constraint",
        "description": "Tomato has strong buyer demand (+15 market score), but farmer's budget is only ₹15,000 against ₹45,000 cultivation cost. Budget score drops to 0/20, preventing it from ranking #1.",
        "profile": {
            "area_acres": 1.0,
            "budget_inr": 15000,
            "soil_type": "Loamy",
            "soil_ph": 6.5,
            "season": "Kharif",
            "irrigation": "Drip",
            "water_availability": "Reliable"
        },
        "scenario_market_override": {
            "tomato": {
                "crop_name": "Tomato",
                "supply_kg": 1000.0,
                "demand_kg": 8000.0,
                "period_days": 30,
                "source_type": "scenario_simulation",
                "data_status": "SIMULATED HIGH DEMAND FOR EXPENSIVE CROP",
                "notes": "Testing budget constraint overriding high demand"
            }
        },
        "pedagogical_focus": "Crucial demonstration: Market demand NEVER overrides financial affordability constraints."
    }
]


def get_demo_scenario(scenario_id: str) -> dict | None:
    for sc in PRESET_SCENARIOS:
        if sc["id"] == scenario_id:
            return sc
    return None
