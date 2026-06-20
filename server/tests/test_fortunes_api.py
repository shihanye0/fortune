# -*- coding: utf-8 -*-
"""Spec 019-021: 运势查看 API 测试"""
from datetime import date, datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.daily_fortune import DailyFortune
from app.models.user import User
from app.core.security import hash_password, create_access_token


@pytest.fixture
def auth_user(db_session: Session):
    """创建已认证用户并返回 (user, token)"""
    user = User(
        username="fortuner",
        email="fortuner@test.com",
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


@pytest.fixture
def fortune_factory(db_session: Session, auth_user):
    """创建运势记录的工厂函数"""
    user, _ = auth_user

    def _create(
        fortune_date=None,
        overall_score=4,
        career_score=4,
        wealth_score=3,
        love_score=5,
        health_score=3,
        llm_interpretation="今日运势不错",
        user_rating=None,
        user_feedback_tags=None,
        user_feedback_text=None,
    ):
        d = fortune_date or date.today()
        f = DailyFortune(
            user_id=user.id,
            date=d,
            heavenly_stem="甲",
            earthly_branch="子",
            overall_score=overall_score,
            career_fortune={"score": career_score, "detail": "事业运良好"},
            wealth_fortune={"score": wealth_score, "detail": "财运一般"},
            love_fortune={"score": love_score, "detail": "感情运佳"},
            health_fortune={"score": health_score, "detail": "注意休息"},
            lucky_color="红色",
            lucky_number="3, 8",
            lucky_direction="东方",
            llm_interpretation=llm_interpretation,
            user_rating=user_rating,
            user_feedback_tags=user_feedback_tags,
            user_feedback_text=user_feedback_text,
        )
        db_session.add(f)
        db_session.commit()
        db_session.refresh(f)
        return f

    return _create


# --- Spec 019: 今日运势查看 ---


class TestTodayFortune:
    """GET /api/v1/fortunes/today"""

    def test_today_fortune_exists(self, client: TestClient, auth_user, fortune_factory):
        """今日运势已生成，返回完整数据"""
        _, token = auth_user
        fortune_factory()

        resp = client.get(
            "/api/v1/fortunes/today",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["date"] == date.today().isoformat()
        assert data["overall_score"] == 4
        assert data["career"]["score"] == 4
        assert data["wealth"]["score"] == 3
        assert data["love"]["score"] == 5
        assert data["health"]["score"] == 3
        assert data["lucky_color"] == "红色"
        assert data["lucky_number"] == "3, 8"
        assert data["lucky_direction"] == "东方"
        assert "今日运势不错" in data["interpretation"]

    def test_today_fortune_not_generated(self, client: TestClient, auth_user):
        """今日运势未生成，返回提示"""
        _, token = auth_user

        resp = client.get(
            "/api/v1/fortunes/today",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"] is None
        assert "生成中" in body["message"]

    def test_today_fortune_unauthenticated(self, client: TestClient):
        """未登录返回 403"""
        resp = client.get("/api/v1/fortunes/today")
        assert resp.status_code == 401


# --- Spec 020: 历史运势列表 ---


class TestFortuneHistory:
    """GET /api/v1/fortunes"""

    def test_history_with_records(self, client: TestClient, auth_user, fortune_factory):
        """有运势记录，按日期倒序返回"""
        _, token = auth_user
        # 创建 3 条不同日期的记录
        from datetime import timedelta

        fortune_factory(fortune_date=date.today(), overall_score=4)
        fortune_factory(
            fortune_date=date.today() - timedelta(days=1), overall_score=3
        )
        fortune_factory(
            fortune_date=date.today() - timedelta(days=2), overall_score=5
        )

        resp = client.get(
            "/api/v1/fortunes",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert len(body["data"]) == 3
        # 倒序：最新的在前
        assert body["data"][0]["date"] == date.today().isoformat()
        assert body["meta"]["total"] == 3
        assert body["meta"]["page"] == 1

    def test_history_empty(self, client: TestClient, auth_user):
        """无历史记录返回空列表"""
        _, token = auth_user

        resp = client.get(
            "/api/v1/fortunes",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"] == []
        assert body["meta"]["total"] == 0

    def test_history_pagination(self, client: TestClient, auth_user, fortune_factory):
        """分页功能正常"""
        _, token = auth_user
        from datetime import timedelta

        for i in range(25):
            fortune_factory(
                fortune_date=date.today() - timedelta(days=i), overall_score=3
            )

        # 第 1 页
        resp = client.get(
            "/api/v1/fortunes?page=1&limit=10",
            headers={"Authorization": f"Bearer {token}"},
        )
        body = resp.json()
        assert len(body["data"]) == 10
        assert body["meta"]["total"] == 25
        assert body["meta"]["total_pages"] == 3

        # 第 3 页
        resp = client.get(
            "/api/v1/fortunes?page=3&limit=10",
            headers={"Authorization": f"Bearer {token}"},
        )
        body = resp.json()
        assert len(body["data"]) == 5


# --- Spec 021: 运势详情与反馈 ---


class TestFortuneDetail:
    """GET /api/v1/fortunes/:id"""

    def test_detail_exists(self, client: TestClient, auth_user, fortune_factory):
        """运势详情存在"""
        _, token = auth_user
        fortune = fortune_factory()

        resp = client.get(
            f"/api/v1/fortunes/{fortune.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["overall_score"] == 4
        assert body["data"]["lucky_color"] == "红色"

    def test_detail_not_found(self, client: TestClient, auth_user):
        """运势不存在"""
        _, token = auth_user

        resp = client.get(
            "/api/v1/fortunes/99999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_detail_other_user_forbidden(
        self, client: TestClient, auth_user, db_session: Session, fortune_factory
    ):
        """不能查看其他用户的运势"""
        _, token = auth_user
        fortune = fortune_factory()

        # 创建另一个用户
        other = User(
            username="other",
            email="other@test.com",
            password_hash=hash_password("Pass1234"),
            gender=1,
            birth_year=1995,
            birth_month=1,
            birth_day=1,
            birth_hour=0,
        )
        db_session.add(other)
        db_session.commit()
        db_session.refresh(other)
        other_token = create_access_token(user_id=other.id)

        resp = client.get(
            f"/api/v1/fortunes/{fortune.id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert resp.status_code == 404


class TestFortuneFeedback:
    """POST /api/v1/fortunes/:id/feedback"""

    def test_submit_feedback(self, client: TestClient, auth_user, fortune_factory):
        """提交反馈成功"""
        _, token = auth_user
        fortune = fortune_factory()

        resp = client.post(
            f"/api/v1/fortunes/{fortune.id}/feedback",
            json={"rating": 4, "tags": ["准", "有帮助"], "feedback_text": "财运分析很准"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["user_rating"] == 4

    def test_update_feedback(self, client: TestClient, auth_user, fortune_factory):
        """修改已有反馈"""
        _, token = auth_user
        fortune = fortune_factory(user_rating=3, user_feedback_tags=["不准"])

        resp = client.post(
            f"/api/v1/fortunes/{fortune.id}/feedback",
            json={"rating": 5, "tags": ["准"], "feedback_text": "修改后很准"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["user_rating"] == 5

    def test_feedback_invalid_rating(self, client: TestClient, auth_user, fortune_factory):
        """评分超出范围"""
        _, token = auth_user
        fortune = fortune_factory()

        resp = client.post(
            f"/api/v1/fortunes/{fortune.id}/feedback",
            json={"rating": 6, "tags": []},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_feedback_not_found(self, client: TestClient, auth_user):
        """运势不存在"""
        _, token = auth_user

        resp = client.post(
            "/api/v1/fortunes/99999/feedback",
            json={"rating": 4, "tags": []},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
