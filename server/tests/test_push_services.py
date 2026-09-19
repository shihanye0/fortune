# -*- coding: utf-8 -*-
"""Spec 016/017: QQ邮箱推送 + 飞书推送测试"""
import smtplib
from unittest.mock import MagicMock, patch

import pytest

from app.services.push_email import _build_html, send_fortune_email
from app.services.push_feishu import _build_card, send_fortune_feishu


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
            "overall_score": 4,
            "career": {"score": 4, "detail": "事业运良好"},
            "wealth": {"score": 3, "detail": "财运平稳"},
            "love": {"score": 4, "detail": "感情运不错"},
            "health": {"score": 4, "detail": "健康良好"},
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
            fortune_data={"date": "2026-06-20", "overall_score": 3},
        )

        assert result is False

    @patch("app.services.push_email.smtplib.SMTP_SSL")
    def test_email_subject_format(self, mock_smtp_cls):
        """邮件主题格式正确"""
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        send_fortune_email(
            to_email="test@qq.com",
            fortune_data={"date": "2026-06-20", "overall_score": 3},
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
                "overall_score": 3,
                "interpretation": "测试解读",
            },
        )

        sent_msg = mock_server.send_message.call_args[0][0]
        payload = sent_msg.get_payload()
        assert payload[0].get_content_type() == "text/plain"
        body = payload[1].get_payload(decode=True).decode()
        assert "<html" in body.lower()

    def test_email_uses_score_scale_detail_and_escapes_dynamic_content(self):
        """邮件显示与计算层一致的 1--5 评分，且不执行动态 HTML。"""
        body = _build_html({
            "date": "2026-06-20",
            "overall_score": 5,
            "career": {"score": 4, "detail": "可推进重点事项"},
            "interpretation": "<script>alert('xss')</script>",
        })

        assert "5<span" in body
        assert "顺势" in body
        assert "可推进重点事项" in body
        assert "<script>" not in body
        assert "&lt;script&gt;" in body

    def test_email_events_are_action_points_not_percent_predictions(self):
        body = _build_html({
            "date": "2026-06-20",
            "overall_score": 3,
            "probability_events": [{"dimension": "事业", "event": "优先处理重点任务", "probability": 82}],
        })
        assert "今日行动关注点" in body
        assert "82%" not in body


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
            "overall_score": 4,
            "career": {"score": 4, "detail": "事业运良好"},
            "wealth": {"score": 3, "detail": "财运平稳"},
            "love": {"score": 4, "detail": "感情运不错"},
            "health": {"score": 4, "detail": "健康良好"},
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
            fortune_data={"date": "2026-06-20", "overall_score": 3},
        )

        assert result is False

    @patch("app.services.push_feishu.httpx.post")
    def test_send_feishu_timeout(self, mock_post):
        """飞书 API 超时"""
        import httpx
        mock_post.side_effect = httpx.TimeoutException("timeout")

        result = send_fortune_feishu(
            webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/test",
            fortune_data={"date": "2026-06-20", "overall_score": 3},
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
                "overall_score": 5,
                "career": {"score": 5, "detail": "好"},
            },
        )

        call_body = mock_post.call_args[1]["json"]
        card_str = str(call_body)
        assert "5/5 顺势" in card_str

    def test_feishu_card_uses_same_score_label(self):
        card = _build_card({"date": "2026-06-20", "overall_score": 1})
        assert "1/5 宜守" in str(card)

    def test_feishu_events_are_action_points_not_percent_predictions(self):
        card = _build_card({
            "date": "2026-06-20",
            "overall_score": 3,
            "probability_events": [{"event": "优先处理重点任务", "probability": 82}],
        })
        assert "今日行动关注点" in str(card)
        assert "82%" not in str(card)

    @patch("app.services.push_feishu.httpx.post")
    def test_feishu_rejects_untrusted_webhook_without_request(self, mock_post):
        assert send_fortune_feishu(
            "https://example.com/hook",
            {"date": "2026-06-20", "overall_score": 3},
        ) is False
        mock_post.assert_not_called()
