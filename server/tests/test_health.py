# -*- coding: utf-8 -*-
"""健康检查端点测试"""
from fastapi.testclient import TestClient


def test_health_endpoint_returns_ok():
    """GET /health 应返回 status ok"""
    from app.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
