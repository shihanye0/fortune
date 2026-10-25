# -*- coding: utf-8 -*-
"""Spec 016/017: QQ邮箱推送 + 飞书推送测试"""
import smtplib
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.models.base import CHINA_TZ
from app.services.push_email import _build_html, _build_text, send_fortune_email
from app.services.push_feishu import _build_card, send_fortune_feishu


def _hour(shichen: str, start: str, end: str, score: int,
          ten_god: str = "", element: str = "", stem: str = "", branch: str = "") -> dict:
    """构造一条时辰运势测试数据。"""
    return {
        "shichen": shichen,
        "shichen_range": f"{start}-{end}",
        "score": score,
        "hourly_stem": stem,
        "hourly_branch": branch,
        "ten_god": ten_god,
        "element": element,
        "favorable": ["签约", "汇报工作"],
        "unfavorable": ["争执", "冲动消费"],
        "events": ["贵人出现", "收到好消息"],
    }


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


class TestHourlyPushRendering:
    """时辰推送优化：已过时辰过滤、状态标记、十神成因、时段建议。"""

    # 发送时刻 14:30：辰时/午时已过，未时进行中，申时/酉时未到
    _NOW = datetime(2026, 6, 20, 14, 30, tzinfo=CHINA_TZ)

    def _data(self) -> dict:
        return {
            "date": "2026-06-20",
            "overall_score": 4,
            "hourly_fortunes": [
                _hour("辰", "07:00", "09:00", 5),
                _hour("午", "11:00", "13:00", 4),
                _hour("未", "13:00", "15:00", 4, "正印", "水", "壬", "未"),
                _hour("申", "15:00", "17:00", 3),
                _hour("酉", "17:00", "19:00", 2),
            ],
        }

    def test_past_hours_excluded_from_recommendations(self):
        """已过时辰不再进入宜/忌卡，未到时辰带开始时间。"""
        body = _build_html(self._data(), now=self._NOW)
        # 卡片才会渲染时辰区间；评分最高的辰时已过，不应出现在卡片里
        assert "07:00-09:00" not in body
        assert "11:00-13:00" not in body
        # 未时进行中、申时未到 → 作为推荐卡
        assert "进行中" in body
        assert "15:00 开始" in body
        assert "13:00-15:00" in body
        # 酉时 2 分且未到 → 忌卡
        assert "17:00-19:00" in body

    def test_preheader_prefers_upcoming_hours(self):
        """收件箱预览从未过时辰里取宜事，不推荐已过的辰时。"""
        body = _build_html(self._data(), now=self._NOW)
        assert "未时宜" in body or "申时宜" in body
        assert "辰时宜" not in body

    def test_hourly_card_shows_ten_god_cause(self):
        """时辰卡展示流时干支与十神成因。"""
        body = _build_html(self._data(), now=self._NOW)
        assert "正印" in body
        assert "壬未时" in body

    def test_all_hours_past_falls_back_with_marker(self):
        """深夜重试场景：全天已过时仍出卡，但明确标注已过。"""
        body = _build_html(self._data(), now=datetime(2026, 6, 20, 23, 30, tzinfo=CHINA_TZ))
        assert "已过" in body
        assert "07:00-09:00" in body

    def test_events_show_suggested_time_window(self):
        """行动关注点带建议时段；已过时段标注而非继续推荐；不显示概率。"""
        body = _build_html({
            "date": "2026-06-20",
            "overall_score": 3,
            "probability_events": [
                {"dimension": "事业", "event": "推进重点任务", "probability": 82,
                 "best_hour": "未", "time_range": "13:00-15:00"},
                {"dimension": "人际", "event": "回复旧消息", "probability": 55,
                 "best_hour": "辰", "time_range": "07:00-09:00"},
                {"dimension": "幸运", "event": "穿幸运色", "probability": 70,
                 "time_range": "全天"},
            ],
        }, now=self._NOW)
        assert "未时 13:00-15:00" in body
        assert "辰时 07:00-09:00" not in body
        assert "已过" in body
        assert "全天" in body
        assert "82%" not in body
        assert "70%" not in body

    def test_text_version_contains_hourly_summary(self):
        """纯文本降级版包含时辰摘要、建议时段和推送设置入口。"""
        text = _build_text({
            "date": "2026-06-20",
            "overall_score": 4,
            "hourly_fortunes": [
                _hour("辰", "07:00", "09:00", 5),
                _hour("未", "13:00", "15:00", 4),
                _hour("申", "15:00", "17:00", 3),
                _hour("酉", "17:00", "19:00", 2),
            ],
            "probability_events": [
                {"dimension": "事业", "event": "推进重点任务",
                 "best_hour": "未", "time_range": "13:00-15:00"},
            ],
        }, now=self._NOW)
        assert "今日吉时：未时 13:00-15:00（4/5）" in text
        assert "需留意时辰：酉时 17:00-19:00（2/5）" in text
        assert "建议时段：未时 13:00-15:00" in text
        assert "推送设置：" in text

    def test_hai_hour_wraps_midnight(self):
        """亥时区间 22:00-00:00 跨午夜，深夜仍应识别为进行中。"""
        body = _build_html({
            "date": "2026-06-20",
            "overall_score": 3,
            "hourly_fortunes": [
                _hour("戌", "20:00", "22:00", 4),
                _hour("亥", "22:00", "00:00", 5),
            ],
        }, now=datetime(2026, 6, 20, 23, 30, tzinfo=CHINA_TZ))
        assert "进行中" in body
        assert "22:00-00:00" in body

    def test_footer_contains_profile_link(self):
        """页脚包含个人中心入口链接。"""
        body = _build_html({"date": "2026-06-20", "overall_score": 3})
        assert "http://82.157.186.52/profile" in body


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
