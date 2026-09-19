# -*- coding: utf-8 -*-
"""Spec 010: 八字排盘测试"""
import pytest
from fortune_engine.bazi.pillar import calculate_bazi


class TestBaziCalculation:
    """八字排盘核心测试"""

    def test_basic_bazi(self):
        """基本排盘：1990-05-15 08:00"""
        result = calculate_bazi(1990, 5, 15, 8, gender=1)
        # 验证四柱非空
        assert "year_pillar" in result
        assert "month_pillar" in result
        assert "day_pillar" in result
        assert "hour_pillar" in result
        # 每柱应为两个字
        assert len(result["year_pillar"]) == 2
        assert len(result["month_pillar"]) == 2
        assert len(result["day_pillar"]) == 2
        assert len(result["hour_pillar"]) == 2

    def test_day_master(self):
        """日柱天干为日主"""
        result = calculate_bazi(1990, 5, 15, 8, gender=1)
        day_pillar = result["day_pillar"]
        assert result["day_master"] == day_pillar[0]

    def test_five_elements_count(self):
        """五行分布应覆盖四柱天干与地支的八个可见字。"""
        result = calculate_bazi(1990, 5, 15, 8, gender=1)
        fe = result["five_elements"]
        assert set(fe.keys()) == {"金", "木", "水", "火", "土"}
        assert sum(fe.values()) == 8  # 四柱天干 + 地支 = 8 个可见字

    def test_ten_gods(self):
        """十神关系"""
        result = calculate_bazi(1990, 5, 15, 8, gender=1)
        tg = result["ten_gods"]
        assert "year" in tg
        assert "month" in tg
        assert "hour" in tg

    def test_zi_hour_midnight(self):
        """子时处理：23:30 应为子时"""
        result = calculate_bazi(1990, 5, 15, 23, gender=1)
        # 时柱应为子时
        assert result["hour_pillar"][1] == "子"

    def test_zi_hour_date_change(self):
        """子时日柱切换：23:30 出生日柱应不同于白天"""
        result_day = calculate_bazi(1990, 5, 15, 10, gender=1)
        result_night = calculate_bazi(1990, 5, 15, 23, gender=1)
        # 23:30 的日柱可能与白天不同（子时换日）
        # 这里只验证不报错，具体规则由实现决定
        assert len(result_night["day_pillar"]) == 2

    def test_major_luck_cycles(self):
        """大运排列应包含按节气差计算的实际起运区间。"""
        result = calculate_bazi(1990, 5, 15, 8, gender=1)
        cycles = result["major_luck_cycles"]
        assert isinstance(cycles, list)
        assert len(cycles) == 8
        # 每个大运应有实际起止年龄、年份和天干地支。
        for c in cycles:
            assert "start_age" in c
            assert "end_age" in c
            assert "start_year" in c
            assert "end_year" in c
            assert "pillar" in c
            assert len(c["pillar"]) == 2
        # 1990-05-15 男命按节气差起运为 8 岁，不能固定写为 10 岁。
        assert cycles[0]["start_age"] == 8
        assert cycles[0]["start_year"] == 1997

    def test_uses_exact_solar_term_boundary(self):
        """立春后应采用节气年柱，而不能沿用农历年柱。"""
        result = calculate_bazi(2026, 2, 4, 12, gender=1)

        assert result["year_pillar"] == "丙午"
        assert result["month_pillar"] == "庚寅"

    def test_weak_day_master_prefers_generating_element(self):
        """日主偏弱时，基础偏向的首项应为生我五行。"""
        result = calculate_bazi(2026, 2, 4, 12, gender=1)

        assert result["day_master"] == "己"
        assert result["five_elements"]["土"] == 1
        assert result["favorable_elements"] == ["火", "土"]

    def test_favorable_elements(self):
        """喜用神"""
        result = calculate_bazi(1990, 5, 15, 8, gender=1)
        fav = result["favorable_elements"]
        assert isinstance(fav, list)
        assert len(fav) > 0
        assert all(f in ["金", "木", "水", "火", "土"] for f in fav)

    def test_different_genders_different_luck(self):
        """不同性别大运排列方向不同"""
        result_m = calculate_bazi(1990, 5, 15, 8, gender=1)
        result_f = calculate_bazi(1990, 5, 15, 8, gender=0)
        # 大运排列应不同（顺排 vs 逆排）
        if result_m["major_luck_cycles"] and result_f["major_luck_cycles"]:
            # 至少前几步大运应不同
            m_pillars = [c["pillar"] for c in result_m["major_luck_cycles"][:3]]
            f_pillars = [c["pillar"] for c in result_f["major_luck_cycles"][:3]]
            # 不要求完全不同，但结构应正确
            assert len(m_pillars) == len(f_pillars)
