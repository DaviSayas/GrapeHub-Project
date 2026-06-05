"""Report API — PDF and CSV export of the collection."""
import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.wine import Wine
from app.services.pdf_report import generate_collection_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


def _user_wines(user: User, db: Session):
    return db.query(Wine).filter(
        Wine.created_by == user.id, Wine.deleted_at.is_(None)
    ).all()


@router.get("/collection.pdf", summary="Exportar colecção em PDF")
def collection_pdf(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wines = _user_wines(current_user, db)
    pdf_bytes = generate_collection_pdf(wines, owner_name=current_user.name)
    filename = f"garrafeira_{datetime.now().strftime('%Y%m%d')}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/collection.csv", summary="Exportar colecção em CSV")
def collection_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wines = _user_wines(current_user, db)
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow([
        "ID", "Nome", "Produtor", "Região", "Ano", "Tipo", "Castas",
        "Volume (ml)", "Álcool (%)", "Stock", "Stock mínimo",
        "Preço (€)", "Classificação média", "Beber de", "Beber até",
    ])
    for w in wines:
        writer.writerow([
            w.id, w.name, w.producer.name if w.producer else "", w.region,
            w.vintage_year, w.wine_type, w.grapes_display, w.volume_ml,
            w.alcoholic_degree or "", w.current_stock, w.min_stock,
            w.purchase_price or "", w.avg_score or "",
            w.consume_from_year or "", w.consume_until_year or "",
        ])
    out.seek(0)
    filename = f"garrafeira_{datetime.now().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([out.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
