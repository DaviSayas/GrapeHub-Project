"""Tests for GrapeHub: auth, wines, stock, photos, PDF, suggestions."""
import io

from tests.conftest import make_wine
from app.services.suggestions import get_drinking_window
from app.services.pairing import get_pairing


# ── Auth ────────────────────────────────────────────────────────────────────

def test_register_and_login(client):
    r = client.post("/auth/register", json={
        "name": "Ana", "email": "ana@grapehub.pt", "password": "secret1"})
    assert r.status_code == 201
    assert "access_token" in r.json()


def test_login_wrong_password(client):
    client.post("/auth/register", json={
        "name": "Ana", "email": "ana@grapehub.pt", "password": "secret1"})
    r = client.post("/auth/login", json={"email": "ana@grapehub.pt", "password": "x"})
    assert r.status_code == 401


def test_wines_require_auth(client):
    assert client.get("/wines").status_code == 401


# ── Wine CRUD + relational model ────────────────────────────────────────────

def test_create_wine_with_producer_and_grapes(auth_client):
    wine = make_wine(auth_client)
    assert wine["producer"]["name"] == "Produtor Teste"
    assert wine["current_stock"] == 6
    assert "Touriga Nacional" in wine["grapes_display"]


def test_list_and_get_wine(auth_client):
    wine = make_wine(auth_client)
    assert any(w["id"] == wine["id"] for w in auth_client.get("/wines").json())
    assert auth_client.get(f"/wines/{wine['id']}").json()["name"] == "Quinta Teste"


def test_update_wine(auth_client):
    wine = make_wine(auth_client)
    r = auth_client.put(f"/wines/{wine['id']}", json={"name": "Novo Nome", "min_stock": 5})
    assert r.status_code == 200
    assert r.json()["name"] == "Novo Nome"
    assert r.json()["min_stock"] == 5


def test_delete_wine(auth_client):
    wine = make_wine(auth_client)
    assert auth_client.delete(f"/wines/{wine['id']}").status_code == 204
    assert auth_client.get(f"/wines/{wine['id']}").status_code == 404


def test_producer_autocomplete(auth_client):
    make_wine(auth_client, producer_name="Quinta do Teste Especial")
    res = auth_client.get("/producers", params={"q": "teste"})
    assert res.status_code == 200
    assert any("Teste" in p["name"] for p in res.json())


# ── Stock movements: in / out / adjust ──────────────────────────────────────

def test_stock_in_out_balance(auth_client):
    wine = make_wine(auth_client, initial_stock=10)  # 10 in
    wid = wine["id"]
    auth_client.post("/stock/movements", json={"wine_id": wid, "type": "out", "quantity": 3})
    auth_client.post("/stock/movements", json={"wine_id": wid, "type": "in", "quantity": 5})
    bal = auth_client.get(f"/stock/balance/{wid}").json()
    assert bal["current_stock"] == 12  # 10 - 3 + 5


def test_stock_adjust_sets_absolute(auth_client):
    wine = make_wine(auth_client, initial_stock=10)
    wid = wine["id"]
    auth_client.post("/stock/movements", json={"wine_id": wid, "type": "adjust", "quantity": 4})
    bal = auth_client.get(f"/stock/balance/{wid}").json()
    assert bal["current_stock"] == 4


def test_stock_never_negative(auth_client):
    wine = make_wine(auth_client, initial_stock=2)
    wid = wine["id"]
    auth_client.post("/stock/movements", json={"wine_id": wid, "type": "out", "quantity": 10})
    bal = auth_client.get(f"/stock/balance/{wid}").json()
    assert bal["current_stock"] == 0


def test_cellar_locations(auth_client):
    r = auth_client.post("/stock/locations", json={"name": "Prateleira X"})
    assert r.status_code == 201
    assert any(l["name"] == "Prateleira X" for l in auth_client.get("/stock/locations").json())


# ── Photo upload ────────────────────────────────────────────────────────────

def _png_bytes():
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (40, 60), (139, 41, 66)).save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_photo_upload_valid(auth_client):
    wine = make_wine(auth_client)
    r = auth_client.post(
        f"/wines/{wine['id']}/photo",
        files={"file": ("bottle.png", _png_bytes(), "image/png")},
    )
    assert r.status_code == 200
    assert r.json()["photo_path"].endswith(".png")


def test_photo_upload_invalid_type(auth_client):
    wine = make_wine(auth_client)
    r = auth_client.post(
        f"/wines/{wine['id']}/photo",
        files={"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert r.status_code == 400


def test_label_upload(auth_client):
    wine = make_wine(auth_client)
    r = auth_client.post(
        f"/wines/{wine['id']}/label",
        files={"file": ("label.png", _png_bytes(), "image/png")},
    )
    assert r.status_code == 200
    assert r.json()["label_photo_path"] is not None


# ── Tastings (structured, 1-100) ────────────────────────────────────────────

def test_create_tasting(auth_client):
    wine = make_wine(auth_client)
    r = auth_client.post("/tastings", json={
        "wine_id": wine["id"], "occasion": "Jantar",
        "appearance": "Rubi", "nose": "Frutos negros", "palate": "Encorpado",
        "finish": "Longo", "overall_score": 92, "would_buy_again": True,
    })
    assert r.status_code == 201
    assert r.json()["overall_score"] == 92
    # avg_score should now appear on the wine
    assert auth_client.get(f"/wines/{wine['id']}").json()["avg_score"] == 92


def test_tasting_score_validation(auth_client):
    wine = make_wine(auth_client)
    r = auth_client.post("/tastings", json={"wine_id": wine["id"], "overall_score": 150})
    assert r.status_code == 422  # > 100


# ── Wishlist ────────────────────────────────────────────────────────────────

def test_wishlist(auth_client):
    r = auth_client.post("/wishlist", json={"description": "Pétrus 2005", "priority": "high"})
    assert r.status_code == 201
    assert any(i["description"] == "Pétrus 2005" for i in auth_client.get("/wishlist").json())


# ── Stats & charts ──────────────────────────────────────────────────────────

def test_stats_summary(auth_client):
    make_wine(auth_client, initial_stock=6, purchase_price=10.0)
    s = auth_client.get("/wines/stats/summary").json()
    assert s["total_bottles"] == 6
    assert s["total_value"] == 60.0


def test_charts_endpoint(auth_client):
    make_wine(auth_client)
    c = auth_client.get("/wines/stats/charts").json()
    assert len(c["month_labels"]) == 12
    assert len(c["monthly_consumption"]) == 12
    assert len(c["value_timeline"]) == 12


# ── PDF / CSV export ────────────────────────────────────────────────────────

def test_pdf_export(auth_client):
    make_wine(auth_client)
    r = auth_client.get("/reports/collection.pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"


def test_csv_export(auth_client):
    make_wine(auth_client)
    r = auth_client.get("/reports/collection.csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]


# ── Suggestion logic (pure functions) ───────────────────────────────────────

def test_drinking_window_bordeaux():
    w = get_drinking_window("red", "Bordeaux", 2010)
    assert w["drink_from"] == 2018
    assert w["drink_until"] == 2045


def test_drinking_window_too_young():
    import datetime
    w = get_drinking_window("red", "Bordeaux", datetime.datetime.now().year)
    assert w["status"] == "too_young"


def test_pairing():
    p = get_pairing("red", "Douro")
    assert len(p["foods"]) > 0
    assert "serving_temp" in p
