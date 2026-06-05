"""Pydantic schemas for Collection."""
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel


class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: Optional[bool] = False


class CollectionOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_public: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CollectionDetail(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_public: bool
    share_token: Optional[str]
    created_at: datetime
    wines: List[dict] = []

    class Config:
        from_attributes = True
