# -*- coding: utf-8 -*-
"""Spec 022-023: 占卜 API 测试"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import hash_password, create_access_token


@pytest.fixture
def auth_user(db_session: Session):
    """创建已认证用户并返回 (user, token)"""
    user = User(
        username="diviner",
        email="diviner@test.com",
        password_hash=hash_password("Pass1234"),
        birth_year=1990,
        birth_month=6,
        birth_day=15,
        birth_hour=8,
        gender=1,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token(user_id=user.id)
    return user, token


# --- Spec 022: 六爻占卜 ---


class TestLiuyaoDivination:
    """POST /api/v1/divination/liuyao"""

    @patch("fortune_engine.services.deepseek._call_deepseek", return_value="卦象显示事业顺利")
    def test_liuyao_with_question(self, mock_llm, client: TestClient, auth_user):
        """输入问题占卜"""
        _, token = auth_user

        resp = client.post(
            "/api/v1/divination/liuyao",
            json={"question": "最近工作是否顺利", "method": "coin"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["question"] == "最近工作是否顺利"
        assert "hexagram" in data
        assert data["hexagram"]["name"]  # 有卦名
        assert data["hexagram"]["lines"]  # 有六爻
        assert "interpretation" in data
        assert data["interpretation"] == "卦象显示事业顺利"
        mock_llm.assert_called_once()

    @patch("fortune_engine.services.deepseek._call_deepseek", return_value="总体运势分析")
    def test_liuyao_without_question(self, mock_llm, client: TestClient, auth_user):
        """不输入问题直接占卜"""
        _, token = auth_user

        resp = client.post(
            "/api/v1/divination/liuyao",
            json={"method": "coin"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["question"] is None or body["data"]["question"] == ""

    def test_liuyao_unauthenticated(self, client: TestClient):
        """未登录返回 401"""
        resp = client.post(
            "/api/v1/divination/liuyao",
            json={"method": "coin"},
        )
        assert resp.status_code == 401

    @patch("fortune_engine.services.deepseek._call_deepseek", return_value=None)
    def test_liuyao_llm_failure(self, mock_llm, client: TestClient, auth_user):
        """LLM 失败时返回降级文本"""
        _, token = auth_user

        resp = client.post(
            "/api/v1/divination/liuyao",
            json={"question": "测试", "method": "coin"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        # 应有降级解读
        assert body["data"]["interpretation"]


# --- Spec 023: 奇门遁甲 ---


class TestQimenDivination:
    """POST /api/v1/divination/qimen"""

    @patch("fortune_engine.services.deepseek._call_deepseek", return_value="奇门盘面分析")
    def test_qimen_question_mode(self, mock_llm, client: TestClient, auth_user):
        """输入问题起盘"""
        _, token = auth_user

        resp = client.post(
            "/api/v1/divination/qimen",
            json={"question": "明天面试是否顺利", "mode": "question"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["question"] == "明天面试是否顺利"
        assert "chart" in data
        assert data["chart"]["yin_yang"] in ("阳遁", "阴遁")
        assert 1 <= data["chart"]["ju_shu"] <= 9
        assert "palace" in data["chart"]
        assert len(data["chart"]["palace"]) == 9
        assert "interpretation" in data
        mock_llm.assert_called_once()

    @patch("fortune_engine.services.deepseek._call_deepseek", return_value="当前时辰分析")
    def test_qimen_realtime_mode(self, mock_llm, client: TestClient, auth_user):
        """实时看盘模式"""
        _, token = auth_user

        resp = client.post(
            "/api/v1/divination/qimen",
            json={"mode": "realtime"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["question"] is None or data["question"] == ""
        assert "chart" in data

    def test_qimen_unauthenticated(self, client: TestClient):
        """未登录返回 401"""
        resp = client.post(
            "/api/v1/divination/qimen",
            json={"mode": "realtime"},
        )
        assert resp.status_code == 401

    @patch("fortune_engine.services.deepseek._call_deepseek", return_value=None)
    def test_qimen_llm_failure(self, mock_llm, client: TestClient, auth_user):
        """LLM 失败时返回降级文本"""
        _, token = auth_user

        resp = client.post(
            "/api/v1/divination/qimen",
            json={"mode": "realtime"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["interpretation"]
