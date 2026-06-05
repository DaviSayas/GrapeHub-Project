"""Tasting ORM model — structured WSET-style tasting notes."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Tasting(Base):
    """A structured tasting note for a wine (1 wine can have many tastings)."""
    __tablename__ = "tastings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    wine_id: Mapped[int] = mapped_column(Integer, ForeignKey("wines.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )
    occasion: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # WSET-style structured notes
    appearance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # cor/aspecto
    nose: Mapped[Optional[str]] = mapped_column(Text, nullable=True)        # aroma
    palate: Mapped[Optional[str]] = mapped_column(Text, nullable=True)      # boca/sabor
    finish: Mapped[Optional[str]] = mapped_column(Text, nullable=True)      # final

    overall_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-100
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    would_buy_again: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    wine = relationship("Wine", back_populates="tastings")
    user = relationship("User", back_populates="tastings")
