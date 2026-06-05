"""Cellar location ORM model — physical storage spots in the cellar."""
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class CellarLocation(Base):
    """A named storage location in the user's cellar (e.g. 'Prateleira A')."""
    __tablename__ = "cellar_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="locations")
    movements = relationship("StockMovement", back_populates="location")
