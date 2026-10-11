from datetime import datetime, date, timezone
from sqlalchemy import String, Integer, Float, DateTime, Date, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(300))
    role: Mapped[str] = mapped_column(String(20), index=True)
    locality: Mapped[str] = mapped_column(String(120), default="Chharoli Budruk")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc)
    farm: Mapped["FarmProfile"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    listings: Mapped[list["CropListing"]] = relationship(back_populates="farmer", cascade="all, delete-orphan")

class FarmProfile(Base):
    __tablename__ = "farm_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    area_acres: Mapped[float] = mapped_column(Float, default=1.0)
    soil_type: Mapped[str] = mapped_column(String(80), default="Unknown")
    soil_ph: Mapped[float | None] = mapped_column(Float, nullable=True)
    nitrogen: Mapped[float | None] = mapped_column(Float, nullable=True)
    phosphorus: Mapped[float | None] = mapped_column(Float, nullable=True)
    potassium: Mapped[float | None] = mapped_column(Float, nullable=True)
    irrigation: Mapped[str] = mapped_column(String(80), default="Rain-fed")
    water_availability: Mapped[str] = mapped_column(String(80), default="Seasonal / uncertain")
    budget_inr: Mapped[float] = mapped_column(Float, default=15000)
    current_crop: Mapped[str] = mapped_column(String(100), default="Not entered")
    season: Mapped[str] = mapped_column(String(50), default="Kharif")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc, onupdate=_now_utc)
    user: Mapped["User"] = relationship(back_populates="farm")

class CropListing(Base):
    __tablename__ = "crop_listings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    crop_name: Mapped[str] = mapped_column(String(100), index=True)
    variety: Mapped[str] = mapped_column(String(100), default="")
    quantity_kg: Mapped[float] = mapped_column(Float)
    price_per_kg: Mapped[float] = mapped_column(Float)
    available_date: Mapped[str] = mapped_column(String(30), default="")
    quality: Mapped[str] = mapped_column(String(80), default="Not specified")
    locality: Mapped[str] = mapped_column(String(120), default="Chharoli Budruk")
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="Active", index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc)
    farmer: Mapped["User"] = relationship(back_populates="listings")

class Inquiry(Base):
    __tablename__ = "inquiries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("crop_listings.id"), index=True)
    retailer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    quantity_kg: Mapped[float] = mapped_column(Float)
    message: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="Pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc)

class AnalysisHistory(Base):
    __tablename__ = "analysis_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    area_acres: Mapped[float] = mapped_column(Float)
    budget_inr: Mapped[float] = mapped_column(Float)
    season: Mapped[str] = mapped_column(String(50))
    soil_type: Mapped[str] = mapped_column(String(80))
    soil_ph: Mapped[float | None] = mapped_column(Float, nullable=True)
    water_availability: Mapped[str] = mapped_column(String(80))
    irrigation: Mapped[str] = mapped_column(String(80))
    top_crop: Mapped[str] = mapped_column(String(100))
    top_score: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc)

