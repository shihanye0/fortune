# -*- coding: utf-8 -*-
"""六爻起卦算法"""
import random
from datetime import datetime

# 八卦名
TRIGRAM_NAMES = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]

# 八卦对应五行
TRIGRAM_WUXING = {
    "乾": "金", "兑": "金", "离": "火", "震": "木",
    "巽": "木", "坎": "水", "艮": "土", "坤": "土",
}

# 八卦自然象
TRIGRAM_IMAGE = {
    "乾": "天", "兑": "泽", "离": "火", "震": "雷",
    "巽": "风", "坎": "水", "艮": "山", "坤": "地",
}

# 八卦二进制映射（下爻到上爻）
TRIGRAM_BINARY = {
    (1, 1, 1): "乾",
    (1, 1, 0): "兑",
    (1, 0, 1): "离",
    (1, 0, 0): "震",
    (0, 1, 1): "巽",
    (0, 1, 0): "坎",
    (0, 0, 1): "艮",
    (0, 0, 0): "坤",
}

# 64 卦名映射 (上卦, 下卦) → 卦名
HEXAGRAM_MAP = {
    ("乾", "乾"): "乾为天", ("坤", "坤"): "坤为地",
    ("坎", "坎"): "坎为水", ("离", "离"): "离为火",
    ("震", "震"): "震为雷", ("巽", "巽"): "巽为风",
    ("艮", "艮"): "艮为山", ("兑", "兑"): "兑为泽",
    ("坤", "乾"): "天地否", ("乾", "坤"): "地天泰",
    ("坎", "离"): "水火既济", ("离", "坎"): "火水未济",
    ("震", "艮"): "山雷颐", ("艮", "震"): "雷山小过",
    ("巽", "兑"): "风泽中孚", ("兑", "巽"): "泽风大过",
    ("乾", "巽"): "风天小畜", ("巽", "乾"): "天风姤",
    ("乾", "兑"): "泽天夬", ("兑", "乾"): "天泽履",
    ("乾", "离"): "火天大有", ("离", "乾"): "天火同人",
    ("乾", "震"): "雷天大壮", ("震", "乾"): "天雷无妄",
    ("乾", "坎"): "水天需", ("坎", "乾"): "天水讼",
    ("乾", "艮"): "山天大畜", ("艮", "乾"): "天山遁",
    ("坤", "巽"): "风地观", ("巽", "坤"): "地风升",
    ("坤", "兑"): "泽地萃", ("兑", "坤"): "地泽临",
    ("坤", "离"): "火地晋", ("离", "坤"): "地火明夷",
    ("坤", "震"): "雷地豫", ("震", "坤"): "地雷复",
    ("坤", "坎"): "水地比", ("坎", "坤"): "地水师",
    ("坤", "艮"): "山地剥", ("艮", "坤"): "地山谦",
    ("坎", "巽"): "风井", ("巽", "坎"): "水风井",
    ("坎", "兑"): "泽水困", ("兑", "坎"): "水泽节",
    ("坎", "离"): "水火既济", ("离", "坎"): "火水未济",
    ("坎", "震"): "雷水解", ("震", "坎"): "水雷屯",
    ("坎", "艮"): "山水蒙", ("艮", "坎"): "水山蹇",
    ("离", "巽"): "风火家人", ("巽", "离"): "火风鼎",
    ("离", "兑"): "泽火革", ("兑", "离"): "火泽睽",
    ("离", "震"): "雷火丰", ("震", "离"): "火雷噬嗑",
    ("离", "艮"): "火山旅", ("艮", "离"): "火艮贲",
    ("震", "巽"): "风雷益", ("巽", "震"): "雷风恒",
    ("震", "兑"): "泽雷随", ("兑", "震"): "雷泽归妹",
    ("震", "艮"): "山雷颐", ("艮", "震"): "雷山小过",
    ("巽", "兑"): "风泽中孚", ("兑", "巽"): "泽风大过",
    ("巽", "艮"): "风山渐", ("艮", "巽"): "山风蛊",
    ("艮", "兑"): "山泽损", ("兑", "艮"): "泽山咸",
}


def _lines_to_trigram(lines: list[int]) -> str:
    """三爻转卦名（阴=0, 阳=1）"""
    binary = tuple(1 if l % 2 == 1 else 0 for l in lines)
    return TRIGRAM_BINARY.get(binary, "乾")


def _get_hexagram_name(upper: str, lower: str) -> str:
    """获取卦名"""
    return HEXAGRAM_MAP.get((upper, lower), f"{TRIGRAM_IMAGE[upper]}{TRIGRAM_IMAGE[lower]}")


def _coin_toss() -> int:
    """铜钱法单爻：三枚铜钱，正面=3 反面=2，求和"""
    total = sum(random.choice([2, 3]) for _ in range(3))
    # 6=老阴, 7=少阳, 8=少阴, 9=老阳
    return total  # 2+2+2=6, 2+2+3=7, 2+3+3=8, 3+3+3=9


def coin_divination(question: str) -> dict:
    """
    铜钱法起卦

    Args:
        question: 占卜问题

    Returns:
        卦象数据
    """
    # 生成六爻
    lines = [_coin_toss() for _ in range(6)]

    # 本卦
    upper = _lines_to_trigram(lines[3:6])
    lower = _lines_to_trigram(lines[0:3])
    name = _get_hexagram_name(upper, lower)

    # 变爻（老阴=6 和老阳=9）
    changing = [i for i, l in enumerate(lines) if l in (6, 9)]

    # 变卦
    changed_lines = lines.copy()
    for i in changing:
        changed_lines[i] = 9 if lines[i] == 6 else 6  # 老阴变老阳，老阳变老阴

    changed_upper = _lines_to_trigram(changed_lines[3:6])
    changed_lower = _lines_to_trigram(changed_lines[0:3])
    changed_name = _get_hexagram_name(changed_upper, changed_lower)

    return {
        "question": question,
        "method": "coin",
        "name": name,
        "upper_trigram": upper,
        "lower_trigram": lower,
        "lines": lines,
        "changing_lines": changing,
        "changed_hexagram": {
            "name": changed_name,
            "upper_trigram": changed_upper,
            "lower_trigram": changed_lower,
            "lines": changed_lines,
        } if changing else None,
    }


def time_divination(question: str, year: int, month: int, day: int, hour: int) -> dict:
    """
    时间起卦（梅花易数）

    上卦 = (年 + 月 + 日) % 8
    下卦 = (年 + 月 + 日 + 时) % 8
    变爻 = (年 + 月 + 日 + 时) % 6
    """
    upper_idx = (year + month + day) % 8
    lower_idx = (year + month + day + hour) % 8
    changing_idx = (year + month + day + hour) % 6

    upper = TRIGRAM_NAMES[upper_idx]
    lower = TRIGRAM_NAMES[lower_idx]
    name = _get_hexagram_name(upper, lower)

    # 生成六爻（时间法固定为少阳/少阴）
    lines = []
    for i in range(6):
        # 根据上下卦推导
        if i < 3:
            tg_binary = list(TRIGRAM_BINARY.keys())[list(TRIGRAM_BINARY.values()).index(lower)]
            lines.append(7 if tg_binary[i] == 1 else 8)
        else:
            tg_binary = list(TRIGRAM_BINARY.keys())[list(TRIGRAM_BINARY.values()).index(upper)]
            lines.append(7 if tg_binary[i - 3] == 1 else 8)

    # 变爻
    changing = [changing_idx]

    # 变卦
    changed_lines = lines.copy()
    changed_lines[changing_idx] = 9 if lines[changing_idx] == 7 else 6
    # 变后还要变
    changed_lines[changing_idx] = 8 if changed_lines[changing_idx] == 9 else 7

    changed_upper = _lines_to_trigram(changed_lines[3:6])
    changed_lower = _lines_to_trigram(changed_lines[0:3])
    changed_name = _get_hexagram_name(changed_upper, changed_lower)

    return {
        "question": question,
        "method": "time",
        "name": name,
        "upper_trigram": upper,
        "lower_trigram": lower,
        "lines": lines,
        "changing_lines": changing,
        "changed_hexagram": {
            "name": changed_name,
            "upper_trigram": changed_upper,
            "lower_trigram": changed_lower,
            "lines": changed_lines,
        },
    }
