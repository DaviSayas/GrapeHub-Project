"""Pydantic schemas for stock movements and cellar locations."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import StockMovementType


class StockMovementCreate(BaseModel):
    wine_id: int
    type: StockMovementType
    quantity: int = Field(..., gt=0)
    location_id: Optional[int] = None
    reason: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None
    date: Optional[datetime] = None


class StockMovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    wine_id: int
    type: str
    quantity: int
    location_id: Optional[int] = None
    reason: Optional[str] = None
    price: Optional[float] = None
    notes: Optional[str] = None
    date: datetime


class LocationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = None


class LocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str] = None
