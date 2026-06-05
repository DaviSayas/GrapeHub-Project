"""Import all GrapeHub models so SQLAlchemy metadata registers them."""
from app.models.user import User
from app.models.producer import Producer
from app.models.grape import Grape, WineGrape
from app.models.wine import Wine
from app.models.location import CellarLocation
from app.models.stock import StockMovement
from app.models.tasting import Tasting
from app.models.wishlist import WishlistItem
from app.models.collection import Collection, CollectionWine

__all__ = [
    "User", "Producer", "Grape", "WineGrape", "Wine",
    "CellarLocation", "StockMovement", "Tasting", "WishlistItem",
    "Collection", "CollectionWine",
]
