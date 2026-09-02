from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_endpoint():
    response = client.post("/api/analyze", json={"text": "I love great code!"})
    assert response.status_code == 200
    data = response.json()
    assert data["sentiment"] == "positive"
    assert data["word_count"] == 4


def test_analyze_rejects_empty():
    response = client.post("/api/analyze", json={"text": ""})
    assert response.status_code == 422


def test_index_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "AI Text Assistant" in response.text


def test_digest_endpoint():
    response = client.post(
        "/api/digest",
        json={"interests": ["focus", "writing", "learning"], "min_engagement": 100},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["fetched"] == 14
    assert len(data["selected"]) > 0
    assert "# Methodology" in data["methodology_markdown"]
    # Low-engagement meme should be filtered out.
    assert all(p["id"] != "1006" for p in data["selected"])


def test_digest_page_served():
    response = client.get("/digest")
    assert response.status_code == 200
    assert "X Digest" in response.text
