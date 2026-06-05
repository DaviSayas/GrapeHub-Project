"""Stock movement ORM model — the ledger that drives current stock."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import StockMovementType
from app.db.session import Base


class StockMovement(Base):
    """A single stock movement. Current stock = SUM(in) - SUM(out) +/- adjust."""
    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    wine_id: Mapped[int] = mapped_column(Integer, ForeignKey("wines.id"), nullable=False, index=True)
    location_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("cellar_locations.id"), nullable=True
    )

    type: Mapped[str] = mapped_column(
        String(10), nullable=False, default=StockMovementType.IN.value, index=True
    )  # in | out | adjust
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    reason: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)  # compra/consumo/oferta/venda/ajuste
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    wine = relationship("Wine", back_populates="stock_movements")
    location = relationship("CellarLocation", back_populates="movements")
