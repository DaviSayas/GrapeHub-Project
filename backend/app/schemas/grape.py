"""Pydantic schemas for grapes and wine-grape blend links."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class GrapeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class GrapeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)


class WineGrapeIn(BaseModel):
    """Used when creating/updating a wine: grape name + optional percentage."""
    name: str = Field(..., min_length=1, max_length=120)
    percentage: Optional[float] = Field(None, ge=0, le=100)


class WineGrapeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    percentage: Optional[float] = None
