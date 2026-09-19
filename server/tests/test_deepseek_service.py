# -*- coding: utf-8 -*-
"""Spec 014: DeepSeek 解读服务测试"""
import pytest
from unittest.mock import patch, MagicMock
from fortune_engine.services.deepseek import (
    DEFAULT_DEEPSEEK_MODEL,
    _build_payload,
    _call_deepseek,
    _normalize_base_url,
    _normalize_model,
    get_user_llm_overrides,
    interpret_fortune,
    interpret_daily,
    probe_llm_connection,
)
from app.api.v1.users import LLMSettingsRequest, _user_to_dict, update_llm_settings
from app.models.user import User


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


class TestMiMoRequestContract:
    """MiMo 正式调用与测试连接共用的请求协议。"""

    def test_legacy_mimo_url_is_migrated(self):
        assert _normalize_base_url("https://token-plan-cn.xiaomimimo.com/v1") == (
            "https://api.xiaomimimo.com/v1"
        )

    def test_deepseek_is_the_default_model(self):
        assert _normalize_model(None) == DEFAULT_DEEPSEEK_MODEL

    def test_deepseek_payload_disables_thinking_for_daily_copy(self):
        payload = _build_payload(
            "请回复 OK。",
            "deepseek-flash",
            "https://api.deepseek.com",
            64,
        )
        assert payload["thinking"] == {"type": "disabled"}
        assert payload["max_tokens"] == 64

    def test_user_overrides_are_kept_separate_from_server_default(self):
        user = type("UserConfig", (), {
            "llm_api_key": "user-key",
            "llm_api_url": "https://example.com/v1",
            "llm_model": "custom-model",
        })()
        assert get_user_llm_overrides(user) == {
            "llm_api_key": "user-key",
            "llm_api_url": "https://example.com/v1",
            "llm_model": "custom-model",
        }

    def test_untrusted_llm_url_is_never_requested(self):
        with patch("fortune_engine.services.deepseek.httpx.post") as mock_post:
            result = _call_deepseek("请回复 OK。", base_url="https://example.com/v1")
        assert result is None
        mock_post.assert_not_called()

    def test_mimo_payload_uses_current_parameter_names(self):
        payload = _build_payload(
            "请回复 OK。",
            "mimo-v2.5",
            "https://api.xiaomimimo.com/v1",
            64,
        )
        assert payload["max_completion_tokens"] == 64
        assert payload["thinking"] == {"type": "disabled"}
        assert "temperature" not in payload
        assert "max_tokens" not in payload

    def test_probe_uses_same_normalized_request(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "OK"}}]
        }
        with patch("fortune_engine.services.deepseek.httpx.post", return_value=mock_response) as mock_post:
            reply, base_url, model = probe_llm_connection(
                api_key="test-key",
                base_url="https://token-plan-cn.xiaomimimo.com/v1",
                model="mimo-v2.5[1M]",
            )

        assert (reply, base_url, model) == ("OK", "https://api.xiaomimimo.com/v1", "mimo-v2.5")
        assert mock_post.call_args.args[0] == "https://api.xiaomimimo.com/v1/chat/completions"
        assert mock_post.call_args.kwargs["json"]["thinking"] == {"type": "disabled"}

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


class TestServerDefaultLLMSelection:
    """个人覆盖只能在用户确认后清除，之后显式回退服务器 DeepSeek。"""

    def test_switch_to_server_default_clears_personal_override(self, db_session):
        user = User(
            username="llm-test-user",
            email="llm-test@example.com",
            password_hash="not-used-in-this-test",
            birth_year=1990,
            birth_month=5,
            birth_day=15,
            birth_hour=8,
            gender=1,
            llm_provider="Xiaomi MiMo",
            llm_notes="legacy personal setting",
            llm_website="https://xiaomimimo.com",
            llm_api_key="personal-secret",
            llm_api_key_url="https://xiaomimimo.com/api-key",
            llm_api_url="https://api.xiaomimimo.com/v1",
            llm_model="mimo-v2.5",
        )
        db_session.add(user)
        db_session.commit()

        result = update_llm_settings(
            LLMSettingsRequest(use_server_default=True),
            current_user=user,
            db=db_session,
        )

        assert result["success"] is True
        assert _user_to_dict(user)["llm_config_source"] == "server_default"
        assert user.llm_api_key is None
        assert user.llm_api_url is None
        assert user.llm_model is None

    def test_personal_api_key_is_encrypted_when_saved(self, db_session):
        user = User(
            username="encrypted-llm-user",
            email="encrypted-llm@example.com",
            password_hash="not-used-in-this-test",
            birth_year=1990,
            birth_month=5,
            birth_day=15,
            birth_hour=8,
            gender=1,
        )
        db_session.add(user)
        db_session.commit()

        update_llm_settings(
            LLMSettingsRequest(
                llm_api_key="personal-secret",
                llm_api_url="https://api.deepseek.com/v1",
                llm_model="deepseek-flash",
            ),
            current_user=user,
            db=db_session,
        )

        assert user.llm_api_key.startswith("fernet:v1:")
        assert get_user_llm_overrides(user)["llm_api_key"] == "personal-secret"
