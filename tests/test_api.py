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


def test_digest_endpoint_with_url(monkeypatch):
    import json
    from pathlib import Path

    import xdigest.sources.x_syndication as syn

    payload = json.loads(
        (Path(__file__).parent / "data" / "syndication_article.json").read_text(
            encoding="utf-8"
        )
    )

    def fake_fetch_post(url_or_id, **kwargs):
        return syn.parse_syndication(payload)

    monkeypatch.setattr(syn, "fetch_post", fake_fetch_post)

    response = client.post(
        "/api/digest",
        json={
            "interests": ["微信贴图号"],
            "min_engagement": 0,
            "lang": "zh",
            "url": "https://x.com/qihang_zeng6688/status/2082293843353821306",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["fetched"] == 1
    assert len(data["selected"]) == 1
    post = data["selected"][0]
    assert post["author"] == "@qihang_zeng6688"
    assert "微信贴图号" in post["matched_keywords"]
