"""Wishlist ORM model — wines the user wants to buy."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import WishlistPriority
from app.db.session import Base


class WishlistItem(Base):
    """A wishlist entry — either links to an existing wine or free-text description."""
    __tablename__ = "wishlist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    wine_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("wines.id"), nullable=True)

    description: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)  # free text
    target_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_tracking: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    priority: Mapped[str] = mapped_column(
        String(10), nullable=False, default=WishlistPriority.MEDIUM.value
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )

    user = relationship("User", back_populates="wishlist_items")
    wine = relationship("Wine")
