"""Enumerations used across models, schemas, and business logic."""
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class WineType(str, Enum):
    RED = "red"            # tinto
    WHITE = "white"        # branco
    ROSÉ = "rosé"          # rosé
    SPARKLING = "sparkling"  # espumante
    FORTIFIED = "fortified"  # licoroso


class StockMovementType(str, Enum):
    IN = "in"          # entrada (compra)
    OUT = "out"        # saída (consumo/oferta/venda)
    ADJUST = "adjust"  # ajuste de inventário


class WishlistPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class WineRegion(str, Enum):
    # Portugal
    DOURO = "Douro"
    ALENTEJO = "Alentejo"
    DAO = "Dão"
    BAIRRADA = "Bairrada"
    VINHO_VERDE = "Vinho Verde"
    LISBOA = "Lisboa"
    SETUBAL = "Setúbal"
    ALGARVE = "Algarve"
    # France
    BORDEAUX = "Bordeaux"
    BURGUNDY = "Burgundy"
    CHAMPAGNE = "Champagne"
    RHONE = "Rhône"
    LOIRE = "Loire"
    ALSACE = "Alsace"
    # Italy
    TUSCANY = "Tuscany"
    PIEDMONT = "Piedmont"
    VENETO = "Veneto"
    SICILY = "Sicily"
    # Spain
    RIOJA = "Rioja"
    RIBERA = "Ribera del Duero"
    PRIORAT = "Priorat"
    # International
    NAPA = "Napa Valley"
    MENDOZA = "Mendoza"
    BAROSSA = "Barossa Valley"
    OTHER = "Other"


class WineCellarStatus(str, Enum):
    IN_CELLAR = "in_cellar"
    WISHLIST = "wishlist"
    ALL_CONSUMED = "all_consumed"


class ConsumptionStatus(str, Enum):
    CONSUMED = "consumed"
    OPENED = "opened"
    PLANNED = "planned"


class DrinkingWindowStatus(str, Enum):
    TOO_YOUNG = "too_young"
    ALMOST_READY = "almost_ready"
    READY = "ready"
    PEAK = "peak"
    DECLINING = "declining"
    PAST_PEAK = "past_peak"
