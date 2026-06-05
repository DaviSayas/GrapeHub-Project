"""User profile endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter(prefix="/users", tags=["users"])


class ProfileUpdate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)


@router.get("/me", response_model=UserOut, summary="Perfil do utilizador")
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut, summary="Actualizar perfil")
def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.name = payload.name
    db.commit()
    db.refresh(current_user)
    return current_user
