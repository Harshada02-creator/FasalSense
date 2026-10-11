import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from .database import Base, engine, get_db
from .models import User, FarmProfile, CropListing, Inquiry, AnalysisHistory
from .security import hash_password, verify_password, create_token, get_current_user, get_optional_current_user, require_role
from .services import (
    get_weather, recommend, CROPS, LAT, LON,
    PRESET_SCENARIOS, get_demo_scenario
)
from .market_data import build_market_signals, load_apmc_benchmarks

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static"

app = FastAPI(
    title="FasalSense — Chharoli Farming Intelligence",
    version="2.0.0",
    description="Multi-factor crop decision-support and produce marketplace prototype for Chharoli Budruk, Pune, Maharashtra."
)

Base.metadata.create_all(bind=engine)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ---------------------------------------------------------------------------
# Request & Response Schemas
# ---------------------------------------------------------------------------

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str
    locality: str = "Chharoli Budruk"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class FarmIn(BaseModel):
    area_acres: float = Field(gt=0, le=10000, default=1.0)
    soil_type: str = "Unknown"
    soil_ph: Optional[float] = Field(default=None, ge=0.0, le=14.0)
    nitrogen: Optional[float] = Field(default=None, ge=0.0)
    phosphorus: Optional[float] = Field(default=None, ge=0.0)
    potassium: Optional[float] = Field(default=None, ge=0.0)
    irrigation: str = "Rain-fed"
    water_availability: str = "Seasonal / uncertain"
    budget_inr: float = Field(ge=0, le=100000000, default=15000)
    current_crop: str = "Not entered"
    season: str = "Kharif"


class AnalyzeIn(BaseModel):
    area_acres: float = Field(gt=0, le=10000, default=1.0)
    soil_type: str = "Unknown"
    soil_ph: Optional[float] = Field(default=None, ge=0.0, le=14.0)
    nitrogen: Optional[float] = Field(default=None, ge=0.0)
    phosphorus: Optional[float] = Field(default=None, ge=0.0)
    potassium: Optional[float] = Field(default=None, ge=0.0)
    irrigation: str = "Rain-fed"
    water_availability: str = "Seasonal / uncertain"
    budget_inr: float = Field(ge=0, le=100000000, default=15000)
    current_crop: str = "Not entered"
    season: str = "Kharif"
    scenario_id: Optional[str] = None
    market_mode: Optional[str] = "hybrid"  # "hybrid" (platform+demo fallback) or "platform_only"


class ListingIn(BaseModel):
    crop_name: str = Field(min_length=2, max_length=100)
    variety: str = ""
    quantity_kg: float = Field(gt=0)
    price_per_kg: float = Field(gt=0)
    available_date: str = ""
    quality: str = "Not specified"
    description: str = ""


class ListingUpdateIn(BaseModel):
    quantity_kg: Optional[float] = Field(default=None, gt=0)
    price_per_kg: Optional[float] = Field(default=None, gt=0)
    available_date: Optional[str] = None
    quality: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class InquiryIn(BaseModel):
    listing_id: int
    quantity_kg: float = Field(gt=0)
    message: str = Field(default="", max_length=1200)


def user_dict(u: User):
    return {
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "role": u.role,
        "locality": u.locality,
        "created_at": u.created_at.isoformat() if u.created_at else None
    }


def farm_dict(f: FarmProfile | None):
    if not f:
        return None
    return {
        k: getattr(f, k) for k in [
            "area_acres", "soil_type", "soil_ph", "nitrogen", "phosphorus",
            "potassium", "irrigation", "water_availability", "budget_inr",
            "current_crop", "season"
        ]
    }


# ---------------------------------------------------------------------------
# General & Health Endpoints
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def home():
    index_file = STATIC_DIR / "index.html"
    return index_file.read_text(encoding="utf-8")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": "FasalSense",
        "version": "2.0.0",
        "target_area": "Chharoli Budruk, Pune, Maharashtra",
        "coordinates": {"latitude": LAT, "longitude": LON},
        "catalogue_size": len(CROPS),
        "database": "sqlite/postgresql",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ---------------------------------------------------------------------------
# Authentication Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/auth/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    role = body.role.strip().lower()
    if role not in ["farmer", "retailer"]:
        raise HTTPException(status_code=400, detail="Role must be either 'farmer' or 'retailer'.")
    email = body.email.strip().lower()
    if db.query(User).filter(func.lower(User.email) == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    u = User(
        name=body.name.strip(),
        email=email,
        password_hash=hash_password(body.password),
        role=role,
        locality="Chharoli Budruk"
    )
    db.add(u)
    db.flush()
    if u.role == "farmer":
        db.add(FarmProfile(user_id=u.id))
    db.commit()
    db.refresh(u)
    return {"token": create_token(u), "user": user_dict(u)}


@app.post("/api/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    u = db.query(User).filter(func.lower(User.email) == email).first()
    if not u or not verify_password(body.password, u.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    return {"token": create_token(u), "user": user_dict(u)}


@app.get("/api/auth/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    farm = db.query(FarmProfile).filter_by(user_id=user.id).first() if user.role == "farmer" else None
    return {"user": user_dict(user), "farm": farm_dict(farm)}


# ---------------------------------------------------------------------------
# Community & Weather Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/community")
def community(db: Session = Depends(get_db)):
    farmers = db.query(User).filter_by(role="farmer").count()
    retailers = db.query(User).filter_by(role="retailer").count()
    farms = db.query(FarmProfile).count()
    crop_rows = (
        db.query(FarmProfile.current_crop, func.count(FarmProfile.id))
        .filter(
            FarmProfile.current_crop.isnot(None),
            FarmProfile.current_crop != "",
            FarmProfile.current_crop != "Not entered"
        )
        .group_by(FarmProfile.current_crop)
        .all()
    )
    listings = db.query(CropListing).filter_by(status="Active").count()
    return {
        "area": "Chharoli Budruk, Pune",
        "farmers_registered": farmers,
        "retailers_registered": retailers,
        "farms_profiled": farms,
        "active_listings": listings,
        "current_crops": [{"crop": r[0], "farmers_reporting": r[1]} for r in crop_rows],
        "data_status": "Live prototype database counts only. They represent registered users in this app, not a complete village census."
    }


@app.get("/api/weather")
async def weather():
    try:
        return await get_weather()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Live weather service (Open-Meteo) is temporarily unavailable. Check network or try again."
        )


# ---------------------------------------------------------------------------
# Farm Profile Endpoints (Farmer Only)
# ---------------------------------------------------------------------------

@app.get("/api/farm")
def get_farm(user: User = Depends(require_role("farmer")), db: Session = Depends(get_db)):
    return farm_dict(db.query(FarmProfile).filter_by(user_id=user.id).first())


@app.put("/api/farm")
def save_farm(body: FarmIn, user: User = Depends(require_role("farmer")), db: Session = Depends(get_db)):
    f = db.query(FarmProfile).filter_by(user_id=user.id).first()
    if not f:
        f = FarmProfile(user_id=user.id)
        db.add(f)
    for k, v in body.model_dump().items():
        setattr(f, k, v)
    db.commit()
    db.refresh(f)
    return farm_dict(f)


# ---------------------------------------------------------------------------
# Scenarios Endpoint (Pedagogical Teacher Demos)
# ---------------------------------------------------------------------------

@app.get("/api/scenarios")
def list_scenarios():
    return {
        "area": "Chharoli Budruk, Pune",
        "total_scenarios": len(PRESET_SCENARIOS),
        "scenarios": PRESET_SCENARIOS
    }


# ---------------------------------------------------------------------------
# Recommendation & Analysis Engine
# ---------------------------------------------------------------------------

@app.post("/api/analyze")
def analyze(
    body: AnalyzeIn,
    user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    # Check if a preset demonstration scenario was requested
    scenario_override = None
    scenario_meta = None
    if body.scenario_id:
        scenario = get_demo_scenario(body.scenario_id)
        if scenario:
            scenario_meta = scenario
            scenario_override = scenario.get("scenario_market_override")

    include_demo = (body.market_mode != "platform_only")
    crop_names = [crop["name"] for crop in CROPS]
    market_signals = build_market_signals(
        db, crop_names, include_demo=include_demo, scenario_override=scenario_override
    )

    profile_data = body.model_dump()
    items = recommend(profile_data, market_signals=market_signals)
    used_sources = sorted({item.get("market_source_type", "unknown") for item in items})

    # Record analysis history if user is logged in as farmer
    top_item = items[0] if items else None
    history_recorded = False
    if user and user.role == "farmer" and top_item:
        try:
            h = AnalysisHistory(
                user_id=user.id,
                area_acres=float(body.area_acres),
                budget_inr=float(body.budget_inr),
                season=body.season,
                soil_type=body.soil_type,
                soil_ph=body.soil_ph,
                water_availability=body.water_availability,
                irrigation=body.irrigation,
                top_crop=top_item["name"],
                top_score=int(top_item["score"]),
            )
            db.add(h)
            db.commit()
            history_recorded = True
        except Exception:
            db.rollback()

    return {
        "area": "Chharoli Budruk, Pune",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "history_recorded": history_recorded,
        "method": "Explainable 5-factor scoring model: Season (25), Water (20), Soil/pH (20), Budget (20), Market Supply vs Demand (15).",
        "market_method": "Compares 30-day supply & demand snapshot. Dynamic app activity is an internal proxy; benchmark prices derive from Pune APMC data.",
        "market_sources_used": used_sources,
        "scenario_applied": scenario_meta["title"] if scenario_meta else None,
        "scenario_pedagogical_focus": scenario_meta["pedagogical_focus"] if scenario_meta else None,
        "recommendations": items
    }


@app.get("/api/analysis-history")
def get_analysis_history(user: User = Depends(require_role("farmer")), db: Session = Depends(get_db)):
    rows = (
        db.query(AnalysisHistory)
        .filter_by(user_id=user.id)
        .order_by(AnalysisHistory.created_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": r.id,
            "area_acres": r.area_acres,
            "budget_inr": r.budget_inr,
            "season": r.season,
            "soil_type": r.soil_type,
            "soil_ph": r.soil_ph,
            "water_availability": r.water_availability,
            "top_crop": r.top_crop,
            "top_score": r.top_score,
            "created_at": r.created_at.isoformat()
        } for r in rows
    ]


# ---------------------------------------------------------------------------
# Marketplace & Produce Listings Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/listings")
def list_listings(
    q: str = "",
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: Session = Depends(get_db)
):
    query = db.query(CropListing).filter_by(status="Active")
    if q.strip():
        term = f"%{q.strip()[:80]}%"
        query = query.filter(CropListing.crop_name.ilike(term) | CropListing.variety.ilike(term))
    if min_price is not None:
        query = query.filter(CropListing.price_per_kg >= min_price)
    if max_price is not None:
        query = query.filter(CropListing.price_per_kg <= max_price)

    rows = query.order_by(CropListing.created_at.desc()).limit(100).all()
    return [
        {
            "id": x.id,
            "crop_name": x.crop_name,
            "variety": x.variety,
            "quantity_kg": x.quantity_kg,
            "price_per_kg": x.price_per_kg,
            "available_date": x.available_date,
            "quality": x.quality,
            "locality": x.locality,
            "description": x.description,
            "farmer_name": x.farmer.name if x.farmer else "Farmer",
            "is_demo": x.is_demo,
            "created_at": x.created_at.isoformat()
        } for x in rows
    ]


@app.post("/api/listings")
def create_listing(
    body: ListingIn,
    user: User = Depends(require_role("farmer")),
    db: Session = Depends(get_db)
):
    item = CropListing(
        farmer_id=user.id,
        crop_name=body.crop_name.strip(),
        variety=body.variety.strip(),
        quantity_kg=body.quantity_kg,
        price_per_kg=body.price_per_kg,
        available_date=body.available_date.strip(),
        quality=body.quality.strip() or "Standard quality",
        locality="Chharoli Budruk",
        description=body.description.strip(),
        status="Active",
        is_demo=False
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "message": "Produce listing successfully published."}


@app.get("/api/my-listings")
def my_listings(user: User = Depends(require_role("farmer")), db: Session = Depends(get_db)):
    rows = db.query(CropListing).filter_by(farmer_id=user.id).order_by(CropListing.created_at.desc()).all()
    return [
        {
            "id": x.id,
            "crop_name": x.crop_name,
            "variety": x.variety,
            "quantity_kg": x.quantity_kg,
            "price_per_kg": x.price_per_kg,
            "available_date": x.available_date,
            "quality": x.quality,
            "description": x.description,
            "status": x.status,
            "created_at": x.created_at.isoformat()
        } for x in rows
    ]


@app.put("/api/listings/{listing_id}")
def update_listing(
    listing_id: int,
    body: ListingUpdateIn,
    user: User = Depends(require_role("farmer")),
    db: Session = Depends(get_db)
):
    item = db.query(CropListing).filter_by(id=listing_id, farmer_id=user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Listing not found.")
    if body.quantity_kg is not None:
        item.quantity_kg = body.quantity_kg
    if body.price_per_kg is not None:
        item.price_per_kg = body.price_per_kg
    if body.available_date is not None:
        item.available_date = body.available_date
    if body.quality is not None:
        item.quality = body.quality
    if body.description is not None:
        item.description = body.description
    if body.status is not None:
        if body.status not in ["Active", "Sold out", "Paused", "Archived"]:
            raise HTTPException(status_code=400, detail="Invalid listing status.")
        item.status = body.status
    db.commit()
    return {"message": "Listing updated successfully.", "id": item.id}


@app.patch("/api/listings/{listing_id}/status")
def listing_status(
    listing_id: int,
    status: str = Query(...),
    user: User = Depends(require_role("farmer")),
    db: Session = Depends(get_db)
):
    if status not in ["Active", "Sold out", "Paused", "Archived"]:
        raise HTTPException(status_code=400, detail="Invalid listing status.")
    item = db.query(CropListing).filter_by(id=listing_id, farmer_id=user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Listing not found.")
    item.status = status
    db.commit()
    return {"message": "Listing status updated.", "status": status}


@app.delete("/api/listings/{listing_id}")
def delete_listing(
    listing_id: int,
    user: User = Depends(require_role("farmer")),
    db: Session = Depends(get_db)
):
    item = db.query(CropListing).filter_by(id=listing_id, farmer_id=user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Listing not found.")
    db.delete(item)
    db.commit()
    return {"message": "Listing deleted successfully."}


# ---------------------------------------------------------------------------
# Inquiries Endpoints (Farmer & Retailer Workflows)
# ---------------------------------------------------------------------------

@app.post("/api/inquiries")
def create_inquiry(
    body: InquiryIn,
    user: User = Depends(require_role("retailer")),
    db: Session = Depends(get_db)
):
    item = db.query(CropListing).filter_by(id=body.listing_id, status="Active").first()
    if not item:
        raise HTTPException(status_code=404, detail="Active listing not found.")
    if item.farmer_id == user.id:
        raise HTTPException(status_code=400, detail="You cannot inquire about your own listing.")
    if body.quantity_kg > item.quantity_kg:
        raise HTTPException(
            status_code=400,
            detail=f"Requested quantity ({body.quantity_kg} kg) exceeds available quantity ({item.quantity_kg} kg)."
        )
    inquiry = Inquiry(
        listing_id=item.id,
        retailer_id=user.id,
        farmer_id=item.farmer_id,
        quantity_kg=body.quantity_kg,
        message=body.message.strip(),
        status="Pending"
    )
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    return {
        "id": inquiry.id,
        "status": inquiry.status,
        "message": "Inquiry successfully submitted to the farmer."
    }


@app.get("/api/inquiries")
def get_inquiries(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Inquiry)
    if user.role == "farmer":
        q = q.filter_by(farmer_id=user.id)
    else:
        q = q.filter_by(retailer_id=user.id)

    rows = q.order_by(Inquiry.created_at.desc()).all()
    results = []
    for x in rows:
        listing = db.get(CropListing, x.listing_id)
        other_user = db.get(User, x.retailer_id if user.role == "farmer" else x.farmer_id)
        results.append({
            "id": x.id,
            "listing_id": x.listing_id,
            "crop_name": listing.crop_name if listing else "Produce",
            "quantity_kg": x.quantity_kg,
            "message": x.message,
            "status": x.status,
            "other_party": other_user.name if other_user else "Counterparty",
            "other_party_role": other_user.role if other_user else "",
            "created_at": x.created_at.isoformat()
        })
    return results


@app.patch("/api/inquiries/{inquiry_id}")
def update_inquiry(
    inquiry_id: int,
    status: str = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if status not in ["Accepted", "Declined", "Completed", "Cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid inquiry status.")
    item = db.query(Inquiry).filter_by(id=inquiry_id).first()
    if not item or user.id not in [item.farmer_id, item.retailer_id]:
        raise HTTPException(status_code=404, detail="Inquiry not found.")
    if user.role == "farmer" and status not in ["Accepted", "Declined", "Completed"]:
        raise HTTPException(status_code=403, detail="Farmers cannot set status to Cancelled.")
    if user.role == "retailer" and status != "Cancelled":
        raise HTTPException(status_code=403, detail="Retailers can only cancel their own inquiry.")
    item.status = status
    db.commit()
    return {"message": f"Inquiry status updated to {status}.", "status": status}


# ---------------------------------------------------------------------------
# Market Supply/Demand & APMC Benchmarks Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/market/supply-demand")
def market_supply_demand(
    mode: str = Query("hybrid", description="Mode: 'hybrid' or 'platform_only'"),
    db: Session = Depends(get_db)
):
    include_demo = (mode != "platform_only")
    crop_names = [crop["name"] for crop in CROPS]
    signals = build_market_signals(db, crop_names, include_demo=include_demo)
    rows = [signals.get(crop["name"].strip().lower(), {}) for crop in CROPS]

    return {
        "area": "Chharoli Budruk, Pune",
        "window_days": 30,
        "mode": mode,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "signals": rows,
        "methodology": "Quantifies per-crop listed supply vs buyer inquiry demand. Supply/Demand ratio < 0.75 indicates potential market gap; ratio > 1.25 indicates potential surplus / high competition.",
        "note": "Supply indicates active listings and demand indicates retailer inquiries recorded within FasalSense. When activity is limited, synthetic simulation data is supplied for pedagogical testing. Neither represents a complete Chharoli village census."
    }


@app.get("/api/market/benchmarks")
def get_benchmarks():
    data = load_apmc_benchmarks()
    return {
        "market_district": "Pune District, Maharashtra",
        "primary_markets": ["Pune APMC (Gultekdi)", "Haveli APMC", "Junnar / Narayangaon APMC", "Baramati APMC"],
        "source": "Maharashtra State Agricultural Marketing Board (MSAMB) & AGMARKNET Pune District Monthly Price Bulletins (2022-2024)",
        "benchmarks": list(data.values())
    }


@app.get("/api/market/sources")
def market_sources():
    return {
        "sources": [
            {
                "name": "Open-Meteo Weather API",
                "status": "Connected live",
                "purpose": "7-day precipitation, temperature, and wind forecast for Chharoli",
                "url": "https://open-meteo.com/"
            },
            {
                "name": "NABARD Pune District Potential Linked Credit Plan (PLP)",
                "status": "Historical reference document (FY 2021-22 / 2022-23)",
                "purpose": "Scales of finance and district-level crop eligibility basis",
                "url": "https://www.nabard.org/auth/writereaddata/tender/1012212259Pune.pdf"
            },
            {
                "name": "MSAMB & AGMARKNET Pune District Mandi Bulletins",
                "status": "Historical benchmark dataset (2022-2024)",
                "purpose": "Wholesale modal benchmark prices, volatility ranges, and arrival seasons",
                "url": "https://agmarknet.gov.in/"
            },
            {
                "name": "FasalSense Platform Activity (Listings & Inquiries)",
                "status": "Dynamic within prototype",
                "purpose": "Active listed produce and retailer inquiry demand in trailing 30 days",
                "url": "/api/market/supply-demand"
            },
            {
                "name": "Simulated Chharoli Supply/Demand Demo Dataset",
                "status": "Synthetic simulation only",
                "purpose": "Demonstrates surplus vs deficit scenarios during academic evaluation",
                "url": "/api/market/supply-demand"
            },
            {
                "name": "Soil Health Card Portal",
                "status": "Not live-connected; manual test input supported",
                "purpose": "Laboratory-tested pH, N, P, K soil parameters",
                "url": "https://soilhealth.dac.gov.in/"
            },
            {
                "name": "Central Ground Water Board (CGWB)",
                "status": "Not live-connected; farmer self-reporting only",
                "purpose": "Regional groundwater table reference",
                "url": "https://cgwb.gov.in/"
            }
        ],
        "non_claims": [
            "No full village census of all produce grown in Chharoli is claimed.",
            "No camera-based AI pH detector is claimed; laboratory soil testing is required.",
            "No guaranteed profit or crop yields are promised; estimates are illustrative operating margins.",
            "No real monetary payment processing is included in this prototype."
        ]
    }


# ---------------------------------------------------------------------------
# Database Demonstration Seeding
# ---------------------------------------------------------------------------

def seed_demo():
    if os.getenv("DEMO_MODE", "true").lower() != "true":
        return
    from .database import SessionLocal
    db = SessionLocal()
    try:
        farmer_email = "farmer.demo@example.com"
        retailer_email = "retailer.demo@example.com"
        if db.query(User).filter_by(email=farmer_email).first():
            return
        farmer = User(
            name="Ramesh Patil (Demo Farmer)",
            email=farmer_email,
            password_hash=hash_password("DemoFarm123!"),
            role="farmer",
            locality="Chharoli Budruk"
        )
        retailer = User(
            name="Pune Fresh Mart (Demo Retailer)",
            email=retailer_email,
            password_hash=hash_password("DemoRetail123!"),
            role="retailer",
            locality="Chharoli Budruk"
        )
        db.add_all([farmer, retailer])
        db.flush()

        db.add(FarmProfile(
            user_id=farmer.id,
            area_acres=1.5,
            soil_type="Black soil",
            soil_ph=7.2,
            nitrogen=240.0,
            phosphorus=18.0,
            potassium=160.0,
            irrigation="Drip",
            water_availability="Reliable",
            budget_inr=35000,
            current_crop="Pearl millet (Bajra)",
            season="Kharif"
        ))

        listing1 = CropListing(
            farmer_id=farmer.id,
            crop_name="Pearl millet (Bajra)",
            variety="Shanti Hybrid",
            quantity_kg=800,
            price_per_kg=26,
            available_date="Ready for pickup",
            quality="Grade A sun-dried grain",
            locality="Chharoli Budruk",
            description="Demonstration listing. Naturally harvested Kharif Bajra from Chharoli fields.",
            status="Active",
            is_demo=True
        )
        listing2 = CropListing(
            farmer_id=farmer.id,
            crop_name="Green gram (Moong)",
            variety="BM 2003-2",
            quantity_kg=350,
            price_per_kg=82,
            available_date="Next week harvest",
            quality="Cleaned & graded pulse",
            locality="Chharoli Budruk",
            description="Demonstration listing. Short-duration high-protein Moong batch.",
            status="Active",
            is_demo=True
        )
        db.add_all([listing1, listing2])
        db.flush()

        inquiry1 = Inquiry(
            listing_id=listing1.id,
            retailer_id=retailer.id,
            farmer_id=farmer.id,
            quantity_kg=200,
            message="Interested in procuring 200 kg for weekly retail supply in Pune.",
            status="Pending"
        )
        db.add(inquiry1)
        db.commit()
    finally:
        db.close()


seed_demo()
