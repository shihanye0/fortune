# -*- coding: utf-8 -*-
"""每日运势评分的唯一展示口径。

计算层以 1--5 为原生评分。此模块同时兼容早期异常降级记录中遗留的
0--100 分数，避免历史记录再次被错误地解释为低分。
"""
from dataclasses import dataclass
from math import floor
from typing import Any


@dataclass(frozen=True)
class FortuneLevel:
    """一个可展示的日运势等级。"""

    score: int
    label: str
    color: str
    guidance: str


FORTUNE_LEVELS = {
    1: FortuneLevel(1, "宜守", "#9f1239", "放慢节奏，优先处理确定性事务。"),
    2: FortuneLevel(2, "谨慎", "#b45309", "留出余地，重要决定多做一次核对。"),
    3: FortuneLevel(3, "平", "#475569", "按既定节奏推进，避免过度解读。"),
    4: FortuneLevel(4, "偏吉", "#0f766e", "条件较顺，可主动推进重要事项。"),
    5: FortuneLevel(5, "顺势", "#6d28d9", "状态较佳，把精力投向优先事项。"),
}


def normalize_score(value: Any, default: int = 3) -> int:
    """将新旧评分统一为 1--5。

    新生成的日运势始终是 1--5。早期异常降级分支曾写入 60、70 等
    百分制数值；读取这些历史记录时按 20 分一个档位转换，避免污染页面
    和推送的等级文案。
    """
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default

    if numeric <= 0:
        return default
    if numeric > 5:
        numeric /= 20

    return max(1, min(5, floor(numeric + 0.5)))


def get_fortune_level(score: Any) -> FortuneLevel:
    """返回评分对应的稳定展示元数据。"""
    return FORTUNE_LEVELS[normalize_score(score)]
