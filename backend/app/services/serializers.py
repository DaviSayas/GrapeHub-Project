"""Helpers to serialize Wine ORM objects into API response dicts."""


def wine_list_item(wine) -> dict:
    """Compact wine representation for grid/list views."""
    return {
        "id": wine.id,
        "name": wine.name,
        "region": wine.region,
        "vintage_year": wine.vintage_year,
        "wine_type": wine.wine_type,
        "purchase_price": wine.purchase_price,
        "photo_path": wine.photo_path,
        "producer_name": wine.producer.name if wine.producer else "",
        "current_stock": wine.current_stock,
        "avg_score": wine.avg_score,
        "min_stock": wine.min_stock,
    }


def wine_detail(wine) -> dict:
    """Full wine representation for the detail page."""
    return {
        "id": wine.id,
        "name": wine.name,
        "region": wine.region,
        "vintage_year": wine.vintage_year,
        "wine_type": wine.wine_type,
        "volume_ml": wine.volume_ml,
        "alcoholic_degree": wine.alcoholic_degree,
        "purchase_price": wine.purchase_price,
        "description": wine.description,
        "consume_from_year": wine.consume_from_year,
        "consume_until_year": wine.consume_until_year,
        "min_stock": wine.min_stock,
        "created_by": wine.created_by,
        "created_at": wine.created_at,
        "updated_at": wine.updated_at,
        "photo_path": wine.photo_path,
        "label_photo_path": wine.label_photo_path,
        "producer": {
            "id": wine.producer.id,
            "name": wine.producer.name,
            "country": wine.producer.country,
            "region": wine.producer.region,
            "website": wine.producer.website,
        } if wine.producer else None,
        "grapes": [
            {"name": link.grape.name, "percentage": link.percentage}
            for link in wine.grape_links if link.grape
        ],
        "current_stock": wine.current_stock,
        "avg_score": wine.avg_score,
        "grapes_display": wine.grapes_display,
    }
