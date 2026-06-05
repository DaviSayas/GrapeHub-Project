"""Wishlist API — wines the user wants to buy."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.wine import Wine
from app.models.wishlist import WishlistItem
from app.schemas.wishlist import WishlistCreate, WishlistOut, WishlistUpdate

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


@router.get("", response_model=List[WishlistOut], summary="Listar lista de desejos")
def list_wishlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(WishlistItem)
        .filter(WishlistItem.user_id == current_user.id)
        .order_by(WishlistItem.created_at.desc())
        .all()
    )


@router.post("", response_model=WishlistOut, status_code=201, summary="Adicionar à lista de desejos")
def create_wishlist(
    payload: WishlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not payload.wine_id and not payload.description:
        raise HTTPException(status_code=400, detail="Indique uma garrafa ou uma descrição")
    item = WishlistItem(
        user_id=current_user.id,
        wine_id=payload.wine_id,
        description=payload.description,
        target_price=payload.target_price,
        priority=payload.priority.value,
        notes=payload.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=WishlistOut, summary="Actualizar item")
def update_wishlist(
    item_id: int,
    payload: WishlistUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(WishlistItem).filter(
        WishlistItem.id == item_id, WishlistItem.user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    data = payload.model_dump(exclude_unset=True)
    if "priority" in data and data["priority"] is not None:
        data["priority"] = data["priority"].value if hasattr(data["priority"], "value") else data["priority"]
    for field, value in data.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204, summary="Remover item")
def delete_wishlist(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(WishlistItem).filter(
        WishlistItem.id == item_id, WishlistItem.user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    db.delete(item)
    db.commit()


@router.get("/deals/summary", summary="Deals encontradas na wishlist")
def wishlist_deals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = db.query(WishlistItem).filter(
        WishlistItem.user_id == current_user.id,
        WishlistItem.price_tracking == True,
        WishlistItem.target_price.isnot(None),
    ).all()

    deals = []
    for item in items:
        price_is_good = False
        avg_price = None

        if item.wine_id:
            wine = db.query(Wine).filter(Wine.id == item.wine_id).first()
            if wine:
                avg_similar = db.query(func.avg(Wine.purchase_price)).filter(
                    Wine.wine_type == wine.wine_type,
                    Wine.region == wine.region,
                    Wine.purchase_price.isnot(None),
                ).scalar()
                avg_price = avg_similar or wine.purchase_price or 0
                price_is_good = avg_price <= item.target_price
        else:
            price_is_good = True

        deals.append({
            "item_id": item.id,
            "wine_id": item.wine_id,
            "description": item.description,
            "target_price": item.target_price,
            "estimated_price": avg_price,
            "price_is_good": price_is_good,
            "priority": item.priority,
        })

    return {
        "deals_found": sum(1 for d in deals if d["price_is_good"]),
        "total_wishlist": len(items),
        "deals": deals,
    }


@router.get("/recommendations/summary", summary="Recomendações baseadas na coleção")
def wishlist_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_wines = db.query(Wine).filter(
        Wine.created_by == current_user.id,
        Wine.deleted_at.is_(None)
    ).all()

    if not user_wines:
        return {"recommendations": []}

    regions = set(w.region for w in user_wines if w.region)
    wine_types = set(w.wine_type for w in user_wines)
    user_wine_ids = set(w.id for w in user_wines)

    recommendations = db.query(Wine).filter(
        Wine.deleted_at.is_(None),
        Wine.id.notin_(user_wine_ids),
        or_(
            Wine.region.in_(regions),
            Wine.wine_type.in_(wine_types),
        ),
    ).order_by(Wine.avg_score.desc()).limit(5).all()

    return {
        "recommendations": [
            {
                "id": w.id,
                "name": w.name,
                "region": w.region,
                "wine_type": w.wine_type,
                "vintage": w.vintage_year,
                "score": w.avg_score,
                "price": w.purchase_price,
            }
            for w in recommendations
        ],
        "found": len(recommendations),
    }
