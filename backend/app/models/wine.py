"""Wine ORM model — central entity. Stock is derived from stock_movements."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import WineType
from app.db.session import Base


class Wine(Base):
    """One wine label/SKU. Quantity in stock is computed from stock_movements."""
    __tablename__ = "wines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    producer_id: Mapped[int] = mapped_column(Integer, ForeignKey("producers.id"), nullable=False)
    region: Mapped[str] = mapped_column(String(80), nullable=False, default="Other")
    vintage_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    wine_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=WineType.RED.value, index=True
    )

    volume_ml: Mapped[int] = mapped_column(Integer, nullable=False, default=750)
    alcoholic_degree: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    purchase_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # reference price
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Consumption window
    consume_from_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    consume_until_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Stock management
    min_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # alert threshold

    # Photos (local storage paths)
    photo_path: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    label_photo_path: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    # Ownership / meta
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)

    # Relations
    producer = relationship("Producer", back_populates="wines")
    owner = relationship("User", back_populates="wines", foreign_keys=[created_by])
    grape_links = relationship("WineGrape", back_populates="wine", cascade="all, delete-orphan")
    stock_movements = relationship(
        "StockMovement", back_populates="wine", cascade="all, delete-orphan",
        order_by="StockMovement.date.desc()",
    )
    tastings = relationship(
        "Tasting", back_populates="wine", cascade="all, delete-orphan",
        order_by="Tasting.date.desc()",
    )
    collections = relationship("Collection", secondary="collection_wines", back_populates="wines")

    # ── Derived properties ────────────────────────────────────────────────────
    @property
    def current_stock(self) -> int:
        total = 0
        # Process in chronological order so 'adjust' sets the absolute value correctly.
        for m in sorted(self.stock_movements, key=lambda x: (x.date, x.id)):
            if m.type == "in":
                total += m.quantity
            elif m.type == "out":
                total -= m.quantity
            elif m.type == "adjust":
                total = m.quantity  # adjust sets absolute value
        return max(0, total)

    @property
    def grapes_display(self) -> str:
        parts = []
        for link in self.grape_links:
            if link.grape:
                if link.percentage:
                    parts.append(f"{link.grape.name} ({int(link.percentage)}%)")
                else:
                    parts.append(link.grape.name)
        return ", ".join(parts)

    @property
    def avg_score(self) -> Optional[float]:
        scores = [t.overall_score for t in self.tastings if t.overall_score]
        return round(sum(scores) / len(scores), 1) if scores else None
