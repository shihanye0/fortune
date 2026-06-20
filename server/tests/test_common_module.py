# -*- coding: utf-8 -*-
"""Spec 009: 公共基础模块测试 — 天干/地支/五行/时辰"""
import pytest
from fortune_engine.common.tiangan import Tiangan, TIANGAN_LIST
from fortune_engine.common.dizhi import Dizhi, DIZHI_LIST
from fortune_engine.common.wuxing import Wuxing, sheng, ke, get_wuxing_of_tiangan, get_wuxing_of_dizhi
from fortune_engine.common.shichen import hour_to_shichen, SHICHEN_MAP


# ====== 天干测试 ======

class TestTiangan:
    def test_tiangan_count(self):
        """天干共 10 个"""
        assert len(TIANGAN_LIST) == 10

    def test_tiangan_order(self):
        """天干顺序：甲乙丙丁戊己庚辛壬癸"""
        expected = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        assert [t.name for t in TIANGAN_LIST] == expected

    def test_tiangan_wuxing(self):
        """天干五行属性"""
        cases = {
            "甲": Wuxing.MU, "乙": Wuxing.MU,
            "丙": Wuxing.HUO, "丁": Wuxing.HUO,
            "戊": Wuxing.TU, "己": Wuxing.TU,
            "庚": Wuxing.JIN, "辛": Wuxing.JIN,
            "壬": Wuxing.SHUI, "癸": Wuxing.SHUI,
        }
        for name, expected_wx in cases.items():
            tg = Tiangan.from_name(name)
            assert tg.wuxing == expected_wx, f"{name} 五行应为 {expected_wx}"

    def test_tiangan_yinyang(self):
        """天干阴阳：甲丙戊庚壬为阳，乙丁己辛癸为阴"""
        yang = ["甲", "丙", "戊", "庚", "壬"]
        yin = ["乙", "丁", "己", "辛", "癸"]
        for name in yang:
            assert Tiangan.from_name(name).yinyang == "阳", f"{name} 应为阳"
        for name in yin:
            assert Tiangan.from_name(name).yinyang == "阴", f"{name} 应为阴"

    def test_tiangan_from_index(self):
        """通过索引获取天干"""
        assert Tiangan.from_index(0).name == "甲"
        assert Tiangan.from_index(9).name == "癸"
        assert Tiangan.from_index(10).name == "甲"  # 循环

    def test_tiangan_from_name_invalid(self):
        """无效天干名返回 None"""
        assert Tiangan.from_name("X") is None


# ====== 地支测试 ======

class TestDizhi:
    def test_dizhi_count(self):
        """地支共 12 个"""
        assert len(DIZHI_LIST) == 12

    def test_dizhi_order(self):
        """地支顺序：子丑寅卯辰巳午未申酉戌亥"""
        expected = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        assert [d.name for d in DIZHI_LIST] == expected

    def test_dizhi_wuxing(self):
        """地支五行属性"""
        cases = {
            "子": Wuxing.SHUI, "丑": Wuxing.TU,
            "寅": Wuxing.MU, "卯": Wuxing.MU,
            "辰": Wuxing.TU, "巳": Wuxing.HUO,
            "午": Wuxing.HUO, "未": Wuxing.TU,
            "申": Wuxing.JIN, "酉": Wuxing.JIN,
            "戌": Wuxing.TU, "亥": Wuxing.SHUI,
        }
        for name, expected_wx in cases.items():
            dz = Dizhi.from_name(name)
            assert dz.wuxing == expected_wx, f"{name} 五行应为 {expected_wx}"

    def test_dizhi_canggan(self):
        """地支藏干"""
        cases = {
            "子": ("癸",),
            "丑": ("己", "癸", "辛"),
            "寅": ("甲", "丙", "戊"),
            "卯": ("乙",),
            "辰": ("戊", "乙", "癸"),
            "巳": ("丙", "庚", "戊"),
            "午": ("丁", "己"),
            "未": ("己", "丁", "乙"),
            "申": ("庚", "壬", "戊"),
            "酉": ("辛",),
            "戌": ("戊", "辛", "丁"),
            "亥": ("壬", "甲"),
        }
        for name, expected_cg in cases.items():
            dz = Dizhi.from_name(name)
            assert dz.canggan == expected_cg, f"{name} 藏干应为 {expected_cg}"

    def test_dizhi_from_index(self):
        """通过索引获取地支"""
        assert Dizhi.from_index(0).name == "子"
        assert Dizhi.from_index(11).name == "亥"
        assert Dizhi.from_index(12).name == "子"  # 循环


# ====== 五行测试 ======

class TestWuxing:
    def test_sheng(self):
        """五行相生：金生水、水生木、木生火、火生土、土生金"""
        assert sheng(Wuxing.JIN) == Wuxing.SHUI
        assert sheng(Wuxing.SHUI) == Wuxing.MU
        assert sheng(Wuxing.MU) == Wuxing.HUO
        assert sheng(Wuxing.HUO) == Wuxing.TU
        assert sheng(Wuxing.TU) == Wuxing.JIN

    def test_ke(self):
        """五行相克：金克木、木克土、土克水、水克火、火克金"""
        assert ke(Wuxing.JIN) == Wuxing.MU
        assert ke(Wuxing.MU) == Wuxing.TU
        assert ke(Wuxing.TU) == Wuxing.SHUI
        assert ke(Wuxing.SHUI) == Wuxing.HUO
        assert ke(Wuxing.HUO) == Wuxing.JIN

    def test_get_wuxing_of_tiangan(self):
        """天干取五行"""
        assert get_wuxing_of_tiangan("甲") == Wuxing.MU
        assert get_wuxing_of_tiangan("庚") == Wuxing.JIN

    def test_get_wuxing_of_dizhi(self):
        """地支取五行"""
        assert get_wuxing_of_dizhi("子") == Wuxing.SHUI
        assert get_wuxing_of_dizhi("午") == Wuxing.HUO


# ====== 时辰测试 ======

class TestShichen:
    def test_hour_to_shichen(self):
        """小时转时辰"""
        assert hour_to_shichen(0) == "子"   # 23:00-01:00
        assert hour_to_shichen(1) == "丑"   # 01:00-03:00
        assert hour_to_shichen(2) == "丑"
        assert hour_to_shichen(3) == "寅"
        assert hour_to_shichen(7) == "辰"
        assert hour_to_shichen(8) == "辰"
        assert hour_to_shichen(11) == "午"
        assert hour_to_shichen(12) == "未"
        assert hour_to_shichen(15) == "申"
        assert hour_to_shichen(17) == "酉"
        assert hour_to_shichen(19) == "戌"
        assert hour_to_shichen(21) == "亥"
        assert hour_to_shichen(23) == "子"

    def test_shichen_map_has_12_unique(self):
        """时辰表共 12 个不同时辰"""
        unique = set(SHICHEN_MAP.values())
        assert len(unique) == 12
