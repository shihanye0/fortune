# -*- coding: utf-8 -*-
"""地支定义"""
from dataclasses import dataclass, field
from fortune_engine.common.wuxing import Wuxing


@dataclass(frozen=True)
class Dizhi:
    """地支"""
    name: str
    index: int          # 0-11
    wuxing: Wuxing
    yinyang: str        # "阳" or "阴"
    canggan: tuple      # 藏干（元组不可变）

    @classmethod
    def from_name(cls, name: str) -> "Dizhi | None":
        """通过地支名获取"""
        for dz in DIZHI_LIST:
            if dz.name == name:
                return dz
        return None

    @classmethod
    def from_index(cls, index: int) -> "Dizhi":
        """通过索引获取（支持循环）"""
        return DIZHI_LIST[index % 12]


DIZHI_LIST = [
    Dizhi("子", 0,  Wuxing.SHUI, "阳", ("癸",)),
    Dizhi("丑", 1,  Wuxing.TU,   "阴", ("己", "癸", "辛")),
    Dizhi("寅", 2,  Wuxing.MU,   "阳", ("甲", "丙", "戊")),
    Dizhi("卯", 3,  Wuxing.MU,   "阴", ("乙",)),
    Dizhi("辰", 4,  Wuxing.TU,   "阳", ("戊", "乙", "癸")),
    Dizhi("巳", 5,  Wuxing.HUO,  "阴", ("丙", "庚", "戊")),
    Dizhi("午", 6,  Wuxing.HUO,  "阳", ("丁", "己")),
    Dizhi("未", 7,  Wuxing.TU,   "阴", ("己", "丁", "乙")),
    Dizhi("申", 8,  Wuxing.JIN,  "阳", ("庚", "壬", "戊")),
    Dizhi("酉", 9,  Wuxing.JIN,  "阴", ("辛",)),
    Dizhi("戌", 10, Wuxing.TU,   "阳", ("戊", "辛", "丁")),
    Dizhi("亥", 11, Wuxing.SHUI, "阴", ("壬", "甲")),
]
