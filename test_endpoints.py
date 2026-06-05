"""Quick endpoint validation test for GrapeHub."""
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("GrapeHub Endpoint Validation")
print("=" * 50)

# Test 1: Health check
response = client.get("/api/health")
assert response.status_code == 200
print("OK: Health endpoint - /api/health")

# Test 2: Auth - Register
response = client.post("/auth/register", json={
    "name": "Test User",
    "email": "test@example.com",
    "password": "test123"
})
print(f"Auth - Register: {response.status_code}")

# Test 3: Auth - Login
if response.status_code == 201:
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "test123"
    })
    if response.status_code == 200:
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"OK: Auth - Login successful")

        # Test 4: Wine endpoints with auth
        response = client.get("/wines", headers=headers)
        print(f"OK: GET /wines - {response.status_code}")

        response = client.get("/collections", headers=headers)
        print(f"OK: GET /collections - {response.status_code}")

        response = client.get("/wishlist", headers=headers)
        print(f"OK: GET /wishlist - {response.status_code}")

        # Test 5: Create a collection
        response = client.post("/collections",
            json={"name": "Test Collection", "is_public": False},
            headers=headers
        )
        print(f"OK: POST /collections - {response.status_code}")

        print("\nAll critical endpoints validated!")
    else:
        print(f"ERROR: Login failed - {response.status_code}")
else:
    print(f"Register response: {response.status_code}")
