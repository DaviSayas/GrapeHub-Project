"""Pytest fixtures for GrapeHub — in-memory DB + authenticated client."""
import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import Base, get_db  # noqa: E402
import app.models  # noqa: E402,F401  (register all models)
from app.main import app  # noqa: E402

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def _setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client):
    client.post("/auth/register", json={
        "name": "Test Sommelier", "email": "tester@grapehub.pt", "password": "test123",
    })
    res = client.post("/auth/login", json={
        "email": "tester@grapehub.pt", "password": "test123",
    })
    token = res.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def make_wine(client, **overrides):
    """Helper: create a wine and return its detail JSON."""
    payload = {
        "name": "Quinta Teste", "producer_name": "Produtor Teste",
        "region": "Douro", "vintage_year": 2015, "wine_type": "red",
        "purchase_price": 25.0, "initial_stock": 6, "min_stock": 2,
        "grapes": [{"name": "Touriga Nacional", "percentage": 100}],
    }
    payload.update(overrides)
    r = client.post("/wines", json=payload)
    assert r.status_code == 201, r.text
    return r.json()
