# -*- coding: utf-8 -*-
"""时辰对照表"""


# 时辰名称按地支排列
SHICHEN_NAMES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 小时 → 时辰映射
# 子时：23:00-01:00（含 23 点和 0 点）
# 丑时：01:00-03:00
# ...
# 亥时：21:00-23:00
SHICHEN_MAP = {
    0: "子", 1: "丑", 2: "丑",
    3: "寅", 4: "寅", 5: "卯", 6: "卯",
    7: "辰", 8: "辰", 9: "巳", 10: "巳",
    11: "午", 12: "未", 13: "未", 14: "申", 15: "申",
    16: "酉", 17: "酉", 18: "戌", 19: "戌",
    20: "亥", 21: "亥", 22: "子", 23: "子",
}


def hour_to_shichen(hour: int) -> str:
    """将 24 小时制转为时辰名（0-23 → 子丑寅...亥）"""
    return SHICHEN_MAP[hour % 24]


def shichen_to_hours(name: str) -> tuple[int, int]:
    """时辰名转小时范围，返回 (start, end)"""
    for h, sc in SHICHEN_MAP.items():
        if sc == name:
            # 找到该时辰对应的起始小时
            start = h
            # 找结束小时
            for h2 in range(h + 1, 25):
                if SHICHEN_MAP.get(h2 % 24) != name:
                    return (start, h2 % 24)
            return (start, 0)
    return (0, 0)
