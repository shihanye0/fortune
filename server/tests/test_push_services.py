# -*- coding: utf-8 -*-
"""Spec 016/017: QQ邮箱推送 + 飞书推送测试"""
import smtplib
from unittest.mock import MagicMock, patch

import pytest

from app.services.push_email import send_fortune_email
from app.services.push_feishu import send_fortune_feishu


# --- QQ 邮箱推送 ---


class TestSendFortuneEmail:
    """send_fortune_email"""

    @patch("app.services.push_email.smtplib.SMTP_SSL")
    def test_send_email_success(self, mock_smtp_cls):
        """发送邮件成功"""
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        fortune_data = {
            "date": "2026-06-20",
            "overall_score": 82,
            "career": {"score": 85, "detail": "事业运良好"},
            "wealth": {"score": 78, "detail": "财运平稳"},
            "love": {"score": 80, "detail": "感情运不错"},
            "health": {"score": 85, "detail": "健康良好"},
            "lucky_color": "红色",
            "lucky_number": "3, 7",
            "lucky_direction": "正南",
            "interpretation": "今日运势整体良好。",
        }

        result = send_fortune_email(
            to_email="test@qq.com",
            fortune_data=fortune_data,
        )

        assert result is True
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()

    @patch("app.services.push_email.smtplib.SMTP_SSL")
    def test_send_email_failure(self, mock_smtp_cls):
        """发送失败返回 False"""
        mock_smtp_cls.side_effect = smtplib.SMTPException("Connection refused")

        result = send_fortune_email(
            to_email="test@qq.com",
            fortune_data={"date": "2026-06-20", "overall_score": 70},
        )

        assert result is False

    @patch("app.services.push_email.smtplib.SMTP_SSL")
    def test_email_subject_format(self, mock_smtp_cls):
        """邮件主题格式正确"""
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        send_fortune_email(
            to_email="test@qq.com",
            fortune_data={"date": "2026-06-20", "overall_score": 70},
        )

        sent_msg = mock_server.send_message.call_args[0][0]
        subject = sent_msg["Subject"]
        assert "命理运势" in subject
        assert "2026" in subject

    @patch("app.services.push_email.smtplib.SMTP_SSL")
    def test_email_content_is_html(self, mock_smtp_cls):
        """邮件内容为 HTML"""
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        send_fortune_email(
            to_email="test@qq.com",
            fortune_data={
                "date": "2026-06-20",
                "overall_score": 75,
                "interpretation": "测试解读",
            },
        )

        sent_msg = mock_server.send_message.call_args[0][0]
        payload = sent_msg.get_payload()
        body = payload[0].get_payload(decode=True).decode()
        assert "<html" in body.lower()


# --- 飞书推送 ---


class TestSendFortuneFeishu:
    """send_fortune_feishu"""

    @patch("app.services.push_feishu.httpx.post")
    def test_send_feishu_success(self, mock_post):
        """发送飞书消息成功"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 0, "msg": "success"}
        mock_post.return_value = mock_response

        fortune_data = {
            "date": "2026-06-20",
            "overall_score": 82,
            "career": {"score": 85, "detail": "事业运良好"},
            "wealth": {"score": 78, "detail": "财运平稳"},
            "love": {"score": 80, "detail": "感情运不错"},
            "health": {"score": 85, "detail": "健康良好"},
            "lucky_color": "红色",
            "interpretation": "今日运势整体良好。",
        }

        result = send_fortune_feishu(
            webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/test123",
            fortune_data=fortune_data,
        )

        assert result is True
        mock_post.assert_called_once()

    @patch("app.services.push_feishu.httpx.post")
    def test_send_feishu_failure(self, mock_post):
        """飞书 API 返回错误"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 19001, "msg": "invalid webhook"}
        mock_post.return_value = mock_response

        result = send_fortune_feishu(
            webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/bad",
            fortune_data={"date": "2026-06-20", "overall_score": 70},
        )

        assert result is False

    @patch("app.services.push_feishu.httpx.post")
    def test_send_feishu_timeout(self, mock_post):
        """飞书 API 超时"""
        import httpx
        mock_post.side_effect = httpx.TimeoutException("timeout")

        result = send_fortune_feishu(
            webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/test",
            fortune_data={"date": "2026-06-20", "overall_score": 70},
        )

        assert result is False

    @patch("app.services.push_feishu.httpx.post")
    def test_feishu_card_contains_score(self, mock_post):
        """消息卡片包含运势评分"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 0}
        mock_post.return_value = mock_response

        send_fortune_feishu(
            webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/test",
            fortune_data={
                "date": "2026-06-20",
                "overall_score": 82,
                "career": {"score": 85, "detail": "好"},
            },
        )

        call_body = mock_post.call_args[1]["json"]
        card_str = str(call_body)
        assert "82" in card_str
