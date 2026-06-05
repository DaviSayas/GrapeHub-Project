"""Grape variety ORM model + wine_grapes association (with percentage)."""
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Grape(Base):
    """A grape variety (casta). Reusable across wines."""
    __tablename__ = "grapes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)

    wine_links = relationship("WineGrape", back_populates="grape", cascade="all, delete-orphan")


class WineGrape(Base):
    """Association between a wine and a grape, carrying the blend percentage."""
    __tablename__ = "wine_grapes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    wine_id: Mapped[int] = mapped_column(Integer, ForeignKey("wines.id"), nullable=False)
    grape_id: Mapped[int] = mapped_column(Integer, ForeignKey("grapes.id"), nullable=False)
    percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-100

    wine = relationship("Wine", back_populates="grape_links")
    grape = relationship("Grape", back_populates="wine_links")
