# -*- coding: utf-8 -*-
"""Spec 018: 每日推送调度测试"""
from datetime import date
from unittest.mock import patch, MagicMock

import pytest

from app.models.user import User
from app.models.daily_fortune import DailyFortune
from app.core.security import hash_password


def _create_user(db, push_enabled=True, push_channel="email", push_time="07:00",
                 feishu_webhook=None, email="push@test.com"):
    """创建带推送设置的用户"""
    user = User(
        username="push_user",
        email=email,
        password_hash=hash_password("Pass1234"),
        birth_year=1990, birth_month=6, birth_day=15,
        birth_hour=8, gender=1,
        push_enabled=push_enabled,
        push_channel=push_channel,
        push_time=push_time,
        feishu_webhook=feishu_webhook,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestDailyPushAPI:
    """POST /api/v1/internal/daily-push"""

    @patch("app.services.push_email.send_fortune_email", return_value=True)
    @patch("fortune_engine.services.deepseek.interpret_daily", return_value="今日运势良好")
    def test_push_to_enabled_users(self, mock_llm, mock_email, client, db_session):
        """推送给开启推送的用户"""
        _create_user(db_session, push_enabled=True, push_channel="email", push_time="07:00")

        res = client.post(
            "/api/v1/internal/daily-push",
            json={"hour": 7},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["pushed_count"] >= 1

    @patch("app.services.push_email.send_fortune_email", return_value=True)
    def test_skip_disabled_users(self, mock_email, client, db_session):
        """跳过未开启推送的用户"""
        _create_user(db_session, push_enabled=False, push_channel="email")

        res = client.post(
            "/api/v1/internal/daily-push",
            json={"hour": 7},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["data"]["pushed_count"] == 0
        mock_email.assert_not_called()

    @patch("app.services.push_email.send_fortune_email", return_value=True)
    def test_push_only_matching_hour(self, mock_email, client, db_session):
        """只推送当前小时的用户"""
        _create_user(db_session, push_enabled=True, push_channel="email", push_time="07:00", email="u1@test.com")
        _create_user(db_session, push_enabled=True, push_channel="email", push_time="08:00", email="u2@test.com")

        res = client.post(
            "/api/v1/internal/daily-push",
            json={"hour": 7},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["data"]["pushed_count"] == 1

    @patch("app.services.push_feishu.send_fortune_feishu", return_value=True)
    @patch("fortune_engine.services.deepseek.interpret_daily", return_value="解读")
    def test_push_to_feishu(self, mock_llm, mock_feishu, client, db_session):
        """飞书渠道推送"""
        _create_user(
            db_session, push_enabled=True, push_channel="feishu", push_time="08:00",
            feishu_webhook="https://open.feishu.cn/open-apis/bot/v2/hook/test",
        )

        res = client.post(
            "/api/v1/internal/daily-push",
            json={"hour": 8},
        )
        assert res.status_code == 200
        mock_feishu.assert_called_once()

    @patch("app.services.push_feishu.send_fortune_feishu", return_value=True)
    @patch("app.services.push_email.send_fortune_email", return_value=True)
    @patch("fortune_engine.services.deepseek.interpret_daily", return_value="解读")
    def test_push_both_channels(self, mock_llm, mock_email, mock_feishu, client, db_session):
        """双渠道推送"""
        _create_user(
            db_session, push_enabled=True, push_channel="both", push_time="09:00",
            feishu_webhook="https://open.feishu.cn/open-apis/bot/v2/hook/test",
        )

        res = client.post(
            "/api/v1/internal/daily-push",
            json={"hour": 9},
        )
        assert res.status_code == 200
        mock_email.assert_called_once()
        mock_feishu.assert_called_once()

    @patch("fortune_engine.services.deepseek.interpret_daily", side_effect=Exception("API down"))
    @patch("app.services.push_email.send_fortune_email", return_value=True)
    def test_llm_failure_degrades_gracefully(self, mock_email, mock_llm, client, db_session):
        """LLM 故障时降级推送"""
        _create_user(db_session, push_enabled=True, push_channel="email", push_time="07:00")

        res = client.post(
            "/api/v1/internal/daily-push",
            json={"hour": 7},
        )
        assert res.status_code == 200
        # 仍然推送，使用降级文本
        mock_email.assert_called_once()

    def test_stores_fortune_to_db(self, client, db_session):
        """运势存入数据库"""
        user = _create_user(db_session, push_enabled=True, push_channel="email", push_time="07:00")

        with patch("app.services.push_email.send_fortune_email", return_value=True), \
             patch("fortune_engine.services.deepseek.interpret_daily", return_value="解读"):
            client.post("/api/v1/internal/daily-push", json={"hour": 7})

        # 检查数据库中有运势记录
        fortune = db_session.query(DailyFortune).filter(
            DailyFortune.user_id == user.id
        ).first()
        assert fortune is not None
        assert fortune.overall_score > 0
