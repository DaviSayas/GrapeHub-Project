"""Pydantic schemas for producers."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProducerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    country: Optional[str] = None
    region: Optional[str] = None
    website: Optional[str] = None


class ProducerCreate(ProducerBase):
    pass


class ProducerOut(ProducerBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
