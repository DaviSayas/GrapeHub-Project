"""Generate a PDF report of the wine collection using ReportLab."""
import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from app.core.enums import WineType
from app.services.suggestions import get_drinking_window

# Brand colours
WINE = colors.HexColor("#8B2942")
GOLD = colors.HexColor("#C9A84C")
DARK = colors.HexColor("#141414")
LIGHT = colors.HexColor("#F0EBE3")

TYPE_LABELS = {
    "red": "Tinto", "white": "Branco", "rosé": "Rosé",
    "sparkling": "Espumante", "fortified": "Licoroso",
}


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "GHTitle", parent=styles["Title"], fontSize=28, textColor=WINE,
        spaceAfter=6, fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        "GHSubtitle", parent=styles["Normal"], fontSize=12, textColor=colors.grey,
        spaceAfter=4, alignment=1,
    ))
    styles.add(ParagraphStyle(
        "GHSection", parent=styles["Heading2"], fontSize=15, textColor=WINE,
        spaceBefore=18, spaceAfter=8, fontName="Helvetica-Bold",
    ))
    return styles


def generate_collection_pdf(wines: list, owner_name: str = "") -> bytes:
    """Build the collection PDF and return raw bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        title="A Minha Garrafeira — GrapeHub",
    )
    styles = _styles()
    story = []

    now = datetime.now(timezone.utc)
    current_year = now.year

    total_bottles = sum(w.current_stock for w in wines)
    total_value = sum((w.purchase_price or 0) * w.current_stock for w in wines)

    # ── Cover ─────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph("🍷 A Minha Garrafeira", styles["GHTitle"]))
    story.append(Paragraph("Relatório da Colecção · GrapeHub", styles["GHSubtitle"]))
    if owner_name:
        story.append(Paragraph(owner_name, styles["GHSubtitle"]))
    story.append(Paragraph(
        f"Exportado em {now.strftime('%d/%m/%Y %H:%M')}", styles["GHSubtitle"]
    ))
    story.append(Spacer(1, 0.8 * cm))

    summary = Table([
        ["Referências", "Garrafas", "Valor Total"],
        [str(len(wines)), str(total_bottles), f"€ {total_value:,.2f}"],
    ], colWidths=[5.5 * cm, 5.5 * cm, 5.5 * cm])
    summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), WINE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, 1), 18),
        ("TEXTCOLOR", (0, 1), (-1, 1), WINE),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
    ]))
    story.append(summary)

    # ── Catalogue table ───────────────────────────────────────────────────────
    story.append(Paragraph("Catálogo Completo", styles["GHSection"]))
    header = ["Nome", "Produtor", "Ano", "Tipo", "Stock", "Nota", "Valor"]
    rows = [header]
    for w in sorted(wines, key=lambda x: (x.region, x.name)):
        stock = w.current_stock
        rows.append([
            Paragraph(w.name, styles["BodyText"]),
            Paragraph(w.producer.name if w.producer else "—", styles["BodyText"]),
            str(w.vintage_year),
            TYPE_LABELS.get(w.wine_type, w.wine_type),
            str(stock),
            str(int(w.avg_score)) if w.avg_score else "—",
            f"€{(w.purchase_price or 0) * stock:,.0f}",
        ])
    # Totals footer
    rows.append([
        Paragraph("<b>TOTAIS</b>", styles["BodyText"]), "", "", "",
        str(total_bottles), "", f"€{total_value:,.0f}",
    ])

    cat = Table(rows, colWidths=[4.2 * cm, 3.6 * cm, 1.2 * cm, 1.8 * cm, 1.3 * cm, 1.2 * cm, 2.2 * cm], repeatRows=1)
    cat.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), GOLD),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ("ALIGN", (6, 0), (6, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F7F2EA")]),
        ("BACKGROUND", (0, -1), (-1, -1), GOLD),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(cat)

    # ── Top tasted ────────────────────────────────────────────────────────────
    rated = [w for w in wines if w.avg_score]
    rated.sort(key=lambda x: x.avg_score, reverse=True)
    if rated:
        story.append(Paragraph("★ Top Degustadas", styles["GHSection"]))
        top_rows = [["Vinho", "Ano", "Classificação"]]
        for w in rated[:10]:
            top_rows.append([
                Paragraph(f"{w.name} — {w.producer.name if w.producer else ''}", styles["BodyText"]),
                str(w.vintage_year),
                f"{w.avg_score}/100",
            ])
        top = Table(top_rows, colWidths=[10 * cm, 2 * cm, 3.5 * cm], repeatRows=1)
        top.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), WINE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F2EA")]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(top)

    # ── Drink soon ────────────────────────────────────────────────────────────
    soon = []
    for w in wines:
        if w.current_stock <= 0:
            continue
        win = get_drinking_window(w.wine_type, w.region, w.vintage_year)
        until = w.consume_until_year or win["drink_until"]
        if until <= current_year + 2:
            soon.append((w, until))
    if soon:
        soon.sort(key=lambda t: t[1])
        story.append(Paragraph("⏳ Consumir em Breve (próximos 2 anos)", styles["GHSection"]))
        soon_rows = [["Vinho", "Ano", "Beber até", "Stock"]]
        for w, until in soon:
            soon_rows.append([
                Paragraph(f"{w.name} — {w.producer.name if w.producer else ''}", styles["BodyText"]),
                str(w.vintage_year), str(until), str(w.current_stock),
            ])
        st = Table(soon_rows, colWidths=[9 * cm, 2 * cm, 2.5 * cm, 2 * cm], repeatRows=1)
        st.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#B45309")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FDF3E7")]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(st)

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        "Gerado por GrapeHub · Gestão de Garrafeira Pessoal",
        ParagraphStyle("foot", parent=styles["Normal"], fontSize=8,
                       textColor=colors.grey, alignment=1),
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()
