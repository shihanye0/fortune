# -*- coding: utf-8 -*-
"""天干定义"""
from dataclasses import dataclass
from fortune_engine.common.wuxing import Wuxing


@dataclass(frozen=True)
class Tiangan:
    """天干"""
    name: str
    index: int      # 0-9
    wuxing: Wuxing
    yinyang: str    # "阳" or "阴"

    @classmethod
    def from_name(cls, name: str) -> "Tiangan | None":
        """通过天干名获取"""
        for tg in TIANGAN_LIST:
            if tg.name == name:
                return tg
        return None

    @classmethod
    def from_index(cls, index: int) -> "Tiangan":
        """通过索引获取（支持循环）"""
        return TIANGAN_LIST[index % 10]


TIANGAN_LIST = [
    Tiangan("甲", 0, Wuxing.MU,   "阳"),
    Tiangan("乙", 1, Wuxing.MU,   "阴"),
    Tiangan("丙", 2, Wuxing.HUO,  "阳"),
    Tiangan("丁", 3, Wuxing.HUO,  "阴"),
    Tiangan("戊", 4, Wuxing.TU,   "阳"),
    Tiangan("己", 5, Wuxing.TU,   "阴"),
    Tiangan("庚", 6, Wuxing.JIN,  "阳"),
    Tiangan("辛", 7, Wuxing.JIN,  "阴"),
    Tiangan("壬", 8, Wuxing.SHUI, "阳"),
    Tiangan("癸", 9, Wuxing.SHUI, "阴"),
]
