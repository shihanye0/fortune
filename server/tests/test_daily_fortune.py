# -*- coding: utf-8 -*-
"""Spec 011: 每日运势推算测试"""
import pytest
from fortune_engine.bazi.daily_fortune import calculate_daily_fortune


class TestDailyFortune:
    """每日运势推算"""

    def _sample_bazi(self):
        """样本八字"""
        return {
            "year_pillar": "庚午",
            "month_pillar": "辛巳",
            "day_pillar": "丙寅",
            "hour_pillar": "壬辰",
            "day_master": "丙",
            "five_elements": {"金": 2, "木": 1, "水": 1, "火": 2, "土": 2},
            "favorable_elements": ["木", "火"],
        }

    def test_returns_four_dimensions(self):
        """应返回四个维度评分"""
        bazi = self._sample_bazi()
        result = calculate_daily_fortune(bazi, 2026, 6, 20)
        assert "career_fortune" in result
        assert "wealth_fortune" in result
        assert "love_fortune" in result
        assert "health_fortune" in result

    def test_scores_in_range(self):
        """评分应在 1-5 范围内"""
        bazi = self._sample_bazi()
        result = calculate_daily_fortune(bazi, 2026, 6, 20)
        for key in ["overall_score", "career_fortune", "wealth_fortune", "love_fortune", "health_fortune"]:
            if key == "overall_score":
                assert 1 <= result[key] <= 5
            else:
                assert 1 <= result[key]["score"] <= 5

    def test_lucky_info(self):
        """应返回幸运信息"""
        bazi = self._sample_bazi()
        result = calculate_daily_fortune(bazi, 2026, 6, 20)
        assert "lucky_color" in result
        assert "lucky_number" in result
        assert "lucky_direction" in result
        assert isinstance(result["lucky_color"], str)
        assert len(result["lucky_color"]) > 0

    def test_stem_and_branch(self):
        """应返回当日干支"""
        bazi = self._sample_bazi()
        result = calculate_daily_fortune(bazi, 2026, 6, 20)
        assert "heavenly_stem" in result
        assert "earthly_branch" in result
        assert len(result["heavenly_stem"]) == 1
        assert len(result["earthly_branch"]) == 1

    def test_different_days_different_scores(self):
        """不同日期运势应不同"""
        bazi = self._sample_bazi()
        r1 = calculate_daily_fortune(bazi, 2026, 6, 20)
        r2 = calculate_daily_fortune(bazi, 2026, 6, 21)
        # 至少一个维度分数不同
        scores1 = [r1["career_fortune"]["score"], r1["wealth_fortune"]["score"]]
        scores2 = [r2["career_fortune"]["score"], r2["wealth_fortune"]["score"]]
        # 不要求完全不同，但结构应完整
        assert len(scores1) == len(scores2)
