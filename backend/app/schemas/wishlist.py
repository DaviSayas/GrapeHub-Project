"""Pydantic schemas for wishlist items."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import WishlistPriority


class WishlistCreate(BaseModel):
    wine_id: Optional[int] = None
    description: Optional[str] = None
    target_price: Optional[float] = Field(None, ge=0)
    priority: WishlistPriority = WishlistPriority.MEDIUM
    notes: Optional[str] = None


class WishlistUpdate(BaseModel):
    description: Optional[str] = None
    target_price: Optional[float] = None
    priority: Optional[WishlistPriority] = None
    notes: Optional[str] = None


class WishlistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    wine_id: Optional[int] = None
    description: Optional[str] = None
    target_price: Optional[float] = None
    priority: str
    notes: Optional[str] = None
    created_at: datetime
