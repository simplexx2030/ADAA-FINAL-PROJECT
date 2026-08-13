"""
Tests for STEP 0.

The build spec requires that every milestone ships with a test (Rule F).
For STEP 0 the only promise the system makes is: the server starts and
answers the health check.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    """GET /health must return 200 with exactly {"status": "ok"}."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_never_exposes_the_api_key():
    """
    The landing endpoint may say whether a key is configured, but it must
    never reveal the key itself (build spec Rule H).
    """
    body = client.get("/").text

    assert "gemini_key_configured" in body
    assert "gemini_api_key" not in body
