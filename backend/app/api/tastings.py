"""Tasting API — structured tasting notes (diário de prova)."""
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.tasting import Tasting
from app.models.user import User
from app.models.wine import Wine
from app.schemas.tasting import (
    TastingCreate, TastingListItem, TastingOut, TastingUpdate,
)

router = APIRouter(prefix="/tastings", tags=["tastings"])


def _check_wine(wine_id: int, user: User, db: Session) -> Wine:
    wine = db.query(Wine).filter(Wine.id == wine_id, Wine.created_by == user.id).first()
    if not wine:
        raise HTTPException(status_code=404, detail="Garrafa não encontrada")
    return wine


def _get_tasting(tasting_id: int, user: User, db: Session) -> Tasting:
    t = db.query(Tasting).filter(
        Tasting.id == tasting_id, Tasting.user_id == user.id
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail="Degustação não encontrada")
    return t


@router.post("", response_model=TastingOut, status_code=201, summary="Registar degustação")
def create_tasting(
    payload: TastingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_wine(payload.wine_id, current_user, db)
    data = payload.model_dump()
    data["date"] = data.get("date") or datetime.now(timezone.utc)
    tasting = Tasting(**data, user_id=current_user.id)
    db.add(tasting)
    db.commit()
    db.refresh(tasting)
    return tasting


@router.get("", response_model=List[TastingListItem], summary="Histórico de degustações")
def list_tastings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return (
        db.query(Tasting)
        .filter(Tasting.user_id == current_user.id)
        .order_by(Tasting.date.desc())
        .offset(skip).limit(limit).all()
    )


@router.get("/stats/summary", summary="Estatísticas de degustação")
def tasting_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.query(Tasting).filter(Tasting.user_id == current_user.id).all()
    scored = [t.overall_score for t in rows if t.overall_score]
    return {
        "total": len(rows),
        "avg_score": round(sum(scored) / len(scored), 1) if scored else 0,
        "would_buy_again": sum(1 for t in rows if t.would_buy_again),
    }


@router.get("/wine/{wine_id}", response_model=List[TastingOut], summary="Degustações de uma garrafa")
def wine_tastings(
    wine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_wine(wine_id, current_user, db)
    return (
        db.query(Tasting)
        .filter(Tasting.wine_id == wine_id)
        .order_by(Tasting.date.desc())
        .all()
    )


@router.put("/{tasting_id}", response_model=TastingOut, summary="Actualizar degustação")
def update_tasting(
    tasting_id: int,
    payload: TastingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    t = _get_tasting(tasting_id, current_user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(t, field, value)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/{tasting_id}", status_code=204, summary="Remover degustação")
def delete_tasting(
    tasting_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    t = _get_tasting(tasting_id, current_user, db)
    db.delete(t)
    db.commit()
