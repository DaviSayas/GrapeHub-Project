"""Producer API — list, autocomplete, create."""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.producer import Producer
from app.models.user import User
from app.schemas.producer import ProducerCreate, ProducerOut

router = APIRouter(prefix="/producers", tags=["producers"])


@router.get("", response_model=List[ProducerOut], summary="Listar/pesquisar produtores")
def list_producers(
    q: Optional[str] = Query(None, description="Texto para autocomplete"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Producer)
    if q:
        query = query.filter(Producer.name.ilike(f"%{q}%"))
    return query.order_by(Producer.name).limit(50).all()


@router.post("", response_model=ProducerOut, status_code=201, summary="Criar produtor")
def create_producer(
    payload: ProducerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(Producer).filter(Producer.name == payload.name).first()
    if existing:
        return existing
    producer = Producer(**payload.model_dump())
    db.add(producer)
    db.commit()
    db.refresh(producer)
    return producer
