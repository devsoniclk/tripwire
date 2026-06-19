"""Tests for tripwire.proxy."""

import pytest
from fastapi.testclient import TestClient
from tripwire.proxy import create_proxy_app
from tripwire.budget import Budget


def test_proxy_app_creation():
    app = create_proxy_app(upstream="https://api.openai.com", budget=Budget(max_usd=10))
    assert app is not None


def test_proxy_health():
    """Verify the app starts and responds to an unknown route with 404."""
    app = create_proxy_app(upstream="https://api.openai.com", budget=Budget(max_usd=10))
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 404  # No health endpoint, just checking app works
