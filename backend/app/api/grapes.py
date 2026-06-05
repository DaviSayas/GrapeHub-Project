"""Grape API — list and create grape varieties."""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.grape import Grape
from app.models.user import User
from app.schemas.grape import GrapeCreate, GrapeOut

router = APIRouter(prefix="/grapes", tags=["grapes"])


@router.get("", response_model=List[GrapeOut], summary="Listar/pesquisar castas")
def list_grapes(
    q: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Grape)
    if q:
        query = query.filter(Grape.name.ilike(f"%{q}%"))
    return query.order_by(Grape.name).limit(100).all()


@router.post("", response_model=GrapeOut, status_code=201, summary="Criar casta")
def create_grape(
    payload: GrapeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(Grape).filter(Grape.name == payload.name).first()
    if existing:
        return existing
    grape = Grape(name=payload.name)
    db.add(grape)
    db.commit()
    db.refresh(grape)
    return grape
