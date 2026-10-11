"""Market supply/demand signal and APMC benchmark helpers for FasalSense.

Combines:
1. Dynamic platform activity from FasalSense active listings and retailer inquiries (trailing 30 days).
2. Explicitly labelled synthetic demonstration baseline (local_supply_demand_demo.csv).
3. Verified historical APMC wholesale price benchmarks for Pune district (market_price_benchmarks.json).
"""
from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from .models import CropListing, Inquiry

ROOT = Path(__file__).resolve().parent.parent
DEMO_MARKET_CSV = ROOT / "data" / "local_supply_demand_demo.csv"
BENCHMARKS_JSON = ROOT / "data" / "market_price_benchmarks.json"
MARKET_WINDOW_DAYS = 30


def crop_key(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def load_demo_market_data() -> dict[str, dict]:
    result: dict[str, dict] = {}
    if not DEMO_MARKET_CSV.exists():
        return result
    with DEMO_MARKET_CSV.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            try:
                result[crop_key(row["crop_name"])] = {
                    "crop_name": row["crop_name"],
                    "period_days": int(row["period_days"]),
                    "supply_kg": float(row["supply_kg"]),
                    "demand_kg": float(row["demand_kg"]),
                    "evidence_status": row.get("evidence_status", "illustrative-demo"),
                    "notes": row.get("notes", ""),
                }
            except (KeyError, ValueError):
                continue
    return result


def load_apmc_benchmarks() -> dict[str, dict]:
    result: dict[str, dict] = {}
    if not BENCHMARKS_JSON.exists():
        return result
    try:
        with BENCHMARKS_JSON.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
            for item in data:
                result[crop_key(item.get("crop_name", ""))] = item
    except Exception:
        pass
    return result


def market_balance(supply_kg: float | None, demand_kg: float | None) -> tuple[str, float | None, int]:
    if supply_kg is None or demand_kg is None or supply_kg <= 0 or demand_kg <= 0:
        return "Insufficient supply/demand records", None, 0
    ratio = supply_kg / demand_kg
    if ratio < 0.75:
        return "Low supply relative to demand", ratio, 8
    if ratio > 1.25:
        return "High supply relative to demand", ratio, -8
    return "Supply and demand broadly balanced", ratio, 2


def signal_from_values(crop_name: str, supply_kg: float | None, demand_kg: float | None,
                       period_days: int, source_type: str, data_status: str, notes: str = "",
                       apmc_benchmark: dict | None = None) -> dict:
    balance, ratio, score_delta = market_balance(supply_kg, demand_kg)
    benchmark_price_q = apmc_benchmark.get("benchmark_price_q") if apmc_benchmark else None
    benchmark_market = apmc_benchmark.get("market") if apmc_benchmark else "Pune APMC benchmark"
    price_trend_label = apmc_benchmark.get("price_trend_label") if apmc_benchmark else "No verified trend connected"
    min_q = apmc_benchmark.get("historical_min_q") if apmc_benchmark else None
    max_q = apmc_benchmark.get("historical_max_q") if apmc_benchmark else None
    arrival_season = apmc_benchmark.get("arrival_season") if apmc_benchmark else "Seasonal"

    return {
        "crop_name": crop_name,
        "supply_kg": round(supply_kg, 1) if supply_kg is not None else None,
        "demand_kg": round(demand_kg, 1) if demand_kg is not None else None,
        "period_days": period_days,
        "source_type": source_type,
        "data_status": data_status,
        "balance_label": balance,
        "supply_demand_ratio": round(ratio, 3) if ratio is not None else None,
        "score_delta": score_delta,
        "notes": notes,
        "benchmark_price_q": benchmark_price_q,
        "benchmark_market": benchmark_market,
        "benchmark_price_trend": price_trend_label,
        "benchmark_historical_range": f"₹{min_q} – ₹{max_q}/q" if min_q and max_q else "Not available",
        "benchmark_arrival_season": arrival_season,
    }


def build_demo_signals(crop_names: list[str]) -> dict[str, dict]:
    demo = load_demo_market_data()
    benchmarks = load_apmc_benchmarks()
    signals = {}
    for name in crop_names:
        key = crop_key(name)
        entry = demo.get(key)
        bm = benchmarks.get(key)
        if not entry:
            signals[key] = signal_from_values(
                name, None, None, MARKET_WINDOW_DAYS, "unknown",
                "Not enough comparable supply and demand data",
                "Missing records are unknown, not zero demand or zero supply.",
                apmc_benchmark=bm
            )
            continue
        signals[key] = signal_from_values(
            name, entry["supply_kg"], entry["demand_kg"], entry["period_days"],
            "illustrative_demo",
            "ILLUSTRATIVE SIMULATION — not measured in Chharoli; do not treat as real market statistics",
            entry.get("notes", ""),
            apmc_benchmark=bm
        )
    return signals


def build_market_signals(db: Session, crop_names: list[str], include_demo: bool | None = None,
                         scenario_override: dict | None = None) -> dict[str, dict]:
    """Build crop-level market balance signals.

    App-observed supply/demand replaces the demonstration baseline only when both
    active supply listings and retailer inquiries exist for that crop in the
    trailing window. A missing inquiry is unknown demand, not zero demand.
    """
    if include_demo is None:
        include_demo = os.getenv("MARKET_DEMO_MODE", "true").strip().lower() == "true"

    cutoff = datetime.now(timezone.utc) - timedelta(days=MARKET_WINDOW_DAYS)
    supply_rows = (
        db.query(func.lower(func.trim(CropListing.crop_name)), func.sum(CropListing.quantity_kg), func.count(CropListing.id))
        .filter(CropListing.status == "Active", CropListing.is_demo.is_(False), CropListing.created_at >= cutoff)
        .group_by(func.lower(func.trim(CropListing.crop_name))).all()
    )
    demand_rows = (
        db.query(func.lower(func.trim(CropListing.crop_name)), func.sum(Inquiry.quantity_kg), func.count(Inquiry.id))
        .join(CropListing, Inquiry.listing_id == CropListing.id)
        .filter(CropListing.is_demo.is_(False), Inquiry.created_at >= cutoff, Inquiry.status != "Cancelled")
        .group_by(func.lower(func.trim(CropListing.crop_name))).all()
    )
    platform_supply = {crop_key(name): {"kg": float(qty or 0), "count": int(count or 0)} for name, qty, count in supply_rows}
    platform_demand = {crop_key(name): {"kg": float(qty or 0), "count": int(count or 0)} for name, qty, count in demand_rows}
    demo = load_demo_market_data() if include_demo else {}
    benchmarks = load_apmc_benchmarks()

    signals: dict[str, dict] = {}
    for name in crop_names:
        key = crop_key(name)
        ps = platform_supply.get(key, {"kg": 0.0, "count": 0})
        pd = platform_demand.get(key, {"kg": 0.0, "count": 0})
        bm = benchmarks.get(key)

        # Check if an explicit scenario override was requested for demonstration testing
        if scenario_override and key in scenario_override:
            over = scenario_override[key]
            supply = over.get("supply_kg")
            demand = over.get("demand_kg")
            source_type = over.get("source_type", "scenario_simulation")
            data_status = over.get("data_status", "TEST SCENARIO SIMULATION")
            period_days = over.get("period_days", MARKET_WINDOW_DAYS)
            notes = over.get("notes", "Teacher demonstration scenario override")
        # Only compare platform totals when both sides have a recorded signal.
        elif ps["count"] > 0 and pd["count"] > 0 and ps["kg"] > 0 and pd["kg"] > 0:
            supply, demand = ps["kg"], pd["kg"]
            source_type = "platform_activity"
            data_status = "FasalSense listings and retailer inquiries in the last 30 days; not a complete Chharoli market census"
            period_days = MARKET_WINDOW_DAYS
            notes = "Observed inside this prototype only; participation may be incomplete."
        elif key in demo:
            entry = demo[key]
            supply, demand = entry["supply_kg"], entry["demand_kg"]
            source_type = "illustrative_demo"
            data_status = "ILLUSTRATIVE SIMULATION — not measured in Chharoli; do not treat as real market statistics"
            period_days = entry["period_days"]
            notes = entry["notes"]
        else:
            supply = demand = None
            source_type = "unknown"
            data_status = "Not enough comparable supply and demand data"
            period_days = MARKET_WINDOW_DAYS
            notes = "Missing records are unknown, not zero demand or zero supply."

        signals[key] = signal_from_values(name, supply, demand, period_days, source_type, data_status, notes, apmc_benchmark=bm)
        signals[key].update({
            "platform_supply_kg": round(ps["kg"], 1),
            "platform_supply_listings": ps["count"],
            "platform_demand_kg": round(pd["kg"], 1),
            "platform_demand_inquiries": pd["count"],
        })
    return signals
