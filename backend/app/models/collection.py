"""Collection ORM model — wine collections that can be shared."""
from datetime import datetime, timezone
from typing import Optional
import secrets

from sqlalchemy import Boolean, DateTime, String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Collection(Base):
    """A wine collection that can be shared with others."""
    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    share_token: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, unique=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    user = relationship("User", back_populates="collections")
    wines = relationship("Wine", secondary="collection_wines", back_populates="collections")


class CollectionWine(Base):
    """Association table for Collection-Wine many-to-many relationship."""
    __tablename__ = "collection_wines"

    collection_id: Mapped[int] = mapped_column(Integer, ForeignKey("collections.id"), primary_key=True)
    wine_id: Mapped[int] = mapped_column(Integer, ForeignKey("wines.id"), primary_key=True)

    added_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
