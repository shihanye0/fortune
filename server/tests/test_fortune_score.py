# -*- coding: utf-8 -*-
"""日运评分展示口径测试。"""
from datetime import date

from app.api.v1.fortunes import _build_week_forecast
from fortune_engine.bazi.score import get_fortune_level, normalize_score


def test_native_scores_have_distinct_labels():
    assert get_fortune_level(1).label == "宜守"
    assert get_fortune_level(2).label == "谨慎"
    assert get_fortune_level(3).label == "平"
    assert get_fortune_level(4).label == "偏吉"
    assert get_fortune_level(5).label == "顺势"


def test_legacy_percentage_scores_are_normalized():
    """兼容异常降级时遗留的百分制存量记录。"""
    assert normalize_score(60) == 3
    assert normalize_score(82) == 4
    assert normalize_score(100) == 5


def test_week_forecast_is_deterministic_and_does_not_need_llm():
    user = type("ForecastUser", (), {
        "birth_year": 1990,
        "birth_month": 5,
        "birth_day": 15,
        "birth_hour": 8,
        "gender": 1,
    })()

    forecast = _build_week_forecast(user, date(2026, 9, 18))

    assert len(forecast) == 7
    assert forecast[0]["date"] == "2026-09-18"
    assert forecast[-1]["date"] == "2026-09-24"
    assert all(1 <= item["overall_score"] <= 5 for item in forecast)
    assert len({item["overall_score"] for item in forecast}) > 1
    assert all(item["focus"]["label"] in {"事业", "财务", "关系", "身心"} for item in forecast)
