"""Stock API — movements (in/out/adjust) and cellar locations."""
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.location import CellarLocation
from app.models.stock import StockMovement
from app.models.user import User
from app.models.wine import Wine
from app.schemas.stock import (
    LocationCreate, LocationOut, StockMovementCreate, StockMovementOut,
)

router = APIRouter(prefix="/stock", tags=["stock"])


def _check_wine(wine_id: int, user: User, db: Session) -> Wine:
    wine = db.query(Wine).filter(
        Wine.id == wine_id, Wine.created_by == user.id, Wine.deleted_at.is_(None)
    ).first()
    if not wine:
        raise HTTPException(status_code=404, detail="Garrafa não encontrada")
    return wine


# ── Movements ─────────────────────────────────────────────────────────────────

@router.post("/movements", response_model=StockMovementOut, status_code=201,
             summary="Registar movimento de stock")
def create_movement(
    payload: StockMovementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_wine(payload.wine_id, current_user, db)
    movement = StockMovement(
        wine_id=payload.wine_id,
        location_id=payload.location_id,
        type=payload.type.value,
        quantity=payload.quantity,
        reason=payload.reason,
        price=payload.price,
        notes=payload.notes,
        date=payload.date or datetime.now(timezone.utc),
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


@router.get("/movements/{wine_id}", response_model=List[StockMovementOut],
            summary="Histórico de movimentos de uma garrafa")
def wine_movements(
    wine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_wine(wine_id, current_user, db)
    return (
        db.query(StockMovement)
        .filter(StockMovement.wine_id == wine_id)
        .order_by(StockMovement.date.desc())
        .all()
    )


@router.get("/balance/{wine_id}", summary="Saldo de stock atual de uma garrafa")
def wine_balance(
    wine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wine = _check_wine(wine_id, current_user, db)
    return {"wine_id": wine.id, "current_stock": wine.current_stock, "min_stock": wine.min_stock}


# ── Cellar locations ──────────────────────────────────────────────────────────

@router.get("/locations", response_model=List[LocationOut], summary="Listar localizações na cave")
def list_locations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(CellarLocation)
        .filter(CellarLocation.user_id == current_user.id)
        .order_by(CellarLocation.name)
        .all()
    )


@router.post("/locations", response_model=LocationOut, status_code=201,
             summary="Criar localização na cave")
def create_location(
    payload: LocationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    loc = CellarLocation(user_id=current_user.id, **payload.model_dump())
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


@router.delete("/locations/{location_id}", status_code=204, summary="Remover localização")
def delete_location(
    location_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    loc = db.query(CellarLocation).filter(
        CellarLocation.id == location_id, CellarLocation.user_id == current_user.id
    ).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Localização não encontrada")
    db.delete(loc)
    db.commit()
