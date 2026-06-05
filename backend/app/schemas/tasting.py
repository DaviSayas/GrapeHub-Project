"""Pydantic schemas for tastings (structured WSET-style notes)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TastingBase(BaseModel):
    wine_id: int
    date: Optional[datetime] = None
    occasion: Optional[str] = None
    appearance: Optional[str] = None
    nose: Optional[str] = None
    palate: Optional[str] = None
    finish: Optional[str] = None
    overall_score: Optional[int] = Field(None, ge=1, le=100)
    notes: Optional[str] = None
    would_buy_again: Optional[bool] = None


class TastingCreate(TastingBase):
    pass


class TastingUpdate(BaseModel):
    occasion: Optional[str] = None
    appearance: Optional[str] = None
    nose: Optional[str] = None
    palate: Optional[str] = None
    finish: Optional[str] = None
    overall_score: Optional[int] = Field(None, ge=1, le=100)
    notes: Optional[str] = None
    would_buy_again: Optional[bool] = None


class TastingOut(TastingBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    created_at: datetime


class TastingListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    wine_id: int
    date: datetime
    occasion: Optional[str] = None
    overall_score: Optional[int] = None
    would_buy_again: Optional[bool] = None
    notes: Optional[str] = None
