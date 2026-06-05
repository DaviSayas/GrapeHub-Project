"""Smart drinking window calculator for GrapeHub."""
from datetime import datetime, timezone
from typing import Optional
from app.core.enums import DrinkingWindowStatus


# ── Drinking-window rules: (min_years, max_years, peak_start, peak_end) ────────
# Values are years AFTER the vintage year.
WINDOW_RULES: dict[str, dict[str, tuple[int, int, int, int]]] = {
    "red": {
        "Douro":           (5, 25, 8,  18),
        "Alentejo":        (3, 15, 5,  10),
        "Dão":             (4, 20, 6,  14),
        "Bairrada":        (4, 20, 7,  15),
        "Bordeaux":        (8, 35, 12, 25),
        "Burgundy":        (5, 25, 8,  18),
        "Tuscany":         (5, 30, 8,  20),
        "Piedmont":        (5, 30, 8,  22),
        "Rioja":           (4, 20, 7,  15),
        "Ribera del Duero":(4, 20, 7,  15),
        "Napa Valley":     (5, 25, 8,  18),
        "Mendoza":         (3, 15, 5,  12),
        "_default":        (3, 15, 5,  12),
    },
    "white": {
        "Vinho Verde":     (0,  3, 1,   2),
        "Douro":           (2, 10, 3,   7),
        "Burgundy":        (3, 20, 5,  15),
        "Alsace":          (3, 20, 5,  15),
        "Loire":           (2, 12, 3,   8),
        "Rhône":           (2, 10, 3,   8),
        "_default":        (1,  6, 2,   4),
    },
    "sparkling": {
        "Champagne":       (1, 15, 3,  10),
        "_default":        (0,  5, 1,   3),
    },
    "rosé": {
        "_default":        (0,  3, 0,   2),
    },
    "fortified": {
        "_default":        (5, 50, 10, 40),
    },
    "dessert": {
        "_default":        (3, 30, 5,  20),
    },
}


def get_drinking_window(wine_type: str, region: str, vintage_year: int) -> dict:
    """
    Calculate the drinking window for a wine.

    Returns:
        {
          drink_from: int,
          drink_until: int,
          peak_from: int,
          peak_until: int,
          status: DrinkingWindowStatus,
          label: str,
          years_to_ready: int | None,
          years_to_decline: int | None,
        }
    """
    current_year = datetime.now(timezone.utc).year
    age = current_year - vintage_year

    rules = WINDOW_RULES.get(wine_type, WINDOW_RULES.get("red", {}))
    window = rules.get(region) or rules.get("_default", (3, 15, 5, 12))

    min_y, max_y, peak_s, peak_e = window

    drink_from   = vintage_year + min_y
    drink_until  = vintage_year + max_y
    peak_from    = vintage_year + peak_s
    peak_until   = vintage_year + peak_e

    # ── Determine status ─────────────────────────────────────────────────────
    if age < min_y - 1:
        window_status = DrinkingWindowStatus.TOO_YOUNG
        label = f"Muito jovem — aguardar {drink_from - current_year} ano(s)"
        years_to_ready  = drink_from - current_year
        years_to_decline = None
    elif age < min_y:
        window_status = DrinkingWindowStatus.ALMOST_READY
        label = f"Quase pronto — beber em {drink_from - current_year} ano(s)"
        years_to_ready  = drink_from - current_year
        years_to_decline = None
    elif peak_from <= current_year <= peak_until:
        window_status = DrinkingWindowStatus.PEAK
        label = "✦ No pico de maturidade!"
        years_to_ready  = None
        years_to_decline = peak_until - current_year
    elif drink_from <= current_year < peak_from:
        window_status = DrinkingWindowStatus.READY
        label = "Pronto para beber"
        years_to_ready  = None
        years_to_decline = drink_until - current_year
    elif peak_until < current_year <= drink_until:
        window_status = DrinkingWindowStatus.DECLINING
        label = f"A declinar — beber nos próximos {drink_until - current_year} ano(s)"
        years_to_ready  = None
        years_to_decline = drink_until - current_year
    else:
        window_status = DrinkingWindowStatus.PAST_PEAK
        label = "Passou o pico de consumo"
        years_to_ready  = None
        years_to_decline = 0

    return {
        "drink_from":       drink_from,
        "drink_until":      drink_until,
        "peak_from":        peak_from,
        "peak_until":       peak_until,
        "status":           window_status.value,
        "label":            label,
        "years_to_ready":   years_to_ready,
        "years_to_decline": years_to_decline,
    }


def get_alerts(wines: list) -> list[dict]:
    """
    Generate alerts (drinking window + low stock) for a list of Wine ORM objects.
    Returns sorted list of alerts (most urgent first).
    Each alert includes: wine_id, wine_name, vintage, type, severity, urgency (1-5), message
    """
    current_year = datetime.now(timezone.utc).year
    alerts = []

    for wine in wines:
        stock = wine.current_stock
        # ── Low-stock alert ──────────────────────────────────────────────────
        if wine.min_stock and stock <= wine.min_stock:
            alerts.append({
                "wine_id":   wine.id,
                "wine_name": wine.name,
                "vintage":   wine.vintage_year,
                "type":      "low_stock",
                "severity":  "warning",
                "urgency":   3,
                "message":   f"{wine.name} {wine.vintage_year} — stock baixo ({stock} ≤ mínimo {wine.min_stock}).",
            })

        if stock <= 0:
            continue
        info = get_drinking_window(wine.wine_type, wine.region, wine.vintage_year)

        if info["status"] == DrinkingWindowStatus.PEAK.value:
            alerts.append({
                "wine_id":   wine.id,
                "wine_name": wine.name,
                "vintage":   wine.vintage_year,
                "type":      "peak",
                "severity":  "success",
                "urgency":   5,
                "message":   f"{wine.name} {wine.vintage_year} está no pico! Aproveite agora.",
            })
        elif info["status"] == DrinkingWindowStatus.DECLINING.value:
            if info.get("years_to_decline", 0) <= 2:
                alerts.append({
                    "wine_id":   wine.id,
                    "wine_name": wine.name,
                    "vintage":   wine.vintage_year,
                    "type":      "urgent",
                    "severity":  "danger",
                    "urgency":   5,
                    "message":   f"{wine.name} {wine.vintage_year} — beber urgentemente! A declinar.",
                })
            else:
                alerts.append({
                    "wine_id":   wine.id,
                    "wine_name": wine.name,
                    "vintage":   wine.vintage_year,
                    "type":      "declining",
                    "severity":  "warning",
                    "urgency":   2,
                    "message":   f"{wine.name} {wine.vintage_year} está em declínio. {info['years_to_decline']} ano(s) restantes.",
                })
        elif info["status"] == DrinkingWindowStatus.PAST_PEAK.value:
            alerts.append({
                "wine_id":   wine.id,
                "wine_name": wine.name,
                "vintage":   wine.vintage_year,
                "type":      "past_peak",
                "severity":  "muted",
                "urgency":   1,
                "message":   f"{wine.name} {wine.vintage_year} passou o pico. Consumir em breve.",
            })

    # Sort: urgent (5) > peak (5) > low_stock (3) > declining (2) > past_peak (1)
    order = {"urgent": 0, "peak": 1, "low_stock": 2, "declining": 3, "past_peak": 4}
    alerts.sort(key=lambda a: (order.get(a["type"], 99), -a.get("urgency", 0)))
    # Limit to top 20 to avoid overwhelming
    return alerts[:20]
