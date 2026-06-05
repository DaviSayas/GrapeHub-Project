"""Pydantic schemas for wines."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import WineType
from app.schemas.grape import WineGrapeIn, WineGrapeOut
from app.schemas.producer import ProducerOut


class WineBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    region: str = "Other"
    vintage_year: int = Field(..., ge=1800, le=2100)
    wine_type: WineType = WineType.RED
    volume_ml: int = 750
    alcoholic_degree: Optional[float] = Field(None, ge=0, le=25)
    purchase_price: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    consume_from_year: Optional[int] = None
    consume_until_year: Optional[int] = None
    min_stock: int = 0


class WineCreate(WineBase):
    producer_name: str = Field(..., min_length=1, max_length=200)
    producer_country: Optional[str] = None
    producer_region: Optional[str] = None
    grapes: List[WineGrapeIn] = []
    # Optional initial stock (creates an 'in' movement)
    initial_stock: int = 0
    location_id: Optional[int] = None


class WineUpdate(BaseModel):
    name: Optional[str] = None
    region: Optional[str] = None
    vintage_year: Optional[int] = None
    wine_type: Optional[WineType] = None
    volume_ml: Optional[int] = None
    alcoholic_degree: Optional[float] = None
    purchase_price: Optional[float] = None
    description: Optional[str] = None
    consume_from_year: Optional[int] = None
    consume_until_year: Optional[int] = None
    min_stock: Optional[int] = None
    producer_name: Optional[str] = None
    grapes: Optional[List[WineGrapeIn]] = None


class WineListItem(BaseModel):
    """Compact representation for list/grid views."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    region: str
    vintage_year: int
    wine_type: str
    purchase_price: Optional[float] = None
    photo_path: Optional[str] = None
    # computed
    producer_name: str = ""
    current_stock: int = 0
    avg_score: Optional[float] = None
    min_stock: int = 0


class WineDetail(WineBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    photo_path: Optional[str] = None
    label_photo_path: Optional[str] = None
    # computed / nested
    producer: Optional[ProducerOut] = None
    grapes: List[WineGrapeOut] = []
    current_stock: int = 0
    avg_score: Optional[float] = None
    grapes_display: str = ""
