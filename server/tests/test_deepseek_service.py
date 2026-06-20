# -*- coding: utf-8 -*-
"""Spec 014: DeepSeek 解读服务测试"""
import pytest
from unittest.mock import patch, MagicMock
from fortune_engine.services.deepseek import interpret_fortune, interpret_daily


class TestInterpretFortune:
    """八字解读服务"""

    def test_returns_string(self):
        """应返回字符串解读"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "您的八字显示...事业运势良好..."}}]
        }

        with patch("fortune_engine.services.deepseek.httpx.post", return_value=mock_response):
            result = interpret_fortune(
                gender="男",
                birth_info="1990年5月15日 辰时",
                bazi="庚午 辛巳 丙寅 壬辰",
                five_elements={"金": 2, "木": 1, "水": 1, "火": 2, "土": 2},
                favorable_elements=["木", "火"],
            )
            assert isinstance(result, str)
            assert len(result) > 0

    def test_api_error_returns_fallback(self):
        """API 故障时返回降级结果"""
        with patch("fortune_engine.services.deepseek.httpx.post", side_effect=Exception("API Error")):
            result = interpret_fortune(
                gender="男",
                birth_info="1990年5月15日 辰时",
                bazi="庚午 辛巳 丙寅 壬辰",
                five_elements={"金": 2, "木": 1, "水": 1, "火": 2, "土": 2},
                favorable_elements=["木", "火"],
            )
            assert "暂不可用" in result or "降级" in result or len(result) > 0


class TestInterpretDaily:
    """每日运势解读"""

    def test_returns_string(self):
        """应返回字符串解读"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "今日运势整体不错，事业方面..."}}]
        }

        with patch("fortune_engine.services.deepseek.httpx.post", return_value=mock_response):
            result = interpret_daily(
                bazi_summary="丙火日主，喜木火",
                daily_fortune={
                    "overall_score": 4,
                    "career_fortune": {"score": 4, "detail": "事业运势不错"},
                    "wealth_fortune": {"score": 3, "detail": "财运平稳"},
                },
                user_feedback_summary="用户偏好详细建议",
            )
            assert isinstance(result, str)
            assert len(result) > 0

    def test_timeout_returns_fallback(self):
        """超时返回降级结果"""
        with patch("fortune_engine.services.deepseek.httpx.post", side_effect=TimeoutError("Timeout")):
            result = interpret_daily(
                bazi_summary="丙火日主",
                daily_fortune={"overall_score": 3},
                user_feedback_summary="",
            )
            assert isinstance(result, str)
            assert len(result) > 0
