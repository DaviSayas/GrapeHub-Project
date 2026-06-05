"""Collections API — wine collections that can be shared."""
import secrets
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.collection import Collection, CollectionWine
from app.models.user import User
from app.models.wine import Wine
from app.schemas.collection import CollectionCreate, CollectionOut, CollectionDetail

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get("", response_model=List[CollectionOut], summary="Listar minhas collections")
def list_collections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Collection).filter(
        Collection.user_id == current_user.id
    ).order_by(Collection.created_at.desc()).all()


@router.post("", response_model=CollectionOut, status_code=201, summary="Criar nova collection")
def create_collection(
    payload: CollectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    collection = Collection(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        is_public=payload.is_public or False,
    )
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return collection


@router.put("/{collection_id}", response_model=CollectionOut, summary="Actualizar collection")
def update_collection(
    collection_id: int,
    payload: CollectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.user_id == current_user.id,
    ).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection não encontrada")

    collection.name = payload.name
    collection.description = payload.description
    collection.is_public = payload.is_public or False
    db.commit()
    db.refresh(collection)
    return collection


@router.delete("/{collection_id}", status_code=204, summary="Remover collection")
def delete_collection(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.user_id == current_user.id,
    ).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection não encontrada")
    db.delete(collection)
    db.commit()


@router.post("/{collection_id}/wines/{wine_id}", status_code=201, summary="Adicionar vinho a collection")
def add_wine_to_collection(
    collection_id: int,
    wine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.user_id == current_user.id,
    ).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection não encontrada")

    wine = db.query(Wine).filter(Wine.id == wine_id, Wine.deleted_at.is_(None)).first()
    if not wine:
        raise HTTPException(status_code=404, detail="Vinho não encontrado")

    existing = db.query(CollectionWine).filter(
        CollectionWine.collection_id == collection_id,
        CollectionWine.wine_id == wine_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Vinho já está nesta collection")

    collection_wine = CollectionWine(collection_id=collection_id, wine_id=wine_id)
    db.add(collection_wine)
    db.commit()
    return {"success": True}


@router.delete("/{collection_id}/wines/{wine_id}", status_code=204, summary="Remover vinho de collection")
def remove_wine_from_collection(
    collection_id: int,
    wine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.user_id == current_user.id,
    ).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection não encontrada")

    collection_wine = db.query(CollectionWine).filter(
        CollectionWine.collection_id == collection_id,
        CollectionWine.wine_id == wine_id,
    ).first()
    if not collection_wine:
        raise HTTPException(status_code=404, detail="Vinho não está nesta collection")

    db.delete(collection_wine)
    db.commit()


@router.post("/{collection_id}/share", summary="Gerar link de partilha pública")
def share_collection(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.user_id == current_user.id,
    ).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection não encontrada")

    if not collection.share_token:
        collection.share_token = secrets.token_urlsafe(24)

    collection.is_public = True
    db.commit()
    db.refresh(collection)

    return {
        "share_token": collection.share_token,
        "public_url": f"/collections/public/{collection.share_token}",
    }


@router.get("/public/{share_token}", response_model=CollectionDetail, summary="Ver collection pública")
def view_public_collection(
    share_token: str,
    db: Session = Depends(get_db),
):
    collection = db.query(Collection).filter(
        Collection.share_token == share_token,
        Collection.is_public == True,
    ).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection não encontrada ou privada")

    return collection


@router.get("/{collection_id}/compare/{other_id}", summary="Comparar duas collections")
def compare_collections(
    collection_id: int,
    other_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    collection_a = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.user_id == current_user.id,
    ).first()
    if not collection_a:
        raise HTTPException(status_code=404, detail="Collection A não encontrada")

    collection_b = db.query(Collection).filter(
        Collection.id == other_id,
    ).first()
    if not collection_b:
        raise HTTPException(status_code=404, detail="Collection B não encontrada")

    if not collection_b.is_public and collection_b.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Não tem permissão para comparar")

    wines_a = set(w.id for w in collection_a.wines)
    wines_b = set(w.id for w in collection_b.wines)

    common = wines_a & wines_b
    only_in_a = wines_a - wines_b
    only_in_b = wines_b - wines_a

    similarity = len(common) / max(1, len(wines_a | wines_b))

    return {
        "collection_a": {
            "id": collection_a.id,
            "name": collection_a.name,
            "wines_count": len(wines_a),
        },
        "collection_b": {
            "id": collection_b.id,
            "name": collection_b.name,
            "wines_count": len(wines_b),
        },
        "common_wines_count": len(common),
        "only_in_a_count": len(only_in_a),
        "only_in_b_count": len(only_in_b),
        "similarity_score": round(similarity * 100, 1),
    }
