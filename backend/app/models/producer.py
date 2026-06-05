"""Producer ORM model — reusable catalogue of wine producers."""
from typing import Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Producer(Base):
    """A wine producer / quinta (reusable across wines)."""
    __tablename__ = "producers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    country: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    wines = relationship("Wine", back_populates="producer")
