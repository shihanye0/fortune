# -*- coding: utf-8 -*-
"""Spec 024: 占卜历史与反馈测试"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.divination_record import DivinationRecord
from app.models.user import User
from app.core.security import hash_password, create_access_token


@pytest.fixture
def auth_user(db_session: Session):
    """创建已认证用户并返回 (user, token)"""
    user = User(
        username="historian",
        email="historian@test.com",
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
def record_factory(db_session: Session, auth_user):
    """创建占卜记录的工厂函数"""
    user, _ = auth_user

    def _create(
        div_type="liuyao",
        question="测试问题",
        raw_data=None,
        llm_interpretation="解读结果",
        user_rating=None,
        user_feedback_text=None,
    ):
        r = DivinationRecord(
            user_id=user.id,
            type=div_type,
            question=question,
            raw_data=raw_data or {"name": "乾为天"},
            llm_interpretation=llm_interpretation,
            user_rating=user_rating,
            user_feedback_text=user_feedback_text,
        )
        db_session.add(r)
        db_session.commit()
        db_session.refresh(r)
        return r

    return _create


# --- GET /api/v1/divination/records ---


class TestDivinationHistory:
    """占卜历史列表"""

    def test_history_with_records(self, client: TestClient, auth_user, record_factory):
        """有占卜记录，按时间倒序"""
        _, token = auth_user
        record_factory(div_type="liuyao", question="工作顺利吗")
        record_factory(div_type="qimen", question="面试结果")

        resp = client.get(
            "/api/v1/divination/records",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert len(body["data"]) == 2
        assert body["meta"]["total"] == 2
        # 验证字段
        item = body["data"][0]
        assert "id" in item
        assert "type" in item
        assert "question" in item
        assert "created_at" in item

    def test_history_empty(self, client: TestClient, auth_user):
        """无记录返回空列表"""
        _, token = auth_user

        resp = client.get(
            "/api/v1/divination/records",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"] == []
        assert body["meta"]["total"] == 0

    def test_history_pagination(self, client: TestClient, auth_user, record_factory):
        """分页功能"""
        _, token = auth_user
        for i in range(15):
            record_factory(question=f"问题{i}")

        resp = client.get(
            "/api/v1/divination/records?page=1&limit=10",
            headers={"Authorization": f"Bearer {token}"},
        )
        body = resp.json()
        assert len(body["data"]) == 10
        assert body["meta"]["total"] == 15
        assert body["meta"]["total_pages"] == 2

    def test_history_filter_by_type(self, client: TestClient, auth_user, record_factory):
        """按类型筛选"""
        _, token = auth_user
        record_factory(div_type="liuyao")
        record_factory(div_type="liuyao")
        record_factory(div_type="qimen")

        resp = client.get(
            "/api/v1/divination/records?type=liuyao",
            headers={"Authorization": f"Bearer {token}"},
        )
        body = resp.json()
        assert len(body["data"]) == 2
        assert all(item["type"] == "liuyao" for item in body["data"])


# --- POST /api/v1/divination/:id/feedback ---


class TestDivinationFeedback:
    """占卜反馈"""

    def test_submit_feedback(self, client: TestClient, auth_user, record_factory):
        """提交反馈成功"""
        _, token = auth_user
        record = record_factory()

        resp = client.post(
            f"/api/v1/divination/{record.id}/feedback",
            json={"rating": 4, "feedback_text": "解读很准"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["user_rating"] == 4

    def test_update_feedback(self, client: TestClient, auth_user, record_factory):
        """修改已有反馈"""
        _, token = auth_user
        record = record_factory(user_rating=3, user_feedback_text="一般")

        resp = client.post(
            f"/api/v1/divination/{record.id}/feedback",
            json={"rating": 5, "feedback_text": "修改后很准"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["user_rating"] == 5

    def test_feedback_not_found(self, client: TestClient, auth_user):
        """记录不存在"""
        _, token = auth_user

        resp = client.post(
            "/api/v1/divination/99999/feedback",
            json={"rating": 4},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_feedback_invalid_rating(self, client: TestClient, auth_user, record_factory):
        """评分超出范围"""
        _, token = auth_user
        record = record_factory()

        resp = client.post(
            f"/api/v1/divination/{record.id}/feedback",
            json={"rating": 6},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422
