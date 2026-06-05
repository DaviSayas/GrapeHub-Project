"""GrapeHub — seed data completo (usuários, produtores, castas, vinhos, degustações, etc).

Usage:
    cd backend
    python -m app.db.seed
"""
import logging
from datetime import datetime, timedelta, timezone

from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models.user import User
from app.models.producer import Producer
from app.models.grape import Grape
from app.models.wine import Wine
from app.models.grape import WineGrape
from app.models.stock import StockMovement
from app.models.tasting import Tasting
from app.models.location import CellarLocation

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def init_db():
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created")


def seed():
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            logger.info("Data already exists — skipping seed")
            return

        # ── Users ─────────────────────────────────────────────────────────────
        admin = User(name="Administrador", email="admin@grapehub.pt",
                     hashed_password=hash_password("admin123"), role="admin", active=True)
        demo = User(name="Demo", email="demo@grapehub.pt",
                    hashed_password=hash_password("demo123"), role="user", active=True)
        partner = User(name="Parceiro", email="parceiro@grapehub.pt",
                       hashed_password=hash_password("parceiro123"), role="user", active=True)
        db.add_all([admin, demo, partner])
        db.commit()
        for u in (admin, demo, partner):
            db.refresh(u)
        logger.info("Users seeded (3)")

        # ── Cellar Locations ──────────────────────────────────────────────────
        loc1 = CellarLocation(user_id=demo.id, name="Prateleira 1", description="Tinta Reserva")
        loc2 = CellarLocation(user_id=demo.id, name="Prateleira 2", description="Branco & Espumante")
        loc3 = CellarLocation(user_id=demo.id, name="Adega Fresca", description="Porto & Generoso")
        db.add_all([loc1, loc2, loc3])
        db.commit()
        for l in (loc1, loc2, loc3):
            db.refresh(l)
        logger.info("Locations seeded (3)")

        # ── Producers (10 PT reais) ───────────────────────────────────────────
        producers_data = [
            ("Quinta da Aveleda", "Portugal", "Vinho Verde"),
            ("Herdade do Rocim", "Portugal", "Alentejo"),
            ("Symington Family", "Portugal", "Douro"),
            ("Casa Ferreirinha", "Portugal", "Douro"),
            ("Quinta do Crasto", "Portugal", "Douro"),
            ("Poço Coelho", "Portugal", "Alentejo"),
            ("Esporão", "Portugal", "Alentejo"),
            ("Adega Mayor", "Portugal", "Alentejo"),
            ("Caves Transmontanas", "Portugal", "Trás-os-Montes"),
            ("Calem", "Portugal", "Porto"),
        ]
        producers = {}
        for name, country, region in producers_data:
            p = Producer(name=name, country=country, region=region)
            db.add(p)
            producers[name] = p
        db.commit()
        for p in producers.values():
            db.refresh(p)
        logger.info("Producers seeded (%d)", len(producers))

        # ── Grapes (10 castas) ────────────────────────────────────────────────
        grapes_data = ["Touriga Nacional", "Touriga Franca", "Tinta Roriz", "Tinta Barroca",
                      "Aragonez", "Alicante", "Vinhão", "Avesso", "Verdelho", "Encruzado"]
        grapes = {}
        for name in grapes_data:
            g = Grape(name=name)
            db.add(g)
            grapes[name] = g
        db.commit()
        for g in grapes.values():
            db.refresh(g)
        logger.info("Grapes seeded (%d)", len(grapes))

        # ── Wines (20 garrafas) ───────────────────────────────────────────────
        now = datetime.now(timezone.utc)
        wines_data = [
            ("Aveleda Branco", producers["Quinta da Aveleda"], "Vinho Verde", "white", 2023, 75, 13.5, 8.50, [("Avesso", 100)]),
            ("Rocim Tinto Reserva", producers["Herdade do Rocim"], "Alentejo", "red", 2019, 75, 14.0, 25.00, [("Aragonez", 70), ("Alicante", 30)]),
            ("Graham's Tawny 20 Anos", producers["Calem"], "Porto", "fortified", 2003, 75, 20.0, 85.00, [("Touriga Nacional", 50), ("Tinta Roriz", 50)]),
            ("Crasto Douro Tinto", producers["Quinta do Crasto"], "Douro", "red", 2018, 75, 13.5, 18.00, [("Touriga Nacional", 60), ("Touriga Franca", 40)]),
            ("Esporão Branco", producers["Esporão"], "Alentejo", "white", 2022, 75, 12.5, 9.50, [("Encruzado", 100)]),
            ("Mayor Memória Tinto", producers["Adega Mayor"], "Alentejo", "red", 2020, 75, 14.5, 12.00, [("Aragonez", 80), ("Alicante", 20)]),
            ("Ferreirinha Réserva Especial", producers["Casa Ferreirinha"], "Douro", "red", 2017, 75, 14.0, 35.00, [("Touriga Nacional", 100)]),
            ("Transmontanas Branco", producers["Caves Transmontanas"], "Trás-os-Montes", "white", 2022, 75, 11.5, 7.50, [("Verdelho", 100)]),
            ("Rocim Cortiçol Tinto", producers["Herdade do Rocim"], "Alentejo", "red", 2021, 75, 14.0, 15.00, [("Aragonez", 100)]),
            ("Crasto Douro Branco", producers["Quinta do Crasto"], "Douro", "white", 2022, 75, 12.0, 11.00, [("Encruzado", 70), ("Verdelho", 30)]),
            ("Aveleda Reserva Espumante", producers["Quinta da Aveleda"], "Vinho Verde", "sparkling", 2021, 75, 12.0, 16.00, [("Avesso", 100)]),
            ("Graham's Vintage 2017", producers["Calem"], "Porto", "fortified", 2017, 75, 20.0, 120.00, [("Touriga Nacional", 80), ("Tinta Barroca", 20)]),
            ("Esporão Tinto Reserva", producers["Esporão"], "Alentejo", "red", 2019, 75, 14.5, 22.00, [("Aragonez", 60), ("Alicante", 40)]),
            ("Poço Coelho Tinto", producers["Poço Coelho"], "Alentejo", "red", 2020, 75, 13.5, 13.00, [("Aragonez", 90), ("Alicante", 10)]),
            ("Mayor Branco", producers["Adega Mayor"], "Alentejo", "white", 2023, 75, 12.0, 8.50, [("Encruzado", 100)]),
            ("Symington Douro Tinto", producers["Symington Family"], "Douro", "red", 2018, 75, 14.0, 28.00, [("Touriga Nacional", 70), ("Tinta Roriz", 30)]),
            ("Aveleda Vinho Verde Rosé", producers["Quinta da Aveleda"], "Vinho Verde", "rosé", 2023, 75, 12.0, 7.50, [("Vinhão", 100)]),
            ("Crasto LBV", producers["Quinta do Crasto"], "Douro", "fortified", 2019, 75, 19.5, 45.00, [("Touriga Nacional", 100)]),
            ("Rocim Premium", producers["Herdade do Rocim"], "Alentejo", "red", 2016, 75, 14.5, 32.00, [("Aragonez", 100)]),
            ("Ferreirinha Douro Branco", producers["Casa Ferreirinha"], "Douro", "white", 2023, 75, 12.5, 10.00, [("Verdelho", 100)]),
        ]

        wines = {}
        for title, producer, region, wine_type, vintage, volume, alcohol, price, grape_list in wines_data:
            w = Wine(
                name=title,
                producer_id=producer.id,
                region=region,
                wine_type=wine_type,
                vintage_year=vintage,
                volume_ml=volume,
                alcoholic_degree=alcohol,
                purchase_price=price,
                created_by=demo.id,
                min_stock=2,
            )
            db.add(w)
            db.flush()

            for grape_name, percentage in grape_list:
                wg = WineGrape(wine_id=w.id, grape_id=grapes[grape_name].id, percentage=percentage)
                db.add(wg)

            wines[title] = w

        db.commit()
        for w in wines.values():
            db.refresh(w)
        logger.info("Wines seeded (%d)", len(wines))

        # ── Stock Movements ───────────────────────────────────────────────────
        for title, wine in list(wines.items())[:15]:
            quantity = 1 if "Vintage" in title or "Réserva" in title else 2
            sm = StockMovement(
                wine_id=wine.id,
                location_id=loc1.id if wine.wine_type == "red" else (loc2.id if wine.wine_type != "fortified" else loc3.id),
                type="in",
                quantity=quantity,
                reason="Compra inicial",
                price=wine.purchase_price,
                date=now - timedelta(days=30),
                notes="Entrada inicial de stock"
            )
            db.add(sm)

        db.commit()
        logger.info("Stock movements seeded (15)")

        # ── Tastings (5 degustações) ──────────────────────────────────────────
        tastings_data = [
            (wines["Rocim Tinto Reserva"], "Jantar com amigos", "Rubi profundo",
             "Frutas vermelhas, especiarias", "Macio, taninos velvety", "Persistente", 92, True),
            (wines["Graham's Tawny 20 Anos"], "Tarde de degustação", "Âmbar dourado",
             "Nozes, passa, baunilha", "Suave, redondo", "Muito longo", 94, True),
            (wines["Crasto Douro Tinto"], "Almoço", "Rubi intenso",
             "Cereja, tabaco", "Estruturado, fresco", "Médio", 88, True),
            (wines["Esporão Branco"], "Aperitivo", "Amarelo claro",
             "Cítricos, flores brancas", "Fresco, mineralizado", "Limpo", 85, True),
            (wines["Mayor Memória Tinto"], "Jogo de tabuleiro", "Rubi escuro",
             "Ameixa, madeira", "Macio, elegante", "Bom", 87, True),
        ]

        for wine, occasion, appearance, nose, palate, finish, score, would_buy in tastings_data:
            t = Tasting(
                wine_id=wine.id,
                user_id=demo.id,
                date=now - timedelta(days=15),
                occasion=occasion,
                appearance=appearance,
                nose=nose,
                palate=palate,
                finish=finish,
                overall_score=score,
                would_buy_again=would_buy
            )
            db.add(t)

        db.commit()
        logger.info("Tastings seeded (5)")

    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    seed()
    print("\n[OK] GrapeHub inicializado com sucesso!")
    print("   Admin:    admin@grapehub.pt    /  admin123")
    print("   Demo:     demo@grapehub.pt     /  demo123")
    print("   Parceiro: parceiro@grapehub.pt /  parceiro123")
    print("\n   Dados demo: 10 produtores, 10 castas, 20 vinhos, movimentos de stock, 5 degustações\n")
