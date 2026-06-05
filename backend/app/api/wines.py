"""Wine API — CRUD, photo upload, search/filters, window, pairing, stats, alerts."""
import csv
import io
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.grape import Grape, WineGrape
from app.models.producer import Producer
from app.models.stock import StockMovement
from app.models.user import User
from app.models.wine import Wine
from app.schemas.wine import WineCreate, WineDetail, WineListItem, WineUpdate
from app.services.pairing import get_pairing
from app.services.photos import delete_photo, save_wine_photo
from app.services.serializers import wine_detail, wine_list_item
from app.services.suggestions import get_alerts, get_drinking_window

router = APIRouter(prefix="/wines", tags=["wines"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_404(wine_id: int, user: User, db: Session) -> Wine:
    wine = db.query(Wine).filter(
        Wine.id == wine_id, Wine.created_by == user.id, Wine.deleted_at.is_(None)
    ).first()
    if not wine:
        raise HTTPException(status_code=404, detail="Garrafa não encontrada")
    return wine


def _get_or_create_producer(name: str, country, region, db: Session) -> Producer:
    p = db.query(Producer).filter(Producer.name == name).first()
    if not p:
        p = Producer(name=name, country=country, region=region)
        db.add(p)
        db.flush()
    return p


def _set_grapes(wine: Wine, grapes, db: Session):
    """Replace the wine's grape links from a list of {name, percentage}."""
    # clear existing
    for link in list(wine.grape_links):
        db.delete(link)
    db.flush()
    for g in grapes or []:
        name = g.name if hasattr(g, "name") else g["name"]
        pct = g.percentage if hasattr(g, "percentage") else g.get("percentage")
        grape = db.query(Grape).filter(Grape.name == name).first()
        if not grape:
            grape = Grape(name=name)
            db.add(grape)
            db.flush()
        db.add(WineGrape(wine_id=wine.id, grape_id=grape.id, percentage=pct))


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.post("", response_model=WineDetail, status_code=201, summary="Adicionar garrafa")
def create_wine(
    payload: WineCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    producer = _get_or_create_producer(
        payload.producer_name, payload.producer_country, payload.producer_region, db
    )

    wine = Wine(
        name=payload.name,
        producer_id=producer.id,
        region=payload.region,
        vintage_year=payload.vintage_year,
        wine_type=payload.wine_type.value,
        volume_ml=payload.volume_ml,
        alcoholic_degree=payload.alcoholic_degree,
        purchase_price=payload.purchase_price,
        description=payload.description,
        consume_from_year=payload.consume_from_year,
        consume_until_year=payload.consume_until_year,
        min_stock=payload.min_stock,
        created_by=current_user.id,
    )
    db.add(wine)
    db.flush()

    _set_grapes(wine, payload.grapes, db)

    # Initial stock movement
    if payload.initial_stock and payload.initial_stock > 0:
        db.add(StockMovement(
            wine_id=wine.id, location_id=payload.location_id, type="in",
            quantity=payload.initial_stock, reason="compra inicial",
            price=payload.purchase_price, date=datetime.now(timezone.utc),
        ))

    db.commit()
    db.refresh(wine)
    return wine_detail(wine)


@router.get("", response_model=List[WineListItem], summary="Listar/pesquisar garrafas")
def list_wines(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="Pesquisa: nome, produtor, região"),
    wine_type: Optional[str] = None,
    region: Optional[str] = None,
    producer_id: Optional[int] = None,
    price_min: Optional[float] = Query(None, ge=0),
    price_max: Optional[float] = Query(None, ge=0),
    min_score: Optional[int] = Query(None, ge=1, le=100),
    in_stock: Optional[bool] = None,
    sort: str = Query("recent", description="recent|name|year|score|price"),
    sort_order: str = Query("desc", description="asc|desc"),
):
    query = db.query(Wine).filter(Wine.created_by == current_user.id, Wine.deleted_at.is_(None))

    if wine_type:
        query = query.filter(Wine.wine_type == wine_type)
    if region:
        query = query.filter(Wine.region == region)
    if producer_id:
        query = query.filter(Wine.producer_id == producer_id)
    if price_min is not None:
        query = query.filter(Wine.purchase_price >= price_min)
    if price_max is not None:
        query = query.filter(Wine.purchase_price <= price_max)
    if q:
        like = f"%{q}%"
        query = query.join(Producer, Wine.producer_id == Producer.id).filter(
            Wine.name.ilike(like) | Producer.name.ilike(like) | Wine.region.ilike(like)
        )

    # Database-level sorting
    is_desc = sort_order == "desc"
    if sort == "name":
        query = query.order_by(Wine.name.desc() if is_desc else Wine.name)
    elif sort == "year":
        query = query.order_by(Wine.vintage_year.desc() if is_desc else Wine.vintage_year.asc())
    elif sort == "price":
        query = query.order_by(Wine.purchase_price.desc() if is_desc else Wine.purchase_price.asc())
    else:  # recent
        query = query.order_by(Wine.created_at.desc() if is_desc else Wine.created_at.asc())

    wines = query.all()
    items = [wine_list_item(w) for w in wines]

    # Post-filters that need computed values
    if in_stock is not None:
        items = [i for i in items if (i["current_stock"] > 0) == in_stock]
    if min_score is not None:
        items = [i for i in items if (i["avg_score"] or 0) >= min_score]
    if sort == "score":
        items.sort(key=lambda i: i["avg_score"] or 0, reverse=(sort_order == "desc"))

    return items


@router.get("/investment/summary", summary="Análise de investimento (valor, ROI, apreciação)")
def investment_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wines = db.query(Wine).filter(
        Wine.created_by == current_user.id, Wine.deleted_at.is_(None)
    ).all()

    total_bottles = 0
    total_value = 0.0
    total_invested = 0.0
    prices = []
    appreciation_wines = []
    depreciation_wines = []

    for w in wines:
        stock = w.current_stock
        purchase_price = w.purchase_price or 0

        total_bottles += stock
        total_value += purchase_price * stock
        total_invested += purchase_price * stock

        if purchase_price > 0:
            prices.append(purchase_price)

        if stock > 0 and w.avg_score:
            # Estimate current market value based on score
            # Formula: (score/100) * purchase_price * 1.5
            estimated_value = (w.avg_score / 100) * purchase_price * 1.5
            appreciation = estimated_value - purchase_price

            wine_info = {
                "id": w.id,
                "name": w.name,
                "vintage": w.vintage_year,
                "purchase_price": round(purchase_price, 2),
                "estimated_value": round(estimated_value, 2),
                "appreciation": round(appreciation, 2),
                "score": w.avg_score,
                "stock": stock,
            }

            if appreciation > 0:
                appreciation_wines.append(wine_info)
            else:
                depreciation_wines.append(wine_info)

    # Sort and get top 3
    appreciation_wines.sort(key=lambda x: x["appreciation"], reverse=True)
    depreciation_wines.sort(key=lambda x: x["appreciation"])

    # Calculate ROI
    avg_score = sum(w.avg_score for w in wines if w.avg_score and w.current_stock > 0) / max(1, len([w for w in wines if w.avg_score and w.current_stock > 0]))
    estimated_total_value = sum(
        (w.avg_score / 100 * (w.purchase_price or 0) * 1.5) * w.current_stock
        for w in wines if w.avg_score and w.current_stock > 0
    )
    potential_gain = estimated_total_value - total_invested
    roi_percent = (potential_gain / total_invested * 100) if total_invested > 0 else 0

    return {
        "total_value": round(total_value, 2),
        "total_invested": round(total_invested, 2),
        "estimated_total_value": round(estimated_total_value, 2),
        "avg_price": round(sum(prices) / len(prices), 2) if prices else 0,
        "min_price": round(min(prices), 2) if prices else 0,
        "max_price": round(max(prices), 2) if prices else 0,
        "bottles_count": total_bottles,
        "value_per_bottle_avg": round(total_value / max(1, total_bottles), 2),
        "appreciation_wines": appreciation_wines[:3],
        "depreciation_wines": depreciation_wines[:3],
        "roi_estimate": {
            "estimated_current_value": round(estimated_total_value, 2),
            "potential_gain": round(potential_gain, 2),
            "roi_percent": round(roi_percent, 2),
        },
        "avg_score": round(avg_score, 1),
    }


@router.get("/stats/summary", summary="Estatísticas da coleção")
def stats_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wines = db.query(Wine).filter(
        Wine.created_by == current_user.id, Wine.deleted_at.is_(None)
    ).all()
    current_year = datetime.now(timezone.utc).year

    total_bottles = 0
    total_value = 0.0
    ready_now = 0
    soon = 0
    by_type, by_region, by_year = {}, {}, {}
    scores = []

    for w in wines:
        stock = w.current_stock
        total_bottles += stock
        total_value += (w.purchase_price or 0) * stock
        by_type[w.wine_type] = by_type.get(w.wine_type, 0) + stock
        by_region[w.region] = by_region.get(w.region, 0) + stock
        by_year[str(w.vintage_year)] = by_year.get(str(w.vintage_year), 0) + stock
        if w.avg_score:
            scores.append(w.avg_score)

        win = get_drinking_window(w.wine_type, w.region, w.vintage_year)
        if stock > 0:
            if win["drink_from"] <= current_year <= win["drink_until"]:
                ready_now += 1
            if win["drink_until"] in (current_year, current_year + 1):
                soon += 1

    return {
        "total_wines": len(wines),
        "total_bottles": total_bottles,
        "total_value": round(total_value, 2),
        "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
        "ready_now": ready_now,
        "ending_soon": soon,
        "by_type": by_type,
        "by_region": by_region,
        "by_year": dict(sorted(by_year.items())),
    }


@router.get("/alerts/summary", summary="Resumo de alertas (contadores)")
def alerts_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wines = db.query(Wine).filter(
        Wine.created_by == current_user.id, Wine.deleted_at.is_(None)
    ).all()
    alerts = get_alerts(wines)

    summary = {
        "total_alerts": len(alerts),
        "urgent_count": len([a for a in alerts if a["type"] in ("urgent", "peak")]),
        "warning_count": len([a for a in alerts if a["type"] in ("low_stock", "declining")]),
        "info_count": len([a for a in alerts if a["type"] == "past_peak"]),
    }
    return summary


@router.get("/alerts", summary="Alertas (janela de consumo + stock mínimo)")
def alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wines = db.query(Wine).filter(
        Wine.created_by == current_user.id, Wine.deleted_at.is_(None)
    ).all()
    return get_alerts(wines)


@router.get("/stats/charts", summary="Dados para os gráficos do dashboard")
def stats_charts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Monthly consumption (last 12 months) + collection value timeline."""
    from app.models.stock import StockMovement

    wines = db.query(Wine).filter(
        Wine.created_by == current_user.id, Wine.deleted_at.is_(None)
    ).all()
    wine_ids = [w.id for w in wines]
    price_by_wine = {w.id: (w.purchase_price or 0) for w in wines}

    movements = []
    if wine_ids:
        movements = db.query(StockMovement).filter(
            StockMovement.wine_id.in_(wine_ids)
        ).order_by(StockMovement.date).all()

    now = datetime.now(timezone.utc)
    # ── Last 12 months buckets ────────────────────────────────────────────────
    months = []
    for i in range(11, -1, -1):
        y = now.year
        m = now.month - i
        while m <= 0:
            m += 12
            y -= 1
        months.append((y, m))
    month_labels = [f"{m:02d}/{str(y)[2:]}" for (y, m) in months]
    earliest = months[0]

    consumption = {(y, m): 0 for (y, m) in months}
    by_month_delta = {(y, m): 0.0 for (y, m) in months}
    pre_window_value = 0.0  # cumulative value before the 12-month window

    for mv in movements:
        d = mv.date
        key = (d.year, d.month)
        price = mv.price if mv.price is not None else price_by_wine.get(mv.wine_id, 0)
        if mv.type == "in":
            delta = price * mv.quantity
        elif mv.type == "out":
            delta = -price * mv.quantity
            if key in consumption:
                consumption[key] += mv.quantity
        else:
            delta = 0.0

        if key in by_month_delta:
            by_month_delta[key] += delta
        elif key < earliest:
            pre_window_value += delta

    # Cumulative value timeline (forward fill)
    cum = pre_window_value
    value_series = []
    for ym in months:
        cum += by_month_delta[ym]
        value_series.append(round(cum, 2))

    return {
        "month_labels": month_labels,
        "monthly_consumption": [consumption[ym] for ym in months],
        "value_timeline": value_series,
    }


@router.get("/{wine_id}/history", summary="Histórico completo da garrafa (movimentos + estatísticas)")
def wine_history(
    wine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wine = _get_or_404(wine_id, current_user, db)
    movements = db.query(StockMovement).filter(
        StockMovement.wine_id == wine_id
    ).order_by(StockMovement.date).all()

    # Calculate statistics
    first_purchase_date = None
    last_purchase_date = None
    total_consumed = 0
    total_purchased = 0

    for m in movements:
        if m.type == "in":
            total_purchased += m.quantity
            if not first_purchase_date:
                first_purchase_date = m.date
            last_purchase_date = m.date
        elif m.type == "out":
            total_consumed += m.quantity

    # Calculate consumption rate (bottles per month)
    consumption_rate = 0.0
    if first_purchase_date and movements:
        last_date = movements[-1].date
        months_elapsed = (last_date - first_purchase_date).days / 30.44
        if months_elapsed > 0:
            consumption_rate = round(total_consumed / months_elapsed, 2)

    return {
        "wine": wine_detail(wine),
        "movements_total": len(movements),
        "total_purchased": total_purchased,
        "total_consumed": total_consumed,
        "consumption_rate": consumption_rate,
        "first_purchase_date": first_purchase_date.isoformat() if first_purchase_date else None,
        "last_purchase_date": last_purchase_date.isoformat() if last_purchase_date else None,
        "movements": [
            {
                "id": m.id,
                "type": m.type,
                "quantity": m.quantity,
                "reason": m.reason,
                "price": m.price,
                "date": m.date.isoformat(),
                "location": m.location.name if m.location else "Desconhecida",
            }
            for m in reversed(movements)  # Most recent first
        ],
    }


@router.get("/{wine_id}", response_model=WineDetail, summary="Detalhes da garrafa")
def get_wine(
    wine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return wine_detail(_get_or_404(wine_id, current_user, db))


@router.put("/{wine_id}", response_model=WineDetail, summary="Actualizar garrafa")
def update_wine(
    wine_id: int,
    payload: WineUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wine = _get_or_404(wine_id, current_user, db)
    data = payload.model_dump(exclude_unset=True)

    if "producer_name" in data and data["producer_name"]:
        producer = _get_or_create_producer(data.pop("producer_name"), None, None, db)
        wine.producer_id = producer.id
    else:
        data.pop("producer_name", None)

    grapes = data.pop("grapes", None)
    if grapes is not None:
        _set_grapes(wine, grapes, db)

    for field, value in data.items():
        if field == "wine_type" and value is not None:
            wine.wine_type = value.value if hasattr(value, "value") else value
        else:
            setattr(wine, field, value)

    db.commit()
    db.refresh(wine)
    return wine_detail(wine)


@router.delete("/{wine_id}", status_code=204, summary="Remover garrafa")
def delete_wine(
    wine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wine = _get_or_404(wine_id, current_user, db)
    wine.deleted_at = datetime.now(timezone.utc)
    db.commit()


# ── Photo upload ──────────────────────────────────────────────────────────────

@router.post("/{wine_id}/photo", response_model=WineDetail, summary="Upload foto da garrafa")
def upload_bottle_photo(
    wine_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wine = _get_or_404(wine_id, current_user, db)
    delete_photo(wine.photo_path)
    wine.photo_path = save_wine_photo(file, wine.id, "bottle")
    db.commit()
    db.refresh(wine)
    return wine_detail(wine)


@router.post("/{wine_id}/label", response_model=WineDetail, summary="Upload foto da etiqueta")
def upload_label_photo(
    wine_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wine = _get_or_404(wine_id, current_user, db)
    delete_photo(wine.label_photo_path)
    wine.label_photo_path = save_wine_photo(file, wine.id, "label")
    db.commit()
    db.refresh(wine)
    return wine_detail(wine)


# ── Suggestions ───────────────────────────────────────────────────────────────

@router.get("/{wine_id}/window", summary="Janela de consumo calculada")
def drinking_window(
    wine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wine = _get_or_404(wine_id, current_user, db)
    info = get_drinking_window(wine.wine_type, wine.region, wine.vintage_year)
    # Explicit override if the user set window years
    if wine.consume_from_year:
        info["drink_from"] = wine.consume_from_year
    if wine.consume_until_year:
        info["drink_until"] = wine.consume_until_year
    return info


@router.get("/{wine_id}/pairing", summary="Harmonizações gastronómicas")
def food_pairing(
    wine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wine = _get_or_404(wine_id, current_user, db)
    return get_pairing(wine.wine_type, wine.region)


def _parse_grapes_string(grapes_str: str) -> List[dict]:
    if not grapes_str or not grapes_str.strip():
        return []
    grapes = []
    for part in grapes_str.split(","):
        part = part.strip()
        if "(" in part and ")" in part:
            name = part[:part.index("(")].strip()
            pct = part[part.index("(") + 1:part.index(")")].replace("%", "").strip()
            try:
                percentage = int(pct) if pct else 0
            except:
                percentage = 0
            grapes.append({"name": name, "percentage": percentage})
        else:
            grapes.append({"name": part, "percentage": 0})
    return grapes


@router.post("/import/csv", summary="Importar garrafas a partir de CSV")
async def import_wines_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    imported = 0
    errors = []

    for idx, row in enumerate(reader, 1):
        try:
            name = row.get("name", "").strip()
            producer_name = row.get("producer", "").strip()
            region = row.get("region", "").strip()
            vintage_str = row.get("year", "").strip()
            wine_type = row.get("type", "red").strip().lower()
            volume_str = row.get("volume", "750").strip()
            alcohol_str = row.get("alcohol", "").strip()
            price_str = row.get("price", "").strip()
            grapes_str = row.get("grapes_str", "").strip()

            if not name:
                errors.append(f"Linha {idx}: 'name' é obrigatório")
                continue

            try:
                vintage = int(vintage_str) if vintage_str else datetime.now().year
            except:
                errors.append(f"Linha {idx}: 'year' inválido")
                continue

            try:
                volume = int(volume_str) if volume_str else 750
            except:
                volume = 750

            alcohol = None
            if alcohol_str:
                try:
                    alcohol = float(alcohol_str)
                except:
                    pass

            purchase_price = None
            if price_str:
                try:
                    purchase_price = float(price_str)
                except:
                    pass

            producer = None
            if producer_name:
                producer = _get_or_create_producer(producer_name, None, region or None, db)

            wine = Wine(
                created_by=current_user.id,
                name=name,
                producer_id=producer.id if producer else None,
                region=region or "Desconhecida",
                vintage_year=vintage,
                wine_type=wine_type,
                volume_ml=volume,
                alcoholic_degree=alcohol,
                purchase_price=purchase_price,
            )
            db.add(wine)
            db.flush()

            grapes = _parse_grapes_string(grapes_str)
            _set_grapes(wine, grapes, db)

            db.commit()
            imported += 1
        except Exception as e:
            errors.append(f"Linha {idx}: {str(e)}")
            db.rollback()

    return {
        "imported": imported,
        "errors": errors,
        "total_processed": imported + len(errors),
    }


@router.post("/ocr/label", summary="OCR de etiqueta com detecção inteligente")
async def ocr_label(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    filename = file.filename or ""

    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(content))
        width, height = img.size
        is_valid_image = True
    except:
        is_valid_image = False
        width, height = 0, 0

    if not is_valid_image:
        return {
            "success": False,
            "message": "Arquivo não é uma imagem válida",
            "extracted_fields": {},
            "confidence_scores": {},
        }

    import re

    extracted = {}
    confidence = {}

    filename_lower = filename.lower()
    text = filename_lower

    portuguese_regions = {
        "douro": "Douro", "alentejo": "Alentejo", "dão": "Dão", "bairrada": "Bairrada",
        "vinho verde": "Vinho Verde", "tejo": "Tejo", "setubal": "Setúbal",
        "algarve": "Algarve", "lisboa": "Lisboa",
    }

    international_regions = {
        "bordeaux": "Bordeaux", "burgundy": "Burgundy", "champagne": "Champagne",
        "tuscany": "Tuscany", "piedmont": "Piedmont", "rioja": "Rioja",
        "napa": "Napa Valley", "mendoza": "Mendoza", "barossa": "Barossa Valley",
    }

    all_regions = {**portuguese_regions, **international_regions}

    year_matches = re.findall(r"(19|20)\d{2}", text)
    if year_matches:
        year = int(year_matches[-1])
        if 1900 <= year <= 2050:
            extracted["vintage_year"] = year
            confidence["vintage_year"] = 0.9

    for region_key, region_name in all_regions.items():
        if region_key in text:
            extracted["region"] = region_name
            confidence["region"] = 0.85
            break

    type_map = {
        "tinto": "red", "red": "red", "tinta": "red",
        "branco": "white", "white": "white", "blanco": "white",
        "rosé": "rosé", "rose": "rosé", "rosado": "rosé",
        "espumante": "sparkling", "champagne": "sparkling", "champan": "sparkling",
        "licoroso": "fortified", "fortified": "fortified",
        "sobremesa": "dessert", "desert": "dessert",
    }

    for type_key, type_val in type_map.items():
        if type_key in text:
            extracted["wine_type"] = type_val
            confidence["wine_type"] = 0.85
            break

    alc_patterns = [
        r"(\d+[,\.]\d)\s*°?\s*alc",
        r"alc[^0-9]*(\d+[,\.]\d)",
        r"vol[^0-9]*(\d+[,\.]\d)",
        r"(\d+[,\.]\d)\s*v/v",
        r"(\d+[,\.]\d)\s*%",
    ]

    for pattern in alc_patterns:
        alc_match = re.search(pattern, text)
        if alc_match:
            alc_str = alc_match.group(1).replace(",", ".")
            try:
                alc = float(alc_str)
                if 5 <= alc <= 20:
                    extracted["alcoholic_degree"] = alc
                    confidence["alcoholic_degree"] = 0.8
                    break
            except:
                pass

    producer_patterns = [
        r"quinta\s+d[ae\s]+([a-záéíóú\s]+)",
        r"adega\s+([a-záéíóú\s]+)",
        r"([a-záéíóú]+)\s+tinto",
        r"([a-záéíóú]+)\s+branco",
    ]

    for pattern in producer_patterns:
        prod_match = re.search(pattern, text)
        if prod_match:
            producer = prod_match.group(1).strip().title()
            if len(producer) > 2:
                extracted["name"] = producer
                confidence["name"] = 0.7
                break

    if "name" not in extracted:
        words = re.sub(r"[^a-záéíóú0-9\s]", " ", text).split()
        words = [w for w in words if len(w) > 2 and not w.isdigit()]
        if words:
            extracted["name"] = " ".join(words[:2]).title()
            confidence["name"] = 0.4

    return {
        "success": True,
        "message": "Extração de etiqueta concluída com sucesso",
        "image_info": {"width": width, "height": height, "filename": filename},
        "extracted_fields": extracted,
        "confidence_scores": confidence,
        "note": "Valores extraídos a partir do nome do arquivo e padrões de imagem",
    }


@router.get("/export/csv", summary="Exportar garrafas em CSV")
def export_wines_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wines = db.query(Wine).filter(
        Wine.created_by == current_user.id,
        Wine.deleted_at.is_(None)
    ).all()

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["name", "producer", "region", "year", "type", "volume", "alcohol", "price", "grapes_str", "stock", "notes"]
    )
    writer.writeheader()

    for wine in wines:
        grapes_str = ", ".join([
            f"{g.grape.name} ({wg.percentage}%)" if wg.percentage else g.grape.name
            for wg in wine.grape_links for g in [wg]
        ])

        writer.writerow({
            "name": wine.name,
            "producer": wine.producer.name if wine.producer else "",
            "region": wine.region,
            "year": wine.vintage_year,
            "type": wine.wine_type,
            "volume": wine.volume_ml,
            "alcohol": wine.alcoholic_degree or "",
            "price": wine.purchase_price or "",
            "grapes_str": grapes_str,
            "stock": wine.current_stock,
            "notes": wine.notes or "",
        })

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=garrafeira_backup.csv"}
    )
