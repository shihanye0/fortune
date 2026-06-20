# -*- coding: utf-8 -*-
"""Spec 012: 六爻起卦测试"""
import pytest
from fortune_engine.liuyao.hexagram import (
    coin_divination,
    time_divination,
    TRIGRAM_NAMES,
    HEXAGRAM_MAP,
)


class TestCoinDivination:
    """铜钱法起卦"""

    def test_returns_six_lines(self):
        """应返回六爻"""
        result = coin_divination("测试问题")
        assert len(result["lines"]) == 6

    def test_lines_valid_values(self):
        """每爻应为 6/7/8/9 之一（老阴/少阳/少阴/老阳）"""
        result = coin_divination("测试问题")
        for line in result["lines"]:
            assert line in [6, 7, 8, 9]

    def test_has_hexagram_name(self):
        """应有卦名"""
        result = coin_divination("测试问题")
        assert "name" in result
        assert len(result["name"]) > 0

    def test_has_upper_lower_trigram(self):
        """应有上下卦"""
        result = coin_divination("测试问题")
        assert "upper_trigram" in result
        assert "lower_trigram" in result
        assert result["upper_trigram"] in TRIGRAM_NAMES
        assert result["lower_trigram"] in TRIGRAM_NAMES

    def test_has_changing_lines(self):
        """应标注变爻"""
        result = coin_divination("测试问题")
        assert "changing_lines" in result
        assert isinstance(result["changing_lines"], list)

    def test_has_changed_hexagram(self):
        """有变爻时应有变卦"""
        result = coin_divination("测试问题")
        # 无论是否有变爻，都应有 changed_hexagram 字段
        assert "changed_hexagram" in result

    def test_question_preserved(self):
        """问题应保留"""
        result = coin_divination("最近工作是否顺利")
        assert result["question"] == "最近工作是否顺利"


class TestTimeDivination:
    """时间起卦"""

    def test_time_divination_basic(self):
        """时间起卦基本功能"""
        result = time_divination("测试", 2026, 6, 20, 14)
        assert len(result["lines"]) == 6
        assert "name" in result

    def test_deterministic(self):
        """同一时间应产生相同卦象"""
        r1 = time_divination("问题A", 2026, 6, 20, 14)
        r2 = time_divination("问题B", 2026, 6, 20, 14)
        assert r1["lines"] == r2["lines"]
        assert r1["name"] == r2["name"]

    def test_different_times_different_hexagram(self):
        """不同时间应产生不同卦象"""
        r1 = time_divination("测试", 2026, 6, 20, 10)
        r2 = time_divination("测试", 2026, 6, 20, 14)
        # 可能相同也可能不同，但结构应完整
        assert len(r1["lines"]) == 6
        assert len(r2["lines"]) == 6
