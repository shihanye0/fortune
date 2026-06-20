# -*- coding: utf-8 -*-
"""Spec 013: 奇门遁甲排盘测试"""
import pytest
from fortune_engine.qimen.chart import calculate_qimen


class TestQimenChart:
    """奇门遁甲排盘"""

    def test_basic_structure(self):
        """基本结构验证"""
        result = calculate_qimen(2026, 6, 20, 8)
        assert "time" in result
        assert "yin_yang" in result
        assert "ju_shu" in result
        assert "palace" in result

    def test_nine_palaces(self):
        """应有 9 个宫位"""
        result = calculate_qimen(2026, 6, 20, 8)
        palaces = result["palace"]
        assert len(palaces) == 9
        for i in range(1, 10):
            assert str(i) in palaces

    def test_palace_contents(self):
        """每个宫位应有九星、八门、八神"""
        result = calculate_qimen(2026, 6, 20, 8)
        for pid, p in result["palace"].items():
            assert "star" in p, f"宫位 {pid} 缺少九星"
            assert "gate" in p, f"宫位 {pid} 缺少八门"
            assert "god" in p, f"宫位 {pid} 缺少八神"

    def test_valid_star_names(self):
        """九星名称应有效"""
        valid_stars = ["天蓬", "天芮", "天冲", "天辅", "天禽", "天心", "天柱", "天任", "天英"]
        result = calculate_qimen(2026, 6, 20, 8)
        for p in result["palace"].values():
            assert p["star"] in valid_stars

    def test_valid_gate_names(self):
        """八门名称应有效"""
        valid_gates = ["休门", "死门", "伤门", "杜门", "开门", "惊门", "生门", "景门"]
        result = calculate_qimen(2026, 6, 20, 8)
        for p in result["palace"].values():
            assert p["gate"] in valid_gates

    def test_valid_god_names(self):
        """八神名称应有效"""
        valid_gods = ["值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]
        result = calculate_qimen(2026, 6, 20, 8)
        for p in result["palace"].values():
            assert p["god"] in valid_gods

    def test_yin_yang_dun(self):
        """阴阳遁应为阳遁或阴遁"""
        result = calculate_qimen(2026, 6, 20, 8)
        assert result["yin_yang"] in ["阳遁", "阴遁"]

    def test_ju_shu_range(self):
        """局数应为 1-9"""
        result = calculate_qimen(2026, 6, 20, 8)
        assert 1 <= result["ju_shu"] <= 9

    def test_deterministic(self):
        """同一时间应产生相同盘面"""
        r1 = calculate_qimen(2026, 6, 20, 8)
        r2 = calculate_qimen(2026, 6, 20, 8)
        assert r1["palace"] == r2["palace"]
        assert r1["ju_shu"] == r2["ju_shu"]
