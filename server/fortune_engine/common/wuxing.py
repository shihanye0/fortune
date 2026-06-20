# -*- coding: utf-8 -*-
"""五行定义与生克关系"""
from enum import Enum


class Wuxing(str, Enum):
    """五行枚举"""
    JIN = "金"
    MU = "木"
    SHUI = "水"
    HUO = "火"
    TU = "土"


# 相生关系：金生水、水生木、木生火、火生土、土生金
SHENG_MAP = {
    Wuxing.JIN: Wuxing.SHUI,
    Wuxing.SHUI: Wuxing.MU,
    Wuxing.MU: Wuxing.HUO,
    Wuxing.HUO: Wuxing.TU,
    Wuxing.TU: Wuxing.JIN,
}

# 相克关系：金克木、木克土、土克水、水克火、火克金
KE_MAP = {
    Wuxing.JIN: Wuxing.MU,
    Wuxing.MU: Wuxing.TU,
    Wuxing.TU: Wuxing.SHUI,
    Wuxing.SHUI: Wuxing.HUO,
    Wuxing.HUO: Wuxing.JIN,
}


def sheng(wx: Wuxing) -> Wuxing:
    """wx 生什么"""
    return SHENG_MAP[wx]


def ke(wx: Wuxing) -> Wuxing:
    """wx 克什么"""
    return KE_MAP[wx]


def get_wuxing_of_tiangan(name: str) -> Wuxing:
    """天干取五行（延迟导入避免循环）"""
    from fortune_engine.common.tiangan import Tiangan
    tg = Tiangan.from_name(name)
    return tg.wuxing


def get_wuxing_of_dizhi(name: str) -> Wuxing:
    """地支取五行"""
    from fortune_engine.common.dizhi import Dizhi
    dz = Dizhi.from_name(name)
    return dz.wuxing
