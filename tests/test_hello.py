from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_hello_endpoint():
    resp = client.get("/hello")
    assert resp.status_code == 200
    data = resp.json()
    assert "message" in data
    assert "supabaseConfigured" in data
